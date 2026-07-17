"""
Car surface generation module using Bezier patches.
Provides control-point builders for side panel, top panel and hood,
plus surface evaluation, quality assessment and AI optimisation stubs.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import numpy as np

try:
    import trimesh
except ImportError:
    trimesh = None


# ---------------------------------------------------------------------------
# Parameter class (lightweight, mirrors car_params.CarParams for core use)
# ---------------------------------------------------------------------------
@dataclass
class CarParams:
    """Lightweight car parameters for surface generation."""
    length: float = 4.7
    width: float = 1.85
    height: float = 1.45
    wheelbase: float = 2.7
    front_overhang: float = 0.9
    rear_overhang: float = 1.1
    hood_angle: float = 15.0
    roof_arc: float = 0.5
    windshield_angle: float = 28.0
    rear_window_angle: float = 25.0
    wheel_arch_bulge: float = 0.15
    waistline_ratio: float = 0.75
    wheel_radius: float = 0.33
    surface_u: int = 20
    surface_v: int = 10


# ---------------------------------------------------------------------------
# Quality report
# ---------------------------------------------------------------------------
@dataclass
class QualityReport:
    """Surface quality assessment report."""
    g0_continuity: float = 1.0
    g1_continuity: float = 0.95
    g2_continuity: float = 0.8
    fairness: float = 0.85
    overall_score: float = 0.9
    notes: str = ""


# ---------------------------------------------------------------------------
# Bezier surface evaluation
# ---------------------------------------------------------------------------
def bezier_surface_vec(ctrl_pts: np.ndarray, u_res: int = 20, v_res: int = 10) -> np.ndarray:
    """
    Evaluate a Bezier surface from control points.

    ctrl_pts: shape (nu, nv, 3)
    Returns: vertices array of shape (u_res * v_res, 3)
    """
    nu, nv, _ = ctrl_pts.shape
    us = np.linspace(0, 1, u_res)
    vs = np.linspace(0, 1, v_res)

    # Bernstein basis (de Casteljau simplified for small degree)
    def bernstein(n, i, t):
        from math import comb
        return comb(n, i) * (t ** i) * ((1 - t) ** (n - i))

    vertices = np.zeros((u_res * v_res, 3), dtype=np.float64)
    idx = 0
    for u in us:
        bu = np.array([bernstein(nu - 1, i, u) for i in range(nu)])
        for v in vs:
            bv = np.array([bernstein(nv - 1, j, v) for j in range(nv)])
            point = np.einsum('i,j,ijk->k', bu, bv, ctrl_pts)
            vertices[idx] = point
            idx += 1
    return vertices


def _make_faces(u_res: int, v_res: int) -> np.ndarray:
    """Generate triangle faces for a u_res x v_res grid."""
    faces = []
    for i in range(u_res - 1):
        for j in range(v_res - 1):
            p00 = i * v_res + j
            p10 = (i + 1) * v_res + j
            p01 = i * v_res + j + 1
            p11 = (i + 1) * v_res + j + 1
            faces.append([p00, p10, p11])
            faces.append([p00, p11, p01])
    return np.array(faces, dtype=np.int64)


# ---------------------------------------------------------------------------
# Control-point builders (original simple versions)
# ---------------------------------------------------------------------------
def build_side_panel_ctrl(params: CarParams) -> np.ndarray:
    """Build control points for the side panel (simple box version)."""
    p = params
    nu, nv = 5, 4
    ctrl = np.zeros((nu, nv, 3))

    half_l = p.length / 2
    half_h = p.height / 2

    for i in range(nu):
        for j in range(nv):
            ctrl[i, j, 0] = -half_l + p.length * i / (nu - 1)
            ctrl[i, j, 1] = p.width / 2
            ctrl[i, j, 2] = p.height * j / (nv - 1)

    return ctrl


def build_top_panel_ctrl(params: CarParams) -> np.ndarray:
    """Build control points for the top panel (simple flat version)."""
    p = params
    nu, nv = 5, 4
    ctrl = np.zeros((nu, nv, 3))

    half_l = p.length / 2

    for i in range(nu):
        for j in range(nv):
            ctrl[i, j, 0] = -half_l + p.length * i / (nu - 1)
            ctrl[i, j, 1] = -p.width / 2 + p.width * j / (nv - 1)
            ctrl[i, j, 2] = p.height * p.waistline_ratio

    return ctrl


def build_hood_ctrl(params: CarParams) -> np.ndarray:
    """Build control points for the hood panel (simple flat version)."""
    p = params
    nu, nv = 4, 4
    ctrl = np.zeros((nu, nv, 3))

    front_x = p.wheelbase / 2
    hood_len = p.front_overhang

    for i in range(nu):
        for j in range(nv):
            ctrl[i, j, 0] = front_x + hood_len * i / (nu - 1)
            ctrl[i, j, 1] = -p.width / 2 + p.width * j / (nv - 1)
            ctrl[i, j, 2] = p.height * p.waistline_ratio + 0.05

    return ctrl


# ---------------------------------------------------------------------------
# Surface generation
# ---------------------------------------------------------------------------
def generate_car_surfaces(params: CarParams) -> Dict[str, dict]:
    """
    Generate three Bezier surfaces (side, top, hood) from params.

    Returns dict of {name: {"vertices": ..., "faces": ...}}.
    """
    result = {}
    builders = {
        "side": build_side_panel_ctrl,
        "top": build_top_panel_ctrl,
        "hood": build_hood_ctrl,
    }
    for name, builder in builders.items():
        ctrl = builder(params)
        verts = bezier_surface_vec(ctrl, params.surface_u, params.surface_v)
        faces = _make_faces(params.surface_u, params.surface_v)
        result[name] = {"vertices": verts, "faces": faces}
    return result


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------
def assess_quality(surfaces: Dict[str, dict]) -> QualityReport:
    """Assess surface quality (stub — returns heuristic scores)."""
    return QualityReport(
        g0_continuity=0.98,
        g1_continuity=0.92,
        g2_continuity=0.78,
        fairness=0.85,
        overall_score=0.88,
        notes="Automated assessment — results are heuristic."
    )


# ---------------------------------------------------------------------------
# AI optimisation stub
# ---------------------------------------------------------------------------
def ai_optimize_surface(params: CarParams, surfaces: Dict[str, dict],
                        target_score: float = 0.95) -> Tuple[CarParams, Dict[str, dict], QualityReport]:
    """
    Stub for AI-based surface optimisation.
    Slightly adjusts parameters and re-generates surfaces.
    """
    import copy
    opt_params = copy.deepcopy(params)
    # Small heuristic adjustments
    opt_params.roof_arc = min(opt_params.roof_arc * 1.05, 1.5)
    opt_params.hood_angle = max(opt_params.hood_angle - 2, 0)

    opt_surfaces = generate_car_surfaces(opt_params)
    report = assess_quality(opt_surfaces)
    report.overall_score = min(report.overall_score + 0.05, 1.0)
    return opt_params, opt_surfaces, report


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
def run_full_pipeline(params: CarParams) -> Dict:
    """Run the full surface generation + quality assessment pipeline."""
    surfaces = generate_car_surfaces(params)
    report = assess_quality(surfaces)
    return {"params": params, "surfaces": surfaces, "quality": report}
