"""M2.5: WebSocket 实时进度推送。

前端用法（Vue 3 / Pinia）：
    const ws = new WebSocket(`ws://host/api/v1/ws/optimize/${task_id}`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      // msg.type: 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
      // msg.progress: 0.0-1.0
      // msg.current_iter / max_iter
      // msg.best_score (PROGRESS/SUCCESS)
    }

断线兜底：
- 如果 WS 在任务完成后才连接，会立即收到 Celery result backend 的最终状态
- 如果任务还在 PENDING（还没 worker 拉起），先 yield STARTED 占位
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.db import OptimizationTask, SessionLocal, TaskStatus
from backend.utils.redis_pubsub import (
    get_task_final_state,
    subscribe_progress,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_task(task_id: str) -> OptimizationTask | None:
    db: Session = SessionLocal()
    try:
        return db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
    finally:
        db.close()


def _task_to_progress_msg(task: OptimizationTask) -> dict[str, Any] | None:
    """把 DB 任务当前状态转成 WS 消息（首条握手用）。"""
    status = task.status.value if hasattr(task.status, "value") else str(task.status)
    msg: dict[str, Any] = {
        "type": status,  # PENDING/STARTED/PROGRESS/SUCCESS/FAILURE/REVOKED
        "progress": float(task.progress or 0.0),
        "current_iter": int(task.current_iter or 0),
        "max_iter": int(task.max_iter or 0),
    }
    if task.error_message:
        msg["error"] = task.error_message
    return msg


@router.websocket("/ws/optimize/{task_id}")
async def ws_optimize_progress(websocket: WebSocket, task_id: str):
    """订阅指定 task 的实时进度。

    协议：
    1. 接受连接（accept）
    2. 检查 task 存在性 → 不存在直接 close 1008
    3. 发首条"快照"消息（DB 当前状态）
    4. 若已 SUCCESS/FAILURE → 发完整结果 → close
    5. 否则订阅 Redis pub/sub，循环 yield
    6. 收到 SUCCESS/FAILURE → close
    """
    await websocket.accept()

    task = _load_task(task_id)
    if not task:
        await websocket.send_json({"type": "ERROR", "error": f"task {task_id} not found"})
        await websocket.close(code=1008)
        return

    # 1. 首条快照（包含完整 result if 已终态）
    snapshot = _task_to_progress_msg(task)
    final_status = task.status.value if hasattr(task.status, "value") else str(task.status)
    if final_status in (TaskStatus.SUCCESS.value, TaskStatus.FAILURE.value, TaskStatus.REVOKED.value):
        # 终态：把 result/error 一次性附到 snapshot（不再发两遍空 msg）
        if task.result_json:
            try:
                snapshot["result"] = json.loads(task.result_json)
            except json.JSONDecodeError:
                pass
        if task.error_message:
            snapshot["error"] = task.error_message
        await websocket.send_json(snapshot)
        await websocket.close()
        return

    # 进行中：先发快照
    if snapshot:
        await websocket.send_json(snapshot)

    # 3. 实时订阅
    try:
        async for msg in subscribe_progress(task_id):
            if msg.get("type") == "SUCCESS":
                # SUCCESS：等 result_json commit（最多 2s 重试）再一次性发带 result 的消息
                import asyncio
                for retry in range(10):
                    final = _load_task(task_id)
                    if final and final.result_json:
                        try:
                            msg["result"] = json.loads(final.result_json)
                            logger.info(f"WS SUCCESS result attached on retry {retry}")
                            break
                        except json.JSONDecodeError:
                            pass
                    await asyncio.sleep(0.2)
                else:
                    logger.warning(f"WS SUCCESS result_json not found after 10 retries for {task_id}")
                await websocket.send_json(msg)
                break
            await websocket.send_json(msg)
            if msg.get("type") in ("FAILURE", "REVOKED"):
                # FAILURE：发原 msg（含 error）后断开
                break
    except WebSocketDisconnect:
        logger.info(f"WS client disconnected: task={task_id}")
    except Exception as e:  # noqa: BLE001
        logger.exception(f"WS error: {e}")
        try:
            await websocket.send_json({"type": "ERROR", "error": str(e)})
        except Exception:  # noqa: BLE001
            pass
    finally:
        try:
            await websocket.close()
        except Exception:  # noqa: BLE001
            pass
