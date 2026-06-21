"""
后视镜建模

每侧包含：底座（小方块）+ 镜壳（大方块）
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams


def build_mirrors(params: CarParams) -> trimesh.Trimesh:
    """
    左右后视镜
    """
    parts: List[trimesh.Trimesh] = []
    mirror_x = -params.L / 2 + params.hood_length + 0.18
    mirror_y = params.W / 2 + 0.04
    mirror_z = params.ground_clearance + 1.05

    for y_sign in [1, -1]:
        # 底座
        base = trimesh.creation.box(extents=[0.05, 0.05, 0.05])
        base.apply_translation([mirror_x, y_sign * mirror_y, mirror_z])
        base.visual.face_colors = [40, 40, 45, 255]
        parts.append(base)
        # 镜壳
        shell = trimesh.creation.box(extents=[0.12, 0.18, 0.07])
        shell.apply_translation([mirror_x, y_sign * (mirror_y + 0.10), mirror_z])
        shell.visual.face_colors = [200, 30, 40, 255]
        parts.append(shell)
    return trimesh.util.concatenate(parts)
