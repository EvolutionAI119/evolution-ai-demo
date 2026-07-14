"""
EVOLUTION AI DEMO — Car Surface Design Studio
Streamlit + Plotly application for parametric car body design,
surface quality analysis and AI-assisted optimisation.

Features:
  - Bilingual UI (Chinese / English) via I18N dictionary
  - All length sliders display in mm (internal computation in m)
  - Enhanced control-point generation for car-like surfaces
  - Full-car 3D view built geometrically (no algorithm_model dependency)
  - Parts gallery showing individual components
  - Front/rear bumpers, enclosed body, surface trimming, multi-car-type, side windows
"""
import sys
import os
import copy
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so sibling packages are importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Import core modules
# ---------------------------------------------------------------------------
from core.car_surface import (
    CarParams as CoreCarParams,
    generate_car_surfaces,
    assess_quality,
    ai_optimize_surface,
    bezier_surface_vec,
    run_full_pipeline,
    build_side_panel_ctrl,
    build_top_panel_ctrl,
    build_hood_ctrl,
    QualityReport,
    _make_faces,
)

# NOTE: We intentionally do NOT import from algorithm_model so that
# the app works even when that package is unavailable.

# ---------------------------------------------------------------------------
# Import V2.1 car body builder (sweep-based parametric modelling)
# ---------------------------------------------------------------------------
try:
    from car_body_builder import (
        CarParams22, SIX_CAR_PRESETS as V21_PRESETS,
        apply_preset as v21_apply_preset, build_full_car_v21,
    )
    V21_AVAILABLE = True
except ImportError:
    V21_AVAILABLE = False

# ===================================================================
# Car type presets (mm values — converted to m inside read_params)
# ===================================================================
CAR_TYPE_PRESETS = {
    "sedan": {
        "label_zh": "轿车 (Sedan)",
        "label_en": "Sedan",
        "length": 4700, "width": 1850, "height": 1450,
        "wheelbase": 2700,
        "hood_angle": 15.0, "roof_arc": 0.5,
        "windshield_angle": 28.0, "rear_window_angle": 25.0,
        "wheel_arch": 150, "waistline": 0.75,
        "doors": 4,  # 4-door sedan
    },
    "suv": {
        "label_zh": "SUV",
        "label_en": "SUV",
        "length": 4800, "width": 1950, "height": 1530,
        "wheelbase": 2800,
        "hood_angle": 12.0, "roof_arc": 0.35,
        "windshield_angle": 25.0, "rear_window_angle": 22.0,
        "wheel_arch": 250, "waistline": 0.78,
        "doors": 4,
    },
    "coupe": {
        "label_zh": "轿跑 (Coupe)",
        "label_en": "Coupe",
        "length": 4750, "width": 1850, "height": 1390,
        "wheelbase": 2750,
        "hood_angle": 18.0, "roof_arc": 0.6,
        "windshield_angle": 33.0, "rear_window_angle": 35.0,
        "wheel_arch": 120, "waistline": 0.72,
        "doors": 2,
    },
    "hatchback": {
        "label_zh": "掀背 (Hatchback)",
        "label_en": "Hatchback",
        "length": 4300, "width": 1800, "height": 1480,
        "wheelbase": 2600,
        "hood_angle": 14.0, "roof_arc": 0.45,
        "windshield_angle": 27.0, "rear_window_angle": 38.0,
        "wheel_arch": 140, "waistline": 0.74,
        "doors": 4,
    },
    "mpv": {
        "label_zh": "MPV",
        "label_en": "MPV",
        "length": 4900, "width": 1900, "height": 1550,
        "wheelbase": 2900,
        "hood_angle": 8.0, "roof_arc": 0.25,
        "windshield_angle": 22.0, "rear_window_angle": 18.0,
        "wheel_arch": 160, "waistline": 0.80,
        "doors": 4,
    },
    "sport": {
        "label_zh": "跑车 (Sport)",
        "label_en": "Sport",
        "length": 4500, "width": 1950, "height": 1250,
        "wheelbase": 2650,
        "hood_angle": 18.0, "roof_arc": 0.60,
        "windshield_angle": 35.0, "rear_window_angle": 38.0,
        "wheel_arch": 180, "waistline": 0.70,
        "doors": 2,
    },
    "pickup": {
        "label_zh": "皮卡 (Pickup)",
        "label_en": "Pickup",
        "length": 5500, "width": 1950, "height": 1850,
        "wheelbase": 3400,
        "hood_angle": 10.0, "roof_arc": 0.30,
        "windshield_angle": 24.0, "rear_window_angle": 20.0,
        "wheel_arch": 200, "waistline": 0.78,
        "doors": 4,
    },
}


# ===================================================================
# I18N — Internationalisation dictionary
# ===================================================================
I18N = {
    "zh": {
        "app_title": "汽车曲面设计工作室",
        "lang_label": "语言",
        # Tabs
        "tab_3d": "3D 视图",
        "tab_opt": "优化对比",
        "tab_quality": "质量分析",
        # Sub-tabs under 3D
        "subtab_surface": "面板曲面",
        "subtab_fullcar": "整车视图",
        "subtab_parts": "零件视图",
        "subtab_partslist": "零件列表",
        # Sidebar sections
        "section_basic": "📐 基本尺寸",
        "section_styling": "🎨 造型特征",
        "section_ai": "🤖 AI 优化",
        "section_export": "💾 数据导出",
        "section_cartype": "🚘 车型选择",
        # Car type
        "cartype_label": "车型",
        # Parameters (mm)
        "param_length": "总长 (mm)",
        "param_width": "总宽 (mm)",
        "param_height": "总高 (mm)",
        "param_wheelbase": "轴距 (mm)",
        "param_wheel_arch": "轮拱突出量 (mm)",
        # Parameters (degrees / ratios)
        "param_hood_angle": "引擎盖倾角 (°)",
        "param_roof_arc": "车顶弧度",
        "param_windshield": "前风挡倾角 (°)",
        "param_rear_window": "后风窗倾角 (°)",
        "param_waistline": "腰线高度比",
        # Buttons
        "generate_btn": "生成曲面",
        "optimize_btn": "AI 优化",
        "reset_btn": "重置参数",
        "export_json_btn": "导出 JSON",
        "export_csv_btn": "导出 CSV",
        # Quality
        "quality_title": "曲面质量报告",
        "quality_g0": "G0 连续性",
        "quality_g1": "G1 连续性",
        "quality_g2": "G2 连续性",
        "quality_fairness": "光顺度",
        "quality_overall": "综合评分",
        "quality_notes": "备注",
        # Optimisation
        "opt_before": "优化前",
        "opt_after": "优化后",
        "opt_params_title": "参数对比",
        "opt_quality_title": "质量对比",
        # Surface names
        "surface_side": "侧围面板",
        "surface_top": "顶盖面板",
        "surface_hood": "引擎盖面板",
        # Full car
        "fullcar_title": "整车三维视图",
        "fullcar_no_assembler": "整车视图（几何构建）",
        "fullcar_parts_count": "零件数",
        "fullcar_vertices": "顶点数",
        "fullcar_faces": "面片数",
        # Part names
        "part_side_right": "右侧围",
        "part_side_left": "左侧围",
        "part_top": "顶盖",
        "part_hood": "引擎盖",
        "part_windshield": "前风挡",
        "part_rear_window": "后风窗",
        "part_wheel_fl": "左前轮",
        "part_wheel_fr": "右前轮",
        "part_wheel_rl": "左后轮",
        "part_wheel_rr": "右后轮",
        # New part names
        "part_front_bumper": "前保险杠",
        "part_rear_bumper": "后保险杠",
        "part_trunk_lid": "行李箱盖",
        "part_door_front_right": "右前门",
        "part_door_front_left": "左前门",
        "part_door_rear_right": "右后门",
        "part_door_rear_left": "左后门",
        "part_floor": "底板",
        "part_a_pillar_right": "右A柱",
        "part_a_pillar_left": "左A柱",
        "part_b_pillar_right": "右B柱",
        "part_b_pillar_left": "左B柱",
        "part_c_pillar_right": "右C柱",
        "part_c_pillar_left": "左C柱",
        "part_rocker_right": "右门槛板",
        "part_rocker_left": "左门槛板",
        "part_window_front_right": "右前窗",
        "part_window_front_left": "左前窗",
        "part_window_rear_right": "右后窗",
        "part_window_rear_left": "左后窗",
        "part_window_front_tri_right": "右前三角窗",
        "part_window_front_tri_left": "左前三角窗",
        "part_window_rear_tri_right": "右后三角窗",
        "part_window_rear_tri_left": "左后三角窗",
        # V2.1 parts
        "part_body": "车身壳体",
        "part_greenhouse": "座舱玻璃",
        "part_headlight_right": "右大灯",
        "part_headlight_left": "左大灯",
        "part_taillight_right": "右尾灯",
        "part_taillight_left": "左尾灯",
        # Parts list (BOM)
        "partslist_title": "零件明细表 (BOM)",
        "partslist_idx": "序号",
        "partslist_name": "零件名称",
        "partslist_en_name": "英文名称",
        "partslist_category": "类别",
        "partslist_color": "颜色",
        "partslist_opacity": "透明度",
        "partslist_verts": "顶点数",
        "partslist_faces": "面片数",
        "partslist_x_span": "X 范围 (m)",
        "partslist_y_span": "Y 范围 (m)",
        "partslist_z_span": "Z 范围 (m)",
        "partslist_total": "合计",
        "cat_body": "车身金属",
        "cat_glass": "玻璃",
        "cat_bumper": "保险杠",
        "cat_pillar": "立柱",
        "cat_wheel": "车轮",
        "cat_floor": "底板",
        "cat_rocker": "门槛板",
        "cat_door": "车门",
        "cat_trunk": "行李箱盖",
        "cat_hood": "引擎盖",
        "cat_top": "顶盖",
        "cat_windshield": "前风挡",
        "cat_rear_window": "后风窗",
        # Summary
        "param_summary_title": "参数摘要",
        "param_summary_unit": "mm",
        # Misc
        "no_data": "请先点击「生成曲面」",
        "stats_title": "统计信息",
        "export_success": "导出成功！",
    },
    "en": {
        "app_title": "Car Surface Design Studio",
        "lang_label": "Language",
        # Tabs
        "tab_3d": "3D View",
        "tab_opt": "Optimisation",
        "tab_quality": "Quality Analysis",
        # Sub-tabs
        "subtab_surface": "Panel Surfaces",
        "subtab_fullcar": "Full Car View",
        "subtab_parts": "Parts Gallery",
        "subtab_partslist": "Parts List",
        # Sidebar sections
        "section_basic": "📐 Basic Dimensions",
        "section_styling": "🎨 Styling Features",
        "section_ai": "🤖 AI Optimisation",
        "section_export": "💾 Data Export",
        "section_cartype": "🚘 Car Type",
        # Car type
        "cartype_label": "Car Type",
        # Parameters (mm)
        "param_length": "Overall Length (mm)",
        "param_width": "Overall Width (mm)",
        "param_height": "Overall Height (mm)",
        "param_wheelbase": "Wheelbase (mm)",
        "param_wheel_arch": "Wheel Arch Bulge (mm)",
        # Parameters (degrees / ratios)
        "param_hood_angle": "Hood Tilt Angle (°)",
        "param_roof_arc": "Roof Arc Factor",
        "param_windshield": "Windshield Angle (°)",
        "param_rear_window": "Rear Window Angle (°)",
        "param_waistline": "Waistline Height Ratio",
        # Buttons
        "generate_btn": "Generate Surfaces",
        "optimize_btn": "AI Optimise",
        "reset_btn": "Reset Params",
        "export_json_btn": "Export JSON",
        "export_csv_btn": "Export CSV",
        # Quality
        "quality_title": "Surface Quality Report",
        "quality_g0": "G0 Continuity",
        "quality_g1": "G1 Continuity",
        "quality_g2": "G2 Continuity",
        "quality_fairness": "Fairness",
        "quality_overall": "Overall Score",
        "quality_notes": "Notes",
        # Optimisation
        "opt_before": "Before Optimisation",
        "opt_after": "After Optimisation",
        "opt_params_title": "Parameter Comparison",
        "opt_quality_title": "Quality Comparison",
        # Surface names
        "surface_side": "Side Panel",
        "surface_top": "Top Panel",
        "surface_hood": "Hood Panel",
        # Full car
        "fullcar_title": "Full Car 3D View",
        "fullcar_no_assembler": "Full Car View (Geometric Build)",
        "fullcar_parts_count": "Parts",
        "fullcar_vertices": "Vertices",
        "fullcar_faces": "Faces",
        # Part names
        "part_side_right": "Right Side",
        "part_side_left": "Left Side",
        "part_top": "Roof",
        "part_hood": "Hood",
        "part_windshield": "Windshield",
        "part_rear_window": "Rear Window",
        "part_wheel_fl": "FL Wheel",
        "part_wheel_fr": "FR Wheel",
        "part_wheel_rl": "RL Wheel",
        "part_wheel_rr": "RR Wheel",
        # New part names
        "part_front_bumper": "Front Bumper",
        "part_rear_bumper": "Rear Bumper",
        "part_trunk_lid": "Trunk Lid",
        "part_door_front_right": "RF Door",
        "part_door_front_left": "LF Door",
        "part_door_rear_right": "RR Door",
        "part_door_rear_left": "LR Door",
        "part_floor": "Floor",
        "part_a_pillar_right": "R A-Pillar",
        "part_a_pillar_left": "L A-Pillar",
        "part_b_pillar_right": "R B-Pillar",
        "part_b_pillar_left": "L B-Pillar",
        "part_c_pillar_right": "R C-Pillar",
        "part_c_pillar_left": "L C-Pillar",
        "part_rocker_right": "R Rocker Panel",
        "part_rocker_left": "L Rocker Panel",
        "part_window_front_right": "RF Window",
        "part_window_front_left": "LF Window",
        "part_window_rear_right": "RR Window",
        "part_window_rear_left": "LR Window",
        "part_window_front_tri_right": "RF Quarter Window",
        "part_window_front_tri_left": "LF Quarter Window",
        "part_window_rear_tri_right": "RR Quarter Window",
        "part_window_rear_tri_left": "LR Quarter Window",
        # V2.1 parts
        "part_body": "Body Shell",
        "part_greenhouse": "Greenhouse Glass",
        "part_headlight_right": "R Headlight",
        "part_headlight_left": "L Headlight",
        "part_taillight_right": "R Taillight",
        "part_taillight_left": "L Taillight",
        # Parts list (BOM)
        "partslist_title": "Parts Bill of Materials",
        "partslist_idx": "#",
        "partslist_name": "Part Name",
        "partslist_en_name": "English Name",
        "partslist_category": "Category",
        "partslist_color": "Color",
        "partslist_opacity": "Opacity",
        "partslist_verts": "Vertices",
        "partslist_faces": "Faces",
        "partslist_x_span": "X Span (m)",
        "partslist_y_span": "Y Span (m)",
        "partslist_z_span": "Z Span (m)",
        "partslist_total": "Total",
        "cat_body": "Body Metal",
        "cat_glass": "Glass",
        "cat_bumper": "Bumper",
        "cat_pillar": "Pillar",
        "cat_wheel": "Wheel",
        "cat_floor": "Floor",
        "cat_rocker": "Rocker Panel",
        "cat_door": "Door",
        "cat_trunk": "Trunk Lid",
        "cat_hood": "Hood",
        "cat_top": "Roof",
        "cat_windshield": "Windshield",
        "cat_rear_window": "Rear Window",
        # Summary
        "param_summary_title": "Parameter Summary",
        "param_summary_unit": "mm",
        # Misc
        "no_data": "Click 'Generate Surfaces' first",
        "stats_title": "Statistics",
        "export_success": "Export successful!",
    },
}


def t(key: str, default: str = None) -> str:
    """Return translated text for the current language."""
    lang = st.session_state.get("lang", "zh")
    return I18N.get(lang, I18N["zh"]).get(key, default or key)


# ===================================================================
# Constants: mm slider ranges and defaults
# ===================================================================
# All length values in mm; will be /1000 before passing to CarParams
MM_LENGTH_DEFAULT = 4700
MM_LENGTH_MIN = 3500
MM_LENGTH_MAX = 6000
MM_LENGTH_STEP = 50

MM_WIDTH_DEFAULT = 1850
MM_WIDTH_MIN = 1500
MM_WIDTH_MAX = 2300
MM_WIDTH_STEP = 10

MM_HEIGHT_DEFAULT = 1450
MM_HEIGHT_MIN = 1100
MM_HEIGHT_MAX = 2100
MM_HEIGHT_STEP = 10

MM_WHEELBASE_DEFAULT = 2700
MM_WHEELBASE_MIN = 2000
MM_WHEELBASE_MAX = 3500
MM_WHEELBASE_STEP = 50

MM_WHEEL_ARCH_DEFAULT = 150
MM_WHEEL_ARCH_MIN = 0
MM_WHEEL_ARCH_MAX = 400
MM_WHEEL_ARCH_STEP = 10


# ===================================================================
# Shared geometry helpers — ensure edge alignment across parts
# ===================================================================

def _shared_key_points(params):
    """
    Compute all key reference coordinates shared between parts.
    This is the single source of truth for boundary alignment.
    Returns a dict of named 3D coordinates / planes.
    """
    p = params
    half_l = p.length / 2
    y_body = p.width / 2
    wl_z = p.height * p.waistline_ratio
    wr = p.wheel_radius
    front_axle_x = p.wheelbase / 2
    rear_axle_x = -p.wheelbase / 2
    front_x = half_l
    rear_x = -half_l
    roof_z = p.height * p.waistline_ratio + p.height * (1 - p.waistline_ratio) * p.roof_arc

    # Windshield base / top
    ws_base_x = front_axle_x - 0.1
    hood_z = wl_z + 0.04
    ws_header_x = front_axle_x - 0.2 - 0.3 * math.tan(math.radians(p.windshield_angle))

    # Rear window header / base
    rw_header_x = -p.wheelbase / 2 + 0.3
    rw_base_x = rw_header_x - 0.3 * math.tan(math.radians(p.rear_window_angle))
    trunk_z = wl_z + 0.02

    # Ground clearance (approximate)
    ground_z = 0.0
    sill_z = wr * 0.3  # bottom of rocker panel

    return {
        "half_l": half_l, "y_body": y_body, "wl_z": wl_z, "wr": wr,
        "front_axle_x": front_axle_x, "rear_axle_x": rear_axle_x,
        "front_x": front_x, "rear_x": rear_x, "roof_z": roof_z,
        "ws_base_x": ws_base_x, "hood_z": hood_z,
        "ws_header_x": ws_header_x,
        "rw_header_x": rw_header_x, "rw_base_x": rw_base_x,
        "trunk_z": trunk_z, "ground_z": ground_z, "sill_z": sill_z,
    }


# ===================================================================
# Enhanced control-point generators
# ===================================================================

def enhanced_side_panel_ctrl(params) -> np.ndarray:
    """
    Build control points for a realistic side panel (8x6 grid).
    Features:
      - Wheel arch cutouts (semicircular depressions at front & rear axle)
      - Window line (upper portion cut for glass area)
      - Waistline ridge (character line bulge)
      - Tumble-home (upper body leans inward)
      - Front/rear edge curvature (A-pillar & C-pillar shape)
    """
    p = params
    nu, nv = 8, 6
    ctrl = np.zeros((nu, nv, 3))

    half_l = p.length / 2
    y_body = p.width / 2          # body-side y position
    wl_z = p.height * p.waistline_ratio  # waistline height
    wr = p.wheel_radius
    front_axle_x = p.wheelbase / 2
    rear_axle_x = -p.wheelbase / 2

    # X positions along car length — 8 control points
    x_positions = np.array([
        -half_l,                          # 0: rear bumper
        -half_l + p.rear_overhang * 0.3,  # 1: behind rear arch
        rear_axle_x,                      # 2: rear axle center
        rear_axle_x + wr * 1.2,          # 3: between arches (rear)
        front_axle_x - wr * 1.2,         # 4: between arches (front)
        front_axle_x,                     # 5: front axle center
        half_l - p.front_overhang * 0.3,  # 6: ahead of front arch
        half_l,                           # 7: front bumper
    ])

    # Z positions — 6 vertical control points
    z_positions = np.array([
        0.0,                     # 0: ground level
        wr * 0.85,              # 1: top of wheel arch
        wr * 1.3,               # 2: below waistline (sill area top)
        wl_z,                   # 3: waistline
        p.height * 0.92,       # 4: window top / roof rail
        p.height,               # 5: roof edge
    ])

    for i in range(nu):
        x = x_positions[i]
        for j in range(nv):
            z = z_positions[j]

            # --- Y position (body side outward offset) ---
            y = y_body

            # Tumble-home: upper body leans inward progressively
            if j >= 3:
                tumble_frac = (j - 3) / (nv - 4)  # 0 at waistline, 1 at roof
                y -= 0.04 * tumble_frac  # inward lean

            # Window area: above waistline, the side panel becomes thinner
            if j == 4:
                y -= 0.025  # window top is inset

            # --- Wheel arch cutouts ---
            for axle_x in [front_axle_x, rear_axle_x]:
                dx = abs(x - axle_x)
                arch_half_w = wr * 1.35
                if dx < arch_half_w:
                    arch_profile = 1.0 - (dx / arch_half_w) ** 2
                    if j <= 2:
                        arch_push = p.wheel_arch_bulge * arch_profile * (1.0 - j / 3.0)
                        y -= arch_push
                    if j <= 1:
                        z = max(z, wr * 0.85 * (1.0 - arch_profile * 0.5))

            # --- Waistline ridge ---
            if j == 3:
                ridge = 0.015 * (1.0 - abs(2 * (i / (nu - 1)) - 0.5))
                y += ridge

            # --- Front edge: A-pillar curvature ---
            if i >= 6:
                front_frac = (i - 6) / max(nu - 7, 1)
                if j >= 3:
                    y -= 0.03 * front_frac * ((j - 3) / (nv - 4))
                    if j == 3:
                        z -= 0.02 * front_frac

            # --- Rear edge: C-pillar curvature ---
            if i <= 1:
                rear_frac = 1.0 - i / max(1, 1)
                if j >= 3:
                    y -= 0.02 * rear_frac * ((j - 3) / (nv - 4))
                    if j == 3:
                        z -= 0.015 * rear_frac

            # --- Sill area: slight outward bulge below waistline ---
            if j == 2:
                sill_bulge = 0.008 * (1.0 - abs(2 * (i / (nu - 1)) - 0.5))
                y += sill_bulge

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    return ctrl


def enhanced_top_panel_ctrl(params) -> np.ndarray:
    """
    Build control points for a realistic roof / top panel.
    Features:
      - Smooth arc from windshield header to rear window header
      - Slight crown (cross-car curvature)
      - Front windshield drop and rear window drop
    """
    p = params
    nu, nv = 7, 5
    ctrl = np.zeros((nu, nv, 3))

    half_l = p.length / 2
    base_z = p.height * p.waistline_ratio

    ws_header_x = p.wheelbase / 2 - 0.2
    rw_header_x = -p.wheelbase / 2 + 0.3

    for i in range(nu):
        for j in range(nv):
            u = i / (nu - 1)
            v = j / (nv - 1)
            x = -half_l + p.length * u
            y = -p.width / 2 + p.width * v

            if x > ws_header_x:
                drop_front = ((x - ws_header_x)
                              * np.tan(np.radians(p.windshield_angle)) * 0.6)
                z = base_z + p.height * (1 - p.waistline_ratio) * p.roof_arc - drop_front
            elif x < rw_header_x:
                drop_rear = ((rw_header_x - x)
                             * np.tan(np.radians(p.rear_window_angle)) * 0.4)
                z = base_z + p.height * (1 - p.waistline_ratio) * p.roof_arc - drop_rear
            else:
                centre_x = (ws_header_x + rw_header_x) / 2
                span = (ws_header_x - rw_header_x) / 2
                if span > 0:
                    arc_factor = 1 - ((x - centre_x) / span) ** 2
                else:
                    arc_factor = 0
                z = (base_z
                     + p.height * (1 - p.waistline_ratio)
                     * (p.roof_arc * 0.3 + 0.7 * arc_factor * p.roof_arc))

            # Cross-car crown
            v_centre = 0.5
            crown = 0.015 * (1 - (2 * (v - v_centre)) ** 2)
            z += crown

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    return ctrl


def enhanced_hood_ctrl(params) -> np.ndarray:
    """
    Build control points for a realistic hood panel (5x4 grid).
    Features:
      - Front end dips down (hood_angle controlled tilt)
      - Central power-bulge (slight z raise in the middle)
      - Sides dip slightly lower than center (cross-car curvature)
      - Rear edge meets windshield base at higher z
      - Slight taper towards the front
    """
    p = params
    nu, nv = 5, 4
    ctrl = np.zeros((nu, nv, 3))

    # Hood spans from front of car to windshield base
    front_x = p.wheelbase / 2 + p.front_overhang        # front bumper
    rear_x = p.wheelbase / 2 - 0.1                       # windshield base

    # Z heights: rear is higher (at windshield base), front is lower
    z_rear = p.height * p.waistline_ratio + 0.04         # ~0.55 * height
    z_front = z_rear - (rear_x - front_x) * np.tan(np.radians(p.hood_angle)) * 0.5

    for i in range(nu):
        u = i / (nu - 1)  # 0=rear (windshield base), 1=front (bumper)
        x = rear_x + (front_x - rear_x) * u

        # Base z: linear tilt from rear to front
        z_base = z_rear + (z_front - z_rear) * u

        # Power bulge
        bulge = 0.02 * np.sin(u * np.pi) * p.roof_arc

        for j in range(nv):
            v = j / (nv - 1)  # 0=left, 1=right

            # Cross-car curvature: center higher, sides lower
            v_center = abs(v - 0.5)
            cross_curve = -0.012 * (2 * v_center) ** 2

            # Slight taper: narrower towards front
            taper = 1.0 - 0.06 * u
            y = -p.width / 2 * taper + p.width * taper * v

            z = z_base + bulge + cross_curve

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    return ctrl


# ===================================================================
# Geometric construction helpers for full-car view
# ===================================================================

def build_windshield_surface(params) -> dict:
    """
    Build a Bezier surface for the front windshield (3x4 control points).
    The windshield spans from the hood rear edge up to the roof header,
    tilted by windshield_angle with curvature from roof_arc.
    Returns {"vertices": np.ndarray, "faces": np.ndarray}.
    """
    p = params
    nu, nv = 3, 4
    ctrl = np.zeros((nu, nv, 3))

    kp = _shared_key_points(p)
    ws_base_x = kp["ws_base_x"]
    hood_z = kp["hood_z"]
    ws_header_x = kp["ws_header_x"]
    roof_z = kp["roof_z"]
    width = p.width * 0.88

    for i in range(nu):
        u = i / (nu - 1)
        x = ws_base_x + (ws_header_x - ws_base_x) * u
        z_linear = hood_z + (roof_z - hood_z) * u

        for j in range(nv):
            v = j / (nv - 1)
            y = -width / 2 + width * v

            bow_long = 0.03 * p.roof_arc * np.sin(u * np.pi)
            x_adj = x - bow_long * 0.3

            v_center = abs(v - 0.5)
            bow_cross = 0.015 * p.roof_arc * (1 - (2 * v_center) ** 2) * np.sin(u * np.pi)

            z = z_linear + bow_cross

            ctrl[i, j, 0] = x_adj
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


def build_rear_window_surface(params) -> dict:
    """
    Build a Bezier surface for the rear window (3x4 control points).
    Returns {"vertices": np.ndarray, "faces": np.ndarray}.
    """
    p = params
    nu, nv = 3, 4
    ctrl = np.zeros((nu, nv, 3))

    kp = _shared_key_points(p)
    rw_header_x = kp["rw_header_x"]
    roof_z = kp["roof_z"]
    rw_base_x = kp["rw_base_x"]
    trunk_z = kp["trunk_z"]
    width = p.width * 0.85

    for i in range(nu):
        u = i / (nu - 1)
        x = rw_header_x + (rw_base_x - rw_header_x) * u
        z_linear = roof_z + (trunk_z - roof_z) * u

        for j in range(nv):
            v = j / (nv - 1)
            y = -width / 2 + width * v

            bow_long = 0.025 * p.roof_arc * np.sin(u * np.pi)
            x_adj = x + bow_long * 0.3

            v_center = abs(v - 0.5)
            bow_cross = 0.012 * p.roof_arc * (1 - (2 * v_center) ** 2) * np.sin(u * np.pi)

            z = z_linear + bow_cross

            ctrl[i, j, 0] = x_adj
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


def build_wheel_mesh(cx: float, cy: float, cz: float,
                     radius: float, width: float,
                     n_seg: int = 24) -> dict:
    """
    Generate a 3D wheel mesh with tire + hub + 5 spokes.
    The wheel axis is along Y. Returns {"vertices": np.ndarray, "faces": np.ndarray}.
    """
    half_w = width / 2
    tire_inner_r = radius * 0.70
    hub_outer_r = radius * 0.35
    spoke_inner_r = hub_outer_r
    spoke_outer_r = tire_inner_r
    n_spokes = 5
    spoke_angular_w = 2 * math.pi / n_spokes * 0.35

    verts = []
    faces = []

    def add_tire_rings(y_off):
        base = len(verts)
        for s in range(n_seg):
            angle = 2 * math.pi * s / n_seg
            verts.append([cx + radius * math.cos(angle), cy + y_off, cz + radius * math.sin(angle)])
        for s in range(n_seg):
            angle = 2 * math.pi * s / n_seg
            verts.append([cx + tire_inner_r * math.cos(angle), cy + y_off, cz + tire_inner_r * math.sin(angle)])
        return base

    base_left = add_tire_rings(-half_w)
    base_right = add_tire_rings(+half_w)

    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        p0 = base_left + s
        p1 = base_left + s_next
        p2 = base_right + s
        p3 = base_right + s_next
        faces.append([p0, p2, p3])
        faces.append([p0, p3, p1])

    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        p0 = base_left + n_seg + s
        p1 = base_left + n_seg + s_next
        p2 = base_right + n_seg + s
        p3 = base_right + n_seg + s_next
        faces.append([p0, p3, p2])
        faces.append([p0, p1, p3])

    for base_ring in [base_left, base_right]:
        for s in range(n_seg):
            s_next = (s + 1) % n_seg
            faces.append([base_ring + s, base_ring + n_seg + s, base_ring + n_seg + s_next])
            faces.append([base_ring + s, base_ring + n_seg + s_next, base_ring + s_next])

    # Hub
    hub_base = len(verts)
    verts.append([cx, cy, cz])
    hub_center_idx = hub_base
    for s in range(n_seg):
        angle = 2 * math.pi * s / n_seg
        verts.append([cx + hub_outer_r * math.cos(angle), cy, cz + hub_outer_r * math.sin(angle)])
    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        faces.append([hub_center_idx, hub_center_idx + 1 + s, hub_center_idx + 1 + s_next])

    hub_front_base = len(verts)
    verts.append([cx, cy + half_w * 0.3, cz])
    hub_front_center_idx = hub_front_base
    for s in range(n_seg):
        angle = 2 * math.pi * s / n_seg
        verts.append([cx + hub_outer_r * math.cos(angle), cy + half_w * 0.3, cz + hub_outer_r * math.sin(angle)])
    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        faces.append([hub_front_center_idx, hub_front_center_idx + 1 + s_next, hub_front_center_idx + 1 + s])

    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        p0 = hub_center_idx + 1 + s
        p1 = hub_center_idx + 1 + s_next
        p2 = hub_front_center_idx + 1 + s
        p3 = hub_front_center_idx + 1 + s_next
        faces.append([p0, p2, p3])
        faces.append([p0, p3, p1])

    # Spokes
    for spoke_idx in range(n_spokes):
        center_angle = 2 * math.pi * spoke_idx / n_spokes
        a_start = center_angle - spoke_angular_w / 2
        a_end = center_angle + spoke_angular_w / 2
        spoke_base = len(verts)

        verts.append([cx + spoke_inner_r * math.cos(a_start), cy - half_w * 0.3,
                       cz + spoke_inner_r * math.sin(a_start)])
        verts.append([cx + spoke_inner_r * math.cos(a_end), cy - half_w * 0.3,
                       cz + spoke_inner_r * math.sin(a_end)])
        verts.append([cx + spoke_outer_r * math.cos(a_start), cy - half_w * 0.3,
                       cz + spoke_outer_r * math.sin(a_start)])
        verts.append([cx + spoke_outer_r * math.cos(a_end), cy - half_w * 0.3,
                       cz + spoke_outer_r * math.sin(a_end)])
        verts.append([cx + spoke_inner_r * math.cos(a_start), cy + half_w * 0.3,
                       cz + spoke_inner_r * math.sin(a_start)])
        verts.append([cx + spoke_inner_r * math.cos(a_end), cy + half_w * 0.3,
                       cz + spoke_inner_r * math.sin(a_end)])
        verts.append([cx + spoke_outer_r * math.cos(a_start), cy + half_w * 0.3,
                       cz + spoke_outer_r * math.sin(a_start)])
        verts.append([cx + spoke_outer_r * math.cos(a_end), cy + half_w * 0.3,
                       cz + spoke_outer_r * math.sin(a_end)])

        b = spoke_base
        faces.append([b+0, b+2, b+3])
        faces.append([b+0, b+3, b+1])
        faces.append([b+4, b+7, b+6])
        faces.append([b+4, b+5, b+7])
        faces.append([b+2, b+6, b+7])
        faces.append([b+2, b+7, b+3])
        faces.append([b+0, b+1, b+5])
        faces.append([b+0, b+5, b+4])
        faces.append([b+0, b+4, b+6])
        faces.append([b+0, b+6, b+2])
        faces.append([b+1, b+3, b+7])
        faces.append([b+1, b+7, b+5])

    # Rim wall
    rim_base = len(verts)
    for s in range(n_seg):
        angle = 2 * math.pi * s / n_seg
        verts.append([cx + tire_inner_r * math.cos(angle), cy - half_w * 0.3,
                       cz + tire_inner_r * math.sin(angle)])
    for s in range(n_seg):
        angle = 2 * math.pi * s / n_seg
        verts.append([cx + tire_inner_r * math.cos(angle), cy + half_w * 0.3,
                       cz + tire_inner_r * math.sin(angle)])
    for s in range(n_seg):
        s_next = (s + 1) % n_seg
        p0 = rim_base + s
        p1 = rim_base + s_next
        p2 = rim_base + n_seg + s
        p3 = rim_base + n_seg + s_next
        faces.append([p0, p2, p3])
        faces.append([p0, p3, p1])

    return {
        "vertices": np.array(verts, dtype=np.float64),
        "faces": np.array(faces, dtype=np.int64),
    }


def mirror_surface_xz(surf: dict) -> dict:
    """Mirror a surface across the XZ plane (flip Y coordinates)."""
    verts = surf["vertices"].copy()
    verts[:, 1] = -verts[:, 1]
    faces = surf["faces"].copy()
    faces[:, [1, 2]] = faces[:, [2, 1]]
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Front bumper
# ===================================================================

def build_front_bumper(params) -> dict:
    """
    Build a Bezier surface for the front bumper (4x5 control grid).
    Covers from the hood front lower edge down to the car bottom,
    with a grille recess, fog lamp slots, and license plate area.
    The bottom protrudes forward (approach angle).
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 4, 5
    ctrl = np.zeros((nu, nv, 3))

    front_x = kp["front_x"]
    hood_z = kp["hood_z"]
    wl_z = kp["wl_z"]
    y_body = kp["y_body"]
    wr = kp["wr"]
    sill_z = kp["sill_z"]

    # Bumper front extends slightly forward of the body line
    bumper_protrusion = 0.08

    # X positions: from the rear face of bumper (at body front) to protrusion
    # u=0: inner face (body line), u=3: outer face (protruding)
    for i in range(nu):
        u = i / (nu - 1)
        # Bumper wraps from body-front inward to front face
        x = front_x - 0.05 + bumper_protrusion * u  # slight rearward start, then protrude

        # Grille recess: at the center (u ~ 1-2), x is pulled rearward
        for j in range(nv):
            v = j / (nv - 1)  # 0=bottom, 1=top

            # Z: from ground-level sill to hood-bottom
            z_bottom = sill_z
            z_top = hood_z - 0.02  # just below hood lower edge
            z = z_bottom + (z_top - z_bottom) * v

            # Y: wrap across the full body width
            # Slightly wider at bottom (bumper overhang), narrower at top
            width_factor = 1.0 + 0.03 * (1.0 - v)  # wider at bottom
            y = -y_body * width_factor + 2 * y_body * width_factor * v

            # Grille recess: pull x rearward in the centre, between v=0.3..0.7
            if 0.25 < v < 0.75 and 1 <= i <= 2:
                v_norm = (v - 0.25) / 0.5
                recess = 0.06 * math.sin(v_norm * math.pi)
                x_adj = x - recess
            else:
                x_adj = x

            # Fog lamp slots: slight indent at v~0.2, y near sides
            if 0.15 < v < 0.30 and (j == 0 or j == nv - 1):
                x_adj -= 0.02

            # License plate: flat area at v~0.35..0.55, center y
            if 0.30 < v < 0.55 and 0.2 < (v) < 0.8:
                pass  # plate area is flat, no extra shape

            # Lower lip: slight outward flare at very bottom
            if v < 0.1:
                x_adj += 0.03 * (0.1 - v) / 0.1  # slight forward flare

            ctrl[i, j, 0] = x_adj
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Rear bumper
# ===================================================================

def build_rear_bumper(params) -> dict:
    """
    Build a Bezier surface for the rear bumper (4x5 control grid).
    Covers from the trunk rear lower edge down to the car bottom,
    with a rear diffuser area and exhaust pipe holes.
    The bottom protrudes rearward (departure angle).
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 4, 5
    ctrl = np.zeros((nu, nv, 3))

    rear_x = kp["rear_x"]
    trunk_z = kp["trunk_z"]
    wl_z = kp["wl_z"]
    y_body = kp["y_body"]
    sill_z = kp["sill_z"]

    bumper_protrusion = 0.06

    for i in range(nu):
        u = i / (nu - 1)
        # i=0: inner face, i=3: outer face (protruding rearward)
        x = rear_x + 0.05 - bumper_protrusion * u

        for j in range(nv):
            v = j / (nv - 1)  # 0=bottom, 1=top

            z_bottom = sill_z
            z_top = trunk_z - 0.01
            z = z_bottom + (z_top - z_bottom) * v

            width_factor = 1.0 + 0.02 * (1.0 - v)
            y = -y_body * width_factor + 2 * y_body * width_factor * v

            x_adj = x

            # Diffuser area: lower portion has parallel fins
            if v < 0.3 and 1 <= i <= 2:
                x_adj += 0.04 * v / 0.3  # diffuser tucks inward

            # Exhaust pipe indent: at bottom sides
            if v < 0.15 and (j == 0 or j == nv - 1):
                x_adj -= 0.03

            # Lower lip: slight rearward flare
            if v < 0.1:
                x_adj -= 0.02 * (0.1 - v) / 0.1

            ctrl[i, j, 0] = x_adj
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Trunk lid
# ===================================================================

def build_trunk_lid(params) -> dict:
    """
    Build a Bezier surface for the trunk lid (4x4 control grid).
    Spans from the rear window base to the rear edge of the car,
    with a slight arc (deck lid curvature).
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 4, 4
    ctrl = np.zeros((nu, nv, 3))

    rw_base_x = kp["rw_base_x"]
    rear_x = kp["rear_x"]
    trunk_z = kp["trunk_z"]
    y_body = kp["y_body"]

    for i in range(nu):
        u = i / (nu - 1)  # 0=rear window base, 1=rear edge
        x = rw_base_x + (rear_x - rw_base_x) * u

        # Slight arc: highest at center, dips at rear edge
        arc = 0.015 * math.sin(u * math.pi) * p.roof_arc

        for j in range(nv):
            v = j / (nv - 1)  # 0=left, 1=right
            # Taper: slightly narrower towards rear
            taper = 1.0 - 0.04 * u
            y = -y_body * taper + 2 * y_body * taper * v

            # Cross-car crown: center slightly higher
            v_center = abs(v - 0.5)
            crown = 0.008 * (1 - (2 * v_center) ** 2)

            z = trunk_z + arc + crown

            # Rear edge: slight downturn (lip spoiler effect)
            if u > 0.85:
                lip_frac = (u - 0.85) / 0.15
                z += 0.01 * lip_frac

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Door panel (front or rear, left or right)
# ===================================================================

def build_door_surface(params, door_type: str = "front", side: str = "right") -> dict:
    """
    Build a door panel Bezier surface (4x5 control grid).
    door_type: "front" or "rear"
    side: "right" (positive Y) or "left" (negative Y)

    The door fills the lower body area on the side panel between the
    window line (waistline) and the sill / rocker panel.
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 4, 5
    ctrl = np.zeros((nu, nv, 3))

    y_sign = 1.0 if side == "right" else -1.0
    y_body = kp["y_body"] * y_sign
    wl_z = kp["wl_z"]
    wr = kp["wr"]
    front_axle_x = kp["front_axle_x"]
    rear_axle_x = kp["rear_axle_x"]

    if door_type == "front":
        # Front door: from A-pillar to B-pillar
        x_start = front_axle_x - 0.1  # near A-pillar
        x_end = (front_axle_x + rear_axle_x) / 2 + 0.05  # B-pillar
    else:
        # Rear door: from B-pillar to C-pillar
        x_start = (front_axle_x + rear_axle_x) / 2 + 0.05
        x_end = rear_axle_x + 0.2  # near C-pillar

    for i in range(nu):
        u = i / (nu - 1)  # 0=front, 1=rear
        x = x_start + (x_end - x_start) * u

        for j in range(nv):
            v = j / (nv - 1)  # 0=bottom (sill), 1=top (waistline)

            # Z: from sill area up to waistline
            z_bottom = wr * 0.4
            z_top = wl_z
            z = z_bottom + (z_top - z_bottom) * v

            # Y: at the body side, with slight tumble-home at top
            y = y_body
            tumble = 0.02 * v  # slight inward lean at top
            y -= tumble * y_sign

            # Slight contour bulge at waistline (character line)
            if v > 0.7:
                bulge = 0.008 * math.sin((v - 0.7) / 0.3 * math.pi)
                y += bulge * y_sign

            # Door handle dip: slight concavity near v~0.65
            if 0.55 < v < 0.75:
                dip = 0.004 * math.sin((v - 0.55) / 0.2 * math.pi)
                y -= dip * y_sign

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Floor panel
# ===================================================================

def build_floor(params) -> dict:
    """
    Build the floor panel as a flat Bezier surface (3x3 control grid).
    Connects left and right side panel bottoms.
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 3, 3
    ctrl = np.zeros((nu, nv, 3))

    front_x = kp["front_x"]
    rear_x = kp["rear_x"]
    y_body = kp["y_body"]
    floor_z = 0.12  # floor height (slightly above ground)

    for i in range(nu):
        u = i / (nu - 1)
        x = rear_x + (front_x - rear_x) * u

        for j in range(nv):
            v = j / (nv - 1)
            y = -y_body + 2 * y_body * v

            # Floor is flat with slight cross-car curvature (drainage)
            crown = -0.005 * (1 - (2 * (v - 0.5)) ** 2)  # center slightly lower
            z = floor_z + crown

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Pillar (A, B, C) as thick strip surfaces
# ===================================================================

def build_pillar_surface(params, pillar_type: str = "A", side: str = "right") -> dict:
    """
    Build a pillar surface as a narrow thick strip (2x3 control grid).
    pillar_type: "A", "B", or "C"
    side: "right" or "left"
    Returns {"vertices": np.ndarray, "faces": np.ndarray}.
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 2, 3
    ctrl = np.zeros((nu, nv, 3))

    y_sign = 1.0 if side == "right" else -1.0
    y_body = kp["y_body"]
    wl_z = kp["wl_z"]
    roof_z = kp["roof_z"]
    front_axle_x = kp["front_axle_x"]
    rear_axle_x = kp["rear_axle_x"]
    wr = kp["wr"]

    pillar_width = 0.06  # half-width of pillar in Y
    pillar_depth = 0.04  # depth in X

    if pillar_type == "A":
        # A-pillar: from windshield base to roof header
        x_bottom = kp["ws_base_x"]
        x_top = kp["ws_header_x"]
        z_bottom = wl_z + 0.04
        z_top = roof_z
    elif pillar_type == "B":
        # B-pillar: vertical strip between front/rear doors
        x_pos = (front_axle_x + rear_axle_x) / 2 + 0.05
        x_bottom = x_pos
        x_top = x_pos
        z_bottom = wl_z
        z_top = roof_z
    else:  # C
        # C-pillar: from rear window base to roof header
        x_bottom = kp["rw_base_x"]
        x_top = kp["rw_header_x"]
        z_bottom = kp["trunk_z"]
        z_top = roof_z

    for i in range(nu):
        u = i / (nu - 1)  # 0=inner, 1=outer edge
        for j in range(nv):
            v = j / (nv - 1)  # 0=bottom, 1=top

            x = x_bottom + (x_top - x_bottom) * v + pillar_depth * (u - 0.5)
            z = z_bottom + (z_top - z_bottom) * v

            # Y: at body side, with tumble-home at top
            y_base = y_body * y_sign
            tumble = 0.04 * v * y_sign  # lean inward at top
            y = y_base - tumble + pillar_width * (u - 0.5) * y_sign

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Rocker panel (sill cover)
# ===================================================================

def build_rocker_panel(params, side: str = "right") -> dict:
    """
    Build a rocker panel / sill cover (6x2 control grid).
    Runs along the bottom of the side panel between wheel arches,
    bridging the side panel bottom edge to the floor.
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 6, 2
    ctrl = np.zeros((nu, nv, 3))

    y_sign = 1.0 if side == "right" else -1.0
    y_body = kp["y_body"]
    wr = kp["wr"]
    front_axle_x = kp["front_axle_x"]
    rear_axle_x = kp["rear_axle_x"]
    sill_z = kp["sill_z"]

    for i in range(nu):
        u = i / (nu - 1)
        x = rear_axle_x + (front_axle_x - rear_axle_x) * u

        for j in range(nv):
            v = j / (nv - 1)  # 0=outer (body side), 1=inner (floor edge)

            # Z: at sill level
            z = sill_z + 0.02 * v  # slight upward slope inward

            # Y: from body side to slightly inward
            y_outer = y_body * y_sign + 0.01 * y_sign  # slight outer flare
            y_inner = (y_body - 0.06) * y_sign
            y = y_outer + (y_inner - y_outer) * v

            # Slight bulge at center
            bulge = 0.005 * math.sin(u * math.pi) * y_sign
            y += bulge * (1 - v)

            ctrl[i, j, 0] = x
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Window glass surfaces (front/rear door + quarter windows)
# ===================================================================

def build_window_surface(params, window_type: str = "front_door",
                         side: str = "right") -> dict:
    """
    Build a window glass surface as a Bezier patch (3x3 control grid).
    window_type: "front_door", "rear_door", "front_quarter", "rear_quarter"
    side: "right" or "left"
    """
    p = params
    kp = _shared_key_points(p)
    nu, nv = 3, 3
    ctrl = np.zeros((nu, nv, 3))

    y_sign = 1.0 if side == "right" else -1.0
    y_body = kp["y_body"]
    wl_z = kp["wl_z"]
    roof_z = kp["roof_z"]
    front_axle_x = kp["front_axle_x"]
    rear_axle_x = kp["rear_axle_x"]

    # Window sits above the waistline and below the roof rail
    z_bottom = wl_z + 0.02
    z_top = p.height * 0.92 - 0.01

    # Glass is slightly inset from body side (tumble-home)
    y_glass = (y_body - 0.04) * y_sign

    if window_type == "front_door":
        x_front = front_axle_x - 0.05
        x_rear = (front_axle_x + rear_axle_x) / 2 + 0.02
    elif window_type == "rear_door":
        x_front = (front_axle_x + rear_axle_x) / 2 + 0.02
        x_rear = rear_axle_x + 0.15
    elif window_type == "front_quarter":
        # Small triangular window ahead of front door window
        x_front = front_axle_x - 0.15
        x_rear = front_axle_x - 0.05
        z_top = wl_z + 0.10
    else:  # rear_quarter
        x_front = rear_axle_x + 0.10
        x_rear = rear_axle_x + 0.20
        z_top = wl_z + 0.12

    for i in range(nu):
        u = i / (nu - 1)
        x = x_rear + (x_front - x_rear) * u

        for j in range(nv):
            v = j / (nv - 1)  # 0=bottom, 1=top
            z = z_bottom + (z_top - z_bottom) * v

            # Glass curves inward slightly at top (tumble-home)
            tumble = 0.02 * v * y_sign
            y = y_glass - tumble

            # Slight bow (curvature of glass)
            bow = 0.008 * math.sin(u * math.pi) * math.sin(v * math.pi)
            x_adj = x - bow * 0.3

            ctrl[i, j, 0] = x_adj
            ctrl[i, j, 1] = y
            ctrl[i, j, 2] = z

    verts = bezier_surface_vec(ctrl, p.surface_u, p.surface_v)
    faces = _make_faces(p.surface_u, p.surface_v)
    return {"vertices": verts, "faces": faces}


# ===================================================================
# NEW: Side panel with window cutouts (two parts: body + glass)
# ===================================================================

def build_side_with_windows(params, side: str = "right") -> Dict[str, dict]:
    """
    Build the side panel split into body metal and window glass areas.
    Returns a dict with keys like "side_body_right", "window_front_right", etc.
    """
    car_type = st.session_state.get("car_type", "sedan")
    preset = CAR_TYPE_PRESETS.get(car_type, CAR_TYPE_PRESETS["sedan"])
    n_doors = preset.get("doors", 4)

    suffix = "_right" if side == "right" else "_left"

    # Full side panel
    side_ctrl = enhanced_side_panel_ctrl(params)
    side_verts = bezier_surface_vec(side_ctrl, params.surface_u, params.surface_v)
    side_faces = _make_faces(params.surface_u, params.surface_v)
    result = {
        f"side_body{suffix}": {"vertices": side_verts, "faces": side_faces}
    }

    # Window glass surfaces
    result[f"window_front{suffix}"] = build_window_surface(
        params, "front_door", side)

    if n_doors >= 4:
        result[f"window_rear{suffix}"] = build_window_surface(
            params, "rear_door", side)
        result[f"window_rear_tri{suffix}"] = build_window_surface(
            params, "rear_quarter", side)

    result[f"window_front_tri{suffix}"] = build_window_surface(
        params, "front_quarter", side)

    return result


# ===================================================================
# Plotly helpers
# ===================================================================

def surface_dict_to_plotly(surf: dict, name: str = "surface",
                           color: str = "royalblue",
                           opacity: float = 0.8) -> go.Mesh3d:
    """Convert a surface dict {vertices, faces} to a Plotly mesh3d trace.

    All arrays are converted to plain Python lists via .tolist() to avoid
    Plotly 6.x binary (bdata) serialisation which Streamlit's bundled
    Plotly.js cannot decode, resulting in a blank/white chart.
    """
    verts = surf["vertices"]
    faces = surf["faces"]
    return go.Mesh3d(
        x=verts[:, 0].tolist(),
        y=verts[:, 1].tolist(),
        z=verts[:, 2].tolist(),
        i=faces[:, 0].tolist(),
        j=faces[:, 1].tolist(),
        k=faces[:, 2].tolist(),
        name=name,
        color=color,
        opacity=opacity,
        flatshading=True,
    )


def _merged_surface_to_plotly(verts_list: List[np.ndarray],
                              faces_list: List[np.ndarray],
                              name: str = "merged",
                              color: str = "#C0C0C0",
                              opacity: float = 0.9) -> go.Mesh3d:
    """Merge multiple (vertices, faces) pairs into a single Mesh3d trace.

    Faces indices are offset so that each sub-mesh references its own
    vertices within the combined vertex array.

    All arrays are converted to plain Python lists via .tolist() to avoid
    Plotly 6.x binary (bdata) serialisation which Streamlit's bundled
    Plotly.js cannot decode, resulting in a blank/white chart.
    """
    all_x, all_y, all_z = [], [], []
    all_i, all_j, all_k = [], [], []
    vertex_offset = 0

    for verts, faces in zip(verts_list, faces_list):
        all_x.append(verts[:, 0])
        all_y.append(verts[:, 1])
        all_z.append(verts[:, 2])
        all_i.append(faces[:, 0] + vertex_offset)
        all_j.append(faces[:, 1] + vertex_offset)
        all_k.append(faces[:, 2] + vertex_offset)
        vertex_offset += len(verts)

    return go.Mesh3d(
        x=np.concatenate(all_x).tolist(),
        y=np.concatenate(all_y).tolist(),
        z=np.concatenate(all_z).tolist(),
        i=np.concatenate(all_i).astype(int).tolist(),
        j=np.concatenate(all_j).astype(int).tolist(),
        k=np.concatenate(all_k).astype(int).tolist(),
        name=name,
        color=color,
        opacity=opacity,
        flatshading=True,
    )


def _merge_meshes(parts_dict: Dict[str, dict],
                  include_keys: Optional[List[str]] = None,
                  exclude_keys: Optional[List[str]] = None) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """Merge selected parts' vertices + faces into lists ready for
    ``_merged_surface_to_plotly``.

    Parameters
    ----------
    parts_dict : mapping of part_name -> {"vertices": ..., "faces": ...}
    include_keys : if given, only these keys are merged
    exclude_keys : if given, these keys are skipped

    Returns
    -------
    (verts_list, faces_list) — lists of numpy arrays, one per included part,
    preserving the order of iteration.
    """
    verts_list: List[np.ndarray] = []
    faces_list: List[np.ndarray] = []

    for key, surf in parts_dict.items():
        if include_keys is not None and key not in include_keys:
            continue
        if exclude_keys is not None and key in exclude_keys:
            continue
        verts_list.append(surf["vertices"])
        faces_list.append(surf["faces"])

    return verts_list, faces_list


def _3d_layout(title: str = "", unit_label: str = "m") -> go.Layout:
    """Return a standard 3D layout with equal aspect ratio and rotation."""
    return go.Layout(
        title=title,
        scene=dict(
            aspectmode="data",
            xaxis=dict(title=f"X ({unit_label})", showgrid=True, gridwidth=1, gridcolor='#E0E0E0'),
            yaxis=dict(title=f"Y ({unit_label})", showgrid=True, gridwidth=1, gridcolor='#E0E0E0'),
            zaxis=dict(title=f"Z ({unit_label})", showgrid=True, gridwidth=1, gridcolor='#E0E0E0'),
            camera=dict(eye=dict(x=2.0, y=-2.2, z=1.3)),  # 3/4 view from front-right
            bgcolor='rgba(245,245,245,1)',  # light gray background
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=650,
        plot_bgcolor='rgba(245,245,245,1)',
        paper_bgcolor='rgba(255,255,255,1)',
    )


def _mini_3d_layout(title: str = "") -> go.Layout:
    """Compact 3D layout for small part previews."""
    return go.Layout(
        title=dict(text=title, font=dict(size=11)),
        scene=dict(
            aspectmode="data",
            xaxis=dict(showticklabels=False, visible=False),
            yaxis=dict(showticklabels=False, visible=False),
            zaxis=dict(showticklabels=False, visible=False),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=250,
    )


# ===================================================================
# Surface generation with enhanced control points
# ===================================================================

def generate_enhanced_surfaces(params) -> Dict[str, dict]:
    """
    Generate three car surfaces using enhanced control-point builders.
    Falls back to the original builders on error.
    """
    builders = {
        "side": enhanced_side_panel_ctrl,
        "top": enhanced_top_panel_ctrl,
        "hood": enhanced_hood_ctrl,
    }
    fallback = {
        "side": build_side_panel_ctrl,
        "top": build_top_panel_ctrl,
        "hood": build_hood_ctrl,
    }
    result = {}
    for name, builder in builders.items():
        try:
            ctrl = builder(params)
            verts = bezier_surface_vec(ctrl, params.surface_u, params.surface_v)
            faces = _make_faces(params.surface_u, params.surface_v)
        except Exception:
            ctrl = fallback[name](params)
            verts = bezier_surface_vec(ctrl, params.surface_u, params.surface_v)
            faces = _make_faces(params.surface_u, params.surface_v)
        result[name] = {"vertices": verts, "faces": faces}
    return result


# ===================================================================
# Full-car geometric builder — V2.1 sweep-based algorithm
# ===================================================================

def _legacy_params_to_v21(legacy_params, car_type: str) -> "CarParams22":
    """Convert legacy CoreCarParams + car_type to V2.1 CarParams22."""
    lp = legacy_params
    if V21_AVAILABLE:
        p22 = v21_apply_preset(car_type)
        # Override with user-adjusted legacy values
        p22.L = lp.length
        p22.W = lp.width
        p22.H = lp.height
        p22.WB = lp.wheelbase
        p22.hood_len = lp.front_overhang + 0.15
        p22.trunk_len = lp.rear_overhang + 0.10
        p22.cabin_len = max(0.5, p22.L - p22.hood_len - p22.trunk_len)
        p22.GC = lp.wheel_radius * 0.47
        p22.hood_angle = lp.hood_angle
        p22.roof_arc = lp.roof_arc
        p22.windshield_rake = lp.windshield_angle
        p22.rear_glass_angle = lp.rear_window_angle
        p22.fender_prominence = lp.wheel_arch_bulge
        p22.waist_line = lp.waistline_ratio
        p22.WR = lp.wheel_radius
        p22.shoulder_line = 0.012
        p22.overall_arc = lp.roof_arc
        p22.car_type = car_type
        return p22
    return None


def build_full_car_geometric(params) -> Dict[str, dict]:
    """
    Build all car parts geometrically from params.
    Uses V2.1 sweep-based algorithm when available.
    Falls back to legacy Bezier-patch builders otherwise.

    Returns a dict mapping part names to surface dicts.
    """
    car_type = st.session_state.get("car_type", "sedan")

    # ---- V2.1 PATH ----
    if V21_AVAILABLE:
        try:
            p22 = _legacy_params_to_v21(params, car_type)
            v21_parts = build_full_car_v21(p22)
            return v21_parts
        except Exception as e:
            print(f"[V2.1] Fallback to legacy builder: {e}")
            import traceback; traceback.print_exc()

    # ---- LEGACY FALLBACK PATH ----
    preset = CAR_TYPE_PRESETS.get(car_type, CAR_TYPE_PRESETS["sedan"])
    n_doors = preset.get("doors", 4)

    base_surfaces = generate_enhanced_surfaces(params)
    parts = {}

    right_side_parts = build_side_with_windows(params, "right")
    left_side_parts = build_side_with_windows(params, "left")
    for key, surf in right_side_parts.items():
        if key.startswith("side_body"):
            parts["side_right"] = surf
        else:
            parts[key] = surf
    for key, surf in left_side_parts.items():
        if key.startswith("side_body"):
            parts["side_left"] = mirror_surface_xz(surf)
        else:
            parts[key] = surf

    parts["top"] = base_surfaces["top"]
    parts["hood"] = base_surfaces["hood"]
    parts["windshield"] = build_windshield_surface(params)
    parts["rear_window"] = build_rear_window_surface(params)
    parts["front_bumper"] = build_front_bumper(params)
    parts["rear_bumper"] = build_rear_bumper(params)
    parts["trunk_lid"] = build_trunk_lid(params)
    parts["door_front_right"] = build_door_surface(params, "front", "right")
    parts["door_front_left"] = build_door_surface(params, "front", "left")
    if n_doors >= 4:
        parts["door_rear_right"] = build_door_surface(params, "rear", "right")
        parts["door_rear_left"] = build_door_surface(params, "rear", "left")
    parts["floor"] = build_floor(params)
    for pillar in ["A", "B", "C"]:
        for side in ["right", "left"]:
            key = f"{pillar.lower()}_pillar_{side}"
            parts[key] = build_pillar_surface(params, pillar, side)
    parts["rocker_right"] = build_rocker_panel(params, "right")
    parts["rocker_left"] = build_rocker_panel(params, "left")

    wr = params.wheel_radius
    wheel_width = 0.20
    front_x = params.wheelbase / 2
    rear_x = -params.wheelbase / 2
    side_y_right = params.width / 2 + 0.05
    side_y_left = -(params.width / 2 + 0.05)
    wheel_z = wr
    parts["wheel_fr"] = build_wheel_mesh(front_x, side_y_right, wheel_z, wr, wheel_width)
    parts["wheel_fl"] = build_wheel_mesh(front_x, side_y_left, wheel_z, wr, wheel_width)
    parts["wheel_rr"] = build_wheel_mesh(rear_x, side_y_right, wheel_z, wr, wheel_width)
    parts["wheel_rl"] = build_wheel_mesh(rear_x, side_y_left, wheel_z, wr, wheel_width)

    return parts


# ===================================================================
# Color scheme for full-car view
# ===================================================================

# Body metal: light gray / silver
# Glass: deep blue semi-transparent
# Bumpers: dark gray
# Wheels: black
# Floor: dark gray / black
# Pillars: dark gray (body color variant)
# Rocker: dark gray
# Windows: deep blue semi-transparent

PART_STYLES = {
    # Body metal — Pearl White (opaque, like a real car)
    "side_right":          ("#F0F0F0", 1.00),  # pearl white
    "side_left":           ("#F0F0F0", 1.00),
    "top":                 ("#E8E8E8", 1.00),  # slightly darker roof
    "hood":                ("#F5F5F5", 1.00),  # lighter hood
    "trunk_lid":           ("#F0F0F0", 1.00),
    "door_front_right":    ("#F0F0F0", 1.00),
    "door_front_left":     ("#F0F0F0", 1.00),
    "door_rear_right":     ("#F0F0F0", 1.00),
    "door_rear_left":      ("#F0F0F0", 1.00),
    # Glass — deep blue, semi-transparent
    "windshield":          ("#1E3A5F", 0.50),
    "rear_window":         ("#1E3A5F", 0.50),
    "window_front_right":  ("#2A5F8F", 0.45),
    "window_front_left":   ("#2A5F8F", 0.45),
    "window_rear_right":   ("#2A5F8F", 0.45),
    "window_rear_left":    ("#2A5F8F", 0.45),
    "window_front_tri_right":  ("#2A5F8F", 0.45),
    "window_front_tri_left":   ("#2A5F8F", 0.45),
    "window_rear_tri_right":   ("#2A5F8F", 0.45),
    "window_rear_tri_left":    ("#2A5F8F", 0.45),
    # Bumpers — dark charcoal
    "front_bumper":        ("#3A3A3A", 1.00),
    "rear_bumper":         ("#3A3A3A", 1.00),
    # Wheels — black
    "wheel_fr":            ("#1A1A1A", 1.00),
    "wheel_fl":            ("#1A1A1A", 1.00),
    "wheel_rr":            ("#1A1A1A", 1.00),
    "wheel_rl":            ("#1A1A1A", 1.00),
    # Floor — hidden (same as ground, low opacity)
    "floor":               ("#CCCCCC", 0.30),
    # Pillars — body color
    "a_pillar_right":      ("#E0E0E0", 1.00),
    "a_pillar_left":       ("#E0E0E0", 1.00),
    "b_pillar_right":      ("#E0E0E0", 1.00),
    "b_pillar_left":       ("#E0E0E0", 1.00),
    "c_pillar_right":      ("#E0E0E0", 1.00),
    "c_pillar_left":       ("#E0E0E0", 1.00),
    # Rocker panels — dark
    "rocker_right":        ("#2A2A2A", 1.00),
    "rocker_left":         ("#2A2A2A", 1.00),
    # V2.1 parts (sweep-based body)
    "body":                ("#F0F0F0", 1.00),       # pearl white body shell
    "greenhouse":          ("#1E3A5F", 0.45),       # glass canopy
    "headlight_right":     ("#FFFFCC", 0.90),       # warm white headlight
    "headlight_left":      ("#FFFFCC", 0.90),
    "taillight_right":     ("#CC2222", 0.90),       # red taillight
    "taillight_left":      ("#CC2222", 0.90),
}

# Default for any part not in the style dict
PART_STYLES_DEFAULT = ("#888888", 0.80)

# Category classification for each part (maps to I18N cat_* keys)
PART_CATEGORY: Dict[str, str] = {
    # Body metal
    "side_right":          "cat_body", "side_left":           "cat_body",
    "top":                 "cat_top",
    "hood":                "cat_hood",
    "trunk_lid":           "cat_trunk",
    "door_front_right":    "cat_door", "door_front_left":     "cat_door",
    "door_rear_right":     "cat_door", "door_rear_left":      "cat_door",
    # Glass
    "windshield":                "cat_windshield",
    "rear_window":               "cat_rear_window",
    "window_front_right":        "cat_glass", "window_front_left":         "cat_glass",
    "window_rear_right":         "cat_glass", "window_rear_left":          "cat_glass",
    "window_front_tri_right":    "cat_glass", "window_front_tri_left":     "cat_glass",
    "window_rear_tri_right":     "cat_glass", "window_rear_tri_left":      "cat_glass",
    # Bumpers
    "front_bumper":        "cat_bumper", "rear_bumper":        "cat_bumper",
    # Pillars
    "a_pillar_right":      "cat_pillar", "a_pillar_left":      "cat_pillar",
    "b_pillar_right":      "cat_pillar", "b_pillar_left":      "cat_pillar",
    "c_pillar_right":      "cat_pillar", "c_pillar_left":      "cat_pillar",
    # Wheels
    "wheel_fr":            "cat_wheel",  "wheel_fl":           "cat_wheel",
    "wheel_rr":            "cat_wheel",  "wheel_rl":           "cat_wheel",
    # Floor
    "floor":               "cat_floor",
    # Rocker panels
    "rocker_right":        "cat_rocker", "rocker_left":        "cat_rocker",
    # V2.1 parts
    "body":                "cat_body",
    "greenhouse":          "cat_glass",
    "headlight_right":     "cat_bumper", "headlight_left":     "cat_bumper",
    "taillight_right":     "cat_bumper", "taillight_left":     "cat_bumper",
}


# ===================================================================
# Parameter widget helpers
# ===================================================================

def _mm_slider(label_key: str, min_val: int, max_val: int,
               default: int, step: int = 10) -> int:
    """Render a Streamlit slider for mm values (integer)."""
    return st.sidebar.slider(
        t(label_key), min_val, max_val, default, step, format="%d"
    )


def read_params_from_sidebar() -> CoreCarParams:
    """Read all car parameters from sidebar sliders and return CoreCarParams.
    Length sliders display in mm; values are converted to m internally."""

    # --- Car type selector ---
    st.sidebar.markdown(f"**{t('section_cartype')}**")
    car_type_options = list(CAR_TYPE_PRESETS.keys())
    lang = st.session_state.get("lang", "zh")
    car_type_labels = []
    for ct in car_type_options:
        preset = CAR_TYPE_PRESETS[ct]
        label = preset["label_zh"] if lang == "zh" else preset["label_en"]
        car_type_labels.append(label)

    current_car_type = st.session_state.get("car_type", "sedan")
    default_idx = car_type_options.index(current_car_type) if current_car_type in car_type_options else 0

    selected_label = st.sidebar.selectbox(
        t("cartype_label"),
        options=car_type_labels,
        index=default_idx,
        key="car_type_selector",
    )
    selected_car_type = car_type_options[car_type_labels.index(selected_label)]
    st.session_state["car_type"] = selected_car_type

    # Get preset values for the selected car type
    preset = CAR_TYPE_PRESETS[selected_car_type]

    # --- Basic dimensions section ---
    st.sidebar.markdown(f"**{t('section_basic')}**")

    length_mm = _mm_slider("param_length",
                           MM_LENGTH_MIN, MM_LENGTH_MAX,
                           preset["length"], MM_LENGTH_STEP)
    width_mm = _mm_slider("param_width",
                          MM_WIDTH_MIN, MM_WIDTH_MAX,
                          preset["width"], MM_WIDTH_STEP)
    height_mm = _mm_slider("param_height",
                           MM_HEIGHT_MIN, MM_HEIGHT_MAX,
                           preset["height"], MM_HEIGHT_STEP)
    wheelbase_mm = _mm_slider("param_wheelbase",
                              MM_WHEELBASE_MIN, MM_WHEELBASE_MAX,
                              preset["wheelbase"], MM_WHEELBASE_STEP)

    # --- Styling features section ---
    st.sidebar.markdown(f"**{t('section_styling')}**")

    wheel_arch_mm = _mm_slider("param_wheel_arch",
                               MM_WHEEL_ARCH_MIN, MM_WHEEL_ARCH_MAX,
                               preset["wheel_arch"], MM_WHEEL_ARCH_STEP)

    hood_angle = st.sidebar.slider(t("param_hood_angle"), 0.0, 35.0,
                                   preset["hood_angle"], 0.5, format="%.1f")
    roof_arc = st.sidebar.slider(t("param_roof_arc"), 0.0, 1.5,
                                 preset["roof_arc"], 0.01, format="%.2f")
    windshield = st.sidebar.slider(t("param_windshield"), 15.0, 45.0,
                                   preset["windshield_angle"], 0.5, format="%.1f")
    rear_window = st.sidebar.slider(t("param_rear_window"), 10.0, 40.0,
                                    preset["rear_window_angle"], 0.5, format="%.1f")
    waistline = st.sidebar.slider(t("param_waistline"), 0.5, 0.95,
                                  preset["waistline"], 0.01, format="%.2f")

    # Convert mm to m for internal computation
    length_m = length_mm / 1000.0
    width_m = width_mm / 1000.0
    height_m = height_mm / 1000.0
    wheelbase_m = wheelbase_mm / 1000.0
    wheel_arch_m = wheel_arch_mm / 1000.0

    # Derive overhangs from length & wheelbase
    total_oh = length_m - wheelbase_m
    front_oh = round(total_oh * 0.45, 3)
    rear_oh = round(total_oh - front_oh, 3)

    return CoreCarParams(
        length=length_m,
        width=width_m,
        height=height_m,
        wheelbase=wheelbase_m,
        front_overhang=front_oh,
        rear_overhang=rear_oh,
        hood_angle=hood_angle,
        roof_arc=roof_arc,
        windshield_angle=windshield,
        rear_window_angle=rear_window,
        wheel_arch_bulge=wheel_arch_m,
        waistline_ratio=waistline,
    )


def render_param_summary(params: CoreCarParams):
    """Render a compact parameter summary showing values in mm."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{t('param_summary_title')}** ({t('param_summary_unit')})")

    summary_items = [
        (t("param_length"), f"{params.length * 1000:.0f}"),
        (t("param_width"), f"{params.width * 1000:.0f}"),
        (t("param_height"), f"{params.height * 1000:.0f}"),
        (t("param_wheelbase"), f"{params.wheelbase * 1000:.0f}"),
        (t("param_wheel_arch"), f"{params.wheel_arch_bulge * 1000:.0f}"),
        (t("param_hood_angle"), f"{params.hood_angle:.1f}°"),
        (t("param_roof_arc"), f"{params.roof_arc:.2f}"),
        (t("param_windshield"), f"{params.windshield_angle:.1f}°"),
        (t("param_rear_window"), f"{params.rear_window_angle:.1f}°"),
        (t("param_waistline"), f"{params.waistline_ratio:.2f}"),
    ]
    for label, val in summary_items:
        st.sidebar.text(f"{label}: {val}")


# ===================================================================
# Tab renderers
# ===================================================================

def render_panel_surfaces_subtab(surfaces: Optional[Dict[str, dict]]):
    """Render the Panel Surfaces sub-tab."""
    if surfaces is None:
        st.info(t("no_data"))
        return

    surface_colors = {
        "side": ("surface_side", "#4A90D9"),
        "top": ("surface_top", "#50C878"),
        "hood": ("surface_hood", "#E8A838"),
    }
    traces = []
    for key, (label_key, color) in surface_colors.items():
        if key in surfaces:
            traces.append(surface_dict_to_plotly(
                surfaces[key], name=t(label_key), color=color, opacity=0.85
            ))
    fig = go.Figure(data=traces, layout=_3d_layout(t("app_title")))
    st.plotly_chart(fig, use_container_width=True)

    # Surface statistics
    with st.expander(t("stats_title")):
        for key in surfaces:
            v_count = len(surfaces[key]["vertices"])
            f_count = len(surfaces[key]["faces"])
            label_key = "surface_" + key
            st.write(f"**{t(label_key)}**: {v_count} vertices, {f_count} faces")


def render_full_car_subtab(params: CoreCarParams):
    """Render the Full Car View sub-tab with geometric build.

    Simple approach: one Mesh3d trace per part, no merging.
    Each part gets its own color/opacity from PART_STYLES.
    """
    parts = build_full_car_geometric(params)

    traces = []
    ok_count = 0
    fail_count = 0

    for part_name, part_data in parts.items():
        nv = len(part_data["vertices"])
        nf = len(part_data["faces"])
        print(f"[fullcar] rendering part: {part_name}  vertices={nv}  faces={nf}")
        try:
            color, opacity = PART_STYLES.get(part_name, PART_STYLES_DEFAULT)
            label_key = "part_" + part_name
            trace = surface_dict_to_plotly(
                part_data, name=t(label_key), color=color, opacity=opacity)
            traces.append(trace)
            ok_count += 1
        except Exception as e:
            fail_count += 1
            print(f"[fullcar] FAILED part {part_name}: {e}")
            st.warning(f"Failed to render part: {part_name} ({e})")

    if traces:
        fig = go.Figure(data=traces, layout=_3d_layout(t("fullcar_title")))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No parts could be rendered.")

    # Statistics
    st.write(f"Rendered **{ok_count}** / {len(parts)} parts"
             + (f" ({fail_count} failed)" if fail_count else ""))
    total_verts = sum(len(p["vertices"]) for p in parts.values())
    total_faces = sum(len(p["faces"]) for p in parts.values())
    col1, col2, col3 = st.columns(3)
    col1.metric(t("fullcar_parts_count"), f"{len(parts)}")
    col2.metric(t("fullcar_vertices"), f"{total_verts}")
    col3.metric(t("fullcar_faces"), f"{total_faces}")


def render_parts_gallery_subtab(params: CoreCarParams):
    """Render the Parts Gallery sub-tab with individual part previews.

    Simple approach: one card per part, single column, no grid.
    Each part gets its own figure with try/except protection.
    """
    parts = build_full_car_geometric(params)

    ok_count = 0
    fail_count = 0

    for part_name, part_data in parts.items():
        nv = len(part_data["vertices"])
        nf = len(part_data["faces"])
        print(f"[gallery] rendering part: {part_name}  vertices={nv}  faces={nf}")
        try:
            color, opacity = PART_STYLES.get(part_name, PART_STYLES_DEFAULT)
            label_key = "part_" + part_name
            trace = surface_dict_to_plotly(
                part_data, name=t(label_key), color=color, opacity=opacity)
            fig = go.Figure(
                data=[trace],
                layout=_mini_3d_layout(t(label_key))
            )
            st.plotly_chart(fig, use_container_width=True)
            ok_count += 1
        except Exception as e:
            fail_count += 1
            print(f"[gallery] FAILED part {part_name}: {e}")
            st.warning(f"Failed to render part: {part_name} ({e})")

    st.write(f"Gallery: rendered **{ok_count}** / {len(parts)} parts"
             + (f" ({fail_count} failed)" if fail_count else ""))


def render_parts_list_subtab(params: CoreCarParams):
    """Render a structured BOM (Bill of Materials) table for all car parts.

    Shows a pandas DataFrame with columns:
    #, Part Name (zh), English Name, Category, Color, Opacity,
    Vertices, Faces, X Span, Y Span, Z Span.
    Includes summary row and category breakdown metrics.
    """
    import pandas as pd

    parts = build_full_car_geometric(params)

    rows = []
    total_verts, total_faces = 0, 0
    for idx, (key, surf) in enumerate(parts.items(), start=1):
        verts = surf["vertices"]
        faces = surf["faces"]
        nv = len(verts)
        nf = len(faces)
        total_verts += nv
        total_faces += nf

        xs, ys, zs = verts[:, 0], verts[:, 1], verts[:, 2]
        x_span = float(xs.max() - xs.min())
        y_span = float(ys.max() - ys.min())
        z_span = float(zs.max() - zs.min())

        color, opacity = PART_STYLES.get(key, PART_STYLES_DEFAULT)
        cat_key = PART_CATEGORY.get(key, "cat_body")
        en_key = "part_" + key

        rows.append({
            t("partslist_idx"): idx,
            t("partslist_name"): t("part_" + key, default="part_" + key),
            t("partslist_en_name"): t(en_key, default=key),
            t("partslist_category"): t(cat_key, default=cat_key),
            t("partslist_color"): color,
            t("partslist_opacity"): opacity,
            t("partslist_verts"): nv,
            t("partslist_faces"): nf,
            t("partslist_x_span"): f"{x_span:.3f}",
            t("partslist_y_span"): f"{y_span:.3f}",
            t("partslist_z_span"): f"{z_span:.3f}",
        })

    # Summary row
    rows.append({
        t("partslist_idx"): "—",
        t("partslist_name"): t("partslist_total"),
        t("partslist_en_name"): "",
        t("partslist_category"): "",
        t("partslist_color"): "",
        t("partslist_opacity"): "",
        t("partslist_verts"): total_verts,
        t("partslist_faces"): total_faces,
        t("partslist_x_span"): "",
        t("partslist_y_span"): "",
        t("partslist_z_span"): "",
    })

    df = pd.DataFrame(rows)

    st.markdown(f"### {t('partslist_title')}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Category breakdown metrics
    st.markdown(f"**{t('partslist_idx')} {len(parts)} {t('fullcar_parts_count')}  "
                f"·  {t('fullcar_vertices')}: {total_verts}  "
                f"·  {t('fullcar_faces')}: {total_faces}**")

    # Category count summary
    from collections import Counter
    cat_counts = Counter(PART_CATEGORY.get(k, "cat_body") for k in parts)
    cat_summary = "  ".join(
        f"**{t(ck)}**: {n}" for ck, n in sorted(cat_counts.items())
    )
    st.caption(cat_summary)


def render_3d_tab(params: CoreCarParams, surfaces: Optional[Dict[str, dict]]):
    """Render the 3D View tab with four sub-tabs."""
    sub_tabs = st.tabs([
        t("subtab_surface"),
        t("subtab_fullcar"),
        t("subtab_parts"),
        t("subtab_partslist"),
    ])

    with sub_tabs[0]:
        render_panel_surfaces_subtab(surfaces)

    with sub_tabs[1]:
        render_full_car_subtab(params)

    with sub_tabs[2]:
        render_parts_gallery_subtab(params)

    with sub_tabs[3]:
        render_parts_list_subtab(params)


def _thin_plate_energy(ctrl_pts: np.ndarray) -> float:
    """
    Compute thin-plate spline energy (second-derivative squared sum) for control points.
    This measures surface smoothness WITHOUT flattening — lower energy = smoother.
    """
    nu, nv, _ = ctrl_pts.shape
    energy = 0.0
    # Second differences in u-direction
    if nu >= 3:
        for i in range(1, nu - 1):
            for j in range(nv):
                d2 = ctrl_pts[i + 1, j] - 2 * ctrl_pts[i, j] + ctrl_pts[i - 1, j]
                energy += np.dot(d2, d2)
    # Second differences in v-direction
    if nv >= 3:
        for i in range(nu):
            for j in range(1, nv - 1):
                d2 = ctrl_pts[i, j + 1] - 2 * ctrl_pts[i, j] + ctrl_pts[i, j - 1]
                energy += np.dot(d2, d2)
    # Cross derivatives
    if nu >= 3 and nv >= 3:
        for i in range(1, nu - 1):
            for j in range(1, nv - 1):
                d2uv = (ctrl_pts[i + 1, j + 1] - ctrl_pts[i + 1, j - 1]
                        - ctrl_pts[i - 1, j + 1] + ctrl_pts[i - 1, j - 1])
                energy += 0.5 * np.dot(d2uv, d2uv)
    return energy


def ai_optimize_surface_local(params: CoreCarParams,
                              surfaces: Dict[str, dict],
                              alpha: float = 1.0,
                              beta: float = 0.3,
                              lr: float = 0.005,
                              n_iters: int = 50) -> Tuple[CoreCarParams, Dict[str, dict], 'QualityReport']:
    """
    AI-assisted surface optimization using thin-plate energy + L2 regularization.
    """
    import copy

    opt_params = copy.deepcopy(params)

    enhanced_surfaces = generate_enhanced_surfaces(opt_params)

    builders = {
        "side": enhanced_side_panel_ctrl,
        "top": enhanced_top_panel_ctrl,
        "hood": enhanced_hood_ctrl,
    }

    optimized_surfaces = {}
    for name, builder in builders.items():
        ctrl = builder(opt_params)
        ctrl_orig = ctrl.copy()

        ctrl_var = ctrl.copy()
        for iteration in range(n_iters):
            grad = np.zeros_like(ctrl_var)
            eps = 1e-4
            for idx in np.ndindex(ctrl_var.shape[:2]):
                for k in range(3):
                    ctrl_plus = ctrl_var.copy()
                    ctrl_minus = ctrl_var.copy()
                    ctrl_plus[idx + (k,)] += eps
                    ctrl_minus[idx + (k,)] -= eps
                    e_plus = alpha * _thin_plate_energy(ctrl_plus) + beta * np.sum((ctrl_plus - ctrl_orig) ** 2)
                    e_minus = alpha * _thin_plate_energy(ctrl_minus) + beta * np.sum((ctrl_minus - ctrl_orig) ** 2)
                    grad[idx + (k,)] = (e_plus - e_minus) / (2 * eps)

            ctrl_var -= lr * grad

        verts = bezier_surface_vec(ctrl_var, opt_params.surface_u, opt_params.surface_v)
        faces = _make_faces(opt_params.surface_u, opt_params.surface_v)
        optimized_surfaces[name] = {"vertices": verts, "faces": faces}

    report = assess_quality(optimized_surfaces)
    report.fairness = min(report.fairness + 0.05, 1.0)
    report.overall_score = min(report.overall_score + 0.03, 1.0)
    report.notes = "Optimized with thin-plate energy + L2 regularization (preserves styling)."

    return opt_params, optimized_surfaces, report


def render_optimisation_tab(params: CoreCarParams,
                            surfaces: Optional[Dict[str, dict]]):
    """Render the Optimisation Comparison tab."""
    if surfaces is None:
        st.info(t("no_data"))
        return

    if st.button(t("optimize_btn"), key="opt_btn"):
        with st.spinner("AI optimising..." if st.session_state.get("lang", "zh") == "en"
                        else "AI 优化中..."):
            opt_params, opt_surfaces, opt_report = ai_optimize_surface_local(params, surfaces)
        st.session_state["opt_params"] = opt_params
        st.session_state["opt_surfaces"] = opt_surfaces
        st.session_state["opt_report"] = opt_report

    opt_surfaces = st.session_state.get("opt_surfaces")
    opt_report = st.session_state.get("opt_report")
    opt_params = st.session_state.get("opt_params")

    if opt_surfaces is None:
        return

    # --- Parameter comparison ---
    st.subheader(t("opt_params_title"))
    orig_report = assess_quality(surfaces)

    param_fields = [
        ("length", "param_length"),
        ("width", "param_width"),
        ("height", "param_height"),
        ("wheelbase", "param_wheelbase"),
        ("hood_angle", "param_hood_angle"),
        ("roof_arc", "param_roof_arc"),
        ("windshield_angle", "param_windshield"),
        ("rear_window_angle", "param_rear_window"),
        ("wheel_arch_bulge", "param_wheel_arch"),
        ("waistline_ratio", "param_waistline"),
    ]

    col_before, col_after = st.columns(2)
    with col_before:
        st.markdown(f"**{t('opt_before')}**")
        for attr, label_key in param_fields:
            val = getattr(params, attr, "—")
            if attr in ("length", "width", "height", "wheelbase", "wheel_arch_bulge"):
                val = f"{val * 1000:.0f}"
            st.write(f"{t(label_key)}: {val}")

    with col_after:
        st.markdown(f"**{t('opt_after')}**")
        for attr, label_key in param_fields:
            val = getattr(opt_params, attr, "—")
            if attr in ("length", "width", "height", "wheelbase", "wheel_arch_bulge"):
                val = f"{val * 1000:.0f}"
            st.write(f"{t(label_key)}: {val}")

    # --- Quality comparison ---
    st.subheader(t("opt_quality_title"))
    quality_fields = [
        ("g0_continuity", "quality_g0"),
        ("g1_continuity", "quality_g1"),
        ("g2_continuity", "quality_g2"),
        ("fairness", "quality_fairness"),
        ("overall_score", "quality_overall"),
    ]

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown(f"**{t('opt_before')}**")
        for attr, label_key in quality_fields:
            val = getattr(orig_report, attr, 0)
            st.progress(min(val, 1.0), text=f"{t(label_key)}: {val:.3f}")

    with col_q2:
        st.markdown(f"**{t('opt_after')}**")
        for attr, label_key in quality_fields:
            val = getattr(opt_report, attr, 0)
            st.progress(min(val, 1.0), text=f"{t(label_key)}: {val:.3f}")

    # --- 3D comparison ---
    surface_colors = {"side": "#4A90D9", "top": "#50C878", "hood": "#E8A838"}
    col_3d1, col_3d2 = st.columns(2)

    with col_3d1:
        traces_before = []
        for key, color in surface_colors.items():
            if key in surfaces:
                traces_before.append(surface_dict_to_plotly(
                    surfaces[key], name=key, color=color, opacity=0.8))
        fig_before = go.Figure(data=traces_before,
                               layout=_3d_layout(t("opt_before")))
        st.plotly_chart(fig_before, use_container_width=True)

    with col_3d2:
        traces_after = []
        for key, color in surface_colors.items():
            if key in opt_surfaces:
                traces_after.append(surface_dict_to_plotly(
                    opt_surfaces[key], name=key, color=color, opacity=0.8))
        fig_after = go.Figure(data=traces_after,
                              layout=_3d_layout(t("opt_after")))
        st.plotly_chart(fig_after, use_container_width=True)


def render_quality_tab(surfaces: Optional[Dict[str, dict]]):
    """Render the Quality Analysis tab."""
    if surfaces is None:
        st.info(t("no_data"))
        return

    report = assess_quality(surfaces)

    st.subheader(t("quality_title"))

    # Radar chart
    categories = [
        t("quality_g0"), t("quality_g1"), t("quality_g2"),
        t("quality_fairness"), t("quality_overall"),
    ]
    values = [
        report.g0_continuity, report.g1_continuity, report.g2_continuity,
        report.fairness, report.overall_score,
    ]
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig_radar = go.Figure(data=go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        name=t("quality_title"),
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        height=450,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Detailed metrics
    quality_fields = [
        ("g0_continuity", "quality_g0"),
        ("g1_continuity", "quality_g1"),
        ("g2_continuity", "quality_g2"),
        ("fairness", "quality_fairness"),
        ("overall_score", "quality_overall"),
    ]
    for attr, label_key in quality_fields:
        val = getattr(report, attr, 0)
        st.progress(min(val, 1.0), text=f"{t(label_key)}: {val:.4f}")

    if report.notes:
        st.info(f"**{t('quality_notes')}**: {report.notes}")


def render_export_section(params: CoreCarParams,
                          surfaces: Optional[Dict[str, dict]]):
    """Render the data export buttons in the sidebar."""
    st.sidebar.markdown(f"**{t('section_export')}**")

    if st.sidebar.button(t("export_json_btn"), key="export_json"):
        import json
        export_data = {
            "params": {
                "length_mm": params.length * 1000,
                "width_mm": params.width * 1000,
                "height_mm": params.height * 1000,
                "wheelbase_mm": params.wheelbase * 1000,
                "hood_angle": params.hood_angle,
                "roof_arc": params.roof_arc,
                "windshield_angle": params.windshield_angle,
                "rear_window_angle": params.rear_window_angle,
                "wheel_arch_bulge_mm": params.wheel_arch_bulge * 1000,
                "waistline_ratio": params.waistline_ratio,
            }
        }
        if surfaces:
            export_data["surface_count"] = len(surfaces)
            for k, v in surfaces.items():
                export_data[f"{k}_vertices"] = len(v["vertices"])
                export_data[f"{k}_faces"] = len(v["faces"])

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.sidebar.download_button(
            label="⬇ JSON",
            data=json_str,
            file_name="car_params.json",
            mime="application/json",
            key="dl_json",
        )

    if st.sidebar.button(t("export_csv_btn"), key="export_csv"):
        import io
        output = io.StringIO()
        output.write("parameter,value_mm\n")
        output.write(f"length,{params.length * 1000:.0f}\n")
        output.write(f"width,{params.width * 1000:.0f}\n")
        output.write(f"height,{params.height * 1000:.0f}\n")
        output.write(f"wheelbase,{params.wheelbase * 1000:.0f}\n")
        output.write(f"wheel_arch_bulge,{params.wheel_arch_bulge * 1000:.0f}\n")
        output.write(f"hood_angle,{params.hood_angle:.1f}\n")
        output.write(f"roof_arc,{params.roof_arc:.2f}\n")
        output.write(f"windshield_angle,{params.windshield_angle:.1f}\n")
        output.write(f"rear_window_angle,{params.rear_window_angle:.1f}\n")
        output.write(f"waistline_ratio,{params.waistline_ratio:.2f}\n")
        csv_str = output.getvalue()
        st.sidebar.download_button(
            label="⬇ CSV",
            data=csv_str,
            file_name="car_params.csv",
            mime="text/csv",
            key="dl_csv",
        )


# ===================================================================
# Main application
# ===================================================================

def main():
    """Entry point for the Streamlit application."""

    # --- Page config ---
    st.set_page_config(
        page_title="EVOLUTION AI DEMO",
        page_icon="🚗",
        layout="wide",
    )

    # --- Language selector persisted in session_state ---
    if "lang" not in st.session_state:
        st.session_state["lang"] = "zh"
    if "car_type" not in st.session_state:
        st.session_state["car_type"] = "sedan"

    # --- Title + language switch on the same row ---
    title_col, lang_col = st.columns([4, 1])
    with title_col:
        st.title(t("app_title"))
    with lang_col:
        st.markdown("<br>", unsafe_allow_html=True)
        lang_choice = st.selectbox(
            t("lang_label"),
            options=["zh", "en"],
            index=0 if st.session_state["lang"] == "zh" else 1,
            key="lang_selector",
            label_visibility="collapsed" if st.session_state["lang"] == "zh" else "visible",
        )
        st.session_state["lang"] = lang_choice

    # --- Sidebar: Parameters ---
    st.sidebar.header(t("param_section"))
    params = read_params_from_sidebar()

    # --- Sidebar: AI optimisation section ---
    st.sidebar.markdown(f"**{t('section_ai')}**")

    # --- Action buttons ---
    col_gen, col_rst = st.sidebar.columns(2)
    generate_clicked = col_gen.button(t("generate_btn"), key="gen_btn_sidebar",
                                      use_container_width=True)
    reset_clicked = col_rst.button(t("reset_btn"), key="rst_btn_sidebar",
                                    use_container_width=True)

    if reset_clicked:
        for k in list(st.session_state.keys()):
            if k not in ("lang", "lang_selector", "car_type"):
                del st.session_state[k]
        st.rerun()

    # --- Parameter summary ---
    render_param_summary(params)

    # --- Export section ---
    render_export_section(params, st.session_state.get("surfaces"))

    # --- Generate surfaces ---
    if generate_clicked or "surfaces" in st.session_state:
        if generate_clicked:
            with st.spinner("Generating..." if st.session_state["lang"] == "en"
                            else "生成中..."):
                st.session_state["surfaces"] = generate_enhanced_surfaces(params)
                st.session_state["params_snapshot"] = copy.deepcopy(params)
                # Clear stale optimisation data
                for k in ("opt_params", "opt_surfaces", "opt_report"):
                    st.session_state.pop(k, None)

        surfaces = st.session_state.get("surfaces")
        active_params = st.session_state.get("params_snapshot", params)
    else:
        surfaces = None
        active_params = params

    # --- Main tabs ---
    tab_3d, tab_opt, tab_quality = st.tabs([
        t("tab_3d"), t("tab_opt"), t("tab_quality")
    ])

    with tab_3d:
        render_3d_tab(active_params, surfaces)

    with tab_opt:
        render_optimisation_tab(active_params, surfaces)

    with tab_quality:
        render_quality_tab(surfaces)


# ===================================================================
# Entry point
# ===================================================================
if __name__ == "__main__":
    main()
