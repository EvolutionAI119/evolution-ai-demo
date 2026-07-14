# EVOLUTION AI 项目架构设计 v1.0

> **作者**：灵感解药
> **时间**：2026-06-19
> **状态**：已批准，待实施
> **版本基线**：算法模型 v1.0.0（5/5 自检通过，9.49s）

---

## 0. 项目定位

**EVOLUTION AI** —— 参数化 + AI 驱动的汽车造型开发平台

**核心闭环**：
```
参数化建模 → 曲面质量评估 → AI 自动优化 → 视频脚本生成
   (3D)        (G0/G1/G2)     (退火)        (90s分镜)
```

**目标用户**：
- **主用户（主人/量子剑客）**：汽车系统开发从业者，技术决策 + 演示
- **下游用户**：造型设计师、评审委员会、对外销售演示

**差异化**：
- 不是 DEMO 玩具 —— 是可工程化部署的全栈产品
- 算法可独立剥离（不依赖 Web）—— 算法模型包已就绪
- 完整数据闭环（方案库 + 评估历史 + 优化曲线）

---

## 1. 全景架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                        EVOLUTION AI 架构                            │
│                                                                     │
│  ╔══════════════════════════════════════════════════════════════╗  │
│  ║                    L1: 表现层 (Frontend)                      ║  │
│  ╠══════════════════════════════════════════════════════════════╣  │
│  ║  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     ║  │
│  ║  │参数编辑器│  │3D 预览   │  │质量报告  │  │AI 优化   │     ║  │
│  ║  │(Vue 3)   │  │(Three.js)│  │(ECharts) │  │(实时进度)│     ║  │
│  ║  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     ║  │
│  ║       └─────────────┴──────┬───────┴──────────────┘           ║  │
│  ╚═════════════════════════════╪═════════════════════════════════╝  │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  L2: API 网关层 (FastAPI + Uvicorn + Nginx)                  │   │
│  │  ─ REST API: /api/v1/{car|quality|optimize|storyboard}      │   │
│  │  ─ WebSocket: /ws/optimize/{task_id}  (实时进度推送)         │   │
│  │  ─ 静态资源: /static/{glb|png|html}                         │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  L3: 业务服务层 (Service Layer)                              │   │
│  │  ─ 建模服务    (CarModelService)                             │   │
│  │  ─ 评估服务    (QualityService)                              │   │
│  │  ─ 优化服务    (OptimizeService, 异步任务)                  │   │
│  │  ─ 脚本服务    (StoryboardService)                          │   │
│  │  ─ 导出服务    (ExportService: GLB/STL/OBJ/PNG)            │   │
│  │  ─ 方案服务    (ProjectService: 增删改查)                   │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  L4: 算法核心层 (algorithm_model/) ← 已交付 ✅               │   │
│  │  ─ car_modeling/      (参数化车身建模, 8 部件)               │   │
│  │  ─ surface_quality/   (G0/G1/G2 评估 + AI 优化)              │   │
│  │  ─ storyboard/        (3 套模板 + 自定义分镜)                │   │
│  │  ─ storyboard_viewer/ (Markdown + HTML 渲染)                 │   │
│  │  ─ api.py              (5 大统一门面 API)                    │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  L5: 基础设施层 (Infrastructure)                             │   │
│  │  ─ 数据: SQLite (方案库) + JSON (评估历史)                   │   │
│  │  ─ 缓存: Redis (优化任务结果 / 会话)                         │   │
│  │  ─ 队列: Celery (异步 AI 优化任务)                           │   │
│  │  ─ 监控: Loguru + Prometheus  (后续 M4 引入)                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术选型

| 层级 | 选型 | 理由 | 状态 |
|------|------|------|------|
| **前端框架** | Vue 3 + Vite | 渐进式，TypeScript 友好，生态成熟 | 待引入 |
| **3D 渲染** | Three.js | 业界标准，GLB/OBJ 格式原生支持 | 待引入 |
| **3D 高保真** | (可选) Blender + Python API | 静态图 / 视频出图 | M3 引入 |
| **数据可视化** | ECharts | 国产开源，中文友好，曲线/雷达图强 | 待引入 |
| **UI 组件** | Element Plus | Vue 3 官方推荐 | 待引入 |
| **后端框架** | FastAPI | 异步原生，自动 OpenAPI 文档，Pydantic 校验 | 核心 |
| **ASGI 服务器** | Uvicorn | 性能稳定，FastAPI 官方推荐 | 核心 |
| **数据校验** | Pydantic v2 | FastAPI 原生 | 核心 |
| **算法层** | algorithm_model/ | 已交付，30 文件，5/5 自检 | ✅ 就绪 |
| **数据库** | SQLite (开发) / PostgreSQL (生产) | 轻量起步，零配置 | M2 引入 |
| **缓存** | Redis (可选) | 优化任务结果缓存 | M3 引入 |
| **异步任务** | Celery + Redis broker | AI 优化耗时 5s+，需异步 | M2 引入 |
| **数据迁移** | Alembic | SQLAlchemy 官方 | M2 引入 |
| **日志** | Loguru | 比 logging 简单 10 倍 | 核心 |
| **测试** | pytest + httpx | FastAPI 官方推荐 | 核心 |
| **容器化** | Docker + docker-compose | 一键启动 | M4 引入 |
| **反向代理** | Nginx (生产) | 静态资源 + HTTPS | M4 引入 |

---

## 3. 目录结构（目标）

```
D:\API\AI_3D_Model_Build\EVOLUTION_AI\
│
├── README.md                          # 项目总览（待写）
├── ARCHITECTURE.md                    # 本文档
├── docker-compose.yml                 # 一键启动编排（M4）
├── .env.example                       # 环境变量模板
├── pyproject.toml                     # 项目元数据 + 依赖（poetry/uv）
│
├── algorithm_model/                   # ★ L4 算法核心层（已就绪）
│   ├── __init__.py                    #   __version__ = "1.0.0"
│   ├── api.py                         #   5 大门面 API
│   ├── main.py                        #   CLI 入口
│   ├── test_all.py                    #   5/5 自检
│   ├── README.md                      #   使用文档
│   ├── requirements.txt
│   ├── car_modeling/                  #   8 部件建模
│   ├── surface_quality/               #   G0/G1/G2 + AI 优化
│   ├── storyboard/                    #   3 套分镜模板
│   ├── storyboard_viewer/             #   MD + HTML 渲染
│   ├── examples/                      #   3 个示例
│   └── outputs/                       #   产物输出
│
├── backend/                           # ★ L2-L3 FastAPI 后端（待建）
│   ├── __init__.py
│   ├── main.py                        #   FastAPI app 入口
│   ├── config.py                      #   Pydantic Settings
│   ├── deps.py                        #   依赖注入
│   │
│   ├── api/                           #   路由层
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── car.py                 #   /api/v1/car/* (建模)
│   │   │   ├── quality.py             #   /api/v1/quality/* (评估)
│   │   │   ├── optimize.py            #   /api/v1/optimize/* (优化)
│   │   │   ├── storyboard.py          #   /api/v1/storyboard/* (脚本)
│   │   │   ├── project.py             #   /api/v1/project/* (方案库)
│   │   │   └── export.py              #   /api/v1/export/* (导出)
│   │   └── websocket/
│   │       └── optimize.py            #   /ws/optimize/{task_id}
│   │
│   ├── services/                      #   业务服务层
│   │   ├── car_model_service.py       #   封装 build_car
│   │   ├── quality_service.py         #   封装 evaluate_surface
│   │   ├── optimize_service.py        #   封装 optimize_surface
│   │   ├── storyboard_service.py      #   封装 make_storyboard
│   │   ├── export_service.py          #   GLB/STL/OBJ 转换
│   │   └── project_service.py         #   方案库 CRUD
│   │
│   ├── models/                        #   Pydantic 数据模型
│   │   ├── car.py                     #   CarParams API 形态
│   │   ├── quality.py                 #   QualityReport API 形态
│   │   ├── optimize.py                #   OptimizationResult API 形态
│   │   ├── storyboard.py
│   │   └── project.py                 #   ORM 模型
│   │
│   ├── db/                            #   L5 数据层
│   │   ├── __init__.py
│   │   ├── base.py                    #   SQLAlchemy 基础
│   │   ├── session.py                 #   session 管理
│   │   └── migrations/                #   Alembic
│   │
│   ├── tasks/                         #   异步任务 (Celery)
│   │   ├── celery_app.py
│   │   └── optimize_task.py           #   AI 优化任务
│   │
│   ├── utils/                         #   工具
│   │   ├── logger.py                  #   Loguru 配置
│   │   ├── file_storage.py            #   文件存储抽象
│   │   └── validators.py
│   │
│   └── tests/                         #   后端测试
│       ├── test_car.py
│       ├── test_quality.py
│       ├── test_optimize.py
│       └── test_storyboard.py
│
├── frontend/                          # ★ L1 前端（待建）
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   ├── stores/                    #   Pinia 状态管理
│   │   ├── api/                       #   axios 封装
│   │   ├── components/
│   │   │   ├── ParamEditor/           #   22 维参数编辑器
│   │   │   ├── CarPreview/            #   Three.js 3D 预览
│   │   │   ├── QualityReport/         #   评估报告
│   │   │   ├── OptimizeProgress/      #   优化进度 (WebSocket)
│   │   │   ├── StoryboardView/        #   分镜展示
│   │   │   └── ProjectList/           #   方案库
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   ├── Designer.vue           #   设计师主界面
│   │   │   ├── Quality.vue
│   │   │   ├── Optimize.vue
│   │   │   ├── Storyboard.vue
│   │   │   └── Projects.vue
│   │   └── assets/
│   └── public/
│
├── outputs/                           #   产物集中目录
│   ├── cars/                          #     GLB 模型
│   ├── reports/                       #     评估报告
│   ├── storyboards/                   #     分镜 (md/html/json)
│   └── snapshots/                     #     静态图 (PNG)
│
├── docs/                              #   文档
│   ├── ARCHITECTURE.md                #     本文档
│   ├── PRODUCT_SPEC.md                #     产品功能定义
│   ├── API.md                         #     API 文档
│   ├── DEPLOYMENT.md                  #     部署指南
│   ├── 算法模型交付总结.md
│   └── 视频脚本展示功能整合总结.md
│
└── scripts/                           #   运维脚本
    ├── start_dev.sh                   #     开发启动
    ├── start_prod.sh                  #     生产启动
    └── seed_data.py                   #     种子数据
```

---

## 4. 数据流

### 4.1 主流程：参数 → 3D 模型

```
用户 (Vue3)
   │ 1. 调整 22 维参数
   ▼
前端 ParamEditor
   │ 2. POST /api/v1/car/build  {params}
   ▼
FastAPI 路由
   │ 3. 调用 CarModelService
   ▼
algorithm_model.api.build_car(params)
   │ 4. 返回 8 部件 dict
   ▼
ExportService.to_glb(parts)
   │ 5. 合并 + 编码 GLB
   ▼
Response { glb_url, stats }
   │
   ▼
前端 CarPreview
   │ 6. GLTFLoader 加载 /static/cars/{hash}.glb
   ▼
Three.js 渲染
```

### 4.2 AI 优化（异步 + WebSocket）

```
用户点击"开始优化"
   │ 1. POST /api/v1/optimize/start  {surface_id, max_iter}
   ▼
FastAPI 路由
   │ 2. 生成 task_id，推入 Celery
   │ 3. 立即返回 { task_id, ws_url }
   ▼
前端建立 WebSocket
   │ 4. WS /ws/optimize/{task_id}
   ▼
Celery Worker 执行 algorithm_model.api.optimize_surface
   │ 5. 每 10 步 publish {progress, best_score, g2_ratio}
   ▼
WebSocket 推送到前端
   │ 6. OptimizeProgress 组件实时更新
   ▼
完成后推送 {done: true, result_url}
   │
   ▼
前端 QualityReport 渲染最终报告
```

### 4.3 视频脚本生成

```
用户在 Optimize.vue 完成
   │ 1. POST /api/v1/storyboard/generate  {product_name, style, ...}
   ▼
StoryboardService
   │ 2. 调用 make_storyboard
   │ 3. 调用 render_storyboard(md) + render_storyboard(html)
   │ 4. 保存到 outputs/storyboards/{id}.{md,html,json}
   ▼
Response { storyboard_id, md_url, html_url, json_url }
   │
   ▼
前端 StoryboardView 内嵌展示
```

---

## 5. API 设计

### 5.1 REST API

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/car/params/default` | 默认参数 | - | CarParams |
| POST | `/api/v1/car/build` | 构建 3D 模型 | CarParams | {glb_url, stats, parts_count} |
| POST | `/api/v1/car/validate` | 参数越界校验 | CarParams | {valid, errors} |
| POST | `/api/v1/quality/assess` | 评估曲面 | {points, panel_name} | QualityReport |
| POST | `/api/v1/optimize/start` | 启动优化 | {points, panel_name, max_iter} | {task_id, ws_url} |
| GET | `/api/v1/optimize/{task_id}` | 查询优化结果 | - | OptimizationResult |
| POST | `/api/v1/storyboard/generate` | 生成分镜 | {product_name, style, ...} | {md, html, json} |
| GET | `/api/v1/storyboard/templates` | 列出模板 | - | [template_name, ...] |
| GET | `/api/v1/project/list` | 方案列表 | ?skip&limit | [Project, ...] |
| POST | `/api/v1/project/save` | 保存方案 | {name, params, ...} | {project_id} |
| GET | `/api/v1/export/{format}/{id}` | 导出 | ?format=glb/stl/obj | file |

### 5.2 WebSocket

| 路径 | 功能 | 消息格式 |
|------|------|---------|
| `/ws/optimize/{task_id}` | 优化进度 | `{progress: 0~100, best_score, g2_ratio, current_iter, done}` |

### 5.3 OpenAPI 文档

FastAPI 自动生成 `/docs`（Swagger UI）和 `/redoc`，无需额外配置。

---

## 6. 关键子系统设计

### 6.1 CarModelService（建模服务）

**职责**：参数校验 → 调 build_car → 导出 GLB → 缓存

```python
class CarModelService:
    def build(self, params: CarParams) -> BuildResult:
        # 1. Pydantic 校验（已在 CarParams.validate()）
        # 2. 调 algorithm_model.api.build_car
        parts = build_car(params)
        # 3. 合并 + GLB 编码
        glb_bytes = trimesh.util.concatenate(list(parts.values())).export(file_type='glb')
        # 4. 存文件 + 算 hash
        glb_hash = sha256(glb_bytes).hexdigest()[:16]
        path = f"outputs/cars/{glb_hash}.glb"
        # 5. 返回 URL
        return BuildResult(glb_url=f"/static/cars/{glb_hash}.glb", stats=...)
```

**缓存策略**：相同 params hash 命中缓存（Redis，M3 引入）

### 6.2 OptimizeService（异步优化服务）

**为什么异步**：AI 优化 80 步 5s+（已测），同步会阻塞

```python
# tasks/optimize_task.py
@celery_app.task(bind=True)
def run_optimize(self, points, panel_name, max_iter, task_id):
    def progress_cb(iter, best_score, g2):
        self.update_state(state='PROGRESS', meta={
            'iter': iter, 'best_score': best_score, 'g2_ratio': g2
        })
        redis.publish(f'optimize:{task_id}', json.dumps(meta))
    result = optimize_surface(points, panel_name, max_iter, progress_cb=progress_cb)
    redis.set(f'optimize:result:{task_id}', pickle.dumps(result), ex=3600)
    return result
```

### 6.3 ProjectService（方案库）

**Schema**（SQLAlchemy）：

```python
class Project(Base):
    __tablename__ = "projects"
    id: int = Column(primary_key=True)
    name: str = Column(String(100), index=True)
    description: str = Column(Text)
    params_json: str = Column(Text)  # CarParams.to_dict()
    quality_json: str = Column(Text, nullable=True)
    optimize_json: str = Column(Text, nullable=True)
    storyboard_json: str = Column(Text, nullable=True)
    glb_path: str = Column(String(200), nullable=True)
    created_at: datetime
    updated_at: datetime
    tags: str = Column(String(200))  # 逗号分隔
```

### 6.4 ExportService（导出服务）

支持格式：
- **GLB**（主用，Three.js / Web 原生）
- **STL**（3D 打印）
- **OBJ**（Blender / Maya 通用）
- **PNG**（matplotlib 静态图）

```python
class ExportService:
    def to_glb(self, parts) -> bytes: ...
    def to_stl(self, parts) -> bytes: ...
    def to_obj(self, parts) -> bytes: ...
    def to_png(self, parts, view='iso') -> bytes:  # matplotlib 三视图
```

---

## 7. 前端架构

### 7.1 路由结构

```
/                       # 首页 (项目概览)
/designer               # 设计师主界面 (参数 + 预览)
  ├─ /designer/params   # 参数编辑
  ├─ /designer/preview  # 3D 预览
  └─ /designer/export   # 导出
/quality                # 质量评估
/optimize               # AI 优化 (WebSocket)
/storyboard             # 视频脚本
/projects               # 方案库
  └─ /projects/:id      # 方案详情
```

### 7.2 状态管理（Pinia）

```typescript
// stores/car.ts
export const useCarStore = defineStore('car', {
  state: () => ({
    params: defaultCarParams,
    glbUrl: null,
    stats: null,
    loading: false,
  }),
  actions: {
    async build() { /* POST /api/v1/car/build */ },
    async validate() { /* POST /api/v1/car/validate */ },
  },
})

// stores/optimize.ts
export const useOptimizeStore = defineStore('optimize', {
  state: () => ({
    taskId: null,
    ws: null,
    progress: 0,
    bestScore: null,
    g2Ratio: null,
    done: false,
  }),
  actions: {
    start() { /* POST /api/v1/optimize/start + WS */ },
  },
})
```

### 7.3 Three.js 集成

- **GLTFLoader** 加载 GLB
- **OrbitControls** 旋转缩放
- **网格化 + 材质**：
  - 车壳：金属漆材质（MeshStandardMaterial，metalness=0.7）
  - 玻璃：透明 + 反射（MeshPhysicalMaterial，transmission=0.9）
  - 轮毂：金属 + 辐条
  - 灯：自发光（emissive）

```typescript
// components/CarPreview.vue 核心
const loader = new GLTFLoader()
loader.load(props.glbUrl, (gltf) => {
  const model = gltf.scene
  model.traverse((child) => {
    if (child.isMesh) {
      // 根据 part name 设置材质
      applyMaterial(child)
    }
  })
  scene.add(model)
})
```

---

## 8. 性能基线（已测）

| 操作 | 耗时 | 数据量 | 备注 |
|------|------|--------|------|
| `build_car()` 默认参数 | ~200ms | 3475 顶点 / 6504 面 | 含合并 |
| `build_car()` 自定义 | ~250ms | 3539 顶点 / 6600 面 | - |
| `evaluate_surface()` 球面 | ~50ms | 20×20 网格 | - |
| `evaluate_surface()` 车身 | ~80ms | 20×20 网格 | - |
| `optimize_surface()` 球面 80 步 | 1.28s | - | 保持 D |
| `optimize_surface()` 车身 80 步 | 4.79s | - | G2 改善 -119 |
| `optimize_surface()` 平面+噪声 120 步 | 3.00s | - | 优化效果最显著 |
| `make_storyboard()` | <50ms | 7 镜 | 模板生成 |
| `render_storyboard()` md | <10ms | 1968 字符 | - |
| `render_storyboard()` html | <30ms | 9471 字符 | - |
| `test_all.py` 全套 | 9.49s | 5 步 | ✅ |

**优化策略**：
- 同 params 缓存 GLB（hash 命中省 200ms）
- AI 优化必须异步（5s+ 必阻塞）
- 评估结果用 Redis 缓存（key=points_hash）
- 静态资源走 CDN（Nginx，M4）

---

## 9. 安全设计

| 维度 | 措施 |
|------|------|
| **API 鉴权** | JWT Token (M3 引入，M1-M2 先开放) |
| **参数越界** | Pydantic + CarParams.validate() 双重校验 |
| **文件上传** | 限制类型（仅 .glb/.stl/.obj）+ 大小（<50MB） |
| **CORS** | 限定 origin（生产环境） |
| **限流** | slowapi（IP 维度 100 req/min） |
| **SQL 注入** | SQLAlchemy ORM（无裸 SQL） |
| **XSS** | Vue 3 自动转义 + CSP 头 |
| **路径遍历** | 文件名 hash 化，不接受用户路径 |

---

## 10. 部署架构

### 10.1 开发环境（M1）

```
主机
  ├─ algorithm_model/        # 算法层（直接 import）
  ├─ backend/                # uvicorn main:app --reload --port 8000
  ├─ frontend/               # npm run dev (port 5173)
  └─ SQLite                  # 本地文件
```

### 10.2 生产环境（M4）

```
                    ┌──────────┐
                    │   CDN    │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  Nginx   │  :443 (HTTPS)
                    │  反向代理 │
                    └────┬─────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │Frontend │     │Backend  │     │Backend  │
   │ (静态)  │     │  #1     │     │  #2     │
   └─────────┘     └────┬────┘     └────┬────┘
                        │                │
                        └────────┬───────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
               ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
               │Postgres│  │ Redis  │  │ Celery │
               │        │  │        │  │ Workers│
               └────────┘  └────────┘  └────────┘
```

**docker-compose.yml**（M4）：
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
  celery-worker:
    build: ./backend
    command: celery -A tasks.celery_app worker -l info
  postgres:
    image: postgres:15
    volumes: ["pgdata:/var/lib/postgresql/data"]
  redis:
    image: redis:7
  nginx:
    image: nginx
    ports: ["443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]
```

---

## 11. 迭代路线（4 个里程碑）

### M1: MVP —— 后端 + CLI（1 周）
**目标**：FastAPI 后端能跑，CLI 可用，浏览器能看 OpenAPI 文档
- [ ] FastAPI 项目骨架（backend/main.py + config + deps）
- [ ] 5 大 API 路由（car/quality/optimize/storyboard/export）
- [ ] 静态资源服务（GLB 导出 + 访问）
- [ ] CORS 配置（开发环境放开）
- [ ] 简单测试页（OpenAPI docs）
- [ ] 后端单元测试（pytest）
- ✅ **验收**：浏览器访问 `/docs` 能调通所有 API，能下载 GLB

### M2: 数据库 + 异步任务（1 周）
**目标**：方案能保存，优化能异步
- [ ] SQLAlchemy + Alembic 初始化
- [ ] Project 模型 + CRUD API
- [ ] Celery + Redis 接入
- [ ] 优化任务改异步（task_id + 轮询）
- [ ] 数据迁移脚本
- [ ] 集成测试
- ✅ **验收**：保存方案 → 异步优化 → 完成后查询结果

### M3: 前端 + WebSocket（2 周）
**目标**：完整 Web 端工作流
- [ ] Vue 3 + Vite 项目骨架
- [ ] 5 大页面（Designer / Quality / Optimize / Storyboard / Projects）
- [ ] Three.js 3D 预览组件
- [ ] ECharts 评估报告组件
- [ ] WebSocket 实时优化进度
- [ ] 22 维参数编辑器（滑块 + 数字输入）
- [ ] 方案库管理（列表 + 详情 + 编辑）
- ✅ **验收**：完整流程跑通（参数→预览→评估→优化→脚本→保存）

### M4: 部署 + 监控（1 周）
**目标**：可上生产
- [ ] Dockerfile + docker-compose.yml
- [ ] Nginx 配置（HTTPS + 反代）
- [ ] Loguru 日志结构化
- [ ] Prometheus 指标（API QPS / 任务耗时）
- [ ] Grafana 面板（M4 延后到 M5）
- [ ] CI/CD（GitHub Actions）
- [ ] 用户手册 + 部署文档
- ✅ **验收**：`docker-compose up` 一键起服，浏览器访问 HTTPS 域名

---

## 12. 与现有产物映射

| 现有产物 | 在新架构中的位置 | 备注 |
|---------|----------------|------|
| `algorithm_model/api.py` | L4 算法层 | **不动**，作为后端服务依赖 |
| `algorithm_model/main.py` | CLI 入口 | 保留，运维/调试用 |
| `algorithm_model/test_all.py` | 测试基线 | **不动**，每次发布前跑 |
| `core/full_body.py` | 历史归档 | 可删除，算法模型已包含 |
| `app.py` (Streamlit) | **删除** | 已被算法模型 + FastAPI 替代 |
| `generate_screenshots.py` | scripts/ | 保留作为静态图生成 |
| `start.bat` / `start.sh` | scripts/ | 重写为 FastAPI 启动 |
| `outputs/*.png` | outputs/snapshots/ | 迁移到新位置 |
| `docs/PRODUCT_SPEC.md` | docs/ | **不动** |
| `docs/算法模型交付总结.md` | docs/ | **不动** |
| `docs/视频脚本展示功能整合总结.md` | docs/ | **不动** |

---

## 13. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| AI 优化耗时不确定 | 异步任务超时 | Celery 软超时 60s + 硬超时 120s，前端可取消 |
| 复杂参数导致 GLB 过大 | 加载慢 | 简化策略（LOD）+ 压缩（draco）|
| Three.js 学习曲线 | 前端延期 | M3 单独排期 + 用现成示例 |
| SQLite 并发写入 | 方案丢失 | M2 升级 PostgreSQL |
| Celery 部署复杂 | M2 延期 | M1 先用 FastAPI BackgroundTasks 同步版 |
| 三方库升级破坏 API | 重构 | requirements 锁版本 + 测试覆盖 |

---

## 14. 总结

**核心思路**：
1. **算法先行** ✅（已交付，5/5 自检，9.49s）
2. **后端承上启下**（M1-M2）：把算法包成 RESTful + WebSocket
3. **前端发力**（M3）：把后端装进 Three.js + Vue 3
4. **工程化收尾**（M4）：Docker + Nginx + 监控

**关键决策**：
- **算法模型与 Web 完全解耦**：算法可独立 CLI 跑、可独立测试、可被其他项目直接 `pip install`
- **后端只做编排，不重写算法**：服务层是薄壳，调 `algorithm_model.api` 即可
- **异步优先**：所有 > 1s 的操作（AI 优化 / 视频生成）默认异步 + 任务队列
- **数据结构稳定**：5 大 API 数据类签名冻结，前端按字段渲染

**预期产出**（4 周）：
- 完整 Web 平台（参数编辑 → 3D 预览 → 质量评估 → AI 优化 → 视频脚本 → 方案管理）
- 一键 Docker 启动
- OpenAPI 自动文档
- 主对话演示流程跑通

---

**主人，要我接着推 M1（FastAPI 后端骨架）吗？还是先把这套架构过一遍，有要改的地方？**
