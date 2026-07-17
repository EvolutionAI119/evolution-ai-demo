#!/bin/bash
set -e

echo "═══════════════════════════════════════════"
echo "  EVOLUTION AI - 启动中..."
echo "═══════════════════════════════════════════"

# 验证 Cython 扩展
echo "[1/3] 验证 Cython 加速模块..."
python3 -c "
from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
from algorithm_model.surface_quality._quality_cy import compute_reflection_score_fast
print('  ✅ Cython 加速模块就绪')
" 2>/dev/null || {
    echo "  ⚠️ Cython 模块未找到，降级为 Python 纯计算模式"
    echo "  （性能约降低 100-400x，功能不受影响）"
}

# 验证核心依赖
echo "[2/3] 验证核心依赖..."
python3 -c "
import numpy, scipy, trimesh
print(f'  numpy={numpy.__version__}  scipy={scipy.__version__}  trimesh={trimesh.__version__}')
"

# 确保数据目录存在
mkdir -p /app/data/outputs/cars /app/data/outputs/reports /app/data/outputs/storyboards /app/data/outputs/snapshots
mkdir -p /app/data/db /app/logs

echo "[3/3] 启动服务..."
echo ""

# 后台启动后端（FastAPI）
echo "  🚀 后端 API: http://localhost:8000"
echo "     Swagger UI: http://localhost:8000/docs"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 2 &
BACKEND_PID=$!

# 等后端就绪
sleep 2

# 前台启动前端（Streamlit）
echo "  🎨 前端 DEMO: http://localhost:8501"
echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ EVOLUTION AI 已就绪"
echo "  📡 API 文档: http://localhost:8000/docs"
echo "  🎨 前端界面: http://localhost:8501"
echo "═══════════════════════════════════════════"
echo ""

# 前台运行 Streamlit（保持容器不退出）
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false

# 如果 Streamlit 退出，等待后端
wait $BACKEND_PID
