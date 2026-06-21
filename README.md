# EVOLUTION AI

> 下一代 AI 汽车造型开发平台 — 从一句话到 3D 整车，全链路 AI 辅助设计

![Status](https://img.shields.io/badge/status-M2%20done-brightgreen) ![Version](https://img.shields.io/badge/version-0.2.0-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-blue)

---

## 🎯 项目愿景

让汽车造型设计进入「**说一句话，就出 3D 整车**」的时代。
从概念草图 → 参数化建模 → AI 优化 → 视频分镜 → 工程交付，一气呵成。

---

## 📦 当前状态

| 里程碑 | 状态 | 工期 | 交付物 |
|--------|------|------|--------|
| **M0** 算法模型 | ✅ Done | - | `algorithm_model/`（30 文件 / 5 API / 7 CLI，5/5 自检 9.49s） |
| **M1** 后端骨架 | ✅ Done | 1 周 | `backend/`（26 文件 / 17 端点 / 15/15 测试通过 3.04s） |
| **M2** 数据+异步 | ✅ Done | 1 周 | 4 张表（SQLAlchemy 2.0 ORM）/ Celery + Redis / 21 端点 / 19/19 测试 / 端到端 3s 闭环 |
| **M3** 前端 | ⏳ Pending | 2 周 | Vue 3 + Three.js + WebSocket |
| **M4** 部署 | ⏳ Pending | 1 周 | Docker + Nginx + 监控 |

---

## 🚀 快速开始

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

#### 2.1 起 Redis（M2 必装）
```bash
# Linux / macOS
redis-server --daemonize yes --port 6379
redis-cli ping  # 应返回 PONG
```
> Windows 用户需先装 Redis（推荐 WSL 或 Memurai）。

#### 2.2 起 Celery worker（M2 必起）
```bash
# Linux / macOS
./start_celery_worker.sh

# Windows
start_celery_worker.bat
```

#### 2.3 起 FastAPI 服务
```bash
# Linux / macOS
./start_backend.sh

# Windows
start_backend.bat
```

服务跑起来后：
- **API 文档**：http://localhost:8000/docs
- **OpenAPI Schema**：http://localhost:8000/openapi.json
- **健康检查**：http://localhost:8000/health

### 3. 跑测试
```bash
cd backend
pytest tests/ -v
```

### 4. 调算法层（独立使用）
```bash
cd algorithm_model
python cli.py quick
# 跑 5/5 自检，约 9.5 秒
```

---

## 🏗️ 架构设计

详见：[`docs/ARCHITECTURE_DESIGN.md`](docs/ARCHITECTURE_DESIGN.md)（14 章 / 1.0 版）

**核心架构 5 层分层**：
```
L1 前端层  ─  Vue 3 + Three.js + WebSocket
L2 API 网关  ─  FastAPI + CORS + 静态资源
L3 服务层  ─  6 大薄壳服务（编排不重写）
L4 算法层  ─  algorithm_model（5 大 API / 7 CLI）
L5 基础设施  ─  文件存储 / 日志 / 配置
```

**4 个关键设计决策**：
1. ✅ 算法模型与 Web 完全解耦（可 pip install）
2. ✅ 后端只做编排，不重写算法
3. ✅ 异步优先（>1s 操作必异步）
4. ✅ 5 大 API 数据类签名冻结

---

## 📂 项目结构

```
EVOLUTION_AI/
├── README.md                       ← 你在这里
├── docs/
│   └── ARCHITECTURE_DESIGN.md     ← 架构设计 v1.0
├── algorithm_model/                ← M0 算法核心（黑盒使用）
│   ├── api/                        ← 5 大 API（build_car / assess_quality / ...）
│   ├── core/                       ← 算法实现（NURBS / 优化 / 评估）
│   ├── models/                     ← 数据类（字段签名已冻结）
│   ├── cli.py                      ← CLI 入口
│   └── quick_test.py               ← 5/5 自检
├── backend/                        ← M1+M2 后端（异步 + 数据持久化）
│   ├── main.py                     ← FastAPI 入口（21 端点）
│   ├── config.py                   ← 配置（Pydantic + env_prefix=EVOLUTION_）
│   ├── deps.py                     ← 依赖注入
│   ├── api/v1/                     ← 6 大路由（project / car / optimize / storyboard / quality / task）
│   ├── services/                   ← 6 大薄壳服务
│   ├── models/                     ← 5 大 Pydantic 模型
│   ├── db/                         ← M2 新增：SQLAlchemy 2.0 ORM（4 表）
│   │   ├── base.py                 ← DeclarativeBase + snake_case
│   │   ├── session.py              ← engine + SessionLocal + get_db
│   │   └── models.py               ← Project / CarModel / QualityReport / OptimizationTask
│   ├── tasks/                      ← M2 新增：Celery 异步任务
│   │   ├── celery_app.py           ← Celery 实例（Redis broker/backend）
│   │   └── optimize_task.py        ← @celery_app.task 优化任务
│   ├── algorithm_compat.py         ← 算法层 sys.path 注入兼容层
│   ├── tests/                      ← 19 个测试用例（M1 15 + M2 4）
│   ├── outputs/                    ← 静态产物 + evolution_ai.db
│   ├── start_backend.sh            ← Linux 启动
│   ├── start_backend.bat           ← Windows 启动
│   ├── start_celery_worker.sh      ← M2 新增：Celery 启动（Linux）
│   ├── start_celery_worker.bat     ← M2 新增：Celery 启动（Windows）
│   └── requirements.txt
├── core/                           ← 历史归档（完整车身建模 v0）
├── legacy/                         ← v0.1 Streamlit 玩具版
└── ...
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| **算法层** | Python 3.11+ / NumPy / SciPy / Trimesh / Plotly |
| **后端** | FastAPI / Pydantic v2 / Loguru / Uvicorn |
| **前端（M3）** | Vue 3 / Three.js / WebSocket |
| **数据库（M2）** | SQLAlchemy 2.0 + SQLite（先）/ PostgreSQL（后） |
| **异步队列（M2）** | Celery 5 + Redis 6 |
| **部署（M4）** | Docker + Nginx + Prometheus + Grafana |

---

## 📊 性能基线

| 场景 | 耗时 | 指标 |
|------|------|------|
| 整车构建 | ~200ms | 3475 顶点 / 6504 面 |
| 球面质量评估 | 50.8ms | grade=D / g2=0.199 / reflection=0.314 |
| M1 后端测试 | 3.04s | 15/15 通过 |
| M2 端到端测试 | 7.85s | 19/19 通过（M1 15 + M2 4） |
| uvicorn 启动 | 4s | 21 端点全部注册 |
| M2 异步优化（sphere/30 iter） | 0.62s | 算法耗时；端到端 3s 含调度 |
| M2 任务消费延迟 | 0.8-1.5s | PENDING → STARTED 间隔 |

---

## 🎬 3 套预设方案

| 方案 | L (m) | W (m) | H (m) | 风格 |
|------|-------|-------|-------|------|
| **sport** | 4.50 | 1.85 | 1.30 | 跑车 |
| **luxury** | 5.20 | 1.95 | 1.50 | 豪华轿车 |
| **suv** | 4.80 | 1.95 | 1.72 | SUV |

API 调 `GET /api/v1/car/presets` 查看完整 22 维参数。

---

## 📚 文档导航

- [架构设计 v1.0](docs/ARCHITECTURE_DESIGN.md) — 5 层分层 + 4 里程碑 5 周
- [产品功能定义](docs/PRODUCT_SPEC.md) — 需求与场景
- [算法模型文档](algorithm_model/README.md) — 5 大 API + 7 CLI 速查
- [M1+M2 后端测试](backend/tests/) — 19 个测试用例

---

## 🧩 Coze 技能

EVOLUTION AI 算法核心已发布为 Coze 技能 `ai-car-styling` v4：
- 技能 ID：`7653081413079646242`
- 部署 ID：`7653079383841718272`
- 商店链接：https://www.coze.cn/store/skill/7653081413079646242

可独立用作 AI 汽车造型开发的通用能力。

---

## 📝 开发规范

- **算法层零修改**：`algorithm_model/` 是黑盒，service 层只调不写
- **后端服务薄壳**：每个 service 10-50 行，纯调度
- **字段 100% 对齐**：Pydantic model 与 algorithm_model 数据类签名必须严格一致
- **测试驱动**：新功能必须配测试用例
- **M2 异步约定**：>1s 操作走 Celery，API 返回 `202 + task_id`，客户端轮询 `GET /api/v1/task/{tid}`

---

## 🤝 协作约定

- **主对话渠道**：Coze
- **沟通风格**：先结论后依据；少解释过程
- **格式**：Coze 用 Markdown；文件用绝对路径引用
- **桌面前缀**：`D:\API\AI_3D_Model_Build\EVOLUTION_AI\`

---

## 📜 License

Proprietary — 内部项目

---

<p align="center">
  <em>「说一句话，就出 3D 整车」— EVOLUTION AI</em>
</p>
# Evolution AI · 汽车造型开发平台

W1 完工前端展示 · 详见 docs/W1_完结报告.md
部署地址：https://EvolutionAI119.github.io/evolution-ai-demo/
