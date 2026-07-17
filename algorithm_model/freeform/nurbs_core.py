"""
NURBS Core Library — 基函数、曲线、曲面求值

核心算法：
- Cox-de Boor 递归求 B 样条基函数
- 开放均匀节点向量（quasi-uniform）
- NURBS 曲线求值（控制点 + 权重）
- NURBS 曲面求值（控制网格 + 权重矩阵）
"""

import numpy as np
from typing import Tuple, Optional, List

# Cython 加速缓存：None=未检测, False=不可用, func=Cython函数
_cy_mesh = None


def find_span(n: int, p: int, u: float, U: np.ndarray) -> int:
    """
    找到 u 所在的节点区间索引 i，使得 U[i] <= u < U[i+1]
    
    使用二分查找。
    边界处理：u == U[n+1] 时返回 n。
    
    Args:
        n: 控制点数 - 1（即 n+1 个控制点）
        p: 次数（degree）
        u: 参数值
        U: 节点向量，长度 = n + p + 2
    
    Returns:
        节点区间索引 i
    """
    # 特殊处理右端点
    if u >= U[n + 1]:
        return n
    if u <= U[p]:
        return p
    
    # 二分查找
    low, high = p, n + 1
    mid = (low + high) // 2
    while u < U[mid] or u >= U[mid + 1]:
        if u < U[mid]:
            high = mid
        else:
            low = mid
        mid = (low + high) // 2
    return mid


def basis_funs(i: int, u: float, p: int, U: np.ndarray) -> np.ndarray:
    """
    计算所有非零的 p 次 B 样条基函数值 N_{i-p,p}(u) ... N_{i,p}(u)
    
    使用三角表算法（Piegl & Tiller Algorithm A2.2）
    
    Args:
        i: 节点区间索引（来自 find_span）
        u: 参数值
        p: 次数
        U: 节点向量
    
    Returns:
        (p+1,) 数组，N[j] = N_{i-p+j, p}(u)，j = 0, ..., p
    """
    N = np.zeros(p + 1)
    left = np.zeros(p + 1)
    right = np.zeros(p + 1)
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
    
    return N


def curve_point(n: int, p: int, P: np.ndarray, U: np.ndarray, u: float) -> np.ndarray:
    """
    计算 NURBS 曲线上参数 u 处的点
    
    Args:
        n: 控制点数 - 1
        p: 次数
        P: (n+1, d) 控制点数组（d 维，通常 d=2 或 3）
        U: 节点向量
        u: 参数值
    
    Returns:
        (d,) 曲线上的点
    """
    span = find_span(n, p, u, U)
    N = basis_funs(span, u, p, U)
    C = np.zeros(P.shape[1])
    for j in range(p + 1):
        C += N[j] * P[span - p + j]
    return C


def surface_point(n_p: int, n_q: int, p: int, q: int, 
                  P: np.ndarray, U: np.ndarray, V: np.ndarray,
                  u: float, v: float) -> np.ndarray:
    """
    计算 NURBS 曲面上参数 (u, v) 处的点
    
    Args:
        n_p: u 方向控制点数 - 1
        n_q: v 方向控制点数 - 1
        p: u 方向次数
        q: v 方向次数
        P: (n_p+1, n_q+1, d) 控制点网格
        U: u 方向节点向量
        V: v 方向节点向量
        u, v: 参数值
    
    Returns:
        (d,) 曲面上的点
    """
    span_u = find_span(n_p, p, u, U)
    Nu = basis_funs(span_u, u, p, U)
    span_v = find_span(n_q, q, v, V)
    Nv = basis_funs(span_v, v, q, V)
    
    d = P.shape[2]
    S = np.zeros(d)
    for j in range(q + 1):
        temp = np.zeros(d)
        for i in range(p + 1):
            temp += Nu[i] * P[span_u - p + i, span_v - q + j]
        S += Nv[j] * temp
    return S


def open_uniform_knots(n: int, p: int) -> np.ndarray:
    """
    生成开放均匀节点向量（quasi-uniform）
    
    两端重复 p+1 次，中间均匀分布。
    
    Args:
        n: 控制点数 - 1
        p: 次数
    
    Returns:
        (n+p+2,) 节点向量
    """
    m = n + p + 1  # 节点数 - 1
    U = np.zeros(m + 1)
    
    # 前 p+1 个 = 0
    U[:p + 1] = 0.0
    # 后 p+1 个 = 1
    U[m - p:] = 1.0
    # 中间均匀
    n_internal = m - 2 * p - 1
    if n_internal > 0:
        for i in range(1, n_internal + 1):
            U[p + i] = i / (n_internal + 1)
    
    return U


def nurbs_surface_from_grid(control_points: np.ndarray,
                             weights: Optional[np.ndarray] = None,
                             degree_u: int = 3,
                             degree_v: int = 3) -> dict:
    """
    从控制点网格创建 NURBS 曲面数据结构
    
    Args:
        control_points: (n_u, n_v, 3) 控制点网格
        weights: (n_u, n_v) 权重矩阵（None 则全 1）
        degree_u: u 方向次数（默认 3，三次）
        degree_v: v 方向次数（默认 3，三次）
    
    Returns:
        dict with keys:
            - control_points: ndarray
            - weights: ndarray
            - degree: (p, q) tuple
            - knots_u: ndarray
            - knots_v: ndarray
            - n: (n_u - 1, n_v - 1) tuple
    """
    n_u, n_v = control_points.shape[:2]
    
    if weights is None:
        weights = np.ones((n_u, n_v))
    
    assert weights.shape == (n_u, n_v)
    assert degree_u < n_u, f"degree_u={degree_u} must be < n_u={n_u}"
    assert degree_v < n_v, f"degree_v={degree_v} must be < n_v={n_v}"
    
    knots_u = open_uniform_knots(n_u - 1, degree_u)
    knots_v = open_uniform_knots(n_v - 1, degree_v)
    
    return {
        'control_points': control_points,
        'weights': weights,
        'degree': (degree_u, degree_v),
        'knots_u': knots_u,
        'knots_v': knots_v,
        'n': (n_u - 1, n_v - 1),
    }


def evaluate_surface(surf: dict, u: float, v: float) -> np.ndarray:
    """
    在 NURBS 曲面上求值
    
    Args:
        surf: nurbs_surface_from_grid 返回的 dict
        u, v: 参数值（通常在 [0, 1] 范围内）
    
    Returns:
        (3,) 曲面上的点
    """
    n_u, n_v = surf['n']
    p, q = surf['degree']
    P = surf['control_points']
    w = surf['weights']
    U = surf['knots_u']
    V = surf['knots_v']
    
    # NURBS = 加权控制点的有理求值
    # C(u,v) = sum(Ni * Nj * wi * Pij) / sum(Ni * Nj * wi)
    
    span_u = find_span(n_u, p, u, U)
    Nu = basis_funs(span_u, u, p, U)
    span_v = find_span(n_v, q, v, V)
    Nv = basis_funs(span_v, v, q, V)
    
    d = P.shape[2]
    numerator = np.zeros(d)
    denominator = 0.0
    
    for j in range(q + 1):
        for i in range(p + 1):
            basis = Nu[i] * Nv[j]
            w_ij = w[span_u - p + i, span_v - q + j]
            bw = basis * w_ij
            numerator += bw * P[span_u - p + i, span_v - q + j]
            denominator += bw
    
    if abs(denominator) < 1e-12:
        return np.zeros(d)
    
    return numerator / denominator


def evaluate_surface_mesh(surf: dict, n_u: int = 50, n_v: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    在 NURBS 曲面上生成网格点（自动使用 Cython 加速，如可用）

    Args:
        surf: nurbs_surface_from_grid 返回的 dict
        n_u: u 方向采样数
        n_v: v 方向采样数

    Returns:
        (points, param_grid)
        - points: (n_u * n_v, 3) 网格点
        - param_grid: (n_u * n_v, 2) 参数坐标
    """
    # 优先使用 Cython 加速版（带模块级缓存）
    global _cy_mesh
    if _cy_mesh is None:
        try:
            from ._nurbs_cy import evaluate_surface_mesh_fast as _cy_mesh
        except ImportError:
            _cy_mesh = False
    if _cy_mesh:
        return _cy_mesh(surf, n_u, n_v)

    # 纯 Python fallback
    u_vals = np.linspace(0, 1, n_u)
    v_vals = np.linspace(0, 1, n_v)

    points = []
    params = []

    for u in u_vals:
        for v in v_vals:
            pt = evaluate_surface(surf, u, v)
            points.append(pt)
            params.append([u, v])

    return np.array(points), np.array(params)
