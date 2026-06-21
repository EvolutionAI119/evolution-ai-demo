"""
车门分缝线建模

按腰线高度在车身两侧生成 N 条门缝
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams


def build_door_seams(
    params: CarParams, door_xs: List[float] = None,
) -> trimesh.Trimesh:
    """
    车门分缝线（默认 3 条：前门 / 中门 / 后门，每条左右对称）

    位置：x = hood_length + 0.50/1.10/1.70
    高度：ground_clearance + (H - ground_clearance) * waist_line
    """
    parts: List[trimesh.Trimesh] = []
    z_seam = params.ground_clearance + (params.H - params.ground_clearance) * params.waist_line

    if door_xs is None:
        door_xs = [
            -params.L / 2 + params.hood_length + 0.50,   # 前门缝
            -params.L / 2 + params.hood_length + 1.10,   # 中门缝
            -params.L / 2 + params.hood_length + 1.70,   # 后门缝
        ]

    for x in door_xs:
        for y_side in [params.W / 2 - 0.005, -params.W / 2 + 0.005]:
            line = trimesh.creation.box(extents=[0.005, 0.01, 0.6])
            line.apply_translation([x, y_side, z_seam])
            line.visual.face_colors = [10, 10, 15, 255]
            parts.append(line)
    return trimesh.util.concatenate(parts) if parts else trimesh.Trimesh()
