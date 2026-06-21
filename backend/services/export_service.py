"""
ExportService - 导出服务

支持 GLB / STL / OBJ 三种格式（M1）
M3 扩展：PNG 三视图
"""
import time
import hashlib
import json
from typing import Dict
import numpy as np
import trimesh
from loguru import logger

from algorithm_model.api import build_car, CarParams


class ExportService:
    """模型导出服务"""

    def export(
        self,
        params,
        fmt: str = "glb",
    ) -> Dict[str, bytes]:
        """
        导出指定格式

        Args:
            params: CarParamsAPI
            fmt: glb / stl / obj

        Returns:
            {data: bytes, filename: str, content_type: str}
        """
        start = time.time()
        algo_params = params.to_car_params() if hasattr(params, "to_car_params") else CarParams(**params.model_dump())
        parts = build_car(algo_params)
        combined = trimesh.util.concatenate(list(parts.values()))

        # 文件名（params hash）
        params_dict = params.model_dump() if hasattr(params, "model_dump") else params
        params_hash = hashlib.sha256(
            json.dumps(params_dict, sort_keys=True).encode()
        ).hexdigest()[:12]

        fmt = fmt.lower()
        if fmt == "glb":
            data = combined.export(file_type="glb")
            filename = f"car_{params_hash}.glb"
            content_type = "model/gltf-binary"
        elif fmt == "stl":
            data = combined.export(file_type="stl")
            filename = f"car_{params_hash}.stl"
            content_type = "model/stl"
        elif fmt == "obj":
            data = combined.export(file_type="obj")
            filename = f"car_{params_hash}.obj"
            content_type = "model/obj"
        else:
            raise ValueError(f"不支持的格式: {fmt} (glb/stl/obj)")

        elapsed = (time.time() - start) * 1000
        logger.info(f"📦 Exported {fmt.upper()} in {elapsed:.1f}ms ({len(data)} bytes)")

        return {
            "data": data,
            "filename": filename,
            "content_type": content_type,
        }
