"""
Swept Surface Module — 沿空间曲线扫描 2D 截面生成曲面

核心算法：
1. 沿路径曲线采样 N 个点
2. 在每个采样点处计算 Frenet 标架（切线 T / 法线 N / 副法线 B）
3. 将截面曲线变换到局部坐标系（由 Frenet 标架定义）
4. 所有截面点构成控制点网格，生成 NURBS 曲面

退化处理：
- 曲率为零的直线段：使用 Rotation Minimizing Frame（RMF）避免扭曲
- 共线路径点：法线方向继承上一有效法线

截面类型：
- circle：圆形截面（半径 r, n_arc_points 个离散点）
- rectangle：矩形截面（宽 w, 高 h, 4 个角 + 插值点）
- custom：自定义截面（用户传入 (M, 2) 截面点）
"""

import numpy as np
from typing import Tuple, Optional, List, Union, Callable
from .nurbs_core import (
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
    open_uniform_knots,
    curve_point,
    find_span,
    basis_funs,
)


# ============================================================
# 截面生成
# ============================================================

def generate_circle_section(
    radius: float,
    n_points: int = 16,
) -> np.ndarray:
    """
    生成圆形截面点

    Args:
        radius: 圆截面半径
        n_points: 离散点数（≥3）

    Returns:
        (n_points, 2) 截面点，中心在原点
    """
    assert n_points >= 3, "n_points must be >= 3 for circle"
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    points = np.stack([radius * np.cos(angles), radius * np.sin(angles)], axis=1)
    return points


def generate_rectangle_section(
    width: float,
    height: float,
    n_per_side: int = 4,
) -> np.ndarray:
    """
    生成矩形截面点（沿矩形周长均匀采样）

    Args:
        width: 矩形宽（y 方向）
        height: 矩形高（z 方向）
        n_per_side: 每边的采样点数（≥2）

    Returns:
        (4 * n_per_side, 2) 截面点，中心在原点
    """
    assert n_per_side >= 2, "n_per_side must be >= 2"
    hw = width / 2
    hh = height / 2

    # 从右下角开始，逆时针
    points = []

    # 底边：(-hw, -hh) → (hw, -hh)
    for i in range(n_per_side):
        t = i / n_per_side
        points.append([-hw + width * t, -hh])

    # 右边：(hw, -hh) → (hw, hh)
    for i in range(n_per_side):
        t = i / n_per_side
        points.append([hw, -hh + height * t])

    # 顶边：(hw, hh) → (-hw, hh)
    for i in range(n_per_side):
        t = i / n_per_side
        points.append([hw - width * t, hh])

    # 左边：(-hw, hh) → (-hw, -hh)
    for i in range(n_per_side):
        t = i / n_per_side
        points.append([-hw, hh - height * t])

    return np.array(points)


# ============================================================
# Frenet 标架计算
# ============================================================

class FrenetFrame:
    """
    Frenet 标架：在每个路径点处计算 (T, N, B) 局部坐标系

    T = 切向量（单位化）
    N = 法向量（主法线，指向曲率中心）
    B = 副法线 = T × N

    退化处理：
    - 曲率为零（直线段）时 N 不存在，使用 Rotation Minimizing Frame
    """

    @staticmethod
    def compute_frames(
        path_points: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        沿路径点序列计算 Frenet 标架

        使用 Rotation Minimizing Frame（RMF）算法避免扭曲，
        仅在第一个点使用 Frenet 标架初始化。

        Args:
            path_points: (N, 3) 路径上的离散点，N >= 2

        Returns:
            (T, N, B): 每个 (N, 3)
                T[i]: 第 i 个点处的单位切向量
                N[i]: 第 i 个点处的法向量
                B[i]: 第 i 个点处的副法线
        """
        N = len(path_points)
        assert N >= 2, "need at least 2 path points"

        T = np.zeros((N, 3))
        Nf = np.zeros((N, 3))
        B = np.zeros((N, 3))

        # ===== 计算切向量 =====
        for i in range(N):
            if i == 0:
                tangent = path_points[1] - path_points[0]
            elif i == N - 1:
                tangent = path_points[-1] - path_points[-2]
            else:
                tangent = path_points[i + 1] - path_points[i - 1]
            norm = np.linalg.norm(tangent)
            if norm < 1e-12:
                tangent = T[i - 1] if i > 0 else np.array([1.0, 0.0, 0.0])
                norm = np.linalg.norm(tangent)
            T[i] = tangent / norm

        # ===== 初始法向量 =====
        # 在第一个点使用 Frenet 方法
        # 找一个与 T[0] 不平行的向量
        t0 = T[0]
        if abs(t0[0]) < 0.9:
            ref = np.array([1.0, 0.0, 0.0])
        else:
            ref = np.array([0.0, 1.0, 0.0])

        # B[0] = T[0] × ref, N[0] = B[0] × T[0]
        B[0] = np.cross(t0, ref)
        b_norm = np.linalg.norm(B[0])
        if b_norm < 1e-12:
            # T 与 ref 平行，换一个方向
            ref = np.array([0.0, 0.0, 1.0])
            B[0] = np.cross(t0, ref)
            b_norm = np.linalg.norm(B[0])
        B[0] = B[0] / b_norm
        Nf[0] = np.cross(B[0], t0)
        Nf[0] = Nf[0] / np.linalg.norm(Nf[0])

        # ===== Rotation Minimizing Frame (RMF) =====
        # Wang et al. (2008) — "Computation of Rotation Minimizing Frames"
        # 使用双反射法（Double Reflection Method）
        for i in range(1, N):
            # 反射 v1：关于平面 (path[i-1]+path[i])/2, 法线 path[i]-path[i-1]
            v1 = path_points[i] - path_points[i - 1]
            c1 = np.dot(v1, v1)
            if c1 < 1e-24:
                # 两点重合，直接继承上一帧
                Nf[i] = Nf[i - 1]
                B[i] = B[i - 1]
                continue

            # 反射 N_L
            rL = Nf[i - 1] - (2.0 / c1) * np.dot(v1, Nf[i - 1]) * v1
            # 反射 T_L
            tL = T[i - 1] - (2.0 / c1) * np.dot(v1, T[i - 1]) * v1

            # 反射 v2：关于平面 (T[i]+tL)/2, 法线 T[i]-tL
            v2 = T[i] - tL
            c2 = np.dot(v2, v2)
            if c2 < 1e-24:
                # 切线方向不变
                Nf[i] = rL
                B[i] = np.cross(T[i], Nf[i])
                if np.linalg.norm(B[i]) < 1e-12:
                    B[i] = B[i - 1]
                else:
                    B[i] = B[i] / np.linalg.norm(B[i])
                Nf[i] = np.cross(B[i], T[i])
                Nf[i] = Nf[i] / np.linalg.norm(Nf[i])
                continue

            # 反射 rL 得到 N[i]
            Nf[i] = rL - (2.0 / c2) * np.dot(v2, rL) * v2
            Nf[i] = Nf[i] / np.linalg.norm(Nf[i])

            # B[i] = T[i] × N[i]
            B[i] = np.cross(T[i], Nf[i])
            b_norm = np.linalg.norm(B[i])
            if b_norm < 1e-12:
                B[i] = B[i - 1]
                B[i] = B[i] / np.linalg.norm(B[i])
                Nf[i] = np.cross(B[i], T[i])
                Nf[i] = Nf[i] / np.linalg.norm(Nf[i])
            else:
                B[i] = B[i] / b_norm

        return T, Nf, B


# ============================================================
# 扫描曲面
# ============================================================

class SweptSurface:
    """
    沿空间曲线扫描 2D 截面生成曲面

    流程：
    1. 对路径曲线采样 path_samples 个点
    2. 在每个路径点计算 Frenet 标架 (T, N, B)
    3. 将截面点从 2D (y, z) 变换到 3D：P = path_point + y * N + z * B
    4. 所有截面点构成控制点网格，生成 NURBS 曲面

    Args:
        path_points: (M, 3) 路径控制点
        section_type: 'circle' | 'rectangle' | 'custom'
        section_params: 截面参数
            - circle: {'radius': float, 'n_points': int}
            - rectangle: {'width': float, 'height': float, 'n_per_side': int}
            - custom: {'points': np.ndarray of shape (K, 2)}
        path_samples: 路径采样点数
        degree_u: u 方向（沿路径）NURBS 次数
        degree_v: v 方向（截面方向）NURBS 次数
        section_scale: Optional 可变截面缩放函数 scale(t) -> float,
            t ∈ [0, 1] 为路径的归一化参数
    """

    def __init__(
        self,
        path_points: np.ndarray,
        section_type: str = 'circle',
        section_params: Optional[dict] = None,
        path_samples: int = 20,
        degree_u: int = 3,
        degree_v: int = 3,
        section_scale: Optional[Callable[[float], float]] = None,
    ):
        self.path_points = np.array(path_points, dtype=float)
        assert self.path_points.shape[1] == 3, "path_points must be (M, 3)"
        assert len(self.path_points) >= 2, "need at least 2 path points"

        self.section_type = section_type
        self.section_params = section_params or {}
        self.path_samples = max(path_samples, 2)
        self.degree_u = degree_u
        self.degree_v = degree_v
        self.section_scale = section_scale

        # 生成截面点
        self.section_points = self._generate_section()

        # 扫描曲面（延迟计算）
        self._surface = None
        self._sampled_path = None
        self._frames = None

    def _generate_section(self) -> np.ndarray:
        """根据截面类型生成 2D 截面点"""
        if self.section_type == 'circle':
            radius = self.section_params.get('radius', 0.01)
            n_points = self.section_params.get('n_points', 16)
            return generate_circle_section(radius, n_points)
        elif self.section_type == 'rectangle':
            width = self.section_params.get('width', 0.02)
            height = self.section_params.get('height', 0.01)
            n_per_side = self.section_params.get('n_per_side', 4)
            return generate_rectangle_section(width, height, n_per_side)
        elif self.section_type == 'custom':
            pts = self.section_params.get('points', None)
            assert pts is not None, "custom section requires 'points' in section_params"
            pts = np.array(pts, dtype=float)
            assert pts.ndim == 2 and pts.shape[1] == 2, "custom points must be (K, 2)"
            return pts
        else:
            raise ValueError(f"Unknown section_type: {self.section_type}")

    def _sample_path(self) -> np.ndarray:
        """
        对路径曲线均匀采样

        使用弧长参数化进行均匀采样。

        Returns:
            (path_samples, 3) 采样点
        """
        pts = self.path_points
        n = len(pts)

        if n == 2:
            # 两点直线：线性插值
            t_vals = np.linspace(0, 1, self.path_samples)
            sampled = np.outer(1 - t_vals, pts[0]) + np.outer(t_vals, pts[1])
            return sampled

        # 使用 NURBS 曲线进行采样
        # 次数 = min(3, n-1)
        degree = min(3, n - 1)
        U = open_uniform_knots(n - 1, degree)

        # 简化：直接用 chord-length 参数化采样
        # 计算弧长
        diffs = np.diff(pts, axis=0)
        seg_lengths = np.linalg.norm(diffs, axis=1)
        cum_lengths = np.concatenate([[0], np.cumsum(seg_lengths)])
        total_length = cum_lengths[-1]

        if total_length < 1e-12:
            # 所有点重合
            return np.tile(pts[0], (self.path_samples, 1))

        # 均匀弧长采样
        target_lengths = np.linspace(0, total_length, self.path_samples)
        sampled = np.zeros((self.path_samples, 3))

        for i, target in enumerate(target_lengths):
            idx = np.searchsorted(cum_lengths, target, side='right') - 1
            idx = min(idx, n - 2)

            t0 = cum_lengths[idx]
            t1 = cum_lengths[idx + 1]
            if t1 - t0 < 1e-12:
                sampled[i] = pts[idx]
            else:
                alpha = (target - t0) / (t1 - t0)
                sampled[i] = (1 - alpha) * pts[idx] + alpha * pts[idx + 1]

        return sampled

    def build(self) -> dict:
        """
        构建扫描曲面

        Returns:
            dict: NURBS 曲面数据（nurbs_surface_from_grid 格式）
                control_points: (path_samples, n_section_pts, 3)
        """
        # 1. 采样路径
        sampled_path = self._sample_path()
        self._sampled_path = sampled_path

        # 2. 计算 Frenet 标架
        T, N, B = FrenetFrame.compute_frames(sampled_path)
        self._frames = (T, N, B)

        # 3. 在每个路径点处变换截面
        n_path = len(sampled_path)
        n_section = len(self.section_points)

        control_points = np.zeros((n_path, n_section, 3))

        for i in range(n_path):
            # 截面缩放
            if self.section_scale is not None:
                t_param = i / (n_path - 1) if n_path > 1 else 0.0
                scale = self.section_scale(t_param)
            else:
                scale = 1.0

            for j in range(n_section):
                y_local = self.section_points[j, 0] * scale
                z_local = self.section_points[j, 1] * scale

                # P = path_point + y * N + z * B
                control_points[i, j] = (
                    sampled_path[i] + y_local * N[i] + z_local * B[i]
                )

        # 4. 创建 NURBS 曲面
        deg_u = min(self.degree_u, n_path - 1)
        deg_v = min(self.degree_v, n_section - 1)

        self._surface = nurbs_surface_from_grid(
            control_points=control_points,
            degree_u=deg_u,
            degree_v=deg_v,
        )

        return self._surface

    def get_surface(self) -> dict:
        """获取已构建的 NURBS 曲面（如果未构建则先构建）"""
        if self._surface is None:
            self.build()
        return self._surface

    def get_sampled_path(self) -> np.ndarray:
        """获取采样后的路径点"""
        if self._sampled_path is None:
            self.build()
        return self._sampled_path

    def get_frames(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """获取 Frenet 标架 (T, N, B)"""
        if self._frames is None:
            self.build()
        return self._frames

    def evaluate(self, u: float, v: float) -> np.ndarray:
        """
        在扫描曲面上求值

        Args:
            u: 沿路径参数 ∈ [0, 1]
            v: 截面参数 ∈ [0, 1]

        Returns:
            (3,) 曲面上的点
        """
        surf = self.get_surface()
        return evaluate_surface(surf, u, v)

    def to_mesh(
        self,
        n_u: int = 30,
        n_v: int = 16,
        color: Tuple[int, int, int, int] = (180, 180, 180, 255),
    ) -> 'trimesh.Trimesh':
        """
        转换为 trimesh 网格

        Args:
            n_u: u 方向采样数
            n_v: v 方向采样数
            color: RGBA 颜色

        Returns:
            trimesh.Trimesh
        """
        import trimesh

        surf = self.get_surface()
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
