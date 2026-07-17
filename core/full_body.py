"""
EVOLUTION AI - 完整汽车造型建模 v3
包含：主车身壳体、四轮+轮拱、玻璃区域、前后大灯、进气格栅、尾灯、后视镜、车门分缝线
所有部件用 trimesh 构建并可参数化调整
"""
import numpy as np
import trimesh
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
import json


# ============================================================
# 整车参数
# ============================================================
@dataclass
class CarParams:
    """整车级参数 - 控制所有造型特征"""
    # 基础尺寸
    L: float = 4.7           # 车长 m
    W: float = 1.85          # 车宽 m
    H: float = 1.45          # 车高 m
    wheelbase: float = 2.8   # 轴距 m

    # 比例姿态
    hood_length: float = 1.1     # 发动机盖长度（占车长比例）
    cabin_length: float = 2.2    # 座舱长度
    trunk_length: float = 1.0    # 行李箱长度
    ground_clearance: float = 0.18  # 最小离地间隙

    # 曲面特征
    hood_angle: float = 12.0         # 发动机盖角度 (°)
    roof_arc: float = 0.35           # 车顶弧度 (0=平，1=高拱)
    windshield_rake: float = 28.0    # 前挡风倾角 (°)
    rear_glass_angle: float = 32.0   # 后挡风倾角 (°)
    fender_prominence: float = 0.15  # 轮眉突出度
    waist_line: float = 0.85         # 腰线相对高度 (0-1)
    shoulder_line: float = 1.0       # 肩线相对宽度 (0-1)
    overall_arc: float = 0.4         # 整体曲面弧度

    # 玻璃
    glass_darkness: float = 0.35     # 玻璃透射

    # 轮
    wheel_radius: float = 0.34       # 轮半径
    wheel_width: float = 0.22        # 轮宽
    wheel_spoke_count: int = 5       # 辐条数

    # 灯
    headlight_width: float = 0.42    # 大灯宽度
    headlight_height: float = 0.10   # 大灯高度

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dict__}


# ============================================================
# 主车身（车壳）
# ============================================================
def _section_width(x_norm: float, params: CarParams) -> float:
    """车长方向位置 x_norm∈[-1,1] 处的车体半宽（y 方向）"""
    # 楔形：前窄中间宽后稍窄
    p = params.shoulder_line
    # 使用 cos^2 形分布，最大在中后
    base = np.cos(x_norm * np.pi / 2) ** 1.5
    # 前段更修长
    front_factor = 1.0 - 0.15 * max(0, -x_norm)
    rear_factor = 1.0 - 0.08 * max(0, x_norm)
    return params.W / 2 * base * front_factor * rear_factor


def _section_height(x_norm: float, params: CarParams) -> float:
    """车长方向位置 x_norm∈[-1,1] 处的车体高度（z 方向地面到顶）"""
    # 引擎盖：低
    # 前挡风：斜向上
    # 车顶：高
    # 后挡风：斜向下
    # 行李箱：低
    L = params.L
    x = x_norm * L / 2  # 实际位置
    # 各段分界
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
        # 从前保险杠向挡风玻璃底部逐渐升高
        t = (x - (-L/2)) / (front_edge - (-L/2))
        base_h = ground_clear + 0.55 + t * (ground_clear + 0.78 - ground_clear - 0.55)
        return base_h
    elif x < windshield_top:  # 前挡风过渡
        t = (x - front_edge) / max(1e-6, windshield_top - front_edge)
        return (ground_clear + 0.78) + t * (ground_clear + 1.0 - (ground_clear + 0.78))
    elif x < roof_start:  # 座舱前沿
        t = (x - windshield_top) / max(1e-6, roof_start - windshield_top)
        h_start = ground_clear + 1.0
        h_end = params.H - 0.05
        # 加入 roof_arc
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


def _section_shape(x_norm: float, z_norm: float, params: CarParams) -> Tuple[float, float]:
    """
    截面形状：给定 x_norm ∈ [-1,1] 和 z_norm ∈ [0,1]（0=地，1=顶）
    返回 (y_norm, lateral_squish)
    """
    half_w = _section_width(x_norm, params)
    # 上窄下宽的造型
    # 顶部（车顶）稍窄，肩部最宽，底部（保险杠）也稍窄
    p_shoulder = 0.65  # 肩部位置
    # 不对称截面：顶部更尖
    top_factor = 1.0 - 0.10 * (z_norm ** 2)
    if z_norm < p_shoulder:
        # 下半部
        bot_factor = 0.85 + 0.15 * (z_norm / p_shoulder)
    else:
        bot_factor = 1.0 - 0.18 * ((z_norm - p_shoulder) / (1 - p_shoulder))
    y = half_w * top_factor * bot_factor
    return y, 1.0


def build_body(params: CarParams, n_long: int = 48, n_circ: int = 24) -> trimesh.Trimesh:
    """构建主车身壳体（包含左右对称的完整外壳）"""
    verts: List[List[float]] = []
    faces: List[List[int]] = []

    # 沿车长方向取截面
    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2
        for j in range(n_circ + 1):
            z_norm = j / n_circ
            z_local = _section_height(x_norm, params)
            z = z_local  # 已经是世界坐标
            y, _ = _section_shape(x_norm, z_norm, params)
            verts.append([x, y, z])
            # 对称侧
            verts.append([x, -y, z])

    # 生成面
    # 每条长向线有 2*(n_circ+1) 个点（左右对称）
    cols = 2 * (n_circ + 1)
    for i in range(n_long):
        for j in range(n_circ):
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

            # 左侧两个三角形
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])
            # 右侧两个三角形（法向相反）
            faces.append([w00, w11, w10])
            faces.append([w00, w01, w11])

    # 顶盖（封闭）
    last_row = n_long * cols
    # 车顶中央线
    center_top_v = len(verts)
    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2
        z_top = _section_height(x_norm, params)
        verts.append([x, 0, z_top])
    # 把每段车顶的左右两个点与中心点连接
    # 但其实车顶本身就是最高点了，先不封顶（trimesh 不要求封闭）
    # 反而底部需要封（地面）
    # 我们先生成底面
    bottom_faces: List[List[int]] = []
    n_bottom = 2 * (n_circ + 1)
    # 找底部的 z 最低点（z_norm=0）
    # 由于 j=0 是 z_norm=0
    # 沿车长方向, 底部一圈, 中心点
    bottom_center = len(verts)
    for i in range(n_long + 1):
        x_norm = -1 + 2 * i / n_long
        x = x_norm * params.L / 2
        # 底部高度
        z_bot = min(_section_height(x_norm, params) for _ in [None])  # 简单起见取 ground_clear
        z_bot = params.ground_clearance + 0.18  # 保险杠底部
        verts.append([x, 0, z_bot])

    mesh = trimesh.Trimesh(
        vertices=np.array(verts, dtype=np.float64),
        faces=np.array(faces, dtype=np.int64),
        process=True,
    )
    # 设置视觉属性
    mesh.visual.face_colors = [200, 30, 40, 255]  # 经典红
    return mesh


# ============================================================
# 玻璃区域
# ============================================================
def build_glass(params: CarParams, n_long: int = 20, n_vert: int = 8) -> trimesh.Trimesh:
    """构建车窗玻璃（前挡风+车顶天窗+后挡风+侧窗）"""
    pieces: List[trimesh.Trimesh] = []

    # 1) 前挡风
    x_front_bottom = -params.L/2 + params.hood_length
    x_front_top = x_front_bottom + 0.55
    z_bottom = params.ground_clearance + 0.78
    z_top = params.H - 0.08
    rake = np.radians(params.windshield_rake)
    fw_verts = []
    for j in range(n_vert + 1):
        t = j / n_vert
        z = z_bottom + t * (z_top - z_bottom)
        x_offset = t * np.tan(rake) * (z_top - z_bottom)
        x = x_front_bottom + x_offset
        half_w_top = _section_width(x / (params.L/2), params) * 0.92
        fw_verts.append([x, -half_w_top, z])
        fw_verts.append([x, half_w_top, z])
    fw_faces = []
    for j in range(n_vert):
        v0 = 2 * j
        v1 = 2 * j + 1
        v2 = 2 * (j + 1)
        v3 = 2 * (j + 1) + 1
        fw_faces.append([v0, v2, v3])
        fw_faces.append([v0, v3, v1])
    fw = trimesh.Trimesh(vertices=np.array(fw_verts), faces=np.array(fw_faces))
    pieces.append(fw)

    # 2) 后挡风
    x_rear_top = params.L/2 - params.trunk_length - 0.55
    x_rear_bottom = x_rear_top + 0.55
    rw_verts = []
    for j in range(n_vert + 1):
        t = j / n_vert
        z = z_top - t * (z_top - (params.ground_clearance + 0.7))
        x_offset = -t * np.tan(np.radians(params.rear_glass_angle)) * (z_top - (params.ground_clearance + 0.7))
        x = x_rear_top + x_offset
        half_w_top = _section_width(x / (params.L/2), params) * 0.92
        rw_verts.append([x, -half_w_top, z])
        rw_verts.append([x, half_w_top, z])
    rw_faces = []
    for j in range(n_vert):
        v0 = 2 * j
        v1 = 2 * j + 1
        v2 = 2 * (j + 1)
        v3 = 2 * (j + 1) + 1
        rw_faces.append([v0, v2, v3])
        rw_faces.append([v0, v3, v1])
    rw = trimesh.Trimesh(vertices=np.array(rw_verts), faces=np.array(rw_faces))
    pieces.append(rw)

    # 3) 车顶天窗（中央矩形玻璃）
    roof_x_start = -params.L/2 + params.hood_length + 0.7
    roof_x_end = params.L/2 - params.trunk_length - 0.7
    sun_verts = []
    n_sun_long = 10
    n_sun_wide = 6
    half_roof_w = params.W / 2 * 0.78
    for i in range(n_sun_long + 1):
        t = i / n_sun_long
        x = roof_x_start + t * (roof_x_end - roof_x_start)
        for j in range(n_sun_wide + 1):
            s = j / n_sun_wide
            y = -half_roof_w + s * (2 * half_roof_w)
            z = params.H - 0.06
            sun_verts.append([x, y, z])
    sun_faces = []
    for i in range(n_sun_long):
        for j in range(n_sun_wide):
            v00 = i * (n_sun_wide + 1) + j
            v10 = (i + 1) * (n_sun_wide + 1) + j
            v01 = i * (n_sun_wide + 1) + (j + 1)
            v11 = (i + 1) * (n_sun_wide + 1) + (j + 1)
            sun_faces.append([v00, v10, v11])
            sun_faces.append([v00, v11, v01])
    sun = trimesh.Trimesh(vertices=np.array(sun_verts), faces=np.array(sun_faces))
    pieces.append(sun)

    # 合并
    glass = trimesh.util.concatenate(pieces)
    d = int(255 * (1 - params.glass_darkness))
    glass.visual.face_colors = [40, 60, d, 220]  # 深蓝玻璃
    return glass


# ============================================================
# 车轮
# ============================================================
def build_wheel(params: CarParams, side: str = "left") -> trimesh.Trimesh:
    """单个车轮 - 包含轮胎+多辐条轮毂"""
    parts: List[trimesh.Trimesh] = []
    R = params.wheel_radius
    W = params.wheel_width

    # 轮胎
    tire = trimesh.creation.cylinder(radius=R, height=W, sections=48)
    # 旋转使轴沿 y
    rot = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
    tire.apply_transform(rot)
    # 轮胎深色
    tire.visual.face_colors = [25, 25, 30, 255]

    # 轮毂中心
    hub = trimesh.creation.cylinder(radius=R * 0.18, height=W * 1.05, sections=16)
    hub.apply_transform(rot)
    hub.visual.face_colors = [180, 180, 190, 255]

    # 辐条
    for k in range(params.wheel_spoke_count):
        angle = 2 * np.pi * k / params.wheel_spoke_count
        spoke = trimesh.creation.box(extents=[R * 0.85, W * 0.6, R * 0.10])
        rot_angle = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
        spoke.apply_transform(rot_angle)
        # 居中
        spoke.apply_translation([R * 0.42, 0, 0])
        rot_y = trimesh.transformations.rotation_matrix(np.pi/2, [1, 0, 0])
        spoke.apply_transform(rot_y)
        spoke.visual.face_colors = [200, 200, 215, 255]
        parts.append(spoke)

    parts.append(tire)
    parts.append(hub)
    wheel = trimesh.util.concatenate(parts)
    return wheel


def build_wheels(params: CarParams) -> trimesh.Trimesh:
    """4 个轮子放置在正确位置"""
    wheels: List[trimesh.Trimesh] = []
    R = params.wheel_radius
    wb_half = params.wheelbase / 2
    wheel_y = params.W / 2 - 0.05
    wheel_z = R + 0.02
    x_positions = [-wb_half, wb_half]
    y_positions = [wheel_y, -wheel_y]

    for x in x_positions:
        for y in y_positions:
            w = build_wheel(params)
            w.apply_translation([x, y, wheel_z])
            wheels.append(w)
    return trimesh.util.concatenate(wheels)


# ============================================================
# 大灯/尾灯
# ============================================================
def build_headlights(params: CarParams) -> trimesh.Trimesh:
    """前大灯组（左右各一）"""
    parts: List[trimesh.Trimesh] = []
    hw = params.headlight_width
    hh = params.headlight_height
    hd = 0.05
    z = params.ground_clearance + 0.65
    x = -params.L/2 + 0.10

    for y_side in [params.W/2 - hw/2 - 0.05, -params.W/2 + hw/2 + 0.05]:
        lamp = trimesh.creation.box(extents=[hd, hw, hh])
        lamp.apply_translation([x, y_side, z])
        # 灯罩
        lamp.visual.face_colors = [240, 250, 255, 255]
        parts.append(lamp)
        # 内侧 LED 灯带
        led = trimesh.creation.box(extents=[hd * 1.1, hw * 0.85, hh * 0.3])
        led.apply_translation([x + 0.005, y_side, z])
        led.visual.face_colors = [255, 240, 200, 255]
        parts.append(led)
    return trimesh.util.concatenate(parts)


def build_taillights(params: CarParams) -> trimesh.Trimesh:
    """尾灯（左右各一）"""
    parts: List[trimesh.Trimesh] = []
    tw = 0.35
    th = 0.10
    td = 0.05
    z = params.ground_clearance + 0.70
    x = params.L/2 - 0.10

    for y_side in [params.W/2 - tw/2 - 0.05, -params.W/2 + tw/2 + 0.05]:
        lamp = trimesh.creation.box(extents=[td, tw, th])
        lamp.apply_translation([x, y_side, z])
        lamp.visual.face_colors = [200, 30, 50, 255]
        parts.append(lamp)
        # LED 条
        led = trimesh.creation.box(extents=[td * 1.1, tw * 0.9, th * 0.4])
        led.apply_translation([x + 0.005, y_side, z])
        led.visual.face_colors = [255, 100, 120, 255]
        parts.append(led)
    return trimesh.util.concatenate(parts)


# ============================================================
# 进气格栅
# ============================================================
def build_grille(params: CarParams) -> trimesh.Trimesh:
    """前脸进气格栅"""
    parts: List[trimesh.Trimesh] = []
    # 梯形格栅框
    x = -params.L/2 + 0.02
    w_top = 0.6
    w_bot = 0.9
    h = 0.18
    z_center = params.ground_clearance + 0.30
    # 用 box 简化
    grille = trimesh.creation.box(extents=[0.04, (w_top + w_bot)/2, h])
    grille.apply_translation([x, 0, z_center])
    grille.visual.face_colors = [30, 30, 35, 255]
    parts.append(grille)

    # 横向格栅条
    n_bars = 5
    for k in range(n_bars):
        bar = trimesh.creation.box(extents=[0.06, (w_top + w_bot)/2 * 0.92, 0.012])
        z_offset = (k - (n_bars-1)/2) * (h * 0.85 / n_bars)
        bar.apply_translation([x + 0.02, 0, z_center + z_offset])
        bar.visual.face_colors = [180, 185, 195, 255]
        parts.append(bar)
    return trimesh.util.concatenate(parts)


# ============================================================
# 后视镜
# ============================================================
def build_mirrors(params: CarParams) -> trimesh.Trimesh:
    """左右后视镜"""
    parts: List[trimesh.Trimesh] = []
    mirror_x = -params.L/2 + params.hood_length + 0.18
    mirror_y = params.W/2 + 0.04
    mirror_z = params.ground_clearance + 1.05

    for y_sign in [1, -1]:
        # 底座
        base = trimesh.creation.box(extents=[0.05, 0.05, 0.05])
        base.apply_translation([mirror_x, y_sign * mirror_y, mirror_z])
        base.visual.face_colors = [40, 40, 45, 255]
        parts.append(base)
        # 镜壳
        shell = trimesh.creation.box(extents=[0.12, 0.18, 0.07])
        shell.apply_translation([mirror_x, y_sign * (mirror_y + 0.10), mirror_z])
        shell.visual.face_colors = [200, 30, 40, 255]
        parts.append(shell)
    return trimesh.util.concatenate(parts)


# ============================================================
# 车门分缝线（线段）
# ============================================================
def build_door_seams(params: CarParams) -> trimesh.Trimesh:
    """车门分缝线（4 条门缝 + 后备箱缝）"""
    parts: List[trimesh.Trimesh] = []
    z_seam = params.ground_clearance + (params.H - params.ground_clearance) * params.waist_line
    # 4 条车门缝
    door_xs = [
        -params.L/2 + params.hood_length + 0.50,   # 前门缝
        -params.L/2 + params.hood_length + 1.10,   # 中门缝
        -params.L/2 + params.hood_length + 1.70,   # 后门缝
    ]
    for x in door_xs:
        for y_side in [params.W/2 - 0.005, -params.W/2 + 0.005]:
            line = trimesh.creation.box(extents=[0.005, 0.01, 0.6])
            line.apply_translation([x, y_side, z_seam])
            line.visual.face_colors = [10, 10, 15, 255]
            parts.append(line)
    return trimesh.util.concatenate(parts) if parts else trimesh.Trimesh()


# ============================================================
# 完整汽车组装
# ============================================================
def build_full_car(params: CarParams) -> Dict[str, Any]:
    """组装完整汽车造型，返回各部件 mesh 字典"""
    body = build_body(params)
    glass = build_glass(params)
    wheels = build_wheels(params)
    headlights = build_headlights(params)
    taillights = build_taillights(params)
    grille = build_grille(params)
    mirrors = build_mirrors(params)
    seams = build_door_seams(params)

    return {
        "body": body,
        "glass": glass,
        "wheels": wheels,
        "headlights": headlights,
        "taillights": taillights,
        "grille": grille,
        "mirrors": mirrors,
        "seams": seams,
    }


def compute_stats(parts: Dict[str, trimesh.Trimesh]) -> Dict[str, Any]:
    """计算整车统计信息"""
    total_verts = sum(len(m.vertices) for m in parts.values())
    total_faces = sum(len(m.faces) for m in parts.values())
    return {
        "total_vertices": total_verts,
        "total_faces": total_faces,
        "body_vertices": len(parts["body"].vertices),
        "wheels_vertices": len(parts["wheels"].vertices),
        "components": list(parts.keys()),
    }


if __name__ == "__main__":
    # 自检
    p = CarParams()
    parts = build_full_car(p)
    stats = compute_stats(parts)
    print("=== 完整汽车自检 ===")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for name, mesh in parts.items():
        print(f"{name}: {len(mesh.vertices)} verts, {len(mesh.faces)} faces, "
              f"bounds={mesh.bounds.tolist()}")
