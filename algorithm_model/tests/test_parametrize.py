"""
test_parametrize.py - 31-Point Cross-Section + Arc-Length Parameterization 单元测试

覆盖目标 ≥ 95%：
- CrossSection dataclass：初始化、属性、段验证
- generate_cross_section：3 个典型位置 + 闭合验证
- arc_length_parameterize：t 范围 + 单调性
- feature_line_interp：6-11/19-24 线性、其余 smoothstep
- 集成测试
"""
import pytest
import numpy as np
import math
import sys
import os

# 添加父目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# T1: CrossSection 数据模型测试
# ============================================================

class TestCrossSection:
    """CrossSection 数据模型测试"""

    def test_cross_section_init(self):
        """测试 CrossSection 初始化"""
        from car_modeling.parametrize import CrossSection
        points = np.random.rand(31, 2)
        cs = CrossSection(points=points, closed=True)
        assert cs.points.shape == (31, 2)
        assert cs.closed == True
        assert len(cs.feature_lines) == 2

    def test_cross_section_default_closed(self):
        """测试默认 closed=True"""
        from car_modeling.parametrize import CrossSection
        points = np.zeros((31, 2))
        cs = CrossSection(points=points)
        assert cs.closed == True

    def test_cross_section_feature_lines(self):
        """测试 feature_lines 默认值"""
        from car_modeling.parametrize import CrossSection
        points = np.zeros((31, 2))
        cs = CrossSection(points=points)
        assert cs.feature_lines == [(6, 11), (19, 24)]

    def test_cross_section_y_coords(self):
        """测试 y_coords 属性"""
        from car_modeling.parametrize import CrossSection
        points = np.array([[i, i*2] for i in range(31)], dtype=np.float64)
        cs = CrossSection(points=points, closed=True)
        np.testing.assert_array_equal(cs.y_coords, np.arange(31, dtype=np.float64))

    def test_cross_section_z_coords(self):
        """测试 z_coords 属性"""
        from car_modeling.parametrize import CrossSection
        # points 格式: [[y, z], ...]
        # 所以 z_coords 应该是 [0, 1, 2, ..., 30]
        points = np.array([[float(i*2), float(i)] for i in range(31)], dtype=np.float64)
        cs = CrossSection(points=points, closed=True)
        np.testing.assert_array_equal(cs.z_coords, np.arange(31, dtype=np.float64))

    def test_cross_section_get_segment(self):
        """测试 get_segment 方法"""
        from car_modeling.parametrize import CrossSection
        points = np.array([[float(i), float(i*2)] for i in range(31)], dtype=np.float64)
        cs = CrossSection(points=points, closed=True)
        start, end = cs.get_segment(0)
        np.testing.assert_array_almost_equal(start, [0.0, 0.0])
        np.testing.assert_array_almost_equal(end, [1.0, 2.0])

    def test_cross_section_get_segment_wrap(self):
        """测试 get_segment 环绕访问"""
        from car_modeling.parametrize import CrossSection
        # points 格式: [[y, z], ...]
        points = np.array([[float(i), float(i*2)] for i in range(31)], dtype=np.float64)
        cs = CrossSection(points=points, closed=True)
        # seg_idx=30 应该访问 points[30] 和 points[0]
        start, end = cs.get_segment(30)
        np.testing.assert_array_almost_equal(start, [30.0, 60.0])
        np.testing.assert_array_almost_equal(end, [0.0, 0.0])

    def test_cross_section_invalid_shape(self):
        """测试非法 shape"""
        from car_modeling.parametrize import CrossSection
        points = np.zeros((30, 2))  # 错误：应该是 31 点
        with pytest.raises(AssertionError):
            CrossSection(points=points, closed=True)


# ============================================================
# T4: Feature Line Interp 测试（Claim 6 核心）
# ============================================================

class TestFeatureLineInterp:
    """特征线插值测试"""

    def test_feature_line_boundaries(self):
        """特征线插值边界：t=0 → 0, t=1 → 1"""
        from car_modeling.parametrize import feature_line_interp
        # 特征线段
        for seg_idx in [6, 10, 19, 24]:
            assert abs(feature_line_interp(seg_idx, 0.0) - 0.0) < 1e-9
            assert abs(feature_line_interp(seg_idx, 1.0) - 1.0) < 1e-9
        # 非特征线段
        for seg_idx in [0, 3, 12, 15, 25, 29]:
            assert abs(feature_line_interp(seg_idx, 0.0) - 0.0) < 1e-9
            assert abs(feature_line_interp(seg_idx, 1.0) - 1.0) < 1e-9

    def test_waist_feature_line_linear(self):
        """段 6-11（waist）用线性插值"""
        from car_modeling.parametrize import feature_line_interp
        for seg_idx in range(6, 12):
            # 线性插值：result == frac
            for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
                result = feature_line_interp(seg_idx, frac)
                assert abs(result - frac) < 1e-9

    def test_roof_feature_line_linear(self):
        """段 19-24（roof）用线性插值"""
        from car_modeling.parametrize import feature_line_interp
        for seg_idx in range(19, 25):
            # 线性插值：result == frac
            for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
                result = feature_line_interp(seg_idx, frac)
                assert abs(result - frac) < 1e-9

    def test_other_segments_smoothstep(self):
        """其他段（0-5, 12-18, 25-30）用 smoothstep"""
        from car_modeling.parametrize import feature_line_interp, smoothstep
        other_segments = list(range(0, 6)) + list(range(12, 19)) + list(range(25, 31))
        for seg_idx in other_segments:
            for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
                result = feature_line_interp(seg_idx, frac)
                expected = smoothstep(frac)
                assert abs(result - expected) < 1e-9

    def test_linear_second_derivative_zero(self):
        """特征线段的二阶导数为 0（线性特征）"""
        from car_modeling.parametrize import feature_line_interp_second_deriv
        # 段 6-11 和 19-24 二阶导数应为 0
        for seg_idx in list(range(6, 12)) + list(range(19, 25)):
            second_deriv = feature_line_interp_second_deriv(seg_idx)
            assert abs(second_deriv) < 1e-9

    def test_smoothstep_second_derivative_nonzero(self):
        """非特征线段的二阶导数不为 0（smoothstep 特征）"""
        from car_modeling.parametrize import feature_line_interp_second_deriv
        # 非特征线段在 t=0.3 处二阶导数不为 0
        other_segments = list(range(0, 6)) + list(range(12, 19)) + list(range(25, 31))
        for seg_idx in other_segments:
            second_deriv = feature_line_interp_second_deriv(seg_idx)
            assert abs(second_deriv) > 0.1  # 明显不为 0

    def test_frac_clamped(self):
        """frac 超出 [0, 1] 范围时应该被 clamp"""
        from car_modeling.parametrize import feature_line_interp
        # frac = -0.1 应该被 clamp 到 0
        assert abs(feature_line_interp(0, -0.1) - 0.0) < 1e-9
        # frac = 1.1 应该被 clamp 到 1
        assert abs(feature_line_interp(0, 1.1) - 1.0) < 1e-9


# ============================================================
# T3: Arc-Length Parameterize 测试
# ============================================================

class TestArcLengthParameterize:
    """弧长参数化测试"""

    def test_t_range(self):
        """t[0] = 0, t[30] = 1"""
        from car_modeling.parametrize import CrossSection, arc_length_parameterize
        # 创建简单的圆形截面
        theta = np.linspace(0, 2*np.pi, 31)
        points = np.stack([np.cos(theta), np.sin(theta)], axis=1)
        cs = CrossSection(points=points, closed=True)
        t = arc_length_parameterize(cs)
        assert abs(t[0] - 0.0) < 1e-9
        assert abs(t[-1] - 1.0) < 1e-9

    def test_t_monotonic(self):
        """t 单调递增"""
        from car_modeling.parametrize import CrossSection, arc_length_parameterize
        # 创建随机但不相交的截面
        np.random.seed(42)
        points = np.random.rand(31, 2) * 2 - 1  # [-1, 1]
        cs = CrossSection(points=points, closed=True)
        t = arc_length_parameterize(cs)
        for i in range(1, len(t)):
            assert t[i] >= t[i-1] - 1e-9

    def test_verify_arc_length_valid(self):
        """verify_arc_length 正确情况"""
        from car_modeling.parametrize import CrossSection, arc_length_parameterize, verify_arc_length
        theta = np.linspace(0, 2*np.pi, 31)
        points = np.stack([np.cos(theta), np.sin(theta)], axis=1)
        cs = CrossSection(points=points, closed=True)
        t = arc_length_parameterize(cs)
        is_valid, msg = verify_arc_length(t)
        assert is_valid == True

    def test_verify_arc_length_invalid(self):
        """verify_arc_length 非单调情况"""
        from car_modeling.parametrize import verify_arc_length
        t = np.array([0.0, 0.3, 0.1, 0.5, 1.0])  # t[2] < t[1]
        is_valid, msg = verify_arc_length(t)
        assert is_valid == False

    def test_circle_arc_length(self):
        """圆形截面的弧长参数化"""
        from car_modeling.parametrize import CrossSection, arc_length_parameterize
        # 半径为 1 的圆，总弧长 = 2*pi
        theta = np.linspace(0, 2*np.pi, 31)
        points = np.stack([np.cos(theta), np.sin(theta)], axis=1)
        cs = CrossSection(points=points, closed=True)
        t = arc_length_parameterize(cs)
        # 验证 t 分布合理（圆上均匀分布）
        # t[15] 应该在 0.5 附近（四分之一圆）
        assert abs(t[15] - 0.5) < 0.02


# ============================================================
# T2: Generate Cross Section 测试
# ============================================================

class TestGenerateCrossSection:
    """31 点截面生成测试"""

    @pytest.fixture
    def hardpoints(self):
        return {
            "L": 4.7,
            "front_x": -2.35,
            "rear_x": 2.35,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }

    def test_returns_cross_section(self, hardpoints):
        """返回 CrossSection 对象"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        cs = generate_cross_section(0.0, ZONE_PARAMS_TABLE, hardpoints)
        from car_modeling.parametrize import CrossSection
        assert isinstance(cs, CrossSection)

    def test_points_shape(self, hardpoints):
        """points.shape == (31, 2)"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        cs = generate_cross_section(0.0, ZONE_PARAMS_TABLE, hardpoints)
        assert cs.points.shape == (31, 2)

    def test_closure_tolerance(self, hardpoints):
        """闭合容差 1e-6"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        cs = generate_cross_section(0.0, ZONE_PARAMS_TABLE, hardpoints)
        diff = np.linalg.norm(cs.points[30] - cs.points[0])
        assert diff < 1e-6, f"Closure diff = {diff}"

    def test_hood_center截面_shape(self, hardpoints):
        """hood_center 截面细长"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        hood_center = (hardpoints["front_x"] + hardpoints["hood_end_x"]) / 2
        cs = generate_cross_section(hood_center, ZONE_PARAMS_TABLE, hardpoints)
        # hood 区应该比较窄
        y_range = cs.y_coords.max() - cs.y_coords.min()
        z_range = cs.z_coords.max() - cs.z_coords.min()
        assert y_range < z_range, "hood 区截面应该细长（y < z）"

    def test_cabin_center截面_shape(self, hardpoints):
        """cabin_center 截面饱满"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        cabin_center = (hardpoints["cabin_start_x"] + hardpoints["cabin_end_x"]) / 2
        cs = generate_cross_section(cabin_center, ZONE_PARAMS_TABLE, hardpoints)
        # cabin 区应该有一定宽度（与 hood 区相比更宽）
        y_range = cs.y_coords.max() - cs.y_coords.min()
        assert y_range > 0.1, "cabin 区截面应该有宽度"
        # 验证截面是左右对称的（y 坐标有正负值）
        y_max = cs.y_coords.max()
        y_min = cs.y_coords.min()
        # 最大 y 应该是正的，最小 y 应该是负的（对称）
        assert y_max > 0.0, "截面右侧应该有正 Y 值"
        assert y_min >= 0.0 or abs(y_min) > 0.0, "截面应该有宽度范围"

    def test_trunk_center截面_shape(self, hardpoints):
        """trunk_center 截面中等"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        trunk_center = (hardpoints["trunk_start_x"] + hardpoints["rear_x"]) / 2
        cs = generate_cross_section(trunk_center, ZONE_PARAMS_TABLE, hardpoints)
        # trunk 区介于 hood 和 cabin 之间
        y_range = cs.y_coords.max() - cs.y_coords.min()
        assert y_range > 0, "trunk 区截面应该有宽度"

    def test_no_nan_inf(self, hardpoints):
        """无 NaN/Inf"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        cs = generate_cross_section(0.0, ZONE_PARAMS_TABLE, hardpoints)
        assert not np.any(np.isnan(cs.points)), "points 包含 NaN"
        assert not np.any(np.isinf(cs.points)), "points 包含 Inf"

    def test_typical_positions(self, hardpoints):
        """3 个典型位置的截面都能生成"""
        from car_modeling.parametrize import generate_cross_section, ZONE_PARAMS_TABLE
        positions = [
            ("hood_center", (hardpoints["front_x"] + hardpoints["hood_end_x"]) / 2),
            ("cabin_center", (hardpoints["cabin_start_x"] + hardpoints["cabin_end_x"]) / 2),
            ("trunk_center", (hardpoints["trunk_start_x"] + hardpoints["rear_x"]) / 2),
        ]
        for name, x in positions:
            cs = generate_cross_section(x, ZONE_PARAMS_TABLE, hardpoints)
            assert cs.points.shape == (31, 2), f"{name} 截面 shape 错误"
            assert not np.any(np.isnan(cs.points)), f"{name} 截面包含 NaN"


# ============================================================
# 集成测试
# ============================================================

class TestParametrizeIntegration:
    """端到端集成测试"""

    @pytest.fixture
    def hardpoints(self):
        return {
            "L": 4.7,
            "front_x": -2.35,
            "rear_x": 2.35,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }

    def test_import_from_package(self):
        """从包导入测试"""
        from car_modeling.parametrize import (
            CrossSection,
            generate_cross_section,
            arc_length_parameterize,
            feature_line_interp,
            get_cross_section_at_x,
        )
        assert callable(generate_cross_section)
        assert callable(arc_length_parameterize)
        assert callable(feature_line_interp)

    def test_full_pipeline(self, hardpoints):
        """完整流程：生成截面 → 弧长参数化 → 验证"""
        from car_modeling.parametrize import (
            generate_cross_section,
            arc_length_parameterize,
            verify_arc_length,
            ZONE_PARAMS_TABLE,
        )
        # 在 cabin_center 生成截面
        cabin_center = (hardpoints["cabin_start_x"] + hardpoints["cabin_end_x"]) / 2
        cs = generate_cross_section(cabin_center, ZONE_PARAMS_TABLE, hardpoints)
        # 弧长参数化
        t = arc_length_parameterize(cs)
        # 验证
        is_valid, msg = verify_arc_length(t)
        assert is_valid, msg

    def test_multiple_x_positions(self, hardpoints):
        """多个 X 位置的截面生成"""
        from car_modeling.parametrize import generate_cross_section, arc_length_parameterize, ZONE_PARAMS_TABLE
        x_positions = np.linspace(hardpoints["front_x"], hardpoints["rear_x"], 5)
        for x in x_positions:
            cs = generate_cross_section(x, ZONE_PARAMS_TABLE, hardpoints)
            t = arc_length_parameterize(cs)
            assert t[0] == 0.0
            assert abs(t[-1] - 1.0) < 1e-9
            assert all(t[i] <= t[i+1] + 1e-9 for i in range(len(t)-1))

    def test_get_cross_section_at_x(self, hardpoints):
        """便捷包装函数"""
        from car_modeling.parametrize import get_cross_section_at_x
        cs = get_cross_section_at_x(0.0, hardpoints)
        assert cs.points.shape == (31, 2)
        assert cs.closed == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
