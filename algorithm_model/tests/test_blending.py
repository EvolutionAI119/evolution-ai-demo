"""
test_blending.py - Three-Zone Blending + Tumblehome 单元测试

覆盖目标 ≥ 95%：
- F4 公式：3 个归一化用例
- F5 公式：3 个 tumblehome 用例
- ZoneParamsTable：dataclass 初始化验证
- three_zone_weights：边界用例
- normalize_zone_weights：边界用例 + sum=1.0 验证
"""
import pytest
import math
import sys
import os

# 添加父目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# T1: ZoneParamsTable 数据结构测试
# ============================================================

class TestZoneParamsTable:
    """ZoneParamsTable 数据结构测试"""

    def test_zone_level_initialization(self):
        """测试 ZoneLevel dataclass 初始化"""
        from car_modeling.blending import ZoneLevel
        level = ZoneLevel(x_offset=0.5, y_scale=0.85, z_scale=0.95)
        assert level.x_offset == 0.5
        assert level.y_scale == 0.85
        assert level.z_scale == 0.95

    def test_zone_params_table_15_cells(self):
        """测试 ZONE_PARAMS_TABLE 15 格全部填满"""
        from car_modeling.blending import ZONE_PARAMS_TABLE
        assert len(ZONE_PARAMS_TABLE.hood) == 5
        assert len(ZONE_PARAMS_TABLE.cabin) == 5
        assert len(ZONE_PARAMS_TABLE.trunk) == 5

    def test_zone_params_table_get_level(self):
        """测试 get_level 方法"""
        from car_modeling.blending import ZONE_PARAMS_TABLE
        level = ZONE_PARAMS_TABLE.get_level("cabin", 4)
        assert level.x_offset == 0.85
        assert level.y_scale == 0.72
        assert level.z_scale == 1.00

    def test_zone_params_table_values(self):
        """测试参数表数值合理性"""
        from car_modeling.blending import ZONE_PARAMS_TABLE
        for zone_name in ["hood", "cabin", "trunk"]:
            for level in getattr(ZONE_PARAMS_TABLE, zone_name):
                assert 0.0 <= level.x_offset <= 1.0
                assert 0.0 <= level.y_scale <= 1.0
                assert 0.0 <= level.z_scale <= 1.0


# ============================================================
# T2: Smoothstep 插值测试
# ============================================================

class TestSmoothstep:
    """Smoothstep 插值函数测试"""

    def test_boundaries(self):
        """边界测试：t=0 → 0, t=1 → 1"""
        from car_modeling.blending import smoothstep
        assert abs(smoothstep(0.0) - 0.0) < 1e-9
        assert abs(smoothstep(1.0) - 1.0) < 1e-9

    def test_midpoint(self):
        """中点测试：t=0.5 → 0.5"""
        from car_modeling.blending import smoothstep
        assert abs(smoothstep(0.5) - 0.5) < 1e-9

    def test_monotonic(self):
        """单调性测试"""
        from car_modeling.blending import smoothstep
        prev = 0.0
        for t in [i/100 for i in range(101)]:
            curr = smoothstep(t)
            assert curr >= prev - 1e-9
            prev = curr

    def test_derivatives(self):
        """导数测试：t=0 和 t=1 处导数为 0（G1 连续）"""
        from car_modeling.blending import smoothstep
        h = 1e-6
        deriv_at_0 = (smoothstep(h) - smoothstep(0)) / h
        assert abs(deriv_at_0) < 1e-3
        deriv_at_1 = (smoothstep(1) - smoothstep(1 - h)) / h
        assert abs(deriv_at_1) < 1e-3


# ============================================================
# T3: F4 Product-based 归一化测试
# ============================================================

class TestNormalizeZoneWeights:
    """F4 归一化公式测试（Claim 4 核心）"""

    def test_sum_equals_one(self):
        """核心测试：归一化后 sum=1.0（容差 1e-9）"""
        from car_modeling.blending import normalize_zone_weights
        test_cases = [
            (1.0, 1.0, 1.0),
            (0.5, 0.5, 0.5),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.3, 0.6, 0.1),
        ]
        for hoodF, cabinF, trunkF in test_cases:
            h, c, t = normalize_zone_weights(hoodF, cabinF, trunkF)
            total = h + c + t
            assert abs(total - 1.0) < 1e-9

    def test_equal_weights(self):
        """等权重测试"""
        from car_modeling.blending import normalize_zone_weights
        h, c, t = normalize_zone_weights(1.0, 1.0, 1.0)
        assert abs(h - 1.0/3.0) < 1e-9
        assert abs(c - 1.0/3.0) < 1e-9
        assert abs(t - 1.0/3.0) < 1e-9

    def test_one_zero_weight(self):
        """一个权重为 0 时，另外两个等权重分配"""
        from car_modeling.blending import normalize_zone_weights
        h, c, t = normalize_zone_weights(0.0, 1.0, 1.0)
        assert abs(h - 0.0) < 1e-9
        assert abs(c - 0.5) < 1e-9
        assert abs(t - 0.5) < 1e-9

    def test_two_zero_weights(self):
        """两个权重为 0 时均匀分配"""
        from car_modeling.blending import normalize_zone_weights
        h, c, t = normalize_zone_weights(1.0, 0.0, 0.0)
        assert abs(h - 1.0/3.0) < 1e-9

    def test_product_fallback_edge_case(self):
        """product-based 归一化在 total_prod 极小时的 fallback"""
        from car_modeling.blending import normalize_zone_weights
        # 当三个权重都非常小但都不是零时，total_prod 会极小
        # 触发 product-based 的 total_prod < 1e-12 fallback
        h, c, t = normalize_zone_weights(1e-7, 1e-7, 1e-7)
        # 应该使用简单求和归一化
        total = h + c + t
        assert abs(total - 1.0) < 1e-9

    def test_all_zero_weights(self):
        """全为零时安全降级"""
        from car_modeling.blending import normalize_zone_weights
        h, c, t = normalize_zone_weights(0.0, 0.0, 0.0)
        assert abs(h - 1.0/3.0) < 1e-9


# ============================================================
# T4: F5 Tumblehome 测试
# ============================================================

class TestComputeTumblehome:
    """F5 Tumblehome 效应测试（Claim 5）"""

    def test_normal_case(self):
        """正常情况测试"""
        from car_modeling.blending import compute_tumblehome
        hw = 1.0
        shoulderW = 1.0
        CA = math.pi / 6
        result = compute_tumblehome(hw, shoulderW, CA)
        expected_factor = 1.0 * 0.45 - math.sin(math.pi / 6) * 0.15
        expected = hw * expected_factor
        assert abs(result - expected) < 1e-9

    def test_ca_pi_half_safety_floor(self):
        """CA = π/2 安全降级到 0.25 下限"""
        from car_modeling.blending import compute_tumblehome
        hw = 1.0
        shoulderW = 1.0
        CA = math.pi / 2
        result = compute_tumblehome(hw, shoulderW, CA)
        expected = hw * max(0.25, 0.45 - 1.0 * 0.15)
        assert abs(result - expected) < 1e-9

    def test_ca_zero_max_width(self):
        """CA = 0 时返回最大宽度"""
        from car_modeling.blending import compute_tumblehome
        hw = 1.0
        shoulderW = 1.0
        CA = 0.0
        result = compute_tumblehome(hw, shoulderW, CA)
        expected = hw * 0.45
        assert abs(result - expected) < 1e-9

    def test_minimum_factor_025(self):
        """下限保护：factor 最小为 0.25"""
        from car_modeling.blending import compute_tumblehome
        hw = 1.0
        shoulderW = 0.3
        CA = math.pi / 2
        result = compute_tumblehome(hw, shoulderW, CA)
        assert abs(result - hw * 0.25) < 1e-9

    def test_tumblehome_scales_with_hw(self):
        """Tumblehome 与原始半宽成正比"""
        from car_modeling.blending import compute_tumblehome
        for hw in [0.5, 1.0, 1.5, 2.0]:
            result = compute_tumblehome(hw, 1.0, 0.0)
            assert abs(result - hw * 0.45) < 1e-9

    def test_shoulder_wide_factor(self):
        """肩部越宽，factor 越大"""
        from car_modeling.blending import compute_tumblehome
        CA = 0.0
        r1 = compute_tumblehome(1.0, 0.5, CA)
        r2 = compute_tumblehome(1.0, 1.0, CA)
        assert r2 > r1


# ============================================================
# Three Zone Weights 测试
# ============================================================

class TestThreeZoneWeights:
    """三区段权重计算测试"""

    @pytest.fixture
    def hardpoints(self):
        return {
            "L": 4.7,
            "front_x": -2.35,
            "rear_x": 3.1,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }

    def test_weights_non_negative(self, hardpoints):
        """权重非负"""
        from car_modeling.blending import three_zone_weights
        for x in [-2.5, -1.5, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5]:
            h, c, t = three_zone_weights(x, hardpoints)
            assert h >= 0
            assert c >= 0
            assert t >= 0

    def test_at_least_one_positive(self, hardpoints):
        """每个位置至少一个权重 > 0"""
        from car_modeling.blending import three_zone_weights
        for x in [-2.5, -1.5, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5]:
            h, c, t = three_zone_weights(x, hardpoints)
            assert max(h, c, t) > 0

    def test_hood_center_high(self, hardpoints):
        """在 hood 中心附近，hoodF 较大"""
        from car_modeling.blending import three_zone_weights
        hood_center = (-2.35 + (-1.0)) / 2
        h, c, t = three_zone_weights(hood_center, hardpoints)
        assert h >= c

    def test_cabin_center_high(self, hardpoints):
        """在 cabin 中心，cabinF 最大"""
        from car_modeling.blending import three_zone_weights
        cabin_center = (0.2 + 2.4) / 2
        h, c, t = three_zone_weights(cabin_center, hardpoints)
        assert c > h
        assert c > t

    def test_trunk_dominant_zone(self, hardpoints):
        """在 trunk 主导区（x > trunk_start_x），trunkF = 1.0"""
        from car_modeling.blending import three_zone_weights
        # x = 3.0 明显在 trunk 主导区
        h, c, t = three_zone_weights(3.0, hardpoints)
        assert abs(t - 1.0) < 1e-9  # trunkF 应该是 1.0
        assert c == 0.0  # cabinF 应该是 0（过渡结束）
        assert h == 0.0  # hoodF 应该是 0（过渡结束）


# ============================================================
# Get Zone 测试
# ============================================================

class TestGetZone:
    """区段判定测试"""

    @pytest.fixture
    def hardpoints(self):
        return {
            "L": 4.7,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }

    def test_hood_zone(self, hardpoints):
        """hood 区段判定"""
        from car_modeling.blending import get_zone
        for x in [-2.5, -2.0, -1.5, -1.0, 0.0]:
            assert get_zone(x, hardpoints) == "hood"

    def test_cabin_zone(self, hardpoints):
        """cabin 区段判定"""
        from car_modeling.blending import get_zone
        for x in [0.2, 0.5, 1.0, 1.5, 2.0, 2.4]:
            assert get_zone(x, hardpoints) == "cabin"

    def test_trunk_zone(self, hardpoints):
        """trunk 区段判定"""
        from car_modeling.blending import get_zone
        for x in [2.6, 2.8, 3.0, 3.5]:
            assert get_zone(x, hardpoints) == "trunk"


# ============================================================
# Get Blended Params 测试
# ============================================================

class TestGetBlendedParams:
    """混合参数计算测试"""

    @pytest.fixture
    def hardpoints(self):
        return {
            "L": 4.7,
            "front_x": -2.35,
            "rear_x": 3.1,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }

    def test_returns_tuple(self, hardpoints):
        """返回 4 元组"""
        from car_modeling.blending import get_blended_params, ZoneLevel
        result = get_blended_params(0.0, hardpoints)
        assert len(result) == 4
        assert isinstance(result[0], ZoneLevel)

    def test_weights_sum_one(self, hardpoints):
        """归一化权重 sum=1"""
        from car_modeling.blending import get_blended_params
        for x in [-2.5, -1.0, 0.0, 1.0, 2.0, 2.5]:
            _, h, c, t = get_blended_params(x, hardpoints)
            assert abs(h + c + t - 1.0) < 1e-9


# ============================================================
# 集成测试
# ============================================================

class TestBlendingIntegration:
    """端到端集成测试"""

    def test_import_from_package(self):
        """从包导入测试"""
        from car_modeling.blending import (
            smoothstep, three_zone_weights, normalize_zone_weights,
            compute_tumblehome, ZONE_PARAMS_TABLE, ZoneLevel, ZoneParamsTable,
            get_zone, get_blended_params,
        )
        assert callable(smoothstep)
        assert callable(three_zone_weights)
        assert callable(normalize_zone_weights)
        assert callable(compute_tumblehome)
        assert isinstance(ZONE_PARAMS_TABLE, ZoneParamsTable)

    def test_full_pipeline(self):
        """完整流程测试"""
        from car_modeling.blending import (
            three_zone_weights, normalize_zone_weights, compute_tumblehome,
        )
        hardpoints = {
            "L": 4.7,
            "front_x": -2.35,
            "rear_x": 3.1,
            "hood_end_x": -1.0,
            "cabin_start_x": 0.2,
            "cabin_end_x": 2.4,
            "trunk_start_x": 2.6,
        }
        h, c, t = three_zone_weights(0.0, hardpoints)
        h_n, c_n, t_n = normalize_zone_weights(h, c, t)
        roof_hw = compute_tumblehome(0.8, 1.0, math.pi / 6)
        assert abs(h_n + c_n + t_n - 1.0) < 1e-9
        assert roof_hw > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
