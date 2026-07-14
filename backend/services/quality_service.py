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


    def reflection_map(self, points: list, light_direction: list = None) -> dict:
        """
        生成反射线可视化数据

        Returns:
            dict with vertices, normals, curvature, reflection_intensity, reflection_score, indices
        """
        from algorithm_model.surface_quality.curvature import estimate_normals, angle_between

        if light_direction is None:
            light_direction = [0.0, 0.0, 1.0]

        pts = np.array(points, dtype=np.float64)
        if pts.ndim != 3 or pts.shape[2] != 3:
            raise ValueError(f"points 形状必须是 (N, M, 3)，当前 {pts.shape}")

        N, M = pts.shape[:2]
        if N < 2 or M < 2:
            raise ValueError("points 至少需要 2x2")

        # 1. 法向量
        normals = estimate_normals(pts)

        # 2. 曲率（相邻法向夹角均值）
        curvature = np.zeros((N, M), dtype=np.float64)
        for i in range(1, N - 1):
            for j in range(1, M - 1):
                a_u = angle_between(normals[i, j], normals[i + 1, j]) if i + 1 < N else 0
                a_d = angle_between(normals[i, j], normals[i - 1, j]) if i - 1 >= 0 else 0
                a_r = angle_between(normals[i, j], normals[i, j + 1]) if j + 1 < M else 0
                a_l = angle_between(normals[i, j], normals[i, j - 1]) if j - 1 >= 0 else 0
                curvature[i, j] = (a_u + a_d + a_r + a_l) / 4.0

        # 3. 反射光强度 = |dot(normal, light_dir)|
        L = np.array(light_direction, dtype=np.float64)
        L = L / (np.linalg.norm(L) + 1e-12)
        # 对每个网格点计算反射强度
        reflection_intensity = np.zeros((N, M), dtype=np.float64)
        for i in range(N):
            for j in range(M):
                n = normals[i, j]
                n_norm = np.linalg.norm(n)
                if n_norm > 1e-9:
                    reflection_intensity[i, j] = abs(np.dot(n / n_norm, L))
                else:
                    reflection_intensity[i, j] = 0.0

        # 4. 反射线评分
        from algorithm_model.surface_quality.reflection import compute_reflection_score
        score = compute_reflection_score(pts)

        # 5. 构建三角形索引
        indices = []
        for i in range(N - 1):
            for j in range(M - 1):
                v00 = i * M + j
                v10 = (i + 1) * M + j
                v01 = i * M + (j + 1)
                v11 = (i + 1) * M + (j + 1)
                indices.extend([v00, v10, v01, v10, v11, v01])

        # 6. flatten
        verts_flat = pts.reshape(-1, 3).tolist()
        norms_flat = normals.reshape(-1, 3).tolist()
        curv_flat = curvature.reshape(-1).tolist()
        refl_flat = reflection_intensity.reshape(-1).tolist()

        return {
            "n": N,
            "m": M,
            "vertices": verts_flat,
            "normals": norms_flat,
            "curvature": curv_flat,
            "reflection_intensity": refl_flat,
            "reflection_score": score,
            "indices": indices,
        }
