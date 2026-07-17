"""
前脸进气格栅建模

结构：
- 格栅框（梯形 box）
- N 条横向格栅条
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams


def build_grille(params: CarParams) -> trimesh.Trimesh:
    """
    前脸进气格栅
    """
    parts: List[trimesh.Trimesh] = []
    x = -params.L / 2 + 0.02
    w_top = 0.6
    w_bot = 0.9
    h = 0.18
    z_center = params.ground_clearance + 0.30

    # 格栅框
    grille = trimesh.creation.box(extents=[0.04, (w_top + w_bot) / 2, h])
    grille.apply_translation([x, 0, z_center])
    grille.visual.face_colors = [30, 30, 35, 255]
    parts.append(grille)

    # 横向格栅条
    n_bars = 5
    for k in range(n_bars):
        bar = trimesh.creation.box(extents=[0.06, (w_top + w_bot) / 2 * 0.92, 0.012])
        z_offset = (k - (n_bars - 1) / 2) * (h * 0.85 / n_bars)
        bar.apply_translation([x + 0.02, 0, z_center + z_offset])
        bar.visual.face_colors = [180, 185, 195, 255]
        parts.append(bar)
    return trimesh.util.concatenate(parts)
