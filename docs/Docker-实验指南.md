# ParaJudge · Docker 实验指南

> 一行命令跑完所有实验（数据下载 → LLM 端到端 → 消融 → 统计）

---

## 零、前置要求

| 要求 | 最低配置 | 推荐配置 |
|---|---|---|
| Docker | ≥ 20.10 | ≥ 24.0 |
| Docker Compose | ≥ 2.0 | ≥ 2.20 |
| 磁盘空间 | 15GB | 30GB |
| 内存 | 8GB | 16GB |
| 网络 | 外网可达 | 稳定 10Mbps+ |
| GPU（可选）| — | NVIDIA GPU + nvidia-container-toolkit |

**GPU 支持**：取消 `docker-compose.yml` 中的 `deploy.resources` 注释即可。

---

## 一、3 步开始实验

### Step 1：克隆项目
```bash
git clone <your-repo-url> parajudge
cd parajudge
```

### Step 2：构建镜像（一键，约 10 分钟）
```bash
make docker-build-all
```
> 如果只想构建 ParaJudge（用已下载的 Ollama）：
> ```bash
> make docker-build  # 仅 ParaJudge 实验容器
> ```

### Step 3：跑实验
```bash
# 推荐顺序（5 步，约 1-4 小时）
make docker-up           # 启动 Ollama（后台）
make docker-test         # 单元测试（5 分钟）
make docker-download     # 下载数据集（约 10-30 分钟，取决于网络）
make docker-llm          # LLM 端到端（约 1-4 小时，取决于模型和题数）
make docker-ablation     # 消融实验（约 1-4 小时）
make docker-statistics   # 统计检验（约 5 分钟）
```

**或者一键跑完所有**：
```bash
make docker-full
```

---

## 二、所有 Docker 命令

| 命令 | 作用 |
|---|---|
| `make docker-build-all` | 构建 ParaJudge + Ollama 两个镜像 |
| `make docker-build` | 仅构建 ParaJudge 实验容器 |
| `make docker-up` | 启动 Ollama 服务（后台） |
| `make docker-down` | 停止所有容器 |
| `make docker-interactive` | 进入容器交互模式（bash） |
| `make docker-test` | 跑单元测试 |
| `make docker-download` | 下载 10 个数据集 |
| `make docker-llm` | LLM 端到端 |
| `make docker-ablation` | 消融实验 |
| `make docker-statistics` | 统计检验 |
| `make docker-full` | 一键完整流程 |
| `make docker-report` | 汇总报告 |

---

## 三、常用参数

```bash
# 换模型（默认 qwen2.5:7b）
make docker-llm MODEL=deepseek-r1:7b

# 减少题数（默认 24 题）
make docker-llm MODEL=qwen2.5:7b QUESTIONS=5

# 仅跑 5 题消融
make docker-ablation MODEL=qwen2.5:7b QUESTIONS=5
```

---

## 四、预期时间与资源

| 实验 | 默认配置 | 快速验证（5 题）|
|---|---|---|
| Ollama 启动 + 模型加载 | ~2 分钟 | — |
| 单元测试（4 个真理论）| ~5 分钟 | — |
| 数据下载（10 个数据集）| 10-60 分钟 | — |
| LLM 端到端（24 题）| 1-4 小时 | 10-30 分钟 |
| 消融（6 组 × 24 题）| 6-24 小时 | 1-2 小时 |
| 统计检验 | 5 分钟 | 2 分钟 |
| **总计** | **8-28 小时** | **1-3 小时** |

---

## 五、GPU 支持（可选）

如果你的机器有 NVIDIA GPU，启用 GPU 加速 sentence-transformers：

```bash
# 1. 安装 nvidia-container-toolkit
# Ubuntu:
sudo apt-get install nvidia-container-toolkit
sudo systemctl restart docker

# 2. 编辑 docker-compose.yml，取消 GPU 注释：
#   # deploy:
#   #   resources:
#   #     reservations:
#   #       devices:
#   #         - driver: nvidia
#   #           count: all
#   #           capabilities: [gpu]

# 3. 重新启动
make docker-down && make docker-up
```

---

## 六、数据持久化

所有实验数据存在宿主机，不随容器删除：

```
./data/raw/              ← 原始数据集（~1GB）
./data/processed/        ← 清洗后数据
./experiments/           ← 所有 JSONL 实验结果
./reports/              ← 报告 + 日志
```

---

## 七、日志查看

```bash
# 实时查看容器日志
docker compose logs -f parajudge
docker compose logs -f ollama

# 查看实验日志
cat reports/docker/run.log

# 查看统计报告
cat experiments/v0.3_real_external/statistics_report.md
```

---

## 八、常见问题

### Q1：构建 Ollama 镜像太慢
**A**：qwen2.5:7b ~6GB，GitHub 在国内慢。解决方案：
```bash
# 方法 1：换模型（小一点）
make docker-build-ollama MODEL=llama3.2:3b   # ~2GB

# 方法 2：先用本机 Ollama 拉模型，再构建镜像
ollama pull qwen2.5:7b
make docker-build-ollama   # 构建时跳过下载

# 方法 3：不构建 Ollama 镜像，直接用 docker compose 内置
# （会自动下载，但每次启动都下载）
docker compose up -d ollama
```

### Q2：内存不够（OOM）
**A**：减小题数和轮数：
```bash
make docker-llm QUESTIONS=10 MODEL=qwen2.5:3b
```

### Q3：外网下载失败
**A**：使用代理：
```bash
export HTTP_PROXY=http://your-proxy:8080
export HTTPS_PROXY=http://your-proxy:8080
make docker-download
```

### Q4：容器里看不到实验结果
**A**：结果在宿主机 `./experiments/` 目录，不在容器内。

### Q5：中断后如何恢复
**A**：所有脚本边跑边写 JSONL，中断后重跑会自动跳过已完成的部分：
```bash
make docker-llm   # 重跑，会自动跳过已有结果
```

---

## 九、Dockerfile 体积优化（可选）

当前镜像约 2-4GB（Python + 依赖），如果需要更小的镜像：

```dockerfile
# 使用 alpine 变体
FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
# 删除构建缓存
RUN rm -rf /root/.cache/pip
```

---

## 十、一句话总结

```bash
# 最快方式（需要 GPU + 代理）
make docker-build-all && make docker-full

# 最简单方式（默认配置，qwen2.5:7b）
make docker-build-all && make docker-up && make docker-llm
```
