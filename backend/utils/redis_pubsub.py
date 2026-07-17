"""Redis Pub/Sub 工具（M2.5：WS 实时进度推送）。

设计要点：
- Publisher 在 Celery worker（同步），用 sync redis client
- Subscriber 在 FastAPI WebSocket（异步），用 async redis client
- Channel 命名：`optimize:{task_id}`
- 消息格式：JSON 字符串

消息类型：
- {"type": "STARTED", "progress": 0.05, "current_iter": 0, "max_iter": 30}
- {"type": "PROGRESS", "progress": 0.1, "current_iter": 3, "max_iter": 30, "best_score": 0.85}
- {"type": "SUCCESS", "progress": 1.0, "current_iter": 30, "best_score": ..., "elapsed_sec": 0.6}
- {"type": "FAILURE", "error": "..."}
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import redis
import redis.asyncio as aioredis

from backend.config import settings

logger = logging.getLogger(__name__)

# 同步 client（worker 用，复用连接）
_sync_pool: redis.ConnectionPool | None = None


def _get_sync_redis() -> redis.Redis:
    """获取同步 redis client（懒加载 + 复用连接池）。"""
    global _sync_pool
    if _sync_pool is None:
        _sync_pool = redis.ConnectionPool.from_url(
            settings.celery_broker_url,
            decode_responses=True,
        )
    return redis.Redis(connection_pool=_sync_pool)


def optimize_channel(task_id: str) -> str:
    """优化任务对应的 pub/sub channel。"""
    return f"optimize:{task_id}"


def publish_progress(task_id: str, payload: dict[str, Any]) -> int:
    """同步 publish 一条进度消息。返回订阅者数（0 = 没人订阅，丢弃即可）。"""
    payload.setdefault("type", "PROGRESS")
    try:
        client = _get_sync_redis()
        return client.publish(optimize_channel(task_id), json.dumps(payload, default=str))
    except Exception as e:  # noqa: BLE001
        # Pub/Sub 是 best-effort，不能因为它挂掉拖垮主任务
        logger.warning(f"publish_progress failed: {e}")
        return 0


def replay_convergence_curve(
    task_id: str,
    curve: list[float],
    max_iter: int,
    interval_sec: float = 0.1,
) -> None:
    """算法跑完后回放 convergence_curve 31 个点，模拟实时进度。

    间隔 0.1s × 31 = 3.1s，刚好匹配 M2 实测的端到端时间。
    订阅者数 = 0 时跳过 sleep（无人订阅就不浪费 CPU）。
    """
    import time

    if not curve:
        return
    n = len(curve)
    for i, score in enumerate(curve):
        progress = round((i + 1) / n, 3)
        subs = publish_progress(
            task_id,
            {
                "type": "PROGRESS",
                "progress": min(progress, 0.99),  # 留 1.0 给 SUCCESS
                "current_iter": int((i + 1) * max_iter / n),
                "max_iter": max_iter,
                "best_score": float(score),
            },
        )
        if subs > 0 and i < n - 1:
            time.sleep(interval_sec)


async def subscribe_progress(task_id: str) -> AsyncIterator[dict[str, Any]]:
    """异步订阅 task 进度，yield 每条消息（JSON 解析后）。

    使用方式（FastAPI WebSocket）：
        async for msg in subscribe_progress(task_id):
            await websocket.send_json(msg)
            if msg.get("type") in ("SUCCESS", "FAILURE"):
                break
    """
    client = aioredis.from_url(
        settings.celery_broker_url,
        decode_responses=True,
        socket_timeout=60.0,
        socket_connect_timeout=5.0,
        socket_keepalive=True,
        health_check_interval=30,
    )
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(optimize_channel(task_id))
    try:
        # redis-py ≥ 5: pubsub.listen() 是 async generator，直接 async for
        # 设置较短 timeout 让上层能感知断开
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                yield json.loads(message["data"])
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"bad pubsub message: {e}")
                continue
    finally:
        try:
            await pubsub.unsubscribe(optimize_channel(task_id))
            await pubsub.aclose() if hasattr(pubsub, "aclose") else await pubsub.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            await client.aclose() if hasattr(client, "aclose") else await client.close()
        except Exception:  # noqa: BLE001
            pass


def get_task_final_state(task_id: str) -> dict[str, Any] | None:
    """从 Redis 读 Celery task 最终状态（兜底用，WS 断线时给前端补一次完整结果）。

    Celery result backend 默认存 1 小时。
    """
    try:
        client = _get_sync_redis()
        # result backend 用了 db 1
        result_key = f"celery-task-meta-{task_id}"
        raw = client.connection_pool.connection_kwargs
        result_client = redis.Redis(
            host=raw.get("host", "localhost"),
            port=raw.get("port", 6379),
            db=1,
            decode_responses=True,
        )
        data = result_client.get(result_key)
        if not data:
            return None
        return json.loads(data)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"get_task_final_state failed: {e}")
        return None
