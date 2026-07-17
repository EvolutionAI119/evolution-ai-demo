# EVOLUTION AI - Docker 部署指南

## 解决的问题

| 问题 | Docker 方案 |
|------|------------|
| 沙箱 FUSE 0-byte bug | 数据存入 Docker Volume，不依赖沙箱文件系统 |
| 沙箱 4h 回收 | Docker 容器在本地运行，无回收机制 |
| 主人电脑无 Python | 全部打包进镜像，只需 Docker Desktop |
| Cython 跨平台编译 | 多阶段构建，在 Linux 容器内编译 .so |

## 前置要求

- **Docker Desktop**（Windows/Mac）：https://www.docker.com/products/docker-desktop/
- 磁盘空间：~2GB（镜像 + 数据）

## 一键启动

### Windows
```
双击 start-docker.bat
```

### Mac/Linux
```bash
chmod +x start-docker.sh && ./start-docker.sh
```

### 手动启动
```bash
# 构建镜像（首次 3-5 分钟）
docker compose build

# 启动
docker compose up -d

# 查看日志
docker compose logs -f
```

## 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | 备用文档 |
| 前端 DEMO | http://localhost:8501 | Streamlit |
| 健康检查 | http://localhost:8000/health | `{"status":"ok"}` |

## 数据持久化

```
Docker Volume: evolution-data  → /app/data/outputs (生成文件)
                                 /app/data/db      (数据库)
Docker Volume: evolution-logs  → /app/logs         (运行日志)
```

容器重建不丢数据。如需备份：
```bash
docker run --rm -v evolution-ai_evolution-data:/data -v $(pwd):/backup \
    alpine tar czf /backup/evolution-data-backup.tar.gz /data
```

## 常用命令

```bash
# 停止服务
docker compose down

# 重启
docker compose restart

# 重新构建（代码更新后）
docker compose build --no-cache && docker compose up -d

# 进入容器调试
docker compose exec evolution-ai bash

# 查看资源占用
docker stats evolution-ai
```

## 架构

```
┌─────────────────────────────────────────┐
│           Docker Container              │
│                                         │
│  ┌──────────────┐  ┌────────────────┐  │
│  │  FastAPI      │  │  Streamlit     │  │
│  │  :8000        │  │  :8501         │  │
│  │              │  │                │  │
│  │  8 个 API    │  │  交互式 DEMO   │  │
│  │  模块        │  │  参数调节      │  │
│  └──────┬───────┘  └───────┬────────┘  │
│         │                  │            │
│  ┌──────┴──────────────────┴────────┐  │
│  │     algorithm_model              │  │
│  │     (Cython 加速 .so)            │  │
│  │     136 个算法 + 19 后端测试      │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     SQLite (evolution_ai.db)     │  │
│  │     → Volume 持久化              │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 可选：启用 Redis（Celery 异步任务）

编辑 `docker-compose.yml`，取消 redis 相关行的注释，然后：
```bash
docker compose up -d
```

## 故障排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 构建失败 "gcc not found" | builder 阶段 apt 问题 | `docker compose build --no-cache` |
| 端口被占用 | 其他程序用了 8000/8501 | 改 docker-compose.yml 的 ports 映射 |
| Cython 警告 | .so 编译异常 | 功能不受影响，降级为 Python 模式 |
| 502/连接拒绝 | 服务未就绪 | 等 10 秒后重试 |

---

**EVOLUTION AI** · embodied.systems
