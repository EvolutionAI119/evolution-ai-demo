"""
反射线评分模块

模拟反射光带在曲面上的扫描效果：
- 反射线越平滑（曲率均匀）→ 评分越高
- 反射线越抖动（曲率突变）→ 评分越低

评分公式：
- uniformity = 1 / (1 + 曲率标准差 / 曲率均值)
- smoothness = 1 / (1 + 最大跳变 / 10)
- reflection_score = 0.5 * uniformity + 0.5 * smoothness
"""
import numpy as np
from typing import List
from .curvature import angle_between, estimate_normals

# Cython 加速缓存
_cy_reflect = None


def compute_reflection_score(surface_points: np.ndarray) -> float:
    """
    计算反射线评分 [0, 1]（自动使用 Cython 加速，如可用）

    Args:
        surface_points: (N, M, 3) 网格点云

    Returns:
        评分 [0, 1]，越接近 1 越光顺
    """
    # 优先使用 Cython 加速版（带模块级缓存）
    global _cy_reflect
    if _cy_reflect is None:
        try:
            from ._quality_cy import compute_reflection_score_fast as _cy_reflect
        except ImportError:
            _cy_reflect = False
    if _cy_reflect:
        return _cy_reflect(np.ascontiguousarray(surface_points, dtype=np.float64))

    # 纯 Python fallback
    n, m = surface_points.shape[:2]
    if n < 2 or m < 2:
        return 0.0
    normals = estimate_normals(surface_points)

    curvature_values: List[float] = []
    max_jump = 0.0
    for i in range(n - 1):
        for j in range(m - 1):
            a1 = angle_between(normals[i, j], normals[i + 1, j])
            a2 = angle_between(normals[i, j], normals[i, j + 1])
            curvature_values.append((a1 + a2) / 2)
            max_jump = max(max_jump, a1, a2)

    if not curvature_values:
        return 0.0

    curv_std = float(np.std(curvature_values))
    curv_mean = float(np.mean(curvature_values))
    uniformity = 1.0 / (1.0 + curv_std / max(0.1, curv_mean))
    smoothness = 1.0 / (1.0 + max_jump / 10.0)
    return 0.5 * uniformity + 0.5 * smoothness
