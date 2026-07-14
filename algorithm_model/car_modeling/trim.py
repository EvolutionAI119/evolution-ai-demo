"""
Trim Strip Module — 装饰条/密封条建模

基于 SweptSurface，沿车身轮廓路径扫描矩形/自定义截面。

典型用例：
- 车门装饰条（chrome_trim）
- 窗框密封条（rubber_seal）
- 保险杠饰条（body_molding）
- 腰线饰条（waist_trim）

预设参数：
- chrome_trim: 镀铬亮条 — 窄宽、薄高、高采样
- rubber_seal: 橡胶密封条 — D 形截面、柔软
- body_molding: 车身防擦条 — 宽厚、保护性
"""

import numpy as np
from typing import Optional, Dict, Any, Tuple, Callable
from ..freeform.swept_surface import SweptSurface
from ..freeform.nurbs_core import (
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
)


# ============================================================
# 预设定义
# ============================================================

TRIM_PRESETS: Dict[str, Dict[str, Any]] = {
    'chrome_trim': {
        'description': '镀铬亮条 — 窄宽薄高，装饰性',
        'section_type': 'rectangle',
        'section_params': {
            'width': 0.015,   # 15mm 宽
            'height': 0.004,  # 4mm 高
            'n_per_side': 3,
        },
        'path_samples': 30,
        'degree_u': 3,
        'degree_v': 2,
        'color': (220, 220, 230, 255),  # 亮银色
    },
    'rubber_seal': {
        'description': '橡胶密封条 — D 形截面，密封性',
        'section_type': 'custom',  # D 形截面
        'section_params': {
            # D 形截面：底部平 + 上部半圆
            'points': None,  # 由 _generate_d_section 动态生成
        },
        'path_samples': 25,
        'degree_u': 3,
        'degree_v': 3,
        'color': (30, 30, 30, 255),  # 黑色橡胶
    },
    'body_molding': {
        'description': '车身防擦条 — 宽厚保护性',
        'section_type': 'rectangle',
        'section_params': {
            'width': 0.030,   # 30mm 宽
            'height': 0.010,  # 10mm 高
            'n_per_side': 3,
        },
        'path_samples': 25,
        'degree_u': 3,
        'degree_v': 2,
        'color': (40, 40, 45, 255),  # 深灰
    },
}


def _generate_d_section(
    base_width: float = 0.012,
    total_height: float = 0.008,
    n_points: int = 16,
) -> np.ndarray:
    """
    生成 D 形截面（底部平坦 + 上部半圆）

    用于橡胶密封条。

    Args:
        base_width: 底部宽度
        total_height: 总高度
        n_points: 离散点数

    Returns:
        (n_points, 2) D 形截面点
    """
    hw = base_width / 2
    flat_height = total_height * 0.4  # 平底部分占 40%
    arc_radius = base_width / 2

    points = []
    # 底部左 → 底部右
    n_flat = max(3, n_points // 4)
    for i in range(n_flat):
        t = i / (n_flat - 1)
        points.append([-hw + base_width * t, 0])

    # 上部半圆弧（右 → 顶部 → 左）
    n_arc = n_points - n_flat
    angles = np.linspace(0, np.pi, n_arc, endpoint=True)
    arc_center = np.array([0, flat_height])

    for angle in angles:
        x = arc_radius * np.cos(angle)
        y = flat_height + arc_radius * np.sin(angle)
        points.append([x, y])

    return np.array(points)


# ============================================================
# TrimStrip 类
# ============================================================

class TrimStrip:
    """
    装饰条/密封条建模

    基于 SweptSurface，沿车身轮廓路径扫描截面。

    Args:
        path_points: (M, 3) 路径点（沿车身轮廓）
        preset: 预设名称 ('chrome_trim', 'rubber_seal', 'body_molding')
            如果为 None，使用 custom_params
        custom_params: 自定义参数 dict，覆盖预设
            - section_type: str
            - section_params: dict
            - path_samples: int
            - degree_u: int
            - degree_v: int
            - color: Tuple[int, int, int, int]
        offset: 截面偏移量（沿法线方向的额外偏移，用于贴合车身表面）
        section_scale: Optional 可变截面缩放函数
    """

    def __init__(
        self,
        path_points: np.ndarray,
        preset: Optional[str] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        offset: float = 0.0,
        section_scale: Optional[Callable[[float], float]] = None,
    ):
        self.path_points = np.array(path_points, dtype=float)
        self.preset = preset
        self.offset = offset
        self.section_scale = section_scale

        # 获取参数（预设 + 自定义覆盖）
        if preset is not None:
            assert preset in TRIM_PRESETS, f"Unknown preset: {preset}. Available: {list(TRIM_PRESETS.keys())}"
            self._params = dict(TRIM_PRESETS[preset])
        else:
            self._params = {
                'section_type': 'rectangle',
                'section_params': {
                    'width': 0.02,
                    'height': 0.008,
                    'n_per_side': 3,
                },
                'path_samples': 20,
                'degree_u': 3,
                'degree_v': 2,
                'color': (180, 180, 180, 255),
            }

        # 自定义参数覆盖
        if custom_params is not None:
            self._params.update(custom_params)

        # 特殊处理 rubber_seal 的 D 形截面
        if preset == 'rubber_seal' and self._params['section_type'] == 'custom':
            d_section = _generate_d_section()
            self._params['section_params']['points'] = d_section

        # 内部 SweptSurface（延迟构建）
        self._swept: Optional[SweptSurface] = None
        self._surface: Optional[dict] = None

    def build(self) -> dict:
        """
        构建装饰条扫描曲面

        Returns:
            dict: NURBS 曲面数据
        """
        # 创建 SweptSurface
        self._swept = SweptSurface(
            path_points=self.path_points,
            section_type=self._params['section_type'],
            section_params=self._params['section_params'],
            path_samples=self._params['path_samples'],
            degree_u=self._params['degree_u'],
            degree_v=self._params['degree_v'],
            section_scale=self.section_scale,
        )

        self._surface = self._swept.build()

        # 如果有偏移，沿法线方向偏移控制点
        if self.offset != 0.0:
            T, N, B = self._swept.get_frames()
            cp = self._surface['control_points']
            n_path = cp.shape[0]
            for i in range(n_path):
                cp[i] += self.offset * N[i]

        return self._surface

    def get_surface(self) -> dict:
        """获取已构建的 NURBS 曲面"""
        if self._surface is None:
            self.build()
        return self._surface

    def evaluate(self, u: float, v: float) -> np.ndarray:
        """
        在装饰条曲面上求值

        Args:
            u: 沿路径参数 ∈ [0, 1]
            v: 截面参数 ∈ [0, 1]

        Returns:
            (3,) 曲面上的点
        """
        surf = self.get_surface()
        return evaluate_surface(surf, u, v)

    def to_mesh(
        self,
        n_u: int = 30,
        n_v: int = 12,
        color: Optional[Tuple[int, int, int, int]] = None,
    ) -> 'trimesh.Trimesh':
        """
        转换为 trimesh 网格

        Args:
            n_u: u 方向采样数
            n_v: v 方向采样数
            color: RGBA 颜色（覆盖预设颜色）

        Returns:
            trimesh.Trimesh
        """
        import trimesh

        if self._swept is None:
            self.build()

        use_color = color or self._params.get('color', (180, 180, 180, 255))
        return self._swept.to_mesh(n_u=n_u, n_v=n_v, color=use_color)

    def get_params(self) -> Dict[str, Any]:
        """获取当前参数（预设 + 自定义覆盖后的完整参数）"""
        return dict(self._params)

    @property
    def description(self) -> str:
        """装饰条描述"""
        return self._params.get('description', 'Custom trim strip')


# ============================================================
# 便捷函数
# ============================================================

def create_chrome_trim(
    path_points: np.ndarray,
    offset: float = 0.0,
) -> TrimStrip:
    """
    创建镀铬亮条

    Args:
        path_points: (M, 3) 路径点
        offset: 法线偏移量

    Returns:
        TrimStrip 实例
    """
    return TrimStrip(path_points, preset='chrome_trim', offset=offset)


def create_rubber_seal(
    path_points: np.ndarray,
    offset: float = 0.0,
) -> TrimStrip:
    """
    创建橡胶密封条

    Args:
        path_points: (M, 3) 路径点
        offset: 法线偏移量

    Returns:
        TrimStrip 实例
    """
    return TrimStrip(path_points, preset='rubber_seal', offset=offset)


def create_body_molding(
    path_points: np.ndarray,
    offset: float = 0.0,
) -> TrimStrip:
    """
    创建车身防擦条

    Args:
        path_points: (M, 3) 路径点
        offset: 法线偏移量

    Returns:
        TrimStrip 实例
    """
    return TrimStrip(path_points, preset='body_molding', offset=offset)
