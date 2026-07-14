# cython: boundscheck=False, wraparound=False, cdivision=True
# distutils: language = c
"""
NURBS Cython 加速内核

向量化批处理：
- find_span_batch: 对 N 个参数值批量查找节点区间
- basis_funs_batch: 对 N 个参数值批量计算基函数
- evaluate_surface_mesh_fast: 利用 tensor-product 结构，
  仅计算 n_u 个 u 基函数 + n_v 个 v 基函数，
  然后 O(n_u*n_v) 张量累加

性能目标：100x100 网格从 344ms → <5ms（~70x 加速）
"""

import numpy as np
cimport numpy as cnp
from libc.math cimport fabs, sqrt

cnp.import_array()

ctypedef cnp.float64_t DTYPE_t


# ─────────────────────── 单点函数（C 级别，nogil） ───────────────────────

cdef int find_span_c(int n, int p, double u, double* U) noexcept nogil:
    """二分查找节点区间索引"""
    cdef int low, high, mid
    if u >= U[n + 1]:
        return n
    if u <= U[p]:
        return p
    low = p
    high = n + 1
    mid = (low + high) // 2
    while u < U[mid] or u >= U[mid + 1]:
        if u < U[mid]:
            high = mid
        else:
            low = mid
        mid = (low + high) // 2
    return mid


cdef void basis_funs_c(int i, double u, int p, double* U,
                        double* N) noexcept nogil:
    """三角表算法计算 p+1 个非零基函数值 (Piegl & Tiller A2.2)"""
    cdef:
        double left[8]
        double right[8]
        double saved, temp
        int j, r
    N[0] = 1.0
    for j in range(1, p + 1):
        left[j] = u - U[i + 1 - j]
        right[j] = U[i + j] - u
        saved = 0.0
        for r in range(j):
            temp = N[r] / (right[r + 1] + left[j - r])
            N[r] = saved + right[r + 1] * temp
            saved = left[j - r] * temp
        N[j] = saved


# ─────────────── 批量函数（Python 可调用，内部 nogil） ──────────────────

def find_span_batch(int n, int p, cnp.ndarray[DTYPE_t, ndim=1] u_vals,
                    cnp.ndarray[DTYPE_t, ndim=1] U):
    """
    批量查找节点区间

    Args:
        n: 控制点数 - 1
        p: 次数
        u_vals: (N,) 参数值数组
        U: 节点向量

    Returns:
        (N,) int32 节点区间索引
    """
    cdef:
        Py_ssize_t N = u_vals.shape[0]
        cnp.ndarray spans = np.empty(N, dtype=np.int32)
        int* spans_data = <int*>spans.data
        double* u_data = <double*>u_vals.data
        double* U_data = <double*>U.data
        Py_ssize_t idx

    with nogil:
        for idx in range(N):
            spans_data[idx] = find_span_c(n, p, u_data[idx], U_data)
    return spans


def basis_funs_batch(int p,
                     cnp.ndarray[DTYPE_t, ndim=1] u_vals,
                     cnp.ndarray[int, ndim=1] spans,
                     cnp.ndarray[DTYPE_t, ndim=1] U):
    """
    批量计算基函数值

    Args:
        p: 次数
        u_vals: (N,) 参数值
        spans: (N,) 节点区间索引（来自 find_span_batch）
        U: 节点向量

    Returns:
        (N, p+1) 基函数值矩阵
    """
    cdef:
        Py_ssize_t N = u_vals.shape[0]
        cnp.ndarray[DTYPE_t, ndim=2] N_arr = np.zeros((N, p + 1), dtype=np.float64)
        double* u_data = <double*>u_vals.data
        int* span_data = <int*>spans.data
        double* U_data = <double*>U.data
        Py_ssize_t idx

    with nogil:
        for idx in range(N):
            basis_funs_c(span_data[idx], u_data[idx], p, U_data, &N_arr[idx, 0])
    return N_arr


# ─────────────── 核心：张量积曲面网格快速求值 ──────────────────────────

def evaluate_surface_mesh_fast(surf, int n_u_eval, int n_v_eval):
    """
    NURBS 曲面网格快速求值（Cython 加速版）

    核心优化：利用 tensor-product 结构
    - 仅计算 n_u_eval 个 u 基函数 + n_v_eval 个 v 基函数（而非 n_u*n_v 次）
    - 张量累加在 C 层完成，零 Python 开销

    Args:
        surf: nurbs_surface_from_grid 返回的 dict
        n_u_eval: u 方向采样数
        n_v_eval: v 方向采样数

    Returns:
        (points, params)
        - points: (n_u_eval*n_v_eval, 3)
        - params: (n_u_eval*n_v_eval, 2)
    """
    cdef:
        int n_p = surf['n'][0]
        int n_q = surf['n'][1]
        int p = surf['degree'][0]
        int q = surf['degree'][1]
        int d = surf['control_points'].shape[2]

        cnp.ndarray[DTYPE_t, ndim=3] P = np.ascontiguousarray(
            surf['control_points'], dtype=np.float64)
        cnp.ndarray[DTYPE_t, ndim=2] w = np.ascontiguousarray(
            surf['weights'], dtype=np.float64)
        cnp.ndarray[DTYPE_t, ndim=1] U = np.ascontiguousarray(
            surf['knots_u'], dtype=np.float64)
        cnp.ndarray[DTYPE_t, ndim=1] V = np.ascontiguousarray(
            surf['knots_v'], dtype=np.float64)

        cnp.ndarray[DTYPE_t, ndim=1] u_vals = np.linspace(0, 1, n_u_eval)
        cnp.ndarray[DTYPE_t, ndim=1] v_vals = np.linspace(0, 1, n_v_eval)

        # 输出数组
        cnp.ndarray[DTYPE_t, ndim=2] points = np.empty(
            (n_u_eval * n_v_eval, d), dtype=np.float64)
        cnp.ndarray[DTYPE_t, ndim=2] params = np.empty(
            (n_u_eval * n_v_eval, 2), dtype=np.float64)

        # 基函数缓存
        cnp.ndarray[DTYPE_t, ndim=2] Nu = np.zeros((n_u_eval, p + 1), dtype=np.float64)
        cnp.ndarray[DTYPE_t, ndim=2] Nv = np.zeros((n_v_eval, q + 1), dtype=np.float64)
        cnp.ndarray[int, ndim=1] spans_u = np.empty(n_u_eval, dtype=np.int32)
        cnp.ndarray[int, ndim=1] spans_v = np.empty(n_v_eval, dtype=np.int32)

        # C 指针
        double* u_data = <double*>u_vals.data
        double* v_data = <double*>v_vals.data
        double* U_data = <double*>U.data
        double* V_data = <double*>V.data
        int* su_data = <int*>spans_u.data
        int* sv_data = <int*>spans_v.data
        double* P_data = <double*>P.data
        double* w_data = <double*>w.data
        double* pts_data = <double*>points.data
        double* prm_data = <double*>params.data

        # 循环变量
        Py_ssize_t i, j, ki, kj, idx, dd
        int span_i, span_j
        double basis, w_ij, bw
        double numerator[3]
        double denominator
        # 内存 stride（C-contiguous: shape (n_u, n_v, d)）
        int stride_w = n_q + 1   # = n_v，权重数组第二维长度
        int stride_P = (n_q + 1) * d  # = n_v * d，控制点中间维 stride

    # ── Step 1: 批量计算 u 方向基函数 ──
    with nogil:
        for i in range(n_u_eval):
            su_data[i] = find_span_c(n_p, p, u_data[i], U_data)
            basis_funs_c(su_data[i], u_data[i], p, U_data, &Nu[i, 0])

    # ── Step 2: 批量计算 v 方向基函数 ──
    with nogil:
        for j in range(n_v_eval):
            sv_data[j] = find_span_c(n_q, q, v_data[j], V_data)
            basis_funs_c(sv_data[j], v_data[j], q, V_data, &Nv[j, 0])

    # ── Step 3: 张量积累加（零 Python 调用） ──
    with nogil:
        for i in range(n_u_eval):
            span_i = su_data[i]
            for j in range(n_v_eval):
                span_j = sv_data[j]
                idx = i * n_v_eval + j

                # 参数坐标
                prm_data[idx * 2] = u_data[i]
                prm_data[idx * 2 + 1] = v_data[j]

                # 有理求值: C = Σ(Ni·Nj·w·P) / Σ(Ni·Nj·w)
                for dd in range(d):
                    numerator[dd] = 0.0
                denominator = 0.0

                for kj in range(q + 1):
                    for ki in range(p + 1):
                        basis = Nu[i, ki] * Nv[j, kj]
                        w_ij = w_data[(span_i - p + ki) * stride_w + (span_j - q + kj)]
                        bw = basis * w_ij
                        for dd in range(d):
                            numerator[dd] += bw * P_data[
                                (span_i - p + ki) * stride_P
                                + (span_j - q + kj) * d
                                + dd]
                        denominator += bw

                if denominator > 1e-12 or denominator < -1e-12:
                    for dd in range(d):
                        pts_data[idx * d + dd] = numerator[dd] / denominator
                else:
                    for dd in range(d):
                        pts_data[idx * d + dd] = 0.0

    return points, params
