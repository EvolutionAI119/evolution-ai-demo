#!/bin/bash
# ─────────────────────────────────────────────────
# Cython 加速编译脚本
# 用法: bash build_cython.sh
# ─────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════"
echo "  NURBS Cython 加速编译"
echo "═══════════════════════════════════════════"

# 检查依赖
python3 -c "import Cython" 2>/dev/null || {
    echo "[1/4] 安装 Cython..."
    pip install cython numpy
}

# 检查 gcc
which gcc >/dev/null 2>&1 || {
    echo "ERROR: gcc not found. Install build-essential."
    exit 1
}

echo "[2/4] 编译 Cython 扩展..."
python3 setup_nurbs.py build_ext --inplace 2>&1

echo "[3/4] 验证编译产物..."
# 查找 .so 文件
SO_FILES=$(find algorithm_model -name "_*_cy*.so" 2>/dev/null)
if [ -z "$SO_FILES" ]; then
    echo "WARNING: No .so files found. Checking for errors..."
    python3 -c "
try:
    from algorithm_model.freeform import _nurbs_cy
    print('  _nurbs_cy: OK')
except Exception as e:
    print(f'  _nurbs_cy: FAIL ({e})')
try:
    from algorithm_model.surface_quality import _quality_cy
    print('  _quality_cy: OK')
except Exception as e:
    print(f'  _quality_cy: FAIL ({e})')
"
else
    echo "$SO_FILES" | while read f; do echo "  ✅ $f"; done
fi

echo "[4/4] 快速性能验证..."
python3 -c "
import time, numpy as np

# 确保能导入
try:
    from algorithm_model.freeform._nurbs_cy import evaluate_surface_mesh_fast
    print('  _nurbs_cy 导入成功 ✅')
except ImportError as e:
    print(f'  _nurbs_cy 导入失败: {e}')
    exit(1)

try:
    from algorithm_model.surface_quality._quality_cy import compute_reflection_score_fast
    print('  _quality_cy 导入成功 ✅')
except ImportError as e:
    print(f'  _quality_cy 导入失败: {e}')

# 基准测试
from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid, evaluate_surface_mesh

np.random.seed(42)
cp = np.random.rand(8, 8, 3) * 100
surf = nurbs_surface_from_grid(cp, np.ones((8, 8)), 3, 3)

# Python 基线
t0 = time.perf_counter()
pts_py, _ = evaluate_surface_mesh(surf, 100, 100)
t_py = time.perf_counter() - t0

# Cython 加速
t0 = time.perf_counter()
pts_cy, _ = evaluate_surface_mesh_fast(surf, 100, 100)
t_cy = time.perf_counter() - t0

# 数值一致性
max_diff = np.max(np.abs(pts_py - pts_cy))
speedup = t_py / t_cy if t_cy > 0 else float('inf')

print(f'')
print(f'  100x100 网格:')
print(f'    Python:   {t_py*1000:.1f} ms')
print(f'    Cython:   {t_cy*1000:.1f} ms')
print(f'    加速比:   {speedup:.1f}x')
print(f'    数值偏差: {max_diff:.2e} {\"✅\" if max_diff < 1e-10 else \"❌\"}')
"

echo ""
echo "═══════════════════════════════════════════"
echo "  编译完成"
echo "═══════════════════════════════════════════"
