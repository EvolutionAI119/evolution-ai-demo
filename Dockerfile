# ============================================
# EVOLUTION AI - 汽车A级曲面参数化设计平台
# 多阶段构建：编译 Cython + 运行服务
# ============================================

# --- 构建阶段：编译 Cython 扩展 ---
FROM python:3.13-slim AS builder

WORKDIR /build

# 编译工具 + 国内镜像加速
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 Docker 缓存层）+ 国内 pip 镜像
COPY requirements.txt backend/requirements.txt algorithm_model/requirements.txt ./
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    -r requirements.txt \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    -r backend/requirements.txt \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    -r algorithm_model/requirements.txt \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
    cython

# 拷贝源码
COPY . .

# 编译 Cython
RUN python setup_nurbs.py build_ext --inplace && \
    echo "✅ Cython 编译完成" && \
    find algorithm_model -name "*.so" -exec ls -lh {} \;

# --- 运行阶段 ---
FROM python:3.13-slim

LABEL maintainer="quantum-swordsman <evolution-ai@embodied.systems>"
LABEL description="EVOLUTION AI - 参数化+AI驱动的汽车造型开发平台"

WORKDIR /app

# 运行时依赖（不需要 gcc）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段拷贝已编译的 Python 包
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 拷贝项目文件
COPY --from=builder /build /app

# 创建数据目录（Volume 挂载点）
RUN mkdir -p /app/data/outputs /app/data/db /app/logs

# Volume：持久化数据，容器重建不丢失
VOLUME ["/app/data", "/app/logs"]

# 环境变量
ENV EVOLUTION_ENV=production \
    EVOLUTION_DEBUG=false \
    EVOLUTION_CORS_ORIGINS='["http://localhost:3000","http://localhost:5173","http://localhost:8501","http://127.0.0.1:3000","http://127.0.0.1:5173","http://127.0.0.1:8501"]' \
    PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 入口
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
