"""Celery 异步任务层（M2 新增）。

优化任务改异步：POST → 立即返回 task_id → GET /task/{id} 轮询。
"""
from .celery_app import celery_app
from .optimize_task import run_optimize_task

__all__ = ["celery_app", "run_optimize_task"]
