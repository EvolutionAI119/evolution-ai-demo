"""
分镜生成器

主入口：generate_storyboard()
支持：模板选择 / 自定义分镜 / 自动时长缩放 / 产品名注入
"""
import copy
import json
from typing import List, Dict, Any, Optional
from .scene import Scene, Storyboard
from .templates import get_template


def generate_storyboard(
    product_name: str = "EVOLUTION AI",
    duration: float = 90,
    style: str = "高端汽车广告 / 科技感蓝紫色调",
    key_features: Optional[List[str]] = None,
    audience: str = "汽车行业研发管理者",
    template: str = "car_promotion",
    custom_scenes: Optional[List[Dict]] = None,
) -> Storyboard:
    """
    生成完整视频脚本

    Args:
        product_name: 产品名称
        duration: 目标时长（秒），会自动缩放
        style: 视觉风格描述
        key_features: 核心卖点列表
        audience: 目标观众
        template: 模板名（car_promotion / tech_demo / minimal_showcase）
        custom_scenes: 自定义分镜（会覆盖模板）

    Returns:
        Storyboard 对象
    """
    if key_features is None:
        key_features = ["参数化建模", "AI 优化", "实时渲染", "质量评估"]

    if custom_scenes is not None:
        scene_dicts = custom_scenes
    else:
        # 深拷贝模板，避免污染全局模板
        scene_dicts = copy.deepcopy(get_template(template)["scenes"])

    # 调整时长到目标 duration
    raw_total = sum(s["duration"] for s in scene_dicts)
    if raw_total > 0:
        scale = duration / raw_total
        for s in scene_dicts:
            s["duration_sec"] = round(s["duration"] * scale, 1)
            # 统一字段名
            s.pop("duration", None)

    # 自动注入产品名到部分字幕
    for s in scene_dicts:
        if "subtitle" in s and "{product}" in s["subtitle"]:
            s["subtitle"] = s["subtitle"].format(product=product_name)

    # 转为 Scene 对象
    scenes: List[Scene] = []
    for i, sd in enumerate(scene_dicts, 1):
        scenes.append(Scene(
            scene_id=i,
            duration_sec=sd.get("duration_sec", 10.0),
            name=sd.get("name", f"分镜 {i}"),
            background=sd.get("background", ""),
            shot_type=sd.get("shot_type", "静态"),
            camera=sd.get("camera", "静态"),
            visual=sd.get("visual", ""),
            subtitle=sd.get("subtitle", ""),
            audio=sd.get("audio", ""),
            components_shown=sd.get("components_shown", []),
            color_palette=sd.get("color_palette", []),
            data_highlights=sd.get("data_highlights", []),
        ))

    return Storyboard(
        title=f"{product_name} 视频脚本",
        total_duration=sum(s.duration_sec for s in scenes),
        style=style,
        audience=audience,
        key_features=key_features,
        scenes=scenes,
    )


def save_storyboard_json(storyboard: Storyboard, file_path: str) -> None:
    """保存为 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(storyboard.to_dict(), f, ensure_ascii=False, indent=2)
