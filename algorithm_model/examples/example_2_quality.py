"""
示例 2: 质量评估 + AI 优化

演示：
- 球面评估（公认难优化）
- 车身曲面评估
- AI 模拟退火优化
- 优化前后对比
"""
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api import (
    build_car, evaluate_surface, optimize_surface,
)


def make_sphere(u_size: int = 20, v_size: int = 20, R: float = 2.0) -> np.ndarray:
    """构造 (u_size, v_size, 3) 球面网格"""
    u = np.linspace(0, np.pi, u_size)
    v = np.linspace(0, np.pi, v_size)
    U, V = np.meshgrid(u, v)
    X = R * np.sin(U) * np.cos(V)
    Y = R * np.sin(U) * np.sin(V)
    Z = R * np.cos(U)
    return np.stack([X, Y, Z], axis=-1)


def make_car_panel() -> tuple:
    """从车壳提取 (49, 25, 3) 曲面网格"""
    parts = build_car()
    body = parts["body"]
    n_long, n_circ = 49, 25
    surface = body.vertices[:n_long * n_circ].reshape(n_long, n_circ, 3)
    return surface, parts["body"]


def test_sphere():
    """球面评估 + 优化"""
    print("=" * 60)
    print("【球面 - 公认难优化曲面】")
    print("=" * 60)

    sphere = make_sphere()

    # 1) 评估
    print("\n1) 初始评估")
    report = evaluate_surface(sphere, "球面")
    print(f"   等级: {report.grade}")
    print(f"   G0: {report.g0_count} | G1: {report.g1_count} | G2: {report.g2_count}")
    print(f"   G1 比率: {report.g1_ratio} | G2 比率: {report.g2_ratio}")
    print(f"   最大跳变: {report.max_curvature_jump}°")
    print(f"   反射线评分: {report.reflection_score}")

    # 2) 优化
    print("\n2) AI 模拟退火优化 (80 次迭代)")
    t0 = time.time()
    result = optimize_surface(sphere, "球面", max_iter=80, seed=42)
    dt = time.time() - t0

    print(f"   耗时: {dt:.3f}s | 实际迭代: {result.iterations}")
    print(f"   等级: {result.initial_grade} → {result.final_grade}")
    print(f"   G2: {result.initial_g2} → {result.final_g2} (Δ={result.final_g2 - result.initial_g2:+d})")
    print(f"   反射线: {result.initial_reflection} → {result.final_reflection} (Δ={result.final_reflection - result.initial_reflection:+.3f})")

    # 3) 收敛曲线
    print(f"\n3) 收敛曲线 (前 10 个值):")
    print(f"   {result.convergence_curve[:10]}")
    print(f"   末值: {result.convergence_curve[-1]:.4f}")


def test_car_panel():
    """车身曲面评估 + 优化"""
    print("\n" + "=" * 60)
    print("【车身侧视曲面 - 实际工业场景】")
    print("=" * 60)

    surface, body = make_car_panel()
    print(f"\n曲面尺寸: {surface.shape} (49 × 25 = {49*25} 顶点)")

    # 1) 评估
    print("\n1) 初始评估")
    report = evaluate_surface(surface, "车身侧视")
    print(f"   等级: {report.grade}")
    print(f"   G2 比率: {report.g2_ratio}")
    print(f"   反射线评分: {report.reflection_score}")

    # 2) 优化
    print("\n2) AI 模拟退火优化 (150 次迭代)")
    t0 = time.time()
    result = optimize_surface(surface, "车身侧视", max_iter=150, seed=42)
    dt = time.time() - t0

    print(f"   耗时: {dt:.3f}s | 实际迭代: {result.iterations}")
    print(f"   等级: {result.initial_grade} → {result.final_grade}")
    print(f"   G2: {result.initial_g2} → {result.final_g2} (Δ={result.final_g2 - result.initial_g2:+d})")
    print(f"   反射线: {result.initial_reflection} → {result.final_reflection} (Δ={result.final_reflection - result.initial_reflection:+.3f})")

    # 3) 优化前后可视化（用 matplotlib 画曲面）
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=(14, 6))

        ax1 = fig.add_subplot(121, projection="3d")
        X, Y, Z = surface[..., 0], surface[..., 1], surface[..., 2]
        ax1.plot_surface(X, Y, Z, cmap="coolwarm", alpha=0.8)
        ax1.set_title(f"优化前: {result.initial_grade} 级\n反射线: {result.initial_reflection}")

        ax2 = fig.add_subplot(122, projection="3d")
        X2, Y2, Z2 = result.best_surface[..., 0], result.best_surface[..., 1], result.best_surface[..., 2]
        ax2.plot_surface(X2, Y2, Z2, cmap="viridis", alpha=0.8)
        ax2.set_title(f"优化后: {result.final_grade} 级\n反射线: {result.final_reflection}")

        output_dir = Path(__file__).parent.parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        out_path = output_dir / "car_panel_optimization.png"
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"\n3) 对比图已保存: {out_path.name}")
    except ImportError:
        print("\n3) 跳过可视化（需 matplotlib）")


if __name__ == "__main__":
    test_sphere()
    test_car_panel()
    print("\n" + "=" * 60)
    print("✅ 示例 2 完成")
    print("=" * 60)
