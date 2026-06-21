"""
主车身壳体建模

通过沿车长方向取截面，按截面形状（宽+高）构建完整外壳。
算法核心：截面宽度 + 截面高度 + 截面形状 → 三角网格
"""
import numpy as np
import trimesh
from typing import List, Tuple
from .car_params import CarParams


def _section_width(x_norm: float, params: CarParams) -> float:
    """
    车长方向位置 x_norm ∈ [-1, 1] 处的车体半宽（y 方向）

    设计：楔形 - 前窄 / 中后宽 / 尾部稍收
    公式：cos^1.5(πx/2) * 前段修长系数 * 后段修长系数
    """
    base = np.cos(x_norm * np.pi / 2) ** 1.5
    front_factor = 1.0 - 0.15 * max(0, -x_norm)
    rear_factor = 1.0 - 0.08 * max(0, x_norm)
    return params.W / 2 * base * front_factor * rear_factor


def _section_height(x_norm: float, params: CarParams) -> float:
    """
    车长方向位置 x_norm ∈ [-1, 1] 处的车体高度（z 方向地面到顶）

    设计 5 段造型：
    - 发动机盖（低平）
    - 前挡风过渡（斜向上）
    - 座舱前沿（快速攀升）
    - 车顶（高顶）
    - 后挡风（斜向下）
    - 行李箱（低平）
    """
    L = params.L
    x = x_norm * L / 2
    front_edge = -L/2 + params.hood_length
    windshield_top = front_edge + 0.05
    roof_start = windshield_top + 0.5
    roof_end = roof_start + params.cabin_length * 0.6
    rear_glass_start = roof_end
    rear_glass_end = rear_glass_start + 0.7
    trunk_start = rear_glass_end
    trunk_end = L/2
    ground_clear = params.ground_clearance
    max_h = params.H - ground_clear

    if x < front_edge:  # 发动机盖
        t = (x - (-L/2)) / (front_edge - (-L/2))
        return ground_clear + 0.55 + t * (ground_clear + 0.78 - ground_clear - 0.55)
    elif x < windshield_top:  # 前挡风过渡
        t = (x - front_edge) / max(1e-6, windshield_top - front_edge)
        return (ground_clear + 0.78) + t * (ground_clear + 1.0 - ground_clear - 0.78)
    elif x < roof_start:  # 座舱前沿
        t = (x - windshield_top) / max(1e-6, roof_start - windshield_top)
        h_start = ground_clear + 1.0
        h_end = params.H - 0.05
        arc = params.roof_arc
        return h_start + t * (h_end - h_start) * (1 + arc * np.sin(t * np.pi))
    elif x < roof_end:  # 车顶
        return params.H - 0.05
    elif x < rear_glass_end:  # 后挡风
        t = (x - rear_glass_start) / max(1e-6, rear_glass_end - rear_glass_start)
        h_start = params.H - 0.05
        h_end = ground_clear + 0.7
        return h_start + t * (h_end - h_start)
    else:  # 行李箱
        t = (x - trunk_start) / max(1e-6, trunk_end - trunk_start)
        h_start = ground_clear + 0.7
        h_end = ground_clear + 0.6
        return h_start + t * (h_end - h_start)


def _section_shape(x_norm: float, z_norm: float, params: CarParams) -> Tuple[float, float]:
    """
    截面形状：给定 x_norm 和 z_norm（0=地，1=顶）
    返回 (y_norm, lateral_squish)

    设计：上窄下宽 / 顶部尖 / 肩部最宽 / 底部稍窄
    """
    half_w = _section_width(x_norm, params)
    p_shoulder = 0.65
    top_factor = 1.0 - 0.10 * (z_norm ** 2)
    if z_norm < p_shoulder:
        bot_factor = 0.85 + 0.15 * (z_norm / p_shoulder)
    else:
        bot_factor = 1.0 - 0.18 * ((z_norm - p_shoulder) / (1 - p_shoulder))
    y = half_w * top_factor * bot_factor
    return y, 1.0


def build_body(params: CarParams, n_long: int = 48, n_circ: int = 24) -> trimesh.Trimesh:
    """
    构建主车身壳体（左右对称的完整外壳）

    Args:
        params: 整车参数
        n_long: 车长方向分段数
        n_circ: 截面方向分段数

    Returns:
        trimesh.Trimesh 车身壳体
    """
    verts: List[List[float]] = []
    faces: List[List[int]] = []

    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2
        for j in range(n_circ + 1):
            z_norm = j / n_circ
            z = _section_height(x_norm, params)
            y, _ = _section_shape(x_norm, z_norm, params)
            verts.append([x, y, z])
            verts.append([x, -y, z])  # 对称侧

    cols = 2 * (n_circ + 1)
    for i in range(n_long):
        for j in range(n_circ):
            v00 = i * cols + 2 * j
            v10 = (i + 1) * cols + 2 * j
            v01 = i * cols + 2 * (j + 1)
            v11 = (i + 1) * cols + 2 * (j + 1)
            w00 = i * cols + 2 * j + 1
            w10 = (i + 1) * cols + 2 * j + 1
            w01 = i * cols + 2 * (j + 1) + 1
            w11 = (i + 1) * cols + 2 * (j + 1) + 1

            # 左侧（法向朝外）
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
            # 右侧（法向朝外）
            faces.append([w00, w11, w10])
            faces.append([w00, w01, w11])

    mesh = trimesh.Trimesh(
        vertices=np.array(verts, dtype=np.float64),
        faces=np.array(faces, dtype=np.int64),
        process=True,
    )
    mesh.visual.face_colors = [200, 30, 40, 255]  # 经典红
    return mesh
