#!/bin/bash
# EVOLUTION AI 启动脚本 (Linux/Mac)
echo "========================================"
echo "EVOLUTION AI - 汽车A级曲面DEMO"
echo "========================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 python3"
    exit 1
fi

# 检查依赖
python3 -c "import streamlit, plotly, numpy, scipy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[安装依赖] ..."
    pip3 install -r requirements.txt
fi

# 启动
echo "[启动] http://localhost:8501"
streamlit run app.py --server.port 8501
