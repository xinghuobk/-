@echo off
REM ============================================================
REM ParaJudge 桌面端 - Windows 开发模式启动
REM 不打包，直接用当前 Python 解释器运行
REM ============================================================

setlocal

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   ParaJudge Desktop - Dev Mode
echo ============================================================
echo.

REM 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

REM 安装依赖（如果缺失）
echo [1/3] Checking dependencies...
python -c "import webview, uvicorn, fastapi" 2>nul
if errorlevel 1 (
    echo Installing missing packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

echo [2/3] Starting ParaJudge Desktop...
echo.

REM 启动
python -m desktop.main

echo.
echo [3/3] ParaJudge exited.
pause
