"""
test_swept.py — SweptSurface + TrimStrip 单元测试

覆盖：
1. Frenet 标架正交性验证（T·N=0, T·B=0, N·B=0）
2. Frenet 标架单位化（|T|=|N|=|B|=1）
3. 直线路径扫描不扭曲
4. 圆弧路径扫描闭合性
5. 矩形截面四角位置正确
6. 可变截面扫描（半径渐变）
7. 退化情况处理（零曲率、共线路径点）
8. TrimStrip 预设参数验证
9. 截面生成函数测试
10. 扫描曲面求值与网格化
"""

import numpy as np
import pytest
import trimesh

from algorithm_model.freeform.swept_surface import (
    SweptSurface,
    FrenetFrame,
    generate_circle_section,
    generate_rectangle_section,
)
from algorithm_model.car_modeling.trim import (
    TrimStrip,
    TRIM_PRESETS,
    create_chrome_trim,
    create_rubber_seal,
    create_body_molding,
    _generate_d_section,
)


# ============================================================
# Helper: 正交性误差 < 1e-10
# ============================================================

def _assert_orthogonal(v1, v2, tol=1e-10):
    """断言两个向量正交"""
    dot = np.dot(v1, v2)
    assert abs(dot) < tol, f"Vectors not orthogonal: dot={dot}, tol={tol}"


def _assert_unit(v, tol=1e-10):
    """断言向量单位化"""
    norm = np.linalg.norm(v)
    assert abs(norm - 1.0) < tol, f"Vector not unit: |v|={norm}, tol={tol}"


# ============================================================
# Test 1: Frenet 标架正交性 — 直线路径
# ============================================================

class TestFrenetOrthogonality:
    """Frenet 标架在路径每点正交"""

    def test_straight_line_orthogonal(self):
        """直线路径：T·N=0, T·B=0, N·B=0"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]])
        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(len(path)):
            _assert_orthogonal(T[i], N[i])
            _assert_orthogonal(T[i], B[i])
            _assert_orthogonal(N[i], B[i])

    def test_circular_arc_orthogonal(self):
        """圆弧路径：T·N=0, T·B=0, N·B=0"""
        n = 50
        angles = np.linspace(0, np.pi / 2, n)
        path = np.stack([
            np.cos(angles),
            np.sin(angles),
            np.zeros(n)
        ], axis=1)

        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(n):
            _assert_orthogonal(T[i], N[i])
            _assert_orthogonal(T[i], B[i])
            _assert_orthogonal(N[i], B[i])

    def test_3d_curve_orthogonal(self):
        """3D 空间曲线（螺旋线）：T·N=0, T·B=0, N·B=0"""
        n = 100
        t = np.linspace(0, 4 * np.pi, n)
        path = np.stack([
            np.cos(t),
            np.sin(t),
            t / (4 * np.pi),  # z 方向线性增加
        ], axis=1)

        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(n):
            _assert_orthogonal(T[i], N[i])
            _assert_orthogonal(T[i], B[i])
            _assert_orthogonal(N[i], B[i])

    def test_frame_unit_vectors(self):
        """Frenet 标架所有向量应为单位向量"""
        path = np.array([
            [0, 0, 0], [1, 0.1, 0], [2, 0.3, 0.1],
            [3, 0.2, 0.3], [4, 0, 0.4]
        ])
        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(len(path)):
            _assert_unit(T[i])
            _assert_unit(N[i])
            _assert_unit(B[i])

    def test_right_handed(self):
        """Frenet 标架应为右手系：T × N = B"""
        path = np.array([
            [0, 0, 0], [1, 0.1, 0], [2, 0.3, 0.1],
            [3, 0.2, 0.3], [4, 0, 0.4]
        ])
        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(len(path)):
            cross = np.cross(T[i], N[i])
            cross = cross / np.linalg.norm(cross)
            # B 应与 T×N 同向
            dot = np.dot(cross, B[i])
            assert dot > 0.9, f"Frame not right-handed at i={i}: dot={dot}"


# ============================================================
# Test 2: 直线路径扫描不扭曲
# ============================================================

class TestStraightPathNoTwist:
    """直线路径扫描：截面不发生扭曲"""

    def test_straight_pipe_consistent_normal(self):
        """直管道：所有路径点的法向量方向一致"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]])
        T, N, B = FrenetFrame.compute_frames(path)

        # 所有 N 应近似相同方向
        for i in range(1, len(path)):
            dot_n = np.dot(N[i], N[0])
            dot_b = np.dot(B[i], B[0])
            assert abs(dot_n - 1.0) < 1e-6, f"N twisted at i={i}: dot={dot_n}"
            assert abs(dot_b - 1.0) < 1e-6, f"B twisted at i={i}: dot={dot_b}"

    def test_straight_swept_circular_section(self):
        """直线路径 + 圆形截面：所有截面在同一平面"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.1, 'n_points': 12},
            path_samples=10,
        )
        surf = swept.build()
        cp = surf['control_points']

        # 检查：所有截面点的 x 坐标应与路径点的 x 坐标一致
        sampled_path = swept.get_sampled_path()
        for i in range(len(sampled_path)):
            # 所有截面点的 y 和 z 应在一个圆上
            for j in range(cp.shape[1]):
                y_local = cp[i, j, 1] - sampled_path[i, 1]
                z_local = cp[i, j, 2] - sampled_path[i, 2]
                dist = np.sqrt(y_local**2 + z_local**2)
                assert abs(dist - 0.1) < 0.01, f"Section point not on circle: dist={dist}"


# ============================================================
# Test 3: 圆弧路径扫描
# ============================================================

class TestCircularArcSwept:
    """圆弧路径扫描"""

    def test_arc_swept_shape(self):
        """圆弧路径 + 圆形截面：生成有效曲面"""
        n = 30
        angles = np.linspace(0, np.pi / 2, n)
        path = np.stack([
            np.cos(angles),
            np.sin(angles),
            np.zeros(n)
        ], axis=1)

        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 12},
            path_samples=20,
        )
        surf = swept.build()

        assert 'control_points' in surf
        assert surf['control_points'].shape[0] == 20
        assert surf['control_points'].shape[2] == 3

    def test_arc_swept_surface_evaluable(self):
        """圆弧路径扫描曲面可在内部求值"""
        n = 30
        angles = np.linspace(0, np.pi / 2, n)
        path = np.stack([
            np.cos(angles),
            np.sin(angles),
            np.zeros(n)
        ], axis=1)

        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=10,
        )
        swept.build()

        # 在几个参数点求值
        for u in [0.0, 0.25, 0.5, 0.75, 1.0]:
            for v in [0.0, 0.5, 1.0]:
                pt = swept.evaluate(u, v)
                assert pt.shape == (3,)
                assert np.all(np.isfinite(pt))


# ============================================================
# Test 4: 矩形截面四角位置正确
# ============================================================

class TestRectangleSection:
    """矩形截面测试"""

    def test_rectangle_section_corners(self):
        """矩形截面四角位置正确"""
        width = 0.02
        height = 0.01
        section = generate_rectangle_section(width, height, n_per_side=2)

        # n_per_side=2 → 8 个点
        assert section.shape == (8, 2)

        # 检查四角存在
        hw = width / 2
        hh = height / 2

        # 四角应在 (±hw, -hh), (hw, ±hh), (±hw, hh), (-hw, ±hh)
        corners = [
            (-hw, -hh), (hw, -hh),
            (hw, hh), (-hw, hh),
        ]
        for cx, cy in corners:
            # 检查是否有截面点接近此角
            dists = np.sqrt((section[:, 0] - cx)**2 + (section[:, 1] - cy)**2)
            assert np.min(dists) < 1e-10, f"Corner ({cx}, {cy}) not found in section"

    def test_rectangle_swept_dimensions(self):
        """矩形截面扫描：控制点尺寸正确"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        width = 0.02
        height = 0.01

        swept = SweptSurface(
            path_points=path,
            section_type='rectangle',
            section_params={'width': width, 'height': height, 'n_per_side': 2},
            path_samples=5,
        )
        surf = swept.build()
        cp = surf['control_points']

        # 4 * n_per_side = 8 截面点
        assert cp.shape[1] == 8

    def test_rectangle_swept_straight_path(self):
        """直线路径 + 矩形截面：角点偏移正确"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        width = 0.02
        height = 0.01

        swept = SweptSurface(
            path_points=path,
            section_type='rectangle',
            section_params={'width': width, 'height': height, 'n_per_side': 2},
            path_samples=5,
        )
        surf = swept.build()
        cp = surf['control_points']
        sampled_path = swept.get_sampled_path()

        # 在直线路径上，截面应在 yz 平面内
        # 检查中点路径处的截面
        mid = 2  # 中间路径点
        for j in range(cp.shape[1]):
            y_local = cp[mid, j, 1] - sampled_path[mid, 1]
            z_local = cp[mid, j, 2] - sampled_path[mid, 2]
            # 点应在矩形上
            assert abs(y_local) <= width / 2 + 1e-10, f"y_local={y_local} exceeds width/2"
            assert abs(z_local) <= height / 2 + 1e-10, f"z_local={z_local} exceeds height/2"


# ============================================================
# Test 5: 可变截面扫描
# ============================================================

class TestVariableSection:
    """可变截面扫描测试"""

    def test_tapered_pipe(self):
        """锥形管道：半径从 0.1 渐变到 0.05"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])

        def scale_fn(t):
            return 1.0 - 0.5 * t  # 从 1.0 缩小到 0.5

        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.1, 'n_points': 12},
            path_samples=10,
            section_scale=scale_fn,
        )
        surf = swept.build()
        cp = surf['control_points']
        sampled_path = swept.get_sampled_path()

        # 起始截面半径 ≈ 0.1, 末尾截面半径 ≈ 0.05
        # 检查起始截面
        start_dists = []
        for j in range(cp.shape[1]):
            d = np.linalg.norm(cp[0, j] - sampled_path[0])
            start_dists.append(d)
        avg_start = np.mean(start_dists)

        # 检查末尾截面
        end_dists = []
        for j in range(cp.shape[1]):
            d = np.linalg.norm(cp[-1, j] - sampled_path[-1])
            end_dists.append(d)
        avg_end = np.mean(end_dists)

        # 起始半径应约为末尾半径的 2 倍
        assert avg_start > avg_end, f"Start radius {avg_start} should be > end radius {avg_end}"

    def test_bulged_pipe(self):
        """鼓形管道：中间粗两端细"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]])

        def scale_fn(t):
            return 1.0 + 0.5 * np.sin(np.pi * t)  # 中间膨胀

        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 12},
            path_samples=15,
            section_scale=scale_fn,
        )
        surf = swept.build()
        cp = surf['control_points']
        sampled_path = swept.get_sampled_path()

        # 中间截面的偏移量应大于两端
        mid = len(sampled_path) // 2
        mid_dist = np.mean([np.linalg.norm(cp[mid, j] - sampled_path[mid]) for j in range(cp.shape[1])])
        start_dist = np.mean([np.linalg.norm(cp[0, j] - sampled_path[0]) for j in range(cp.shape[1])])
        end_dist = np.mean([np.linalg.norm(cp[-1, j] - sampled_path[-1]) for j in range(cp.shape[1])])

        assert mid_dist > start_dist, "Mid section should be wider than start"
        assert mid_dist > end_dist, "Mid section should be wider than end"


# ============================================================
# Test 6: 退化情况处理
# ============================================================

class TestDegenerateCases:
    """退化情况测试"""

    def test_collinear_path_points(self):
        """共线路径点：标架不应退化"""
        # 所有点在 x 轴上
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0], [4, 0, 0]])
        T, N, B = FrenetFrame.compute_frames(path)

        # 切线应沿 x 方向
        for i in range(len(path)):
            assert abs(T[i, 0] - 1.0) < 1e-10, f"T not along x at i={i}"
            # 法线和副法线应正交
            _assert_orthogonal(T[i], N[i])
            _assert_orthogonal(T[i], B[i])

    def test_two_point_path(self):
        """只有两个路径点：应正常构建"""
        path = np.array([[0, 0, 0], [1, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=10,
        )
        surf = swept.build()
        assert surf is not None

    def test_near_collinear_path(self):
        """近似共线路径点：标架应稳定"""
        path = np.array([
            [0, 0, 0],
            [1, 1e-8, 0],
            [2, 2e-8, 0],
            [3, 1e-8, 0],
        ])
        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(len(path)):
            _assert_unit(T[i], tol=1e-6)
            _assert_unit(N[i], tol=1e-6)
            _assert_unit(B[i], tol=1e-6)

    def test_sharp_corner_path(self):
        """急转弯路径：标架仍正交"""
        path = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [1, 1, 1],
        ])
        T, N, B = FrenetFrame.compute_frames(path)

        for i in range(len(path)):
            _assert_orthogonal(T[i], N[i])
            _assert_orthogonal(T[i], B[i])
            _assert_orthogonal(N[i], B[i])


# ============================================================
# Test 7: 截面生成函数
# ============================================================

class TestSectionGeneration:
    """截面生成函数测试"""

    def test_circle_section_num_points(self):
        """圆形截面点数正确"""
        for n in [3, 8, 16, 32]:
            section = generate_circle_section(0.1, n)
            assert section.shape == (n, 2)

    def test_circle_section_on_circle(self):
        """圆形截面所有点在圆上"""
        radius = 0.05
        n = 16
        section = generate_circle_section(radius, n)

        for j in range(n):
            dist = np.sqrt(section[j, 0]**2 + section[j, 1]**2)
            assert abs(dist - radius) < 1e-10, f"Point {j} not on circle: dist={dist}"

    def test_circle_section_center(self):
        """圆形截面中心在原点"""
        section = generate_circle_section(0.1, 16)
        center = np.mean(section, axis=0)
        assert np.linalg.norm(center) < 1e-10

    def test_rectangle_section_shape(self):
        """矩形截面形状正确"""
        section = generate_rectangle_section(0.02, 0.01, n_per_side=4)
        assert section.shape == (16, 2)  # 4 sides × 4 points

    def test_d_section_shape(self):
        """D 形截面形状正确"""
        section = _generate_d_section()
        assert section.shape[0] >= 3
        assert section.shape[1] == 2

    def test_d_section_has_flat_bottom(self):
        """D 形截面有平底"""
        section = _generate_d_section(base_width=0.012, total_height=0.008)
        # 底部点 y=0
        bottom_points = section[section[:, 1] < 1e-6]
        assert len(bottom_points) >= 2, "D section should have flat bottom"

    def test_custom_section(self):
        """自定义截面"""
        custom_pts = np.array([[0, 0], [0.01, 0], [0.01, 0.005], [0, 0.005]])
        swept = SweptSurface(
            path_points=np.array([[0, 0, 0], [1, 0, 0]]),
            section_type='custom',
            section_params={'points': custom_pts},
            path_samples=5,
        )
        surf = swept.build()
        assert surf['control_points'].shape[1] == 4


# ============================================================
# Test 8: TrimStrip 预设参数验证
# ============================================================

class TestTrimStripPresets:
    """TrimStrip 预设参数验证"""

    def test_all_presets_exist(self):
        """所有预设应存在"""
        expected = ['chrome_trim', 'rubber_seal', 'body_molding']
        for preset in expected:
            assert preset in TRIM_PRESETS, f"Missing preset: {preset}"

    def test_chrome_trim_dimensions(self):
        """镀铬亮条：窄宽薄高"""
        preset = TRIM_PRESETS['chrome_trim']
        assert preset['section_params']['width'] == 0.015
        assert preset['section_params']['height'] == 0.004
        assert preset['section_type'] == 'rectangle'

    def test_rubber_seal_custom_section(self):
        """橡胶密封条：D 形截面"""
        preset = TRIM_PRESETS['rubber_seal']
        assert preset['section_type'] == 'custom'

    def test_body_molding_wider(self):
        """车身防擦条：比镀铬亮条更宽"""
        molding_w = TRIM_PRESETS['body_molding']['section_params']['width']
        chrome_w = TRIM_PRESETS['chrome_trim']['section_params']['width']
        assert molding_w > chrome_w

    def test_chrome_trim_build(self):
        """镀铬亮条可构建"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(path, preset='chrome_trim')
        surf = trim.build()
        assert 'control_points' in surf

    def test_rubber_seal_build(self):
        """橡胶密封条可构建"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(path, preset='rubber_seal')
        surf = trim.build()
        assert 'control_points' in surf

    def test_body_molding_build(self):
        """车身防擦条可构建"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(path, preset='body_molding')
        surf = trim.build()
        assert 'control_points' in surf

    def test_invalid_preset_raises(self):
        """无效预设应抛出错误"""
        path = np.array([[0, 0, 0], [1, 0, 0]])
        with pytest.raises(AssertionError):
            TrimStrip(path, preset='nonexistent_preset')

    def test_custom_params_override(self):
        """自定义参数覆盖预设"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(
            path, preset='chrome_trim',
            custom_params={'path_samples': 15}
        )
        params = trim.get_params()
        assert params['path_samples'] == 15  # 覆盖了预设的 30

    def test_no_preset_default(self):
        """无预设时使用默认参数"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(path)
        surf = trim.build()
        assert 'control_points' in surf

    def test_trim_with_offset(self):
        """偏移后的装饰条"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim_no_offset = TrimStrip(path, preset='chrome_trim')
        trim_with_offset = TrimStrip(path, preset='chrome_trim', offset=0.01)

        surf_no = trim_no_offset.build()
        surf_yes = trim_with_offset.build()

        cp_no = surf_no['control_points']
        cp_yes = surf_yes['control_points']

        # 有偏移的控制点应与无偏移的不同
        assert not np.allclose(cp_no, cp_yes)

    def test_trim_description(self):
        """装饰条描述正确"""
        path = np.array([[0, 0, 0], [1, 0, 0]])
        trim = TrimStrip(path, preset='chrome_trim')
        assert '镀铬' in trim.description or 'chrome' in trim.description.lower()


# ============================================================
# Test 9: 便捷函数
# ============================================================

class TestConvenienceFunctions:
    """便捷创建函数测试"""

    def test_create_chrome_trim(self):
        """create_chrome_trim 便捷函数"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = create_chrome_trim(path)
        assert isinstance(trim, TrimStrip)
        surf = trim.build()
        assert 'control_points' in surf

    def test_create_rubber_seal(self):
        """create_rubber_seal 便捷函数"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = create_rubber_seal(path)
        surf = trim.build()
        assert 'control_points' in surf

    def test_create_body_molding(self):
        """create_body_molding 便捷函数"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = create_body_molding(path)
        surf = trim.build()
        assert 'control_points' in surf


# ============================================================
# Test 10: 扫描曲面求值与网格化
# ============================================================

class TestSweptSurfaceEvaluation:
    """扫描曲面求值与网格化测试"""

    def test_evaluate_at_endpoints(self):
        """端点求值：u=0 和 u=1 对应路径两端"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=10,
        )
        swept.build()

        # u=0 时应在路径起点附近
        pt_start = swept.evaluate(0.0, 0.0)
        assert pt_start[0] < 0.5  # x 应接近 0

        # u=1 时应在路径终点附近
        pt_end = swept.evaluate(1.0, 0.0)
        assert pt_end[0] > 1.5  # x 应接近 2

    def test_to_mesh(self):
        """转换为 trimesh 网格"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=10,
        )
        swept.build()
        mesh = swept.to_mesh(n_u=20, n_v=8)

        assert isinstance(mesh, trimesh.Trimesh)
        assert mesh.vertices.shape[1] == 3
        assert len(mesh.faces) > 0

    def test_trim_to_mesh(self):
        """装饰条转网格"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        trim = TrimStrip(path, preset='chrome_trim')
        trim.build()
        mesh = trim.to_mesh(n_u=20, n_v=8)

        assert isinstance(mesh, trimesh.Trimesh)

    def test_swept_surface_data_structure(self):
        """扫描曲面数据结构正确"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 12},
            path_samples=15,
        )
        surf = swept.build()

        required_keys = ['control_points', 'weights', 'degree', 'knots_u', 'knots_v', 'n']
        for key in required_keys:
            assert key in surf, f"Missing key: {key}"

        assert surf['control_points'].shape == (15, 12, 3)
        assert surf['n'] == (14, 11)


# ============================================================
# Test 11: UV 参数化连续性
# ============================================================

class TestUVContinuity:
    """UV 参数化连续性测试"""

    def test_u_direction_continuity(self):
        """u 方向连续：相邻参数点的值应接近"""
        path = np.array([
            [0, 0, 0], [1, 0.2, 0], [2, 0.1, 0.3],
            [3, -0.1, 0.2], [4, 0, 0]
        ])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=20,
        )
        swept.build()

        # 沿 u 方向采样，相邻点距离应有限
        prev_pt = None
        for u in np.linspace(0, 1, 50):
            pt = swept.evaluate(u, 0.5)
            if prev_pt is not None:
                dist = np.linalg.norm(pt - prev_pt)
                assert dist < 1.0, f"Discontinuity at u={u}: dist={dist}"
            prev_pt = pt

    def test_v_direction_continuity(self):
        """v 方向连续：相邻参数点的值应接近"""
        path = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
        swept = SweptSurface(
            path_points=path,
            section_type='circle',
            section_params={'radius': 0.05, 'n_points': 8},
            path_samples=10,
        )
        swept.build()

        # 沿 v 方向采样
        prev_pt = None
        for v in np.linspace(0, 1, 50):
            pt = swept.evaluate(0.5, v)
            if prev_pt is not None:
                dist = np.linalg.norm(pt - prev_pt)
                assert dist < 1.0, f"Discontinuity at v={v}: dist={dist}"
            prev_pt = pt


# ============================================================
# 运行入口
# ============================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
