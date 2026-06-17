# ParaJudge · Makefile
# 跳出沙箱后 5 步流程的一键命令

.PHONY: help env-check install download-data test-unit run-llm run-ablation run-statistics run-all report clean

help:
	@echo "ParaJudge v0.3 Makefile"
	@echo ""
	@echo "  make env-check       环境检查（必跑第一件事）"
	@echo "  make install         安装依赖（pip）"
	@echo "  make download-data   下载 10 个真实数据集"
	@echo "  make test-unit       跑 4 个真理论的单元测试"
	@echo "  make run-llm         跑真实 LLM 端到端（默认 Ollama qwen2.5:7b）"
	@echo "  make run-ablation    跑 6 组消融（默认 Ollama qwen2.5:7b）"
	@echo "  make run-statistics  跑统计检验"
	@echo "  make run-all         一键跑完 download → llm → ablation → statistics"
	@echo "  make report          汇总生成报告"
	@echo "  make clean           清理 experiments/ 和 data/ 缓存"
	@echo ""
	@echo "  示例："
	@echo "    make run-llm PROVIDER=openai MODEL=gpt-4o-mini"
	@echo "    make run-ablation PROVIDER=ollama QUESTIONS=10"

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
