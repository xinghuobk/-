#!/usr/bin/env bash
# ============================================================
# ParaJudge - Ollama 本地 LLM 一键安装与启动脚本
# ============================================================
# 适用：Windows (Git Bash / WSL) / macOS / Linux
# 作用：自动安装 Ollama + 拉取 ParaJudge 推荐模型
# ============================================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 推荐模型清单（ParaJudge 中文辩论场景优化）
RECOMMENDED_MODELS=(
    "qwen2.5:7b"          # 中文主力（推荐）
    "qwen2.5:14b"         # 高质量
    "llama3.1:8b"         # 英文
    "deepseek-r1:7b"      # 推理增强
    "qwen2.5:3b"          # 低显存
)

# 显存推荐配置
declare -A VRAM_REQUIREMENTS=(
    ["qwen2.5:3b"]="4GB"
    ["qwen2.5:7b"]="8GB"
    ["qwen2.5:14b"]="16GB"
    ["llama3.1:8b"]="8GB"
    ["deepseek-r1:7b"]="8GB"
)

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  ParaJudge - Ollama 本地 LLM 部署脚本${NC}"
echo -e "${BLUE}============================================================${NC}"
echo

# ---------- 1. 检测操作系统 ----------
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ -n "$WSL_DISTRO_NAME" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
}

# ---------- 2. 安装 Ollama ----------
install_ollama() {
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama 已安装：$(ollama --version)${NC}"
        return 0
    fi

    echo -e "${YELLOW}→ 正在安装 Ollama...${NC}"
    case "$OS" in
        linux)
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install ollama
            else
                echo -e "${RED}请先安装 Homebrew (https://brew.sh) 或手动下载：${NC}"
                echo "https://ollama.com/download/Ollama-darwin.zip"
                exit 1
            fi
            ;;
        windows)
            echo -e "${YELLOW}请从 https://ollama.com/download/OllamaSetup.exe 下载并安装${NC}"
            echo -e "${YELLOW}安装后请重新运行此脚本${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}不支持的操作系统：$OSTYPE${NC}"
            exit 1
            ;;
    esac
}

# ---------- 3. 启动 Ollama 服务 ----------
start_service() {
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama 服务已在运行 (http://localhost:11434)${NC}"
        return 0
    fi

    echo -e "${YELLOW}→ 启动 Ollama 服务...${NC}"
    case "$OS" in
        windows)
            # Windows 下用 ollama app 自带服务
            ollama serve &
            ;;
        *)
            nohup ollama serve > /tmp/ollama.log 2>&1 &
            ;;
    esac
    sleep 3

    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama 服务启动成功${NC}"
    else
        echo -e "${RED}✗ Ollama 服务启动失败，请检查日志：/tmp/ollama.log${NC}"
        exit 1
    fi
}

# ---------- 4. 拉取模型 ----------
pull_model() {
    local model=$1
    echo -e "${YELLOW}→ 拉取模型 $model (需要 ${VRAM_REQUIREMENTS[$model]:-?} 显存)...${NC}"
    if ollama pull "$model"; then
        echo -e "${GREEN}✓ $model 拉取成功${NC}"
    else
        echo -e "${RED}✗ $model 拉取失败${NC}"
        return 1
    fi
}

# ---------- 5. 测试连通性 ----------
test_model() {
    local model=$1
    echo -e "${YELLOW}→ 测试模型 $model...${NC}"
    local response=$(curl -s http://localhost:11434/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"回复 OK\"}],\"max_tokens\":20}" \
        | grep -o '"content":"[^"]*"' | head -1)

    if [[ -n "$response" ]]; then
        echo -e "${GREEN}✓ $model 测试通过：$response${NC}"
    else
        echo -e "${RED}✗ $model 测试失败${NC}"
    fi
}

# ---------- 6. 写入 ParaJudge 配置 ----------
write_config() {
    local config_file="frontend/js/llm-defaults.js"
    cat > "$config_file" <<EOF
/**
 * ParaJudge LLM 默认配置（自动生成，请勿手动修改）
 * 生成时间：$(date -Iseconds 2>/dev/null || date)
 */
window.PARAJUDGE_LLM_DEFAULTS = {
    providers: [
        { code: 'ollama', name: 'Ollama (本地)', default_model: 'qwen2.5:7b', base_url: 'http://localhost:11434/v1' },
        { code: 'openai', name: 'OpenAI / 兼容', default_model: 'gpt-3.5-turbo' },
        { code: 'dashscope', name: '通义千问', default_model: 'qwen-max' },
        { code: 'mock', name: 'Mock (离线)', default_model: 'mock-model' }
    ],
    available_models: $(ollama list 2>/dev/null | tail -n +2 | awk '{print "\""$1"\""}' | tr '\n' ',' | sed 's/,$//' | tr -d '\n' | xargs -I {} echo "[{}]")
};
EOF
    echo -e "${GREEN}✓ ParaJudge 配置已生成: $config_file${NC}"
}

# ============================================================
# 主流程
# ============================================================

detect_os
echo -e "检测到操作系统: ${BLUE}$OS${NC}"
echo

install_ollama
echo

start_service
echo

# 询问拉取哪些模型
echo -e "${BLUE}ParaJudge 推荐模型清单：${NC}"
for i in "${!RECOMMENDED_MODELS[@]}"; do
    model="${RECOMMENDED_MODELS[$i]}"
    vram="${VRAM_REQUIREMENTS[$model]:-?}"
    echo "  $((i+1)). $model  (推荐显存: $vram)"
done
echo "  0. 自定义模型名"
echo "  s. 跳过拉取（已拉取过）"
echo

read -p "请选择要拉取的模型（多选用空格分隔，如 '1 2'，或 'qwen2.5:7b' 直接拉取）: " choices

if [[ "$choices" == "s" ]]; then
    echo -e "${YELLOW}跳过拉取${NC}"
else
    for choice in $choices; do
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if [[ "$choice" == "0" ]]; then
                read -p "请输入模型名 (如 'qwen2.5:7b'): " custom_model
                pull_model "$custom_model"
            else
                idx=$((choice - 1))
                pull_model "${RECOMMENDED_MODELS[$idx]}"
            fi
        else
            pull_model "$choice"
        fi
    done
fi
echo

# 测试已拉取的模型
echo -e "${BLUE}=== 测试已拉取的模型 ===${NC}"
for model in $(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}'); do
    test_model "$model"
done
echo

# 写入配置
write_config
echo

# 输出总结
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  ✓ ParaJudge Ollama 部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo
echo -e "已安装的模型："
ollama list 2>/dev/null | tail -n +2
echo
echo -e "${BLUE}在 ParaJudge 中使用：${NC}"
echo "  1. 启动 ParaJudge: python -m desktop.main"
echo "  2. 辩论室选择模型: qwen2.5:7b （默认）"
echo "  3. 或使用 CLI:  python cli.py parajudge run \"你的问题\" --provider ollama --model qwen2.5:7b"
echo
echo -e "${BLUE}服务管理：${NC}"
echo "  启动: ollama serve"
echo "  停止: pkill ollama"
echo "  列表: ollama list"
echo "  删除: ollama rm <model>"
echo
