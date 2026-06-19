"""Phase 0 · 证据构建器（EvidenceBuilder）。

给定一个问题：
  1. 抽取关键词
  2. 调用统一论文检索入口（arXiv + Crossref + Semantic Scholar）
  3. 将检索结果包装为 EvidenceBrief（结构化证据包）

设计原则：
- 不使用 LLM（纯程序逻辑），保证可预测性与速度
- 不修改原始 PaperMeta，仅做映射与裁剪
- 为每条证据提供一个启发式相关性评分（后续阶段可使用）
"""
from __future__ import annotations

import time
import re
from typing import List, Optional

from backend.models.schemas import (
    EvidenceBrief,
    EvidenceItem,
    PaperMeta,
    SearchQuery,
    SearchSource,
    SearchResult,
)
from src.search.engine import unified_search


# ============================================================
# 主入口
# ============================================================

def build_evidence_brief(
    problem: str,
    max_papers: int = 20,
    sources: Optional[List[SearchSource]] = None,
) -> EvidenceBrief:
    """构建证据摘要包。"""
    t0 = time.perf_counter()

    if sources is None:
        sources = [SearchSource.ARXIV, SearchSource.CROSSREF, SearchSource.SEMANTIC_SCHOLAR]

    query_terms = _extract_keywords(problem)

    # 尝试用抽取的关键词搜索；如果失败，用原问题全文
    keyword = " ".join(query_terms) if query_terms else problem
    # 如果关键词太短，改用原问题的前 80 字
    if len(keyword.strip()) < 4:
        keyword = problem[:80]

    query = SearchQuery(
        keyword=keyword,
        max_results=max(max_papers, 5),
        sources=sources,
    )
    search_result: SearchResult = unified_search(query)

    items: List[EvidenceItem] = []
    for idx, paper in enumerate(search_result.papers[:max_papers]):
        item = _paper_to_item(paper, idx, keyword)
        items.append(item)

    return EvidenceBrief(
        problem=problem,
        query_terms=query_terms or [keyword],
        items=items,
        total_count=len(items),
        build_time_sec=round(time.perf_counter() - t0, 3),
    )


# ============================================================
# 关键词提取（简单启发式）
# ============================================================

# 中文停用词 + 英文停用词的精简集合
_STOPWORDS = {
    # 中文常用虚词/代词
    "的", "了", "是", "在", "和", "与", "或", "而", "但", "就",
    "这", "那", "什么", "吗", "呢", "吧", "啊", "会", "能", "可以",
    "应该", "是否", "我们", "你", "我", "他", "她", "它", "它们",
    "一个", "一些", "很多", "大部分", "可能", "也许",
    # 英文
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "and", "or", "but", "of", "in", "on", "at", "to", "for", "with",
    "about", "against", "between", "into", "through", "during",
    "this", "that", "these", "those", "it", "its", "as", "by",
    "what", "which", "who", "whom", "whose", "do", "does", "did",
    "will", "would", "should", "could", "can", "may", "might",
    "has", "have", "had", "having",
}

# 保留长度 >= 2 的中文词，英文长度 >= 3
_MIN_CHINESE_LEN = 2
_MIN_ENGLISH_LEN = 3


def _extract_keywords(text: str, max_terms: int = 5) -> List[str]:
    """从问题文本中抽取关键词。

    策略：
      1. 将文本按标点/空白分段
      2. 对英文段：tokenize，过滤停用词 + 短词
      3. 对中文段：保留长度 >= 2 的词（不做分词以避免依赖 jieba）
      4. 按字符长度降序取前 max_terms 个
    """
    if not text or not text.strip():
        return []

    # 拆分：保留英文词和中文词
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+|[\u4e00-\u9fff]{2,}", text)
    tokens = [t.strip().lower() for t in tokens if t.strip()]

    # 过滤停用词和过短的词
    filtered = []
    for t in tokens:
        if t in _STOPWORDS:
            continue
        # 判断是否全为中文 / 全为英文
        if all("\u4e00" <= ch <= "\u9fff" for ch in t):
            if len(t) >= _MIN_CHINESE_LEN:
                filtered.append(t)
        else:  # 英文或混合
            if len(t) >= _MIN_ENGLISH_LEN:
                filtered.append(t)

    # 去重（保持首次出现的顺序）
    seen = set()
    unique = []
    for t in filtered:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    # 按长度降序（长词往往更具体），但保留前若干个
    unique.sort(key=lambda s: -len(s))
    return unique[:max_terms]


# ============================================================
# PaperMeta -> EvidenceItem
# ============================================================

def _paper_to_item(paper: PaperMeta, index: int, query_keyword: str) -> EvidenceItem:
    """将检索返回的 PaperMeta 映射为 EvidenceItem。"""
    abstract = paper.abstract or ""
    excerpt = abstract.strip()
    if len(excerpt) > 400:
        excerpt = excerpt[:400] + "…"

    # 启发式相关性评分：
    #   - 基础：引用数信号（citation_count / (citation_count + 100)）
    #   - 标题/摘要是否含 query 关键词作为加分
    #   - 最后按 1 / (index + 1) 衰减（检索引擎已排序，优先保留前序结果）
    citations = paper.citation_count if paper.citation_count is not None else 0
    citation_signal = citations / (citations + 100)  # 0 ~ 0.5

    title = (paper.title or "").lower()
    kw_lower = query_keyword.lower()
    # 关键词是否出现在标题/摘要中
    keyword_hit = 0.0
    if kw_lower and kw_lower in title:
        keyword_hit += 0.3
    if kw_lower and kw_lower in abstract.lower():
        keyword_hit += 0.2

    rank_signal = 1.0 / (index + 1)  # 1.0, 0.5, 0.33, ...
    # 归一化并加权
    score = 0.35 * citation_signal + 0.25 * keyword_hit + 0.4 * min(rank_signal, 1.0)
    score = max(0.0, min(1.0, score))

    # 论文链接
    url = None
    if paper.url:
        if isinstance(paper.url, list):
            url = paper.url[0] if paper.url else None
        else:
            url = paper.url

    authors = paper.authors or []
    if isinstance(authors, str):
        authors = [authors]

    return EvidenceItem(
        evidence_id=f"E-{index + 1:03d}",
        title=paper.title or "Untitled Paper",
        authors=list(authors[:5]),  # 最多保留 5 位作者
        year=paper.year,
        venue=paper.venue,
        abstract_excerpt=excerpt or "[No abstract available]",
        key_quotes=[],  # MVP 不使用 LLM 抽取关键句
        relevance_score=round(score, 3),
        source_type="academic_paper",
        citation_count=paper.citation_count,
        url=url or (paper.doi if paper.doi else None),
    )


__all__ = ["build_evidence_brief"]
