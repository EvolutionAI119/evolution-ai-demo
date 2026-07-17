"""算法层兼容导入。

把 algorithm_model 的 sys.path 注入封装到一处。
所有 backend 代码调这个，不要直接 from algorithm_model。
"""
import sys
from pathlib import Path

# 把 EVOLUTION_AI_DEMO/ 加入 sys.path，让 algorithm_model 可被 import
_WORKSPACE = Path(__file__).resolve().parent.parent  # backend/
_PROJECT_ROOT = _WORKSPACE.parent  # EVOLUTION_AI_DEMO/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# 现在可以正常导入
from algorithm_model.api import (  # noqa: E402
    build_car,
    evaluate_surface,
    optimize_surface,
    make_storyboard,
    render_storyboard,
    get_car_stats,
    run_full_pipeline,
)

__all__ = [
    "build_car",
    "evaluate_surface",
    "optimize_surface",
    "make_storyboard",
    "render_storyboard",
    "get_car_stats",
    "run_full_pipeline",
]
