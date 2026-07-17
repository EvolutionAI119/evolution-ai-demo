"""M2.5 car_body bug 修复 E2E。

Bug 链路：
  旧 _make_surface("car_body") → (N, 3) 散点 → estimate_normals 把 m=3 当 M → 越界
  "At least one array has zero dimension"

修复：
  _make_surface("car_body") → body.vertices[:49*48].reshape(49, 48, 3) → 正常网格

E2E 范围：
  T1 _make_surface 4 shape 输出都是 3D
  T2 car_body 异步任务走通 → SUCCESS（不再 FAILURE）
  T3 收敛曲线 11 个点 + g2/反射线 数字合理
  T4 sphere / plane / cylinder 4 shape 异步回归（确保 car_body 修复没破其他 shape）
  T5 body 散点结构对账（49×48=2352 验证）

注意：car_body 因散点无序问题 grade=D 是 W2-D1 的活（KDTree 重排），
本 E2E 只验"算法层不报 zero dimension"+"任务能跑完"。
"""
import json
import sys
import time
import urllib.request

from backend.tasks.optimize_task import _make_surface
import numpy as np

API = "http://127.0.0.1:8000"


def post(path: str, payload: dict, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get(path: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=timeout) as r:
        return json.loads(r.read())


def wait_task(task_id: str, max_sec: int = 30) -> dict:
    """轮询 task status，返回最终结果 dict。"""
    for i in range(max_sec):
        time.sleep(1)
        d = get(f"/api/v1/task/{task_id}")
        if d["status"] in ("SUCCESS", "FAILURE"):
            return d
        print(f"    t={i+1}s status={d['status']}")
    raise TimeoutError(f"task {task_id} not finish in {max_sec}s")


def main() -> int:
    passed, failed = 0, 0

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"  ✅ {name}{(' — ' + detail) if detail else ''}")
        else:
            failed += 1
            print(f"  ❌ {name}{(' — ' + detail) if detail else ''}")

    print("=" * 60)
    print("T1 _make_surface 4 shape 输出都是 3D 网格")
    print("=" * 60)
    for shape in ("sphere", "plane", "cylinder", "car_body"):
        try:
            arr = _make_surface(shape)
            ok = arr.ndim == 3 and arr.shape[2] == 3
            check(
                f"_make_surface({shape!r}) ndim=3",
                ok,
                f"shape={arr.shape}",
            )
        except Exception as e:
            check(f"_make_surface({shape!r})", False, f"raised {e!r}")

    # T1.1 car_body 必须是 (49, 48, 3)
    cb = _make_surface("car_body")
    check(
        "car_body reshape 后是 (49, 48, 3)",
        cb.shape == (49, 48, 3),
        f"actual={cb.shape}",
    )

    # T1.2 body.vertices 散点对账
    from backend.algorithm_compat import build_car
    body = build_car(None)["body"]
    body_n = np.array(body.vertices).shape[0]
    check(
        "body 顶点数 = 49×48 = 2352",
        body_n == 2352,
        f"body_n={body_n}, 49*48=2352",
    )

    print()
    print("=" * 60)
    print("T2 car_body 异步任务 → SUCCESS（修 bug 核心）")
    print("=" * 60)
    try:
        r = post("/api/v1/optimize/start-preset", {"shape": "car_body", "max_iter": 10})
        task_id = r["task_id"]
        print(f"  task_id={task_id}")
        result = wait_task(task_id, max_sec=30)
        check(
            "car_body 异步 status=SUCCESS",
            result["status"] == "SUCCESS",
            f"actual={result['status']}",
        )
        if result["status"] == "SUCCESS":
            res = result["result"]
            check(
                "有 initial_grade + final_grade",
                "initial_grade" in res and "final_grade" in res,
                f"{res['initial_grade']}→{res['final_grade']}",
            )
            check(
                "g2 数字合理 (initial_g2 > 0)",
                res["initial_g2"] > 0 and res["final_g2"] > 0,
                f"g2 {res['initial_g2']}→{res['final_g2']}",
            )
            check(
                "convergence_curve 11 个点（10 iter + 1 initial）",
                len(res["convergence_curve"]) == 11,
                f"len={len(res['convergence_curve'])}",
            )
            check(
                "optimized_points 是 (49, 48, 3) 网格",
                np.array(res["optimized_points"]).shape == (49, 48, 3),
                f"shape={np.array(res['optimized_points']).shape}",
            )
            # 不报 "zero dimension" 错
            check(
                'error_message 不含 "zero dimension"',
                "zero dimension" not in (result.get("error_message") or ""),
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        check("car_body 异步任务", False, str(e))

    print()
    print("=" * 60)
    print("T3 / T4 其他 3 shape 异步回归（确保 car_body 修复没破其他）")
    print("=" * 60)
    for shape in ("sphere", "plane_with_noise", "cylinder"):
        try:
            r = post("/api/v1/optimize/start-preset", {"shape": shape, "max_iter": 10})
            task_id = r["task_id"]
            result = wait_task(task_id, max_sec=20)
            check(
                f"{shape} 异步 SUCCESS",
                result["status"] == "SUCCESS",
                f"status={result['status']}",
            )
        except Exception as e:
            check(f"{shape} 异步回归", False, str(e))

    print()
    print("=" * 60)
    print(f"总计: {passed} ✅ / {failed} ❌")
    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
