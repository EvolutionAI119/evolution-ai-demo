"""
Storyboard 路由
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_storyboard_service
from backend.models.storyboard import (
    StoryboardGenerateRequest,
    StoryboardResponse,
    StoryboardTemplate,
)
from backend.services.storyboard_service import StoryboardService

router = APIRouter()


@router.post("/generate", response_model=StoryboardResponse, summary="生成分镜脚本")
def generate(
    req: StoryboardGenerateRequest,
    service: StoryboardService = Depends(get_storyboard_service),
):
    """
    生成分镜脚本，同时返回 Markdown + HTML + JSON 三种格式

    可选 template：
    - car_promotion: 7 镜 90s 汽车产品宣传片
    - tech_demo: 5 镜 90s 技术演示片
    - minimal_showcase: 2 镜 90s 极简展示
    """
    try:
        return service.generate(
            product_name=req.product_name,
            duration=req.duration,
            style=req.style,
            key_features=req.key_features,
            audience=req.audience,
            template=req.template,
            custom_scenes=req.custom_scenes,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/templates", response_model=list[StoryboardTemplate], summary="列出所有模板")
def list_templates(
    service: StoryboardService = Depends(get_storyboard_service),
):
    """返回 3 套内置模板的摘要信息"""
    return service.list_templates()
