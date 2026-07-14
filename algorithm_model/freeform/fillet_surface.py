"""
Fillet & Chamfer Surface Module

在两面之间生成过渡曲面：
- 圆角（Fillet）：G0 连续，可变半径
- 倒角（Chamfer）：45° 或指定角度的斜面过渡

核心算法：
1. 沿交线采样 N 个点
2. 在每个采样点处，计算两面的法向量
3. 用圆弧（圆角）或直线（倒角）在两面之间插值
4. 将所有截面曲线缝合为 NURBS 曲面
"""

import numpy as np
import trimesh
from typing import Tuple, Optional, Callable, List
from .nurbs_core import (
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
    open_uniform_knots,
)


# ============================================================
# 交线定义
# ============================================================

class IntersectionCurve:
    """
    两面交线的参数化表示
    
    交线可以是：
    - 直线段（两点定义）
    - 空间曲线（控制点定义）
    - 离散点序列（采样后插值）
    """
    
    def __init__(self, points: np.ndarray):
        """
        Args:
            points: (N, 3) 交线上的离散点，N >= 2
        """
        assert points.shape[1] == 3, "points must be (N, 3)"
        assert len(points) >= 2, "need at least 2 points"
        self.points = points
        self.n_points = len(points)
        
        # 预计算弧长参数化
        self.arc_lengths = self._compute_arc_lengths()
        self.total_length = self.arc_lengths[-1]
    
    def _compute_arc_lengths(self) -> np.ndarray:
        """计算累积弧长"""
        diffs = np.diff(self.points, axis=0)
        segment_lengths = np.linalg.norm(diffs, axis=1)
        return np.concatenate([[0], np.cumsum(segment_lengths)])
    
    def evaluate(self, t: float) -> np.ndarray:
        """
        在弧长参数 t ∈ [0, total_length] 处求值
        
        使用线性插值。
        
        Returns:
            (3,) 交线上的点
        """
        t = np.clip(t, 0, self.total_length)
        
        # 找到 t 所在的段
        idx = np.searchsorted(self.arc_lengths, t, side='right') - 1
        idx = min(idx, self.n_points - 2)
        
        # 段内线性插值
        t0 = self.arc_lengths[idx]
        t1 = self.arc_lengths[idx + 1]
        if t1 - t0 < 1e-12:
            return self.points[idx].copy()
        
        alpha = (t - t0) / (t1 - t0)
        return (1 - alpha) * self.points[idx] + alpha * self.points[idx + 1]
    
    def tangent(self, t: float) -> np.ndarray:
        """
        在 t 处的切向量（单位化）
        """
        eps = 1e-6
        p0 = self.evaluate(max(0, t - eps))
        p1 = self.evaluate(min(self.total_length, t + eps))
        tangent = p1 - p0
        norm = np.linalg.norm(tangent)
        if norm < 1e-12:
            return np.array([1.0, 0.0, 0.0])
        return tangent / norm


# ============================================================
# 圆角曲面生成
# ============================================================

def create_fillet_surface(
    intersection: IntersectionCurve,
    surface_a_normal: Callable[[np.ndarray], np.ndarray],
    surface_b_normal: Callable[[np.ndarray], np.ndarray],
    radius: float = 0.02,
    n_samples: int = 20,
    n_arc_points: int = 8,
    variable_radius: Optional[Callable[[float], float]] = None,
) -> dict:
    """
    在交线两侧生成圆角过渡曲面
    
    算法：
    1. 沿交线采样 n_samples 个点
    2. 在每个点处，用 surface_a_normal 和 surface_b_normal 获取两面法向
    3. 在法向平面内，用圆弧（半径=radius）连接两面
    4. 圆弧离散为 n_arc_points 个点
    5. 所有圆弧点构成控制点网格，生成 NURBS 曲面
    
    Args:
        intersection: 交线
        surface_a_normal: 面 A 在点 p 处的法向量函数 normal(p) -> (3,)
        surface_b_normal: 面 B 在点 p 处的法向量函数
        radius: 圆角半径（米），默认 0.02m = 20mm
        n_samples: 沿交线的采样数
        n_arc_points: 每条圆弧的离散点数
        variable_radius: 可变半径函数 radius(t) -> float
            t ∈ [0, 1] 为交线的归一化弧长参数
            如果为 None，使用固定半径
    
    Returns:
        dict: NURBS 曲面数据（nurbs_surface_from_grid 格式）
            control_points: (n_samples, n_arc_points, 3)
            可直接传给 evaluate_surface
    """
    control_points = np.zeros((n_samples, n_arc_points, 3))
    
    for i in range(n_samples):
        # 沿交线采样
        t_curve = i / (n_samples - 1) * intersection.total_length
        p = intersection.evaluate(t_curve)
        tangent = intersection.tangent(t_curve)
        
        # 获取两面法向
        na = surface_a_normal(p)
        nb = surface_b_normal(p)
        
        # 法向量归一化
        na = na / (np.linalg.norm(na) + 1e-12)
        nb = nb / (np.linalg.norm(nb) + 1e-12)
        
        # 确定半径
        if variable_radius is not None:
            r = variable_radius(i / (n_samples - 1))
        else:
            r = radius
        
        # 在法向平面内生成圆弧
        # 圆弧从 na 方向旋转到 nb 方向
        # 旋转轴 = tangent（交线切向）
        arc_points = _fillet_arc(p, na, nb, tangent, r, n_arc_points)
        control_points[i] = arc_points
    
    # 创建 NURBS 曲面
    degree_u = min(3, n_samples - 1)
    degree_v = min(3, n_arc_points - 1)
    
    surf = nurbs_surface_from_grid(
        control_points=control_points,
        degree_u=degree_u,
        degree_v=degree_v,
    )
    
    return surf


def _fillet_arc(
    center: np.ndarray,
    normal_a: np.ndarray,
    normal_b: np.ndarray,
    tangent: np.ndarray,
    radius: float,
    n_points: int,
) -> np.ndarray:
    """
    在两面法向之间生成圆角弧
    
    圆弧在法向平面内，从 normal_a 方向旋转到 normal_b 方向。
    
    Args:
        center: 交线上的点（圆弧起点参考）
        normal_a: 面 A 的法向量
        normal_b: 面 B 的法向量
        tangent: 交线切向量（旋转轴）
        radius: 圆弧半径
        n_points: 离散点数
    
    Returns:
        (n_points, 3) 圆弧上的点
    """
    # 将法向量投影到与 tangent 垂直的平面
    na_proj = normal_a - np.dot(normal_a, tangent) * tangent
    nb_proj = normal_b - np.dot(normal_b, tangent) * tangent
    
    na_norm = np.linalg.norm(na_proj)
    nb_norm = np.linalg.norm(nb_proj)
    
    if na_norm < 1e-8 or nb_norm < 1e-8:
        # 退化情况：法向与切向平行，用默认方向
        perp = np.array([0, 1, 0]) if abs(tangent[1]) < 0.9 else np.array([0, 0, 1])
        na_proj = np.cross(tangent, perp)
        na_proj /= np.linalg.norm(na_proj)
        nb_proj = na_proj.copy()
    else:
        na_proj /= na_norm
        nb_proj /= nb_norm
    
    # 计算旋转角度
    cos_angle = np.clip(np.dot(na_proj, nb_proj), -1, 1)
    angle = np.arccos(cos_angle)
    
    # 旋转轴
    rot_axis = np.cross(na_proj, nb_proj)
    rot_axis_norm = np.linalg.norm(rot_axis)
    if rot_axis_norm < 1e-8:
        # 两面法向平行，无需过渡
        arc = np.tile(center + radius * na_proj, (n_points, 1))
        return arc
    rot_axis /= rot_axis_norm
    
    # 生成圆弧点
    angles = np.linspace(0, angle, n_points)
    arc_points = np.zeros((n_points, 3))
    
    for k, theta in enumerate(angles):
        # Rodrigues 旋转公式
        v = na_proj
        v_rot = (v * np.cos(theta) +
                 np.cross(rot_axis, v) * np.sin(theta) +
                 rot_axis * np.dot(rot_axis, v) * (1 - np.cos(theta)))
        
        # 圆弧中心偏移（圆心在交线内侧）
        arc_center = center - radius * (1 - np.cos(theta)) * na_proj
        arc_points[k] = arc_center + radius * v_rot
    
    return arc_points


# ============================================================
# 倒角曲面生成
# ============================================================

def create_chamfer_surface(
    intersection: IntersectionCurve,
    surface_a_normal: Callable[[np.ndarray], np.ndarray],
    surface_b_normal: Callable[[np.ndarray], np.ndarray],
    width: float = 0.015,
    angle: float = 45.0,
    n_samples: int = 20,
) -> dict:
    """
    在交线两侧生成倒角（斜面）过渡曲面
    
    倒角是一条直线段连接两面，形成斜面过渡。
    
    Args:
        intersection: 交线
        surface_a_normal: 面 A 法向量函数
        surface_b_normal: 面 B 法向量函数
        width: 倒角宽度（米）
        angle: 倒角角度（度），45° 为对称倒角
        n_samples: 沿交线的采样数
    
    Returns:
        dict: NURBS 曲面数据
    """
    # 倒角用 2 个点（起点 + 终点）
    n_arc_points = 2
    
    control_points = np.zeros((n_samples, n_arc_points, 3))
    
    angle_rad = np.radians(angle)
    
    for i in range(n_samples):
        t_curve = i / (n_samples - 1) * intersection.total_length
        p = intersection.evaluate(t_curve)
        tangent = intersection.tangent(t_curve)
        
        na = surface_a_normal(p)
        nb = surface_b_normal(p)
        na = na / (np.linalg.norm(na) + 1e-12)
        nb = nb / (np.linalg.norm(nb) + 1e-12)
        
        # 倒角起点和终点
        # 起点：沿 -na 方向偏移 width * cos(angle)
        # 终点：沿 -nb 方向偏移 width * cos(angle)
        offset_a = width * np.cos(angle_rad)
        offset_b = width * np.cos(angle_rad)
        
        pt_a = p - offset_a * na
        pt_b = p - offset_b * nb
        
        control_points[i, 0] = pt_a
        control_points[i, 1] = pt_b
    
    # 创建 NURBS 曲面
    degree_u = min(3, n_samples - 1)
    degree_v = 1  # 倒角是线性过渡
    
    surf = nurbs_surface_from_grid(
        control_points=control_points,
        degree_u=degree_u,
        degree_v=degree_v,
    )
    
    return surf


# ============================================================
# 车身应用：轮眉圆角
# ============================================================

def create_wheel_arch_fillet(
    wheel_center: np.ndarray,
    wheel_radius: float,
    body_params: dict,
    fillet_radius: float = 0.015,
    n_samples: int = 24,
    n_arc_points: int = 8,
) -> dict:
    """
    创建轮眉处的圆角过渡
    
    轮眉是车轮与车身之间的圆角过渡。
    
    Args:
        wheel_center: (3,) 车轮中心坐标
        wheel_radius: 车轮半径
        body_params: 车身参数 dict（需要 ground_clearance, W, L）
        fillet_radius: 圆角半径
        n_samples: 沿轮眉弧的采样数
        n_arc_points: 圆角截面采样数
    
    Returns:
        dict: NURBS 曲面数据
    """
    # 轮眉交线：半圆弧（车轮上方 180°）
    arch_center = wheel_center.copy()
    arch_radius = wheel_radius + 0.01  # 略大于车轮
    
    # 生成半圆弧点（从后到前，经过顶部）
    angles = np.linspace(np.pi, 0, n_samples)  # 从 π 到 0
    arch_points = np.zeros((n_samples, 3))
    
    for i, theta in enumerate(angles):
        arch_points[i, 0] = arch_center[0] + arch_radius * np.cos(theta) * 0.3  # x 方向压缩
        arch_points[i, 1] = arch_center[1] + arch_radius * np.cos(theta)  # y 方向（横向）
        arch_points[i, 2] = arch_center[2] + arch_radius * np.sin(theta)  # z 方向（上方）
    
    intersection = IntersectionCurve(arch_points)
    
    # 法向量函数（简化：轮眉上方指向车身外侧）
    def wheel_normal(p):
        """车轮面法向：从轮心向外"""
        diff = p - wheel_center
        diff[0] *= 2  # x 方向压缩
        norm = np.linalg.norm(diff)
        if norm < 1e-8:
            return np.array([0, 1, 0])
        return diff / norm
    
    def body_normal(p):
        """车身面法向：近似向上"""
        return np.array([0, 0, 1])
    
    return create_fillet_surface(
        intersection=intersection,
        surface_a_normal=wheel_normal,
        surface_b_normal=body_normal,
        radius=fillet_radius,
        n_samples=n_samples,
        n_arc_points=n_arc_points,
    )


# ============================================================
# 曲面网格化（用于 GLB 导出）
# ============================================================

def surface_to_mesh(
    surf: dict,
    n_u: int = 30,
    n_v: int = 10,
    color: Tuple[int, int, int, int] = (180, 180, 180, 255),
) -> trimesh.Trimesh:
    """
    将 NURBS 曲面转换为 trimesh
    
    Args:
        surf: NURBS 曲面数据
        n_u: u 方向网格数
        n_v: v 方向网格数
        color: RGBA 颜色
    
    Returns:
        trimesh.Trimesh
    """
    points, params = evaluate_surface_mesh(surf, n_u, n_v)
    
    # 构建三角网格
    faces = []
    for i in range(n_u - 1):
        for j in range(n_v - 1):
            v00 = i * n_v + j
            v10 = (i + 1) * n_v + j
            v01 = i * n_v + (j + 1)
            v11 = (i + 1) * n_v + (j + 1)
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
    
    mesh = trimesh.Trimesh(
        vertices=points,
        faces=np.array(faces, dtype=np.int64),
        process=False,
    )
    mesh.visual.face_colors = list(color)
    
    return mesh
