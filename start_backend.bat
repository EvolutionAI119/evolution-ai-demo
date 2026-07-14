@echo off
REM EVOLUTION AI Backend 启动脚本（Windows）
cd /d %~dp0\..

echo Installing dependencies...
pip install -q -r backend\requirements.txt -r algorithm_model\requirements.txt

echo Starting EVOLUTION AI Backend...
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
