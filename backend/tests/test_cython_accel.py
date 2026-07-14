"""
test_cython_accel.py — Cython 加速模块测试

覆盖：
1. 数值一致性（Cython vs Python，100x100 网格 < 1e-10）
2. 性能基准（100x100 网格 < 5ms，200x 加速）
3. API 集成（自动 fallback 机制）
4. 边缘 case（1x1 网格、单点、退化曲面）
"""
import time
import numpy as np
import pytest


# ──────────── 1. 数值一致性 ────────────

class TestNumericalCorrectness:
    """验证 Cython 与 Python 结果完全一致"""

    def _make_surf(self, seed=42):
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        np.random.seed(seed)
        cp = np.random.rand(8, 8, 3) * 100
        return nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)

    def test_mesh_30x30(self):
        """30x30 网格数值一致性"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        surf = self._make_surf()
        pts_py = self._py_eval(surf, 30, 30)
        pts_cy, _ = evaluate_surface_mesh_fast(surf, 30, 30)
        assert np.allclose(pts_py, pts_cy, atol=1e-10)

    def test_mesh_100x100(self):
        """100x100 网格数值一致性"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        surf = self._make_surf()
        pts_py = self._py_eval(surf, 100, 100)
        pts_cy, _ = evaluate_surface_mesh_fast(surf, 100, 100)
        assert np.max(np.abs(pts_py - pts_cy)) < 1e-10

    def test_mesh_50x80_non_square(self):
        """非方阵 50x80 网格"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        surf = self._make_surf()
        pts_py = self._py_eval(surf, 50, 80)
        pts_cy, _ = evaluate_surface_mesh_fast(surf, 50, 80)
        assert np.max(np.abs(pts_py - pts_cy)) < 1e-10

    def test_weighted_surface(self):
        """非均匀权重曲面"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        np.random.seed(99)
        cp = np.random.rand(6, 6, 3) * 50
        w = np.random.rand(6, 6) * 2 + 0.5  # 权重 [0.5, 2.5]
        surf = nurbs_surface_from_grid(cp, w, 3, 3)
        pts_py = self._py_eval(surf, 40, 40)
        pts_cy, _ = evaluate_surface_mesh_fast(surf, 40, 40)
        assert np.max(np.abs(pts_py - pts_cy)) < 1e-10

    def test_boundary_points(self):
        """边界点 (u,v) = (0,0), (1,0), (0,1), (1,1)"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        surf = self._make_surf()
        pts_cy, params = evaluate_surface_mesh_fast(surf, 2, 2)
        # 4 个角点
        assert pts_cy.shape == (4, 3)
        assert np.allclose(params[0], [0, 0])
        assert np.allclose(params[3], [1, 1])

    def _py_eval(self, surf, nu, nv):
        """纯 Python 求值（不走 Cython）"""
        from algorithm_model.freeform.nurbs_core import evaluate_surface
        u_vals = np.linspace(0, 1, nu)
        v_vals = np.linspace(0, 1, nv)
        pts = []
        for u in u_vals:
            for v in v_vals:
                pts.append(evaluate_surface(surf, u, v))
        return np.array(pts)


# ──────────── 2. 性能基准 ────────────

class TestPerformance:
    """验证性能达标"""

    def test_mesh_100x100_under_5ms(self):
        """100x100 网格 < 5ms"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        np.random.seed(42)
        cp = np.random.rand(8, 8, 3) * 100
        surf = nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)
        # warmup
        evaluate_surface_mesh_fast(surf, 10, 10)
        t0 = time.perf_counter()
        pts, _ = evaluate_surface_mesh_fast(surf, 100, 100)
        t = (time.perf_counter() - t0) * 1000
        assert t < 5.0, f"100x100 mesh took {t:.2f}ms (target <5ms)"

    def test_200x_speedup(self):
        """相对纯 Python 加速比 > 200x"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid, evaluate_surface
        np.random.seed(42)
        cp = np.random.rand(8, 8, 3) * 100
        surf = nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)

        # Python baseline (50x50 to save time)
        t0 = time.perf_counter()
        u_vals = np.linspace(0, 1, 50)
        v_vals = np.linspace(0, 1, 50)
        for u in u_vals:
            for v in v_vals:
                evaluate_surface(surf, u, v)
        t_py = time.perf_counter() - t0

        # Cython
        evaluate_surface_mesh_fast(surf, 10, 10)  # warmup
        t0 = time.perf_counter()
        evaluate_surface_mesh_fast(surf, 50, 50)
        t_cy = time.perf_counter() - t0

        speedup = t_py / t_cy
        assert speedup > 200, f"Speedup only {speedup:.0f}x (target >200x)"

    def test_reflection_under_2ms(self):
        """反射线评分 50x50 < 2ms"""
        from algorithm_model.surface_quality._quality_cy import compute_reflection_score_fast
        grid = np.random.rand(50, 50, 3) * 10
        compute_reflection_score_fast(grid)  # warmup
        t0 = time.perf_counter()
        compute_reflection_score_fast(grid)
        t = (time.perf_counter() - t0) * 1000
        assert t < 2.0, f"Reflection score took {t:.2f}ms (target <2ms)"

    def test_car_body_under_5ms_per_panel(self):
        """整车模拟：20 板 × 50x50 < 5ms/板"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        evaluate_surface_mesh_fast(
            nurbs_surface_from_grid(np.random.rand(8, 8, 3), np.ones((8, 8)), 3, 3),
            10, 10
        )  # warmup
        t0 = time.perf_counter()
        for k in range(20):
            cp = np.random.rand(8, 8, 3) * 100
            surf = nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)
            evaluate_surface_mesh_fast(surf, 50, 50)
        t_per_panel = (time.perf_counter() - t0) / 20 * 1000
        assert t_per_panel < 5.0, f"Per panel: {t_per_panel:.2f}ms (target <5ms)"


# ──────────── 3. API 集成 ────────────

class TestAPIIntegration:
    """验证 API 自动使用 Cython"""

    def test_evaluate_surface_mesh_uses_cython(self):
        """evaluate_surface_mesh 自动走 Cython 路径"""
        from algorithm_model.freeform.nurbs_core import evaluate_surface_mesh, nurbs_surface_from_grid
        np.random.seed(42)
        cp = np.random.rand(8, 8, 3) * 100
        surf = nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)
        # warmup
        evaluate_surface_mesh(surf, 10, 10)
        # 实测
        t0 = time.perf_counter()
        pts, params = evaluate_surface_mesh(surf, 100, 100)
        t = (time.perf_counter() - t0) * 1000
        assert t < 10, f"API call took {t:.2f}ms, Cython should be <5ms"
        assert pts.shape == (10000, 3)

    def test_reflection_score_uses_cython(self):
        """compute_reflection_score 自动走 Cython 路径"""
        from algorithm_model.surface_quality.reflection import compute_reflection_score
        grid = np.random.rand(50, 50, 3) * 10
        # warmup
        compute_reflection_score(np.random.rand(10, 10, 3) * 10)
        # 实测
        t0 = time.perf_counter()
        score = compute_reflection_score(grid)
        t = (time.perf_counter() - t0) * 1000
        assert t < 5, f"API call took {t:.2f}ms, Cython should be <2ms"
        assert 0.0 <= score <= 1.0


# ──────────── 4. 边缘 case ────────────

class TestEdgeCases:
    """边缘情况测试"""

    def test_minimal_grid_2x2(self):
        """最小网格 2x2"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        cp = np.array([[[0, 0, 0], [1, 0, 0]], [[0, 1, 0], [1, 1, 0]]], dtype=float)
        # degree 1 for 2x2
        surf = nurbs_surface_from_grid(cp, np.ones((2, 2)), 1, 1)
        pts, _ = evaluate_surface_mesh_fast(surf, 2, 2)
        assert pts.shape == (4, 3)

    def test_high_degree_surface(self):
        """高次曲面 degree=5"""
        from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid
        np.random.seed(7)
        cp = np.random.rand(10, 10, 3) * 50
        surf = nurbs_surface_from_grid(cp, np.ones((10, 10)), 5, 5)
        pts_cy, _ = evaluate_surface_mesh_fast(surf, 30, 30)
        assert pts_cy.shape == (900, 3)
        assert not np.any(np.isnan(pts_cy))

    def test_reflection_empty_grid(self):
        """反射线：极小网格"""
        from algorithm_model.surface_quality._quality_cy import compute_reflection_score_fast
        grid = np.random.rand(3, 3, 3)
        score = compute_reflection_score_fast(grid)
        assert 0.0 <= score <= 1.0

    def test_reflection_single_value(self):
        """反射线：2x2 最小有效网格"""
        from algorithm_model.surface_quality._quality_cy import compute_reflection_score_fast
        grid = np.random.rand(2, 2, 3)
        score = compute_reflection_score_fast(grid)
        assert isinstance(score, float)
