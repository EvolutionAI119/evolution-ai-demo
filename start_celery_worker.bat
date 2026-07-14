@echo off
REM Celery worker 启动脚本（桌面端 / Windows）
REM 用法: 双击或在 cmd 中执行
REM 停止: taskkill /F /FI "WINDOWTITLE eq Celery Worker*"

setlocal
cd /d %~dp0
if not exist logs mkdir logs

if "%CELERY_CONCURRENCY%"=="" set CELERY_CONCURRENCY=2

echo ========================================
echo  Evolution AI · Celery Worker
echo   cwd: %cd%
echo   concurrency: %CELERY_CONCURRENCY%
echo ========================================

REM 确保 Redis 在（Windows 没有内置 redis-server，需手动安装或跑 WSL）
where redis-cli >nul 2>&1
if errorlevel 1 (
  echo [WARN] redis-cli 不在 PATH，假设 Redis 已运行在 localhost:6379
) else (
  redis-cli ping >nul 2>&1
  if errorlevel 1 (
    echo [WARN] Redis 未响应，请先启动 redis-server
  )
)

set PYTHONPATH=.
title Celery Worker - Evolution AI
celery -A backend.tasks.celery_app worker -l info --concurrency=%CELERY_CONCURRENCY%
endlocal
