"""
Car 相关 Pydantic 模型
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, model_validator


class FreeformPreset(str, Enum):
    """自由变形预设类型"""
    fender_bulge = "fender_bulge"      # 轮眉凸起
    door_dent = "door_dent"            # 门板凹痕
    hood_scoop = "hood_scoop"          # 发动机盖进气口
    character_line = "character_line"  # 腰线特征线
    roof_sculpt = "roof_sculpt"        # 车顶雕塑感
    custom = "custom"                  # 自定义控制点


class FreeformParams(BaseModel):
    """
    自由变形参数

    在车身网格上施加 NURBS 曲面变形，支持 5 种预设 + 自定义模式。
    """
    preset: FreeformPreset = Field(
        ...,
        description="变形预设类型，custom 模式需提供 custom_control_points",
    )
    amplitude: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="变形幅度 0.0-1.0，缩放预设/自定义变形的强度",
    )
    center_x: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="变形中心 X 坐标（归一化 -1.0~1.0，对应车尾到车头）",
    )
    center_z: float = Field(
        default=0.5,
        ge=-1.0,
        le=1.0,
        description="变形中心 Z 坐标（归一化 -1.0~1.0，对应车底到车顶）",
    )
    custom_control_points: Optional[List[List[float]]] = Field(
        default=None,
        description="自定义控制点网格（仅 custom 模式），二维数组 [[z00, z01, ...], ...]",
    )

    @model_validator(mode="after")
    def validate_custom_mode(self) -> "FreeformParams":
        """custom 模式必须提供 custom_control_points"""
        if self.preset == FreeformPreset.custom and not self.custom_control_points:
            raise ValueError("custom 模式必须提供 custom_control_points")
        if self.preset != FreeformPreset.custom and self.custom_control_points:
            raise ValueError("非 custom 模式不应提供 custom_control_points")
        return self


class CarParamsAPI(BaseModel):
    """22 维 CarParams API 形态 - 完整参数"""
    # 基础尺寸
    L: float = Field(default=4.7, ge=3.5, le=5.5, description="车长 m")
    W: float = Field(default=1.85, ge=1.6, le=2.1, description="车宽 m")
    H: float = Field(default=1.45, ge=1.25, le=1.85, description="车高 m（SUV 放宽到 1.85）")
    wheelbase: float = Field(default=2.8, ge=2.3, le=3.2, description="轴距 m")

    # 比例姿态
    hood_length: float = Field(default=1.1, ge=0.7, le=1.5)
    cabin_length: float = Field(default=2.2, ge=1.6, le=2.6)
    trunk_length: float = Field(default=1.0, ge=0.5, le=1.4)
    ground_clearance: float = Field(default=0.18, ge=0.12, le=0.25)

    # 曲面特征
    hood_angle: float = Field(default=12.0, ge=5.0, le=25.0)
    roof_arc: float = Field(default=0.35, ge=0.0, le=0.8)
    windshield_rake: float = Field(default=30.0, ge=20.0, le=40.0)
    rear_glass_angle: float = Field(default=35.0, ge=25.0, le=45.0)
    fender_prominence: float = Field(default=0.15, ge=0.0, le=0.35)
    waist_line: float = Field(default=0.8, ge=0.65, le=0.95)
    shoulder_line: float = Field(default=1.0, ge=0.85, le=1.15)

    # 整体
    overall_arc: float = Field(default=0.2, ge=0.0, le=0.7)

    # 玻璃
    glass_darkness: float = Field(default=0.4, ge=0.1, le=0.7)

    # 轮
    wheel_radius: float = Field(default=0.34, ge=0.28, le=0.40)
    wheel_width: float = Field(default=0.22, ge=0.18, le=0.28)
    wheel_spoke_count: int = Field(default=5, ge=3, le=10)

    # 灯
    headlight_width: float = Field(default=0.42, ge=0.30, le=0.55)
    headlight_height: float = Field(default=0.10, ge=0.06, le=0.16)

    def to_car_params(self):
        """转 algorithm_model 的 CarParams dataclass"""
        from algorithm_model.car_modeling import CarParams
        return CarParams(**self.model_dump())


class CarStatsAPI(BaseModel):
    """整车统计信息（对齐 compute_stats 真实返回）"""
    total_vertices: int
    total_faces: int
    components: Dict[str, Dict[str, Any]]  # {part_name: {vertices, faces, color}}
    bounds: List[List[float]]  # [[xmin, ymin, zmin], [xmax, ymax, zmax]]


class CarBuildResponse(BaseModel):
    """build 接口响应"""
    glb_url: str
    stats: CarStatsAPI
    params_hash: str
    build_time_ms: float
    freeform_applied: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="已应用的自由变形摘要（无 freeform 参数时为 None）",
    )


class CarBuildRequest(BaseModel):
    """build 接口请求（向后兼容：body 可直接传 CarParamsAPI 字段，也可嵌套 params + freeform）"""
    params: Optional[CarParamsAPI] = Field(
        default=None,
        description="22 维形态参数（不传则使用默认值）",
    )
    freeform: Optional[FreeformParams] = Field(
        default=None,
        description="可选自由变形参数",
    )


class CarValidateRequest(BaseModel):
    """validate 接口请求"""
    params: CarParamsAPI


class CarValidateResponse(BaseModel):
    """validate 接口响应"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class CarPreset(BaseModel):
    """预设方案"""
    name: str
    description: str
    params: CarParamsAPI
    icon: Optional[str] = None

class ExportFormat(str, Enum):
    """模型导出格式"""
    glb = "glb"
    obj = "obj"
    stl = "stl"


class CarExportRequest(BaseModel):
    """export 接口请求 — 构建并导出为指定格式"""
    params: Optional[CarParamsAPI] = Field(
        default=None,
        description="22 维形态参数（不传则使用默认值）",
    )
    freeform: Optional[FreeformParams] = Field(
        default=None,
        description="可选自由变形参数",
    )
    format: ExportFormat = Field(
        default=ExportFormat.glb,
        description="导出格式：glb / obj / stl",
    )


class CarExportResponse(BaseModel):
    """export 接口响应"""
    file_url: str
    format: str
    file_size_bytes: int
    build_time_ms: float