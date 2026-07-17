"""
Export 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from backend.deps import get_export_service
from backend.models.car import CarParamsAPI
from backend.services.export_service import ExportService

router = APIRouter()


@router.get("/{fmt}", summary="导出指定格式（GLB/STL/OBJ）")
def export_model(
    fmt: str,
    params: CarParamsAPI = Depends(),
    service: ExportService = Depends(get_export_service),
):
    """
    根据 URL 参数导出 3D 模型

    - 路径参数 fmt: glb / stl / obj
    - 查询参数 params: 22 维 CarParams（也可 POST body）

    简单起见 M1 用 GET（参数多可以 POST 后续支持）
    """
    fmt = fmt.lower()
    if fmt not in ("glb", "stl", "obj"):
        raise HTTPException(status_code=400, detail=f"不支持的格式: {fmt}")

    try:
        result = service.export(params, fmt)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return Response(
        content=result["data"],
        media_type=result["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{result["filename"]}"',
        },
    )
