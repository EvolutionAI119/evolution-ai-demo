"""
EVOLUTION AI - Streamlit 交互式 DEMO
运行: streamlit run app.py
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time

from core.car_surface import (
    CarParams, generate_car_surfaces, assess_quality,
    ai_optimize_surface, bezier_surface, run_full_pipeline,
    build_side_panel_ctrl, build_top_panel_ctrl, build_hood_ctrl,
    QualityReport
)

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="EVOLUTION AI - 汽车A级曲面",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚗 EVOLUTION AI - 汽车A级曲面智能建模与优化")
st.caption("v1.0 DEMO | AI驱动的车身曲面建模 · 实时修改 · 智能光顺优化")

# ============================================================
# 侧边栏 - 参数控制
# ============================================================

st.sidebar.header("📐 整车参数控制")

with st.sidebar:
    st.subheader("基础尺寸")
    L = st.slider("总长 L (m)", 4.0, 5.2, 4.7, 0.05)
    W = st.slider("总宽 W (m)", 1.7, 2.0, 1.85, 0.01)
    H = st.slider("总高 H (m)", 1.30, 1.65, 1.45, 0.01)
    wheelbase = st.slider("轴距 (m)", 2.5, 3.0, 2.8, 0.05)

    st.subheader("造型特征")
    hood_angle = st.slider("引擎盖倾角 (°)", 5, 25, 12, 1)
    roof_arc = st.slider("车顶弧度系数", 0.0, 0.8, 0.35, 0.05)
    windshield_rake = st.slider("前风挡倾角 (°)", 20, 35, 28, 1)
    rear_angle = st.slider("后风窗倾角 (°)", 15, 30, 22, 1)
    fender_prominence = st.slider("轮拱突出量 (m)", 0.05, 0.25, 0.15, 0.01)
    waist_line = st.slider("腰线高度比", 0.7, 0.95, 0.85, 0.01)

    st.subheader("AI 优化")
    enable_ai = st.checkbox("启用AI智能优化", value=True)
    iterations = st.slider("优化迭代次数", 10, 200, 80, 10) if enable_ai else 0
    resolution = st.slider("曲面分辨率", 20, 60, 40, 5)

# 构造参数对象
params = CarParams(
    L=L, W=W, H=H, wheelbase=wheelbase,
    hood_angle=hood_angle, roof_arc=roof_arc,
    windshield_rake=windshield_rake, rear_angle=rear_angle,
    fender_prominence=fender_prominence, waist_line=waist_line
)

# ============================================================
# 主区域
# ============================================================

col1, col2 = st.columns([3, 1])

with col1:
    tab_view, tab_compare, tab_metrics = st.tabs([
        "🎨 3D 视图", "🔄 优化对比", "📊 质量分析"
    ])

with col2:
    st.markdown("### 📋 当前参数")
    param_text = f"""
    - **尺寸**: {L}×{W}×{H} m
    - **轴距**: {wheelbase} m
    - **引擎盖**: {hood_angle}°
    - **车顶弧度**: {roof_arc}
    - **前风挡**: {windshield_rake}°
    - **后风窗**: {rear_angle}°
    - **腰线**: {waist_line}
    """
    st.markdown(param_text)

# ============================================================
# 数据生成
# ============================================================

@st.cache_data(show_spinner=False)
def _cached_pipeline(params_tuple, ai_optimize, iterations, resolution):
    params_dict = json.loads(params_tuple)
    params = CarParams(**params_dict)
    return run_full_pipeline(params, ai_optimize=ai_optimize, iterations=iterations)


with st.spinner("🎨 AI 正在生成车身曲面..."):
    params_dict = {
        "L": L, "W": W, "H": H, "wheelbase": wheelbase,
        "hood_angle": hood_angle, "roof_arc": roof_arc,
        "windshield_rake": windshield_rake, "rear_angle": rear_angle,
        "fender_prominence": fender_prominence, "waist_line": waist_line,
    }
    params_tuple = json.dumps(params_dict)
    result = _cached_pipeline(params_tuple, enable_ai, iterations, resolution)

surfaces = result["surfaces_before"]
reports = result["reports_before"]
surfaces_after = result.get("surfaces_after", surfaces)
reports_after = result.get("reports_after", reports)

# ============================================================
# Tab 1: 3D 视图
# ============================================================

def build_3d_figure(surfs, title="车身曲面"):
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("侧围 (Side)", "顶盖 (Top)", "引擎盖 (Hood)"),
        specs=[[{"type": "surface"}, {"type": "surface"}, {"type": "surface"}]],
        horizontal_spacing=0.05,
    )

    surface_data = [
        ("side", surfs["side"], 1, 1, "Viridis"),
        ("top", surfs["top"], 1, 2, "Plasma"),
        ("hood", surfs["hood"], 1, 3, "Cividis"),
    ]

    for name, pts, row, col, colorscale in surface_data:
        x = pts[:, :, 0]
        y = pts[:, :, 1]
        z = pts[:, :, 2]

        # 着色基于 z 值（高度）
        fig.add_trace(
            go.Surface(
                x=x, y=y, z=z,
                colorscale=colorscale,
                showscale=True,
                name=name,
                lighting=dict(ambient=0.5, diffuse=0.7, specular=0.3,
                              roughness=0.4, fresnel=0.2),
                lightposition=dict(x=100, y=200, z=300),
                opacity=0.95,
            ),
            row=row, col=col,
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        height=520,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


with tab_view:
    fig = build_3d_figure(surfaces, f"车身三大主要曲面 - 实时建模")
    st.plotly_chart(fig, use_container_width=True, key="view_main")

    st.info("""
    **🎯 操作说明**:
    - 拖动左侧参数滑块，3D 曲面会**实时更新**
    - 启用 AI 优化后，会自动光顺曲面
    - 鼠标拖拽可旋转视角，滚轮缩放
    """)

# ============================================================
# Tab 2: 优化对比
# ============================================================

with tab_compare:
    if "surfaces_after" in result:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### 📌 优化前")
            fig_before = build_3d_figure(surfaces, "原始曲面")
            st.plotly_chart(fig_before, use_container_width=True, key="cmp_before")

        with col_b:
            st.markdown("#### 🤖 AI 优化后")
            fig_after = build_3d_figure(surfaces_after, "AI 光顺后")
            st.plotly_chart(fig_after, use_container_width=True, key="cmp_after")

        if "optimization_history" in result:
            st.markdown("#### 📈 优化收敛曲线")
            history = result["optimization_history"]
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                y=history, mode='lines+markers',
                name='优化目标值',
                line=dict(color='#FF6B6B', width=2),
                marker=dict(size=4),
            ))
            fig_hist.update_layout(
                xaxis_title="迭代次数",
                yaxis_title="目标函数值 (越小越光顺)",
                height=300,
                showlegend=False,
            )
            st.plotly_chart(fig_hist, use_container_width=True, key="history")
    else:
        st.warning("请在左侧启用 AI 优化以查看对比效果")

# ============================================================
# Tab 3: 质量分析
# ============================================================

def render_quality_card(name: str, rep: QualityReport, col):
    with col:
        grade_color = {
            "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"
        }.get(rep.overall_grade, "⚪")

        st.markdown(f"""
        <div style="border: 1px solid #ddd; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
            <h4>{grade_color} {name.upper()} 面板</h4>
            <p><b>综合等级:</b> <span style="font-size: 20px;">{rep.overall_grade}</span></p>
            <p><b>G0 连续点:</b> {rep.g0_count}</p>
            <p><b>G1 连续点:</b> {rep.g1_count}</p>
            <p><b>G2 连续点:</b> {rep.g2_count}</p>
            <p><b>最大曲率跳变:</b> {rep.max_curvature_jump:.2f}°</p>
            <p><b>平均曲率:</b> {rep.mean_curvature:.2f}°</p>
            <p><b>反射线评分:</b> {rep.reflection_score:.3f}</p>
        </div>
        """, unsafe_allow_html=True)


with tab_metrics:
    st.markdown("### 📊 优化前质量评估")
    c1, c2, c3 = st.columns(3)
    render_quality_card("侧围", reports["side"], c1)
    render_quality_card("顶盖", reports["top"], c2)
    render_quality_card("引擎盖", reports["hood"], c3)

    if "reports_after" in result and reports_after != reports:
        st.markdown("### 🤖 优化后质量评估")
        c1, c2, c3 = st.columns(3)
        render_quality_card("侧围", reports_after["side"], c1)
        render_quality_card("顶盖", reports_after["top"], c2)
        render_quality_card("引擎盖", reports_after["hood"], c3)

        st.markdown("#### 🎯 改进幅度")
        improve_data = []
        for name in ["side", "top", "hood"]:
            before = reports[name]
            after = reports_after[name]
            improve_data.append({
                "曲面": name,
                "G2连续点(前)": before.g2_count,
                "G2连续点(后)": after.g2_count,
                "最大跳变(前)": f"{before.max_curvature_jump:.2f}°",
                "最大跳变(后)": f"{after.max_curvature_jump:.2f}°",
                "反射线(前)": f"{before.reflection_score:.3f}",
                "反射线(后)": f"{after.reflection_score:.3f}",
            })
        st.dataframe(improve_data, use_container_width=True)

# ============================================================
# 侧边栏 - 数据导出
# ============================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 数据导出")

if st.sidebar.button("导出控制点 (JSON)"):
    side_ctrl = build_side_panel_ctrl(params)
    top_ctrl = build_top_panel_ctrl(params)
    hood_ctrl = build_hood_ctrl(params)

    export_data = {
        "params": params_dict,
        "side_control_points": side_ctrl.tolist(),
        "top_control_points": top_ctrl.tolist(),
        "hood_control_points": hood_ctrl.tolist(),
        "quality": {
            name: {
                "grade": rep.overall_grade,
                "g2_count": rep.g2_count,
                "max_jump": rep.max_curvature_jump,
            }
            for name, rep in reports.items()
        }
    }
    st.sidebar.download_button(
        "📥 下载 JSON",
        data=json.dumps(export_data, indent=2, ensure_ascii=False),
        file_name=f"evolution_ai_{int(time.time())}.json",
        mime="application/json",
    )

# ============================================================
# 页脚
# ============================================================

st.markdown("---")
st.caption("""
**EVOLUTION AI v1.0 DEMO** | 基于 Bezier 曲面的参数化车身建模 ·
AI 优化算法: 模拟退火 + 曲率光顺目标函数 ·
质量评估: G0/G1/G2 连续性 + 反射线分析
""")
