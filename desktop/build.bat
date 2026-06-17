@echo off
REM ============================================================
REM ParaJudge 桌面端 - Windows 打包脚本
REM 用 PyInstaller 打包成单一 .exe（实际是文件夹+exe）
REM 产物：dist/ParaJudge/ParaJudge.exe
REM ============================================================

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   ParaJudge Desktop - Build for Windows
echo ============================================================
echo.

REM 1. 检查环境
echo [1/5] Checking environment...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
where pyinstaller >nul 2>&l
if errorlevel 1 (
    echo PyInstaller not found, installing...
    pip install pyinstaller pystray pillow -q
)

REM 2. 清理旧产物
echo [2/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ParaJudge.spec del ParaJudge.spec

REM 3. 生成 spec
echo [3/5] Generating spec file...
copy /Y desktop\ParaJudge.spec ParaJudge.spec >nul

REM 4. 执行打包
echo [4/5] Building... (this may take a few minutes)
pyinstaller ParaJudge.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM 5. 复制到 dist
echo [5/5] Finalizing...
if not exist dist\ParaJudge mkdir dist\ParaJudge

REM 复制资源文件
if exist README.md copy /Y README.md dist\ParaJudge\ >nul
if exist requirements.txt copy /Y requirements.txt dist\ParaJudge\ >nul
if exist desktop\README.md copy /Y desktop\README.md dist\ParaJudge\桌面端使用说明.md >nul

echo.
echo ============================================================
echo   Build complete!
echo.
echo   Output:  dist\ParaJudge\ParaJudge.exe
echo   Size:    (see dist\ParaJudge\)
echo.
echo   To create installer, run:  build_installer.bat
echo ============================================================
echo.

REM 显示目录
dir dist\ParaJudge\ParaJudge.exe
pause
