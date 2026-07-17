"""
Loguru 日志配置
"""
import sys
from loguru import logger
from backend.config import settings


def setup_logger():
    """配置 loguru"""
    logger.remove()  # 移除默认 handler

    # 控制台输出
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.debug else "INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 文件输出
    log_file = settings.outputs_dir / "logs" / "backend.log"
    log_file.parent.mkdir(exist_ok=True)
    logger.add(
        str(log_file),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    return logger
