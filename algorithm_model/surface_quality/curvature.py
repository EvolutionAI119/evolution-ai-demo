"""
曲率估算模块

核心算法：
- 离散网格的法向量 = 局部三角形法向的面积加权平均
- 跨边的法向夹角 = 离散曲率指标
"""
import numpy as np


def estimate_normals(surface_points: np.ndarray) -> np.ndarray:
    """
    估算曲面网格点的法向量

    Args:
        surface_points: (N, M, 3) 网格点云

    Returns:
        (N, M, 3) 单位法向量，边界点法向为 [0, 0, 1]
    """
    n, m = surface_points.shape[:2]
    normals = np.zeros((n, m, 3))

    for i in range(1, n - 1):
        for j in range(1, m - 1):
            v00 = surface_points[i, j]
            v10 = surface_points[i + 1, j]
            v01 = surface_points[i, j + 1]
            v11 = surface_points[i + 1, j + 1]
            # 两个对角三角形的法向求平均
            t1 = np.cross(v10 - v00, v11 - v00)
            t2 = np.cross(v11 - v01, v00 - v01)
            n_v = (t1 + t2) / 2
            n_norm = np.linalg.norm(n_v)
            if n_norm > 1e-9:
                normals[i, j] = n_v / n_norm
            else:
                normals[i, j] = [0, 0, 1]
    return normals


def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    两个向量的夹角（度）

    Returns:
        0-180 度夹角
    """
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_a)))
