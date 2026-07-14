"""
G0/G1/G2 连续性判定

工业标准：
- G0: 位置连续（默认所有三角面都满足）
- G1: 切线连续（法向夹角 < 阈值）
- G2: 曲率连续（法向夹角 < 更严格阈值）
"""
import numpy as np
from .curvature import angle_between
from typing import Tuple


def check_g0_g1_g2(
    surface_points: np.ndarray,
    g1_threshold: float = 5.0,
    g2_threshold: float = 2.0,
) -> Tuple[int, int, int, float]:
    """
    评估曲面的 G0/G1/G2 连续性

    Args:
        surface_points: (N, M, 3) 网格点云
        g1_threshold: G1 判定阈值（法向夹角度数），默认 5°
        g2_threshold: G2 判定阈值（更严格），默认 2°

    Returns:
        (g0_count, g1_count, g2_count, max_jump)
        - g0_count: 总三角面数
        - g1_count: 满足 G1 的边数
        - g2_count: 满足 G2 的边数
        - max_jump: 最大法向跳变角度
    """
    from .curvature import estimate_normals
    n, m = surface_points.shape[:2]
    normals = estimate_normals(surface_points)

    g0_count = (n - 1) * (m - 1) * 2
    g1_count = 0
    g2_count = 0
    max_jump = 0.0

    for i in range(n - 1):
        for j in range(m - 1):
            n00 = normals[i, j]
            n10 = normals[i + 1, j]
            n01 = normals[i, j + 1]

            a1 = angle_between(n00, n10)
            a2 = angle_between(n00, n01)

            if a1 < g1_threshold:
                g1_count += 1
            if a2 < g1_threshold:
                g1_count += 1
            if a1 < g2_threshold:
                g2_count += 1
            if a2 < g2_threshold:
                g2_count += 1
            max_jump = max(max_jump, a1, a2)

    return g0_count, g1_count, g2_count, max_jump
