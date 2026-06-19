"""测试 Phase 0 · EvidenceBuilder。

覆盖点：
- _extract_keywords 的启发式抽取
- 完整 build_evidence_brief 流程
- EvidenceItem 的字段完整性
- relevance_score 的范围约束
"""
from __future__ import annotations

import pytest
from backend.models.schemas import EvidenceBrief, EvidenceItem, PaperMeta, SearchQuery, SearchResult
from src.debate.evidence_builder import build_evidence_brief, _extract_keywords


# ======================================================================
# 关键词抽取
# ======================================================================

class TestExtractKeywords:
    def test_basic_cn_en_mixed(self):
        """中英文混合问题能抽取出关键词。"""
        terms = _extract_keywords("LLM 是否会取代人类大部分工作？")
        assert isinstance(terms, list)
        # 至少抽出若干个（> 0）
        assert len(terms) > 0
        # 所有返回值应为字符串
        assert all(isinstance(t, str) for t in terms)

    def test_empty_input(self):
        assert _extract_keywords("") == []
        assert _extract_keywords("   ") == []

    def test_max_terms(self):
        """返回结果不应超过 max_terms 默认值（5）。"""
        long = " ".join(
            ["longword" + str(i) for i in range(20)]
        )
        terms = _extract_keywords(long)
        assert len(terms) <= 5

    def test_stops_words_filtered(self):
        """停用词不应出现在结果中。"""
        terms = _extract_keywords("the is are 什么吗的是的是什么 the a an is")
        # 不应该包含纯停用词
        for t in terms:
            assert t not in {"the", "is", "are", "a", "an", "什么", "吗", "的"}

    def test_cn_keywords(self):
        """中文问题至少抽取出 2 个词。"""
        terms = _extract_keywords("量子计算 对 密码学 的 影响 与 未来 展望")
        assert len(terms) >= 2


# ======================================================================
# 主流程（依赖网络的部分使用 mock/unittest）
# ======================================================================

class TestBuildEvidenceBrief:
    def test_returns_evidence_brief(self, monkeypatch):
        """确保在 mock 检索引擎下能返回 EvidenceBrief。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            papers = []
            for i in range(min(query.max_results, 5)):
                papers.append(PaperMeta(
                    title=f"Paper {i + 1}: Study on LLM and Jobs",
                    authors=["Author One", "Author Two"],
                    abstract=(
                        f"Abstract {i + 1}: 这篇论文研究了大型语言模型对工作岗位的影响，"
                        f"包含来自 {100 + i} 家企业的实证数据。"
                    ),
                    year=2020 + i,
                    venue="arXiv",
                    url=[f"https://example.com/{i}"],
                    citation_count=(i + 1) * 10,
                ))
            return SearchResult(total_count=len(papers), papers=papers, query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        brief = build_evidence_brief("LLM 是否会取代人类大部分工作？", max_papers=5)
        assert isinstance(brief, EvidenceBrief)
        assert brief.total_count > 0
        assert len(brief.items) == brief.total_count

    def test_relevance_scores_in_valid_range(self, monkeypatch):
        """relevance_score 必须在 [0, 1] 之间。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            papers = [
                PaperMeta(title=f"Paper {i}", abstract="关于 LLM 与 工作 的研究",
                          year=2024, venue="arXiv", citation_count=50,
                          url=["https://example.com"])
                for i in range(query.max_results)
            ]
            return SearchResult(total_count=len(papers), papers=papers, query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        brief = build_evidence_brief("LLM 是否会取代人类大部分工作？", max_papers=5)
        for item in brief.items:
            assert 0.0 <= item.relevance_score <= 1.0, (
                f"{item.evidence_id} relevance_score={item.relevance_score} 超出范围"
            )

    def test_evidence_ids_have_expected_format(self, monkeypatch):
        """evidence_id 应以 E-xxx 格式出现。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            papers = [
                PaperMeta(title=f"P{i}", abstract="摘要", year=2024, venue="arXiv",
                          url=[f"https://example.com/{i}"], citation_count=10)
                for i in range(3)
            ]
            return SearchResult(total_count=len(papers), papers=papers, query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        brief = build_evidence_brief("测试问题", max_papers=3)
        for item in brief.items:
            assert item.evidence_id.startswith("E-")
            assert int(item.evidence_id.split("-")[1]) > 0

    def test_query_terms_populated(self, monkeypatch):
        """如果抽取到关键词，query_terms 应有内容。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            return SearchResult(total_count=1, papers=[
                PaperMeta(title="P", abstract="摘要", year=2024, venue="arXiv",
                          url=["https://example.com"], citation_count=0)
            ], query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        brief = build_evidence_brief("LLM 是否会取代人类大部分工作？", max_papers=1)
        # query_terms 要么有关键词，要么回退到问题全文（至少有 1 项）
        assert len(brief.query_terms) >= 1

    def test_empty_search_results(self, monkeypatch):
        """检索返回 0 篇论文时，不应抛异常，返回空的 EvidenceBrief。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            return SearchResult(total_count=0, papers=[], query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        brief = build_evidence_brief("无结果问题", max_papers=5)
        assert brief.total_count == 0
        assert brief.items == []

    def test_respects_max_papers(self, monkeypatch):
        """实际返回条数不应超过 max_papers。"""
        import src.debate.evidence_builder as builder_module

        def fake_search(query: SearchQuery) -> SearchResult:
            papers = [
                PaperMeta(title=f"P{i}", abstract="摘要", year=2024, venue="arXiv",
                          url=["https://example.com"], citation_count=10)
                for i in range(20)
            ]
            return SearchResult(total_count=len(papers), papers=papers, query=query, used_time=0.01)

        monkeypatch.setattr(builder_module, "unified_search", fake_search)

        for max_p in [1, 3, 5]:
            brief = build_evidence_brief("问题", max_papers=max_p)
            assert brief.total_count <= max_p
            assert len(brief.items) <= max_p
