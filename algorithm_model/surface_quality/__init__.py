"""
surface_quality - 曲面质量评估 + AI 优化

5 个子模块：
- curvature: 曲率估算（基于法向量变化）
- continuity: G0/G1/G2 连续性判定
- reflection: 反射线评分
- grader: 综合等级
- optimizer: AI 模拟退火优化
"""
from .curvature import estimate_normals, angle_between
from .continuity import check_g0_g1_g2
from .reflection import compute_reflection_score
from .grader import assess_quality, QualityReport
from .optimizer import ai_optimize, OptimizationResult

__all__ = [
    "estimate_normals",
    "angle_between",
    "check_g0_g1_g2",
    "compute_reflection_score",
    "assess_quality",
    "QualityReport",
    "ai_optimize",
    "OptimizationResult",
]
