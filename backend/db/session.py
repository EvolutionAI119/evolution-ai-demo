"""SQLAlchemy engine + session 管理。"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings


def _create_engine() -> Engine:
    """根据当前 settings 动态创建 engine。"""
    extra: dict = {}
    if settings.database_url.startswith("sqlite"):
        extra["connect_args"] = {"check_same_thread": False}
        # in-memory DB 需要 StaticPool 共享连接，否则每次新连接都是新 DB
        if ":memory:" in settings.database_url:
            from sqlalchemy.pool import StaticPool
            extra["poolclass"] = StaticPool
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
        **extra,
    )


# 延迟初始化（避免 config 加载顺序问题）
engine: Engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def reload_engine() -> Engine:
    """测试用：根据当前 settings 重建 engine（支持 in-memory DB）。"""
    global engine
    engine = _create_engine()
    SessionLocal.configure(bind=engine)
    return engine


def init_db() -> None:
    """初始化所有表（开发环境用，生产用 Alembic）。"""
    from backend.db.base import Base
    from backend.db import models  # noqa: F401 触发模型注册

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：每个请求一个 session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """非请求上下文使用的 session（如后台任务、脚本）。"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
