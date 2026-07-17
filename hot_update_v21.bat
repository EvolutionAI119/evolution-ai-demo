@echo off
REM ============================================================
REM EVOLUTION AI V2.1 — Docker Hot Update Script (Windows)
REM ============================================================
REM Usage:  double-click or run from cmd
REM ============================================================

set CONTAINER_NAME=evolution-ai
set SCRIPT_DIR=%~dp0

echo ==========================================
echo   EVOLUTION AI V2.1 Hot Update
echo ==========================================
echo.

REM Check container
docker ps --format "{{.Names}}" | findstr /B "%CONTAINER_NAME%" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Container not running. Starting via docker-compose...
    cd /d "%SCRIPT_DIR%"
    docker compose up -d 2>nul || docker-compose up -d 2>nul
    timeout /t 5 /nobreak >nul
)

REM Copy files
echo [1/3] Copying car_body_builder.py ...
docker cp "%SCRIPT_DIR%car_body_builder.py" %CONTAINER_NAME%:/app/car_body_builder.py
echo [2/3] Copying updated app.py ...
docker cp "%SCRIPT_DIR%app.py" %CONTAINER_NAME%:/app/app.py

echo [3/3] Restarting application ...
docker exec %CONTAINER_NAME% cmd /c "taskkill /F /IM python.exe 2>nul & timeout /t 3 /nobreak >nul & cd /d C:\app & start /B python app.py" 2>nul

echo.
echo ==========================================
echo   UPDATE COMPLETE
echo ==========================================
echo.
echo  V2.1 changes applied:
echo   - Sweep-based parametric body
echo   - 6 car types, 22-dim parameters
echo   - Smoothstep curves, wheel arches
echo.
echo  Refresh your browser to see changes.
echo.
pause
