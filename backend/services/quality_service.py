"""
QualityService - 评估服务
"""
import time
import numpy as np
from loguru import logger

from algorithm_model.api import assess_quality


# ===== 预设曲面生成（helper）=====

def make_sphere_surface(n: int = 20, radius: float = 1.0) -> np.ndarray:
    u = np.linspace(0, np.pi, n)
    v = np.linspace(0, 2 * np.pi, n)
    U, V = np.meshgrid(u, v)
    X = radius * np.sin(U) * np.cos(V)
    Y = radius * np.sin(U) * np.sin(V)
    Z = radius * np.cos(U)
    return np.stack([X, Y, Z], axis=-1)


def make_plane_surface(n: int = 20, size: float = 2.0) -> np.ndarray:
    x = np.linspace(-size, size, n)
    y = np.linspace(-size, size, n)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)
    return np.stack([X, Y, Z], axis=-1)


def make_cylinder_surface(n: int = 20, radius: float = 1.0, height: float = 2.0) -> np.ndarray:
    z = np.linspace(0, height, n)
    theta = np.linspace(0, 2 * np.pi, n)
    Z, T = np.meshgrid(z, theta)
    X = radius * np.cos(T)
    Y = radius * np.sin(T)
    return np.stack([X, Y, Z], axis=-1)


def make_car_body_panel(n: int = 20) -> np.ndarray:
    """从默认车身取一块面板"""
    from algorithm_model.api import build_car
    parts = build_car()
    body = parts["body"]
    verts = body.vertices
    if len(verts) < n * n:
        # 退化用平面
        return make_plane_surface(n)
    pts = verts[:n * n].reshape(n, n, 3)
    return pts


class QualityService:
    """曲面质量评估服务（薄壳）"""

    PRESET_MAKERS = {
        "sphere": make_sphere_surface,
        "plane": make_plane_surface,
        "cylinder": make_cylinder_surface,
        "car_body": make_car_body_panel,
    }

    def assess(self, points: list, panel_name: str = "panel") -> dict:
        """
        评估曲面质量
        """
        start = time.time()
        points_arr = np.array(points, dtype=float)

        if points_arr.ndim != 3 or points_arr.shape[2] != 3:
            raise ValueError(f"points 形状必须是 (N, M, 3)，当前 {points_arr.shape}")

        report = assess_quality(points_arr, panel_name)
        elapsed = (time.time() - start) * 1000
        logger.info(f"📊 Quality assessed in {elapsed:.1f}ms → grade={report.grade}")

        return {
            "panel_name": report.panel_name,
            "grade": report.grade,
            "g0_count": report.g0_count,
            "g1_count": report.g1_count,
            "g2_count": report.g2_count,
            "g1_ratio": report.g1_ratio,
            "g2_ratio": report.g2_ratio,
            "max_curvature_jump": report.max_curvature_jump,
            "mean_curvature": report.mean_curvature,
            "reflection_score": report.reflection_score,
            "details": report.details,
        }

    def assess_preset(self, shape: str, resolution: int = 20) -> dict:
        """预设曲面评估"""
        if shape not in self.PRESET_MAKERS:
            raise ValueError(f"shape 必须是 {list(self.PRESET_MAKERS.keys())} 之一")
        points = self.PRESET_MAKERS[shape](resolution)
        return self.assess(points.tolist(), panel_name=shape)
