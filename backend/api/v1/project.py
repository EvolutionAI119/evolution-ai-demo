"""Project 路由（方案库 M2：SQLAlchemy ORM）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from backend.services.project_service import ProjectService

router = APIRouter()
_service = ProjectService()


@router.get("/list", summary="方案列表")
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tag: str = Query(None),
    db: Session = Depends(get_db),
):
    items = _service.list(db, skip, limit, tag)
    return {"items": [_service.to_dict(p) for p in items], "count": len(items)}


@router.get("/count", summary="方案总数")
def count(db: Session = Depends(get_db)):
    return {"count": _service.count(db)}


@router.post("", status_code=201, summary="创建方案")
def create_project(
    req: ProjectCreateRequest,
    db: Session = Depends(get_db),
):
    params_dict = req.params.model_dump() if hasattr(req.params, "model_dump") else req.params
    project = _service.create(
        db=db,
        name=req.name,
        description=req.description or "",
        params=params_dict,
        tags=req.tags or [],
        preset=req.preset or "custom",
    )
    return _service.to_dict(project)


@router.get("/{project_id}", summary="获取方案详情")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = _service.get(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"方案 {project_id} 不存在")
    return _service.to_dict(project)


@router.patch("/{project_id}", summary="更新方案")
def update_project(
    project_id: int,
    req: ProjectUpdateRequest,
    db: Session = Depends(get_db),
):
    project = _service.update(
        db,
        project_id,
        name=req.name,
        description=req.description,
        params=req.params.model_dump() if req.params and hasattr(req.params, "model_dump") else None,
        tags=req.tags,
        preset=req.preset,
    )
    if not project:
        raise HTTPException(status_code=404, detail=f"方案 {project_id} 不存在")
    return _service.to_dict(project)


@router.delete("/{project_id}", status_code=204, summary="删除方案")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    if not _service.delete(db, project_id):
        raise HTTPException(status_code=404, detail=f"方案 {project_id} 不存在")
    return None
