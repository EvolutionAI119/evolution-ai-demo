"""M2.5 WebSocket 端到端验证。

流程：
1. POST /api/v1/optimize/start-preset  → 拿到 task_id
2. ws://127.0.0.1:8000/api/v1/ws/optimize/{task_id}  → 收消息
3. 统计 STARTED / PROGRESS / SUCCESS 数量 + 打印前 2 条/类型

用法：python /app/data/所有对话/主对话/EVOLUTION_AI_DEMO/logs/m25_ws_e2e.py
"""
import json
import sys
import time

import httpx
import websocket

BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"


def main() -> int:
    # 1. 启动优化任务
    print("=" * 60)
    print("[1] POST /api/v1/optimize/start-preset")
    with httpx.Client(timeout=10.0) as client:
        r = client.post(
            f"{BASE}/api/v1/optimize/start-preset",
            json={"shape": "sphere", "max_iter": 30},
        )
    if r.status_code != 202:
        print(f"  ❌ HTTP {r.status_code}: {r.text}")
        return 1
    task = r.json()
    task_id = task["task_id"]
    print(f"  ✅ task_id={task_id}")
    print(f"  📋 status={task.get('status')}, status_url={task.get('status_url')}")

    # 2. 连接 WS
    print("=" * 60)
    print(f"[2] WS connect: {WS_BASE}/api/v1/ws/optimize/{task_id}")
    ws = websocket.create_connection(
        f"{WS_BASE}/api/v1/ws/optimize/{task_id}",
        timeout=15.0,
    )
    print("  ✅ connected")

    # 3. 收消息直到 SUCCESS / FAILURE / 超时
    print("=" * 60)
    print("[3] 接收消息流:")
    counts: dict[str, int] = {}
    samples: dict[str, list[dict]] = {}
    started_at = time.time()
    try:
        while time.time() - started_at < 15.0:
            try:
                ws.settimeout(8.0)
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                print("  ⏰ 8s 内无消息，超时退出")
                break
            if not raw:
                continue
            msg = json.loads(raw)
            t = msg.get("type", "UNKNOWN")
            counts[t] = counts.get(t, 0) + 1
            if t not in samples:
                samples[t] = []
            if len(samples[t]) < 2:
                samples[t].append(msg)
            # 终态退出
            if t in ("SUCCESS", "FAILURE"):
                # 服务端会再发一条带 result 的（SUCCESS 时）
                try:
                    ws.settimeout(2.0)
                    final_raw = ws.recv()
                    if final_raw:
                        final_msg = json.loads(final_raw)
                        ft = final_msg.get("type", "UNKNOWN")
                        counts[ft] = counts.get(ft, 0) + 1
                        if ft not in samples:
                            samples[ft] = [final_msg]
                except Exception:  # noqa: BLE001
                    pass
                break
    finally:
        try:
            ws.close()
        except Exception:  # noqa: BLE001
            pass

    elapsed = time.time() - started_at
    print("=" * 60)
    print("[4] 统计")
    print(f"  ⏱️  端到端耗时: {elapsed:.2f}s")
    print(f"  📊 消息计数: {counts}")
    print()
    print("  样本消息（前 2 条/类型）:")
    for t, msgs in samples.items():
        for i, m in enumerate(msgs):
            short = {k: v for k, v in m.items() if k != "result"}
            print(f"    [{t} #{i + 1}] {json.dumps(short, ensure_ascii=False)[:200]}")

    # 5. 验收
    print("=" * 60)
    print("[5] 验收")
    ok = True
    if counts.get("STARTED", 0) < 1:
        print("  ❌ 缺 STARTED")
        ok = False
    if counts.get("PROGRESS", 0) < 10:
        print(f"  ⚠️ PROGRESS 只收到 {counts.get('PROGRESS', 0)} 条（期望 ≥ 10）")
        ok = False
    if counts.get("SUCCESS", 0) < 1:
        print("  ❌ 缺 SUCCESS")
        ok = False
    if ok:
        print("  ✅ WS 全流程通过：STARTED → PROGRESS×N → SUCCESS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
