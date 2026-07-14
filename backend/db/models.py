"""SQLAlchemy ORM 模型：4 张核心表。

设计原则：
- 所有 JSON 字段存 TEXT（SQLite 友好），读时反序列化
- 时间字段统一 UTC
- 软删除：使用 is_deleted 标记
- 外键级联：删除 project 时连带删除其下所有快照
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class TaskStatus(str, enum.Enum):
    """异步任务状态。"""

    PENDING = "PENDING"        # 已入队未启动
    STARTED = "STARTED"        # Worker 拉起
    PROGRESS = "PROGRESS"      # 正在执行（有进度）
    SUCCESS = "SUCCESS"        # 完成
    FAILURE = "FAILURE"        # 失败
    REVOKED = "REVOKED"        # 取消


class Project(Base):
    """方案主表：存元数据 + 参数 JSON。"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    tags: Mapped[Optional[str]] = mapped_column(String(200), default="")  # 逗号分隔
    preset: Mapped[Optional[str]] = mapped_column(String(50), default="custom")  # sport/luxury/suv/custom

    # 22 维参数 JSON（完整 CarParams 序列化）
    params_json: Mapped[str] = mapped_column(Text, nullable=False)

    # 关联快照（级联删除）
    car_model: Mapped[Optional["CarModel"]] = relationship(
        "CarModel", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    quality_reports: Mapped[list["QualityReport"]] = relationship(
        "QualityReport", back_populates="project", cascade="all, delete-orphan"
    )
    optimization_tasks: Mapped[list["OptimizationTask"]] = relationship(
        "OptimizationTask", back_populates="project", cascade="all, delete-orphan"
    )

    is_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class CarModel(Base):
    """3D 模型快照：存 GLB 路径 + 统计。"""

    __tablename__ = "car_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    glb_path: Mapped[str] = mapped_column(String(300), nullable=False)
    glb_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stats_json: Mapped[Optional[str]] = mapped_column(Text)  # components + bounds
    parts_count: Mapped[int] = mapped_column(Integer, default=0)
    vertex_count: Mapped[int] = mapped_column(Integer, default=0)
    face_count: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship("Project", back_populates="car_model")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class QualityReport(Base):
    """曲面质量评估报告。"""

    __tablename__ = "quality_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    panel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # A/B/C/D

    # QualityReport 关键字段
    g0_count: Mapped[int] = mapped_column(Integer, default=0)
    g1_count: Mapped[int] = mapped_column(Integer, default=0)
    g2_count: Mapped[int] = mapped_column(Integer, default=0)
    g1_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    g2_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    max_curvature_jump: Mapped[float] = mapped_column(Float, default=0.0)
    mean_curvature: Mapped[float] = mapped_column(Float, default=0.0)
    reflection_score: Mapped[float] = mapped_column(Float, default=0.0)
    details_json: Mapped[Optional[str]] = mapped_column(Text)  # 完整 QualityReport.details

    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="quality_reports")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OptimizationTask(Base):
    """异步优化任务状态。"""

    __tablename__ = "optimization_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # 任务参数
    panel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    surface_type: Mapped[str] = mapped_column(String(50), default="custom")  # sphere/plane/cylinder/custom
    max_iter: Mapped[int] = mapped_column(Integer, default=80)
    initial_params_json: Mapped[Optional[str]] = mapped_column(Text)

    # 任务状态
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False), default=TaskStatus.PENDING, index=True
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 - 1.0
    current_iter: Mapped[int] = mapped_column(Integer, default=0)
    best_score: Mapped[Optional[float]] = mapped_column(Float)

    # 结果（SUCCESS 时填）
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="optimization_tasks")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
