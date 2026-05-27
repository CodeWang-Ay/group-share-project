# =============================================================================
# 研究生组会管理系统 - Dockerfile
# =============================================================================
# 多阶段构建，优化镜像大小

# -----------------------------------------------------------------------------
# 第一阶段：构建依赖
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到临时目录
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------------------------------------
# 第二阶段：运行镜像
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY uploads/ ./uploads/
COPY requirements.txt .

# 创建必要的目录
RUN mkdir -p /app/uploads/avatars \
             /app/uploads/materials \
             /app/uploads/papers \
             /app/uploads/personal_papers \
             /app/uploads/share_files \
             /app/logs

# 初始化数据库
RUN python backend/database/connection.py

# 暴露端口
EXPOSE 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8081"]