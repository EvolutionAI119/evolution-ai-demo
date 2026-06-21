"""
CarModelService - 建模服务
"""
import time
import hashlib
import json
from typing import Dict, Any

import numpy as np
import trimesh
from loguru import logger

from algorithm_model.api import build_car, CarParams
from algorithm_model.car_modeling import compute_stats


class CarModelService:
    """整车造型构建服务（薄壳）"""

    def build(self, params) -> Dict[str, Any]:
        """
        构建完整汽车造型

        Args:
            params: backend.models.car.CarParamsAPI

        Returns:
            {glb_url, stats, params_hash, build_time_ms}
        """
        start = time.time()
        # 1. Pydantic 模型 → algorithm_model 的 CarParams dataclass
        algo_params = params.to_car_params() if hasattr(params, "to_car_params") else CarParams(**params.model_dump())

        # 2. 调算法层
        parts = build_car(algo_params)
        logger.info(f"🔧 Built car with {len(parts)} parts")

        # 3. 合并 + GLB 编码
        combined = trimesh.util.concatenate(list(parts.values()))
        glb_bytes = combined.export(file_type="glb")

        # 4. 计算 hash（用于缓存去重）
        params_dict = params.model_dump() if hasattr(params, "model_dump") else params
        params_hash = hashlib.sha256(
            json.dumps(params_dict, sort_keys=True).encode()
        ).hexdigest()[:16]

        # 5. 保存 + 返回 URL
        from backend.utils.file_storage import save_bytes
        glb_url = save_bytes(glb_bytes, "cars", ".glb")

        # 6. 统计
        stats = compute_stats(parts)

        elapsed = (time.time() - start) * 1000
        logger.info(f"✅ Car built in {elapsed:.1f}ms ({stats['total_vertices']} verts)")

        return {
            "glb_url": glb_url,
            "stats": stats,
            "params_hash": params_hash,
            "build_time_ms": round(elapsed, 2),
        }

    def get_default_params(self):
        """获取默认参数"""
        from backend.models.car import CarParamsAPI
        return CarParamsAPI()

    def validate(self, params) -> Dict[str, Any]:
        """参数越界校验（已在 Pydantic Field 自动校验，这里返回细粒度错误）"""
        from backend.models.car import CarParamsAPI
        errors = []
        warnings = []

        try:
            p = params if isinstance(params, CarParamsAPI) else CarParamsAPI(**params)
            algo_params = p.to_car_params()
            algo_params.validate()  # 调用 algorithm_model 的边界校验
        except ValueError as e:
            errors.append(str(e))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
