"""
Storyboard 相关 Pydantic 模型（字段对齐 Scene/Storyboard dataclass）
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StoryboardGenerateRequest(BaseModel):
    """分镜生成请求"""
    product_name: str = Field(default="EVOLUTION AI 智能汽车", min_length=1, max_length=100)
    duration: int = Field(default=90, ge=10, le=600, description="总时长（秒）")
    style: str = Field(default="科技感", description="整体风格")
    key_features: List[str] = Field(
        default=["参数化造型", "AI 自动优化", "曲面质量评估"],
        description="核心卖点"
    )
    audience: str = Field(default="专业评审", description="目标受众")
    template: str = Field(default="car_promotion", description="模板名")
    custom_scenes: Optional[List[Dict[str, Any]]] = Field(default=None, description="自定义分镜")


class StoryboardSceneAPI(BaseModel):
    """单个分镜（对齐 Scene dataclass）"""
    scene_id: int
    duration_sec: float
    name: str
    background: str
    shot_type: str
    camera: str
    visual: str
    subtitle: str
    audio: str
    components_shown: List[str] = []
    color_palette: List[str] = []
    data_highlights: List[Dict[str, str]] = []


class StoryboardResponse(BaseModel):
    """分镜响应"""
    id: str
    product_name: str
    duration: float
    style: str
    audience: str
    key_features: List[str]
    template: str
    scene_count: int
    scenes: List[StoryboardSceneAPI]
    markdown: str
    html: str
    json: str


class StoryboardTemplate(BaseModel):
    """分镜模板摘要"""
    name: str
    description: str
    scene_count: int
    total_duration: float
