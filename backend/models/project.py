"""
Project 相关 Pydantic 模型（M2 升级：方案 ID 改 int 主键自增）。
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.models.car import CarParamsAPI


class ProjectCreateRequest(BaseModel):
    """创建方案请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    params: CarParamsAPI
    tags: List[str] = Field(default_factory=list)
    preset: str = Field(default="custom", description="sport | luxury | suv | custom")


class ProjectUpdateRequest(BaseModel):
    """更新方案请求"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    params: Optional[CarParamsAPI] = None
    tags: Optional[List[str]] = None
    preset: Optional[str] = Field(default=None, description="sport | luxury | suv | custom")


class ProjectResponse(BaseModel):
    """方案响应（M2：id 改 int，tags 保留为 list）"""
    id: int
    name: str
    description: str
    preset: str = "custom"
    tags: List[str] = Field(default_factory=list)
    is_deleted: bool = False
    params: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
