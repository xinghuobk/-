"""
核心 PDF 解析器
依赖: PyMuPDF (fitz), 可选 pdfplumber（用于表格提取）

提供:
- PDFParser 类：围绕 PDF 的一组解析方法
- parse_pdf(pdf_path) 便捷函数

结果模型统一使用 backend.models.schemas 中的：
- PDFPage
- PDFParseResult
- PaperMeta

异常处理:
- 文件不存在: FileNotFoundError
- PDF 损坏 / 无法打开: RuntimeError (由 fitz 抛出，封装为 ValueError)
"""
from __future__ import annotations

import os
import re
import time
from collections import Counter
from typing import Dict, List, Optional

from backend.models.schemas import PDFPage, PDFParseResult, PaperMeta

from .text_cleaner import clean_text, normalize_whitespace, remove_headers_footers

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    fitz = None
    _FITZ_IMPORT_ERROR = exc
else:
    _FITZ_IMPORT_ERROR = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None


# ============================================================
# 章节标题正则
# ============================================================

_SECTION_PATTERNS: List[tuple] = [
    ("abstract", re.compile(r"(?im)^\s*(?:\d+\.?\s*)?abstract\s*[:：.]?\s*$")),
    ("摘要", re.compile(r"(?m)^\s*摘\s*要\s*[:：.]?\s*$")),
    ("introduction", re.compile(
        r"(?im)^\s*(?:1\.?|I\.?)?\s*(?:introduction|intro|引言|引\s*言)\s*[:：.]?\s*$"
    )),
    ("method", re.compile(
        r"(?im)^\s*(?:\d+\.?|II\.?)?\s*(?:method(?:s)?|methodology|materials?\s+and\s+methods?|"
        r"方法|实验方法|materials\s*&?\s*methods?)\s*[:：.]?\s*$"
    )),
    ("results", re.compile(
        r"(?im)^\s*(?:\d+\.?|III\.?)?\s*(?:results?|实验结果|结果)\s*[:：.]?\s*$"
    )),
    ("discussion", re.compile(
        r"(?im)^\s*(?:\d+\.?|IV\.?)?\s*(?:discussion|讨论)\s*[:：.]?\s*$"
    )),
    ("conclusion", re.compile(
        r"(?im)^\s*(?:\d+\.?|V\.?)?\s*(?:conclusions?|summary|结论|结\s*论)\s*[:：.]?\s*$"
    )),
    ("references", re.compile(
        r"(?im)^\s*(?:references?|bibliography|works\s+cited|参\s*考\s*文\s*献|参考文献)\s*[:：.]?\s*$"
    )),
    ("acknowledgments", re.compile(
        r"(?im)^\s*(?:acknowledge?ments?|acknowledgements?|致谢)\s*[:：.]?\s*$"
    )),
    ("appendix", re.compile(
        r"(?im)^\s*(?:appendix|appendices?|附录)\s*[:：.]?\s*[A-Za-z0-9]?\s*$"
    )),
]

_FIGURE_CAPTION_RE = re.compile(
    r"(?im)(?:^|\n)\s*(?:figure|fig\.?|figure\s*\d+[.:：]?|图\s*\d+)\b[^\n]*",
)

_TABLE_MARK_RE = re.compile(
    r"(?im)(?:^|\n)\s*(?:table\s*\d+|表\s*\d+)\b[^\n]*",
)


# ============================================================
# 英文停用词（简易内置，避免外部依赖）
# ============================================================

_ENGLISH_STOPWORDS = {
    "a", "an", "and", "or", "but", "if", "then", "else", "when", "at",
    "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "in", "out", "on", "off", "over", "under", "again", "further",
    "once", "here", "there", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "the", "of", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "this", "that", "these", "those", "i", "me", "my", "myself",
    "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
    "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
    "herself", "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "whose", "as", "also",
}


def _slugify(text: str) -> str:
    """将任意文本转成简短 slug，作为 id 使用。"""
    if not text:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "-", text.strip())
    cleaned = cleaned.strip("-").lower()
    return cleaned[:80] or "untitled"


# ============================================================
# PDFParser
# ============================================================

class PDFParser:
    """
    核心 PDF 解析器。

    用法:
        parser = PDFParser("/path/to/paper.pdf")
        result = parser.parse()
        parser.close()

    或使用上下文管理器:
        with PDFParser("/path/to/paper.pdf") as parser:
            result = parser.parse()
    """

    def __init__(self, pdf_path: str):
        if _FITZ_IMPORT_ERROR is not None:
            raise RuntimeError(
                f"PyMuPDF (fitz) 未正确安装: {_FITZ_IMPORT_ERROR}"
            ) from _FITZ_IMPORT_ERROR
        if not isinstance(pdf_path, str) or not pdf_path:
            raise ValueError("pdf_path 必须为非空字符串")
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        if not os.path.isfile(pdf_path):
            raise ValueError(f"路径不是文件: {pdf_path}")

        self.pdf_path = pdf_path
        try:
            self._doc: fitz.Document = fitz.open(pdf_path)
        except Exception as exc:
            raise ValueError(f"无法打开 PDF 文件（可能已损坏）: {pdf_path}: {exc}") from exc

        self._closed = False
        self._pages_cache: Optional[List[PDFPage]] = None
        self._full_text_cache: Optional[str] = None

    # --------------------------------------------------------
    # 上下文管理 / 资源管理
    # --------------------------------------------------------
    def __enter__(self) -> "PDFParser":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """关闭 PDF 文档，释放资源。"""
        if getattr(self, "_closed", False):
            return
        doc = getattr(self, "_doc", None)
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
        self._closed = True

    # --------------------------------------------------------
    # 基本文本提取
    # --------------------------------------------------------
    def extract_text_by_page(self) -> List[PDFPage]:
        """逐页提取文本，返回 PDFPage 列表（使用统一模型）。"""
        if self._closed:
            raise RuntimeError("PDFParser 已关闭")
        if self._pages_cache is not None:
            return self._pages_cache

        pages: List[PDFPage] = []
        for i, page in enumerate(self._doc.pages(), start=1):
            try:
                raw = page.get_text("text") or ""
            except Exception:
                raw = ""
            text = clean_text(raw)
            text = remove_headers_footers(text)
            pages.append(PDFPage(
                page_num=i,
                text=text,
                images_count=0,
            ))
        self._pages_cache = pages
        return pages

    @property
    def full_text(self) -> str:
        if self._full_text_cache is not None:
            return self._full_text_cache
        pages = self.extract_text_by_page()
        joined = "\n\n".join(p.text for p in pages if p.text)
        self._full_text_cache = joined
        return joined

    # --------------------------------------------------------
    # 章节识别
    # --------------------------------------------------------
    def extract_sections(self) -> Dict[str, str]:
        """
        基于常见章节标题正则匹配，识别章节内容。
        返回 {section_name: section_text} 字典。
        """
        text = self.full_text
        sections: Dict[str, str] = {}
        if not text:
            return sections

        hits: List[tuple] = []
        for name, pattern in _SECTION_PATTERNS:
            for m in pattern.finditer(text):
                hits.append((m.start(), m.end(), name))

        hits.sort(key=lambda x: x[0])
        if not hits:
            return sections

        seen: set = set()
        ordered: List[tuple] = []
        for start, end, name in hits:
            if name in seen:
                continue
            seen.add(name)
            ordered.append((start, end, name))

        for idx, (start, end, name) in enumerate(ordered):
            next_start = ordered[idx + 1][0] if idx + 1 < len(ordered) else len(text)
            snippet = text[end:next_start].strip()
            if not snippet:
                continue
            lines = [ln.strip() for ln in snippet.splitlines() if ln.strip()]
            sections[name] = "\n".join(lines)[:8000]
        return sections

    # --------------------------------------------------------
    # 参考文献提取
    # --------------------------------------------------------
    def extract_references(self) -> List[str]:
        """
        提取参考文献部分（从 "References" 标题到文档末尾），按条目拆分。
        """
        text = self.full_text
        if not text:
            return []

        ref_pattern = _SECTION_PATTERNS[7][1]
        m = ref_pattern.search(text)
        if not m:
            return []

        block = text[m.end():].strip()
        entries: List[str] = []

        raw_lines = block.splitlines()
        merged: List[str] = []
        buffer = ""
        for line in raw_lines:
            line = line.rstrip()
            if not line.strip():
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                continue
            if re.match(r"^\s*(?:\[\d+\]|\d+\.?\s|\([1-9][0-9]*\))", line) or \
                    re.match(r"^[A-Z][A-Za-z'`\- ]+,", line):
                if buffer:
                    merged.append(buffer)
                buffer = line
            else:
                if buffer:
                    buffer = buffer.rstrip() + " " + line.strip()
                else:
                    buffer = line
        if buffer:
            merged.append(buffer)

        for entry in merged:
            entry = normalize_whitespace(entry).strip()
            if len(entry) >= 20:
                entries.append(entry[:2000])

        if not entries:
            single_paragraph = re.split(r"\n\s*\n", block)
            for p in single_paragraph:
                p = normalize_whitespace(p).strip()
                if 20 <= len(p) <= 2000:
                    entries.append(p)
        return entries[:500]

    # --------------------------------------------------------
    # 表格提取
    # --------------------------------------------------------
    def extract_tables(self) -> List[str]:
        """
        提取表格：优先使用 pdfplumber.find_tables，不可用时基于 "Table N" 标记回退。
        """
        if self._closed:
            raise RuntimeError("PDFParser 已关闭")

        tables: List[str] = []

        if pdfplumber is not None:
            try:
                with pdfplumber.open(self.pdf_path) as plumb_doc:
                    for page in plumb_doc.pages:
                        try:
                            detected = page.find_tables() or []
                        except Exception:
                            detected = []
                        for tbl in detected:
                            try:
                                extracted = tbl.extract()
                            except Exception:
                                extracted = None
                            if extracted:
                                rows = []
                                for row in extracted:
                                    cells = [(c or "").strip() for c in row]
                                    rows.append("\t".join(cells))
                                tables.append("\n".join(rows))
            except Exception:
                tables = []

        if tables:
            return tables

        text = self.full_text
        if not text:
            return []
        for m in _TABLE_MARK_RE.finditer(text):
            caption = m.group(0).strip()
            if caption:
                tables.append(caption)
        return tables

    # --------------------------------------------------------
    # 图注提取
    # --------------------------------------------------------
    def extract_figures(self) -> List[str]:
        """基于 'Figure' / 'Fig.' / '图 N' 关键词提取图注。"""
        text = self.full_text
        if not text:
            return []
        seen: set = set()
        figures: List[str] = []
        for m in _FIGURE_CAPTION_RE.finditer(text):
            caption = m.group(0).strip().lstrip("\n").strip()
            caption = normalize_whitespace(caption)
            if not caption or len(caption) < 6:
                continue
            key = re.sub(r"\s+", " ", caption).lower()[:120]
            if key in seen:
                continue
            seen.add(key)
            figures.append(caption[:1000])
        return figures

    # --------------------------------------------------------
    # 元数据
    # --------------------------------------------------------
    def extract_metadata(self) -> PaperMeta:
        """从 PDF 元数据 + 首页标题推断，返回统一的 PaperMeta。"""
        doc_meta = getattr(self._doc, "metadata", None) or {}

        pages = self.extract_text_by_page()
        first_page_text = pages[0].text if pages else ""

        title = (doc_meta.get("title") or "").strip()
        if not title and first_page_text:
            first_lines = [
                ln.strip() for ln in first_page_text.splitlines() if ln.strip()
            ]
            for ln in first_lines[:5]:
                if 6 <= len(ln) <= 200 and not re.search(
                    r"(?i)(arxiv|preprint|doi|http|www\.|vol\.|page|pp\.)", ln
                ):
                    title = ln
                    break

        author = (doc_meta.get("author") or "").strip()
        authors: List[str] = []
        if author:
            authors = [a.strip() for a in re.split(r"[,;]|\band\b|\b与\b", author) if a.strip()]

        year: Optional[int] = None
        for key in ("creationDate", "modDate", "xmp:createdate"):
            val = doc_meta.get(key) or ""
            m = re.search(r"(19|20)\d{2}", str(val))
            if m:
                year = int(m.group(0))
                break
        if not year and first_page_text:
            m = re.search(r"(19|20)\d{2}", first_page_text)
            if m:
                year = int(m.group(0))

        doi: Optional[str] = None
        doi_match = re.search(
            r"(?i)\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", self.full_text
        )
        if doi_match:
            doi = doi_match.group(1).rstrip(".,;:")

        abstract: Optional[str] = None
        try:
            from .text_cleaner import extract_abstract as _ea
            abstract = _ea(self.full_text) or None
        except Exception:
            abstract = None

        # 标题兜底：schemas 中 PaperMeta.title 为必填字段
        if not title:
            base = os.path.splitext(os.path.basename(self.pdf_path))[0]
            title = base or "untitled"

        meta_id = _slugify(title) or "untitled"

        return PaperMeta(
            id=meta_id,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            venue=None,
            pdf_url=self.pdf_path,
            doi=doi,
            arxiv_id=None,
            url=[],
            tags=[],
            citation_count=0,
            source=None,
        )

    # --------------------------------------------------------
    # 关键词
    # --------------------------------------------------------
    def extract_keywords(self, text: Optional[str] = None, top_k: int = 10) -> List[str]:
        """
        简单关键词提取：统计词频，过滤停用词。
        - 若未传入 text，则使用 PDF 全文
        - 仅处理英文单词；中文支持可通过分词库扩展（建议 jieba）
        """
        if text is None:
            text = self.full_text
        if not text:
            return []

        tokens = re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text.lower())
        tokens = [
            t for t in tokens
            if t not in _ENGLISH_STOPWORDS and 2 < len(t) < 40
        ]
        if not tokens:
            return []

        counter = Counter(tokens)
        return [w for w, _ in counter.most_common(top_k)]

    # --------------------------------------------------------
    # 综合解析
    # --------------------------------------------------------
    def parse(self) -> PDFParseResult:
        """执行全部解析，返回统一的 PDFParseResult 结构化结果。"""
        if self._closed:
            raise RuntimeError("PDFParser 已关闭")

        start = time.perf_counter()

        pages = self.extract_text_by_page()
        full_text = self.full_text
        sections = self.extract_sections()
        references = self.extract_references()
        tables = self.extract_tables()
        figures = self.extract_figures()
        metadata = self.extract_metadata()
        keywords = self.extract_keywords(full_text, top_k=20)

        summary = (full_text or "")[:500]

        parse_time = round(time.perf_counter() - start, 4)

        return PDFParseResult(
            pages=pages,
            full_text=full_text,
            summary=summary,
            keywords=keywords,
            sections=sections,
            tables=tables,
            figures=figures,
            references=references,
            metadata=metadata,
            parse_time=parse_time,
        )


# ============================================================
# 便捷函数
# ============================================================

def parse_pdf(pdf_path: str) -> PDFParseResult:
    """便捷函数：打开 PDF、完整解析并关闭文档。"""
    with PDFParser(pdf_path) as parser:
        return parser.parse()
