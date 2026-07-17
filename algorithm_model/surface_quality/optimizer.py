"""
AI 模拟退火优化器

算法：
- 目标函数：法向跳变平方和（越小越光顺）
- 扰动：随机选一个内部点加高斯噪声
- 接受准则：Metropolis（目标更优直接接受；目标更差按概率 exp(-Δ/T) 接受）
- 降温：T *= cooling（指数降温）

适用于：曲面光顺、参数化造型优化、网格变形。
"""
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List
from .curvature import angle_between, estimate_normals
from .grader import assess_quality


@dataclass
class OptimizationResult:
    """优化结果"""
    initial_grade: str
    final_grade: str
    initial_g2: int
    final_g2: int
    initial_reflection: float
    final_reflection: float
    iterations: int
    convergence_curve: List[float] = field(default_factory=list)
    best_surface: np.ndarray = None


def _objective(surface_points: np.ndarray) -> float:
    """优化目标：法向跳变平方和（越小越光顺）"""
    n, m = surface_points.shape[:2]
    if n < 2 or m < 2:
        return 0.0
    normals = estimate_normals(surface_points)
    s = 0.0
    for i in range(n - 1):
        for j in range(m - 1):
            a1 = angle_between(normals[i, j], normals[i + 1, j])
            a2 = angle_between(normals[i, j], normals[i, j + 1])
            s += a1 * a1 + a2 * a2
    return s / max(1, (n - 1) * (m - 1))


def ai_optimize(
    surface_points: np.ndarray,
    panel_name: str = "panel",
    max_iter: int = 150,
    lr: float = 0.08,
    cooling: float = 0.97,
    min_temp: float = 0.005,
    seed: int = 42,
) -> OptimizationResult:
    """
    AI 模拟退火优化曲面光顺度

    Args:
        surface_points: (N, M, 3) 初始网格
        panel_name: 面板名称（用于报告）
        max_iter: 最大迭代次数
        lr: 初始学习率（扰动幅度）
        cooling: 冷却系数（每步 T *= cooling）
        min_temp: 最低温度（达到后停止）
        seed: 随机种子

    Returns:
        OptimizationResult
    """
    random.seed(seed)
    np.random.seed(seed)

    current = surface_points.copy()
    best = current.copy()
    initial_obj = _objective(current)
    current_obj = initial_obj
    best_obj = initial_obj

    T = 1.0
    convergence: List[float] = [current_obj]

    for it in range(max_iter):
        # 扰动：随机选一个内部点（边界点固定）
        i = random.randint(2, current.shape[0] - 3)
        j = random.randint(2, current.shape[1] - 3)
        noise = np.random.randn(3) * lr * T
        current[i, j] = best[i, j] + noise

        new_obj = _objective(current)

        # Metropolis 接受准则
        delta = new_obj - current_obj
        if delta < 0 or random.random() < np.exp(-delta / max(0.001, T)):
            current_obj = new_obj
            if new_obj < best_obj:
                best = current.copy()
                best_obj = new_obj

        convergence.append(current_obj)
        T *= cooling
        if T < min_temp:
            break

    # 重新评估最终质量
    initial_report = assess_quality(surface_points, panel_name)
    final_report = assess_quality(best, panel_name)

    return OptimizationResult(
        initial_grade=initial_report.grade,
        final_grade=final_report.grade,
        initial_g2=initial_report.g2_count,
        final_g2=final_report.g2_count,
        initial_reflection=initial_report.reflection_score,
        final_reflection=final_report.reflection_score,
        iterations=len(convergence) - 1,
        convergence_curve=convergence,
        best_surface=best,
    )
