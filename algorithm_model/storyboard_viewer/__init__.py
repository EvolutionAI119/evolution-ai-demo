"""
storyboard_viewer - 视频脚本可视化模块

2 个子模块：
- markdown_renderer: Markdown 渲染（含表格、配色、数据对比）
- html_renderer: HTML 渲染（含 CSS 样式、响应式布局、交互）
"""
try:
    from .markdown_renderer import render_markdown
    from .html_renderer import render_html
except ImportError:
    from markdown_renderer import render_markdown
    from html_renderer import render_html

__all__ = [
    "render_markdown",
    "render_html",
]
