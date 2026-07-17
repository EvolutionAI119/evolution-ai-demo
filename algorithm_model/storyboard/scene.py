"""
分镜数据结构

- Scene: 单个分镜
- Storyboard: 完整视频脚本
"""
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class Scene:
    """单个分镜"""
    scene_id: int
    duration_sec: float
    name: str
    background: str
    shot_type: str           # 镜头类型：渐变/特写/广角/旋转/分屏/仰拍/俯拍
    camera: str              # 镜头运动：静态/缓推/摇移/环绕/跟拍
    visual: str              # 画面描述
    subtitle: str            # 字幕
    audio: str               # 配乐/音效
    components_shown: List[str] = field(default_factory=list)  # 出现的部件
    color_palette: List[str] = field(default_factory=list)     # 配色 HEX
    data_highlights: List[Dict[str, str]] = field(default_factory=list)  # 数据亮点

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Storyboard:
    """完整视频脚本"""
    title: str
    total_duration: float
    style: str
    audience: str
    key_features: List[str]
    scenes: List[Scene]
    storyboard_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "storyboard_id": self.storyboard_id,
            "title": self.title,
            "total_duration": self.total_duration,
            "style": self.style,
            "audience": self.audience,
            "key_features": self.key_features,
            "scenes": [s.to_dict() for s in self.scenes],
            "created_at": self.created_at,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
