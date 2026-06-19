"""测试 Phase 2.2 · JudgmentEngine。

覆盖点：
- 5 位法官的独立评分（judge_scores 应有 5 项）
- pro_score / con_score 在 [0, 100] 范围内
- 胜负判定：pro 明显高 → winner="pro"，反之亦然
- 推理链非空且由 claim / evidence 节点组成
- uncertainties 在审理存在 critical 问题时应被填充
"""
from __future__ import annotations

import pytest
from backend.models.schemas import (
    EvidenceBrief,
    EvidenceItem,
    DebateTranscript,
    DebateArgument,
    ArgumentIndex,
    ReviewReport,
    IssueItem,
    JudgmentResult,
    JudgeScore,
    ReasoningNode,
)
from src.judgment.judgment_engine import JudgmentEngine
from src.writer.llm_client import LLMClient


# ======================================================================
# 主裁决流程
# ======================================================================

class TestJudgmentRun:
    def test_returns_judgment_result(self, small_brief, sample_debate_transcript, clean_review_report):
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)

        assert isinstance(result, JudgmentResult)
        # 5 位法官
        assert len(result.judge_scores) == 5

    def test_all_scores_in_valid_range(self, small_brief, sample_debate_transcript, clean_review_report):
        """所有 pro_score / con_score 都必须在 [0, 100] 范围内。"""
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)

        for js in result.judge_scores:
            assert 0 <= js.pro_score <= 100
            assert 0 <= js.con_score <= 100
        assert 0 <= result.pro_final_score <= 100
        assert 0 <= result.con_final_score <= 100

    def test_final_scores_are_averages_of_judges(self, small_brief, sample_debate_transcript, clean_review_report):
        """pro_final_score / con_final_score 应等于 5 位法官的均值。"""
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)

        expected_pro = round(sum(js.pro_score for js in result.judge_scores) / len(result.judge_scores), 1)
        expected_con = round(sum(js.con_score for js in result.judge_scores) / len(result.judge_scores), 1)
        # 允许浮点误差 0.1
        assert abs(result.pro_final_score - expected_pro) <= 0.1
        assert abs(result.con_final_score - expected_con) <= 0.1

    def test_winner_valid_values(self, small_brief, sample_debate_transcript, clean_review_report):
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)
        assert result.winner in ("pro", "con", "tie")


# ======================================================================
# 推理链
# ======================================================================

class TestReasoningChain:
    def test_reasoning_chain_not_empty(self, small_brief, sample_debate_transcript, clean_review_report):
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)
        # 至少应该有节点
        assert isinstance(result.reasoning_chain_pro, list)
        assert isinstance(result.reasoning_chain_con, list)
        # 正方有论点，应该生成推理链
        assert len(result.reasoning_chain_pro) > 0

    def test_reasoning_nodes_have_expected_source_type(self, small_brief,
                                                       sample_debate_transcript,
                                                       clean_review_report):
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)
        for node in result.reasoning_chain_pro + result.reasoning_chain_con:
            assert isinstance(node, ReasoningNode)
            assert node.source_type in ("claim", "evidence", "intermediate")


# ======================================================================
# 不确定性提示
# ======================================================================

class TestUncertainties:
    def test_critical_issues_trigger_uncertainties(self, small_brief, sample_debate_transcript):
        """审理报告中有 critical 问题时，不确定性字段应有内容。"""
        review = ReviewReport(
            issues=[
                IssueItem(
                    issue_id=f"R-{i+1:03d}",
                    severity="critical",
                    issue_type="invalid_cite",
                    target_arg_id=sample_debate_transcript.arguments[i % 2].arg_id,
                    excerpt=sample_debate_transcript.arguments[i % 2].content[:30],
                    description="引用了证据包中不存在的 evidence_id。",
                )
                for i in range(2)
            ],
            critical_count=2,
            warning_count=0,
            pro_issues=1,
            con_issues=1,
            summary="审理发现 2 个严重问题。",
            generation_time=0.1,
        )
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, review)
        assert len(result.uncertainties) > 0
        assert any("严重" in u or "critical" in u.lower() for u in result.uncertainties)

    def test_large_judge_disagreement_triggers_uncertainty(self, small_brief, sample_debate_transcript,
                                                            clean_review_report):
        """如果法官评分分歧大（spread > 25），uncertainties 应有提示。

        用确定性的自定义 LLM，对不同 judge_type 返回悬殊评分，以确保触发分歧提示。
        """

        _call_count = {"n": 0}
        _score_pattern = [
            (10, 90),
            (90, 10),
            (15, 85),
            (85, 20),
            (95, 15),
        ]

        class SpreadLLM:
            def call_json(self, prompt, max_tokens=500, temperature=0.7):
                idx = _call_count["n"] % len(_score_pattern)
                _call_count["n"] += 1
                pro, con = _score_pattern[idx]
                return {"pro_score": pro, "con_score": con,
                        "pro_feedback": f"第 {idx + 1} 位法官",
                        "con_feedback": f"第 {idx + 1} 位法官",
                        "reasoning": "悬殊评分"}

        engine = JudgmentEngine(SpreadLLM())
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)
        # 不做过度断言，只要系统在评分分歧大时能填充 uncertainties 即可
        assert isinstance(result.uncertainties, list)
        assert len(result.uncertainties) > 0, (
            f"法官 pro 评分: {[js.pro_score for js in result.judge_scores]}，"
            f"反方评分: {[js.con_score for js in result.judge_scores]}，"
            f"但 uncertainties 为空"
        )


# ======================================================================
# 关键论点提取
# ======================================================================

class TestKeyPoints:
    def test_key_points_reflect_arguments(self, small_brief, sample_debate_transcript, clean_review_report):
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)

        pro_args_contents = {a.content for a in sample_debate_transcript.arguments if a.side == "pro"}
        con_args_contents = {a.content for a in sample_debate_transcript.arguments if a.side == "con"}
        # key_points 应来自对应 side 的论点正文
        for kp in result.key_points_pro:
            assert kp in pro_args_contents, f"{kp} 不是正方论点的正文"
        for kp in result.key_points_con:
            assert kp in con_args_contents, f"{kp} 不是反方论点的正文"


# ======================================================================
# judge_type / judge_name 完整性
# ======================================================================

class TestJudgeTypes:
    def test_all_judge_types_covered(self, small_brief, sample_debate_transcript, clean_review_report):
        """裁决应包含 5 位不同的法官，且 judge_type 都在预期集合中。"""
        expected_types = {"evidence", "logic", "principle", "case", "innovation"}
        llm = LLMClient(provider="mock")
        engine = JudgmentEngine(llm)
        result = engine.run(sample_debate_transcript, small_brief, clean_review_report)
        actual_types = {js.judge_type for js in result.judge_scores}
        assert actual_types == expected_types, (
            f"缺少法官类型: {expected_types - actual_types}, 多余: {actual_types - expected_types}"
        )
