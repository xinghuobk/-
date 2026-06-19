"""BibTeX 引用管理模块。

提供 BibTeX 文件的解析、保存、搜索、以及输出到多种学术引用格式
（APA、GB/T 7714 中文）的能力，同时支持从论文元数据生成 BibTeX
条目字符串。
"""
from __future__ import annotations

import re
from typing import Dict, List

from backend.models.schemas import BibEntry, PaperMeta


_ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)
_FIELD_RE = re.compile(
    r"(\w[\w\-]*)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\"|([^,}\n]+))",
    re.IGNORECASE | re.DOTALL,
)


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class BibTeXManager:
    """BibTeX 管理器。

    支持加载 .bib 文件、保存文件、添加条目、关键词搜索，
    以及导出到 APA / GB/T 7714 等引用格式。
    """

    def __init__(self, entries: List[BibEntry] | None = None) -> None:
        self.entries: List[BibEntry] = list(entries) if entries else []

    # ------------------------------------------------------------------
    # 文件读写
    # ------------------------------------------------------------------
    def load_file(self, path: str) -> List[BibEntry]:
        """解析 .bib 文件，返回 BibEntry 列表。

        解析采用简单但稳健的策略：先识别 ``@type{key,``，
        然后找到配对的右大括号 ``}``（考虑字段中的嵌套括号），
        最后在块内使用正则抓取 ``field = {value}`` 形式。
        """
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        entries: List[BibEntry] = []
        i = 0
        n = len(text)
        while i < n:
            m = _ENTRY_RE.search(text, i)
            if not m:
                break
            entry_type = m.group(1).lower()
            key = m.group(2)
            start = m.end()
            depth = 1
            j = start
            while j < n and depth > 0:
                ch = text[j]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = text[start:j]
            raw_start = m.start()
            raw_end = j + 1
            raw = text[raw_start:raw_end].strip()
            fields: Dict[str, str] = {}
            for fm in _FIELD_RE.finditer(body):
                name = fm.group(1).strip().lower()
                val = fm.group(2) or fm.group(3) or fm.group(4) or ""
                fields[name] = _clean_value(val)
            entries.append(
                BibEntry(
                    key=key,
                    entry_type=entry_type,
                    fields=fields,
                    raw=raw,
                )
            )
            i = j + 1

        self.entries = entries
        return entries

    def save_file(self, entries: List[BibEntry], path: str) -> None:
        """将 entries 保存为 .bib 文件。"""
        lines: List[str] = []
        for entry in entries:
            lines.append(f"@{entry.entry_type}{{{entry.key},")
            for name, value in entry.fields.items():
                safe_value = value.replace("{", "(").replace("}", ")")
                lines.append(f"  {name} = {{{safe_value}}},")
            lines.append("}\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # ------------------------------------------------------------------
    # 条目管理
    # ------------------------------------------------------------------
    def add_entry(self, entry: BibEntry) -> None:
        """新增条目。"""
        self.entries.append(entry)

    def add_entry_str(self, bibtex: str) -> BibEntry | None:
        """从 BibTeX 字符串解析并添加条目。"""
        i = 0
        n = len(bibtex)
        m = _ENTRY_RE.search(bibtex, i)
        if not m:
            return None
        entry_type = m.group(1).lower()
        key = m.group(2)
        start = m.end()
        depth = 1
        j = start
        while j < n and depth > 0:
            ch = bibtex[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = bibtex[start:j]
        raw = bibtex[m.start():j + 1].strip()
        fields: Dict[str, str] = {}
        for fm in _FIELD_RE.finditer(body):
            name = fm.group(1).strip().lower()
            val = fm.group(2) or fm.group(3) or fm.group(4) or ""
            fields[name] = _clean_value(val)
        entry = BibEntry(
            key=key,
            entry_type=entry_type,
            fields=fields,
            raw=raw,
        )
        self.entries.append(entry)
        return entry

    def search(self, keyword: str) -> List[BibEntry]:
        """关键词搜索（不区分大小写，覆盖 key 与字段值）。"""
        kw = keyword.strip().lower()
        if not kw:
            return list(self.entries)
        result: List[BibEntry] = []
        for entry in self.entries:
            if kw in entry.key.lower() or kw in entry.entry_type.lower():
                result.append(entry)
                continue
            for value in entry.fields.values():
                if kw in value.lower():
                    result.append(entry)
                    break
        return result

    # ------------------------------------------------------------------
    # 格式转换
    # ------------------------------------------------------------------
    def to_apa(self, entry: BibEntry) -> str:
        """转为 APA 7th 风格引用。

        模板：``Authors. (Year). Title. Journal.``
        当条目类型为 book 时使用 Publisher 替代 Journal。
        """
        fields = entry.fields
        authors = fields.get("author", "").strip() or "Anonymous"
        year = fields.get("year", "").strip() or "n.d."
        title = fields.get("title", "").strip() or "Untitled"
        journal = fields.get("journal", "").strip() or fields.get(
            "booktitle", ""
        ).strip()

        if entry.entry_type.lower() == "book":
            publisher = fields.get("publisher", "").strip()
            if publisher:
                return f"{authors}. ({year}). {title}. {publisher}."
            return f"{authors}. ({year}). {title}."

        if journal:
            extra_bits: List[str] = []
            volume = fields.get("volume", "").strip()
            number = fields.get("number", "").strip()
            if volume:
                extra_bits.append(volume)
            if number:
                extra_bits.append(f"({number})")
            vol_str = ", ".join(extra_bits)
            pages = fields.get("pages", "").strip()
            journal_part = f"{journal}, {vol_str}" if vol_str else journal
            if pages:
                journal_part += f", {pages}"
            return f"{authors}. ({year}). {title}. {journal_part}."
        return f"{authors}. ({year}). {title}."

    def to_gb7714(self, entry: BibEntry) -> str:
        """转为 GB/T 7714-2015 中文格式。

        期刊文章模板：``作者. 题名[J]. 刊名, 年, 卷(期): 页码.``
        图书模板：``作者. 书名[M]. 出版地: 出版社, 年: 页码.``
        """
        fields = entry.fields
        authors = fields.get("author", "").strip() or "佚名"
        title = fields.get("title", "").strip() or "未命名"
        year = fields.get("year", "").strip()
        journal = fields.get("journal", "").strip() or fields.get(
            "booktitle", ""
        ).strip()
        volume = fields.get("volume", "").strip()
        number = fields.get("number", "").strip()
        pages = fields.get("pages", "").strip()
        publisher = fields.get("publisher", "").strip()

        etype = entry.entry_type.lower()
        if etype == "book":
            label = "[M]"
            parts = [f"{authors}. {title}{label}."]
            pub_parts: List[str] = []
            if publisher:
                pub_parts.append(publisher)
            if year:
                pub_parts.append(year)
            if pub_parts:
                parts[-1] += " " + ", ".join(pub_parts) + "."
            if pages:
                parts.append(f"{pages}.")
            return " ".join(parts)

        label = "[J]" if etype == "article" else "[C]"
        main = f"{authors}. {title}{label}."
        j_parts: List[str] = []
        if journal:
            j_parts.append(journal)
        if year:
            j_parts.append(year)
        middle = ", ".join(j_parts)
        tail = ""
        if volume and number:
            tail += f"{volume}({number})"
        elif volume:
            tail += volume
        elif number:
            tail += f"({number})"
        if pages:
            tail += (f": {pages}" if tail else f"{pages}")
        if middle:
            main += f" {middle}"
            if tail:
                main += f", {tail}"
        elif tail:
            main += f" {tail}"
        if not main.endswith("."):
            main += "."
        return main


# ----------------------------------------------------------------------
# 便捷函数
# ----------------------------------------------------------------------
def generate_bibtex_from_paper(paper: PaperMeta) -> str:
    """从论文元数据生成 BibTeX 条目字符串。"""
    key = _generate_key(paper)
    etype = "article"
    lines: List[str] = [f"@{etype}{{{key},"]

    if paper.authors:
        lines.append(f"  author = {{ {' and '.join(paper.authors)} }},")
    if paper.title:
        lines.append(f"  title = {{{paper.title}}},")
    if paper.year is not None:
        lines.append(f"  year = {{{paper.year}}},")
    if paper.venue:
        lines.append(f"  journal = {{{paper.venue}}},")
    if paper.doi:
        lines.append(f"  doi = {{{paper.doi}}},")
    if paper.arxiv_id:
        lines.append(f"  eprint = {{{paper.arxiv_id}}},")
    if paper.pdf_url:
        lines.append(f"  url = {{{paper.pdf_url}}},")
    if paper.url:
        lines.append(f"  howpublished = {{{', '.join(paper.url)}}},")
    lines.append("}")
    return "\n".join(lines)


def _generate_key(paper: PaperMeta) -> str:
    first_author = (paper.authors[0] if paper.authors else "author")
    last_name = re.split(r"[\s,]+", first_author.strip())[-1]
    last_name = re.sub(r"[^A-Za-z0-9]+", "", last_name) or "author"
    year = paper.year or "xxxx"
    title_token = ""
    if paper.title:
        tokens = [
            t for t in re.split(r"\W+", paper.title.lower())
            if t and t not in {"a", "an", "the", "of", "on", "in", "and", "for"}
        ]
        title_token = tokens[0] if tokens else ""
    return f"{last_name.lower()}{year}{title_token}"


__all__ = [
    "BibTeXManager",
    "generate_bibtex_from_paper",
]
