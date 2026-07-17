"""
分镜模板库

3 套内置模板：
- car_promotion: 7 镜 90s 汽车产品宣传片
- tech_demo: 5 镜 45s 技术演示片
- minimal_showcase: 2 镜 50s 极简展示
"""
from typing import Dict, List, Any


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "car_promotion": {
        "name": "汽车产品宣传片",
        "scenes": [
            {
                "duration": 8,
                "name": "开场 · 行业转型",
                "background": "黑屏渐亮，金属质感流动",
                "shot_type": "渐变 + 粒子动画",
                "camera": "静态",
                "visual": "白色光点勾勒车身轮廓线，金属质感流动",
                "subtitle": "AI 正在重塑汽车造型设计",
                "audio": "科技感配乐起",
                "color_palette": ["#0A0E27", "#4A6FFF"],
            },
            {
                "duration": 12,
                "name": "构建过程 · 参数到整车",
                "background": "白底纯色，分屏布局",
                "shot_type": "分屏 / 渐次构建",
                "camera": "静态 + 局部放大",
                "visual": "左侧参数面板（10+ 维），右侧逐步出现：车壳→玻璃→4 轮→大灯→尾灯→格栅→后视镜→门缝",
                "subtitle": "10+ 维参数驱动完整汽车造型",
                "audio": "构建音节拍",
                "components_shown": ["body", "glass", "wheels", "headlights", "taillights", "grille", "mirrors", "seams"],
                "color_palette": ["#FFFFFF", "#4A6FFF", "#9D4EDD"],
            },
            {
                "duration": 18,
                "name": "360° 整车旋转展示",
                "background": "黑底哑光舞台，展厅灯光",
                "shot_type": "3/4 英雄镜头",
                "camera": "低角度环绕（车高 0.4 倍）",
                "visual": "完整汽车模型 360° 匀速旋转，金属车漆高光、玻璃透射、轮毂反光、灯带发光",
                "subtitle": "EVOLUTION AI - Class A Surface 智能平台",
                "audio": "配乐渐强",
                "components_shown": ["body", "glass", "wheels", "headlights", "taillights"],
                "color_palette": ["#000000", "#1A1F3A", "#4A6FFF"],
            },
            {
                "duration": 17,
                "name": "AI 优化对比",
                "background": "黑底，分屏布局",
                "shot_type": "分屏 / 反射线扫描",
                "camera": "静态",
                "visual": "左：优化前 B 级（反射线腰部折线）vs 右：优化后 A 级（反射线平滑）",
                "subtitle": "B → A 智能光顺升级",
                "audio": "机械光顺音",
                "color_palette": ["#0A0E27", "#FF6B6B", "#4ADE80"],
                "data_highlights": [
                    {"label": "G2 连续性", "before": "1142", "after": "1436"},
                    {"label": "反射线评分", "before": "0.782", "after": "0.877"},
                    {"label": "质量等级", "before": "B", "after": "A"},
                ],
            },
            {
                "duration": 15,
                "name": "多角度细节",
                "background": "黑底，四宫格",
                "shot_type": "四宫格 / 多视角",
                "camera": "静态",
                "visual": "前 3/4 / 侧视 / 顶视 / 后 3/4 四个视角并排",
                "subtitle": "全视角造型掌控",
                "audio": "配乐维持",
                "color_palette": ["#000000", "#4A6FFF"],
            },
            {
                "duration": 15,
                "name": "参数实时联动",
                "background": "黑底，右侧参数面板",
                "shot_type": "单画面 + 参数面板",
                "camera": "静态",
                "visual": "依次拖动 3 个滑块：车顶弧度/腰线/前挡风倾角，车身实时变形",
                "subtitle": "参数驱动 · 1 秒响应",
                "audio": "滑块音节拍",
                "color_palette": ["#0A0E27", "#4A6FFF", "#9D4EDD"],
                "data_highlights": [
                    {"label": "车顶弧度", "before": "0.35", "after": "0.55"},
                    {"label": "腰线高度", "before": "0.85", "after": "0.95"},
                    {"label": "前挡风倾角", "before": "28°", "after": "35°"},
                ],
            },
            {
                "duration": 5,
                "name": "结尾 · Logo",
                "background": "黑屏",
                "shot_type": "Logo 动画",
                "camera": "静态",
                "visual": "EVOLUTION AI logo（几何化汽车轮廓 + 神经网络连线）",
                "subtitle": "AI 驱动 A 级曲面设计革新",
                "audio": "配乐收尾",
                "color_palette": ["#000000", "#4A6FFF", "#9D4EDD"],
            },
        ],
    },
    "tech_demo": {
        "name": "技术演示片",
        "scenes": [
            {
                "duration": 5,
                "name": "问题陈述",
                "background": "白底，问题文字",
                "shot_type": "文字动画",
                "camera": "静态",
                "visual": "传统造型开发的痛点：3-4 周 / 反复修改 / 工具碎片化",
                "subtitle": "汽车 A 级曲面开发：3 周起步，30 轮修改",
                "audio": "低音提琴",
                "color_palette": ["#FFFFFF", "#1A1F3A"],
            },
            {
                "duration": 8,
                "name": "解决方案概述",
                "background": "渐变蓝紫",
                "shot_type": "Logo 揭示",
                "camera": "缓推",
                "visual": "EVOLUTION AI logo + 核心数据：周期 65%↓ / 精度 ±0.1mm",
                "subtitle": "一个平台，贯穿全程",
                "audio": "科技感起",
                "color_palette": ["#0A0E27", "#4A6FFF", "#9D4EDD"],
            },
            {
                "duration": 20,
                "name": "功能演示",
                "background": "黑底 + UI 叠加",
                "shot_type": "屏幕录制 + 旁白",
                "camera": "静态",
                "visual": "参数面板 → 实时 3D → AI 优化 → 质量报告 → 工程数据导出",
                "subtitle": "参数→造型→优化→质检→交付",
                "audio": "UI 音效 + 旁白",
                "color_palette": ["#000000", "#4A6FFF", "#9D4EDD"],
                "components_shown": ["body", "glass", "wheels", "headlights", "taillights", "grille", "mirrors"],
            },
            {
                "duration": 7,
                "name": "成果对比",
                "background": "分屏布局",
                "shot_type": "分屏对比",
                "camera": "静态",
                "visual": "传统方式 4 周 vs EVOLUTION AI 1 周，并排展示",
                "subtitle": "从 4 周到 1 周",
                "audio": "配乐高潮",
                "color_palette": ["#0A0E27", "#FF6B6B", "#4ADE80"],
                "data_highlights": [
                    {"label": "开发周期", "before": "4 周", "after": "1 周"},
                    {"label": "F5/F6/F7 检查", "before": "人工抽检", "after": "100% 覆盖"},
                ],
            },
            {
                "duration": 5,
                "name": "结尾 · 行动号召",
                "background": "黑屏 + Logo",
                "shot_type": "Logo + CTA",
                "camera": "静态",
                "visual": "EVOLUTION AI logo + 「立即申请试用」",
                "subtitle": "立即申请试用 → evolution.ai",
                "audio": "配乐收尾",
                "color_palette": ["#000000", "#4A6FFF"],
            },
        ],
    },
    "minimal_showcase": {
        "name": "极简展示",
        "scenes": [
            {
                "duration": 30,
                "name": "整体造型 360° 展示",
                "background": "渐变 #0A0E27 → #1A1F3A",
                "shot_type": "3D 环绕",
                "camera": "缓速环绕（0.5x 速度）",
                "visual": "完整汽车在渐变背景中 360° 旋转，金属高光，玻璃透射",
                "audio": "环境电子乐",
                "color_palette": ["#0A0E27", "#1A1F3A", "#4A6FFF"],
                "components_shown": ["body", "glass", "wheels", "headlights", "taillights", "grille", "mirrors"],
            },
            {
                "duration": 20,
                "name": "参数变形展示",
                "background": "渐变黑紫",
                "shot_type": "单画面 + 参数面板",
                "camera": "静态",
                "visual": "参数面板拖动 3 次：车顶弧度/腰线/前挡风倾角，车身实时变形",
                "subtitle": "参数即造型",
                "audio": "UI 音效",
                "color_palette": ["#0A0E27", "#4A6FFF", "#9D4EDD"],
            },
        ],
    },
}


def get_template(name: str) -> Dict[str, Any]:
    """
    获取模板

    Args:
        name: 模板名（car_promotion / tech_demo / minimal_showcase）

    Returns:
        模板字典
    """
    if name not in TEMPLATES:
        raise ValueError(
            f"未知模板 '{name}'，可选: {list(TEMPLATES.keys())}"
        )
    return TEMPLATES[name]


def list_templates() -> List[str]:
    """列出所有可用模板名"""
    return list(TEMPLATES.keys())
