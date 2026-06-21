@echo off
chcp 65001 > nul
echo ========================================
echo EVOLUTION AI - 汽车A级曲面DEMO
echo ========================================
echo.

REM 激活虚拟环境（如果有）
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM 检查依赖
echo [检查依赖] ...
python -c "import streamlit, plotly, numpy, scipy" 2>nul
if errorlevel 1 (
    echo [安装依赖] ...
    python -m pip install -r requirements.txt
)

REM 启动服务
echo.
echo [启动] http://localhost:8501
echo.
streamlit run app.py --server.port 8501
pause
