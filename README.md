# EVOLUTION AI

> 下一代 AI 汽车造型开发平台 — 从一句话到 3D 整车，全链路 AI 辅助设计

![Status](https://img.shields.io/badge/status-W4%20complete-brightgreen) ![Version](https://img.shields.io/badge/version-2.1.0-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![Tests](https://img.shields.io/badge/tests-155%2F155%20PASSED-green) ![Docker](https://img.shields.io/badge/docker-ready-blue)

---

## 🎯 项目愿景

让汽车造型设计进入「**说一句话，就出 3D 整车**」的时代。

从概念草图 → 参数化建模 → AI 优化 → 视频分镜 → 曲面质量评估 → 工程交付，一气呵成。

---

## 📦 当前状态

| 里程碑 | 状态 | 周期 | 交付物 |
|--------|------|------|--------|
| **M0** 算法模型 | ✅ Done | — | `algorithm_model/`（37 文件 / 5 API / 7 CLI） |
| **M1** 后端骨架 | ✅ Done | 1 周 | `backend/`（17 端点 / FastAPI + Celery） |
| **M2** 数据+异步 | ✅ Done | 1 周 | SQLAlchemy ORM / 21 端点 / E2E 3s 闭环 |
| **W1** 前端 E2E | ✅ Done | 1 周 | Vue 3 + Three.js / 5 段曲面 30+124 测试 |
| **W2** 前端重构 | ✅ Done | 1 周 | Vite 分包 / 三区段融合 / 31 点截面弧长参数化 |
| **W3** 算法扩展 | ✅ Done | 1 周 | NURBS / 圆角 / 扫描 / Freeform / Cython 399× |
| **W4** 前端增强 | ✅ Done | 1 周 | freeform 滑块 / GLB+OBJ+STL 导出 / 反射线可视化 |
| **V2.1** 整车升级 | ✅ Done | 1 天 | 截面扫掠方案 / 超椭圆车身 / 6 款车型验证 |
| **Docker** 部署 | ✅ Ready | — | 多阶段构建 / Cython 编译 / Volume 持久化 |
| **Streamlit** 前端 | 🟡 ~95% | — | `app.py` 2541 行 / 双语 i18n / 整车渲染 |

---

## 🚀 快速开始

### 🌐 在线演示

**GitHub Pages**：https://EvolutionAI119.github.io/evolution-ai-demo/

### Docker 一键部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/EvolutionAI119/evolution-ai-demo.git
cd evolution-ai-demo

# 构建 + 启动（首次 3-5 分钟）
docker compose up -d

# 查看日志
docker compose logs -f
```

启动后访问：
- **Streamlit 前端**：http://localhost:8501
- **FastAPI 后端**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Streamlit
streamlit run app.py --server.port 8501

# 启动后端 API
cd backend && uvicorn main:app --port 8000 --reload
```

### 跑测试

```bash
# 算法模型测试（136 项）
cd algorithm_model && pytest tests/ -v

# 后端测试（19 项）
cd backend && pytest tests/ -v

# 全量自测
cd algorithm_model && python test_all.py
```

---

## 🏗️ V2.1 截面扫掠建模方案

V2.1 是整车建模算法的核心升级，从 Bezier Patch 拼接方案升级为**截面扫掠参数化建模**：

| 特性 | 说明 |
|------|------|
| **Hardpoint 推导** | 所有车身锚点由 22 维参数推导，单一事实来源 |
| **Smoothstep 轮廓** | 6 段连续过渡（Nose → Hood → A-Pillar → Roof → C-Pillar → Tail） |
| **Tumblehome 收腰** | 前翼最大宽 → 客舱收窄 → 后翼恢复 → 前后端收窄 |
| **超椭圆截面** | 60 站位 × 28 点 = 完整车身网格，`overall_arc` 控制指数 |
| **轮拱切割** | 前后轮拱自动切割车身网格 |
| **Cython 加速** | 399× 性能提升，0.40ms/板 |

### 22 维参数体系

| 类别 | 参数示例 | 范围 |
|------|---------|------|
| 基本尺寸 | L / W / H / 轴距 / 机盖长 / 座舱长 | 3.5-5.5m |
| 姿态 | 离地间隙 / 机盖倾角 / 车顶弧度 / 前挡倾角 | 按需 |
| 曲面特征 | 翼子板突出 / 腰线 / 肩线 / 整体弧度 | 按需 |
| 细节 | 大灯宽高 / 轮辐数 / 玻璃暗度 | 按需 |

### 6 款预设车型

| 车型 | L (mm) | W (mm) | H (mm) | 离地间隙 (mm) |
|------|--------|--------|--------|------------|
| Sedan | 4800 | 1850 | 1450 | 150 |
| SUV | 4900 | 1950 | 1750 | 200 |
| Coupe | 4700 | 1850 | 1350 | 130 |
| MPV | 5100 | 1900 | 1800 | 160 |
| Sport | 4500 | 1950 | 1250 | 110 |
| Pickup | 5500 | 1950 | 1850 | 220 |

---

## 📂 项目结构

```
evolution-ai-demo/
├── app.py                          ← Streamlit 前端（2541 行，双语 i18n）
├── car_body_builder.py             ← V2.1 整车建模入口
├── Dockerfile                      ← 多阶段构建（Cython 编译 + 运行）
├── docker-compose.yml              ← 一键部署（端口 8000 + 8501）
├── docker-entrypoint.sh            ← 容器启动脚本
├── start-docker.bat                ← Windows 双击启动
├── build_cython.sh                 ← Cython 编译脚本
├── requirements.txt                ← streamlit==1.39.0 / plotly / numpy / scipy
│
├── algorithm_model/                ← 算法核心（黑盒使用）
│   ├── api.py                      ← 5 大 API 入口
│   ├── car_modeling/               ← 整车建模（22 维参数 / 20+ 零件）
│   │   ├── assembler.py            ← 零件装配
│   │   ├── body.py                 ← 车身壳体（V2.1 截面扫掠）
│   │   ├── blending.py             ← 三区段融合
│   │   ├── glass.py                ← 座舱玻璃
│   │   ├── lights.py               ← 前/后灯
│   │   ├── wheels.py               ← 车轮（带轮辐）
│   │   ├── grille.py               ← 格栅
│   │   ├── mirrors.py              ← 后视镜
│   │   ├── parametrize.py          ← 31 点截面弧长参数化
│   │   ├── seams.py                ← 门缝
│   │   └── trim.py                 ← 装饰条
│   ├── freeform/                   ← NURBS 自由曲面库
│   │   ├── nurbs_core.py           ← Cox-de Boor 基函数
│   │   ├── freeform_surface.py     ← FFD 5 种预设 + 自定义
│   │   ├── fillet_surface.py       ← 圆角/倒角曲面
│   │   └── swept_surface.py        ← RMF 扫描曲面
│   ├── surface_quality/            ← 曲面质量评估
│   │   ├── continuity.py           ← G0/G1/G2 连续性
│   │   ├── curvature.py            ← 曲率分析
│   │   ├── grader.py               ← 质量分级
│   │   ├── optimizer.py            ← AI 优化器
│   │   └── reflection.py           ← 反射线分析
│   ├── storyboard/                 ← 视频分镜生成
│   ├── storyboard_viewer/          ← 分镜浏览器（HTML/Markdown）
│   ├── tests/                      ← 算法测试（136 项）
│   └── examples/                   ← 使用示例
│
├── backend/                        ← FastAPI 后端
│   ├── main.py                     ← 入口（23 端点）
│   ├── config.py                   ← Pydantic 配置
│   ├── api/v1/                     ← 路由（car / quality / optimize / storyboard）
│   ├── services/                   ← 薄壳服务层
│   ├── models/                     ← Pydantic 数据模型
│   ├── db/                         ← SQLAlchemy 2.0 ORM
│   ├── tasks/                      ← Celery 异步任务
│   └── tests/                      ← 后端测试（19 项）
│
├── docs/                           ← 项目文档
│   ├── ARCHITECTURE_DESIGN.md      ← 架构设计 v1.0（14 章）
│   ├── PRODUCT_SPEC.md             ← 产品功能定义
│   ├── W1_完结报告.md               ← W1 完工总结
│   ├── W2_完结报告.md               ← W2 完工总结
│   ├── W3_完结报告.md               ← W3 完工总结
│   ├── W4D4_反射线可视化_完工报告.md ← 反射线可视化文档
│   ├── DOCKER_部署指南.md           ← Docker 部署说明
│   ├── reflection_visualizer.html  ← 反射线可视化（独立 HTML）
│   └── embodied_3d_demo.html       ← 具身智能 3D 展示
│
├── core/                           ← 历史归档（车身建模 v0）
└── build/                          ← Cython 编译产物
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| **算法层** | Python 3.11+ / NumPy / SciPy / Trimesh / Cython（399× 加速） |
| **NURBS** | Cox-de Boor 基函数 / FFD / RMF 扫描 / 圆角倒角 |
| **前端** | Streamlit 1.39.0 + Plotly 5.x（整车 3D + 零件画廊 + 双语 i18n） |
| **前端独立** | Three.js + GLTFLoader（反射线可视化 / 具身智能展示） |
| **后端** | FastAPI / Pydantic v2 / Loguru / Uvicorn |
| **数据库** | SQLAlchemy 2.0 + SQLite |
| **异步队列** | Celery 5 + Redis（可选） |
| **部署** | Docker 多阶段构建 / docker-compose / Volume 持久化 |
| **导出** | GLB / OBJ / STL 三格式 |

---

## 📊 性能基线

| 场景 | 耗时 | 指标 |
|------|------|------|
| 整车构建（V2.1 截面扫掠） | ~200ms | 4862 顶点 / 9660 面 |
| Cython 加速单板 | 0.40ms | 399× 性能提升 |
| 球面质量评估 | 50.8ms | grade=D / G0 100% |
| RMF 扫描正交性 | — | 误差 1.65e-15 |
| 算法全量测试 | ~6s | 136/136 PASSED |
| 后端全量测试 | ~3s | 19/19 PASSED |
| Docker 镜像构建 | 3-5 分钟 | 含 Cython 编译 |

---

## 🎨 前端功能

### Streamlit App（`app.py`）
- **双语切换**：中/英文一键切换（i18N 字典）
- **22 维参数滑块**：实时驱动整车模型
- **6 款预设车型**：Sedan / SUV / Coupe / MPV / Sport / Pickup
- **整车 3D 视图**：Plotly 3D 渲染 + OrbitControls
- **零件画廊**：分部件展示（车身/玻璃/灯/轮/格栅/镜）
- **质量评估面板**：曲率热力图 + 质量等级 + 反射线评分
- **Freeform 变形**：5 种预设 + 自定义参数

### 独立 HTML 工具
- `reflection_visualizer.html`：反射线可视化（4 模式 / 6 预设曲面）
- `embodied_3d_demo.html`：具身智能 3D 动效展示
- `3d_avatar_showcase_embed.html`：3D Avatar 展示台

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计 v1.0](docs/ARCHITECTURE_DESIGN.md) | 5 层分层 + 4 里程碑 |
| [产品功能定义](docs/PRODUCT_SPEC.md) | 需求与场景 |
| [V2.1 升级说明](V21_UPGRADE_README.md) | 截面扫掠方案详解 |
| [W1 完结报告](docs/W1_完结报告.md) | 前端 E2E |
| [W2 完结报告](docs/W2_完结报告.md) | 前端重构 |
| [W3 完结报告](docs/W3_完结报告.md) | 算法扩展 155 测试 |
| [反射线可视化](docs/W4D4_反射线可视化_完工报告.md) | W4-D4 完工报告 |
| [Docker 部署指南](docs/DOCKER_部署指南.md) | 一键启动说明 |
| [算法模型文档](algorithm_model/README.md) | 5 大 API + 7 CLI |
| [Freeform 模块](algorithm_model/freeform/README.md) | NURBS / FFD / 圆角 / 扫描 |

---

## 🧩 Coze 技能

EVOLUTION AI 算法核心已发布为 Coze 技能：

| 技能 | 说明 |
|------|------|
| [AI 汽车造型开发](https://www.coze.cn/store/skill/7653081413079646242) | 参数化整车建模 + AI 优化 + 视频分镜 |
| [测试优化技能](https://www.coze.cn/store/skill/7621182441138536484) | A 级曲面全流程工作流 |

---

## 🧪 测试覆盖

| 测试集 | 数量 | 覆盖模块 |
|--------|------|---------|
| `test_freeform.py` | 37 | NURBS 基函数 / FFD 5 预设 |
| `test_fillet.py` | 28 | 圆角 / 倒角 / 可变半径 |
| `test_swept.py` | 46 | RMF 扫描 / 3 种截面 / 装饰条 |
| `test_blending.py` | 32 | 三区段融合 / 零值处理 |
| `test_parametrize.py` | 32 | 31 点截面 / 弧长参数化 |
| `test_performance.py` | 9 | 性能基准 |
| `test_quality.py` | 16 | G0/G1/G2 / 曲率 / 体积 / 拓扑 |
| `test_api.py` + `test_export.py` | 26 | 后端 API / GLB+OBJ+STL 导出 |
| `test_cython_accel.py` | 15 | Cython 399× 加速验证 |
| `test_m2_e2e.py` | 4 | M2 端到端 |
| **合计** | **155/155 PASSED** | **零回归** |

---

## 📝 开发规范

- **算法层零修改**：`algorithm_model/` 是黑盒，service 层只调不写
- **后端服务薄壳**：每个 service 10-50 行，纯调度
- **字段 100% 对齐**：Pydantic model 与 algorithm_model 数据类签名严格一致
- **测试驱动**：新功能必须配测试用例
- **Streamlit 版本锁定**：`streamlit==1.39.0`（1.59.x 前端有 bug 导致白屏）
- **Cython 可选**：无 .so 时自动回退纯 Python 实现

---

## 📜 License

Proprietary — 内部项目

---

<p align="center">
  <em>「说一句话，就出 3D 整车」— EVOLUTION AI</em>
</p>
