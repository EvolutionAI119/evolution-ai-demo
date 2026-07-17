"""
EVOLUTION AI 算法模型 - 统一对外 API

5 个高层 API：
1. build_car(params)            - 构建完整汽车（返回 8 部件 dict）
2. evaluate_surface(points)     - 评估曲面质量（返回 QualityReport）
3. optimize_surface(points)     - AI 优化曲面（返回 OptimizationResult）
4. generate_storyboard(...)     - 生成视频脚本（返回 Storyboard）
5. render_storyboard(sb, fmt)   - 渲染视频脚本（返回 md/html 字符串）

设计原则：
- 一个函数 = 一个完整工作流
- 函数签名稳定，便于跨项目调用
- 内部细节封装，对外只暴露数据类
"""
from typing import Dict, Any, Optional
import trimesh
import numpy as np

# Car Modeling（兼容包导入和直接导入）
try:
    from .car_modeling import CarParams, build_full_car, compute_stats
except ImportError:
    from car_modeling import CarParams, build_full_car, compute_stats

# Surface Quality
try:
    from .surface_quality import (
        assess_quality, ai_optimize, QualityReport, OptimizationResult,
    )
except ImportError:
    from surface_quality import (
        assess_quality, ai_optimize, QualityReport, OptimizationResult,
    )

# Storyboard
try:
    from .storyboard import generate_storyboard, save_storyboard_json, Storyboard
except ImportError:
    from storyboard import generate_storyboard, save_storyboard_json, Storyboard

# Storyboard Viewer
try:
    from .storyboard_viewer import render_markdown, render_html
except ImportError:
    from storyboard_viewer import render_markdown, render_html


# ============================================================
# 1. 整车造型
# ============================================================

def build_car(params: Optional[CarParams] = None) -> Dict[str, trimesh.Trimesh]:
    """
    构建完整汽车造型

    Args:
        params: CarParams 对象，None 则用默认值

    Returns:
        dict: {body, glass, wheels, headlights, taillights, grille, mirrors, seams}

    Example:
        >>> params = CarParams(L=4.8, W=1.88, H=1.48, roof_arc=0.55)
        >>> parts = build_car(params)
        >>> parts['body'].vertices.shape
        (2352, 3)
    """
    if params is None:
        params = CarParams()
    return build_full_car(params)


def get_car_stats(params: Optional[CarParams] = None) -> Dict[str, Any]:
    """获取整车统计信息"""
    if params is None:
        params = CarParams()
    parts = build_full_car(params)
    return compute_stats(parts)


# ============================================================
# 2. 曲面质量评估
# ============================================================

def evaluate_surface(
    surface_points: np.ndarray,
    panel_name: str = "panel",
) -> QualityReport:
    """
    评估 (N, M, 3) 网格曲面的质量

    Args:
        surface_points: 网格点云 (N, M, 3)
        panel_name: 面板名称

    Returns:
        QualityReport（grade / G0/G1/G2 / 反射线评分）

    Example:
        >>> u = np.linspace(0, np.pi, 16)
        >>> v = np.linspace(0, np.pi, 16)
        >>> U, V = np.meshgrid(u, v)
        >>> X, Y, Z = 2*np.sin(U)*np.cos(V), 2*np.sin(U)*np.sin(V), 2*np.cos(U)
        >>> surface = np.stack([X, Y, Z], axis=-1)
        >>> report = evaluate_surface(surface, "球面")
        >>> report.grade
        'D'
    """
    return assess_quality(surface_points, panel_name)


# ============================================================
# 3. AI 曲面优化
# ============================================================

def optimize_surface(
    surface_points: np.ndarray,
    panel_name: str = "panel",
    max_iter: int = 150,
    seed: int = 42,
) -> OptimizationResult:
    """
    用 AI 模拟退火算法优化曲面光顺度

    Args:
        surface_points: 初始网格 (N, M, 3)
        panel_name: 面板名称
        max_iter: 最大迭代次数
        seed: 随机种子

    Returns:
        OptimizationResult（含优化前后对比 + 收敛曲线 + 最佳曲面）
    """
    return ai_optimize(surface_points, panel_name, max_iter=max_iter, seed=seed)


# ============================================================
# 4. 视频脚本生成
# ============================================================

def make_storyboard(
    product_name: str = "EVOLUTION AI",
    duration: float = 90,
    style: str = "高端汽车广告 / 科技感蓝紫色调",
    key_features: Optional[list] = None,
    audience: str = "汽车行业研发管理者",
    template: str = "car_promotion",
    custom_scenes: Optional[list] = None,
) -> Storyboard:
    """
    生成视频脚本

    Args:
        product_name: 产品名
        duration: 目标时长（秒）
        style: 视觉风格
        key_features: 核心卖点
        audience: 目标观众
        template: 模板名 (car_promotion / tech_demo / minimal_showcase)
        custom_scenes: 自定义分镜列表（覆盖模板）

    Returns:
        Storyboard
    """
    return generate_storyboard(
        product_name=product_name,
        duration=duration,
        style=style,
        key_features=key_features,
        audience=audience,
        template=template,
        custom_scenes=custom_scenes,
    )


# ============================================================
# 5. 视频脚本渲染
# ============================================================

def render_storyboard(
    storyboard: Storyboard,
    fmt: str = "markdown",
) -> str:
    """
    渲染视频脚本为可视化文档

    Args:
        storyboard: Storyboard 对象
        fmt: 输出格式 (markdown / html)

    Returns:
        文档字符串
    """
    fmt = fmt.lower()
    if fmt in ("md", "markdown"):
        return render_markdown(storyboard)
    elif fmt == "html":
        return render_html(storyboard)
    else:
        raise ValueError(f"不支持的格式 '{fmt}'，可选: markdown / html")


# ============================================================
# 一次性：跑完整流程（用于演示 / 自检）
# ============================================================

def run_full_pipeline(
    car_params: Optional[CarParams] = None,
    storyboard_template: str = "car_promotion",
) -> Dict[str, Any]:
    """
    跑完整流程：建模 → 提取面板 → 评估 → 优化 → 生成脚本 → 渲染

    Returns:
        dict: {car_parts, stats, quality_before, quality_after, storyboard, md, html}
    """
    if car_params is None:
        car_params = CarParams()
    parts = build_car(car_params)
    stats = get_car_stats(car_params)

    # 用 body 网格作为测试面板
    body = parts["body"]
    n_long, n_circ = 49, 25
    surface = body.vertices[:n_long * n_circ].reshape(n_long, n_circ, 3)

    quality_before = evaluate_surface(surface, "车身侧视")
    optimization = optimize_surface(surface, "车身侧视", max_iter=80)
    quality_after = evaluate_surface(optimization.best_surface, "车身侧视-优化后")

    sb = make_storyboard(template=storyboard_template)
    md = render_storyboard(sb, "markdown")
    html_doc = render_storyboard(sb, "html")

    return {
        "car_params": car_params.to_dict(),
        "car_parts": {k: len(v.vertices) for k, v in parts.items()},
        "stats": stats,
        "quality_before": quality_before,
        "quality_after": quality_after,
        "optimization": {
            "initial_grade": optimization.initial_grade,
            "final_grade": optimization.final_grade,
            "initial_g2": optimization.initial_g2,
            "final_g2": optimization.final_g2,
            "initial_reflection": optimization.initial_reflection,
            "final_reflection": optimization.final_reflection,
            "iterations": optimization.iterations,
        },
        "storyboard": sb,
        "markdown": md,
        "html": html_doc,
    }
