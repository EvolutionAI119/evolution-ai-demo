"""
CarParams - 整车级参数定义

22 维参数控制完整汽车造型：
- 基础尺寸 (4): 车长 L / 车宽 W / 车高 H / 轴距 wheelbase
- 比例姿态 (4): 发动机盖长 / 座舱长 / 行李箱长 / 离地间隙
- 曲面特征 (7): 机盖角度 / 车顶弧度 / 前挡风倾角 / 后挡风倾角 / 轮眉突出 / 腰线 / 肩线
- 整体形状 (1): 整体弧度
- 玻璃 (1): 玻璃透射
- 轮 (3): 轮半径 / 轮宽 / 辐条数
- 灯 (2): 大灯宽度 / 大灯高度
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List


# 参数边界定义
PARAM_BOUNDS = {
    "L": (3.5, 5.5),                    # m
    "W": (1.6, 2.1),
    "H": (1.25, 1.65),
    "wheelbase": (2.3, 3.2),
    "hood_length": (0.7, 1.5),
    "cabin_length": (1.6, 2.6),
    "trunk_length": (0.5, 1.4),
    "ground_clearance": (0.12, 0.25),
    "hood_angle": (5.0, 25.0),          # 度
    "roof_arc": (0.0, 0.8),
    "windshield_rake": (20.0, 40.0),    # 度
    "rear_glass_angle": (25.0, 45.0),   # 度
    "fender_prominence": (0.0, 0.35),
    "waist_line": (0.65, 0.95),
    "shoulder_line": (0.85, 1.15),
    "overall_arc": (0.0, 0.7),
    "glass_darkness": (0.1, 0.7),
    "wheel_radius": (0.28, 0.40),
    "wheel_width": (0.18, 0.28),
    "wheel_spoke_count": (3, 10),
    "headlight_width": (0.30, 0.55),
    "headlight_height": (0.06, 0.16),
}


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
        """转字典"""
        return {k: getattr(self, k) for k in self.__dict__}

    def validate(self) -> List[str]:
        """
        参数合法性校验

        Returns:
            错误信息列表（空表示通过）
        """
        errors = []
        for k, (lo, hi) in PARAM_BOUNDS.items():
            v = getattr(self, k)
            if v < lo or v > hi:
                errors.append(f"{k}={v} 超出合理范围 [{lo}, {hi}]")
        # 内部一致性
        if self.hood_length + self.cabin_length + self.trunk_length > self.L * 1.2:
            errors.append("三段长度之和超过车长合理范围")
        if self.H <= self.ground_clearance + 0.5:
            errors.append("车高过低（去除离地间隙后不足 0.5m）")
        return errors

    def to_json(self) -> str:
        """转 JSON 字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CarParams":
        """从字典构造"""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
