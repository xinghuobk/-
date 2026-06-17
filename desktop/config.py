"""ParaJudge Desktop 应用配置。"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _get_app_data_dir() -> Path:
    """跨平台获取用户数据目录（用于存放配置/日志/缓存）。"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "ParaJudge"


class AppConfig:
    """应用配置（启动时从环境变量或默认值读取）。"""

    # 窗口
    window_title: str = os.environ.get("PARAJUDGE_TITLE", "ParaJudge · AI 多智能体辩论评估")
    window_width: int = int(os.environ.get("PARAJUDGE_WIDTH", "1400"))
    window_height: int = int(os.environ.get("PARAJUDGE_HEIGHT", "900"))
    window_min_width: int = 1100
    window_min_height: int = 720
    confirm_close: bool = False  # 关闭时弹窗确认（默认关闭）

    # 后端
    backend_host: str = "127.0.0.1"
    backend_port: int = int(os.environ.get("PARAJUDGE_PORT", "8765"))
    # 说明：故意用 8765 而非 8000，避免与其他服务冲突

    # GUI 后端
    #   Windows: 'edgechromium' (WebView2) / 'mshtml' (IE 旧版)
    #   macOS:   'cocoa' (WebKit)
    #   Linux:   'gtk' (WebKitGTK)
    gui_backend: str = os.environ.get("PARAJUDGE_GUI", "")

    # 调试模式
    debug: bool = os.environ.get("PARAJUDGE_DEBUG", "0") == "1"

    @classmethod
    def user_data_dir(cls) -> Path:
        return _get_app_data_dir()

    @classmethod
    def cache_dir(cls) -> Path:
        d = cls.user_data_dir() / "cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def export_dir(cls) -> Path:
        d = cls.user_data_dir() / "exports"
        d.mkdir(parents=True, exist_ok=True)
        return d
