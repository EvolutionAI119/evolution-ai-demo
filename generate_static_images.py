"""
用 matplotlib 生成静态PNG效果截图
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from core.car_surface import (
    CarParams, generate_car_surfaces, assess_quality,
    ai_optimize_surface, bezier_surface_vec, build_side_panel_ctrl
)


def plot_surface_3d(ax, points, title, color='viridis'):
    """绘制单个曲面"""
    x = points[:, :, 0]
    y = points[:, :, 1]
    z = points[:, :, 2]

    # 用高度做颜色
    z_norm = (z - z.min()) / (z.max() - z.min() + 1e-9)

    ax.plot_surface(x, y, z, facecolors=plt.cm.viridis(z_norm),
                    linewidth=0, antialiased=True, alpha=0.9)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.view_init(elev=20, azim=45)


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(out_dir, exist_ok=True)

    params = CarParams(L=4.7, W=1.85, H=1.45)
    print("1. 生成优化前曲面")
    surfs_before = generate_car_surfaces(params, resolution=40)

    print("2. AI 智能优化 (150次)")
    side_ctrl = build_side_panel_ctrl(params)
    opt_ctrl, history = ai_optimize_surface(side_ctrl, iterations=150)

    u = np.linspace(0, 1, 40)
    v = np.linspace(0, 1, 40)
    opt_side = bezier_surface_vec(u, v, opt_ctrl)
    surfs_after = {**surfs_before, "side": opt_side}

    # ============ 对比图 (分批渲染) ============
    print("3. 生成对比图 (PNG) - 分批渲染")
    for batch, (panel_set, title_suffix) in enumerate([
        ([("side", "侧围 (Side)")], "车身侧围 - 优化前 vs AI优化后"),
        ([("top", "顶盖 (Top)"), ("hood", "引擎盖 (Hood)")], "顶盖+引擎盖 - 优化前 vs AI优化后"),
    ]):
        n_panels = len(panel_set)
        fig = plt.figure(figsize=(7 * n_panels, 10))
        for col, (name, label) in enumerate(panel_set, start=1):
            ax_before = fig.add_subplot(2, n_panels, col, projection='3d')
            plot_surface_3d(ax_before, surfs_before[name], f"{label}\n优化前")
            ax_after = fig.add_subplot(2, n_panels, col + n_panels, projection='3d')
            plot_surface_3d(ax_after, surfs_after[name], f"{label}\nAI优化后")
        fig.suptitle(f"EVOLUTION AI - {title_suffix}",
                     fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()
        suffix = "_side" if batch == 0 else "_top_hood"
        out_path = os.path.join(out_dir, f"01_comparison{suffix}.png")
        plt.savefig(out_path, dpi=110, bbox_inches='tight', facecolor='white')
        plt.close()
        size = os.path.getsize(out_path)
        print(f"   ✅ {out_path} ({size/1024:.1f} KB)")

    # 合并主图标识
    import shutil
    src = os.path.join(out_dir, "01_comparison_top_hood.png")
    dst = os.path.join(out_dir, "01_comparison.png")
    shutil.copyfile(src, dst)

    # ============ 收敛曲线 ============
    print("4. 生成收敛曲线 (PNG)")
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(history, color='#FF6B6B', linewidth=2.5, marker='o',
            markersize=4, markevery=5)
    ax.fill_between(range(len(history)), history, alpha=0.2, color='#FF6B6B')
    ax.set_xlabel('迭代次数', fontsize=12)
    ax.set_ylabel('曲率光顺目标值 (越小越光顺)', fontsize=12)
    ax.set_title('AI 智能优化收敛曲线', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.text(0.6, 0.85,
            f'初始: {history[0]:.3f}\n最终: {history[-1]:.3f}\n'
            f'改进: {(1 - history[-1]/history[0])*100:.1f}%\n'
            f'迭代: {len(history)} 次',
            transform=ax.transAxes, fontsize=11,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "02_convergence.png"),
                dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ {out_dir}/02_convergence.png")

    # ============ 质量报告表 ============
    print("5. 生成质量报告图")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('off')

    reports_before = {n: assess_quality(p, n) for n, p in surfs_before.items()}
    reports_after = {n: assess_quality(p, n) for n, p in surfs_after.items()}

    table_data = [["面板", "等级", "G2连续", "反射线", "最大跳变(°)"]]
    for name in ["side", "top", "hood"]:
        r = reports_before[name]
        table_data.append([f"{name} (前)", r.overall_grade, str(r.g2_count),
                          f"{r.reflection_score:.3f}", f"{r.max_curvature_jump:.2f}"])
    for name in ["side", "top", "hood"]:
        r = reports_after[name]
        table_data.append([f"{name} (后)", r.overall_grade, str(r.g2_count),
                          f"{r.reflection_score:.3f}", f"{r.max_curvature_jump:.2f}"])

    table = ax.table(cellText=table_data, loc='center', cellLoc='center',
                     colWidths=[0.18, 0.12, 0.18, 0.18, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2.2)

    # 着色：第一行表头 + 优化后行用浅绿色
    for i in range(len(table_data)):
        for j in range(len(table_data[0])):
            cell = table[i, j]
            if i == 0:
                cell.set_facecolor('#4472C4')
                cell.set_text_props(weight='bold', color='white')
            elif i >= 4:  # 优化后
                cell.set_facecolor('#E2EFDA')

    ax.set_title("质量评估报告 - 优化前 vs AI优化后",
                 fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "03_quality_report.png"),
                dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   ✅ {out_dir}/03_quality_report.png")

    print("\n=== 优化结果 ===")
    for name in ["side", "top", "hood"]:
        b, a = reports_before[name], reports_after[name]
        print(f"  {name:6s}  等级: {b.overall_grade}→{a.overall_grade} | "
              f"G2: {b.g2_count}→{a.g2_count} | "
              f"反射线: {b.reflection_score:.3f}→{a.reflection_score:.3f}")


if __name__ == "__main__":
    main()
