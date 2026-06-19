"""
Crossref 搜索客户端
- 使用官方 REST API：https://api.crossref.org/works
- 使用 httpx 发起请求，解析 JSON 返回
- 网络异常或 API 失败时返回空列表，不抛出异常
"""
from __future__ import annotations

from typing import List, Optional

from backend.models.schemas import PaperMeta, SearchSource

CROSSREF_API = "https://api.crossref.org/works"


def _normalize_name(author: dict) -> str:
    given = (author.get("given") or "").strip()
    family = (author.get("family") or "").strip()
    if given and family:
        return f"{given} {family}"
    return family or given or ""


def search_crossref(keyword: str, max_results: int = 10) -> List[PaperMeta]:
    """
    通过 Crossref API 搜索论文元数据。

    :param keyword: 搜索关键词
    :param max_results: 最多返回条数，默认 10
    :return: ``PaperMeta`` 列表；网络异常或 API 失败时返回空列表
    """
    if not keyword or not keyword.strip():
        return []

    import httpx

    params = {
        "query": keyword.strip(),
        "rows": max(max_results, 1),
        "select": "title,author,abstract,issued,published-print,published-online,container-title,DOI,is-referenced-by-count,URL",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(CROSSREF_API, params=params, follow_redirects=True)
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return []

    items = (payload.get("message") or {}).get("items") or []
    results: List[PaperMeta] = []

    for item in items:
        title_list = item.get("title") or []
        title = (title_list[0] if title_list else "").strip()
        if not title:
            continue

        authors_raw = item.get("author") or []
        authors: List[str] = []
        for a in authors_raw:
            name = _normalize_name(a)
            if name:
                authors.append(name)

        abstract: Optional[str] = None
        raw_abstract = (item.get("abstract") or "").strip()
        if raw_abstract and not raw_abstract.startswith("<jats:"):
            abstract = raw_abstract

        year: Optional[int] = None
        for date_field in ("issued", "published-print", "published-online"):
            date_obj = item.get(date_field) or {}
            parts = (date_obj.get("date-parts") or [[]])[0]
            if parts and parts[0]:
                try:
                    year = int(parts[0])
                    break
                except (TypeError, ValueError):
                    continue

        container = item.get("container-title") or []
        venue = container[0].strip() if container else None

        citation_count: Optional[int] = None
        raw_count = item.get("is-referenced-by-count")
        if isinstance(raw_count, int):
            citation_count = raw_count
        elif isinstance(raw_count, str):
            try:
                citation_count = int(raw_count)
            except ValueError:
                citation_count = None

        doi = item.get("DOI")
        item_url = item.get("URL")
        pdf_url = f"https://doi.org/{doi}" if doi else None
        urls: List[str] = []
        if item_url:
            urls.append(item_url)
        if pdf_url:
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
                url=urls,
                tags=["crossref"],
                citation_count=citation_count,
                source=SearchSource.CROSSREF,
                id=doi,
            )
        )

    return results
