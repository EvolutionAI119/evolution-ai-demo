@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   EVOLUTION AI DEMO - One-Click Launcher
echo ============================================
echo.

REM Kill existing processes on port 8000 and 8501
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1

echo [1/2] Starting Backend (port 8000)...
start "EVOLUTION-BACKEND" cmd /k "cd /d D:\API\EVOLUTION_AI_DEMO_v1.0\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend (port 8501)...
start "EVOLUTION-FRONTEND" cmd /k "cd /d D:\API\EVOLUTION_AI_DEMO_v1.0 && python -m streamlit run app.py --server.port 8501"

timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   Starting browser...
echo ============================================
start http://localhost:8501

echo.
echo Done! Close this window will NOT stop the servers.
echo To stop, close the BACKEND and FRONTEND command windows.
pause
