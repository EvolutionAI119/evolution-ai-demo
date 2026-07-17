"""TaskService - 异步任务状态查询。

不负责执行任务（Celery 负责），只管查询。
"""
import json
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from backend.db import OptimizationTask, TaskStatus


class TaskService:
    """任务状态查询服务。"""

    def get_by_id(self, db: Session, task_id: str) -> Optional[OptimizationTask]:
        return (
            db.query(OptimizationTask)
            .filter(OptimizationTask.task_id == task_id)
            .first()
        )

    def get_by_project(self, db: Session, project_id: int) -> list[OptimizationTask]:
        return (
            db.query(OptimizationTask)
            .filter(OptimizationTask.project_id == project_id)
            .order_by(OptimizationTask.created_at.desc())
            .all()
        )

    def to_status_dict(self, task: OptimizationTask) -> dict:
        """ORM → API 响应 dict（轮询用）。"""
        d = {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "panel_name": task.panel_name,
            "surface_type": task.surface_type,
            "max_iter": task.max_iter,
            "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
            "progress": task.progress,
            "current_iter": task.current_iter,
            "best_score": task.best_score,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
        }
        if task.error_message:
            d["error_message"] = task.error_message
        if task.result_json:
            try:
                d["result"] = json.loads(task.result_json)
            except json.JSONDecodeError:
                logger.warning(f"task {task.task_id} result_json 解析失败")
        return d
