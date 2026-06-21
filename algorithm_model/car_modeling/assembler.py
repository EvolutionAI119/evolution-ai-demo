"""
整车组装器

将 8 大部件组装为完整汽车，并提供统计功能。
支持导出为 GLB / STL / OBJ / PLY。
"""
import json
import trimesh
from typing import Dict, Any
from .car_params import CarParams
from .body import build_body
from .glass import build_glass
from .wheels import build_wheels
from .lights import build_headlights, build_taillights
from .grille import build_grille
from .mirrors import build_mirrors
from .seams import build_door_seams


def build_full_car(params: CarParams) -> Dict[str, trimesh.Trimesh]:
    """
    组装完整汽车造型

    Returns:
        dict: 8 个部件 mesh
        {
            "body": 车壳,
            "glass": 玻璃,
            "wheels": 4 轮,
            "headlights": 大灯,
            "taillights": 尾灯,
            "grille": 格栅,
            "mirrors": 后视镜,
            "seams": 门缝
        }
    """
    return {
        "body": build_body(params),
        "glass": build_glass(params),
        "wheels": build_wheels(params),
        "headlights": build_headlights(params),
        "taillights": build_taillights(params),
        "grille": build_grille(params),
        "mirrors": build_mirrors(params),
        "seams": build_door_seams(params),
    }


def merge_all(parts: Dict[str, trimesh.Trimesh]) -> trimesh.Trimesh:
    """合并所有部件为单个 mesh"""
    return trimesh.util.concatenate(list(parts.values()))


def compute_stats(parts: Dict[str, trimesh.Trimesh]) -> Dict[str, Any]:
    """
    计算整车统计信息

    Returns:
        {
            "total_vertices": 总顶点数,
            "total_faces": 总面数,
            "components": {部件: (verts, faces, color)},
            "bounds": 包围盒
        }
    """
    total_verts = sum(len(m.vertices) for m in parts.values())
    total_faces = sum(len(m.faces) for m in parts.values())
    components = {}
    for name, m in parts.items():
        color = m.visual.face_colors[0].tolist() if len(m.visual.face_colors) > 0 else None
        components[name] = {
            "vertices": len(m.vertices),
            "faces": len(m.faces),
            "color": color,
        }
    all_meshes = merge_all(parts)
    return {
        "total_vertices": total_verts,
        "total_faces": total_faces,
        "components": components,
        "bounds": all_meshes.bounds.tolist(),  # [[xmin,ymin,zmin], [xmax,ymax,zmax]]
    }


def export(
    parts: Dict[str, trimesh.Trimesh], file_path: str, file_type: str = None,
) -> str:
    """
    导出整车为 3D 文件

    Args:
        parts: 8 部件字典
        file_path: 输出文件路径（扩展名推断类型，支持 .glb / .stl / .obj / .ply）
        file_type: 显式指定类型（可选）

    Returns:
        输出文件的绝对路径
    """
    merged = merge_all(parts)
    merged.export(file_path, file_type=file_type)
    return file_path
