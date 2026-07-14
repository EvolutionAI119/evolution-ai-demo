"""
示例 3: 视频脚本生成 + 渲染

演示：
- 3 套内置模板
- 自定义分镜
- Markdown 渲染
- HTML 渲染
- 输出到文件
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api import make_storyboard, render_storyboard
from storyboard import save_storyboard_json


def test_builtin_templates():
    """3 套内置模板"""
    print("=" * 60)
    print("1) 3 套内置模板")
    print("=" * 60)

    for template in ["car_promotion", "tech_demo", "minimal_showcase"]:
        sb = make_storyboard(template=template, duration=90)
        print(f"\n📋 {template}:")
        print(f"   标题: {sb.title}")
        print(f"   时长: {sb.total_duration}s | 分镜: {len(sb.scenes)} 个")
        print(f"   卖点: {sb.key_features}")
        for s in sb.scenes:
            print(f"   [{s.scene_id:>2d}] {s.duration_sec:>4.1f}s | {s.name} | {s.camera}")


def test_custom_storyboard():
    """自定义分镜"""
    print("\n" + "=" * 60)
    print("2) 自定义分镜")
    print("=" * 60)

    custom_scenes = [
        {
            "duration": 5,
            "name": "痛点引入",
            "background": "黑底白字",
            "shot_type": "文字动画",
            "camera": "静态",
            "visual": "传统开发流程：4 周起步，反复修改 30 次",
            "subtitle": "3-4 周 起步 / 30 轮 修改",
            "audio": "低沉开场",
            "color_palette": ["#000000", "#FFFFFF"],
        },
        {
            "duration": 8,
            "name": "EVOLUTION AI 方案",
            "background": "渐变蓝紫",
            "shot_type": "Logo 揭示",
            "camera": "缓推",
            "visual": "平台 Logo + 核心数据：周期 65%↓ / 精度 ±0.1mm",
            "subtitle": "1 周 完成 / 1 次到位",
            "audio": "科技感配乐起",
            "color_palette": ["#0A0E27", "#4A6FFF", "#9D4EDD"],
            "data_highlights": [
                {"label": "开发周期", "before": "4 周", "after": "1 周"},
                {"label": "修改次数", "before": "30 轮", "after": "1 次"},
            ],
        },
        {
            "duration": 10,
            "name": "功能演示",
            "background": "黑底 + UI",
            "shot_type": "屏幕录制",
            "camera": "静态",
            "visual": "参数 → 造型 → 优化 → 质检 → 导出",
            "subtitle": "参数驱动 · AI 优化 · 全流程贯通",
            "audio": "UI 音效",
            "color_palette": ["#000000", "#4A6FFF"],
            "components_shown": ["body", "glass", "wheels", "headlights", "taillights"],
        },
        {
            "duration": 5,
            "name": "结尾",
            "background": "黑屏 + Logo",
            "shot_type": "Logo + CTA",
            "camera": "静态",
            "visual": "EVOLUTION AI Logo + 「立即申请试用」",
            "subtitle": "evolution.ai",
            "audio": "配乐收尾",
            "color_palette": ["#000000", "#4A6FFF", "#9D4EDD"],
        },
    ]

    sb = make_storyboard(
        product_name="EVOLUTION AI",
        duration=28,
        style="科技感 / 高端工业风",
        key_features=["周期 65%↓", "精度 ±0.1mm", "100% 覆盖", "全流程贯通"],
        audience="主机厂研发管理者",
        template="tech_demo",
        custom_scenes=custom_scenes,
    )

    print(f"标题: {sb.title}")
    print(f"时长: {sb.total_duration}s | 分镜: {len(sb.scenes)}")
    for s in sb.scenes:
        print(f"  [{s.scene_id}] {s.duration_sec:>4.1f}s | {s.name}")


def test_render_outputs():
    """渲染并保存输出"""
    print("\n" + "=" * 60)
    print("3) 渲染为 Markdown + HTML")
    print("=" * 60)

    sb = make_storyboard(template="car_promotion", duration=90)

    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    # Markdown
    md = render_storyboard(sb, "markdown")
    md_path = output_dir / "example_storyboard.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"✅ Markdown: {md_path} ({len(md):,} 字符)")

    # HTML
    html_doc = render_storyboard(sb, "html")
    html_path = output_dir / "example_storyboard.html"
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"✅ HTML: {html_path} ({len(html_doc):,} 字符)")

    # JSON
    json_path = output_dir / "example_storyboard.json"
    save_storyboard_json(sb, str(json_path))
    print(f"✅ JSON: {json_path} ({json_path.stat().st_size:,} bytes)")

    # 打印 Markdown 前 500 字符预览
    print(f"\n📄 Markdown 预览（前 500 字符）:")
    print("-" * 60)
    print(md[:500])
    print("...")


if __name__ == "__main__":
    test_builtin_templates()
    test_custom_storyboard()
    test_render_outputs()
    print("\n" + "=" * 60)
    print("✅ 示例 3 完成")
    print("=" * 60)
