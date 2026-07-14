#!/bin/bash
# ========================================
#   EVOLUTION AI - Docker 一键部署 (Mac/Linux)
# ========================================

set -e

echo "========================================"
echo "  EVOLUTION AI - Docker 一键部署"
echo "========================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[错误] 未检测到 Docker"
    echo ""
    echo "请先安装 Docker Desktop:"
    echo "  https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "[1/3] 构建镜像（首次约 3-5 分钟）..."
docker compose build --progress=plain

echo ""
echo "[2/3] 启动服务..."
docker compose up -d

echo ""
echo "[3/3] 等待服务就绪..."
sleep 5

echo ""
echo "========================================"
echo "  ✅ EVOLUTION AI 已启动"
echo "========================================"
echo ""
echo "  🚀 后端 API:  http://localhost:8000"
echo "  📡 API 文档:  http://localhost:8000/docs"
echo "  🎨 前端 DEMO: http://localhost:8501"
echo ""
echo "  停止服务: docker compose down"
echo "  查看日志: docker compose logs -f"
echo "========================================"
echo ""

# 尝试打开浏览器
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
fi
