@echo off
REM ============================================================
REM ParaJudge - Ollama 本地 LLM 一键安装脚本 (Windows)
REM ============================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ============================================================
echo   ParaJudge - Ollama 本地 LLM 部署 (Windows)
echo ============================================================
echo.

REM 1. 检查 Ollama 是否已安装
where ollama >nul 2>&1
if errorlevel 1 (
    echo [1/5] Ollama 未安装，正在下载安装包...
    echo        下载地址: https://ollama.com/download/OllamaSetup.exe
    echo.
    echo 请选择：
    echo   1. 自动下载并静默安装（需要管理员权限）
    echo   2. 手动打开浏览器下载
    echo   3. 跳过（已通过其他方式安装）
    set /p choice=你的选择 (1/2/3):
    if "!choice!"=="1" (
        echo 正在下载 OllamaSetup.exe ...
        powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'"
        echo 正在安装...
        OllamaSetup.exe /S
        del OllamaSetup.exe
    ) else if "!choice!"=="2" (
        start https://ollama.com/download/OllamaSetup.exe
        echo 请下载安装后重新运行此脚本
        pause
        exit /b 1
    ) else (
        echo 跳过安装
    )
) else (
    echo [1/5] ✓ Ollama 已安装: 
    ollama --version
)
echo.

REM 2. 启动 Ollama 服务
echo [2/5] 启动 Ollama 服务...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo        正在后台启动 ollama serve ...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Ollama 服务启动失败
        echo          请手动运行 ollama serve
        pause
        exit /b 1
    )
)
echo        ✓ Ollama 服务已就绪
echo.

REM 3. 推荐模型
echo [3/5] ParaJudge 推荐模型：
echo   1. qwen2.5:7b     (中文主力，推荐)
echo   2. qwen2.5:14b    (中文高质量)
echo   3. llama3.1:8b    (英文)
echo   4. deepseek-r1:7b (推理增强)
echo   5. qwen2.5:3b     (低显存)
echo   0. 跳过
echo   自定义输入模型名直接拉取
echo.
set /p model_choice=请选择要拉取的模型（多选用空格分隔）:

if not "!model_choice!"=="0" if not "!model_choice!"=="" (
    for %%m in (!model_choice!) do (
        echo 正在拉取 %%m ...
        ollama pull %%m
    )
)
echo.

REM 4. 测试
echo [4/5] 测试已安装模型...
for /f "skip=1 tokens=1" %%i in ('ollama list') do (
    echo   测试 %%i ...
    curl -s -X POST http://localhost:11434/v1/chat/completions ^
        -H "Content-Type: application/json" ^
        -d "{\"model\":\"%%i\",\"messages\":[{\"role\":\"user\",\"content\":\"回复OK\"}],\"max_tokens\":10}" >nul 2>&1
    if errorlevel 1 (
        echo     [WARN] %%i 测试失败
    ) else (
        echo     [OK] %%i 可用
    )
)
echo.

REM 5. 写 ParaJudge 配置
echo [5/5] 写入 ParaJudge 配置...
(
echo /**
echo  * ParaJudge LLM 默认配置（自动生成）
echo  * 生成时间：%date% %time%
echo  */
echo window.PARAJUDGE_LLM_DEFAULTS = {
echo     providers: [
echo         { code: 'ollama', name: 'Ollama ^(本地^)', default_model: 'qwen2.5:7b', base_url: 'http://localhost:11434/v1' },
echo         { code: 'openai', name: 'OpenAI / 兼容', default_model: 'gpt-3.5-turbo' },
echo         { code: 'dashscope', name: '通义千问', default_model: 'qwen-max' },
echo         { code: 'mock', name: 'Mock ^(离线^)', default_model: 'mock-model' }
echo     ],
echo     available_models: []
echo };
) > frontend\js\llm-defaults.js
echo        ✓ 已写入 frontend\js\llm-defaults.js
echo.

echo ============================================================
echo   ✓ ParaJudge Ollama 部署完成！
echo ============================================================
echo.
echo 已安装模型：
ollama list
echo.
echo 在 ParaJudge 中使用：
echo   1. 启动 ParaJudge: desktop\start.bat
echo   2. 辩论室选择模型: qwen2.5:7b
echo   3. 或 CLI: python cli.py parajudge run "你的问题" --provider ollama --model qwen2.5:7b
echo.
pause
