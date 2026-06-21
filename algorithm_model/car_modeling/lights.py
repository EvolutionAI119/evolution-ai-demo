"""
前大灯 / 尾灯建模

大灯：左右各一（灯罩 + LED 灯带）
尾灯：左右各一（灯罩 + LED 条）
"""
import numpy as np
import trimesh
from typing import List
from .car_params import CarParams


def build_headlights(params: CarParams) -> trimesh.Trimesh:
    """
    前大灯组（左右各一）

    灯罩：白色半透
    LED 灯带：暖黄色发光
    """
    parts: List[trimesh.Trimesh] = []
    hw = params.headlight_width
    hh = params.headlight_height
    hd = 0.05
    z = params.ground_clearance + 0.65
    x = -params.L / 2 + 0.10

    for y_side in [params.W / 2 - hw / 2 - 0.05, -params.W / 2 + hw / 2 + 0.05]:
        lamp = trimesh.creation.box(extents=[hd, hw, hh])
        lamp.apply_translation([x, y_side, z])
        lamp.visual.face_colors = [240, 250, 255, 255]
        parts.append(lamp)
        # LED 灯带
        led = trimesh.creation.box(extents=[hd * 1.1, hw * 0.85, hh * 0.3])
        led.apply_translation([x + 0.005, y_side, z])
        led.visual.face_colors = [255, 240, 200, 255]
        parts.append(led)
    return trimesh.util.concatenate(parts)


def build_taillights(params: CarParams) -> trimesh.Trimesh:
    """
    尾灯（左右各一）

    灯罩：暗红
    LED 条：亮红
    """
    parts: List[trimesh.Trimesh] = []
    tw = 0.35
    th = 0.10
    td = 0.05
    z = params.ground_clearance + 0.70
    x = params.L / 2 - 0.10

    for y_side in [params.W / 2 - tw / 2 - 0.05, -params.W / 2 + tw / 2 + 0.05]:
        lamp = trimesh.creation.box(extents=[td, tw, th])
        lamp.apply_translation([x, y_side, z])
        lamp.visual.face_colors = [200, 30, 50, 255]
        parts.append(lamp)
        # LED 条
        led = trimesh.creation.box(extents=[td * 1.1, tw * 0.9, th * 0.4])
        led.apply_translation([x + 0.005, y_side, z])
        led.visual.face_colors = [255, 100, 120, 255]
        parts.append(led)
    return trimesh.util.concatenate(parts)
