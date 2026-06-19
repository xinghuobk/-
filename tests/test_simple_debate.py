"""测试 Phase 1 · SimpleDebate。

覆盖点：
- 固定轮次：每一轮次都有正反方各至少一个论点
- ArgumentIndex 的 pro_count / con_count 是否准确
- LLM mock 输出的论点都有合法的 side
- 回退逻辑：当 LLM 完全失败时系统仍能生成论点
"""
from __future__ import annotations

import pytest
from backend.models.schemas import DebateArgument, DebateTranscript, ArgumentIndex
from src.debate.simple_debate import SimpleDebate
from src.writer.llm_client import LLMClient


# ======================================================================
# 主流程（使用 mock LLM）
# ======================================================================

class TestSimpleDebateRun:
    def test_3_rounds_produces_at_least_6_arguments(self, small_brief):
        """3 轮至少生成 6 个论点（每轮正方 + 反方各一个）。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=3)
        transcript = debater.run("LLM 是否会取代人类大部分工作？", small_brief)

        assert isinstance(transcript, DebateTranscript)
        assert transcript.rounds_total == 3
        # 至少每轮产生 1 pro + 1 con，共 >= 6 个
        assert len(transcript.arguments) >= 6

    def test_argument_index_counts_consistent(self, small_brief):
        """ArgumentIndex 的 pro_count/con_count 必须与论点列表一致。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=2)
        transcript = debater.run("LLM 是否会取代人类大部分工作？", small_brief)

        expected_pro = sum(1 for a in transcript.arguments if a.side == "pro")
        expected_con = sum(1 for a in transcript.arguments if a.side == "con")

        assert transcript.argument_index.pro_count == expected_pro
        assert transcript.argument_index.con_count == expected_con
        assert expected_pro + expected_con == len(transcript.arguments)

    def test_argument_ids_are_unique(self, small_brief):
        """所有论点的 arg_id 必须互不相同。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=3)
        transcript = debater.run("LLM 是否会取代人类大部分工作？", small_brief)

        ids = [a.arg_id for a in transcript.arguments]
        assert len(ids) == len(set(ids)), "存在重复的 arg_id"

    def test_each_argument_has_valid_side(self, small_brief):
        """每个论点的 side 必须为 'pro' 或 'con'。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=2)
        transcript = debater.run("问题", small_brief)

        for arg in transcript.arguments:
            assert arg.side in ("pro", "con"), f"非法的 side 值: {arg.side}"

    def test_argument_index_helper_methods(self, small_brief):
        """ArgumentIndex.by_side / by_evidence 能正确过滤。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=2)
        transcript = debater.run("问题", small_brief)

        index = transcript.argument_index
        pro_args = index.by_side("pro")
        con_args = index.by_side("con")
        assert len(pro_args) == index.pro_count
        assert len(con_args) == index.con_count
        assert all(a.side == "pro" for a in pro_args)
        assert all(a.side == "con" for a in con_args)


# ======================================================================
# 异常 & 回退场景
# ======================================================================

class TestDebateFallback:
    def test_llm_returns_unparseable_text(self, small_brief, monkeypatch):
        """当 LLM 返回无法解析的内容时，系统应回退到默认论点，不应抛异常。"""
        class UnparseableLLM:
            def call_json(self, prompt, max_tokens=500, temperature=0.7):
                return "not a dict at all"

        debater = SimpleDebate(UnparseableLLM(), rounds=1)
        # 不抛异常
        transcript = debater.run("问题", small_brief)
        # 至少要有论点（来自 fallback 路径）
        assert len(transcript.arguments) >= 2
        # 正反方都应有
        assert transcript.argument_index.pro_count >= 1
        assert transcript.argument_index.con_count >= 1

    def test_llm_returns_missing_arguments_key(self, small_brief, monkeypatch):
        """LLM 返回 dict 但缺少 arguments 字段时，应正常回退。"""
        class PartialLLM:
            def call_json(self, prompt, max_tokens=500, temperature=0.7):
                return {"reasoning": "some text"}  # 缺少 arguments 字段

        debater = SimpleDebate(PartialLLM(), rounds=1)
        transcript = debater.run("问题", small_brief)
        # fallback 路径应确保至少产生 2 个论点
        assert len(transcript.arguments) >= 2

    def test_rounds_zero_not_allowed(self, small_brief):
        """SimpleDebate 至少要有 1 轮。"""
        llm = LLMClient(provider="mock")
        # rounds=0 应该被钳制到 1
        debater = SimpleDebate(llm, rounds=0)
        transcript = debater.run("问题", small_brief)
        assert transcript.rounds_total >= 1

    def test_rounds_negative_not_allowed(self, small_brief):
        """负数轮次应被钳制到 1。"""
        llm = LLMClient(provider="mock")
        debater = SimpleDebate(llm, rounds=-5)
        transcript = debater.run("问题", small_brief)
        assert transcript.rounds_total >= 1


# ======================================================================
# Prompt 模板单独测试
# ======================================================================

class TestPrompts:
    def test_debater_prompt_contains_expected_keywords(self, small_brief):
        from src.debate.prompts import build_debater_prompt
        prompt = build_debater_prompt("pro", "LLM 是否会取代人类工作？", small_brief.items)
        assert "证据包" in prompt
        assert "JSON" in prompt
        assert "reasoning" in prompt or "arguments" in prompt

    def test_review_prompt_structure(self, small_brief):
        from src.debate.prompts import build_review_prompt
        prompt = build_review_prompt(
            "问题？",
            small_brief.items,
            arguments_text="[A-001] 论点内容 [引用: E-001]",
        )
        assert "invalid_cite" in prompt or "evidence" in prompt.lower()
        assert "JSON" in prompt

    def test_judge_prompt_variants_differ(self, small_brief):
        """不同类型的法官 prompt 应当不同。"""
        from src.debate.prompts import build_judge_prompt

        pro_args = [{"id": "A-001", "content": "正方论点", "evidence_refs": ["E-001"]}]
        con_args = [{"id": "A-002", "content": "反方论点", "evidence_refs": ["E-002"]}]

        prompts = []
        for jtype in ("evidence", "logic", "principle", "case", "innovation"):
            prompts.append(build_judge_prompt(
                jtype, "问题？", small_brief.items, pro_args, con_args, ""
            ))
        # 所有 prompt 非空，且应当互有不同（至少存在差异）
        for p in prompts:
            assert len(p) > 0
        # 取前字符的集合应不完全相同
        unique_starts = {p[:60] for p in prompts}
        assert len(unique_starts) >= 2, "不同法官的 prompt 几乎相同"
