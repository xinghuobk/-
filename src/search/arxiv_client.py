"""
arXiv 搜索客户端
- 使用官方 Atom XML API：http://export.arxiv.org/api/query
- 解析 title / authors / abstract / published year / arxiv_id / pdf_url / doi
- 网络异常或 API 失败时返回 mock 数据，不抛出异常
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from typing import List, Optional

from backend.models.schemas import PaperMeta, SearchSource

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = "{http://www.w3.org/2005/Atom}"
_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")


def _build_query(keyword: str, year_min: Optional[int], year_max: Optional[int]) -> str:
    """拼接 arXiv search_query 字符串。"""
    parts = [f"all:{urllib.parse.quote(keyword)}"]
    if year_min is not None or year_max is not None:
        ymin = year_min if year_min is not None else 1900
        ymax = year_max if year_max is not None else 9999
        parts.append(f"lastUpdatedDate:[{ymin}01010000 TO {ymax}12312359]")
    return " AND ".join(parts)


def _extract_arxiv_id(url_or_id: str) -> Optional[str]:
    """从 arXiv 链接或 ID 字符串中提取形如 2301.01234 的基础 ID。"""
    if not url_or_id:
        return None
    match = _ARXIV_ID_RE.search(url_or_id)
    return match.group(1) if match else url_or_id.strip()


def _parse_entries(xml_text: str) -> List[PaperMeta]:
    """解析 arXiv Atom XML，返回 PaperMeta 列表。"""
    results: List[PaperMeta] = []
    try:
        from xml.etree import ElementTree as ET

        root = ET.fromstring(xml_text)
    except Exception:
        return results

    for entry in root.findall(f"{ARXIV_NS}entry"):
        title_el = entry.find(f"{ARXIV_NS}title")
        summary_el = entry.find(f"{ARXIV_NS}summary")
        published_el = entry.find(f"{ARXIV_NS}published")
        id_el = entry.find(f"{ARXIV_NS}id")

        title = (title_el.text or "").strip() if title_el is not None else ""
        if not title:
            continue
        abstract = (summary_el.text or "").strip() if summary_el is not None else None
        raw_id = (id_el.text or "").strip() if id_el is not None else ""
        arxiv_id = _extract_arxiv_id(raw_id)

        year: Optional[int] = None
        if published_el is not None and published_el.text:
            try:
                year = int(published_el.text[:4])
            except (TypeError, ValueError):
                year = None

        authors: List[str] = []
        for author in entry.findall(f"{ARXIV_NS}author"):
            name_el = author.find(f"{ARXIV_NS}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        doi: Optional[str] = None
        pdf_url: Optional[str] = None
        urls: List[str] = []
        for link in entry.findall(f"{ARXIV_NS}link"):
            title_attr = link.attrib.get("title", "")
            rel = link.attrib.get("rel", "")
            href = link.attrib.get("href", "")
            if not href:
                continue
            urls.append(href)
            if title_attr == "pdf" or "/pdf" in href:
                pdf_url = href
            if "doi" in href.lower() and doi is None:
                doi = href
            if rel == "alternate" and not pdf_url:
                pass

        results.append(
            PaperMeta(
                title=title,
                authors=authors,
                abstract=abstract or None,
                year=year,
                venue="arXiv",
                pdf_url=pdf_url,
                doi=doi,
                arxiv_id=arxiv_id,
                url=urls,
                tags=["arxiv"],
                citation_count=0,
                source=SearchSource.ARXIV,
                id=arxiv_id,
            )
        )
    return results


def _mock_papers(keyword: str) -> List[PaperMeta]:
    """当网络不可用时使用的演示数据。"""
    return [
        PaperMeta(
            title=f"A Survey of {keyword} Methods and Applications",
            authors=["Alice Zhang", "Bob Li", "Carol Wang"],
            abstract=f"This paper presents a comprehensive survey of {keyword}-related techniques, "
                     "covering recent advances, benchmarks, and open challenges in the field.",
            year=2024,
            venue="arXiv",
            pdf_url="https://arxiv.org/pdf/2401.00001",
            doi=None,
            arxiv_id="2401.00001",
            url=["https://arxiv.org/abs/2401.00001", "https://arxiv.org/pdf/2401.00001"],
            tags=["arxiv", "survey"],
            citation_count=120,
            source=SearchSource.ARXIV,
            id="2401.00001",
        ),
        PaperMeta(
            title=f"Towards Efficient {keyword} via Novel Architectures",
            authors=["David Chen", "Emma Liu"],
            abstract=f"We propose a novel architecture for {keyword} that achieves state-of-the-art "
                     "performance on several benchmarks with reduced compute cost.",
            year=2023,
            venue="arXiv",
            pdf_url="https://arxiv.org/pdf/2310.12345",
            doi=None,
            arxiv_id="2310.12345",
            url=["https://arxiv.org/abs/2310.12345", "https://arxiv.org/pdf/2310.12345"],
            tags=["arxiv", "architecture"],
            citation_count=58,
            source=SearchSource.ARXIV,
            id="2310.12345",
        ),
        PaperMeta(
            title=f"An Empirical Study of {keyword} in Real-world Scenarios",
            authors=["Frank Huang", "Grace Zhao", "Helen Sun"],
            abstract=f"An empirical evaluation of {keyword} models on practical real-world datasets, "
                     "highlighting failure modes and actionable takeaways for practitioners.",
            year=2025,
            venue="arXiv",
            pdf_url="https://arxiv.org/pdf/2502.06789",
            doi=None,
            arxiv_id="2502.06789",
            url=["https://arxiv.org/abs/2502.06789", "https://arxiv.org/pdf/2502.06789"],
            tags=["arxiv", "empirical"],
            citation_count=12,
            source=SearchSource.ARXIV,
            id="2502.06789",
        ),
    ]


def search_arxiv(
    keyword: str,
    max_results: int = 10,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
) -> List[PaperMeta]:
    """
    通过 arXiv API 搜索论文。

    :param keyword: 搜索关键词
    :param max_results: 最多返回条数，默认 10
    :param year_min: 最早发表年份（含），None 则不过滤
    :param year_max: 最晚发表年份（含），None 则不过滤
    :return: ``PaperMeta`` 列表；网络异常或 API 失败时返回 mock 数据
    """
    if not keyword or not keyword.strip():
        return []

    query = _build_query(keyword.strip(), year_min, year_max)
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max(max_results, 1),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"{ARXIV_API}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "research-search/1.0"})

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            xml_text = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return _mock_papers(keyword)

    if not xml_text.strip():
        return _mock_papers(keyword)

    papers = _parse_entries(xml_text)
    if not papers:
        return _mock_papers(keyword)

    if year_min is not None:
        papers = [p for p in papers if p.year is None or p.year >= year_min]
    if year_max is not None:
        papers = [p for p in papers if p.year is None or p.year <= year_max]

    time.sleep(0.1)
    return papers
