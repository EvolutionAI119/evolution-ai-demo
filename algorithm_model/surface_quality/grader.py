"""
综合等级评定器

等级标准（汽车 A 级曲面行业标准）：
- A 级: G2 比率 > 85% 且反射线 > 0.7
- B 级: G2 比率 > 70% 且反射线 > 0.5
- C 级: G2 比率 > 50%
- D 级: 其他
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any
from .continuity import check_g0_g1_g2
from .reflection import compute_reflection_score


@dataclass
class QualityReport:
    """完整质量报告"""
    panel_name: str = ""
    grade: str = "B"
    g0_count: int = 0
    g1_count: int = 0
    g2_count: int = 0
    g1_ratio: float = 0.0
    g2_ratio: float = 0.0
    max_curvature_jump: float = 0.0
    mean_curvature: float = 0.0
    reflection_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


def _compute_grade(g2_ratio: float, reflection: float) -> str:
    """根据 G2 比率和反射线评分定级"""
    if g2_ratio > 0.85 and reflection > 0.7:
        return "A"
    elif g2_ratio > 0.70 and reflection > 0.5:
        return "B"
    elif g2_ratio > 0.50:
        return "C"
    else:
        return "D"


def assess_quality(
    surface_points: np.ndarray,
    panel_name: str = "panel",
    g1_threshold: float = 5.0,
    g2_threshold: float = 2.0,
) -> QualityReport:
    """
    评估曲面质量（综合 G0/G1/G2 + 反射线 + 等级）

    Args:
        surface_points: (N, M, 3) 网格点云
        panel_name: 面板名称
        g1_threshold: G1 判定阈值（度）
        g2_threshold: G2 判定阈值（度）

    Returns:
        QualityReport
    """
    n, m = surface_points.shape[:2]
    g0, g1, g2, max_jump = check_g0_g1_g2(surface_points, g1_threshold, g2_threshold)
    reflection = compute_reflection_score(surface_points)
    g1_ratio = g1 / max(1, g0)
    g2_ratio = g2 / max(1, g0)

    # 平均曲率
    from .curvature import angle_between, estimate_normals
    normals = estimate_normals(surface_points)
    curvatures = []
    for i in range(n - 1):
        for j in range(m - 1):
            curvatures.append(angle_between(normals[i, j], normals[i + 1, j]))
            curvatures.append(angle_between(normals[i, j], normals[i, j + 1]))
    mean_curv = float(np.mean(curvatures)) if curvatures else 0.0

    grade = _compute_grade(g2_ratio, reflection)

    return QualityReport(
        panel_name=panel_name,
        grade=grade,
        g0_count=g0,
        g1_count=g1,
        g2_count=g2,
        g1_ratio=round(g1_ratio, 3),
        g2_ratio=round(g2_ratio, 3),
        max_curvature_jump=round(max_jump, 2),
        mean_curvature=round(mean_curv, 3),
        reflection_score=round(reflection, 3),
        details={
            "n_samples": n * m,
            "g1_threshold": g1_threshold,
            "g2_threshold": g2_threshold,
        },
    )
