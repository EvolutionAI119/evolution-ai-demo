"""Optimize 路由（M2 升级：同步 + 异步双接口）。

- POST /run /run-preset  : 同步（M1 兼容，5s+ 阻塞）
- POST /start /start-preset : 异步（M2 新增，立即返回 task_id）
- GET  /api/v1/task/{task_id}  : 轮询（task.py 路由）
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.optimize import (
    OptimizePresetRequest,
    OptimizeRequest,
    OptimizeStartPresetRequest,
    OptimizeStartRequest,
)
from backend.services.optimize_service import OptimizeService
from backend.services.task_service import TaskService

router = APIRouter()
_optimize_service = OptimizeService()
_task_service = TaskService()


# ==================== 同步（M1 保留） ====================

@router.post("/run", summary="同步优化（5s+ 阻塞，M1 兼容）")
def optimize_sync(req: OptimizeRequest):
    return _optimize_service.optimize(
        points=req.points,
        panel_name=req.panel_name,
        max_iter=req.max_iter,
        seed=req.seed,
    )


@router.post("/run-preset", summary="同步预设优化（M1 兼容）")
def optimize_preset_sync(req: OptimizePresetRequest):
    return _optimize_service.optimize_preset(
        shape=req.shape,
        max_iter=req.max_iter,
        seed=req.seed,
    )


# ==================== 异步（M2 新增） ====================

@router.post("/start", status_code=202, summary="启动异步优化")
def optimize_start(
    req: OptimizeStartRequest,
    db: Session = Depends(get_db),
):
    """立即返回 task_id，前端轮询 GET /api/v1/task/{task_id}。"""
    task = _optimize_service.start_async(
        db=db,
        panel_name=req.panel_name,
        surface_type=req.surface_type,
        max_iter=req.max_iter,
        seed=req.seed,
        project_id=req.project_id,
    )
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "status_url": f"/api/v1/task/{task.task_id}",
        "panel_name": task.panel_name,
        "max_iter": task.max_iter,
    }


@router.post("/start-preset", status_code=202, summary="启动异步预设优化")
def optimize_start_preset(
    req: OptimizeStartPresetRequest,
    db: Session = Depends(get_db),
):
    task = _optimize_service.start_preset_async(
        db=db,
        shape=req.shape,
        max_iter=req.max_iter,
        project_id=req.project_id,
    )
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "status_url": f"/api/v1/task/{task.task_id}",
        "shape": req.shape,
        "max_iter": req.max_iter,
    }
