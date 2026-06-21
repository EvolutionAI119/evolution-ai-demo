"""
Car 相关 Pydantic 模型
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


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
