@echo off
chcp 65001 > nul
echo ========================================
echo   EVOLUTION AI - 本地部署
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 安装后端依赖...
python -m pip install -r backend\requirements.txt
python -m pip install -r algorithm_model\requirements.txt
python -m pip install trimesh aiosqlite

echo.
echo [2/3] 尝试编译 Cython 加速（可选，失败不影响使用）...
python -m pip install cython numpy 2>nul
python setup_nurbs.py build_ext --inplace 2>nul
if errorlevel 1 (
    echo   ⚠️ Cython 编译跳过（需要 gcc），使用 Python 纯计算模式
    echo   功能完全正常，性能约慢 100-400x
) else (
    echo   ✅ Cython 加速已启用
)

echo.
echo [3/3] 启动后端服务...
echo.
echo ========================================
echo   ✅ EVOLUTION AI 后端已启动
echo   📡 API 文档: http://localhost:8000/docs
echo   🚀 健康检查: http://localhost:8000/health
echo ========================================
echo.
echo   按 Ctrl+C 停止服务
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
