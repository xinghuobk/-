# -*- mode: python ; coding: utf-8 -*-
"""
ParaJudge 桌面端 PyInstaller 打包配置

打包后产物：
  dist/ParaJudge.exe             # 单一可执行文件（开发）
  dist/ParaJudge/                # 文件夹模式（更易调试）
  dist/ParaJudge-0.1.0-setup.exe # NSIS 安装包（build_installer.bat 进一步打包）

使用方法：
  pyinstaller ParaJudge.spec
  # 或运行 build.bat
"""
from pathlib import Path
import os
import sys

block_cipher = None

# 推断项目根：spec 文件可能在 PyInstaller 命名空间下 exec，没有 __file__
# 采用 cwd 作为根（运行 build.bat 时 cwd 一定是项目根）
PROJECT_ROOT = Path(os.getcwd()).resolve()
ICON_PATH = PROJECT_ROOT / "desktop" / "assets" / "icon.ico"

# ============================================================
# 收集数据文件
# ============================================================
datas = [
    # 前端静态资源
    (str(PROJECT_ROOT / "frontend"), "frontend"),
    # 后端 Python 包
    (str(PROJECT_ROOT / "backend"), "backend"),
    # 核心 Python 模块
    (str(PROJECT_ROOT / "src"), "src"),
]

# ============================================================
# 隐藏导入（PyInstaller 静态分析不出来的动态导入）
# ============================================================
hiddenimports = [
    # 后端
    "backend.api.server",
    "backend.api.routers.parajudge",
    "backend.api.routers.health",
    "backend.api.routers.judges",
    "backend.api.routers.examples",
    "backend.api.schemas_api",
    "backend.api.job_manager",
    "backend.api.sse",
    "backend.models.schemas",
    # 核心模块
    "src.debate.evidence_builder",
    "src.debate.simple_debate",
    "src.debate.prompts",
    "src.judgment.review_engine",
    "src.judgment.judgment_engine",
    "src.orchestration.orchestrator",
    "src.writer.llm_client",
    "src.writer.llm_helper",
    "src.writer.prompt_templates",
    "src.search.engine",
    "src.search.arxiv_client",
    "src.search.crossref_client",
    "src.search.semantic_scholar_client",
    "src.parse.pdf_parser",
    "src.parse.text_cleaner",
    "src.reference.bibtex_manager",
    "src.utils.io",
    # 第三方
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "starlette.applications",
    "starlette.routing",
    "starlette.middleware",
    "starlette.middleware.cors",
    "pydantic",
    "pydantic.main",
    "pydantic.fields",
    "pydantic.types",
    "typer",
    "rich",
    "httpx",
    "anyio",
    "sniffio",
    # webview
    "webview",
    "webview.platforms.winforms",
]

# 排除不需要的库（减小体积）
excludes = [
    "tkinter",
    "matplotlib",
    "numpy.tests",
    "pandas",
    "scipy",
    "notebook",
    "IPython",
    "pytest",
]

a = Analysis(
    [str(PROJECT_ROOT / "desktop" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
print("ParaJudge.spec Analysis OK with", len(datas), "data dirs and", len(hiddenimports), "hiddenimports")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ParaJudge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                   # UPX 压缩（体积更小）
    console=False,              # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ParaJudge",
)
