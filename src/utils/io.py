"""通用 I/O 工具：目录创建、JSON/文本读写。"""
from __future__ import annotations

import json
import os
from typing import Any


def ensure_dir(path: str) -> None:
    """若目录不存在则创建；父目录也会一并创建。

    对传入的文件路径，会自动取其父目录进行创建。
    """
    if not path:
        return
    target = os.path.dirname(path) if not os.path.basename(
        path
    ) or "." in os.path.basename(path) else path
    # Fallback: 如果 path 本身是目录名（如 ./data），dirname 会为空；
    # 此时对 path 直接调用 makedirs。
    final = target or path
    if final and not os.path.exists(final):
        os.makedirs(final, exist_ok=True)


def save_json(obj: Any, path: str) -> None:
    """将对象以 UTF-8 JSON 形式保存到文件。"""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_json(path: str) -> Any:
    """从文件加载 JSON 对象。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_text(text: str, path: str) -> None:
    """将字符串以 UTF-8 形式保存到文件。"""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_text(path: str) -> str:
    """从文件读取文本。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


__all__ = [
    "ensure_dir",
    "save_json",
    "load_json",
    "save_text",
    "load_text",
]
