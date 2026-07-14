"""ProjectService - 方案库服务（M2 升级：SQLAlchemy ORM）。"""
import json
from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from backend.db import Project


class ProjectService:
    """方案库服务（ORM 版）。"""

    def create(
        self,
        db: Session,
        name: str,
        description: str,
        params: dict,
        tags: Optional[List[str]] = None,
        preset: str = "custom",
    ) -> Project:
        project = Project(
            name=name,
            description=description or "",
            tags=",".join(tags or []),
            preset=preset,
            params_json=json.dumps(params, default=str),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info(f"📁 Project created: id={project.id} name={name}")
        return project

    def get(self, db: Session, project_id: int) -> Optional[Project]:
        return (
            db.query(Project)
            .filter(Project.id == project_id, Project.is_deleted == False)  # noqa: E712
            .first()
        )

    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        tag: Optional[str] = None,
    ) -> List[Project]:
        q = db.query(Project).filter(Project.is_deleted == False)  # noqa: E712
        if tag:
            q = q.filter(Project.tags.like(f"%{tag}%"))
        return q.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()

    def update(self, db: Session, project_id: int, **kwargs) -> Optional[Project]:
        project = self.get(db, project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if value is None:
                continue
            if key == "tags" and isinstance(value, list):
                project.tags = ",".join(value)
            elif key == "params" and isinstance(value, dict):
                project.params_json = json.dumps(value, default=str)
            elif hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        logger.info(f"✏️ Project updated: id={project_id}")
        return project

    def delete(self, db: Session, project_id: int) -> bool:
        project = self.get(db, project_id)
        if not project:
            return False
        project.is_deleted = True  # 软删除
        project.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"🗑️ Project soft-deleted: id={project_id}")
        return True

    def count(self, db: Session) -> int:
        return (
            db.query(Project)
            .filter(Project.is_deleted == False)  # noqa: E712
            .count()
        )

    def to_dict(self, project: Project, include_params: bool = True) -> dict:
        """ORM → API 响应 dict。"""
        d = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "tags": [t for t in (project.tags or "").split(",") if t],
            "preset": project.preset,
            "is_deleted": project.is_deleted,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        if include_params:
            try:
                d["params"] = json.loads(project.params_json)
            except (json.JSONDecodeError, TypeError):
                d["params"] = {}
        return d
