"""
Quality 路由
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_quality_service
from backend.models.quality import (
    QualityAssessRequest,
    QualityAssessResponse,
    QualityPresetRequest,
)
from backend.services.quality_service import QualityService

router = APIRouter()


@router.post("/assess", response_model=QualityAssessResponse, summary="评估曲面质量")
def assess(
    req: QualityAssessRequest,
    service: QualityService = Depends(get_quality_service),
):
    """
    评估 3D 网格曲面的质量

    返回：
    - grade: A/B/C/D 等级
    - g1_ratio / g2_ratio: 切线/曲率连续性比率
    - reflection_score: 反射线评分 0~1
    - max_curvature_jump: 最大曲率跳变
    """
    try:
        return service.assess(req.points, req.panel_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/assess-preset", response_model=QualityAssessResponse, summary="预设曲面评估")
def assess_preset(
    req: QualityPresetRequest,
    service: QualityService = Depends(get_quality_service),
):
    """
    预设曲面评估（无需传 points）

    可选 shape：sphere | plane | cylinder | car_body
    """
    try:
        return service.assess_preset(req.shape, req.resolution)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
