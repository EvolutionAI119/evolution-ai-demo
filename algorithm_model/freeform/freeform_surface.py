"""
Freeform Surface Deformation Module

在已有车体网格上施加 NURBS 曲面变形。
支持预设变形（fender bulge, door dent, hood scoop, character line）。

设计思路：
1. 变形区域映射到局部 NURBS 曲面的 (u, v) ∈ [0, 1]² 参数域
2. 变形量 = NURBS 曲面的 z 分量偏移
3. 用 smoothstep 确保变形区域边界 C1 连续过渡到零
"""

import numpy as np
import trimesh
from typing import Dict, Tuple, Optional, List
from .nurbs_core import (
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
)


# ============================================================
# 预设变形定义
# ============================================================

DEFORM_PRESETS = {
    'fender_bulge': {
        'description': '轮眉凸起 — 翼子板区域的鼓包',
        'control_points': None,  # 运行时生成
        'size': (0.3, 0.2),  # u, v 方向的变形影响范围（占参数域比例）
        'amplitude': 0.05,  # z 方向最大偏移（米）
        'center': (0.5, 0.5),  # 变形中心在参数域中的位置
    },
    'door_dent': {
        'description': '门板凹痕 — 车门区域的局部凹陷',
        'size': (0.25, 0.3),
        'amplitude': -0.02,
        'center': (0.5, 0.5),
    },
    'hood_scoop': {
        'description': '发动机盖进气口 — 机盖上的隆起',
        'size': (0.4, 0.15),
        'amplitude': 0.04,
        'center': (0.5, 0.5),
    },
    'character_line': {
        'description': '腰线特征线 — 沿车长方向的凸起线条',
        'size': (0.8, 0.05),
        'amplitude': 0.015,
        'center': (0.5, 0.5),
    },
    'roof_sculpt': {
        'description': '车顶雕塑感 — 车顶区域的柔和凹凸',
        'size': (0.5, 0.4),
        'amplitude': 0.03,
        'center': (0.5, 0.5),
    },
}


def _gaussian_bump_control_grid(size: Tuple[float, float],
                                  amplitude: float,
                                  grid_n: int = 5) -> np.ndarray:
    """
    生成高斯凸起形状的控制点网格（z 分量）
    
    用于创建平滑的局部变形。控制点按高斯分布赋值。
    
    Args:
        size: (sigma_u, sigma_v) 高斯宽度参数
        amplitude: 最大偏移量
        grid_n: 控制网格大小（grid_n × grid_n）
    
    Returns:
        (grid_n, grid_n) z 偏移控制点
    """
    sigma_u, sigma_v = size
    u = np.linspace(-1, 1, grid_n)
    v = np.linspace(-1, 1, grid_n)
    U, V = np.meshgrid(u, v, indexing='ij')
    
    # 高斯
    z = amplitude * np.exp(-(U**2 / (2 * sigma_u**2) + V**2 / (2 * sigma_v**2)))
    
    return z


class FreeformDeformation:
    """
    自由变形管理器
    
    管理多个局部 NURBS 变形，支持叠加。
    
    Usage:
        ffd = FreeformDeformation()
        ffd.add_deformation('fender_bulge', center_x=1.2, center_z=0.5, 
                           amplitude=0.06, size=(0.3, 0.2))
        ffd.add_deformation('hood_scoop', center_x=-0.8, center_z=0.9,
                           amplitude=0.04, size=(0.4, 0.15))
        
        vertices = mesh.vertices.copy()
        vertices_deformed = ffd.apply(vertices, body_length=4.5, body_height=1.4)
    """
    
    def __init__(self):
        self.deformations: List[Dict] = []
    
    def add_deformation(self, preset_name: str,
                         center_x: float = 0.0,
                         center_z: float = 0.5,
                         amplitude: Optional[float] = None,
                         size: Optional[Tuple[float, float]] = None,
                         grid_n: int = 5):
        """
        添加一个局部变形
        
        Args:
            preset_name: 预设名称（见 DEFORM_PRESETS）
            center_x: 变形中心在车身 x 方向的位置（米，-L/2 ~ L/2）
            center_z: 变形中心在车身 z 方向的归一化位置（0=底, 1=顶）
            amplitude: 振幅覆盖（None 用预设默认值）
            size: 影响范围覆盖（None 用预设默认值）
            grid_n: NURBS 控制网格大小
        """
        preset = DEFORM_PRESETS.get(preset_name)
        if preset is None:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(DEFORM_PRESETS.keys())}")
        
        amp = amplitude if amplitude is not None else preset['amplitude']
        sz = size if size is not None else preset['size']
        
        # 生成 z 偏移控制点网格
        z_grid = _gaussian_bump_control_grid(
            size=(sz[0] * 2, sz[1] * 2),  # 扩大 sigma 以覆盖控制网格
            amplitude=amp,
            grid_n=grid_n,
        )
        
        self.deformations.append({
            'preset_name': preset_name,
            'center_x': center_x,
            'center_z': center_z,
            'amplitude': amp,
            'size': sz,
            'z_grid': z_grid,
            'grid_n': grid_n,
        })
    
    def compute_deformation_field(self, vertices: np.ndarray,
                                    body_length: float,
                                    body_height: float) -> np.ndarray:
        """
        计算所有变形在当前顶点集上产生的位移场
        
        Args:
            vertices: (N, 3) 顶点坐标
            body_length: 车身总长度（米）
            body_height: 车身总高度（米）
        
        Returns:
            (N, 3) 位移向量（主要是 z/y 方向的偏移）
        """
        displacement = np.zeros_like(vertices)
        
        for deform in self.deformations:
            center_x = deform['center_x']
            center_z_norm = deform['center_z']
            sz_u, sz_v = deform['size']
            z_grid = deform['z_grid']
            grid_n = deform['grid_n']
            
            # 将顶点映射到变形局部坐标 (u_local, v_local) ∈ [-1, 1]²
            # u_local: x 方向（沿车长）
            # v_local: z 方向（沿车高）
            half_L = body_length / 2
            u_local = (vertices[:, 0] - center_x) / (sz_u * half_L)
            v_local = (vertices[:, 2] / body_height - center_z_norm) / sz_v
            
            # 创建 NURBS 曲面的控制点（3D）
            # 控制点网格的 x 分量 = u_local * sz_u * half_L（局部变形范围）
            # 控制点网格的 z 分量 = z_grid（偏移量）
            control_pts = np.zeros((grid_n, grid_n, 3))
            u_knots = np.linspace(-1, 1, grid_n)
            v_knots = np.linspace(-1, 1, grid_n)
            for i in range(grid_n):
                for j in range(grid_n):
                    control_pts[i, j, 0] = u_knots[i] * sz_u * half_L
                    control_pts[i, j, 1] = 0  # y 方向不变
                    control_pts[i, j, 2] = z_grid[i, j]
            
            surf = nurbs_surface_from_grid(
                control_points=control_pts,
                degree_u=min(3, grid_n - 1),
                degree_v=min(3, grid_n - 1),
            )
            
            # 对每个顶点，如果在变形影响范围内，计算位移
            # 使用 smoothstep 边界衰减
            mask = (np.abs(u_local) < 1.5) & (np.abs(v_local) < 1.5)
            
            if not np.any(mask):
                continue
            
            # smoothstep 衰减
            def smoothstep_edge(t):
                """t ∈ [0, 1.5] → smoothstep falloff"""
                t = np.abs(t)
                if t >= 1.5:
                    return 0.0
                if t <= 0.8:
                    return 1.0
                # 0.8 ~ 1.5 之间平滑过渡
                s = (t - 0.8) / 0.7
                return 1.0 - s * s * (3 - 2 * s)
            
            for idx in np.where(mask)[0]:
                u_val = (u_local[idx] + 1) / 2  # [-1,1] → [0,1]
                v_val = (v_local[idx] + 1) / 2
                
                u_val = np.clip(u_val, 0, 1)
                v_val = np.clip(v_val, 0, 1)
                
                offset = evaluate_surface(surf, u_val, v_val)
                
                # 应用 smoothstep 衰减
                falloff_u = smoothstep_edge(u_local[idx])
                falloff_v = smoothstep_edge(v_local[idx])
                falloff = falloff_u * falloff_v
                
                displacement[idx, 1] += offset[1] * falloff  # y 方向
                displacement[idx, 2] += offset[2] * falloff  # z 方向
        
        return displacement
    
    def apply(self, vertices: np.ndarray,
              body_length: float,
              body_height: float) -> np.ndarray:
        """
        将变形应用到顶点集
        
        Args:
            vertices: (N, 3) 原始顶点坐标
            body_length: 车身总长度
            body_height: 车身总高度
        
        Returns:
            (N, 3) 变形后的顶点坐标
        """
        displacement = self.compute_deformation_field(vertices, body_length, body_height)
        return vertices + displacement
    
    def summary(self) -> List[Dict]:
        """返回当前所有变形的摘要"""
        return [
            {
                'preset': d['preset_name'],
                'center_x': d['center_x'],
                'center_z': d['center_z'],
                'amplitude': d['amplitude'],
                'size': d['size'],
            }
            for d in self.deformations
        ]
