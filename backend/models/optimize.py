"""
Optimize 相关 Pydantic 模型（字段对齐 algorithm_model）
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    """优化请求"""
    points: List[List[List[float]]] = Field(..., description="3D 点阵 (N, M, 3)")
    panel_name: str = Field(default="panel")
    max_iter: int = Field(default=80, ge=10, le=500)
    seed: int = Field(default=42, ge=0)


class OptimizeResponse(BaseModel):
    """优化响应（对齐 OptimizationResult 字段）"""
    task_id: str
    panel_name: str
    initial_grade: str
    final_grade: str
    initial_g2_count: int  # 字段对齐 g2_count
    final_g2_count: int
    initial_reflection: float
    final_reflection: float
    improvement: float  # g2 count 差值
    iterations: int
    elapsed_seconds: float
    convergence_curve: List[float] = []  # 目标函数值历史（单值 List）
    optimized_points: Optional[List[List[List[float]]]] = None


class OptimizePresetRequest(BaseModel):
    """预设曲面优化请求"""
    shape: str = Field(..., description="sphere | plane_with_noise | car_body")
    max_iter: int = Field(default=80, ge=10, le=300)
    seed: int = Field(default=42, ge=0)



# ==================== M2 异步请求模型 ====================

class OptimizeStartRequest(BaseModel):
    """异步优化请求（M2 新增）。

    与 OptimizeRequest 的区别：
    - 不要 points 字段（surface_type 指定即可，由后端构造初始曲面）
    - 多 project_id 字段（任务可关联到具体方案）
    """
    panel_name: str = Field(default="panel", description="面板名称")
    surface_type: str = Field(
        default="custom",
        description="sphere | plane | cylinder | car_body | custom",
    )
    max_iter: int = Field(default=80, ge=10, le=500)
    seed: int = Field(default=42, ge=0)
    project_id: Optional[int] = Field(default=None, description="关联方案 ID")


class OptimizeStartPresetRequest(BaseModel):
    """异步预设优化请求（M2 新增）。"""
    shape: str = Field(..., description="sphere | plane_with_noise | cylinder | car_body")
    max_iter: int = Field(default=80, ge=10, le=300)
    project_id: Optional[int] = Field(default=None, description="关联方案 ID")


class OptimizeStartResponse(BaseModel):
    """异步启动响应（M2 新增）。"""
    task_id: str
    status: str
    status_url: str
    panel_name: Optional[str] = None
    shape: Optional[str] = None
    max_iter: int
