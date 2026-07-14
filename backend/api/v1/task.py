"""Task 路由 - 异步任务状态查询（M2 新增）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.services.task_service import TaskService

router = APIRouter()
_service = TaskService()


@router.get("/{task_id}", summary="查询异步任务状态")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    task = _service.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    return _service.to_status_dict(task)


@router.get("/by-project/{project_id}", summary="查询某方案的所有任务")
def list_by_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    tasks = _service.get_by_project(db, project_id)
    return {"items": [_service.to_status_dict(t) for t in tasks], "count": len(tasks)}
