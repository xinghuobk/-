"""
Semantic Scholar 搜索客户端
- 使用官方 Graph API：https://api.semanticscholar.org/graph/v1/paper/search
- 提取 title, authors, abstract, year, venue, citationCount, paperId
- 网络异常或 API 失败时返回空列表，不抛出异常
"""
from __future__ import annotations

from typing import List, Optional

from backend.models.schemas import PaperMeta, SearchSource

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
_DEFAULT_FIELDS = "paperId,title,authors,abstract,year,venue,citationCount,externalIds,url"


def search_semantic_scholar(keyword: str, max_results: int = 10) -> List[PaperMeta]:
    """
    通过 Semantic Scholar Graph API 搜索论文。

    :param keyword: 搜索关键词
    :param max_results: 最多返回条数，默认 10
    :return: ``PaperMeta`` 列表；网络异常或 API 失败时返回空列表
    """
    if not keyword or not keyword.strip():
        return []

    import httpx

    params = {
        "query": keyword.strip(),
        "limit": max(max_results, 1),
        "fields": _DEFAULT_FIELDS,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                SEMANTIC_SCHOLAR_API,
                params=params,
                follow_redirects=True,
                headers={"User-Agent": "research-search/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return []

    data = payload.get("data") or []
    results: List[PaperMeta] = []

    for item in data:
        title = (item.get("title") or "").strip()
        if not title:
            continue

        authors_raw = item.get("authors") or []
        authors: List[str] = []
        for a in authors_raw:
            name = (a.get("name") or "").strip()
            if name:
                authors.append(name)

        abstract: Optional[str] = (item.get("abstract") or "").strip() or None

        year = item.get("year")
        if isinstance(year, str):
            try:
                year = int(year)
            except ValueError:
                year = None

        venue = (item.get("venue") or "").strip() or None
        citation_count: Optional[int] = None
        raw_citation = item.get("citationCount")
        if isinstance(raw_citation, int):
            citation_count = raw_citation
        elif isinstance(raw_citation, str):
            try:
                citation_count = int(raw_citation)
            except ValueError:
                citation_count = None

        paper_id = item.get("paperId")
        item_url = item.get("url")
        external_ids = item.get("externalIds") or {}
        doi = external_ids.get("DOI") if isinstance(external_ids, dict) else None
        arxiv_id = external_ids.get("ArXiv") if isinstance(external_ids, dict) else None
        pdf_url = f"https://doi.org/{doi}" if doi else item_url

        urls: List[str] = []
        if item_url:
            urls.append(item_url)
        if pdf_url and pdf_url != item_url:
            urls.append(pdf_url)

        results.append(
            PaperMeta(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                venue=venue,
                pdf_url=pdf_url,
                doi=doi,
                arxiv_id=arxiv_id,
                url=urls,
                tags=["semantic_scholar"],
                citation_count=citation_count,
                source=SearchSource.SEMANTIC_SCHOLAR,
                id=paper_id,
            )
        )

    return results
