"""
文件存储工具
"""
import hashlib
from pathlib import Path
from typing import Optional
from loguru import logger

from backend.config import settings


def file_hash(data: bytes, length: int = 16) -> str:
    """计算文件 hash（短）"""
    return hashlib.sha256(data).hexdigest()[:length]


def save_bytes(data: bytes, subdir: str, suffix: str) -> str:
    """
    保存字节到 outputs/{subdir}/{hash}{suffix}

    Returns:
        相对 URL: /static/{subdir}/{hash}{suffix}
    """
    h = file_hash(data)
    path = settings.outputs_dir / subdir / f"{h}{suffix}"
    if not path.exists():
        path.write_bytes(data)
        logger.info(f"💾 Saved {path} ({len(data)} bytes)")
    return f"/static/{subdir}/{path.name}"


def read_bytes(subdir: str, filename: str) -> Optional[bytes]:
    """读取 outputs/{subdir}/{filename}"""
    path = settings.outputs_dir / subdir / filename
    if path.exists():
        return path.read_bytes()
    return None


def get_path(subdir: str, filename: str) -> Path:
    """获取文件路径"""
    return settings.outputs_dir / subdir / filename
