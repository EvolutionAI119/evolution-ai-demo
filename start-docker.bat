@echo off
chcp 65001 > nul
echo ========================================
echo   EVOLUTION AI - Docker 一键部署
echo ========================================
echo.

REM 检查 Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker
    echo.
    echo 请先安装 Docker Desktop:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo [1/3] 构建镜像（首次约 3-5 分钟）...
docker compose build --progress=plain
if errorlevel 1 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)

echo.
echo [2/3] 启动服务...
docker compose up -d
if errorlevel 1 (
    echo [错误] 服务启动失败
    docker compose logs --tail=30
    pause
    exit /b 1
)

echo.
echo [3/3] 等待服务就绪...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   ✅ EVOLUTION AI 已启动
echo ========================================
echo.
echo   🚀 后端 API:  http://localhost:8000
echo   📡 API 文档:  http://localhost:8000/docs
echo   🎨 前端 DEMO: http://localhost:8501
echo.
echo   停止服务: docker compose down
echo   查看日志: docker compose logs -f
echo ========================================
echo.

REM 自动打开浏览器
start http://localhost:8501

pause
