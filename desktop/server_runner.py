"""后端 uvicorn 子进程管理。

桌面端启动时拉起 FastAPI 后端作为子进程，关闭时优雅 kill。
"""
from __future__ import annotations

import logging
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("parajudge.desktop.server")


def _resolve_uvicorn_cmd() -> List[str]:
    """构造 uvicorn 启动命令。"""
    # 直接用当前 Python 解释器调 uvicorn
    # 比依赖 PATH 中的 uvicorn 更稳
    return [sys.executable, "-m", "uvicorn", "backend.api.server:app"]


def _get_backend_cwd() -> Path:
    """后端运行的工作目录（项目根）。"""
    # desktop/main.py → 项目根是 desktop 的父目录的父目录
    return Path(__file__).resolve().parent.parent


class ServerRunner:
    """管理后端 uvicorn 子进程的生命周期。"""

    def __init__(self, host: str, port: int, log_level: str = "info"):
        self.host = host
        self.port = port
        self.log_level = log_level
        self.process: Optional[subprocess.Popen] = None
        self.cwd = _get_backend_cwd()

    def start(self) -> bool:
        """启动子进程；返回是否成功 fork。"""
        if self.process is not None:
            logger.warning("后端进程已存在，先停止旧的")
            self.stop()

        cmd = _resolve_uvicorn_cmd() + [
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", self.log_level,
            "--no-access-log",     # 桌面端不需要 access log
        ]

        env = os.environ.copy()
        env["PARAJUDGE_DESKTOP"] = "1"  # 后端可借此判断是否桌面环境

        logger.info(f"启动后端: {' '.join(cmd)}")
        logger.info(f"  CWD: {self.cwd}")

        # 打包后：stdout/stderr 输出到日志文件
        log_dir = Path.home() / ".parajudge" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = open(log_dir / "backend.log", "a", encoding="utf-8")

        try:
            if sys.platform == "win32":
                # Windows 下隐藏子进程控制台窗口
                creationflags = subprocess.CREATE_NO_WINDOW
                self.process = subprocess.Popen(
                    cmd,
                    cwd=str(self.cwd),
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                    close_fds=True,
                )
            else:
                self.process = subprocess.Popen(
                    cmd,
                    cwd=str(self.cwd),
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
        except FileNotFoundError as e:
            logger.error(f"找不到 Python 解释器或 uvicorn: {e}")
            return False
        except Exception as e:
            logger.exception(f"启动子进程失败: {e}")
            return False

        logger.info(f"后端子进程已 fork，PID={self.process.pid}")
        return True

    def wait_ready(self, timeout: float = 30.0, poll_interval: float = 0.3) -> bool:
        """轮询端口直到后端就绪或超时。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.process and self.process.poll() is not None:
                logger.error(f"后端进程已退出，returncode={self.process.returncode}")
                return False
            if self._is_listening():
                logger.info(f"后端已就绪 (http://{self.host}:{self.port})")
                return True
            time.sleep(poll_interval)
        logger.error(f"等待后端就绪超时 ({timeout}s)")
        return False

    def _is_listening(self) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                return s.connect_ex((self.host, self.port)) == 0
            except OSError:
                return False

    def stop(self) -> None:
        """停止子进程（先 SIGTERM，再 SIGKILL 兜底）。"""
        if self.process is None:
            return
        if self.process.poll() is not None:
            logger.info("后端进程已退出")
            self.process = None
            return

        logger.info("停止后端进程...")
        try:
            if sys.platform == "win32":
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
                logger.info("后端进程已优雅退出")
            except subprocess.TimeoutExpired:
                logger.warning("后端 5s 内未退出，强制 kill")
                self.process.kill()
                self.process.wait(timeout=2)
        except Exception as e:
            logger.exception(f"停止后端时出错: {e}")
        finally:
            self.process = None

    @property
    def pid(self) -> Optional[int]:
        return self.process.pid if self.process else None
