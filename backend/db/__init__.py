"""L5 数据层：SQLAlchemy ORM + Alembic 迁移。

4 张表：
- projects: 方案主表
- car_models: 方案关联的 3D 模型快照
- quality_reports: 方案关联的曲面质量报告
- optimization_tasks: 异步优化任务状态（M2 新增）
"""
from .base import Base
from .session import engine, SessionLocal, get_db, init_db
from .models import (
    Project,
    CarModel,
    QualityReport,
    OptimizationTask,
    TaskStatus,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Project",
    "CarModel",
    "QualityReport",
    "OptimizationTask",
    "TaskStatus",
]
