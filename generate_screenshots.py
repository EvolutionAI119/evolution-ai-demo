"""
生成 DEMO 效果截图
- 优化前后对比 3D 图
- 优化收敛曲线
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.car_surface import (
    CarParams, generate_car_surfaces, assess_quality,
    ai_optimize_surface, bezier_surface_vec as bezier_surface, run_full_pipeline,
    build_side_panel_ctrl
)


def build_comparison_figure(surfs_before, surfs_after, title=""):
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            "侧围 (优化前)", "顶盖 (优化前)", "引擎盖 (优化前)",
            "侧围 (AI优化后)", "顶盖 (AI优化后)", "引擎盖 (AI优化后)",
        ),
        specs=[[{"type": "surface"}] * 3, [{"type": "surface"}] * 3],
        horizontal_spacing=0.05,
        vertical_spacing=0.08,
    )

    surface_data = [
        (surfs_before, 1, "Viridis"),
        (surfs_after, 2, "Plasma"),
    ]

    surface_names = ["side", "top", "hood"]
    for surfs, row, colorscale in surface_data:
        for col, name in enumerate(surface_names, start=1):
            pts = surfs[name]
            x, y, z = pts[:, :, 0], pts[:, :, 1], pts[:, :, 2]
            fig.add_trace(
                go.Surface(
                    x=x, y=y, z=z,
                    colorscale=colorscale,
                    showscale=(col == 3),
                    lighting=dict(ambient=0.5, diffuse=0.7, specular=0.4,
                                  roughness=0.3, fresnel=0.3),
                    lightposition=dict(x=100, y=200, z=300),
                    opacity=0.95,
                ),
                row=row, col=col,
            )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        height=900,
        showlegend=False,
    )
    return fig


def build_convergence_figure(history):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=history,
        mode='lines+markers',
        name='优化目标值',
        line=dict(color='#FF6B6B', width=2.5),
        marker=dict(size=5),
    ))
    fig.update_layout(
        title=dict(text="AI 优化收敛曲线", x=0.5),
        xaxis_title="迭代次数",
        yaxis_title="曲率跳变目标值 (越小越光顺)",
        height=400,
    )
    return fig


def main():
    print("生成 DEMO 效果截图 ...")

    params = CarParams(
        L=4.7, W=1.85, H=1.45,
        hood_angle=12, roof_arc=0.35,
        windshield_rake=28, rear_angle=22,
        fender_prominence=0.15, waist_line=0.85,
    )

    print("  1. 优化前曲面生成")
    surfs_before = generate_car_surfaces(params)

    print("  2. AI 智能优化 (迭代 150 次)")
    side_ctrl = build_side_panel_ctrl(params)
    opt_ctrl, history = ai_optimize_surface(side_ctrl, iterations=150)

    u = np.linspace(0, 1, 40)
    v = np.linspace(0, 1, 40)
    opt_side = bezier_surface(u, v, opt_ctrl)
    surfs_after = {**surfs_before, "side": opt_side}

    print("  3. 生成对比图")
    fig_cmp = build_comparison_figure(
        surfs_before, surfs_after,
        "EVOLUTION AI - 优化前 vs AI智能优化后"
    )
    import os
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
    os.makedirs(out_dir, exist_ok=True)
    fig_cmp.write_html(os.path.join(out_dir, "01_comparison.html"))
    try:
        fig_cmp.write_image(os.path.join(out_dir, "01_comparison.png"), width=1400, height=900)
    except Exception as e:
        print(f"  (PNG导出失败,仅HTML: {e})")

    print("  4. 生成收敛曲线")
    fig_hist = build_convergence_figure(history)
    fig_hist.write_html(os.path.join(out_dir, "02_convergence.html"))
    try:
        fig_hist.write_image(os.path.join(out_dir, "02_convergence.png"), width=1200, height=500)
    except Exception as e:
        print(f"  (PNG导出失败,仅HTML: {e})")

    print("  5. 质量报告")
    reports_before = {n: assess_quality(p) for n, p in surfs_before.items()}
    reports_after = {n: assess_quality(p) for n, p in surfs_after.items()}

    print("\n  === 优化前 ===")
    for n, r in reports_before.items():
        print(f"    [{n}] 等级: {r.overall_grade}  G2: {r.g2_count}  "
              f"最大跳变: {r.max_curvature_jump:.2f}°  "
              f"反射线: {r.reflection_score:.3f}")

    print("\n  === 优化后 ===")
    for n, r in reports_after.items():
        print(f"    [{n}] 等级: {r.overall_grade}  G2: {r.g2_count}  "
              f"最大跳变: {r.max_curvature_jump:.2f}°  "
              f"反射线: {r.reflection_score:.3f}")

    print(f"\n  优化收敛: {history[0]:.4f} → {history[-1]:.4f}")
    print(f"\n  ✅ 截图已保存到 outputs/ 目录")


if __name__ == "__main__":
    main()
