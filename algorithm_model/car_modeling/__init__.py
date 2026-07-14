"""
car_modeling - 参数化汽车造型建模模块

包含 8 大部件：车壳、玻璃、4 轮、大灯、尾灯、格栅、后视镜、门缝
全部由 CarParams 22 维参数驱动

W2-D2 新增：三区段 blending + tumblehome
"""
from .car_params import CarParams
from .body import build_body, get_hardpoints
from .glass import build_glass
from .wheels import build_wheel, build_wheels
from .lights import build_headlights, build_taillights
from .grille import build_grille
from .mirrors import build_mirrors
from .seams import build_door_seams
from .assembler import build_full_car, compute_stats
from .blending import (
    ZoneLevel,
    ZoneParamsTable,
    ZONE_PARAMS_TABLE,
    smoothstep,
    three_zone_weights,
    normalize_zone_weights,
    compute_tumblehome,
    get_zone,
    get_blended_params,
)
from .trim import (
    TrimStrip,
    TRIM_PRESETS,
    create_chrome_trim,
    create_rubber_seal,
    create_body_molding,
)

__all__ = [
    "CarParams",
    "build_body",
    "get_hardpoints",
    "build_glass",
    "build_wheel",
    "build_wheels",
    "build_headlights",
    "build_taillights",
    "build_grille",
    "build_mirrors",
    "build_door_seams",
    "build_full_car",
    "compute_stats",
    # blending 模块
    "ZoneLevel",
    "ZoneParamsTable",
    "ZONE_PARAMS_TABLE",
    "smoothstep",
    "three_zone_weights",
    "normalize_zone_weights",
    "compute_tumblehome",
    "get_zone",
    "get_blended_params",
    # trim 模块
    "TrimStrip",
    "TRIM_PRESETS",
    "create_chrome_trim",
    "create_rubber_seal",
    "create_body_molding",
]
