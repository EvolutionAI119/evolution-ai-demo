"""OptimizeService - AI 优化服务（M2 升级：同步 + 异步双接口）。

- 同步（optimize / optimize_preset）：M1 接口保留
- 异步（start_async）：M2 新增，写 DB + 推 Celery，立即返回 task_id
"""
import time
import uuid
from typing import Optional

import numpy as np
from loguru import logger
from sqlalchemy.orm import Session

from backend.algorithm_compat import optimize_surface
from backend.db import OptimizationTask, TaskStatus
from backend.services.quality_service import (
    make_car_body_panel,
    make_cylinder_surface,
    make_plane_surface,
    make_sphere_surface,
)


def make_plane_with_noise(n: int = 20, noise_level: float = 0.05, seed: int = 42) -> np.ndarray:
    """带高斯噪声的平面（优化效果最显著的演示用例）。"""
    rng = np.random.default_rng(seed)
    plane = make_plane_surface(n)
    plane += rng.normal(0, noise_level, plane.shape)
    return plane


class OptimizeService:
    """AI 优化服务（同步 + 异步双接口）。"""

    PRESET_MAKERS = {
        "sphere": lambda n=20: make_sphere_surface(n),
        "plane_with_noise": lambda n=20: make_plane_with_noise(n),
        "cylinder": lambda n=20: make_cylinder_surface(n),
        "car_body": lambda n=20: make_car_body_panel(n),
    }

    # ==================== 同步（M1 保留） ====================

    def optimize(
        self,
        points: list,
        panel_name: str = "panel",
        max_iter: int = 80,
        seed: int = 42,
    ) -> dict:
        """同步优化（M1 兼容接口，5s+ 会阻塞）。"""
        start = time.time()
        points_arr = np.array(points, dtype=float)
        if points_arr.ndim != 3 or points_arr.shape[2] != 3:
            raise ValueError(f"points 形状必须是 (N, M, 3)，当前 {points_arr.shape}")
        logger.info(f"🎯 [sync] Start optimize: {panel_name} (max_iter={max_iter})")
        result = optimize_surface(points_arr, panel_name, max_iter, seed)
        elapsed = time.time() - start
        improvement = result.final_g2 - result.initial_g2
        logger.info(
            f"✅ [sync] Optimized in {elapsed:.2f}s: "
            f"{result.initial_grade} → {result.final_grade}, g2 Δ={improvement:+d}"
        )
        return {
            "task_id": uuid.uuid4().hex[:16],
            "panel_name": panel_name,
            "initial_grade": result.initial_grade,
            "final_grade": result.final_grade,
            "initial_g2_count": result.initial_g2,
            "final_g2_count": result.final_g2,
            "initial_reflection": result.initial_reflection,
            "final_reflection": result.final_reflection,
            "improvement": improvement,
            "iterations": result.iterations,
            "elapsed_seconds": round(elapsed, 3),
            "convergence_curve": result.convergence_curve,
            "optimized_points": result.best_surface.tolist() if result.best_surface is not None else None,
        }

    def optimize_preset(self, shape: str, max_iter: int = 80, seed: int = 42) -> dict:
        """预设曲面同步优化。"""
        if shape not in self.PRESET_MAKERS:
            raise ValueError(f"shape 必须是 {list(self.PRESET_MAKERS.keys())} 之一")
        points = self.PRESET_MAKERS[shape](20)
        return self.optimize(points.tolist(), panel_name=shape, max_iter=max_iter, seed=seed)

    # ==================== 异步（M2 新增） ====================

    def start_async(
        self,
        db: Session,
        panel_name: str,
        surface_type: str = "custom",
        max_iter: int = 80,
        seed: int = 42,
        project_id: Optional[int] = None,
        initial_params: Optional[dict] = None,
    ) -> OptimizationTask:
        """创建任务记录 + 推 Celery，立即返回 task_id。

        Args:
            surface_type: sphere / plane / cylinder / car_body / custom
        """
        from backend.tasks.optimize_task import run_optimize_task

        if surface_type not in ("sphere", "plane", "cylinder", "car_body", "custom"):
            raise ValueError(f"surface_type 必须是 sphere/plane/cylinder/car_body/custom 之一")

        task_id = uuid.uuid4().hex
        task = OptimizationTask(
            task_id=task_id,
            project_id=project_id,
            panel_name=panel_name,
            surface_type=surface_type,
            max_iter=max_iter,
            initial_params_json=str(initial_params) if initial_params else None,
            status=TaskStatus.PENDING,
            progress=0.0,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 推 Celery（broker 不可用时 degrade 到同步执行）
        try:
            run_optimize_task.delay(task_id, panel_name, surface_type, max_iter, seed)
            logger.info(f"🚀 [{task_id}] Async optimize queued: {panel_name} (max_iter={max_iter})")
        except Exception as e:  # noqa: BLE001
            # Redis 不可用 → degrade
            logger.warning(f"⚠️ Celery 推送失败，degrade 到同步执行: {e}")
            try:
                run_optimize_task.apply(args=[task_id, panel_name, surface_type, max_iter, seed])
            except Exception as e2:  # noqa: BLE001
                logger.error(f"❌ 同步 fallback 也失败: {e2}")
                task.status = TaskStatus.FAILURE
                task.error_message = f"celery={e}; sync={e2}"
                db.commit()
                raise

        return task

    def start_preset_async(
        self,
        db: Session,
        shape: str,
        max_iter: int = 80,
        project_id: Optional[int] = None,
    ) -> OptimizationTask:
        """预设曲面异步优化。"""
        if shape not in self.PRESET_MAKERS:
            raise ValueError(f"shape 必须是 {list(self.PRESET_MAKERS.keys())} 之一")
        # shape 名字直接当 surface_type 传（plane_with_noise 映射为 plane，car_body 映射为 car_body）
        surface_type_map = {
            "sphere": "sphere",
            "plane_with_noise": "plane",
            "cylinder": "cylinder",
            "car_body": "car_body",
        }
        return self.start_async(
            db=db,
            panel_name=shape,
            surface_type=surface_type_map[shape],
            max_iter=max_iter,
            project_id=project_id,
        )
