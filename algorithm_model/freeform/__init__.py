"""
freeform — NURBS 自由曲面 + 变形模块

提供：
- NURBS 基函数、曲线/曲面求值（nurbs_core）
- 自由变形管理器 + 5 个预设（freeform_surface）
- 圆角/倒角曲面（fillet_surface）
- 扫描曲面（swept_surface）
"""
from .nurbs_core import (
    find_span,
    basis_funs,
    curve_point,
    surface_point,
    open_uniform_knots,
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
)
from .freeform_surface import (
    FreeformDeformation,
    DEFORM_PRESETS,
)
from .fillet_surface import (
    IntersectionCurve,
    create_fillet_surface,
    create_chamfer_surface,
    create_wheel_arch_fillet,
    surface_to_mesh,
)
from .swept_surface import (
    SweptSurface,
    FrenetFrame,
    generate_circle_section,
    generate_rectangle_section,
)

__all__ = [
    "find_span",
    "basis_funs",
    "curve_point",
    "surface_point",
    "open_uniform_knots",
    "nurbs_surface_from_grid",
    "evaluate_surface",
    "evaluate_surface_mesh",
    "FreeformDeformation",
    "DEFORM_PRESETS",
    "IntersectionCurve",
    "create_fillet_surface",
    "create_chamfer_surface",
    "create_wheel_arch_fillet",
    "surface_to_mesh",
    "SweptSurface",
    "FrenetFrame",
    "generate_circle_section",
    "generate_rectangle_section",
]
