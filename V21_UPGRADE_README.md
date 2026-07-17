# EVOLUTION AI — V2.1 整车造型算法升级说明

## 升级概述

本次升级将整车建模算法从 **Bezier Patch 拼接方案** 升级为 **V2.1 截面扫掠参数化建模方案**，解决了原方案生成模型"像透明盒子"的问题，实现了真实汽车造型特征。

## 核心改进

### 1. Hardpoint 推导系统
所有车身关键锚点（轮心、A柱、C柱、腰线、引擎盖等）均由 22 维参数推导得出，形成**单一事实来源**（Single Source of Truth）。

### 2. Smoothstep 侧视图轮廓曲线
使用五次 smoothstep 插值实现 6 段连续过渡：
- **Nose** (t<0.08): 鼻尖上升
- **Hood** (0.08-0.20): 引擎盖
- **A-Pillar** (0.20-0.40): A柱 → 车顶
- **Roof** (0.40-0.60): 平坦段 + 弧度
- **C-Pillar** (0.60-0.80): C柱下降
- **Tail** (0.80-1.00): 尾部收尾

### 3. 俯视图宽度曲线（Planform）
Tumblehome 收腰设计：
- 前翼子板最大宽度（95%）
- 客舱区域收窄（86%）
- 后翼子板恢复最大宽度
- 前后端收窄

### 4. 超椭圆截面扫掠
- **60 个站位 × 28 个点** = 完整车身网格
- 超椭圆指数由 `overall_arc` 参数控制
- 肩线凸起、Tumblehome 收窄

### 5. 轮拱切割
前后轮拱自动切割车身网格，形成真实的轮拱造型。

### 6. 新增零部件
- 车身壳体（统一 sweep body）
- 座舱玻璃区（greenhouse）
- 大灯（前）× 2
- 尾灯（后）× 2
- 带轮辐的车轮 × 4

## 22 维参数体系

| 类别 | 参数 | 说明 | 范围 |
|------|------|------|------|
| 基本尺寸 | L, W, H | 总长/宽/高 | 3.5-5.5m |
| 基本尺寸 | WB | 轴距 | 2.2-3.6m |
| 基本尺寸 | hood_len | 引擎盖长 | 0.8-1.3m |
| 基本尺寸 | cabin_len | 客舱长 | 1.2-2.5m |
| 基本尺寸 | trunk_len | 行李箱长 | 0.5-1.8m |
| 姿态 | GC | 离地间隙 | 0.08-0.25m |
| 姿态 | hood_angle | 引擎盖倾角 | 5-25° |
| 姿态 | roof_arc | 车顶弧度 | 0-1 |
| 姿态 | windshield_rake | 前挡倾角 | 15-45° |
| 姿态 | rear_glass_angle | 后风窗倾角 | 10-45° |
| 曲面特征 | fender_prominence | 翼子板突出 | 0-0.08m |
| 曲面特征 | waist_line | 腰线高度比 | 0.5-0.95 |
| 曲面特征 | shoulder_line | 肩线凸起 | 0-0.03m |
| 曲面特征 | overall_arc | 整体弧度 | 0-1 |
| 曲面特征 | glass_darkness | 玻璃暗度 | 0-1 |
| 曲面特征 | WR | 轮半径 | 0.25-0.40m |
| 曲面特征 | WW | 轮宽 | 0.15-0.28m |
| 曲面特征 | spoke_count | 轮辐数 | 3-10 |
| 细节 | headlight_w | 大灯宽 | 0.2-0.5m |
| 细节 | headlight_h | 大灯高 | 0.05-0.15m |

## 六车型默认参数

| 车型 | L (mm) | W (mm) | H (mm) | WB (mm) | GC (mm) | WR (mm) |
|------|--------|--------|--------|---------|---------|---------|
| sedan | 4800 | 1850 | 1450 | 2800 | 150 | 320 |
| suv | 4900 | 1950 | 1750 | 2850 | 200 | 360 |
| coupe | 4700 | 1850 | 1350 | 2700 | 130 | 320 |
| mpv | 5100 | 1900 | 1800 | 3000 | 160 | 340 |
| sport | 4500 | 1950 | 1250 | 2650 | 110 | 330 |
| pickup | 5500 | 1950 | 1850 | 3400 | 220 | 375 |

## 文件清单

| 文件 | 说明 |
|------|------|
| `car_body_builder.py` | **新增** — V2.1 截面扫掠建模核心模块 |
| `app.py` | **更新** — 集成 V2.1 模块，新增车型和 I18N |
| `hot_update_v21.sh` | **新增** — Linux/Mac Docker 热更新脚本 |
| `hot_update_v21.bat` | **新增** — Windows Docker 热更新脚本 |
| `V21_UPGRADE_README.md` | 本文件 |

## Docker 热更新（无需重建镜像）

### Linux / macOS
```bash
chmod +x hot_update_v21.sh
./hot_update_v21.sh
```

### Windows
```cmd
hot_update_v21.bat
```

### 手动更新
```bash
# 1. 复制文件到容器
docker cp car_body_builder.py evolution-ai:/app/car_body_builder.py
docker cp app.py evolution-ai:/app/app.py

# 2. 重启容器内应用
docker exec evolution-ai pkill -f streamlit
docker exec evolution-ai bash -c "cd /app && streamlit run app.py &"
```

## API 接口兼容性

所有现有 API 接口保持不变：
- `POST /api/v1/build` — 构建整车（内部自动使用 V2.1）
- `GET /api/v1/quality` — 质量评估
- `POST /api/v1/optimize` — AI 优化
- `GET /api/v1/export` — 数据导出

## 回退机制

如果 V2.1 模块加载失败，系统自动回退到原有 Bezier Patch 方案，确保服务不中断。
