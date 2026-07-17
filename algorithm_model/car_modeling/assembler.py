"""
Full-car assembler: builds all body panels and merges them into a single mesh.
"""
from typing import Dict, List, Optional
import numpy as np

try:
    import trimesh
except ImportError:
    trimesh = None

from .car_params import CarParams


def _make_box_mesh(cx, cy, cz, sx, sy, sz, name="part"):
    """Create a simple box mesh centered at (cx,cy,cz) with half-sizes (sx,sy,sz)."""
    if trimesh is None:
        return None
    vertices = np.array([
        [cx - sx, cy - sy, cz - sz],
        [cx + sx, cy - sy, cz - sz],
        [cx + sx, cy + sy, cz - sz],
        [cx - sx, cy + sy, cz - sz],
        [cx - sx, cy - sy, cz + sz],
        [cx + sx, cy - sy, cz + sz],
        [cx + sx, cy + sy, cz + sz],
        [cx - sx, cy + sy, cz + sz],
    ], dtype=np.float64)
    faces = np.array([
        [0, 1, 2], [0, 2, 3],  # bottom
        [4, 6, 5], [4, 7, 6],  # top
        [0, 4, 5], [0, 5, 1],  # front
        [2, 6, 7], [2, 7, 3],  # back
        [0, 3, 7], [0, 7, 4],  # left
        [1, 5, 6], [1, 6, 2],  # right
    ], dtype=np.int64)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    mesh.metadata["name"] = name
    return mesh


def _make_cylinder_mesh(cx, cy, cz, radius, height, segments=16, name="cylinder"):
    """Create a cylinder mesh centered at (cx,cy,cz)."""
    if trimesh is None:
        return None
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=segments)
    mesh.apply_translation([cx, cy, cz])
    mesh.metadata["name"] = name
    return mesh


def build_full_car(params: CarParams) -> Dict[str, "trimesh.Trimesh"]:
    """
    Build all car body parts from the given parameters.

    Returns a dict mapping part name -> trimesh.Trimesh.
    Parts include: body, hood, roof, windshield, rear_window,
                   wheel_fl, wheel_fr, wheel_rl, wheel_rr
    """
    p = params
    parts: Dict[str, trimesh.Trimesh] = {}

    half_w = p.width / 2
    half_l = p.length / 2
    half_h = p.height / 2

    # Main body block (lower body)
    body_h = p.height * p.waistline_ratio
    parts["body"] = _make_box_mesh(
        0, 0, body_h / 2,
        half_l * 0.95, half_w * 0.95, body_h / 2,
        name="body"
    )

    # Hood
    hood_cx = half_l - p.front_overhang / 2 - 0.3
    hood_cz = body_h + 0.08
    hood_len = p.front_overhang * 0.8
    parts["hood"] = _make_box_mesh(
        hood_cx, 0, hood_cz,
        hood_len / 2, half_w * 0.9, 0.06,
        name="hood"
    )

    # Roof
    roof_cx = -p.rear_overhang * 0.3
    roof_cz = p.height * 0.9
    roof_len = p.wheelbase * 0.7
    parts["roof"] = _make_box_mesh(
        roof_cx, 0, roof_cz,
        roof_len / 2, half_w * 0.85, 0.05,
        name="roof"
    )

    # Windshield (simplified as angled box)
    ws_cx = p.wheelbase / 2 - 0.3
    ws_cz = body_h + (p.height - body_h) * 0.6
    parts["windshield"] = _make_box_mesh(
        ws_cx, 0, ws_cz,
        0.4, half_w * 0.8, 0.02,
        name="windshield"
    )

    # Rear window
    rw_cx = -p.wheelbase / 2 + 0.3
    rw_cz = body_h + (p.height - body_h) * 0.6
    parts["rear_window"] = _make_box_mesh(
        rw_cx, 0, rw_cz,
        0.4, half_w * 0.8, 0.02,
        name="rear_window"
    )

    # Wheels
    wr = p.wheel_radius
    ww = p.wheel_width
    wy_off = half_w + ww / 2 + p.wheel_arch_bulge
    front_x = p.wheelbase / 2
    rear_x = -p.wheelbase / 2

    parts["wheel_fl"] = _make_cylinder_mesh(front_x, wy_off, wr, wr, ww, name="wheel_fl")
    parts["wheel_fr"] = _make_cylinder_mesh(front_x, -wy_off, wr, wr, ww, name="wheel_fr")
    parts["wheel_rl"] = _make_cylinder_mesh(rear_x, wy_off, wr, wr, ww, name="wheel_rl")
    parts["wheel_rr"] = _make_cylinder_mesh(rear_x, -wy_off, wr, wr, ww, name="wheel_rr")

    return parts


def compute_stats(parts: Dict[str, "trimesh.Trimesh"]) -> Dict[str, int]:
    """Compute basic statistics for all parts."""
    total_verts = 0
    total_faces = 0
    for name, mesh in parts.items():
        if mesh is not None:
            total_verts += len(mesh.vertices)
            total_faces += len(mesh.faces)
    return {"parts": len(parts), "vertices": total_verts, "faces": total_faces}


def merge_all(parts: Dict[str, "trimesh.Trimesh"]) -> "trimesh.Trimesh":
    """Merge all part meshes into a single trimesh.Trimesh."""
    if trimesh is None:
        raise RuntimeError("trimesh is not installed")
    meshes = [m for m in parts.values() if m is not None]
    if not meshes:
        return trimesh.Trimesh()
    combined = trimesh.util.concatenate(meshes)
    return combined
