"""ParaJudge 辩论相关模块（Phase 0 + Phase 1）。

- evidence_builder.py: 证据构建器（从问题 -> EvidenceBrief）
- simple_debate.py: 极简辩论引擎（正反方轮流发言）
- prompts.py: LLM Prompt 模板集合
"""
from .evidence_builder import build_evidence_brief
from .simple_debate import SimpleDebate
from .prompts import build_debater_prompt, build_review_prompt, build_judge_prompt

__all__ = [
    "build_evidence_brief",
    "SimpleDebate",
    "build_debater_prompt",
    "build_review_prompt",
    "build_judge_prompt",
]
