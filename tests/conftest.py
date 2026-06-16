"""ParaJudge 全系统测试 - 共享 fixtures 与辅助函数。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 确保项目根目录在 sys.path 中，便于 import src.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.models.schemas import (
    EvidenceItem,
    EvidenceBrief,
    DebateArgument,
    DebateTranscript,
    ArgumentIndex,
    IssueItem,
    ReviewReport,
    JudgeScore,
    JudgmentResult,
)

# ======================================================================
# 通用 fixture
# ======================================================================

@pytest.fixture
def fake_paper_list():
    """10 篇模拟论文（供 EvidenceBuilder 测试用）。"""
    titles = [
        "The Economic Potential of Generative AI and the Future of Work",
        "Large Language Models and the Labor Market: Evidence from 10000 Firms",
        "Automation and New Tasks: How Technology Changes Labor Demand",
        "Generative AI at Work: Productivity Effects and Worker Adaptation",
        "The Future of Employment: How Susceptible are Jobs to Computerization?",
        "Human-AI Collaboration: Productivity and Creativity in Knowledge Work",
        "LLM Adoption and Job Displacement: A Three-Year Longitudinal Study",
        "Complementarity in AI: Evidence from Software Development",
        "The Skill Content of Recent Technological Change: An Empirical Exploration",
        "AI and Jobs: The Role of Demand",
    ]
    return titles


@pytest.fixture
def small_brief():
    """构造一个最小可用的 EvidenceBrief（3 条证据）。"""
    items = [
        EvidenceItem(
            evidence_id=f"E-{i+1:03d}",
            title=f"Evidence Title {i+1}",
            authors=["Author A", "Author B"],
            year=2020 + i,
            venue="arXiv",
            abstract_excerpt=f"摘要 {i+1}：关于 LLM 与人类工作关系的一项研究，关键发现包括 ...",
            key_quotes=[],
            relevance_score=round(0.5 + i * 0.1, 2),
            source_type="academic_paper",
            citation_count=100 * (i + 1),
            url=f"https://example.com/paper_{i+1}",
        )
        for i in range(3)
    ]
    return EvidenceBrief(
        problem="LLM 是否会取代人类大部分工作？",
        query_terms=["LLM", "取代", "工作"],
        items=items,
        total_count=len(items),
        build_time_sec=0.01,
    )


@pytest.fixture
def sample_debate_transcript(small_brief):
    """构造一个最小的 DebateTranscript（2 轮 × 2 方 = 4 个论点）。"""
    args = [
        DebateArgument(
            arg_id=f"A-{i+1:03d}",
            content=f"正方论点 {i+1}：这是基于证据的一个明确主张（E-00{i%3+1}）。",
            side="pro",
            speaker="Pro Agent",
            round_index=(i // 2) + 1,
            evidence_refs=[f"E-00{(i%3)+1}"],
            reasoning="选择最直接支持立场的证据。",
            timestamp=float(i + 1),
        )
        for i in range(2)
    ] + [
        DebateArgument(
            arg_id=f"A-{i+3:03d}",
            content=f"反方论点 {i+1}：历史上技术革命总是创造更多岗位（E-00{i%3+1}）。",
            side="con",
            speaker="Con Agent",
            round_index=(i // 2) + 1,
            evidence_refs=[f"E-00{(i%3)+1}"],
            reasoning="使用类比推理，将 LLM 与历史技术革命并列。",
            timestamp=float(i + 3),
        )
        for i in range(2)
    ]

    index = ArgumentIndex(
        arguments=args,
        pro_count=sum(1 for a in args if a.side == "pro"),
        con_count=sum(1 for a in args if a.side == "con"),
    )
    return DebateTranscript(
        problem="LLM 是否会取代人类大部分工作？",
        pro_stance="正方：主张问题的答案为「是」",
        con_stance="反方：主张问题的答案为「否」",
        rounds_total=2,
        arguments=args,
        argument_index=index,
        generation_time=0.5,
    )


@pytest.fixture
def review_with_issues(sample_debate_transcript):
    """构造一个包含典型问题的 ReviewReport。"""
    args = sample_debate_transcript.arguments
    issues = [
        IssueItem(
            issue_id="R-001",
            severity="warning",
            issue_type="no_evidence",
            target_arg_id=args[0].arg_id,
            excerpt=args[0].content[:40],
            description="该论点未引用任何证据，属于纯粹的主张。",
        ),
        IssueItem(
            issue_id="R-002",
            severity="critical",
            issue_type="invalid_cite",
            target_arg_id=args[2].arg_id,
            excerpt=args[2].content[:40],
            description="引用了证据包中不存在的 evidence_id。",
        ),
    ]
    return ReviewReport(
        issues=issues,
        critical_count=1,
        warning_count=1,
        pro_issues=1,
        con_issues=1,
        summary="审理发现 1 个严重问题、1 个警告。",
        generation_time=0.1,
    )


@pytest.fixture
def clean_review_report():
    """构造一个「未发现问题」的 ReviewReport。"""
    return ReviewReport(
        issues=[],
        critical_count=0,
        warning_count=0,
        pro_issues=0,
        con_issues=0,
        summary="未发现显著问题。",
        generation_time=0.1,
    )


@pytest.fixture
def mock_llm():
    """预配置的 mock LLM 客户端（不调用网络）。"""
    from src.writer.llm_client import LLMClient
    return LLMClient(provider="mock", model="mock-model")


__all__ = [
    "small_brief",
    "sample_debate_transcript",
    "review_with_issues",
    "clean_review_report",
    "mock_llm",
    "fake_paper_list",
]
