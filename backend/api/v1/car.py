"""
Car 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_car_model_service
from backend.models.car import (
    CarParamsAPI,
    CarStatsAPI,
    CarBuildRequest,
    CarBuildResponse,
    CarExportRequest,
    CarExportResponse,
    CarValidateRequest,
    CarValidateResponse,
    FreeformParams,
)
from backend.services.car_model_service import CarModelService

router = APIRouter()


@router.get("/params/default", response_model=CarParamsAPI, summary="获取默认参数")
def get_default_params():
    """返回 22 维默认参数"""
    return CarParamsAPI()


@router.post("/build", response_model=CarBuildResponse, summary="构建整车 3D 模型")
def build_car(
    req: CarBuildRequest,
    service: CarModelService = Depends(get_car_model_service),
):
    """
    根据 22 维参数构建完整汽车造型

    Body:
    - params: 22 维形态参数（可选，不传则用默认值）
    - freeform: 可选自由变形参数（5 种预设 + 自定义模式）

    返回：
    - glb_url: 静态资源 URL，前端可直传 Three.js GLTFLoader
    - stats: 顶点数/面数/部件统计
    - params_hash: 参数 hash（用于缓存去重）
    - build_time_ms: 构建耗时
    - freeform_applied: 已应用的变形摘要（无 freeform 时为 None）
    """
    params = req.params if req.params is not None else CarParamsAPI()
    try:
        result = service.build(params, freeform=req.freeform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/export", response_model=CarExportResponse, summary="导出模型（GLB/OBJ/STL）")
def export_car(
    req: CarExportRequest,
    service: CarModelService = Depends(get_car_model_service),
):
    """
    构建并导出为指定格式

    Body:
    - params: 22 维形态参数（可选，不传则用默认值）
    - freeform: 可选自由变形参数
    - format: 导出格式 glb / obj / stl（默认 glb）

    OBJ 格式可能包含 .obj + .mtl 两个文件，会打包为 .obj.zip

    返回：
    - file_url: 静态资源 URL
    - format: 实际导出格式
    - file_size_bytes: 文件大小
    - build_time_ms: 构建耗时
    """
    params = req.params if req.params is not None else CarParamsAPI()
    try:
        result = service.export_model(
            params,
            export_format=req.format.value,
            freeform=req.freeform,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/validate", response_model=CarValidateResponse, summary="参数越界校验")
def validate_params(
    req: CarValidateRequest,
    service: CarModelService = Depends(get_car_model_service),
):
    """参数边界校验（双重：Pydantic Field + CarParams.validate）"""
    return service.validate(req.params)


@router.get("/presets", summary="预设方案（运动型/豪华型/SUV）")
def get_presets():
    """3 套预设方案，方便用户快速开始"""
    return {
        "sport": {
            "name": "运动型轿车",
            "description": "低矮、宽体、激进",
            "params": CarParamsAPI(
                L=4.6, W=1.9, H=1.32, wheelbase=2.75,
                hood_angle=8.0, roof_arc=0.65, windshield_rake=28.0,
                fender_prominence=0.28, overall_arc=0.45,
                wheel_radius=0.36, wheel_width=0.25, wheel_spoke_count=5,
            ).model_dump(),
        },
        "luxury": {
            "name": "豪华型轿车",
            "description": "修长、优雅、舒适",
            "params": CarParamsAPI(
                L=5.1, W=1.88, H=1.48, wheelbase=3.05,
                hood_angle=15.0, roof_arc=0.30, windshield_rake=33.0,
                fender_prominence=0.10, overall_arc=0.15,
                wheel_radius=0.33, wheel_width=0.22, wheel_spoke_count=7,
            ).model_dump(),
        },
        "suv": {
            "name": "SUV",
            "description": "高大、硬朗、空间大",
            "params": CarParamsAPI(
                L=4.8, W=1.95, H=1.72, wheelbase=2.85,
                hood_angle=20.0, roof_arc=0.15, windshield_rake=38.0,
                ground_clearance=0.22, fender_prominence=0.25, overall_arc=0.08,
                wheel_radius=0.38, wheel_width=0.26, wheel_spoke_count=6,
            ).model_dump(),
        },
    }
