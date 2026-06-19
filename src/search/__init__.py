"""
论文搜索模块包导出
- 提供 arXiv / Crossref / Semantic Scholar 统一搜索入口
"""
from .arxiv_client import search_arxiv
from .crossref_client import search_crossref
from .semantic_scholar_client import search_semantic_scholar
from .engine import unified_search, SearchSource, PaperMeta, SearchQuery, SearchResult

__all__ = [
    "search_arxiv",
    "search_crossref",
    "search_semantic_scholar",
    "unified_search",
    "SearchSource",
    "PaperMeta",
    "SearchQuery",
    "SearchResult",
]
