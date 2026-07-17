"""
HTML 渲染器

输出格式：
- 响应式布局
- 每镜卡片（景别 / 镜头运动 / 时长 / 画面 / 字幕 / 配乐）
- 数据对比高亮（before/after 颜色对比）
- 配色色卡预览
- 组件徽章
"""
import html
from typing import List
try:
    from ..storyboard.scene import Storyboard, Scene
except ImportError:
    from storyboard.scene import Storyboard, Scene


_HTML_CSS = """
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; max-width: 980px; margin: 0 auto; padding: 20px; background: #0f1115; color: #e5e7eb; }
  h1 { color: #4A6FFF; border-bottom: 2px solid #4A6FFF; padding-bottom: 8px; }
  h2 { color: #9D4EDD; margin-top: 30px; }
  .meta { background: #1a1f3a; padding: 12px 16px; border-radius: 8px; margin: 12px 0; }
  .scene { background: #1a1f3a; border-left: 4px solid #4A6FFF; border-radius: 6px; padding: 16px 20px; margin: 16px 0; }
  .scene-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
  .badge { background: #4A6FFF; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
  .badge-duration { background: #9D4EDD; }
  .visual { font-size: 15px; line-height: 1.6; margin: 8px 0; }
  .subtitle { color: #4ADE80; font-weight: bold; margin: 8px 0; }
  .audio { color: #facc15; font-size: 13px; }
  .components { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
  .component { background: #374151; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; }
  .palette { display: flex; gap: 6px; align-items: center; margin: 8px 0; }
  .swatch { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #555; display: inline-block; }
  .palette-code { font-family: monospace; font-size: 12px; color: #9ca3af; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th { background: #4A6FFF; color: #fff; padding: 8px; text-align: left; }
  td { padding: 8px; border-bottom: 1px solid #374151; }
  .before { color: #FF6B6B; font-weight: bold; }
  .after { color: #4ADE80; font-weight: bold; }
  hr { border: none; border-top: 1px solid #374151; margin: 20px 0; }
</style>
"""


def _render_palette_html(scene: Scene) -> str:
    if not scene.color_palette:
        return ""
    swatches = "".join(
        f'<span class="swatch" style="background:{c};" title="{c}"></span>' for c in scene.color_palette
    )
    codes = " ".join(f'<span class="palette-code">{c}</span>' for c in scene.color_palette)
    return f'<div class="palette">{swatches}<div>{codes}</div></div>'


def _render_components_html(scene: Scene) -> str:
    if not scene.components_shown:
        return ""
    comps = "".join(
        f'<span class="component">{html.escape(c)}</span>' for c in scene.components_shown
    )
    return f'<div class="components">出现的部件：{comps}</div>'


def _render_data_html(scene: Scene) -> str:
    if not scene.data_highlights:
        return ""
    rows = "".join(
        f'<tr><td>{html.escape(h.get("label", ""))}</td>'
        f'<td class="before">{html.escape(h.get("before", ""))}</td>'
        f'<td class="after">{html.escape(h.get("after", ""))}</td></tr>'
        for h in scene.data_highlights
    )
    return (
        '<table>'
        '<thead><tr><th>指标</th><th>优化前</th><th>优化后</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


def render_scene_html(scene: Scene) -> str:
    """渲染单个分镜为 HTML"""
    return f"""
    <div class="scene">
      <h2>{scene.scene_id}. {html.escape(scene.name)}</h2>
      <div class="scene-meta">
        <span class="badge badge-duration">⏱ {scene.duration_sec}s</span>
        <span class="badge">📷 {html.escape(scene.camera)}</span>
        <span class="badge">🎬 {html.escape(scene.shot_type)}</span>
      </div>
      <div class="visual">🎨 <strong>画面</strong>：{html.escape(scene.visual)}</div>
      <div class="visual">🖼 <strong>背景</strong>：{html.escape(scene.background)}</div>
      <div class="subtitle">💬 {html.escape(scene.subtitle)}</div>
      <div class="audio">🎵 {html.escape(scene.audio)}</div>
      {_render_components_html(scene)}
      {_render_palette_html(scene)}
      {_render_data_html(scene)}
    </div>
    """


def render_html(storyboard: Storyboard, include_css: bool = True) -> str:
    """
    渲染完整 Storyboard 为 HTML

    Args:
        storyboard: Storyboard 对象
        include_css: 是否包含内联 CSS（默认 True）

    Returns:
        HTML 字符串
    """
    css = _HTML_CSS if include_css else ""
    features_html = " · ".join(html.escape(f) for f in storyboard.key_features)
    meta = f"""
    <div class="meta">
      <p><strong>总时长</strong>：{storyboard.total_duration}s ·
         <strong>分镜数</strong>：{len(storyboard.scenes)} ·
         <strong>观众</strong>：{html.escape(storyboard.audience)}</p>
      <p><strong>视觉风格</strong>：{html.escape(storyboard.style)}</p>
      <p><strong>核心卖点</strong>：{features_html}</p>
    </div>
    """

    scenes_html = "".join(render_scene_html(s) for s in storyboard.scenes)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(storyboard.title)}</title>
  {css}
</head>
<body>
  <h1>🎬 {html.escape(storyboard.title)}</h1>
  {meta}
  {scenes_html}
</body>
</html>"""
