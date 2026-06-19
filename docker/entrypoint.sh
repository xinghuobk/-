#!/usr/bin/env bash
# ============================================================
# ParaJudge v0.3 · Docker 实验入口脚本
# ============================================================
# 模式：
#   --mode=full         一键跑完：download → llm → ablation → statistics
#   --mode=download     仅下载数据集
#   --mode=test-unit    仅跑单元测试
#   --mode=llm          仅跑 LLM 端到端（24 题）
#   --mode=ablation     仅跑消融实验
#   --mode=statistics   仅跑统计检验
#   --mode=interactive  交互模式（进入 bash）
#
# 示例：
#   docker compose run --rm parajudge --mode=download
#   docker compose run --rm parajudge --mode=llm
#   docker compose run --rm parajudge --mode=full
# ============================================================

set -euo pipefail

MODE="${MODE:-interactive}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
MODEL="${MODEL:-qwen2.5:7b}"
QUESTIONS="${QUESTIONS:-24}"
LOG_DIR="/workspace/reports/docker"

mkdir -p "$LOG_DIR"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG_DIR/run.log"
}

log_error() {
    echo "[ERROR] $*" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >> "$LOG_DIR/run.log"
}

# ── 健康检查：等待 Ollama 就绪 ───────────────────────────
wait_for_ollama() {
    log "等待 Ollama 服务就绪..."
    local retries=30
    for i in $(seq 1 $retries); do
        if curl -sf "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
            log "✅ Ollama 已就绪（第 ${i} 次尝试）"
            # 验证模型是否存在
            if curl -sf "${OLLAMA_URL}/api/tags" | grep -q "\"name\":\"${MODEL}\""; then
                log "✅ 模型 ${MODEL} 已就绪"
            else
                log_error "模型 ${MODEL} 未找到，开始下载..."
                ollama pull "${MODEL}" 2>&1 | tee -a "$LOG_DIR/ollama_pull.log"
            fi
            return 0
        fi
        log "Ollama 未就绪（${i}/${retries}），等待 5s..."
        sleep 5
    done
    log_error "Ollama 启动超时"
    return 1
}

# ── 步骤 0：环境检查 ─────────────────────────────────────
step_env() {
    log "═══ Step 0: 环境检查 ═══"
    cd /workspace
    python scripts/env_check.py --json | tee "$LOG_DIR/env_check.json"
    log "环境检查完成"
}

# ── 步骤 1：单元测试 ─────────────────────────────────────
step_test_unit() {
    log "═══ Step 1: 单元测试 ═══"
    cd /workspace
    for f in src/innovation_v2/t*.py; do
        log "  → 测试 $f"
        python "$f" 2>&1 | tee -a "$LOG_DIR/unit_tests.log" || {
            log_error "单元测试失败: $f"
            return 1
        }
    done
    log "✅ 单元测试全部通过"
}

# ── 步骤 2：下载数据集 ──────────────────────────────────
step_download() {
    log "═══ Step 2: 下载数据集 ═══"
    cd /workspace
    python scripts/download_real_datasets.py 2>&1 | tee -a "$LOG_DIR/download.log"
    local failed=$(grep -c '"status": "FAILED"' "$LOG_DIR/download.log" 2>/dev/null || echo 0)
    if [ "$failed" -gt 0 ]; then
        log_error "$failed 个数据集下载失败（不影响其他实验）"
    else
        log "✅ 全部数据集下载成功"
    fi
}

# ── 步骤 3：真实 LLM 端到端 ─────────────────────────────
step_llm() {
    log "═══ Step 3: 真实 LLM 端到端 ═══"
    wait_for_ollama || {
        log_error "Ollama 不可用，跳过 LLM 实验（使用 --provider mock 可强制 mock 模式）"
        return 0
    }
    cd /workspace
    python scripts/run_real_llm_e2e.py \
        --provider ollama \
        --model "${MODEL}" \
        --questions "${QUESTIONS}" \
        --rounds 2 \
        2>&1 | tee -a "$LOG_DIR/llm_e2e.log"
    log "✅ LLM 端到端完成"
}

# ── 步骤 4：消融实验 ────────────────────────────────────
step_ablation() {
    log "═══ Step 4: 消融实验 ═══"
    wait_for_ollama || {
        log_error "Ollama 不可用，跳过消融实验"
        return 0
    }
    cd /workspace
    python scripts/run_real_ablation.py \
        --provider ollama \
        --model "${MODEL}" \
        --questions "${QUESTIONS}" \
        2>&1 | tee -a "$LOG_DIR/ablation.log"
    log "✅ 消融实验完成"
}

# ── 步骤 5：统计检验 ────────────────────────────────────
step_statistics() {
    log "═══ Step 5: 统计检验 ═══"
    cd /workspace
    local llm_files=$(ls experiments/v0.3_real_external/llm_e2e_*.jsonl 2>/dev/null | tr '\n' ' ')
    local abl_file=$(ls experiments/v0.3_real_external/ablation_*.jsonl 2>/dev/null | head -1)
    if [ -z "$llm_files" ]; then
        log_error "没有 LLM 端到端 JSONL，跳过统计"
        return 1
    fi
    python scripts/run_real_statistics.py \
        --llm $llm_files \
        --ablation "${abl_file:-}" \
        2>&1 | tee -a "$LOG_DIR/statistics.log"
    log "✅ 统计检验完成"
}

# ── 汇总报告 ───────────────────────────────────────────
step_report() {
    log "═══ 汇总报告 ═══"
    cd /workspace
    # 读取统计报告
    if [ -f experiments/v0.3_real_external/statistics_report.md ]; then
        cp experiments/v0.3_real_external/statistics_report.md "$LOG_DIR/statistics_report.md"
        log "报告已复制到 $LOG_DIR/"
    fi
    # 统计实验结果
    log "实验结果统计："
    log "  LLM 端到端 JSONL: $(ls experiments/v0.3_real_external/llm_e2e_*.jsonl 2>/dev/null | wc -l) 个"
    log "  消融 JSONL: $(ls experiments/v0.3_real_external/ablation_*.jsonl 2>/dev/null | wc -l) 个"
    log "  统计数据: $(ls experiments/v0.3_real_external/*.json 2>/dev/null | wc -l) 个"
    log "  日志: $LOG_DIR/"
    log "══════════════════════════════════════════════"
    log "  ParaJudge v0.3 Docker 实验完成！"
    log "  完整报告：$LOG_DIR/"
    log "══════════════════════════════════════════════"
}

# ── 主流程 ─────────────────────────────────────────────
main() {
    log "ParaJudge v0.3 Docker 实验启动"
    log "模式: ${MODE}"
    log "OLLAMA: ${OLLAMA_URL}"
    log "MODEL: ${MODEL}"
    log "QUESTIONS: ${QUESTIONS}"

    case "${MODE}" in
        full)
            log "═══ 完整流程：download → test → llm → ablation → statistics ═══"
            step_env
            step_test_unit
            step_download
            step_llm
            step_ablation
            step_statistics
            step_report
            ;;
        download)
            step_download
            ;;
        test-unit)
            step_test_unit
            ;;
        llm)
            step_llm
            ;;
        ablation)
            step_ablation
            ;;
        statistics)
            step_statistics
            ;;
        env-check)
            step_env
            ;;
        report)
            step_report
            ;;
        interactive|bash|"")
            log "进入交互模式（exit 退出）"
            exec bash
            ;;
        *)
            log_error "未知模式: ${MODE}"
            echo "用法: --mode=full|download|test-unit|llm|ablation|statistics|interactive"
            exit 1
            ;;
    esac
}

main
