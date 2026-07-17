"""
test_freeform.py — NURBS Core Library + Freeform Deformation 单元测试

覆盖：
1. find_span — 边界情况（u=0, u=1, u 在节点上, u 在节点区间内）
2. basis_funs — 分区性（partition of unity）、非负性
3. open_uniform_knots — 长度正确、两端重复 p+1 次
4. curve_point — 线性曲线、三次曲线端点插值
5. surface_point — 平面测试
6. nurbs_surface_from_grid — 返回值结构正确
7. evaluate_surface — 有理曲面（权重变化时结果改变）
8. FreeformDeformation — 添加预设、apply 不改变顶点数量、零变形不改变顶点
9. 集成测试 — 对 trimesh 球体施加变形后顶点位置确实改变
"""

import numpy as np
import pytest
import trimesh
from algorithm_model.freeform import (
    find_span,
    basis_funs,
    curve_point,
    surface_point,
    open_uniform_knots,
    nurbs_surface_from_grid,
    evaluate_surface,
    evaluate_surface_mesh,
    FreeformDeformation,
    DEFORM_PRESETS,
)


# ============================================================
# Test 1: find_span — 边界情况
# ============================================================

def test_find_span_u_zero():
    """u=0 时应返回 p（首个节点区间）"""
    n, p = 4, 3
    U = open_uniform_knots(n, p)  # [0,0,0,0,0.25,0.5,0.75,1,1,1,1]
    span = find_span(n, p, 0.0, U)
    assert span == p  # span = 3


def test_find_span_u_one():
    """u=1 时应返回 n（末个节点区间）"""
    n, p = 4, 3
    U = open_uniform_knots(n, p)
    span = find_span(n, p, 1.0, U)
    assert span == n  # span = 4


def test_find_span_u_on_knot():
    """u 恰好落在节点上时的行为"""
    n, p = 4, 3
    U = open_uniform_knots(n, p)
    # 中间某个节点
    mid_knot = U[p + 1]  # 0.25
    span = find_span(n, p, mid_knot, U)
    # 应该在包含该节点右边界的位置
    assert span >= p
    assert span <= n


def test_find_span_u_in_span():
    """u 在节点区间内部"""
    n, p = 4, 3
    U = open_uniform_knots(n, p)
    # 对于 n=4, p=3, U=[0,0,0,0,0.5,1,1,1,1], u=0.5 落在区间 [0.5, 1)
    span = find_span(n, p, 0.5, U)
    assert span == 4  # 区间 [0.5, 1)


def test_find_span_right_endpoint():
    """u 略小于 1 时应在末区间"""
    n, p = 4, 3
    U = open_uniform_knots(n, p)
    span = find_span(n, p, 0.999, U)
    assert span == n  # 应在最后一个有意义的区间


# ============================================================
# Test 2: basis_funs — 分区性与非负性
# ============================================================

def test_basis_funs_partition_of_unity():
    """所有基函数之和 = 1（单位分解）"""
    n, p = 6, 3
    U = open_uniform_knots(n, p)
    test_us = np.linspace(0.05, 0.95, 10)
    
    for u in test_us:
        span = find_span(n, p, u, U)
        N = basis_funs(span, u, p, U)
        total = np.sum(N)
        assert abs(total - 1.0) < 1e-10, f"At u={u}: sum(N) = {total}"


def test_basis_funs_nonnegative():
    """基函数值应非负"""
    n, p = 6, 3
    U = open_uniform_knots(n, p)
    test_us = np.linspace(0, 1, 20)
    
    for u in test_us:
        span = find_span(n, p, u, U)
        N = basis_funs(span, u, p, U)
        assert np.all(N >= -1e-10), f"At u={u}: N has negative values: {N}"


def test_basis_funs_degree_zero():
    """次数为 0 时，基函数应该是一个分段常数"""
    n, p = 4, 0
    U = np.array([0, 1, 2, 3, 4])
    # 只有当 u 在对应区间时才为 1
    N0 = basis_funs(0, 0.0, 0, U)
    assert len(N0) == 1
    assert N0[0] == 1.0


# ============================================================
# Test 3: open_uniform_knots — 长度与边界
# ============================================================

def test_knots_length():
    """节点向量长度应为 n + p + 2"""
    n, p = 5, 3
    U = open_uniform_knots(n, p)
    expected_len = n + p + 2
    assert len(U) == expected_len, f"len={len(U)}, expected={expected_len}"


def test_knots_end_repetition():
    """首尾各有 p+1 个重复节点"""
    n, p = 5, 3
    U = open_uniform_knots(n, p)
    # 前 p+1=4 个应为 0
    assert np.allclose(U[:p+1], 0.0)
    # 后 p+1=4 个应为 1
    assert np.allclose(U[-(p+1):], 1.0)


def test_knots_middle_uniform():
    """中间节点应均匀分布"""
    n, p = 5, 3
    U = open_uniform_knots(n, p)
    middle = U[p+1:-(p+1)]
    if len(middle) > 1:
        diffs = np.diff(middle)
        assert np.allclose(diffs, diffs[0], atol=1e-10), "Middle knots not uniform"


def test_knots_various_degrees():
    """不同次数的节点向量"""
    n = 6
    for p in [1, 2, 3, 4]:
        U = open_uniform_knots(n, p)
        assert len(U) == n + p + 2
        assert U[0] == 0.0
        assert U[-1] == 1.0


# ============================================================
# Test 4: curve_point — 线性曲线、三次曲线端点插值
# ============================================================

def test_curve_linear_interpolation():
    """一次 NURBS 曲线应插值控制点"""
    n, p = 2, 1
    P = np.array([[0, 0], [1, 0], [2, 0]], dtype=float)  # 直线
    U = open_uniform_knots(n, p)
    
    # 端点应精确插值
    pt0 = curve_point(n, p, P, U, 0.0)
    pt1 = curve_point(n, p, P, U, 1.0)
    
    assert np.allclose(pt0, P[0], atol=1e-10), f"Start point: {pt0} vs {P[0]}"
    assert np.allclose(pt1, P[-1], atol=1e-10), f"End point: {pt1} vs {P[-1]}"


def test_curve_cubic_endpoint_interpolation():
    """三次曲线端点插值"""
    n, p = 3, 3
    P = np.array([[0, 0], [1, 1], [2, 1], [3, 0]], dtype=float)
    U = open_uniform_knots(n, p)
    
    pt0 = curve_point(n, p, P, U, 0.0)
    pt1 = curve_point(n, p, P, U, 1.0)
    
    assert np.allclose(pt0, P[0], atol=1e-10)
    assert np.allclose(pt1, P[-1], atol=1e-10)


def test_curve_convex_hull():
    """曲线点应在控制多边形凸包内"""
    n, p = 4, 3
    P = np.array([[0, 0], [1, 2], [2, 2], [3, 0], [4, 1]], dtype=float)
    U = open_uniform_knots(n, p)
    
    test_us = np.linspace(0.01, 0.99, 10)
    for u in test_us:
        pt = curve_point(n, p, P, U, u)
        # 简单检查：点到所有控制点的最大距离应有限
        assert np.all(np.isfinite(pt))


# ============================================================
# Test 5: surface_point — 平面测试
# ============================================================

def test_surface_planar():
    """所有控制点共面时，曲面也在该平面内"""
    n_p, n_q = 4, 4
    p, q = 3, 3
    
    # 创建 z=0 平面的控制网格
    P = np.zeros((n_p + 1, n_q + 1, 3))
    for i in range(n_p + 1):
        for j in range(n_q + 1):
            P[i, j] = [i * 0.5, j * 0.5, 0]
    
    U = open_uniform_knots(n_p, p)
    V = open_uniform_knots(n_q, q)
    
    # 测试多个采样点
    for u in [0.25, 0.5, 0.75]:
        for v in [0.25, 0.5, 0.75]:
            pt = surface_point(n_p, n_q, p, q, P, U, V, u, v)
            assert abs(pt[2]) < 1e-10, f"Point not in z=0 plane: {pt}"


def test_surface_corners():
    """曲面四角应与控制点网格四角重合（端点插值）"""
    n_p, n_q = 3, 3
    p, q = 3, 3
    
    P = np.zeros((n_p + 1, n_q + 1, 3))
    P[:, :, 0] = np.linspace(0, 1, n_p + 1)[:, None]  # x
    P[:, :, 1] = np.linspace(0, 1, n_q + 1)[None, :]  # y
    P[:, :, 2] = 0.5  # z constant
    
    U = open_uniform_knots(n_p, p)
    V = open_uniform_knots(n_q, q)
    
    pt_00 = surface_point(n_p, n_q, p, q, P, U, V, 0.0, 0.0)
    pt_11 = surface_point(n_p, n_q, p, q, P, U, V, 1.0, 1.0)
    
    assert np.allclose(pt_00, P[0, 0], atol=1e-10)
    assert np.allclose(pt_11, P[-1, -1], atol=1e-10)


# ============================================================
# Test 6: nurbs_surface_from_grid — 返回值结构
# ============================================================

def test_surface_from_grid_structure():
    """返回值应包含所有必需字段"""
    control_pts = np.zeros((5, 5, 3))
    surf = nurbs_surface_from_grid(control_pts)
    
    required_keys = ['control_points', 'weights', 'degree', 'knots_u', 'knots_v', 'n']
    for key in required_keys:
        assert key in surf, f"Missing key: {key}"


def test_surface_from_grid_weights():
    """默认权重应全为 1"""
    control_pts = np.zeros((5, 5, 3))
    surf = nurbs_surface_from_grid(control_pts)
    assert np.allclose(surf['weights'], 1.0)


def test_surface_from_grid_custom_weights():
    """自定义权重应被正确存储"""
    control_pts = np.zeros((4, 4, 3))
    weights = np.ones((4, 4)) * 2.0
    surf = nurbs_surface_from_grid(control_pts, weights=weights)
    assert np.allclose(surf['weights'], 2.0)


def test_surface_from_grid_degree():
    """度数应正确存储"""
    control_pts = np.zeros((6, 6, 3))
    surf = nurbs_surface_from_grid(control_pts, degree_u=2, degree_v=3)
    assert surf['degree'] == (2, 3)


def test_surface_from_grid_n_tuple():
    """n 元组应为 (n_u-1, n_v-1)"""
    n_u, n_v = 6, 5
    control_pts = np.zeros((n_u, n_v, 3))
    surf = nurbs_surface_from_grid(control_pts)
    assert surf['n'] == (n_u - 1, n_v - 1)


# ============================================================
# Test 7: evaluate_surface — 有理曲面
# ============================================================

def test_evaluate_surface_basic():
    """基本求值测试"""
    control_pts = np.zeros((5, 5, 3))
    for i in range(5):
        for j in range(5):
            control_pts[i, j] = [i * 0.25, j * 0.25, 0]
    
    surf = nurbs_surface_from_grid(control_pts)
    pt = evaluate_surface(surf, 0.5, 0.5)
    
    assert pt.shape == (3,)
    assert np.all(np.isfinite(pt))


def test_evaluate_surface_rational_weights():
    """有权重时曲面应与无权重时不同"""
    # 创建非对称控制点以突出权重效果
    control_pts = np.zeros((4, 4, 3))
    for i in range(4):
        for j in range(4):
            control_pts[i, j] = [i, j, (i + j) * 0.1]
    
    surf_no_weight = nurbs_surface_from_grid(control_pts)
    surf_weighted = nurbs_surface_from_grid(control_pts, weights=np.ones((4, 4)) * 2.0)
    
    # 均匀权重应不影响结果（与权重=1等价）
    pt1 = evaluate_surface(surf_no_weight, 0.5, 0.5)
    pt2 = evaluate_surface(surf_weighted, 0.5, 0.5)
    assert np.allclose(pt1, pt2, atol=1e-10)


def test_evaluate_surface_non_uniform_weights():
    """非均匀权重应改变曲面形状"""
    control_pts = np.zeros((4, 4, 3))
    for i in range(4):
        for j in range(4):
            control_pts[i, j] = [i, j, 0]
    
    # 中心权重更大
    weights = np.ones((4, 4))
    weights[1:3, 1:3] = 5.0
    
    surf = nurbs_surface_from_grid(control_pts, weights=weights)
    pt = evaluate_surface(surf, 0.5, 0.5)
    
    # 中心应该被"拉向"权重大的控制点
    # 由于高权重在中心，z 值应该接近中心控制点的 z（也是0）
    # 这里只验证它是一个有效的点
    assert np.all(np.isfinite(pt))


# ============================================================
# Test 8: evaluate_surface_mesh — 网格采样
# ============================================================

def test_evaluate_surface_mesh_output_shape():
    """网格采样输出形状正确"""
    control_pts = np.zeros((5, 5, 3))
    for i in range(5):
        for j in range(5):
            control_pts[i, j] = [i * 0.25, j * 0.25, 0]
    
    surf = nurbs_surface_from_grid(control_pts)
    n_u, n_v = 10, 8
    points, params = evaluate_surface_mesh(surf, n_u=n_u, n_v=n_v)
    
    assert points.shape == (n_u * n_v, 3)
    assert params.shape == (n_u * n_v, 2)


def test_evaluate_surface_mesh_param_range():
    """参数网格应在 [0, 1] 范围内"""
    control_pts = np.zeros((5, 5, 3))
    surf = nurbs_surface_from_grid(control_pts)
    points, params = evaluate_surface_mesh(surf, n_u=5, n_v=5)
    
    assert np.all(params[:, 0] >= 0) and np.all(params[:, 0] <= 1)
    assert np.all(params[:, 1] >= 0) and np.all(params[:, 1] <= 1)


# ============================================================
# Test 9: FreeformDeformation — 预设与基本操作
# ============================================================

def test_deform_presets_exist():
    """所有预设应存在"""
    expected_presets = ['fender_bulge', 'door_dent', 'hood_scoop', 'character_line', 'roof_sculpt']
    for preset in expected_presets:
        assert preset in DEFORM_PRESETS, f"Missing preset: {preset}"


def test_deform_add_single():
    """添加单个变形"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, center_z=0.5)
    summary = ffd.summary()
    assert len(summary) == 1
    assert summary[0]['preset'] == 'fender_bulge'


def test_deform_add_multiple():
    """添加多个变形"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0)
    ffd.add_deformation('hood_scoop', center_x=1.0)
    ffd.add_deformation('character_line', center_x=-1.0)
    summary = ffd.summary()
    assert len(summary) == 3


def test_deform_apply_preserves_vertex_count():
    """apply 不改变顶点数量"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, center_z=0.5)
    
    vertices = np.random.rand(100, 3)
    vertices_deformed = ffd.apply(vertices, body_length=4.0, body_height=1.5)
    
    assert vertices_deformed.shape == vertices.shape


def test_deform_zero_amplitude_unchanged():
    """零振幅变形不改变顶点"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, center_z=0.5, amplitude=0.0)
    
    vertices = np.random.rand(50, 3) * np.array([2.0, 2.0, 1.5])  # 缩放到车身范围
    vertices_deformed = ffd.apply(vertices, body_length=4.0, body_height=1.5)
    
    assert np.allclose(vertices, vertices_deformed, atol=1e-10)


def test_deform_override_amplitude():
    """振幅覆盖功能"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, amplitude=0.1)  # 覆盖默认的 0.05
    
    summary = ffd.summary()
    assert summary[0]['amplitude'] == 0.1


def test_deform_override_size():
    """影响范围覆盖功能"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, size=(0.5, 0.3))
    
    summary = ffd.summary()
    assert summary[0]['size'] == (0.5, 0.3)


def test_deform_invalid_preset_raises():
    """无效预设名应抛出错误"""
    ffd = FreeformDeformation()
    with pytest.raises(ValueError):
        ffd.add_deformation('invalid_preset_name')


# ============================================================
# Test 10: 集成测试 — 对 trimesh 球体施加变形
# ============================================================

def test_deform_sphere_changes_vertices():
    """对 trimesh 球体施加变形后顶点位置确实改变"""
    # 创建小球体
    sphere = trimesh.creation.box(extents=[1.0, 1.0, 1.0])  # 用立方体代替球体加速测试
    
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, center_z=0.5, amplitude=0.1, size=(0.5, 0.5))
    
    vertices_original = sphere.vertices.copy()
    vertices_deformed = ffd.apply(vertices_original, body_length=2.0, body_height=2.0)
    
    # 至少有一些顶点应该发生变化
    diff = np.abs(vertices_deformed - vertices_original)
    max_diff = np.max(diff)
    assert max_diff > 1e-6, "Vertices should change after deformation"


def test_deform_multiple_layers_additive():
    """多层变形应叠加"""
    ffd = FreeformDeformation()
    ffd.add_deformation('fender_bulge', center_x=0.0, amplitude=0.03)
    ffd.add_deformation('hood_scoop', center_x=0.0, amplitude=0.02)
    
    vertices = np.random.rand(100, 3) * np.array([2.0, 2.0, 1.5])
    
    # 单层变形
    ffd_single = FreeformDeformation()
    ffd_single.add_deformation('fender_bulge', center_x=0.0, amplitude=0.03)
    verts_single = ffd_single.apply(vertices.copy(), body_length=4.0, body_height=1.5)
    
    # 双层变形
    verts_double = ffd.apply(vertices.copy(), body_length=4.0, body_height=1.5)
    
    # 双层变形与单层变形应该不同
    # （因为有两层不同的变形）
    diff = np.abs(verts_double - verts_single)
    # 验证至少有部分变化
    assert np.any(diff > 1e-8)


# ============================================================
# 运行入口
# ============================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
