"""
玻璃区域建模

包含 4 个玻璃面：
- 前挡风（带角度的矩形）
- 后挡风（带角度的矩形）
- 车顶天窗（中央矩形）
- 侧窗（左右两侧各一）
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams
from .body import _section_width, _section_height


def _build_windshield(
    x_bottom: float, x_top: float, z_bottom: float, z_top: float,
    angle_deg: float, dir_sign: float, params: CarParams, n_vert: int = 8,
) -> trimesh.Trimesh:
    """
    通用挡风玻璃构建（前/后通用）

    Args:
        x_bottom: 底部 x 位置
        x_top: 顶部 x 位置
        z_bottom: 底部 z 高度
        z_top: 顶部 z 高度
        angle_deg: 倾角（度）
        dir_sign: 方向（+1=前挡风，-1=后挡风）
        params: 整车参数
        n_vert: 纵向分段
    """
    rake = np.radians(angle_deg)
    verts = []
    for j in range(n_vert + 1):
        t = j / n_vert
        z = z_bottom + t * (z_top - z_bottom)
        x_offset = t * np.tan(rake) * (z_top - z_bottom) * dir_sign
        x = x_bottom + x_offset
        half_w_top = _section_width(x / (params.L / 2), params) * 0.92
        verts.append([x, -half_w_top, z])
        verts.append([x, half_w_top, z])
    faces = []
    for j in range(n_vert):
        v0 = 2 * j
        v1 = 2 * j + 1
        v2 = 2 * (j + 1)
        v3 = 2 * (j + 1) + 1
        faces.append([v0, v2, v3])
        faces.append([v0, v3, v1])
    return trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces))


def _build_sunroof(params: CarParams, n_long: int = 10, n_wide: int = 6) -> trimesh.Trimesh:
    """车顶天窗"""
    roof_x_start = -params.L / 2 + params.hood_length + 0.7
    roof_x_end = params.L / 2 - params.trunk_length - 0.7
    half_roof_w = params.W / 2 * 0.78
    z = params.H - 0.06

    verts = []
    for i in range(n_long + 1):
        t = i / n_long
        x = roof_x_start + t * (roof_x_end - roof_x_start)
        for j in range(n_wide + 1):
            s = j / n_wide
            y = -half_roof_w + s * (2 * half_roof_w)
            verts.append([x, y, z])
    faces = []
    for i in range(n_long):
        for j in range(n_wide):
            v00 = i * (n_wide + 1) + j
            v10 = (i + 1) * (n_wide + 1) + j
            v01 = i * (n_wide + 1) + (j + 1)
            v11 = (i + 1) * (n_wide + 1) + (j + 1)
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
    return trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces))


def _build_side_windows(params: CarParams, n_long: int = 12, n_vert: int = 4) -> trimesh.Trimesh:
    """左右侧窗"""
    pieces = []
    x_start = -params.L / 2 + params.hood_length + 0.55
    x_end = params.L / 2 - params.trunk_length - 0.55
    z_top = params.H - 0.08
    z_bot = params.ground_clearance + 0.95

    for y_side in [params.W / 2 - 0.04, -params.W / 2 + 0.04]:
        verts = []
        for i in range(n_long + 1):
            t = i / n_long
            x = x_start + t * (x_end - x_start)
            for j in range(n_vert + 1):
                s = j / n_vert
                z = z_bot + s * (z_top - z_bot)
                verts.append([x, y_side, z])
        faces = []
        for i in range(n_long):
            for j in range(n_vert):
                v00 = i * (n_vert + 1) + j
                v10 = (i + 1) * (n_vert + 1) + j
                v01 = i * (n_vert + 1) + (j + 1)
                v11 = (i + 1) * (n_vert + 1) + (j + 1)
                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])
        pieces.append(trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces)))

    return trimesh.util.concatenate(pieces) if pieces else trimesh.Trimesh()


def build_glass(
    params: CarParams, n_long: int = 20, n_vert: int = 8, include_side: bool = True,
) -> trimesh.Trimesh:
    """
    构建车窗玻璃

    Args:
        params: 整车参数
        n_long: 长向分段
        n_vert: 纵向分段
        include_side: 是否包含侧窗

    Returns:
        trimesh.Trimesh 玻璃组合 mesh
    """
    pieces: List[trimesh.Trimesh] = []

    # 1) 前挡风
    z_top = params.H - 0.08
    z_bottom_fw = params.ground_clearance + 0.78
    x_bottom_fw = -params.L / 2 + params.hood_length
    pieces.append(_build_windshield(
        x_bottom_fw, x_bottom_fw + 0.55, z_bottom_fw, z_top,
        params.windshield_rake, +1, params, n_vert,
    ))

    # 2) 后挡风
    z_bottom_rw = params.ground_clearance + 0.7
    x_top_rw = params.L / 2 - params.trunk_length - 0.55
    pieces.append(_build_windshield(
        x_top_rw, x_top_rw + 0.55, z_bottom_rw, z_top,
        params.rear_glass_angle, -1, params, n_vert,
    ))

    # 3) 车顶天窗
    pieces.append(_build_sunroof(params))

    # 4) 侧窗（可选）
    if include_side:
        pieces.append(_build_side_windows(params))

    glass = trimesh.util.concatenate(pieces)
    d = int(255 * (1 - params.glass_darkness))
    glass.visual.face_colors = [40, 60, d, 220]  # 深蓝玻璃
    return glass
