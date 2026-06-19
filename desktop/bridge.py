"""PyWebView JS-Python 桥（暴露给前端调用）。

前端通过 `window.pywebview.api.<方法名>(...)` 调用：
- 打开本地文件对话框
- 保存文件对话框
- 在系统文件管理器中显示文件
- 导出裁决 JSON / Markdown
- 退出应用
"""
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from desktop.config import AppConfig

logger = logging.getLogger("parajudge.desktop.bridge")


class DesktopBridge:
    """暴露给前端 window.pywebview.api 的方法集合。"""

    def __init__(self, server, config: AppConfig):
        self.server = server
        self.config = config
        # 标记应用为桌面运行模式
        self._is_desktop = True

    # ============================================================
    # 文件对话框
    # ============================================================

    def open_file_dialog(self, title: str = "选择文件", file_types: str = "所有文件 (*.*)|*.*") -> Optional[str]:
        """弹出系统文件选择对话框，返回选中的文件路径（取消返回 None）。"""
        try:
            import webview
            window = webview.windows[0] if webview.windows else None
            if window is None:
                return None
            # file_types 格式："PDF 文件 (*.pdf)|*.pdf|所有文件 (*.*)|*.*"
            result = window.create_file_dialog(
                dialog_type=webview.FileDialog.OPEN,
                directory=str(Path.home()),
                allow_multiple=False,
                file_types=file_types,
            )
            if not result:
                return None
            # result 可能是 str 或 list，统一返回 str
            if isinstance(result, (list, tuple)):
                return str(result[0]) if result else None
            return str(result)
        except Exception as e:
            logger.exception(f"open_file_dialog 失败: {e}")
            return None

    def save_file_dialog(
        self,
        title: str = "保存文件",
        default_filename: str = "",
        file_types: str = "所有文件 (*.*)|*.*",
    ) -> Optional[str]:
        """弹出系统保存对话框，返回用户选择的保存路径。"""
        try:
            import webview
            window = webview.windows[0] if webview.windows else None
            if window is None:
                return None
            result = window.create_file_dialog(
                dialog_type=webview.FileDialog.SAVE,
                directory=str(self.config.export_dir()),
                save_filename=default_filename,
                file_types=file_types,
            )
            if not result:
                return None
            return str(result)
        except Exception as e:
            logger.exception(f"save_file_dialog 失败: {e}")
            return None

    # ============================================================
    # 文件操作
    # ============================================================

    def open_path(self, path: str) -> bool:
        """用系统默认应用打开文件或目录。"""
        try:
            p = Path(path)
            if not p.exists():
                logger.warning(f"路径不存在: {p}")
                return False
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(p)], check=True)
            else:
                subprocess.run(["xdg-open", str(p)], check=True)
            return True
        except Exception as e:
            logger.exception(f"open_path 失败: {e}")
            return False

    def show_in_folder(self, path: str) -> bool:
        """在系统文件管理器中显示并选中文件。"""
        try:
            p = Path(path).resolve()
            if not p.exists():
                return False
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(p)], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(p)], check=False)
            else:
                subprocess.run(["xdg-open", str(p.parent)], check=False)
            return True
        except Exception as e:
            logger.exception(f"show_in_folder 失败: {e}")
            return False

    # ============================================================
    # 导出裁决
    # ============================================================

    def export_verdict_json(self, payload_json: str) -> str:
        """导出裁决为 JSON 文件。返回文件路径（失败返回空字符串）。"""
        try:
            data = json.loads(payload_json)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            problem = data.get("problem", "verdict")[:30].replace("/", "-")
            default = f"parajudge-{ts}-{problem}.json"
            path = self.save_file_dialog(
                title="导出裁决 JSON",
                default_filename=default,
                file_types="JSON 文件 (*.json)|*.json",
            )
            if not path:
                return ""
            # 确保 .json 后缀
            if not path.lower().endswith(".json"):
                path += ".json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已导出 JSON: {path}")
            return str(path)
        except Exception as e:
            logger.exception(f"export_verdict_json 失败: {e}")
            return ""

    def export_verdict_markdown(self, markdown_text: str, problem: str = "verdict") -> str:
        """导出裁决为 Markdown 文件。"""
        try:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            safe = (problem or "verdict")[:30].replace("/", "-")
            default = f"parajudge-{ts}-{safe}.md"
            path = self.save_file_dialog(
                title="导出裁决 Markdown",
                default_filename=default,
                file_types="Markdown 文件 (*.md)|*.md",
            )
            if not path:
                return ""
            if not path.lower().endswith(".md"):
                path += ".md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            logger.info(f"已导出 Markdown: {path}")
            return str(path)
        except Exception as e:
            logger.exception(f"export_verdict_markdown 失败: {e}")
            return ""

    # ============================================================
    # 元信息
    # ============================================================

    def get_app_info(self) -> Dict[str, Any]:
        """返回应用元信息。"""
        return {
            "name": "ParaJudge",
            "version": "0.1.0",
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "backend_port": self.config.backend_port,
            "is_desktop": True,
            "data_dir": str(self.config.user_data_dir()),
            "export_dir": str(self.config.export_dir()),
        }

    def get_data_dir(self) -> str:
        """返回用户数据目录。"""
        return str(self.config.user_data_dir())

    # ============================================================
    # 应用控制
    # ============================================================

    def quit_app(self) -> None:
        """退出应用。"""
        logger.info("quit_app called from frontend")
        try:
            import webview
            if webview.windows:
                for w in webview.windows:
                    w.destroy()
        except Exception as e:
            logger.exception(f"quit_app 失败: {e}")
            sys.exit(0)
