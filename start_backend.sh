#!/bin/bash
# EVOLUTION AI Backend 启动脚本（Linux/macOS）
set -e

cd "$(dirname "$0")/.."

# 激活虚拟环境（可选）
# source venv/bin/activate

# 安装依赖
pip install -q -r backend/requirements.txt -r algorithm_model/requirements.txt

# 启动服务
echo "🚀 Starting EVOLUTION AI Backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
