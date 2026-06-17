"""ParaJudge 桌面端启动器

启动后端 uvicorn 子进程 → 等待就绪 → 创建 PyWebView 窗口 → 加载前端。
打包后是单一可执行文件，运行时无需 Python 环境。
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path

from desktop.server_runner import ServerRunner
from desktop.bridge import DesktopBridge
from desktop.config import AppConfig


def _setup_logging() -> None:
    log_dir = AppConfig.user_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "parajudge.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _resolve_resource_path(rel: str) -> Path:
    """解析资源路径（兼容 PyInstaller --onefile 打包后的 _MEIPASS 临时目录）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parent.parent / rel


def _is_already_running(port: int) -> bool:
    """检测端口是否已被占用（可能是上次的 ParaJudge 后台进程没关掉）。"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    _setup_logging()
    logger = logging.getLogger("parajudge.desktop")
    logger.info("=" * 60)
    logger.info("ParaJudge Desktop starting...")
    logger.info(f"  Python:   {sys.version.split()[0]}")
    logger.info(f"  Platform: {sys.platform}")
    logger.info(f"  CWD:      {os.getcwd()}")
    logger.info(f"  Frozen:   {getattr(sys, 'frozen', False)}")

    cfg = AppConfig()

    # 检查是否已有后端在运行
    if _is_already_running(cfg.backend_port):
        logger.info(f"检测到端口 {cfg.backend_port} 已被占用，假定后端已在运行")
        server = None
    else:
        # 启动后端 uvicorn 子进程
        server = ServerRunner(
            host="127.0.0.1",
            port=cfg.backend_port,
            log_level="info",
        )
        if not server.start():
            logger.error("后端启动失败")
            return 1
        # 等待后端就绪
        if not server.wait_ready(timeout=30):
            logger.error("后端未在 30s 内就绪")
            server.stop()
            return 2

    # 创建 PyWebView 窗口
    try:
        import webview
    except ImportError:
        logger.error("pywebview 未安装，请先 pip install pywebview")
        if server:
            server.stop()
        return 3

    bridge = DesktopBridge(server, cfg)

    window = webview.create_window(
        title=cfg.window_title,
        url=f"http://127.0.0.1:{cfg.backend_port}/ui/index.html",
        width=cfg.window_width,
        height=cfg.window_height,
        min_size=(cfg.window_min_width, cfg.window_min_height),
        resizable=True,
        fullscreen=False,
        easy_drag=True,
        shadow=True,
        text_select=True,
        confirm_close=cfg.confirm_close,
    )

    # 把窗口和桥注入到 webview 全局，供 evaluate_code 使用
    webview.windows[0] = window  # type: ignore[index]
    window.expose(  # type: ignore[attr-defined]
        bridge.open_file_dialog,
        bridge.save_file_dialog,
        bridge.open_path,
        bridge.show_in_folder,
        bridge.export_verdict_json,
        bridge.export_verdict_markdown,
        bridge.get_app_info,
        bridge.get_data_dir,
        bridge.quit_app,
    )

    # 关闭窗口时清理
    def on_closing():
        logger.info("Window closing, stopping server...")
        if server:
            server.stop()
        return True

    window.events.closing += on_closing  # type: ignore[attr-defined]

    logger.info(f"启动窗口: {cfg.window_title} ({cfg.window_width}x{cfg.window_height})")
    webview.start(
        gui=cfg.gui_backend,           # 显式指定 GUI 后端
        debug=cfg.debug,
        http_server=False,
    )

    logger.info("ParaJudge Desktop exited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
