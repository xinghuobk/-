@echo off
REM ============================================================
REM ParaJudge 桌面端 - 生成 NSIS 安装包（可选）
REM 需要先安装 NSIS 3.0+：https://nsis.sourceforge.io/Download
REM ============================================================

setlocal

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   ParaJudge Desktop - Build NSIS Installer
echo ============================================================
echo.

REM 检查 NSIS
where makensis >nul 2>&1
if errorlevel 1 (
    echo [ERROR] NSIS not found in PATH
    echo Please install NSIS 3.0+ from https://nsis.sourceforge.io/Download
    echo Or compile installer.nsi manually with NSIS editor.
    pause
    exit /b 1
)

REM 检查 dist/ParaJudge
if not exist dist\ParaJudge\ParaJudge.exe (
    echo [ERROR] dist\ParaJudge\ParaJudge.exe not found. Run build.bat first.
    pause
    exit /b 1
)

echo [1/3] Generating NSIS script...
REM 替换版本号（如果需要）
powershell -Command "(Get-Content desktop\installer.nsi) -replace '\$\{VERSION\}', '0.1.0' | Set-Content dist\ParaJudge-installer.nsi"

echo [2/3] Compiling installer...
cd dist
makensis ParaJudge-installer.nsi
cd ..

if errorlevel 1 (
    echo [ERROR] NSIS build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo Installer: dist\ParaJudge-Setup-0.1.0.exe
dir dist\ParaJudge-Setup-0.1.0.exe
pause
