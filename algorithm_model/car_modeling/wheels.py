"""
车轮建模

单轮结构：轮胎（圆柱）+ 中心轮毂（圆柱）+ N 个辐条（长方体）
4 轮布局：按轴距 + 轮距 + 轮半径 定位
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams


def build_wheel(params: CarParams) -> trimesh.Trimesh:
    """
    单个车轮 - 包含轮胎 + 轮毂中心 + 多辐条

    Args:
        params: 整车参数（使用 wheel_radius / wheel_width / wheel_spoke_count）

    Returns:
        trimesh.Trimesh
    """
    parts: List[trimesh.Trimesh] = []
    R = params.wheel_radius
    W = params.wheel_width

    # 1) 轮胎
    tire = trimesh.creation.cylinder(radius=R, height=W, sections=48)
    # 旋转使轴沿 y
    rot = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    tire.apply_transform(rot)
    tire.visual.face_colors = [25, 25, 30, 255]

    # 2) 中心轮毂
    hub = trimesh.creation.cylinder(radius=R * 0.18, height=W * 1.05, sections=16)
    hub.apply_transform(rot)
    hub.visual.face_colors = [180, 180, 190, 255]

    # 3) 辐条
    for k in range(params.wheel_spoke_count):
        angle = 2 * np.pi * k / params.wheel_spoke_count
        spoke = trimesh.creation.box(extents=[R * 0.85, W * 0.6, R * 0.10])
        rot_angle = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
        spoke.apply_transform(rot_angle)
        spoke.apply_translation([R * 0.42, 0, 0])
        rot_y = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        spoke.apply_transform(rot_y)
        spoke.visual.face_colors = [200, 200, 215, 255]
        parts.append(spoke)

    parts.append(tire)
    parts.append(hub)
    return trimesh.util.concatenate(parts)


def build_wheels(params: CarParams) -> trimesh.Trimesh:
    """
    4 个轮子放置在正确位置

    布局：左前 / 右前 / 左后 / 右后
    x = ±轴距/2
    y = ±轮距/2 = ±(车宽/2 - 0.05)
    z = 轮半径 + 微小间隙
    """
    wheels: List[trimesh.Trimesh] = []
    R = params.wheel_radius
    wb_half = params.wheelbase / 2
    wheel_y = params.W / 2 - 0.05
    wheel_z = R + 0.02
    x_positions = [-wb_half, wb_half]
    y_positions = [wheel_y, -wheel_y]

    for x in x_positions:
        for y in y_positions:
            w = build_wheel(params)
            w.apply_translation([x, y, wheel_z])
            wheels.append(w)
    return trimesh.util.concatenate(wheels)
