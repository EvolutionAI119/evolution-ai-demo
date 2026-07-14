"""
依赖注入（M2：project_service 改用 Depends(get_db) ORM 模式，不再走单例）。
"""
from functools import lru_cache

from backend.services.car_model_service import CarModelService
from backend.services.quality_service import QualityService
from backend.services.optimize_service import OptimizeService
from backend.services.storyboard_service import StoryboardService
from backend.services.export_service import ExportService


@lru_cache
def get_car_model_service() -> CarModelService:
    return CarModelService()


@lru_cache
def get_quality_service() -> QualityService:
    return QualityService()


@lru_cache
def get_optimize_service() -> OptimizeService:
    return OptimizeService()


@lru_cache
def get_storyboard_service() -> StoryboardService:
    return StoryboardService()


@lru_cache
def get_export_service() -> ExportService:
    return ExportService()
