"""
test_performance.py — 性能基准测试

覆盖：
1. NURBS 求值性能（基函数 / 曲线 / 曲面）
2. FreeformDeformation 性能（50 / 5000 / 50000 顶点）
3. 圆角曲面生成性能
4. 扫描曲面性能（100 控制点路径 + 10 截面点）
"""

import time
import numpy as np
import pytest
from algorithm_model.freeform.nurbs_core import (
    find_span,
    basis_funs,
    curve_point,
    surface_point,
    open_uniform_knots,
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
)
from algorithm_model.freeform.freeform_surface import FreeformDeformation
from algorithm_model.freeform.fillet_surface import (
    IntersectionCurve,
    create_fillet_surface,
    surface_to_mesh,
)
from algorithm_model.freeform.swept_surface import (
    SweptSurface,
    FrenetFrame,
    generate_circle_section,
)


# ============================================================
# Helpers
# ============================================================

def _time_it(fn, *args, repeats=5, **kwargs):
    """多次执行取中位数耗时（ms）"""
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(*args, **kwargs)
        times.append((time.perf_counter() - t0) * 1000)
    return float(np.median(times))


# ============================================================
# 1. NURBS 求值性能
# ============================================================

class TestNURBSPerformance:
    """NURBS 核心算法性能基准"""

    @pytest.fixture
    def degree3_setup(self):
        """degree=3, 50 个节点的通用 setup"""
        p = 3
        n = 49  # 50 个控制点
        U = open_uniform_knots(n, p)
        # 随机控制点
        np.random.seed(42)
        P_curve = np.random.randn(n + 1, 3)
        return n, p, U, P_curve

    def test_basis_funs_performance(self, degree3_setup):
        """基函数求值：degree=3, 50 个节点 → 单次 < 1ms"""
        n, p, U, _ = degree3_setup
        u = 0.37

        elapsed = _time_it(lambda: basis_funs(find_span(n, p, u, U), u, p, U))
        print(f"  basis_funs (degree=3, n=49): {elapsed:.4f} ms")
        assert elapsed < 1.0, f"basis_funs too slow: {elapsed:.4f} ms > 1 ms"

    def test_curve_point_performance(self, degree3_setup):
        """曲线求值：100 个采样点 → < 10ms"""
        n, p, U, P_curve = degree3_setup
        u_vals = np.linspace(0, 1, 100)

        def _eval_100():
            for u in u_vals:
                curve_point(n, p, P_curve, U, u)

        elapsed = _time_it(_eval_100)
        print(f"  curve_point x100: {elapsed:.4f} ms")
        assert elapsed < 10.0, f"curve_point x100 too slow: {elapsed:.4f} ms > 10 ms"

    def test_surface_point_performance(self):
        """曲面求值：50×50 网格 → < 200ms（纯 Python 循环实现）"""
        # 创建 6×6 控制点网格的三次曲面
        n_u, n_v = 5, 5
        p, q = 3, 3
        np.random.seed(42)
        control_pts = np.random.randn(n_u + 1, n_v + 1, 3)
        U = open_uniform_knots(n_u, p)
        V = open_uniform_knots(n_v, q)

        def _eval_50x50():
            for u in np.linspace(0, 1, 50):
                for v in np.linspace(0, 1, 50):
                    surface_point(n_u, n_v, p, q, control_pts, U, V, u, v)

        elapsed = _time_it(_eval_50x50)
        print(f"  surface_point 50x50: {elapsed:.4f} ms")
        # 纯 Python 循环逐点求值，基准 ~80-100ms
        assert elapsed < 200.0, f"surface_point 50x50 too slow: {elapsed:.4f} ms > 200 ms"

    def test_evaluate_surface_mesh_performance(self):
        """NURBS 曲面网格求值（evaluate_surface_mesh）：50×50 → < 200ms"""
        np.random.seed(42)
        control_pts = np.random.randn(6, 6, 3)
        surf = nurbs_surface_from_grid(control_pts, degree_u=3, degree_v=3)

        elapsed = _time_it(lambda: evaluate_surface_mesh(surf, 50, 50))
        print(f"  evaluate_surface_mesh 50x50: {elapsed:.4f} ms")
        # 纯 Python 循环逐点求值，基准 ~80-100ms
        assert elapsed < 200.0, f"evaluate_surface_mesh 50x50 too slow: {elapsed:.4f} ms > 200 ms"


# ============================================================
# 2. FreeformDeformation 性能
# ============================================================

class TestFreeformPerformance:
    """自由变形性能基准"""

    def _make_vertices(self, n):
        """生成 n 个模拟车身顶点"""
        np.random.seed(42)
        verts = np.random.randn(n, 3)
        verts[:, 0] *= 2.3  # x: 车长方向
        verts[:, 1] *= 0.9  # y: 车宽方向
        verts[:, 2] = np.abs(verts[:, 2]) * 0.7 + 0.1  # z: 车高方向
        return verts

    def test_ffd_50_vertices(self):
        """FreeformDeformation 50 顶点变形 → < 5ms"""
        ffd = FreeformDeformation()
        ffd.add_deformation('fender_bulge', center_x=1.2, center_z=0.5)
        verts = self._make_vertices(50)

        elapsed = _time_it(lambda: ffd.apply(verts, body_length=4.7, body_height=1.45))
        print(f"  FFD 50 vertices: {elapsed:.4f} ms")
        assert elapsed < 5.0, f"FFD 50 vertices too slow: {elapsed:.4f} ms > 5 ms"

    def test_ffd_5000_vertices(self):
        """FreeformDeformation 5000 顶点变形 → < 50ms"""
        ffd = FreeformDeformation()
        ffd.add_deformation('fender_bulge', center_x=1.2, center_z=0.5)
        verts = self._make_vertices(5000)

        elapsed = _time_it(lambda: ffd.apply(verts, body_length=4.7, body_height=1.45))
        print(f"  FFD 5000 vertices: {elapsed:.4f} ms")
        assert elapsed < 50.0, f"FFD 5000 vertices too slow: {elapsed:.4f} ms > 50 ms"

    def test_ffd_50000_vertices(self):
        """FreeformDeformation 50000 顶点变形 → < 1000ms（逐顶点 NURBS 求值实现）"""
        ffd = FreeformDeformation()
        ffd.add_deformation('fender_bulge', center_x=1.2, center_z=0.5)
        verts = self._make_vertices(50000)

        elapsed = _time_it(lambda: ffd.apply(verts, body_length=4.7, body_height=1.45))
        print(f"  FFD 50000 vertices: {elapsed:.4f} ms")
        # 逐顶点 NURBS 求值 + smoothstep 衰减，基准 ~400-500ms
        assert elapsed < 1000.0, f"FFD 50000 vertices too slow: {elapsed:.4f} ms > 1000 ms"


# ============================================================
# 3. 圆角曲面性能
# ============================================================

class TestFilletPerformance:
    """圆角曲面生成性能"""

    def test_single_fillet_generation(self):
        """单面圆角生成 → < 20ms"""
        # 创建一条沿 x 轴的交线
        line_pts = np.linspace([0, 0, 0], [1, 0, 0], 10)
        intersection = IntersectionCurve(line_pts)

        # 法向量函数
        def normal_a(p):
            return np.array([0.0, 1.0, 0.0])

        def normal_b(p):
            return np.array([0.0, 0.0, 1.0])

        elapsed = _time_it(lambda: create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=20,
            n_arc_points=8,
        ))
        print(f"  single fillet: {elapsed:.4f} ms")
        assert elapsed < 20.0, f"fillet generation too slow: {elapsed:.4f} ms > 20 ms"


# ============================================================
# 4. 扫描曲面性能
# ============================================================

class TestSweptPerformance:
    """扫描曲面性能"""

    def test_swept_surface_100pts_path(self):
        """路径扫描（100 控制点路径 + 10 截面点）→ < 30ms"""
        # 100 个控制点的空间路径（S 形曲线）
        np.random.seed(42)
        t = np.linspace(0, 4 * np.pi, 100)
        path_points = np.column_stack([
            t / (4 * np.pi),                # x: 0 → 1
            0.1 * np.sin(t),                # y: 正弦波动
            0.05 * np.cos(t) + 0.5,        # z: 绕中线波动
        ])

        elapsed = _time_it(lambda: SweptSurface(
            path_points=path_points,
            section_type='circle',
            section_params={'radius': 0.01, 'n_points': 10},
            path_samples=100,
        ).build())
        print(f"  swept surface (100 path + 10 section): {elapsed:.4f} ms")
        assert elapsed < 30.0, f"swept surface too slow: {elapsed:.4f} ms > 30 ms"
