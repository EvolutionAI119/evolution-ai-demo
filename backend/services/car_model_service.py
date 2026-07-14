"""
CarModelService - 建模服务
"""
import time
import hashlib
import json
from typing import Dict, Any, Optional

import numpy as np
import trimesh
from loguru import logger

from algorithm_model.api import build_car, CarParams
from algorithm_model.car_modeling import compute_stats
from algorithm_model.freeform import FreeformDeformation
from backend.models.car import FreeformParams


class CarModelService:
    """整车造型构建服务（薄壳）"""

    def build(self, params, freeform: Optional[FreeformParams] = None) -> Dict[str, Any]:
        """
        构建完整汽车造型

        Args:
            params: backend.models.car.CarParamsAPI
            freeform: 可选自由变形参数

        Returns:
            {glb_url, stats, params_hash, build_time_ms, freeform_applied}
        """
        start = time.time()
        # 1. Pydantic 模型 → algorithm_model 的 CarParams dataclass
        algo_params = params.to_car_params() if hasattr(params, "to_car_params") else CarParams(**params.model_dump())

        # 2. 调算法层
        parts = build_car(algo_params)
        logger.info(f"🔧 Built car with {len(parts)} parts")

        # 3. 合并 + 应用自由变形（在 GLB 导出前）
        freeform_applied = None
        combined = trimesh.util.concatenate(list(parts.values()))

        if freeform is not None:
            combined = self._apply_freeform(combined, freeform, algo_params)
            freeform_applied = self._freeform_summary(freeform)
            logger.info(f"🎨 Applied freeform deformation: preset={freeform.preset.value}, "
                        f"amplitude={freeform.amplitude}, center=({freeform.center_x}, {freeform.center_z})")

        # 4. GLB 编码
        glb_bytes = combined.export(file_type="glb")

        # 5. 计算 hash（用于缓存去重）
        params_dict = params.model_dump() if hasattr(params, "model_dump") else params
        params_hash = hashlib.sha256(
            json.dumps(params_dict, sort_keys=True).encode()
        ).hexdigest()[:16]

        # 6. 保存 + 返回 URL
        from backend.utils.file_storage import save_bytes
        glb_url = save_bytes(glb_bytes, "cars", ".glb")

        # 7. 统计
        stats = compute_stats(parts)

        elapsed = (time.time() - start) * 1000
        logger.info(f"✅ Car built in {elapsed:.1f}ms ({stats['total_vertices']} verts)")

        return {
            "glb_url": glb_url,
            "stats": stats,
            "params_hash": params_hash,
            "build_time_ms": round(elapsed, 2),
            "freeform_applied": freeform_applied,
        }

    def _apply_freeform(
        self,
        mesh: trimesh.Trimesh,
        freeform: FreeformParams,
        algo_params,
    ) -> trimesh.Trimesh:
        """
        对车身网格应用自由变形

        Args:
            mesh: 合并后的整车网格
            freeform: 自由变形参数
            algo_params: CarParams（提供车身尺寸信息）

        Returns:
            变形后的网格
        """
        ffd = FreeformDeformation()

        # 车身尺寸（从 CarParams 获取）
        body_length = algo_params.L
        body_height = algo_params.H

        # 将归一化的 center_x 映射到实际坐标
        # center_x: -1.0 ~ 1.0 映射到 -L/2 ~ L/2
        actual_center_x = freeform.center_x * (body_length / 2)

        # 预设名称
        preset_name = freeform.preset.value

        if preset_name == "custom":
            # 自定义模式：使用用户提供的控制点
            self._apply_custom_deformation(
                ffd, freeform, actual_center_x, body_length, body_height
            )
        else:
            # 预设模式：使用 amplitude 缩放预设的变形幅度
            # 从 DEFORM_PRESETS 获取默认 amplitude，按比例缩放
            from algorithm_model.freeform.freeform_surface import DEFORM_PRESETS
            preset_config = DEFORM_PRESETS.get(preset_name)
            if preset_config is None:
                raise ValueError(
                    f"Unknown freeform preset: {preset_name}. "
                    f"Available: {list(DEFORM_PRESETS.keys())} + ['custom']"
                )
            scaled_amplitude = preset_config["amplitude"] * freeform.amplitude
            ffd.add_deformation(
                preset_name=preset_name,
                center_x=actual_center_x,
                center_z=freeform.center_z,
                amplitude=scaled_amplitude,
            )

        # 应用变形
        vertices = mesh.vertices.copy()
        deformed_vertices = ffd.apply(vertices, body_length, body_height)

        # 创建变形后的网格
        deformed_mesh = mesh.copy()
        deformed_mesh.vertices = deformed_vertices

        return deformed_mesh

    def _apply_custom_deformation(
        self,
        ffd: FreeformDeformation,
        freeform: FreeformParams,
        actual_center_x: float,
        body_length: float,
        body_height: float,
    ):
        """
        应用自定义控制点变形

        使用用户提供的 custom_control_points 构建 NURBS 变形
        """
        import numpy as np
        from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid

        control_points_grid = np.array(freeform.custom_control_points)
        grid_n = control_points_grid.shape[0]

        # 缩放幅度
        scaled_grid = control_points_grid * freeform.amplitude

        # 使用 character_line 预设的参数框架，替换控制点
        ffd.add_deformation(
            preset_name="character_line",  # 使用一个通用预设作为框架
            center_x=actual_center_x,
            center_z=freeform.center_z,
            amplitude=1.0,  # 幅度已通过 scaled_grid 体现
            size=(0.5, 0.3),
            grid_n=grid_n,
        )
        # 替换最后一个变形 z_grid 为自定义网格
        ffd.deformations[-1]["z_grid"] = scaled_grid
        ffd.deformations[-1]["grid_n"] = grid_n
        ffd.deformations[-1]["preset_name"] = "custom"

    @staticmethod
    def _freeform_summary(freeform: FreeformParams) -> list:
        """生成 freeform 变形摘要"""
        summary = [{
            "preset": freeform.preset.value,
            "amplitude": freeform.amplitude,
            "center_x": freeform.center_x,
            "center_z": freeform.center_z,
        }]
        if freeform.preset.value == "custom" and freeform.custom_control_points:
            grid = freeform.custom_control_points
            summary[0]["custom_grid_size"] = f"{len(grid)}x{len(grid[0]) if grid else 0}"
        return summary

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

    def export_model(
        self,
        params,
        export_format: str = "glb",
        freeform: Optional[FreeformParams] = None,
    ) -> Dict[str, Any]:
        """
        构建并导出为指定格式（glb / obj / stl）

        流程与 build() 相同，区别在于最后导出的文件格式不同。
        OBJ 导出可能包含 .obj + .mtl 两个文件，打包为 zip。
        """
        import io
        import zipfile

        start = time.time()

        # 1. 参数转换
        algo_params = params.to_car_params() if hasattr(params, "to_car_params") else CarParams(**params.model_dump())

        # 2. 构建
        parts = build_car(algo_params)
        combined = trimesh.util.concatenate(list(parts.values()))

        # 3. 自由变形
        if freeform is not None:
            combined = self._apply_freeform(combined, freeform, algo_params)
            logger.info(f"🎨 Export with freeform: preset={freeform.preset.value}")

        # 4. 按格式导出
        file_size = 0
        if export_format == "glb":
            data = combined.export(file_type="glb")
            from backend.utils.file_storage import save_bytes
            file_url = save_bytes(data, "exports", ".glb")
            file_size = len(data)

        elif export_format == "obj":
            # trimesh OBJ 导出返回 dict: {'.obj': bytes, '.mtl': bytes} 或单 bytes
            result = combined.export(file_type="obj")
            if isinstance(result, dict):
                # 多文件 → 打 zip
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for ext, content in result.items():
                        name = f"car_model{ext}"
                        if isinstance(content, str):
                            content = content.encode()
                        zf.writestr(name, content)
                zip_data = buf.getvalue()
                from backend.utils.file_storage import save_bytes
                file_url = save_bytes(zip_data, "exports", ".obj.zip")
                file_size = len(zip_data)
            else:
                # 单文件
                data = result if isinstance(result, bytes) else result.encode()
                from backend.utils.file_storage import save_bytes
                file_url = save_bytes(data, "exports", ".obj")
                file_size = len(data)

        elif export_format == "stl":
            data = combined.export(file_type="stl")
            if isinstance(data, str):
                data = data.encode()
            from backend.utils.file_storage import save_bytes
            file_url = save_bytes(data, "exports", ".stl")
            file_size = len(data)

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        elapsed = (time.time() - start) * 1000
        logger.info(f"📦 Exported {export_format.upper()} in {elapsed:.1f}ms ({file_size} bytes)")

        return {
            "file_url": file_url,
            "format": export_format,
            "file_size_bytes": file_size,
            "build_time_ms": round(elapsed, 2),
        }