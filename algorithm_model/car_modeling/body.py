"""
主车身壳体建模

通过沿车长方向取截面，按截面形状（宽+高）构建完整外壳。
算法核心：截面宽度 + 截面高度 + 截面形状 → 三角网格

集成 W2-D2 三区段 blending + tumblehome：
- ZoneParamsTable 查表
- three_zone_weights + normalize_zone_weights（F4）
- compute_tumblehome（F5）
"""
import numpy as np
import trimesh
from typing import List, Tuple, Dict, Any
from .car_params import CarParams
from .blending import (
    three_zone_weights,
    normalize_zone_weights,
    compute_tumblehome,
    ZONE_PARAMS_TABLE,
    get_zone,
)


def get_hardpoints(params: CarParams) -> Dict[str, float]:
    """
    从 CarParams 生成硬点字典

    用于三区段 blending 计算。

    区段定义：
    - hood: front_x ~ hood_end_x
    - cabin: cabin_start_x ~ cabin_end_x（包含前挡风区域）
    - trunk: trunk_start_x ~ rear_x
    """
    L = params.L
    front_x = -L / 2
    rear_x = L / 2

    # 发动机盖终点
    hood_end_x = front_x + params.hood_length

    # 座舱起止点
    # cabin_start_x < hood_end_x 确保平滑过渡
    cabin_start_x = min(hood_end_x - 0.1, front_x + params.hood_length * 0.85)
    cabin_end_x = cabin_start_x + params.cabin_length

    # 行李箱起点
    # trunk_start_x > cabin_end_x 确保平滑过渡
    trunk_start_x = max(cabin_end_x + 0.1, rear_x - params.trunk_length * 0.85)

    return {
        "L": L,
        "front_x": front_x,
        "rear_x": rear_x,
        "hood_end_x": hood_end_x,
        "cabin_start_x": cabin_start_x,
        "cabin_end_x": cabin_end_x,
        "trunk_start_x": trunk_start_x,
    }


def _section_width(
    x_norm: float,
    params: CarParams,
    hardpoints: Dict[str, float],
    zone_params_table=None,
) -> float:
    """
    车长方向位置 x_norm ∈ [-1, 1] 处的车体半宽（y 方向）

    设计：楔形 - 前窄 / 中后宽 / 尾部稍收
    公式：cos^1.5(πx/2) * 前段修长系数 * 后段修长系数

    三区段 blending 集成：
    - 使用 three_zone_weights 获取区段权重
    - 使用 ZONE_PARAMS_TABLE 查表调整宽度
    """
    x = x_norm * params.L / 2

    # ===== 原始宽度计算 =====
    base = np.cos(x_norm * np.pi / 2) ** 1.5
    front_factor = 1.0 - 0.15 * max(0, -x_norm)
    rear_factor = 1.0 - 0.08 * max(0, x_norm)
    base_width = params.W / 2 * base * front_factor * rear_factor

    # ===== 三区段 blending =====
    if zone_params_table is not None:
        # 获取原始权重
        hoodF, cabinF, trunkF = three_zone_weights(x, hardpoints)
        # 归一化
        hood_n, cabin_n, trunk_n = normalize_zone_weights(hoodF, cabinF, trunkF)

        # 获取各区段 waist level（中间水平）的 y_scale
        waist_idx = 2  # waist level index
        hood_scale = zone_params_table.get_level("hood", waist_idx).y_scale
        cabin_scale = zone_params_table.get_level("cabin", waist_idx).y_scale
        trunk_scale = zone_params_table.get_level("trunk", waist_idx).y_scale

        # 加权混合
        blended_scale = hood_n * hood_scale + cabin_n * cabin_scale + trunk_n * trunk_scale
        return base_width * blended_scale

    return base_width


def _section_height(x_norm: float, params: CarParams) -> float:
    """
    车长方向位置 x_norm ∈ [-1, 1] 处的车体高度（z 方向地面到顶）

    设计 5 段造型：
    - 发动机盖（低平）
    - 前挡风过渡（斜向上）
    - 座舱前沿（快速攀升）
    - 车顶（高顶）
    - 后挡风（斜向下）
    - 行李箱（低平）
    """
    L = params.L
    x = x_norm * L / 2
    front_edge = -L/2 + params.hood_length
    windshield_top = front_edge + 0.05
    roof_start = windshield_top + 0.5
    roof_end = roof_start + params.cabin_length * 0.6
    rear_glass_start = roof_end
    rear_glass_end = rear_glass_start + 0.7
    trunk_start = rear_glass_end
    trunk_end = L/2
    ground_clear = params.ground_clearance
    max_h = params.H - ground_clear

    if x < front_edge:  # 发动机盖
        t = (x - (-L/2)) / (front_edge - (-L/2))
        return ground_clear + 0.55 + t * (ground_clear + 0.78 - ground_clear - 0.55)
    elif x < windshield_top:  # 前挡风过渡
        t = (x - front_edge) / max(1e-6, windshield_top - front_edge)
        return (ground_clear + 0.78) + t * (ground_clear + 1.0 - ground_clear - 0.78)
    elif x < roof_start:  # 座舱前沿
        t = (x - windshield_top) / max(1e-6, roof_start - windshield_top)
        h_start = ground_clear + 1.0
        h_end = params.H - 0.05
        arc = params.roof_arc
        return h_start + t * (h_end - h_start) * (1 + arc * np.sin(t * np.pi))
    elif x < roof_end:  # 车顶
        return params.H - 0.05
    elif x < rear_glass_end:  # 后挡风
        t = (x - rear_glass_start) / max(1e-6, rear_glass_end - rear_glass_start)
        h_start = params.H - 0.05
        h_end = ground_clear + 0.7
        return h_start + t * (h_end - h_start)
    else:  # 行李箱
        t = (x - trunk_start) / max(1e-6, trunk_end - trunk_start)
        h_start = ground_clear + 0.7
        h_end = ground_clear + 0.6
        return h_start + t * (h_end - h_start)


def _section_shape(
    x_norm: float,
    z_norm: float,
    params: CarParams,
    hardpoints: Dict[str, float],
    zone_params_table=None,
) -> Tuple[float, float]:
    """
    截面形状：给定 x_norm 和 z_norm（0=地，1=顶）
    返回 (y_norm, lateral_squish)

    设计：上窄下宽 / 顶部尖 / 肩部最宽 / 底部稍窄

    Tumblehome 集成（车顶区域）：
    - 根据 C-pillar 角度计算 tumblehome 衰减
    - 车顶越窄，肩部越宽
    """
    half_w = _section_width(x_norm, params, hardpoints, zone_params_table)
    p_shoulder = 0.65
    top_factor = 1.0 - 0.10 * (z_norm ** 2)
    if z_norm < p_shoulder:
        bot_factor = 0.85 + 0.15 * (z_norm / p_shoulder)
    else:
        bot_factor = 1.0 - 0.18 * ((z_norm - p_shoulder) / (1 - p_shoulder))
    y = half_w * top_factor * bot_factor

    # ===== Tumblehome 效应（F5）=====
    # 仅在车顶区域（z_norm > 0.8）应用 tumblehome
    if zone_params_table is not None and z_norm > 0.8:
        x = x_norm * params.L / 2
        zone = get_zone(x, hardpoints)

        # 获取 shoulder level 的 y_scale
        shoulder_idx = 3
        zone_level = zone_params_table.get_level(zone, shoulder_idx)
        shoulderW = zone_level.y_scale

        # C-pillar 角度（简化：使用后挡风倾角）
        CA = np.radians(params.rear_glass_angle) * 0.7  # 缩放系数

        # 计算 tumblehome
        hw_base = half_w
        roof_hw = compute_tumblehome(hw_base, shoulderW, CA)

        # 调整车顶宽度
        tumblehome_ratio = roof_hw / hw_base if hw_base > 1e-6 else 1.0
        # 在车顶区域平滑应用
        top_smooth = (z_norm - 0.8) / 0.2  # 0.8-1.0 区间
        top_smooth = max(0.0, min(1.0, top_smooth))
        adjustment = 1.0 - (1.0 - tumblehome_ratio) * top_smooth
        y = y * adjustment

    return y, 1.0


def build_body(
    params: CarParams,
    n_long: int = 48,
    n_circ: int = 24,
    use_blending: bool = True,
) -> trimesh.Trimesh:
    """
    构建主车身壳体（左右对称的完整外壳）

    Args:
        params: 整车参数
        n_long: 车长方向分段数
        n_circ: 截面方向分段数
        use_blending: 是否启用三区段 blending（默认 True）

    Returns:
        trimesh.Trimesh 车身壳体
    """
    # 生成硬点
    hardpoints = get_hardpoints(params)
    zone_params = ZONE_PARAMS_TABLE if use_blending else None

    verts: List[List[float]] = []
    faces: List[List[int]] = []

    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2
        for j in range(n_circ + 1):
            z_norm = j / n_circ
            z = _section_height(x_norm, params)
            y, _ = _section_shape(x_norm, z_norm, params, hardpoints, zone_params)
            verts.append([x, y, z])
            verts.append([x, -y, z])  # 对称侧

    cols = 2 * (n_circ + 1)
    for i in range(n_long):
        for j in range(n_circ):
            v00 = i * cols + 2 * j
            v10 = (i + 1) * cols + 2 * j
            v01 = i * cols + 2 * (j + 1)
            v11 = (i + 1) * cols + 2 * (j + 1)
            w00 = i * cols + 2 * j + 1
            w10 = (i + 1) * cols + 2 * j + 1
            w01 = i * cols + 2 * (j + 1) + 1
            w11 = (i + 1) * cols + 2 * (j + 1) + 1

            # 左侧（法向朝外）
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
            # 右侧（法向朝外）
            faces.append([w00, w11, w10])
            faces.append([w00, w01, w11])

    mesh = trimesh.Trimesh(
        vertices=np.array(verts, dtype=np.float64),
        faces=np.array(faces, dtype=np.int64),
        process=True,
    )
    mesh.visual.face_colors = [200, 30, 40, 255]  # 经典红
    return mesh


# ============================================================
# D3: 31 点截面网格装配（使用 parametrize 模块）
# ============================================================

def build_body_31point(
    params: CarParams,
    n_long: int = 80,
    use_blending: bool = True,
) -> trimesh.Trimesh:
    """
    构建主车身壳体（使用 31 点闭合截面）

    D3 新增方法，使用 parametrize 模块的 generate_cross_section
    生成 31 点闭合截面，然后沿车长方向堆叠。

    Args:
        params: 整车参数
        n_long: 车长方向分段数（默认 80）
        use_blending: 是否启用三区段 blending（默认 True）

    Returns:
        trimesh.Trimesh 车身壳体
    """
    # 延迟导入避免循环依赖
    from .parametrize import generate_cross_section, ZONE_PARAMS_TABLE as PARAMS_TABLE

    # 生成硬点
    hardpoints = get_hardpoints(params)
    zone_params = PARAMS_TABLE if use_blending else None

    verts: List[List[float]] = []
    faces: List[List[int]] = []

    # 每截面 30 个独立点（不包括重复的闭合点）
    # 31 点闭合截面：points[0..29] 独立，points[30] = points[0]
    # 为了 G0 100%，我们使用 30 个独立点，最后一条边闭合
    n_pts_per_section = 30  # 独立点数

    # 存储每截面的顶点索引范围（用于端盖）
    section_start_idx = []

    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2

        section_start_idx.append(len(verts))

        # 生成 31 点截面，取前 30 个独立点
        if zone_params is not None:
            cs = generate_cross_section(x, zone_params, hardpoints)
            # 只取前 30 个点，第 31 点 = 第 1 点（闭合）
            section_yz = cs.points[:30]  # shape (30, 2)
        else:
            # 降级
            section_yz = np.zeros((30, 2))
            for j in range(30):
                z_norm = j / 29
                half_w = _section_width(x_norm, params, hardpoints, None)
                z = _section_height(x_norm, params)
                y, _ = _section_shape(x_norm, z_norm, params, hardpoints, None)
                section_yz[j] = [y, z]

        # 添加顶点（左右对称）
        for j in range(n_pts_per_section):
            y_coord = section_yz[j, 0]
            z_coord = section_yz[j, 1]
            verts.append([x, y_coord, z_coord])  # 左侧
            verts.append([x, -y_coord, z_coord])  # 右侧

    # 三角形连接
    cols = 2 * n_pts_per_section  # 每行的顶点数

    for i in range(n_long):
        for j in range(n_pts_per_section - 1):
            # 当前截面和下一截面的顶点索引
            # 左侧
            v00 = i * cols + 2 * j
            v10 = (i + 1) * cols + 2 * j
            v01 = i * cols + 2 * (j + 1)
            v11 = (i + 1) * cols + 2 * (j + 1)

            # 右侧
            w00 = i * cols + 2 * j + 1
            w10 = (i + 1) * cols + 2 * j + 1
            w01 = i * cols + 2 * (j + 1) + 1
            w11 = (i + 1) * cols + 2 * (j + 1) + 1

            # 左侧三角形（法向朝外）
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])

            # 右侧三角形（法向朝外）
            faces.append([w00, w11, w10])
            faces.append([w00, w01, w11])

        # 添加闭合三角形：第 29 点连接第 0 点
        j = n_pts_per_section - 1  # j = 29
        k = 0  # k = 0（闭合）
        # 左侧
        v_last = i * cols + 2 * j      # (i, 29)
        v_next = (i + 1) * cols + 2 * j  # (i+1, 29)
        v_first = i * cols + 2 * k      # (i, 0)
        v_next_first = (i + 1) * cols + 2 * k  # (i+1, 0)
        faces.append([v_last, v_first, v_next])
        faces.append([v_next, v_first, v_next_first])

        # 右侧
        w_last = i * cols + 2 * j + 1
        w_next = (i + 1) * cols + 2 * j + 1
        w_first = i * cols + 2 * k + 1
        w_next_first = (i + 1) * cols + 2 * k + 1
        faces.append([w_last, w_next_first, w_first])
        faces.append([w_last, w_next, w_next_first])

    # 添加车头端盖（i=0 的第一个截面）
    # 使用扇形三角化，每个三角形 = [center, edge_j, edge_{j+1}]
    # 这样边缘边 (edge_j, edge_{j+1}) 只被一个三角形覆盖
    front_center = len(verts)
    front_section_start = section_start_idx[0]
    verts.append(verts[front_section_start])  # 中心点 = 第一个顶点
    for j in range(n_pts_per_section - 1):
        v0 = front_section_start + 2 * j      # 左侧边缘点
        v1 = front_section_start + 2 * (j + 1)  # 下一个左侧边缘点
        faces.append([front_center, v1, v0])  # 三角形 = [center, next, current]
    # 闭合
    v_last = front_section_start + 2 * (n_pts_per_section - 1)
    v_first = front_section_start
    faces.append([front_center, v_first, v_last])

    # 添加车尾端盖（i=n_long 的最后一个截面）
    # 使用相同的扇形三角化方向
    rear_center = len(verts)
    rear_section_start = section_start_idx[-1]
    verts.append(verts[rear_section_start])  # 中心点
    for j in range(n_pts_per_section - 1):
        v0 = rear_section_start + 2 * j
        v1 = rear_section_start + 2 * (j + 1)
        faces.append([rear_center, v0, v1])  # 方向与前盖一致
    # 闭合
    v_last = rear_section_start + 2 * (n_pts_per_section - 1)
    v_first = rear_section_start
    faces.append([rear_center, v_last, v_first])

    # 创建 mesh（不调用 process，避免引入多重边）
    vertices = np.array(verts, dtype=np.float64)
    faces_arr = np.array(faces, dtype=np.int64)

    # 验证：无 NaN/Inf
    assert not np.any(np.isnan(vertices)), "vertices 包含 NaN"
    assert not np.any(np.isinf(vertices)), "vertices 包含 Inf"

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=faces_arr,
        process=False,  # 不调用 process，保持 G0 连续性
    )
    mesh.visual.face_colors = [200, 30, 40, 255]  # 经典红

    return mesh


def assemble_mesh(
    params: CarParams,
    n_long: int = 80,
) -> trimesh.Trimesh:
    """
    D3 网格装配入口（兼容原 API）

    80 longitudinal stations × 31 截面点 = 2,480 stations

    Args:
        params: 整车参数
        n_long: 车长方向分段数（默认 80）

    Returns:
        trimesh.Trimesh: 组装后的 mesh
    """
    return build_body_31point(params, n_long=n_long, use_blending=True)
