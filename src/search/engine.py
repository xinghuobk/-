"""
论文搜索统一入口
- 根据 query.sources 分发到 arXiv / Crossref / Semantic Scholar
- 按 citation_count 降序排序，并以 DOI / title 去重
- 计算并返回总耗时（秒）
"""
from __future__ import annotations

import time
from typing import Dict, List

from backend.models.schemas import (
    PaperMeta,
    SearchQuery,
    SearchResult,
    SearchSource,
)
from src.search.arxiv_client import search_arxiv
from src.search.crossref_client import search_crossref
from src.search.semantic_scholar_client import search_semantic_scholar


_DISPATCH: Dict[SearchSource, object] = {
    SearchSource.ARXIV: search_arxiv,
    SearchSource.CROSSREF: search_crossref,
    SearchSource.SEMANTIC_SCHOLAR: search_semantic_scholar,
}


def _call_source(source: SearchSource, query: SearchQuery) -> List[PaperMeta]:
    """调用单个来源的搜索函数；异常时返回空列表。"""
    fn = _DISPATCH.get(source)
    if fn is None:
        return []

    try:
        if source == SearchSource.ARXIV:
            return fn(
                keyword=query.keyword,
                max_results=query.max_results,
                year_min=query.year_min,
                year_max=query.year_max,
            )
        return fn(keyword=query.keyword, max_results=query.max_results)
    except Exception:
        return []


def _normalize_key(paper: PaperMeta) -> str:
    """构造去重 key：优先 DOI，否则按规范化 title。"""
    doi = (paper.doi or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = (paper.title or "").strip().lower()
    title = "".join(ch for ch in title if ch.isalnum())
    return f"title:{title}" if title else f"_unique:{id(paper)}"


def _sort_key(paper: PaperMeta):
    count = paper.citation_count if paper.citation_count is not None else 0
    year = paper.year if paper.year is not None else 0
    return (-count, -year)


def unified_search(query: SearchQuery) -> SearchResult:
    """
    在多个来源搜索论文并合并、排序、去重。

    :param query: 统一搜索查询对象
    :return: ``SearchResult``，包含合并后的论文列表、总耗时
    """
    start = time.perf_counter()

    if not query.sources:
        return SearchResult(
            total_count=0,
            papers=[],
            query=query,
            used_time=round(time.perf_counter() - start, 4),
        )

    collected: List[PaperMeta] = []
    for source in query.sources:
        collected.extend(_call_source(source, query))

    seen: Dict[str, PaperMeta] = {}
    for paper in collected:
        key = _normalize_key(paper)
        existing = seen.get(key)
        if existing is None:
            seen[key] = paper
            continue
        existing_count = existing.citation_count or 0
        new_count = paper.citation_count or 0
        if new_count > existing_count:
            seen[key] = paper

    merged = list(seen.values())
    merged.sort(key=_sort_key)

    used_time = round(time.perf_counter() - start, 4)

    return SearchResult(
        total_count=len(merged),
        papers=merged,
        query=query,
        used_time=used_time,
    )


__all__ = [
    "unified_search",
    "SearchSource",
    "PaperMeta",
    "SearchQuery",
    "SearchResult",
]
