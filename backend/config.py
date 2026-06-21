"""
Pydantic Settings 配置（M2 升级：+ DB + Celery + Redis）。
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # 基础
    env: str = "development"  # development | production
    debug: bool = True

    # CORS（开发环境全放开，生产环境收敛）
    cors_origins: list[str] = [
        "http://localhost:3000",   # React/Vue 默认
        "http://localhost:5173",   # Vite
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # 文件存储
    outputs_dir: Path = Path(__file__).resolve().parent / "outputs"
    max_upload_size: int = 50 * 1024 * 1024  # 50MB

    # API 限制
    rate_limit: str = "100/minute"

    # 算法模型版本
    algorithm_model_version: str = "1.0.0"

    # ===== M2: 数据库（SQLAlchemy）=====
    # 注意：database_url 默认空，由下方动态计算绝对路径
    database_url: str = ""
    db_echo: bool = False  # 是否打印 SQL（生产 False）

    # ===== M2: Celery 异步任务 =====
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="EVOLUTION_",
    )


# 全局单例
settings = Settings()

# 兼容：暴露旧名字
DATABASE_URL = settings.database_url
DB_ECHO = settings.db_echo
CELERY_BROKER_URL = settings.celery_broker_url
CELERY_RESULT_BACKEND = settings.celery_result_backend

# 动态计算 DB 路径（绝对路径，避免 CWD 不一致）
if not settings.database_url:
    _DB_PATH = Path(__file__).resolve().parent / "outputs" / "evolution_ai.db"
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.database_url = f"sqlite:///{_DB_PATH}"
    DATABASE_URL = settings.database_url

# 确保输出目录存在
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
(settings.outputs_dir / "cars").mkdir(exist_ok=True)
(settings.outputs_dir / "reports").mkdir(exist_ok=True)
(settings.outputs_dir / "storyboards").mkdir(exist_ok=True)
(settings.outputs_dir / "snapshots").mkdir(exist_ok=True)
(settings.outputs_dir.parent / "db").mkdir(exist_ok=True)  # DB 目录
