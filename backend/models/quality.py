"""
Quality 相关 Pydantic 模型（字段对齐 algorithm_model）
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class QualityAssessRequest(BaseModel):
    """曲面评估请求"""
    points: List[List[List[float]]] = Field(..., description="3D 点阵 (N, M, 3)")
    panel_name: str = Field(default="panel", description="面板名称")


class QualityAssessResponse(BaseModel):
    """曲面评估响应（字段对齐 QualityReport）"""
    panel_name: str
    grade: str  # A/B/C/D
    g0_count: int
    g1_count: int
    g2_count: int
    g1_ratio: float
    g2_ratio: float
    max_curvature_jump: float
    mean_curvature: float
    reflection_score: float
    details: Dict[str, Any] = {}


class QualityPresetRequest(BaseModel):
    """预设曲面评估请求"""
    shape: str = Field(..., description="sphere | plane | cylinder | car_body")
    resolution: int = Field(default=20, ge=5, le=50)
