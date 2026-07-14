#!/bin/bash
# ============================================================
# EVOLUTION AI V2.1 — Docker Hot Update Script
# ============================================================
# This script updates the car body builder inside a running
# Docker container WITHOUT rebuilding the image.
#
# Usage:
#   chmod +x hot_update_v21.sh
#   ./hot_update_v21.sh
#
# Prerequisites:
#   - Docker container 'evolution-ai' is running
#   - docker-compose.yml is in the current directory
# ============================================================

set -e

CONTAINER_NAME="evolution-ai"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "  EVOLUTION AI V2.1 Hot Update"
echo "=========================================="
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[WARN] Container '${CONTAINER_NAME}' not found running."
    echo "       Trying to start via docker-compose..."
    cd "$SCRIPT_DIR"
    docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
    sleep 5
fi

# Verify container is now running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[ERROR] Container still not running. Please start it manually."
    exit 1
fi

echo "[OK] Container '${CONTAINER_NAME}' is running."
echo ""

# Find the app directory inside the container
APP_DIR=$(docker exec "$CONTAINER_NAME" find /app -name "app.py" -maxdepth 3 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
if [ -z "$APP_DIR" ]; then
    APP_DIR="/app"
fi
echo "[INFO] App directory in container: ${APP_DIR}"

# Copy the V2.1 car body builder
echo "[1/3] Copying car_body_builder.py ..."
docker cp "${SCRIPT_DIR}/car_body_builder.py" "${CONTAINER_NAME}:${APP_DIR}/car_body_builder.py"
echo "       -> ${APP_DIR}/car_body_builder.py"

# Copy the updated app.py
echo "[2/3] Copying updated app.py ..."
docker cp "${SCRIPT_DIR}/app.py" "${CONTAINER_NAME}:${APP_DIR}/app.py"
echo "       -> ${APP_DIR}/app.py"

# Restart the Streamlit/FastAPI process inside the container
echo "[3/3] Restarting application ..."
# Kill existing python processes (supervisor will restart them)
docker exec "$CONTAINER_NAME" bash -c "
    pkill -f 'streamlit run' 2>/dev/null || true
    pkill -f 'uvicorn' 2>/dev/null || true
    sleep 2
    # If using supervisord
    if command -v supervisorctl &>/dev/null; then
        supervisorctl restart all 2>/dev/null || true
    fi
    # If using the entrypoint script
    if [ -f /docker-entrypoint.sh ]; then
        /docker-entrypoint.sh &
    elif [ -f ${APP_DIR}/start.sh ]; then
        cd ${APP_DIR} && bash start.sh &
    fi
" 2>/dev/null || true

echo ""
echo "=========================================="
echo "  UPDATE COMPLETE"
echo "=========================================="
echo ""
echo "V2.1 changes:"
echo "  ✓ car_body_builder.py — V2.1 sweep-based parametric modelling"
echo "  ✓ 6 car types: sedan, SUV, coupe, MPV, sport, pickup"
echo "  ✓ 22-dimensional parameter system"
echo "  ✓ Smoothstep side-profile & planform curves"
echo "  ✓ Hyper-ellipse cross-section sweep (60 stations × 28 pts)"
echo "  ✓ Wheel arch cutting, headlights, taillights"
echo "  ✓ Legacy fallback preserved"
echo ""
echo "Refresh your browser to see the new 3D model."
echo ""
