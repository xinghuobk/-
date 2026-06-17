# =============================================================
# ParaJudge v0.3 · Makefile
# 两条路线：
#   本机路线（无 Docker）→ make install / make run-llm ...
#   Docker 路线（推荐）  → make docker-build / make docker-up ...
# =============================================================

.PHONY: help
help:
	@echo "ParaJudge v0.3 Makefile"
	@echo ""
	@echo "【本机路线（不需要 Docker）】"
	@echo "  make install         安装依赖（pip）"
	@echo "  make env-check       环境检查"
	@echo "  make test-unit       跑 4 个真理论的单元测试"
	@echo "  make download-data   下载 10 个真实数据集"
	@echo "  make run-llm        跑真实 LLM 端到端（默认 Ollama qwen2.5:7b）"
	@echo "  make run-ablation    跑 6 组消融"
	@echo "  make run-statistics  跑统计检验"
	@echo "  make run-all        一键跑完（download→test→llm→ablation→statistics）"
	@echo ""
	@echo "【Docker 路线（推荐，一键搞定）】"
	@echo "  make docker-build        构建 ParaJudge + Ollama 镜像"
	@echo "  make docker-pull-model   预拉取模型（可选，构建时已内嵌）"
	@echo "  make docker-up          启动 Ollama + ParaJudge（后台）"
	@echo "  make docker-interactive 进入容器交互"
	@echo "  make docker-test        仅跑单元测试"
	@echo "  make docker-full        一键跑完整实验（download→test→llm→ablation→statistics）"
	@echo "  make docker-down         停止并清理容器"
	@echo ""
	@echo "  make docker-llm QUESTIONS=5   仅跑 5 题 LLM 端到端"
	@echo "  make docker-ablation MODEL=deepseek-r1:7b  换模型跑消融"
	@echo ""
	@echo "示例："
	@echo "  # 本机"
	@echo "  make install && make run-all"
	@echo ""
	@echo "  # Docker"
	@echo "  make docker-build && make docker-full"

# =============================================================
# 本机路线（不需要 Docker）
# =============================================================

env-check:
	@echo "🔍 Step 1: 环境检查"
	python scripts/env_check.py

install:
	@echo "📦 安装依赖"
	pip install -r requirements.txt
	@if [ ! -f requirements.txt ]; then \
		echo "生成 requirements.txt..."; \
		pip freeze > requirements.txt; \
	fi

download-data:
	@echo "⬇️  Step 2: 下载 10 个真实数据集"
	python scripts/download_real_datasets.py

test-unit:
	@echo "🧪 跑 4 个真理论单元测试"
	@for f in src/innovation_v2/t*.py; do \
		echo "  → $$f"; \
		PYTHONPATH=. python $$f || exit 1; \
	done

run-llm:
	@echo "🤖 Step 3: 真实 LLM 端到端"
	@PROVIDER=$${PROVIDER:-ollama}; \
	MODEL=$${MODEL:-qwen2.5:7b}; \
	QUESTIONS=$${QUESTIONS:-24}; \
	python scripts/run_real_llm_e2e.py --provider $$PROVIDER --model $$MODEL --questions $$QUESTIONS

run-ablation:
	@echo "🔬 Step 4: 6 组消融"
	@PROVIDER=$${PROVIDER:-ollama}; \
	MODEL=$${MODEL:-qwen2.5:7b}; \
	QUESTIONS=$${QUESTIONS:-24}; \
	python scripts/run_real_ablation.py --provider $$PROVIDER --model $$MODEL --questions $$QUESTIONS

run-statistics:
	@echo "📊 Step 5: 11 个实验的统计检验"
	@LLM_FILES=$$(ls experiments/v0.3_real_external/llm_e2e_*.jsonl 2>/dev/null); \
	ABL_FILE=$$(ls experiments/v0.3_real_external/ablation_*.jsonl 2>/dev/null | head -1); \
	echo "  LLM files: $$LLM_FILES"; \
	echo "  Ablation file: $$ABL_FILE"; \
	if [ -z "$$LLM_FILES" ]; then \
		echo "❌ 没有 LLM 端到端 JSONL，请先 make run-llm"; \
		exit 1; \
	fi; \
	python scripts/run_real_statistics.py --llm $$LLM_FILES --ablation $$ABL_FILE

run-all: download-data test-unit run-llm run-ablation run-statistics report
	@echo ""
	@echo "✅ 全部完成。报告：experiments/v0.3_real_external/"

report:
	@echo "📝 汇总报告"
	@echo "  沙箱内: docs/ParaJudge-v0.2-真实实验报告.md"
	@echo "  沙箱外: experiments/v0.3_real_external/statistics_report.md"
	@echo "  完整指南: docs/ParaJudge-跳出沙箱工作指南.md"

clean:
	@echo "🧹 清理缓存"
	rm -rf experiments/v0.3_real_external/*.jsonl experiments/v0.3_real_external/*.json experiments/v0.3_real_external/*.md
	rm -rf data/raw/* data/processed/* data/manifest.json
	rm -rf reports/env_check.*
	@echo "✅ 清理完成"

# =============================================================
# Docker 路线（推荐）
# =============================================================

DOCKER_TAG ?= parajudge:v0.3
OLLAMA_TAG ?= parajudge/ollama:v0.3
MODEL ?= qwen2.5:7b
QUESTIONS ?= 24

docker-build-ollama:
	@echo "🔨 构建 Ollama 镜像（含 ${MODEL}）..."
	docker build \
		--build-arg OLLAMA_MODEL=${MODEL} \
		-t ${OLLAMA_TAG} \
		-f docker/Dockerfile.ollama \
		docker/
	@echo "✅ Ollama 镜像构建完成: ${OLLAMA_TAG}"

docker-build:
	@echo "🔨 构建 ParaJudge 实验镜像..."
	docker build \
		-t ${DOCKER_TAG} \
		-f docker/Dockerfile \
		.
	@echo "✅ ParaJudge 镜像构建完成: ${DOCKER_TAG}"

docker-build-all: docker-build-ollama docker-build
	@echo "✅ 全部镜像构建完成"
	@echo "   ParaJudge: ${DOCKER_TAG}"
	@echo "   Ollama:    ${OLLAMA_TAG}"

docker-pull-model:
	@echo "⬇️  预拉取模型 ${MODEL}..."
	docker compose run --rm ollama ollama pull ${MODEL}

docker-up:
	@echo "🚀 启动 Ollama + ParaJudge（后台）..."
	docker compose up -d ollama
	@echo "⏳ 等待 Ollama 健康..."
	@for i in $$(seq 1 30); do \
		if docker compose exec -T ollama curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then \
			echo "✅ Ollama 已就绪"; exit 0; \
		fi; \
		echo "   等待中 ($$i/30)..."; \
		sleep 2; \
	done; \
	echo "⚠️ Ollama 启动超时，但已启动，可继续"

docker-down:
	@echo "🛑 停止容器..."
	docker compose down
	@echo "✅ 已停止"

docker-interactive:
	@echo "🐚 进入容器交互模式..."
	docker compose run --rm --service-ports parajudge bash

docker-test:
	@echo "🧪 Docker 跑单元测试..."
	docker compose run --rm \
		-e MODE=test-unit \
		parajudge

docker-env:
	@echo "🔍 Docker 环境检查..."
	docker compose run --rm \
		-e MODE=env-check \
		parajudge

docker-download:
	@echo "⬇️  Docker 下载数据集..."
	docker compose run --rm \
		-e MODE=download \
		parajudge

docker-llm:
	@echo "🤖 Docker LLM 端到端..."
	docker compose run --rm \
		-e MODE=llm \
		-e MODEL=${MODEL} \
		-e QUESTIONS=${QUESTIONS} \
		parajudge

docker-ablation:
	@echo "🔬 Docker 消融实验..."
	docker compose run --rm \
		-e MODE=ablation \
		-e MODEL=${MODEL} \
		-e QUESTIONS=${QUESTIONS} \
		parajudge

docker-statistics:
	@echo "📊 Docker 统计检验..."
	docker compose run --rm \
		-e MODE=statistics \
		parajudge

docker-full:
	@echo "🚀 Docker 一键完整流程：download → test → llm → ablation → statistics"
	docker compose run --rm \
		-e MODE=full \
		-e MODEL=${MODEL} \
		-e QUESTIONS=${QUESTIONS} \
		parajudge

docker-report:
	@echo "📝 Docker 汇总报告..."
	docker compose run --rm \
		-e MODE=report \
		parajudge
