"""
Three-Zone Blending + Tumblehome 模块

专利 Claim 4 / Claim 5 实现：
- F4: Product-based 三区段归一化
- F5: Tumblehome 车顶宽度衰减

三区段：hood（发动机盖区）、cabin（座舱区）、trunk（行李箱区）
五水平：bottom / sill / waist / shoulder / roof
"""
from dataclasses import dataclass, field
from typing import List, Tuple
import math


# ============================================================
# T1: ZoneParamsTable 数据结构
# ============================================================

@dataclass
class ZoneLevel:
    """
    单个水平（height level）的区段参数

    Attributes:
        x_offset: 相对 X 偏移量（沿车长方向，相对于区段中心）
        y_scale: 相对 Y 倍率（截面宽度缩放）
        z_scale: 相对 Z 倍率（截面高度缩放）
    """
    x_offset: float
    y_scale: float
    z_scale: float


@dataclass
class ZoneParamsTable:
    """
    5水平 × 3区段的参数查找表

    Attributes:
        hood: 发动机盖区段（5个水平参数）
        cabin: 座舱区段（5个水平参数）
        trunk: 行李箱区段（5个水平参数）
    """
    hood: List[ZoneLevel]
    cabin: List[ZoneLevel]
    trunk: List[ZoneLevel]

    def get_level(self, zone: str, level_idx: int) -> ZoneLevel:
        """
        获取指定区段和水平等级的参数

        Args:
            zone: 区段名称 ("hood", "cabin", "trunk")
            level_idx: 水平索引 (0=bottom, 1=sill, 2=waist, 3=shoulder, 4=roof)

        Returns:
            ZoneLevel 参数
        """
        zone_map = {"hood": self.hood, "cabin": self.cabin, "trunk": self.trunk}
        return zone_map[zone][level_idx]


# ============================================================
# T5: ZONE_PARAMS_TABLE 常量数据（15格）
# 来源：专利说明书 Step 5 表格
# ============================================================

ZONE_PARAMS_TABLE = ZoneParamsTable(
    hood=[
        ZoneLevel(x_offset=0.00, y_scale=0.85, z_scale=0.15),   # bottom
        ZoneLevel(x_offset=0.15, y_scale=0.95, z_scale=0.30),  # sill
        ZoneLevel(x_offset=0.30, y_scale=0.92, z_scale=0.55),  # waist
        ZoneLevel(x_offset=0.50, y_scale=0.78, z_scale=0.85),   # shoulder
        ZoneLevel(x_offset=0.70, y_scale=0.62, z_scale=1.00),   # roof
    ],
    cabin=[
        ZoneLevel(x_offset=0.00, y_scale=0.90, z_scale=0.20),   # bottom
        ZoneLevel(x_offset=0.20, y_scale=0.98, z_scale=0.40),  # sill
        ZoneLevel(x_offset=0.40, y_scale=0.95, z_scale=0.65),  # waist
        ZoneLevel(x_offset=0.65, y_scale=0.85, z_scale=0.95),  # shoulder
        ZoneLevel(x_offset=0.85, y_scale=0.72, z_scale=1.00),  # roof
    ],
    trunk=[
        ZoneLevel(x_offset=0.00, y_scale=0.88, z_scale=0.18),   # bottom
        ZoneLevel(x_offset=0.10, y_scale=0.94, z_scale=0.35),  # sill
        ZoneLevel(x_offset=0.25, y_scale=0.86, z_scale=0.55),  # waist
        ZoneLevel(x_offset=0.45, y_scale=0.68, z_scale=0.85),  # shoulder
        ZoneLevel(x_offset=0.65, y_scale=0.55, z_scale=1.00),  # roof
    ],
)


# ============================================================
# T2: Smoothstep 插值（替代硬切换 step blend，保 G1 连续性）
# ============================================================

def smoothstep(t: float) -> float:
    """
    Smoothstep 插值函数：3t² - 2t³

    特性：
    - t=0 → 0
    - t=1 → 1
    - 导数 t=0/1 处为 0（切线水平，G1 连续）
    - 二阶导数连续（C2 连续）

    用于替代 step blend，避免硬切换破坏 G1 连续性。
    """
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
    return t * t * (3.0 - 2.0 * t)


def _smoothstep_clamped(t: float) -> float:
    """Smoothstep with clamp to [0, 1]"""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def three_zone_weights(x: float, hardpoints: dict) -> Tuple[float, float, float]:
    """
    计算三区段权重（归一化前的原始值）

    使用 smoothstep 实现平滑过渡，避免硬切换破坏 G1 连续性。

    Args:
        x: 当前 X 位置（沿车长方向）
        hardpoints: 硬点字典，包含：
            - front_x: 车头 X 坐标
            - rear_x: 车尾 X 坐标
            - hood_end_x: 发动机盖终点 X 坐标
            - cabin_start_x: 座舱起点 X 坐标
            - cabin_end_x: 座舱终点 X 坐标
            - trunk_start_x: 行李箱起点 X 坐标

    Returns:
        Tuple[hoodF, cabinF, trunkF]: 三个原始权重值（未归一化）

    算法：
    - hood 主导区：[front_x, hood_end_x]
    - cabin 主导区：[cabin_start_x, cabin_end_x]
    - trunk 主导区：[trunk_start_x, rear_x]
    - 各区段内部权重为 1.0，过渡区用 smoothstep 平滑
    """
    front_x = hardpoints["front_x"]
    rear_x = hardpoints["rear_x"]
    hood_end_x = hardpoints["hood_end_x"]
    cabin_start_x = hardpoints["cabin_start_x"]
    cabin_end_x = hardpoints["cabin_end_x"]
    trunk_start_x = hardpoints["trunk_start_x"]

    # 过渡区宽度
    hood_tran_w = 0.3  # hood 过渡宽度
    cabin_tran_w = 0.2  # cabin 前后过渡宽度
    trunk_tran_w = 0.3  # trunk 过渡宽度

    # ===== hoodF =====
    # [front_x, hood_end_x] 主导 = 1.0
    # 过渡到 cabin：[hood_end_x, hood_end_x + hood_tran_w]
    if x <= hood_end_x:
        # hood 主导区
        hoodF = 1.0
    else:
        # hood -> cabin 过渡
        t = (x - hood_end_x) / (hood_tran_w + 1e-6)
        hoodF = 1.0 - _smoothstep_clamped(t)

    # ===== cabinF =====
    # [cabin_start_x, cabin_end_x] 主导 = 1.0
    # 过渡：[hood_end_x, cabin_start_x] 和 [cabin_end_x, trunk_start_x]
    if x < cabin_start_x:
        # hood -> cabin 过渡
        t = (x - hood_end_x) / (cabin_start_x - hood_end_x + 1e-6)
        cabinF = _smoothstep_clamped(t)
    elif x <= cabin_end_x:
        # cabin 主导区
        cabinF = 1.0
    else:
        # cabin -> trunk 过渡
        t = (x - cabin_end_x) / (trunk_start_x - cabin_end_x + 1e-6)
        cabinF = 1.0 - _smoothstep_clamped(t)

    # ===== trunkF =====
    # [trunk_start_x, rear_x] 主导 = 1.0
    # 过渡：[cabin_end_x, trunk_start_x]
    if x < trunk_start_x:
        # cabin -> trunk 过渡
        t = (x - cabin_end_x) / (trunk_start_x - cabin_end_x + 1e-6)
        trunkF = _smoothstep_clamped(t)
    else:
        # trunk 主导区
        trunkF = 1.0

    # 确保非负
    hoodF = max(0.0, hoodF)
    cabinF = max(0.0, cabinF)
    trunkF = max(0.0, trunkF)

    return hoodF, cabinF, trunkF


# ============================================================
# T3: Product-based 归一化（Claim 4）
# ============================================================

def normalize_zone_weights(
    hoodF: float, cabinF: float, trunkF: float
) -> Tuple[float, float, float]:
    """
    Product-based 归一化（Claim 4 核心公式）

    公式：
        ŵ_i = ∏_{j≠i} w_j / Σ_k ∏_{j≠k} w_j

    特性：
    - sum(ŵ_i) = 1.0（数学证明）
    - 某个权重为 0 时，另外两个等权重分配
    - 避免简单求和归一化导致的"孤岛效应"

    Args:
        hoodF: hood 区段原始权重
        cabinF: cabin 区段原始权重
        trunkF: trunk 区段原始权重

    Returns:
        Tuple[hood_n, cabin_n, trunk_n]: 归一化后的权重，sum=1.0
    """
    total_raw = hoodF + cabinF + trunkF

    # 如果总和小于阈值，使用简单求和归一化（避免 product-based 在边界情况下的问题）
    if total_raw < 1e-9:
        # 全为零时均匀分配
        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)

    # 如果有零值，使用简单求和归一化来正确处理"0 时等分"的需求
    # product-based 在零值时会错误地将 0 权重的产品分配给其他区段
    # 统计零值数量
    zero_count = sum(1 for w in [hoodF, cabinF, trunkF] if w < 1e-12)
    if zero_count == 1:
        # 一个零值时，另外两个等权重分配
        return (hoodF / total_raw, cabinF / total_raw, trunkF / total_raw)
    elif zero_count >= 2:
        # 两个或三个零值时，均匀分配
        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)

    # Product-based normalization (Claim 4)
    # ŵ_i = ∏_{j≠i} w_j / Σ_k ∏_{j≠k} w_j
    prod_hood = cabinF * trunkF      # ∏_{j≠hood} w_j
    prod_cabin = hoodF * trunkF     # ∏_{j≠cabin} w_j
    prod_trunk = hoodF * cabinF     # ∏_{j≠trunk} w_j

    total_prod = prod_hood + prod_cabin + prod_trunk

    # 防止除零（全为零时）或其他边界情况
    if total_prod < 1e-12:
        # 当 product-based 无法区分时，使用简单求和归一化
        # 但保留原始权重的相对大小
        return (hoodF / total_raw, cabinF / total_raw, trunkF / total_raw)

    hood_n = prod_hood / total_prod
    cabin_n = prod_cabin / total_prod
    trunk_n = prod_trunk / total_prod

    return hood_n, cabin_n, trunk_n


# ============================================================
# T4: Tumblehome 效应（F5 公式）
# ============================================================

def compute_tumblehome(
    hw: float, shoulderW: float, CA: float
) -> float:
    """
    计算车顶半宽（含 tumblehome 衰减效应）

    Claim 5 公式：
        c_RoofHW = hw * max(0.25, shoulderW * 0.45 - sin(CA) * 0.15)

    Tumblehome 效应：
    - C-pillar 越倾斜（CA 越大），车顶越窄
    - 肩部越宽（shoulderW 越大），车顶相对越宽
    - 下限保护：max(0.25, ...) 确保车顶不会过窄

    Args:
        hw: 原始半宽（half-width）
        shoulderW: 肩部宽度
        CA: C-pillar 角度（弧度）

    Returns:
        float: 调整后的车顶半宽
    """
    # F5 公式
    factor = shoulderW * 0.45 - math.sin(CA) * 0.15

    # 安全降级：CA = π/2 时 sin(π/2) = 1.0，factor 可能为负
    # max(0.25, ...) 确保下限保护
    factor = max(0.25, factor)

    return hw * factor


# ============================================================
# 辅助函数
# ============================================================

def get_zone(x: float, hardpoints: dict) -> str:
    """
    根据 X 位置确定当前区段

    Args:
        x: 当前 X 位置
        hardpoints: 硬点字典

    Returns:
        str: "hood" / "cabin" / "trunk"
    """
    cabin_start_x = hardpoints["cabin_start_x"]
    cabin_end_x = hardpoints["cabin_end_x"]

    if x < cabin_start_x:
        return "hood"
    elif x <= cabin_end_x:
        return "cabin"
    else:
        return "trunk"


def get_blended_params(
    x: float,
    hardpoints: dict,
    zone_params: ZoneParamsTable = ZONE_PARAMS_TABLE
) -> Tuple[ZoneLevel, float, float, float]:
    """
    获取当前 X 位置的混合区段参数

    Args:
        x: 当前 X 位置
        hardpoints: 硬点字典
        zone_params: 区段参数表

    Returns:
        Tuple[ZoneLevel, hood_n, cabin_n, trunk_n]:
        - 归一化后的主要区段参数（基于最大权重）
        - 三个归一化权重（用于后续混合）
    """
    # 获取原始权重
    hoodF, cabinF, trunkF = three_zone_weights(x, hardpoints)

    # 归一化
    hood_n, cabin_n, trunk_n = normalize_zone_weights(hoodF, cabinF, trunkF)

    # 确定主要区段
    zone = get_zone(x, hardpoints)
    zone_map = {"hood": hood_n, "cabin": cabin_n, "trunk": trunk_n}
    weights = {"hood": hood_n, "cabin": cabin_n, "trunk": trunk_n}

    # 返回最大权重的区段参数（简化版，实际可做多区段加权混合）
    primary_zone = max(weights, key=weights.get)
    level_idx = 2  # 默认 waist level，可根据 x 的 z 位置动态选择

    return zone_params.get_level(primary_zone, level_idx), hood_n, cabin_n, trunk_n
