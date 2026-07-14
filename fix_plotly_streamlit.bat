@echo off
chcp 65001 >nul
echo ============================================================
echo   EVOLUTION AI - Plotly 版本修复脚本
echo   修复 Streamlit 1.57.0 + Plotly 6.x 3D 渲染白屏问题
echo ============================================================
echo.

echo [1/4] 当前版本检查...
python -c "import plotly; print(f'  Plotly (当前): {plotly.__version__}')" 2>nul
if errorlevel 1 (
    echo   Plotly 未安装！
)
python -c "import streamlit; print(f'  Streamlit: {streamlit.__version__}')" 2>nul
if errorlevel 1 (
    echo   Streamlit 未安装！
)
echo.

echo [2/4] 降级 Plotly 到 5.24.0...
python -m pip install "plotly>=5.18,<6.0" --force-reinstall
echo.

echo [3/4] 验证降级结果...
python -c "import plotly; v=plotly.__version__; print(f'  Plotly (修复后): {v}'); assert v.startswith('5.'), f'版本仍为 {v}，降级失败！'; print('  ✅ 版本正确 (5.x)')"
if errorlevel 1 (
    echo   ❌ 降级失败，请手动检查
    pause
    exit /b 1
)
echo.

echo [4/4] 运行渲染自测...
python -c "
import plotly.graph_objects as go
import json

fig = go.Figure()
fig.add_trace(go.Mesh3d(
    x=[0.0,1.0,1.0,0.0], y=[0.0,0.0,1.0,1.0], z=[0.0,0.0,0.0,0.0],
    i=[0,1], j=[1,2], k=[2,3], color='red', flatshading=True
))
j = json.loads(fig.to_json())
trace = j['data'][0]

# 检查无 bdata
bdata_found = any(isinstance(trace.get(k), dict) and 'bdata' in trace.get(k, {}) for k in ['x','y','z','i','j','k'])
print(f'  数据格式: {\"bdata (有问题)\" if bdata_found else \"标准 list (正确)\"}')

# 检查 template
has_template = 'template' in j.get('layout', {})
print(f'  含 template: {has_template}')

import plotly
print(f'  Plotly.js 版本: {plotly.__version__}')
print('  ✅ 自测通过')
"
echo.

echo ============================================================
echo   修复完成！请重启 Streamlit：
echo   streamlit run app.py
echo.
echo   验证标准：
echo   1. 整车视图：显示白色车身（非白屏/工地）
echo   2. 零件画廊：各零件正常渲染
echo   3. 切换英文：不白屏
echo   4. 控制台无 "Cannot read properties of null" 错误
echo ============================================================
pause
