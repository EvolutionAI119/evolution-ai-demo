"""
Markdown 渲染器

输出格式：
- 标题 + 元信息
- 每个分镜一个二级标题
- 表格化镜头信息
- 数据对比表（如果有 data_highlights）
- 配色色卡（如果有 color_palette）
"""
from typing import List
try:
    from ..storyboard.scene import Storyboard, Scene
except ImportError:
    from storyboard.scene import Storyboard, Scene


def _format_data_highlights(scene: Scene) -> str:
    """格式化数据对比表"""
    if not scene.data_highlights:
        return ""
    lines = ["| 指标 | 优化前 | 优化后 |", "|------|--------|--------|"]
    for h in scene.data_highlights:
        label = h.get("label", "")
        before = h.get("before", "")
        after = h.get("after", "")
        lines.append(f"| {label} | {before} | {after} |")
    return "\n".join(lines)


def _format_color_palette(scene: Scene) -> str:
    """格式化配色色卡"""
    if not scene.color_palette:
        return ""
    cells: List[str] = []
    for c in scene.color_palette:
        cells.append(f"`{c}`")
    return " · ".join(cells)


def render_scene_md(scene: Scene) -> str:
    """渲染单个分镜为 Markdown"""
    md = f"## {scene.scene_id}. {scene.name}\n\n"
    md += f"**时长**：{scene.duration_sec}s | **镜头**：{scene.camera} | **景别**：{scene.shot_type}\n\n"
    md += f"**画面描述**：{scene.visual}\n\n"
    md += f"**背景**：{scene.background}\n\n"
    md += f"**字幕**：{scene.subtitle}\n\n"
    md += f"**配乐**：{scene.audio}\n\n"

    if scene.components_shown:
        comps = "、".join(scene.components_shown)
        md += f"**出现的部件**：`{comps}`\n\n"

    if scene.color_palette:
        md += f"**配色**：{_format_color_palette(scene)}\n\n"

    if scene.data_highlights:
        md += f"**数据对比**：\n\n{_format_data_highlights(scene)}\n\n"

    md += "---\n\n"
    return md


def render_markdown(storyboard: Storyboard) -> str:
    """
    渲染完整 Storyboard 为 Markdown

    Args:
        storyboard: Storyboard 对象

    Returns:
        Markdown 字符串
    """
    md = f"# {storyboard.title}\n\n"
    md += f"> **总时长**：{storyboard.total_duration}s | "
    md += f"**分镜数**：{len(storyboard.scenes)} | "
    md += f"**观众**：{storyboard.audience}\n\n"
    md += f"**视觉风格**：{storyboard.style}\n\n"
    md += f"**核心卖点**：{' · '.join(storyboard.key_features)}\n\n"
    md += "---\n\n"

    for scene in storyboard.scenes:
        md += render_scene_md(scene)

    return md
