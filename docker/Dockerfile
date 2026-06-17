# ============================================================
# ParaJudge v0.3 · 实验容器镜像
# ============================================================
# 用途：跑所有真实实验（数据下载 / LLM 端到端 / 消融 / 统计）
# 构建：docker build -t parajudge:v0.3 -f docker/Dockerfile .
# 运行：docker compose up parajudge（或 docker run）
# ============================================================

FROM python:3.11-slim

LABEL maintainer="parajudge"
LABEL description="ParaJudge v0.3 Experiment Container"
LABEL version="0.3"

# ── 系统依赖 ────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    wget \
    gnupg \
    ca-certificates \
    unzip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Ollama 客户端（ollama CLI，用于 pull 模型）───────────────
RUN curl -fsSL https://ollama.ai/install.sh | sh

# ── 工作目录 ────────────────────────────────────────────────
WORKDIR /workspace

# ── Python 依赖 ─────────────────────────────────────────────
# 先复制 requirements 再 pip install，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── ParaJudge 源码 ─────────────────────────────────────────
COPY . /workspace/

# ── 环境变量 ────────────────────────────────────────────────
# Ollama 服务地址（由 docker-compose 提供）
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV OLLAMA_HOST=0.0.0.0
ENV PYTHONPATH=/workspace

# ── 数据目录（持久化卷）────────────────────────────────────
VOLUME ["/workspace/data", "/workspace/experiments", "/workspace/reports"]

# ── 健康检查 ────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags > /dev/null 2>&1 || exit 1

# ── 默认命令（可在 docker-compose.yml / docker run 覆盖）───
ENTRYPOINT ["/workspace/docker/entrypoint.sh"]
CMD ["--mode=interactive"]
