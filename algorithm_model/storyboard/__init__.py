"""
storyboard - 视频脚本分镜生成模块

3 个子模块：
- scene: 分镜 / Storyboard 数据结构
- templates: 模板库（3 套：car_promotion / tech_demo / minimal_showcase）
- generator: 生成器（支持自定义分镜 + 自动时长缩放）
"""
from .scene import Scene, Storyboard
from .templates import TEMPLATES, get_template
from .generator import generate_storyboard, save_storyboard_json

__all__ = [
    "Scene",
    "Storyboard",
    "TEMPLATES",
    "get_template",
    "generate_storyboard",
    "save_storyboard_json",
]
