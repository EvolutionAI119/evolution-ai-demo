"""
FastAPI 应用入口
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# 把父目录加入 sys.path，以便 backend 可以 import algorithm_model
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.config import settings
from backend.api.v1 import car, quality, optimize, storyboard, project, export, task, ws
from backend.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 DB，关闭时清理"""
    setup_logger()
    logger.info(f"🚀 EVOLUTION AI Backend 启动 (env={settings.env})")
    logger.info(f"📁 静态资源: {settings.outputs_dir}")
    logger.info(f"🗄️ 数据库: {settings.database_url}")
    # M2: 启动时初始化 DB（开发环境用，生产用 Alembic 迁移）
    try:
        from backend.db import init_db
        init_db()
        logger.info("✅ 数据库表已就绪")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"⚠️ DB 初始化失败: {e}")
    yield
    logger.info("👋 EVOLUTION AI Backend 关闭")


app = FastAPI(
    title="EVOLUTION AI API",
    description="参数化 + AI 驱动的汽车造型开发平台",
    version="0.2.0",  # M2 升级
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源服务
app.mount(
    "/static",
    StaticFiles(directory=str(settings.outputs_dir)),
    name="static",
)

# 注册路由（每个业务模块独立 prefix）
API_PREFIX = "/api/v1"
app.include_router(car.router, prefix=f"{API_PREFIX}/car", tags=["car"])
app.include_router(quality.router, prefix=f"{API_PREFIX}/quality", tags=["quality"])
app.include_router(optimize.router, prefix=f"{API_PREFIX}/optimize", tags=["optimize"])
app.include_router(storyboard.router, prefix=f"{API_PREFIX}/storyboard", tags=["storyboard"])
app.include_router(project.router, prefix=f"{API_PREFIX}/project", tags=["project"])
app.include_router(export.router, prefix=f"{API_PREFIX}/export", tags=["export"])
app.include_router(task.router, prefix=f"{API_PREFIX}/task", tags=["task"])  # M2
app.include_router(ws.router, prefix=f"{API_PREFIX}", tags=["ws"])  # M2.5: WebSocket 实时进度


@app.get("/", tags=["root"])
async def root():
    """根路径 - API 总览"""
    return {
        "name": "EVOLUTION AI",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "algorithm_model": "1.0.0",
        "endpoints": {
            "car": f"{API_PREFIX}/car",
            "quality": f"{API_PREFIX}/quality",
            "optimize": f"{API_PREFIX}/optimize",
            "storyboard": f"{API_PREFIX}/storyboard",
            "project": f"{API_PREFIX}/project",
            "export": f"{API_PREFIX}/export",
        },
    }


@app.get("/health", tags=["root"])
async def health():
    """健康检查"""
    return {"status": "ok", "env": settings.env}
