# cython: boundscheck=False, wraparound=False, cdivision=True
# distutils: language = c
"""
曲面质量评估 Cython 加速内核

优化项：
- estimate_normals_fast: 向量化法向量估算（numpy cross + Cython 归一化）
- compute_reflection_score_fast: 向量化角度计算 + C 层统计

性能目标：50x50 反射线评分从 102ms → <3ms
"""

import numpy as np
cimport numpy as cnp
from libc.math cimport sqrt, fabs, atan2, acos, M_PI
from numpy cimport ndarray

cnp.import_array()

ctypedef cnp.float64_t DTYPE_t


# ─────────────────── 法向量快速估算 ───────────────────

def estimate_normals_fast(ndarray[DTYPE_t, ndim=3] surface_points):
    """
    向量化法向量估算（Cython 加速版）

    内部使用 numpy cross product 计算所有三角形法向（一次 C 调用），
    然后在 Cython 中做面积加权平均和归一化。

    Args:
        surface_points: (N, M, 3) 网格点云

    Returns:
        (N, M, 3) 单位法向量
    """
    cdef:
        int N = surface_points.shape[0]
        int M = surface_points.shape[1]
        ndarray[DTYPE_t, ndim=3] normals = np.zeros((N, M, 3), dtype=np.float64)

        # 用 numpy 向量化计算三角形法向
        ndarray[DTYPE_t, ndim=3] d1a, d2a, d1b, d2b
        ndarray[DTYPE_t, ndim=3] t1, t2, n_avg
        ndarray[DTYPE_t, ndim=2] norms
        int i, j

    # 三角形 1: cross(P[i+1,j]-P[i,j], P[i+1,j+1]-P[i,j])
    d1a = surface_points[1:N-1, 1:M-1, :]   # P[i,j]
    d2a = surface_points[2:N, 1:M-1, :] - d1a  # P[i+1,j] - P[i,j]
    d1b = surface_points[2:N, 2:M, :] - d1a    # P[i+1,j+1] - P[i,j]
    t1 = np.cross(d2a, d1b)  # 全部三角形1的法向

    # 三角形 2: cross(P[i+1,j+1]-P[i,j+1], P[i,j]-P[i,j+1])
    d1a = surface_points[1:N-1, 2:M, :]    # P[i,j+1]
    d2a = surface_points[2:N, 2:M, :] - d1a    # P[i+1,j+1] - P[i,j+1]
    d1b = surface_points[1:N-1, 1:M-1, :] - d1a  # P[i,j] - P[i,j+1]
    t2 = np.cross(d2a, d1b)

    # 面积加权平均
    n_avg = (t1 + t2) / 2.0

    # 归一化 (C 层循环)
    for i in range(N - 2):
        for j in range(M - 2):
            norms_val = sqrt(
                n_avg[i, j, 0] * n_avg[i, j, 0]
                + n_avg[i, j, 1] * n_avg[i, j, 1]
                + n_avg[i, j, 2] * n_avg[i, j, 2]
            )
            if norms_val > 1e-9:
                normals[i + 1, j + 1, 0] = n_avg[i, j, 0] / norms_val
                normals[i + 1, j + 1, 1] = n_avg[i, j, 1] / norms_val
                normals[i + 1, j + 1, 2] = n_avg[i, j, 2] / norms_val
            else:
                normals[i + 1, j + 1, 0] = 0.0
                normals[i + 1, j + 1, 1] = 0.0
                normals[i + 1, j + 1, 2] = 1.0

    return normals


# ─────────────────── 反射线评分快速版 ──────────────────

def compute_reflection_score_fast(ndarray[DTYPE_t, ndim=3] surface_points):
    """
    反射线评分（Cython 加速版）

    1. 法向量用 numpy cross product 向量化
    2. 角度计算用 numpy 向量化（dot product + arccos）
    3. 统计量在 C 层计算

    Args:
        surface_points: (N, M, 3) 网格点云

    Returns:
        float 评分 [0, 1]
    """
    cdef:
        int N = surface_points.shape[0]
        int M = surface_points.shape[1]
        int nm, idx
        double curv_std, curv_mean, uniformity, smoothness
        double max_jump
        ndarray[DTYPE_t, ndim=3] normals
        ndarray[DTYPE_t, ndim=2] dot_u, dot_v
        ndarray[DTYPE_t, ndim=2] angle_u, angle_v

    if N < 2 or M < 2:
        return 0.0

    # Step 1: 法向量（向量化）
    normals = estimate_normals_fast(surface_points)

    # Step 2: 法向夹角（向量化）
    # 内积 + arccos
    dot_u = np.sum(normals[:N-1, :M-1, :] * normals[1:N, :M-1, :], axis=2)
    dot_v = np.sum(normals[:N-1, :M-1, :] * normals[:N-1, 1:M, :], axis=2)

    np.clip(dot_u, -1.0, 1.0, out=dot_u)
    np.clip(dot_v, -1.0, 1.0, out=dot_v)

    angle_u = np.degrees(np.arccos(dot_u))  # (N-1, M-1)
    angle_v = np.degrees(np.arccos(dot_v))  # (N-1, M-1)

    # Step 3: 统计量
    nm = (N - 1) * (M - 1)
    max_jump = float(np.maximum(angle_u.max(), angle_v.max()))
    curv_mean = float(np.mean((angle_u + angle_v) / 2.0))
    curv_std = float(np.std((angle_u + angle_v) / 2.0))

    uniformity = 1.0 / (1.0 + curv_std / max(0.1, curv_mean))
    smoothness = 1.0 / (1.0 + max_jump / 10.0)

    return 0.5 * uniformity + 0.5 * smoothness
