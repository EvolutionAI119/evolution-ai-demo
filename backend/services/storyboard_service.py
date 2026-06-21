"""
StoryboardService - 视频脚本服务
"""
import time
import uuid
from loguru import logger

from algorithm_model.api import make_storyboard, render_storyboard


class StoryboardService:
    """视频脚本生成 + 渲染服务（薄壳）"""

    def generate(
        self,
        product_name: str = "EVOLUTION AI 智能汽车",
        duration: int = 90,
        style: str = "科技感",
        key_features: list = None,
        audience: str = "专业评审",
        template: str = "car_promotion",
        custom_scenes: list = None,
    ) -> dict:
        """
        生成分镜脚本
        """
        start = time.time()
        if key_features is None:
            key_features = ["参数化造型", "AI 自动优化", "曲面质量评估"]

        sb_id = uuid.uuid4().hex[:12]
        logger.info(f"🎬 [{sb_id}] Generating storyboard: {product_name} (template={template})")

        # 1. 生成
        sb = make_storyboard(
            product_name=product_name,
            duration=duration,
            style=style,
            key_features=key_features,
            audience=audience,
            template=template,
            custom_scenes=custom_scenes,
        )

        # 2. 渲染 3 种格式
        md = render_storyboard(sb, fmt="markdown")
        html = render_storyboard(sb, fmt="html")

        # 3. 序列化 scenes（对齐 Scene dataclass 字段）
        scenes = [
            {
                "scene_id": s.scene_id,
                "duration_sec": s.duration_sec,
                "name": s.name,
                "background": s.background,
                "shot_type": s.shot_type,
                "camera": s.camera,
                "visual": s.visual,
                "subtitle": s.subtitle,
                "audio": s.audio,
                "components_shown": s.components_shown,
                "color_palette": s.color_palette,
                "data_highlights": s.data_highlights,
            }
            for s in sb.scenes
        ]

        elapsed = (time.time() - start) * 1000
        logger.info(f"✅ [{sb_id}] Storyboard ready in {elapsed:.1f}ms ({len(scenes)} scenes)")

        return {
            "id": sb_id,
            "product_name": sb.title,
            "duration": sb.total_duration,
            "style": sb.style,
            "audience": sb.audience,
            "key_features": sb.key_features,
            "template": template,
            "scene_count": len(scenes),
            "scenes": scenes,
            "markdown": md,
            "html": html,
            "json": sb.to_json(),
        }

    def list_templates(self) -> list:
        """列出所有模板（带场景数 + 总时长）"""
        from algorithm_model.storyboard.templates import TEMPLATES
        result = []
        for name, tpl in TEMPLATES.items():
            total_dur = sum(s.get("duration", 0) for s in tpl.get("scenes", []))
            result.append({
                "name": name,
                "description": tpl.get("name", name),
                "scene_count": len(tpl.get("scenes", [])),
                "total_duration": float(total_dur),
            })
        return result
