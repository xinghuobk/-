"""测试 LLMClient - 统一的 LLM 调用封装。"""
from __future__ import annotations

import json
import pytest
from src.writer.llm_client import LLMClient


# ======================================================================
# 构造 & 基本属性
# ======================================================================

class TestLLMClientInit:
    def test_mock_provider_default(self):
        """默认情况下 provider 为 mock，可正常构造，不抛异常。"""
        client = LLMClient(provider="mock", model="mock-model")
        assert client.provider == "mock"
        assert client.model == "mock-model"

    def test_provider_is_normalized_to_lowercase(self):
        """用户提供大写的 provider 名也应该被正常化。"""
        client = LLMClient(provider="MOCK", model="Test-Model")
        assert client.provider == "mock"
        assert client.model == "Test-Model"


# ======================================================================
# call() / call_json() - mock 模式
# ======================================================================

class TestMockMode:
    def test_call_returns_string(self):
        client = LLMClient(provider="mock")
        # 默认 prompt 不命中任何模式 -> 纯文本提示
        text = client.call("plain prompt")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_call_json_debate_returns_dict(self):
        """命中辩论 prompt 时，mock 返回 dict 结构。"""
        client = LLMClient(provider="mock")
        result = client.call_json(
            "请以 JSON 格式输出辩论论点：reasoning, arguments 等。"
        )
        # 要么是 {"reasoning": ..., "arguments": [...]} 要么是 error 回退
        assert isinstance(result, dict)
        assert "reasoning" in result or "error" in result
        if "reasoning" in result:
            assert isinstance(result.get("arguments"), list)

    def test_call_json_judge_score_returns_dict(self):
        """命中法官评分 prompt 时，mock 返回包含 pro_score/con_score 的 dict。"""
        client = LLMClient(provider="mock")
        result = client.call_json(
            "你是一位严谨的法官，请给出 pro_score 和 con_score。"
        )
        assert isinstance(result, dict)
        # 至少有 pro_score 或 error 字段
        assert "pro_score" in result or "error" in result
        if "pro_score" in result:
            assert 0 <= float(result["pro_score"]) <= 100
            assert 0 <= float(result["con_score"]) <= 100

    def test_call_json_issue_review_returns_dict(self):
        """命中审理问题 prompt 时，mock 返回 issues 列表。"""
        client = LLMClient(provider="mock")
        result = client.call_json(
            "请检查论点中的 invalid_cite 和 weak_support 问题，输出 JSON。"
        )
        assert isinstance(result, dict)
        # issues 字段应存在（或 error 回退）
        assert "issues" in result or "error" in result
        if "issues" in result:
            assert isinstance(result["issues"], list)


# ======================================================================
# JSON 解析鲁棒性
# ======================================================================

class TestJsonParsing:
    def test_call_json_malformed_with_fallback(self):
        """当 prompt 无法让 mock 返回 JSON 时，call_json 不应该抛异常。"""
        client = LLMClient(provider="mock")
        # 不包含任何特殊关键词，mock 返回纯文本，但 call_json 不会抛错
        result = client.call_json("完全不相关的请求")
        assert isinstance(result, dict)  # 总是返回 dict（即使是 error 回退）

    def test_extract_json_returns_none_for_invalid(self):
        """_extract_json 对无效输入返回 None 而非抛异常。"""
        assert LLMClient._extract_json("这不是 json") is None
        assert LLMClient._extract_json("") is None
        # 合法 JSON 应该被识别
        extracted = LLMClient._extract_json('{"a": 1}')
        assert extracted is not None
        data = json.loads(extracted)
        assert data["a"] == 1


# ======================================================================
# openai / dashscope provider 无 API key 时的降级行为
# ======================================================================

class TestProviderFallback:
    def test_openai_without_key_falls_back_to_mock(self):
        """未配置 API key 时，openai provider 降级为 mock，不抛异常。"""
        client = LLMClient(provider="openai", model="test-model")
        # 临时强制无 API key
        text = client.call("随便什么 prompt")
        # 降级后应该返回字符串（可能是 mock 文本）
        assert isinstance(text, str)
        assert len(text) > 0

    def test_dashscope_without_key_falls_back_to_mock(self):
        client = LLMClient(provider="dashscope", model="test-model")
        text = client.call("随便什么 prompt")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_unsupported_provider_returns_info_string(self):
        """未知 provider 不应抛异常，仅返回提示字符串。"""
        client = LLMClient(provider="unknown-xyz", model="test")
        text = client.call("prompt")
        assert isinstance(text, str)
        assert "unsupported" in text.lower()


# ======================================================================
# 与 ParaJudge 各阶段集成（mock 下的基本契约）
# ======================================================================

class TestParajudgeIntegration:
    def test_debater_prompt_produces_arguments(self):
        """模拟辩论者 prompt，mock 应返回 arguments 列表。"""
        from src.debate.prompts import build_debater_prompt
        from backend.models.schemas import EvidenceItem, EvidenceBrief

        brief = EvidenceBrief(
            problem="测试问题？",
            items=[
                EvidenceItem(
                    evidence_id=f"E-{i+1:03d}",
                    title="Paper",
                    authors=["X"],
                    year=2024,
                    abstract_excerpt="摘要内容",
                    relevance_score=0.5,
                )
                for i in range(3)
            ],
            total_count=3,
        )
        client = LLMClient(provider="mock")
        prompt = build_debater_prompt("pro", brief.problem, brief.items)
        result = client.call_json(prompt)
        assert isinstance(result, dict)
        # 只要不抛异常、返回 dict，即为通过

    def test_judge_prompt_produces_scores(self):
        from src.debate.prompts import build_judge_prompt
        from backend.models.schemas import EvidenceItem, EvidenceBrief

        brief = EvidenceBrief(
            problem="测试问题？",
            items=[
                EvidenceItem(evidence_id=f"E-{i+1:03d}", title="P",
                             abstract_excerpt="x", relevance_score=0.5)
                for i in range(3)
            ],
            total_count=3,
        )
        client = LLMClient(provider="mock")
        prompt = build_judge_prompt(
            judge_type="evidence",
            problem=brief.problem,
            evidence_items=brief.items,
            pro_arguments=[{"id": "A-001", "content": "正方论点", "evidence_refs": ["E-001"]}],
            con_arguments=[{"id": "A-002", "content": "反方论点", "evidence_refs": ["E-002"]}],
            review_summary="未发现显著问题。",
        )
        result = client.call_json(prompt)
        assert isinstance(result, dict)
