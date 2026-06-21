#!/bin/bash
# Celery worker 启动脚本（云端 / Linux）
# 用法: bash start_celery_worker.sh
# 停止: pkill -f "celery.*backend.tasks.celery_app"

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p logs

CONCURRENCY="${CELERY_CONCURRENCY:-2}"

echo "========================================"
echo " Evolution AI · Celery Worker"
echo "  cwd: $SCRIPT_DIR"
echo "  concurrency: $CONCURRENCY"
echo "  broker: redis://localhost:6379/0"
echo "  backend: redis://localhost:6379/1"
echo "========================================"

# 确保 Redis 在
if ! redis-cli ping >/dev/null 2>&1; then
  echo "❌ Redis not running, starting..."
  redis-server --daemonize yes --port 6379
  sleep 1
fi

PYTHONPATH=. exec celery -A backend.tasks.celery_app worker \
  -l info \
  --concurrency="$CONCURRENCY" \
  --logfile=logs/celery_worker.log
