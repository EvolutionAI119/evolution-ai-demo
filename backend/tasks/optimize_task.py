"""AI 曲面优化异步任务。

调用 algorithm_model.api.optimize_surface（一次性同步执行），写回 DB。
中间进度通过 Redis Pub/Sub 推到 M2.5 WebSocket（M2 只用 Celery 状态机）。
"""
import json
import time
from datetime import datetime
from typing import Any

import numpy as np

from backend.db import OptimizationTask, SessionLocal, TaskStatus
from backend.tasks.celery_app import celery_app
from backend.utils.redis_pubsub import publish_progress, replay_convergence_curve


def _make_surface(surface_type: str, n: int = 20) -> np.ndarray:
    """根据 surface_type 构造初始 (N, M, 3) 网格。

    注意：algorithm_model.api.optimize_surface 要求 (N, M, 3) 三维形状。
    """
    if surface_type == "sphere":
        u = np.linspace(0, np.pi, n)
        v = np.linspace(0, 2 * np.pi, n)
        U, V = np.meshgrid(u, v)
        return np.stack(
            [np.sin(U) * np.cos(V), np.sin(U) * np.sin(V), np.cos(U)], axis=-1
        )
    if surface_type == "plane":
        rng = np.random.default_rng(42)
        u = np.linspace(-1, 1, n)
        v = np.linspace(-1, 1, n)
        U, V = np.meshgrid(u, v)
        Z = 0.05 * rng.standard_normal((n, n))
        return np.stack([U, V, Z], axis=-1)
    if surface_type == "cylinder":
        u = np.linspace(0, 2 * np.pi, n)
        v = np.linspace(-1, 1, n)
        U, V = np.meshgrid(u, v)
        return np.stack([np.cos(U), np.sin(U), V], axis=-1)
    if surface_type == "car_body":
        # 调用 algorithm_model 的 build_car 取侧围面板（build_car 默认参数就是 CarParams()）
        # build_car 返回 Dict[str, Trimesh]，取 body 部件的 vertices
        from backend.algorithm_compat import build_car

        parts = build_car(None)  # None → 用默认 CarParams()
        # 找车身主体，取其顶点 (N, 3)
        body_arr: np.ndarray | None = None
        for k in ("body", "side_panel", "left_side", "body_side", "side"):
            if k in parts:
                tm = parts[k]
                if hasattr(tm, "vertices"):
                    arr = np.array(tm.vertices)
                    if arr.ndim == 2 and arr.shape[1] == 3:
                        body_arr = arr
                        break
        # 兜底：取第一个有 vertices 的三维部件
        if body_arr is None:
            for v in parts.values():
                if hasattr(v, "vertices"):
                    arr = np.array(v.vertices)
                    if arr.ndim == 2 and arr.shape[1] == 3:
                        body_arr = arr
                        break
        if body_arr is None:
            raise ValueError("car_body 构建无 (N, 3) 部件")
        # algorithm_model 算法层（estimate_normals / check_g0_g1_g2 / compute_reflection_score）
        # 要求输入是规则网格 (N, M, 3)，车身默认是 49（X 长向）× 48（Y 圆周向）= 2352 散点。
        # 直接 reshape：与 run_full_pipeline 内部（49, 25）保持一致只用前 N*M 个点对齐为网格。
        n_long, n_circ = 49, 48
        if body_arr.shape[0] < n_long * n_circ:
            # 退化：兜不住 49×48 时按最长规则方阵铺
            side = int(np.sqrt(body_arr.shape[0]))
            n_long, n_circ = side, side
        return body_arr[: n_long * n_circ].reshape(n_long, n_circ, 3)
    raise ValueError(f"unknown surface_type: {surface_type}")


@celery_app.task(bind=True, name="backend.tasks.optimize_task.run_optimize_task")
def run_optimize_task(
    self,
    task_id: str,
    panel_name: str,
    surface_type: str,
    max_iter: int,
    seed: int = 42,
) -> dict:
    """执行 AI 优化，并把结果写回 DB。

    返回：{"task_id", "status", "elapsed_sec", "result" (dict)}
    """
    from backend.algorithm_compat import optimize_surface

    # 1. 状态 → STARTED
    db = SessionLocal()
    try:
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        if not task:
            return {"error": f"task {task_id} not found"}
        task.status = TaskStatus.STARTED
        task.started_at = datetime.utcnow()
        task.progress = 0.05  # 标记已启动
        db.commit()
    finally:
        db.close()

    # M2.5: WS STARTED 推送
    publish_progress(
        task_id,
        {
            "type": "STARTED",
            "progress": 0.05,
            "current_iter": 0,
            "max_iter": max_iter,
        },
    )

    # 2. 构造初始曲面
    try:
        points = _make_surface(surface_type)
    except Exception as e:  # noqa: BLE001
        _mark_failure(task_id, f"surface construction failed: {e}")
        raise

    # 3. 执行优化（算法层无 progress_cb，一次性跑完）
    start = time.time()
    try:
        result = optimize_surface(points, panel_name, max_iter, seed)
        elapsed = time.time() - start

        # 4. 写回 SUCCESS
        result_dict = {
            "initial_grade": result.initial_grade,
            "final_grade": result.final_grade,
            "initial_g2": result.initial_g2,
            "final_g2": result.final_g2,
            "initial_reflection": result.initial_reflection,
            "final_reflection": result.final_reflection,
            "iterations": result.iterations,
            "convergence_curve": result.convergence_curve,
            "elapsed_sec": elapsed,
        }
        # best_surface 是 ndarray，序列化为 list
        if result.best_surface is not None:
            result_dict["optimized_points"] = result.best_surface.tolist()

        db = SessionLocal()
        try:
            task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
            if task:
                task.status = TaskStatus.SUCCESS
                task.progress = 1.0
                task.current_iter = max_iter
                task.finished_at = datetime.utcnow()
                task.result_json = json.dumps(result_dict, default=str)
                db.commit()
        finally:
            db.close()

        # M2.5: 回放 31 个进度点（0.1s × 31 = 3.1s，与 M2 端到端时延对齐）
        replay_convergence_curve(
            task_id,
            result.convergence_curve or [],
            max_iter=max_iter,
            interval_sec=0.1,
        )

        # M2.5: WS SUCCESS 推送
        publish_progress(
            task_id,
            {
                "type": "SUCCESS",
                "progress": 1.0,
                "current_iter": result.iterations,
                "max_iter": max_iter,
                "best_score": float(result.convergence_curve[-1]) if result.convergence_curve else None,
                "elapsed_sec": elapsed,
                "initial_grade": result.initial_grade,
                "final_grade": result.final_grade,
            },
        )

        return {"task_id": task_id, "status": "SUCCESS", "elapsed_sec": elapsed, "result": result_dict}

    except Exception as e:  # noqa: BLE001
        _mark_failure(task_id, str(e))
        # M2.5: WS FAILURE 推送
        publish_progress(task_id, {"type": "FAILURE", "error": str(e)})
        raise


def _mark_failure(task_id: str, error_message: str) -> None:
    db = SessionLocal()
    try:
        task = db.query(OptimizationTask).filter(OptimizationTask.task_id == task_id).first()
        if task:
            task.status = TaskStatus.FAILURE
            task.error_message = error_message
            task.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
