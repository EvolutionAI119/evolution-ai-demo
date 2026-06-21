"""
EVOLUTION AI - 汽车A级曲面核心模块 (v2 重构版)
- 全向量化法向量计算
- 严格的G0/G1/G2 连续性评估
- 改进的AI优化 (基于曲率变化目标)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Any
import json
from math import comb


# ============================================================
# 数据结构
# ============================================================

@dataclass
class CarParams:
    """整车级参数"""
    L: float = 4.7
    W: float = 1.85
    H: float = 1.45
    wheelbase: float = 2.8
    hood_angle: float = 12.0
    roof_arc: float = 0.35
    windshield_rake: float = 28.0
    rear_angle: float = 22.0
    fender_prominence: float = 0.15
    waist_line: float = 0.85


@dataclass
class QualityReport:
    """质量报告"""
    panel_name: str = ""
    n_samples: int = 0
    g0_count: int = 0
    g1_count: int = 0
    g2_count: int = 0
    max_curvature_jump: float = 0.0
    mean_curvature: float = 0.0
    reflection_score: float = 0.0
    overall_grade: str = "B"
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Bezier 工具
# ============================================================

def bernstein(u: np.ndarray, n: int, i: int) -> np.ndarray:
    return comb(n, i) * (u ** i) * ((1 - u) ** (n - i))


def bezier_surface_vec(u: np.ndarray, v: np.ndarray, ctrl: np.ndarray) -> np.ndarray:
    """向量化Bezier曲面"""
    n, m = 3, 3
    Bu = np.stack([bernstein(u, n, i) for i in range(n + 1)], axis=0)  # (4, len(u))
    Bv = np.stack([bernstein(v, m, j) for j in range(m + 1)], axis=0)  # (4, len(v))
    # points[iu, iv, :] = sum_ij Bu[i,iu] * Bv[j,iv] * ctrl[i,j,:]
    #  = sum_ij Bu[i,iu] * Bv[j,iv] * ctrl[i,j]'
    # 收缩为 (iu, iv, 3)
    weights = np.einsum('iu,jv->ijuv', Bu, Bv)  # (4,4,len(u),len(v))
    return np.einsum('ijuv,ijc->uvc', weights, ctrl)


# ============================================================
# 车身曲面控制点构造
# ============================================================

def build_side_panel_ctrl(params: CarParams) -> np.ndarray:
    """侧围控制点 (4x4x3):  v方向=下→上(0→3),  u方向=前→后(0→3)"""
    L, H = params.L, params.H
    hood_a = np.tan(np.radians(params.hood_angle))
    rear_a = np.tan(np.radians(params.rear_angle))
    roof_arc = params.roof_arc
    waist = params.waist_line

    ctrl = np.zeros((4, 4, 3))
    # 含义: ctrl[v, u, :] = (x前-后位置, y下-上, z侧向外凸)
    for i_u in range(4):  # 前→后
        x_norm = i_u / 3.0
        x_pos = x_norm * L

        # v=0 底部
        if x_norm < 0.25:
            bulge = 0.05 * (0.25 - x_norm) / 0.25 * hood_a
        elif x_norm > 0.75:
            bulge = 0.05 * (x_norm - 0.75) / 0.25 * rear_a
        else:
            bulge = 0.0
        ctrl[0, i_u] = [x_pos, 0.0, bulge]

        # v=1 腰线
        y_waist = H * waist
        if x_norm < 0.25:
            bulge_w = 0.18 * (0.25 - x_norm) / 0.25 * hood_a
        elif x_norm > 0.75:
            bulge_w = 0.18 * (x_norm - 0.75) / 0.25 * rear_a
        else:
            bulge_w = 0.12
        ctrl[1, i_u] = [x_pos, y_waist, bulge_w]

        # v=2 车顶下沿
        y_top_b = H * 0.93
        arc_z = roof_arc * 0.35 * np.sin(np.pi * x_norm)
        ctrl[2, i_u] = [x_pos, y_top_b, arc_z + 0.05]

        # v=3 车顶
        arc_z_top = roof_arc * 0.25 * np.sin(np.pi * x_norm)
        ctrl[3, i_u] = [x_pos, H, arc_z_top]

    return ctrl


def build_top_panel_ctrl(params: CarParams) -> np.ndarray:
    """顶盖控制点 (4x4x3):  u=左→右,  v=前→后"""
    L, W = params.L, params.W
    roof_arc = params.roof_arc

    ctrl = np.zeros((4, 4, 3))
    for i_u in range(4):
        for i_v in range(4):
            x_norm = i_u / 3.0  # 横向
            y_norm = i_v / 3.0  # 纵向

            # 横向收缩（车顶比车体窄）
            x_shrink = 0.85 + 0.15 * (1 - abs(x_norm - 0.5) * 2)
            z_pos = (x_norm - 0.5) * W * x_shrink

            # 纵向收缩（前后收窄）
            if y_norm < 0.15:
                y_shrink = 0.3 + 0.7 * y_norm / 0.15
            elif y_norm > 0.85:
                y_shrink = 0.3 + 0.7 * (1 - y_norm) / 0.15
            else:
                y_shrink = 1.0
            y_pos = y_norm * L

            # 高度：中部隆起
            arc_h = roof_arc * 0.12 * (1 - abs(x_norm - 0.5) * 2) * \
                    np.sin(np.pi * y_norm)
            y_height = params.H + arc_h

            ctrl[i_u, i_v] = [y_pos, y_height, z_pos]

    return ctrl


def build_hood_ctrl(params: CarParams) -> np.ndarray:
    """引擎盖控制点 (4x4x3):  u=左→右,  v=前→后"""
    L, W = params.L, params.W
    hood_a = np.tan(np.radians(params.hood_angle))

    ctrl = np.zeros((4, 4, 3))
    y_base = 0.4
    y_len = 1.0

    for i_u in range(4):
        for i_v in range(4):
            x_norm = i_u / 3.0
            y_norm = i_v / 3.0

            z = (x_norm - 0.5) * W * 0.95
            y_pos = y_base + y_norm * y_len
            h_drop = hood_a * y_norm * 0.4
            central = 0.04 * (1 - abs(x_norm - 0.5) * 2)

            x = y_pos
            y = params.H * 0.62 - h_drop + central

            ctrl[i_u, i_v] = [x, y, z]

    return ctrl


# ============================================================
# 曲率与质量评估
# ============================================================

def compute_normals(points: np.ndarray) -> np.ndarray:
    """
    鲁棒法向量计算（向量化）
    points: (U, V, 3)
    返回: (U, V, 3) 单位法向量
    """
    U, V, _ = points.shape
    normals = np.zeros_like(points)

    # 中心差分
    if U < 3 or V < 3:
        return normals

    du = points[2:, 1:-1] - points[:-2, 1:-1]  # (U-2, V-2, 3)
    dv = points[1:-1, 2:] - points[1:-1, :-2]

    n = np.cross(du, dv)  # (U-2, V-2, 3)
    n_norm = np.linalg.norm(n, axis=2, keepdims=True)
    n_norm[n_norm < 1e-9] = 1.0
    n_normalized = n / n_norm

    # 填充内部点
    normals[1:-1, 1:-1] = n_normalized

    # 边界外推
    normals[0, :] = normals[1, :]
    normals[-1, :] = normals[-2, :]
    normals[:, 0] = normals[:, 1]
    normals[:, -1] = normals[:, -2]

    # 再次归一化
    n_norm = np.linalg.norm(normals, axis=2, keepdims=True)
    n_norm[n_norm < 1e-9] = 1.0
    return normals / n_norm


def assess_quality(points: np.ndarray, panel_name: str = "") -> QualityReport:
    """A 级曲面质量评估"""
    U, V, _ = points.shape
    report = QualityReport(panel_name=panel_name)
    if U < 3 or V < 3:
        return report

    normals = compute_normals(points)

    # 评估点：内部区域（避开边界）
    g0 = g1 = g2 = 0
    total = 0
    max_jump = 0.0
    curvatures = []

    for i in range(1, U - 1):
        for j in range(1, V - 1):
            n_cur = normals[i, j]
            n_u = normals[i + 1, j]
            n_v = normals[i, j + 1]

            # 跳过零向量
            if np.linalg.norm(n_cur) < 1e-6:
                continue

            dot_u = np.clip(np.dot(n_cur, n_u), -1, 1)
            angle_u = np.degrees(np.arccos(abs(dot_u)))  # 用abs避免翻转
            dot_v = np.clip(np.dot(n_cur, n_v), -1, 1)
            angle_v = np.degrees(np.arccos(abs(dot_v)))

            # G0: 位置连续
            g0 += 1

            # G1: 切线连续 (法向量夹角 < 5°)
            if angle_u < 5 and angle_v < 5:
                g1 += 1

            # G2: 曲率连续 (夹角 < 2°)
            if angle_u < 2 and angle_v < 2:
                g2 += 1

            local_jump = max(angle_u, angle_v)
            max_jump = max(max_jump, local_jump)
            curvatures.append(local_jump)
            total += 1

    report.n_samples = total
    report.g0_count = g0
    report.g1_count = g1
    report.g2_count = g2
    report.max_curvature_jump = float(max_jump)
    report.mean_curvature = float(np.mean(curvatures)) if curvatures else 0.0

    # 反射线评分（基于曲率均匀性 + 整体平滑度）
    if curvatures:
        cv = np.std(curvatures) / (np.mean(curvatures) + 1e-6)
        # 平滑度：平均曲率越小越好
        smooth_score = max(0, 1.0 - np.mean(curvatures) / 10.0)
        uniform_score = max(0, 1.0 - cv / 3.0)
        report.reflection_score = float((smooth_score + uniform_score) / 2)

    # 综合等级
    g2_ratio = g2 / max(total, 1)
    g1_ratio = g1 / max(total, 1)
    if g2_ratio > 0.85 and report.reflection_score > 0.7:
        report.overall_grade = "A"
    elif g1_ratio > 0.7 and report.reflection_score > 0.5:
        report.overall_grade = "B"
    elif g1_ratio > 0.4:
        report.overall_grade = "C"
    else:
        report.overall_grade = "D"

    report.details = {
        "g2_ratio": g2_ratio,
        "g1_ratio": g1_ratio,
        "reflection_lines_smooth": report.reflection_score > 0.6,
    }

    return report


# ============================================================
# AI 智能优化
# ============================================================

def smoothness_metric(ctrl: np.ndarray) -> float:
    """
    曲面光顺度度量：法向量跳变平方和
    """
    u = np.linspace(0, 1, 30)
    v = np.linspace(0, 1, 30)
    pts = bezier_surface_vec(u, v, ctrl)
    normals = compute_normals(pts)

    # 内部点的法向量跳变
    diffs_u = np.linalg.norm(np.diff(normals[1:-1, 1:-1], axis=0), axis=2)
    diffs_v = np.linalg.norm(np.diff(normals[1:-1, 1:-1], axis=1), axis=2)
    return float(np.sum(diffs_u ** 2) + np.sum(diffs_v ** 2))


def ai_optimize_surface(initial_ctrl: np.ndarray,
                        target_smoothness: float = 0.5,
                        iterations: int = 150,
                        seed: int = 42) -> Tuple[np.ndarray, List[float]]:
    """
    AI 智能优化：模拟退火 + 曲率光顺目标
    - 保留4个角点（边界条件）
    - 调整中间控制点的z分量（控制曲面外凸/内凹）
    """
    np.random.seed(seed)
    ctrl = initial_ctrl.copy()
    n, m, _ = ctrl.shape
    best_ctrl = ctrl.copy()
    best_cost = smoothness_metric(ctrl)
    history = [best_cost]

    # 自适应学习率
    lr = 0.08
    # 起始温度 = 成本的一定比例
    temperature = max(best_cost * 0.5, 1.0)
    cooling = 0.97
    min_temp = 0.005

    for it in range(iterations):
        new_ctrl = best_ctrl.copy()

        # 随机扰动内部控制点
        for i in range(1, n - 1):
            for j in range(1, m - 1):
                # 主要扰动 z 分量（控制曲面形状）
                noise_z = np.random.randn() * lr * 0.4
                # 次要扰动 y 分量（控制高度）
                noise_y = np.random.randn() * lr * 0.1
                new_ctrl[i, j, 2] += noise_z
                new_ctrl[i, j, 1] += noise_y

        new_cost = smoothness_metric(new_ctrl)
        delta = new_cost - best_cost

        if delta < 0 or np.random.random() < np.exp(-delta / max(temperature, min_temp)):
            best_ctrl = new_ctrl
            best_cost = new_cost

        temperature *= cooling
        history.append(best_cost)

        if best_cost < target_smoothness:
            break

    return best_ctrl, history


# ============================================================
# 主流程
# ============================================================

def generate_car_surfaces(params: CarParams, resolution: int = 40) -> Dict[str, np.ndarray]:
    u = np.linspace(0, 1, resolution)
    v = np.linspace(0, 1, resolution)

    side_ctrl = build_side_panel_ctrl(params)
    side_points = bezier_surface_vec(u, v, side_ctrl)

    top_ctrl = build_top_panel_ctrl(params)
    top_points = bezier_surface_vec(u, v, top_ctrl)

    hood_ctrl = build_hood_ctrl(params)
    hood_points = bezier_surface_vec(u, v, hood_ctrl)

    return {
        "side": side_points,
        "top": top_points,
        "hood": hood_points,
    }


def run_full_pipeline(params: CarParams,
                      ai_optimize: bool = True,
                      iterations: int = 100,
                      resolution: int = 40) -> Dict[str, Any]:
    """端到端流水线"""
    surfaces = generate_car_surfaces(params, resolution=resolution)
    reports_before = {n: assess_quality(p, n) for n, p in surfaces.items()}

    result = {
        "surfaces_before": surfaces,
        "reports_before": reports_before,
    }

    if ai_optimize:
        side_ctrl = build_side_panel_ctrl(params)
        opt_ctrl, history = ai_optimize_surface(side_ctrl, iterations=iterations)

        u = np.linspace(0, 1, resolution)
        v = np.linspace(0, 1, resolution)
        optimized_side = bezier_surface_vec(u, v, opt_ctrl)
        optimized_report = assess_quality(optimized_side, "side")

        result["surfaces_after"] = {**surfaces, "side": optimized_side}
        result["reports_after"] = {**reports_before, "side": optimized_report}
        result["optimization_history"] = history
        result["optimized_ctrl"] = opt_ctrl

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("EVOLUTION AI v2 - 汽车A级曲面建模DEMO")
    print("=" * 60)

    params = CarParams()
    print(f"\n📐 参数: L={params.L} W={params.W} H={params.H}")

    result = run_full_pipeline(params, ai_optimize=True, iterations=120)

    print("\n📊 质量评估（优化前）:")
    for name, rep in result["reports_before"].items():
        print(f"  [{name:6s}] 等级: {rep.overall_grade} | G2: {rep.g2_count:4d} | "
              f"反射线: {rep.reflection_score:.3f} | "
              f"最大跳变: {rep.max_curvature_jump:.2f}°")

    if "reports_after" in result:
        print("\n🤖 AI 智能优化后:")
        for name, rep in result["reports_after"].items():
            print(f"  [{name:6s}] 等级: {rep.overall_grade} | G2: {rep.g2_count:4d} | "
                  f"反射线: {rep.reflection_score:.3f} | "
                  f"最大跳变: {rep.max_curvature_jump:.2f}°")
        history = result["optimization_history"]
        print(f"\n📈 优化收敛: {history[0]:.2f} → {history[-1]:.2f} "
              f"(迭代 {len(history)} 次)")
    print("\n✅ DEMO 运行完成")
