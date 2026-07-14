"""Celery 应用实例配置。

Broker/Backend: Redis
序列化: JSON
时区: Asia/Shanghai
"""
from celery import Celery

from backend.config import settings

celery_app = Celery(
    "evolution_ai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.tasks.optimize_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=180,        # 硬超时 3 分钟
    task_soft_time_limit=150,   # 软超时 2.5 分钟
    worker_max_tasks_per_child=200,  # 防内存泄漏
    worker_prefetch_multiplier=1,    # 长任务别预取太多
    broker_connection_retry_on_startup=True,
)
