"""
文本清理工具
- clean_text: 去除多余空格、连字符换行、特殊字符
- normalize_whitespace: 规范化空白
- remove_headers_footers: 简单页眉页脚去除（重复短行）
- extract_abstract: 尝试从文本中提取摘要
"""
from __future__ import annotations

import re
from typing import List


_HYPHEN_NEWLINE_RE = re.compile(r"(\w)-\s*\n\s*(\w)", re.UNICODE)
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ABSTRACT_HEADING_RE = re.compile(
    r"(?im)^\s*(?:abstract|摘要|ABSTRACT)\s*[:：\.。]?\s*$"
)


def normalize_whitespace(text: str) -> str:
    """规范化空白：将多种空白压缩为单个空格，保留换行。"""
    if not text:
        return ""
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def clean_text(text: str) -> str:
    """去除多余空格、连字符换行、特殊字符，统一规范化。"""
    if not text:
        return ""
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _HYPHEN_NEWLINE_RE.sub(r"\1\2", text)
    lines: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    text = "\n".join(lines)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def remove_headers_footers(text: str, min_repeat: int = 2, max_len: int = 80) -> str:
    """
    简单页眉页脚去除：统计重复出现的短行并删除。

    - min_repeat: 至少出现多少次才被视为页眉/页脚
    - max_len: 行的最大长度（页眉页脚通常较短）
    """
    if not text:
        return ""
    lines = text.splitlines()
    counter: dict = {}
    for line in lines:
        stripped = line.strip()
        if 0 < len(stripped) <= max_len:
            counter[stripped] = counter.get(stripped, 0) + 1

    blacklist = {ln for ln, cnt in counter.items() if cnt >= min_repeat}

    cleaned: List[str] = []
    for line in lines:
        if line.strip() in blacklist:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def extract_abstract(text: str) -> str:
    """
    尝试从文本中提取摘要。
    策略：
    1. 匹配 "Abstract" / "摘要" 标题行，之后截取到下一个章节标题或空行段落
    2. 若未找到标题，则返回前几个段落中较长的一段
    """
    if not text:
        return ""

    normalized = clean_text(text)

    section_heading_re = re.compile(
        r"(?im)^\s*(?:\d+\.?\s*)?"
        r"(?:abstract|摘要|introduction|引言|keywords|key\s*words|关键词"
        r"|1\s+introduction|I\.?\s+INTRODUCTION)\b.*$"
    )

    m = _ABSTRACT_HEADING_RE.search(normalized)
    if m:
        start = m.end()
        remainder = normalized[start:]
        next_match = section_heading_re.search(remainder)
        end = next_match.start() if next_match else len(remainder)
        abstract_text = remainder[:end].strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", abstract_text) if p.strip()]
        return "\n\n".join(paragraphs).strip()

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    for p in paragraphs[:3]:
        if 150 <= len(p) <= 1500:
            return p
    return paragraphs[0] if paragraphs else ""
