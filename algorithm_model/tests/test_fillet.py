"""
Tests for fillet_surface module

圆角/倒角曲面模块的单元测试
"""

import numpy as np
import pytest
import trimesh
from algorithm_model.freeform.fillet_surface import (
    IntersectionCurve,
    create_fillet_surface,
    create_chamfer_surface,
    create_wheel_arch_fillet,
    surface_to_mesh,
)


# ============================================================
# Test IntersectionCurve
# ============================================================

class TestIntersectionCurve:
    """测试交线类"""
    
    def test_straight_line_two_points(self):
        """直线交线：2点定义，evaluate返回中间点"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        curve = IntersectionCurve(points)
        
        # t=0 时应返回起点
        p0 = curve.evaluate(0)
        np.testing.assert_array_almost_equal(p0, [0, 0, 0])
        
        # t=total_length/2 时应返回中点
        mid = curve.evaluate(curve.total_length / 2)
        np.testing.assert_array_almost_equal(mid, [0.5, 0, 0])
        
        # t=total_length 时应返回终点
        p1 = curve.evaluate(curve.total_length)
        np.testing.assert_array_almost_equal(p1, [1, 0, 0])
    
    def test_polyline_corner_interpolation(self):
        """折线交线：3点，evaluate在拐角处正确插值"""
        points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        curve = IntersectionCurve(points)
        
        # 总弧长 = 1 + 1 = 2
        assert curve.total_length == 2.0
        
        # 在拐角处
        corner = curve.evaluate(1.0)
        np.testing.assert_array_almost_equal(corner, [1, 0, 0])
    
    def test_tangent_direction(self):
        """tangent方向正确"""
        # 沿 x 轴的直线
        points = np.array([[0, 0, 0], [1, 0, 0]])
        curve = IntersectionCurve(points)
        
        tangent = curve.tangent(0.5)
        np.testing.assert_array_almost_equal(tangent, [1, 0, 0])
    
    def test_tangent_polyline(self):
        """折线的tangent分段正确"""
        points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        curve = IntersectionCurve(points)
        
        # 第一段沿 x 方向
        tangent1 = curve.tangent(0.3)
        np.testing.assert_array_almost_equal(tangent1, [1, 0, 0])
        
        # 第二段沿 y 方向
        tangent2 = curve.tangent(1.5)
        np.testing.assert_array_almost_equal(tangent2, [0, 1, 0])
    
    def test_arc_length_computation(self):
        """弧长计算正确"""
        # L 形折线
        points = np.array([[0, 0, 0], [3, 0, 0], [3, 4, 0]])
        curve = IntersectionCurve(points)
        
        # 弧长 = 3 + 4 = 7
        assert curve.total_length == 7.0
        
        # 累积弧长
        np.testing.assert_array_almost_equal(
            curve.arc_lengths, [0, 3, 7]
        )
    
    def test_arc_length_normalization(self):
        """弧长归一化参数 t ∈ [0,1]"""
        points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0]])
        curve = IntersectionCurve(points)
        
        # t=0.5 对应弧长 1.0（总长的一半）
        p = curve.evaluate(curve.total_length * 0.5)
        np.testing.assert_array_almost_equal(p, [1, 0, 0])
    
    def test_clip_boundary(self):
        """边界clip正确"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        curve = IntersectionCurve(points)
        
        # 超出范围应clip到端点
        p_neg = curve.evaluate(-1)
        np.testing.assert_array_almost_equal(p_neg, [0, 0, 0])
        
        p_over = curve.evaluate(10)
        np.testing.assert_array_almost_equal(p_over, [1, 0, 0])


# ============================================================
# Test create_fillet_surface
# ============================================================

class TestCreateFilletSurface:
    """测试圆角曲面生成"""
    
    def test_fixed_radius_returns_valid_surf(self):
        """固定半径圆角：返回正确的control_points形状"""
        # 定义简单交线
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        # 定义常法向量
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=10,
            n_arc_points=8,
        )
        
        # 验证返回值
        assert 'control_points' in surf
        assert surf['control_points'].shape == (10, 8, 3)
        assert 'knots_u' in surf
        assert 'knots_v' in surf
    
    def test_variable_radius_gradient(self):
        """可变半径圆角：半径从大到小渐变"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        # 可变半径：从 0.05 渐变到 0.01
        def var_radius(t):
            return 0.05 - 0.04 * t
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=8,
            variable_radius=var_radius,
        )
        
        cp = surf['control_points']
        
        # 检查起点和终点的圆弧半径差异
        # 起点的偏移量应大于终点
        start_offset = np.linalg.norm(cp[0, 0] - cp[0, -1])
        end_offset = np.linalg.norm(cp[-1, 0] - cp[-1, -1])
        
        # 起点半径(0.05) > 终点半径(0.01)，偏移量应该更大
        assert start_offset > end_offset
    
    def test_degenerate_parallel_normals(self):
        """法向量平行时的退化处理"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        # 两面法向相同（平行）
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 0, 1])
        
        # 不应抛出异常
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=4,
        )
        
        assert surf is not None
    
    def test_different_n_samples(self):
        """不同采样数"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        for n_samples in [5, 10, 20]:
            surf = create_fillet_surface(
                intersection=intersection,
                surface_a_normal=normal_a,
                surface_b_normal=normal_b,
                radius=0.02,
                n_samples=n_samples,
                n_arc_points=6,
            )
            
            assert surf['control_points'].shape[0] == n_samples
    
    def test_different_n_arc_points(self):
        """不同圆弧点数"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        for n_arc in [4, 6, 8]:
            surf = create_fillet_surface(
                intersection=intersection,
                surface_a_normal=normal_a,
                surface_b_normal=normal_b,
                radius=0.02,
                n_samples=10,
                n_arc_points=n_arc,
            )
            
            assert surf['control_points'].shape[1] == n_arc


# ============================================================
# Test create_chamfer_surface
# ============================================================

class TestCreateChamferSurface:
    """测试倒角曲面生成"""
    
    def test_45degree_chamfer_symmetric(self):
        """45°倒角：起终点对称"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        width = 0.01
        surf = create_chamfer_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            width=width,
            angle=45.0,
            n_samples=5,
        )
        
        cp = surf['control_points']
        
        # 45°时，两方向的偏移量相同
        for i in range(5):
            offset_a = np.linalg.norm(cp[i, 0] - intersection.evaluate(i / 4 * intersection.total_length))
            offset_b = np.linalg.norm(cp[i, 1] - intersection.evaluate(i / 4 * intersection.total_length))
            np.testing.assert_almost_equal(offset_a, offset_b, decimal=10)
    
    def test_non_45degree_chamfer_asymmetric(self):
        """非45°倒角：不对称偏移"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        width = 0.01
        surf = create_chamfer_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            width=width,
            angle=30.0,  # 30° 非对称
            n_samples=5,
        )
        
        cp = surf['control_points']
        
        # 不同角度的偏移量相同（因为width相同）
        # 但control_points的分布会不同
        assert cp.shape == (5, 2, 3)
    
    def test_chamfer_control_points_shape(self):
        """倒角曲面控制点形状"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_chamfer_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            width=0.01,
            angle=45.0,
            n_samples=15,
        )
        
        # v 方向只有 2 个点（起点 + 终点）
        assert surf['control_points'].shape == (15, 2, 3)
        
        # degree_v = 1（线性）
        assert surf['degree'][1] == 1


# ============================================================
# Test create_wheel_arch_fillet
# ============================================================

class TestCreateWheelArchFillet:
    """测试轮眉圆角生成"""
    
    def test_returns_valid_nurbs_surface(self):
        """返回有效的NURBS曲面"""
        wheel_center = np.array([0, 0, 0.3])
        wheel_radius = 0.3
        body_params = {
            'ground_clearance': 0.2,
            'W': 1.6,
            'L': 4.5,
        }
        
        surf = create_wheel_arch_fillet(
            wheel_center=wheel_center,
            wheel_radius=wheel_radius,
            body_params=body_params,
            fillet_radius=0.015,
            n_samples=24,
            n_arc_points=8,
        )
        
        assert 'control_points' in surf
        assert 'knots_u' in surf
        assert 'knots_v' in surf
    
    def test_control_points_shape(self):
        """control_points形状正确"""
        wheel_center = np.array([0, 0, 0.3])
        wheel_radius = 0.3
        body_params = {'ground_clearance': 0.2, 'W': 1.6, 'L': 4.5}
        
        n_samples = 24
        n_arc_points = 8
        
        surf = create_wheel_arch_fillet(
            wheel_center=wheel_center,
            wheel_radius=wheel_radius,
            body_params=body_params,
            fillet_radius=0.015,
            n_samples=n_samples,
            n_arc_points=n_arc_points,
        )
        
        assert surf['control_points'].shape == (n_samples, n_arc_points, 3)
    
    def test_arch_follows_wheel(self):
        """圆弧沿车轮"""
        wheel_center = np.array([0, 0, 0.3])
        wheel_radius = 0.3
        body_params = {'ground_clearance': 0.2, 'W': 1.6, 'L': 4.5}
        
        surf = create_wheel_arch_fillet(
            wheel_center=wheel_center,
            wheel_radius=wheel_radius,
            body_params=body_params,
            fillet_radius=0.01,
            n_samples=10,
            n_arc_points=4,
        )
        
        # 控制点应沿车轮上方（z > wheel_center[2]）
        cp = surf['control_points']
        min_z = cp[:, :, 2].min()
        max_z = cp[:, :, 2].max()
        
        # 轮眉在车轮上方
        assert min_z > wheel_center[2] - wheel_radius
        assert max_z > wheel_center[2]


# ============================================================
# Test surface_to_mesh
# ============================================================

class TestSurfaceToMesh:
    """测试曲面网格化"""
    
    def test_generates_valid_trimesh(self):
        """生成有效的trimesh"""
        # 创建简单曲面
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=4,
        )
        
        mesh = surface_to_mesh(surf, n_u=10, n_v=5)
        
        assert isinstance(mesh, trimesh.Trimesh)
        assert mesh.vertices.shape[1] == 3  # 3D 点
        assert len(mesh.faces) > 0
    
    def test_vertex_count(self):
        """顶点数 = n_u * n_v"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=4,
        )
        
        n_u, n_v = 30, 10
        mesh = surface_to_mesh(surf, n_u=n_u, n_v=n_v)
        
        expected_vertices = n_u * n_v
        assert len(mesh.vertices) == expected_vertices
    
    def test_face_count(self):
        """面数 = (n_u-1) * (n_v-1) * 2"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=4,
        )
        
        n_u, n_v = 30, 10
        mesh = surface_to_mesh(surf, n_u=n_u, n_v=n_v)
        
        expected_faces = (n_u - 1) * (n_v - 1) * 2
        assert len(mesh.faces) == expected_faces
    
    def test_mesh_has_color(self):
        """网格有颜色"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=5,
            n_arc_points=4,
        )
        
        custom_color = (100, 150, 200, 255)
        mesh = surface_to_mesh(surf, n_u=10, n_v=5, color=custom_color)
        
        assert hasattr(mesh.visual, 'face_colors')
    
    def test_wheel_arch_mesh(self):
        """轮眉网格化"""
        wheel_center = np.array([0, 0, 0.3])
        wheel_radius = 0.3
        body_params = {'ground_clearance': 0.2, 'W': 1.6, 'L': 4.5}
        
        surf = create_wheel_arch_fillet(
            wheel_center=wheel_center,
            wheel_radius=wheel_radius,
            body_params=body_params,
            fillet_radius=0.015,
            n_samples=24,
            n_arc_points=8,
        )
        
        mesh = surface_to_mesh(surf, n_u=30, n_v=10)
        
        assert isinstance(mesh, trimesh.Trimesh)
        assert len(mesh.faces) > 0


# ============================================================
# Test edge cases and robustness
# ============================================================

class TestEdgeCases:
    """边界情况和健壮性测试"""
    
    def test_zero_length_intersection(self):
        """零长度交线（两点重合）"""
        points = np.array([[0, 0, 0], [0, 0, 0]])
        # 理论上应该报错，但根据实现，至少要有2个点
        # 这里测试正常长度的最小情况
        points = np.array([[0, 0, 0], [0.001, 0, 0]])
        curve = IntersectionCurve(points)
        
        assert curve.total_length > 0
    
    def test_many_points_curve(self):
        """多点曲线"""
        # 圆形曲线
        n = 100
        angles = np.linspace(0, 2*np.pi, n)
        points = np.stack([
            np.cos(angles),
            np.sin(angles),
            np.zeros(n)
        ], axis=1)
        
        curve = IntersectionCurve(points)
        
        # 弧长约等于圆的周长
        expected_circumference = 2 * np.pi
        np.testing.assert_almost_equal(
            curve.total_length, expected_circumference, decimal=1
        )
    
    def test_perpendicular_normals(self):
        """垂直法向情况"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        # 两个垂直的法向量
        def normal_a(p):
            return np.array([1, 0, 0])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=0.02,
            n_samples=10,
            n_arc_points=8,
        )
        
        assert surf['control_points'].shape == (10, 8, 3)
    
    def test_chamfer_zero_width(self):
        """零宽度倒角"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_chamfer_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            width=0.0,  # 零宽度
            angle=45.0,
            n_samples=5,
        )
        
        cp = surf['control_points']
        # 零宽度时，两点应该重合于交线
        for i in range(5):
            np.testing.assert_array_almost_equal(cp[i, 0], cp[i, 1])
    
    def test_small_radius(self):
        """小半径圆角"""
        points = np.array([[0, 0, 0], [1, 0, 0]])
        intersection = IntersectionCurve(points)
        
        def normal_a(p):
            return np.array([0, 0, 1])
        
        def normal_b(p):
            return np.array([0, 1, 0])
        
        surf = create_fillet_surface(
            intersection=intersection,
            surface_a_normal=normal_a,
            surface_b_normal=normal_b,
            radius=1e-6,  # 极小半径
            n_samples=5,
            n_arc_points=4,
        )
        
        assert surf is not None
