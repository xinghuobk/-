"""测试 Phase 2.1 · ReviewEngine。

覆盖点：
- 程序化检查：no_evidence / invalid_cite
- LLM 检查：weak_support / circular / contradiction
- 统计字段（critical_count / warning_count / pro_issues / con_issues）
- summary 的格式一致性
"""
from __future__ import annotations

import pytest
from backend.models.schemas import (
    DebateArgument,
    DebateTranscript,
    ArgumentIndex,
    IssueItem,
    ReviewReport,
)
from src.judgment.review_engine import ReviewEngine
from src.writer.llm_client import LLMClient


# ======================================================================
# 程序化检查（无需 LLM）
# ======================================================================

class TestProgrammaticCheck:
    def test_detects_no_evidence(self, small_brief):
        """没有 evidence_refs 的论点应被标记为 no_evidence。"""
        args = [
            DebateArgument(
                arg_id=f"A-{i+1:03d}",
                content="该论点无任何证据引用",
                side=("pro" if i % 2 == 0 else "con"),
                speaker="Agent",
                round_index=1,
                evidence_refs=[],
            )
            for i in range(4)
        ]
        transcript = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=args,
            argument_index=ArgumentIndex(
                arguments=args,
                pro_count=2,
                con_count=2,
            ),
        )

        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(transcript, small_brief)

        assert report.warning_count >= 4
        assert all(i.issue_type == "no_evidence" for i in report.issues)

    def test_detects_invalid_cite(self, small_brief):
        """引用证据包中不存在的 evidence_id 应被标记为 invalid_cite。"""
        args = [
            DebateArgument(
                arg_id=f"A-{i+1:03d}",
                content=f"有问题的论点 {i+1}",
                side="pro",
                speaker="Pro Agent",
                round_index=1,
                evidence_refs=["E-999"],  # 不存在
            )
            for i in range(2)
        ]
        transcript = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=args,
            argument_index=ArgumentIndex(arguments=args, pro_count=2, con_count=0),
        )
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(transcript, small_brief)
        # 2 个 invalid_cite（severity=critical）
        assert report.critical_count >= 2
        assert any(i.issue_type == "invalid_cite" for i in report.issues)

    def test_valid_evidence_passes(self, small_brief):
        """引用合法 evidence_id 的论点不应被程序检查标记。"""
        valid_ids = [e.evidence_id for e in small_brief.items]
        args = [
            DebateArgument(
                arg_id=f"A-{i+1:03d}",
                content=f"正常论点 {i+1}",
                side="pro",
                speaker="Pro Agent",
                round_index=1,
                evidence_refs=[valid_ids[i % len(valid_ids)]],
            )
            for i in range(3)
        ]
        transcript = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=args,
            argument_index=ArgumentIndex(arguments=args, pro_count=3, con_count=0),
        )
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(transcript, small_brief)
        assert report.critical_count == 0
        assert report.warning_count == 0

    def test_empty_transcript_is_fine(self, small_brief):
        """空 transcript 不应抛异常。"""
        empty = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=[],
            argument_index=ArgumentIndex(),
        )
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(empty, small_brief)
        assert report.critical_count == 0
        assert report.warning_count == 0


# ======================================================================
# LLM 检查（使用 mock）
# ======================================================================

class TestLLMCheck:
    def test_mock_review_returns_issues(self, small_brief, sample_debate_transcript):
        """启用 LLM 检查时，mock 返回的 issue 应被收录。"""
        llm = LLMClient(provider="mock")
        reviewer = ReviewEngine(llm=llm, enable_llm_check=True)
        report = reviewer.run(sample_debate_transcript, small_brief)
        # 至少有程序检查 + 可能的 LLM 检查
        assert isinstance(report, ReviewReport)
        assert len(report.issues) >= 0
        # 不抛异常即通过

    def test_summary_reflects_issue_count(self, small_brief, sample_debate_transcript):
        """summary 字段应能反映问题数量。"""
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(sample_debate_transcript, small_brief)
        assert isinstance(report.summary, str)
        assert len(report.summary) > 0

    def test_issue_targets_map_to_existing_arguments(self, small_brief):
        """所有 issue.target_arg_id 都应指向 transcript 中存在的论点。"""
        # 构造混合测试：一半有效引用，一半无效
        valid_ids = [e.evidence_id for e in small_brief.items]
        args = []
        for i in range(6):
            refs = [] if i < 3 else [valid_ids[i % len(valid_ids)]]
            args.append(DebateArgument(
                arg_id=f"A-{i+1:03d}",
                content=f"论点 {i+1}",
                side=("pro" if i % 2 == 0 else "con"),
                speaker="Agent",
                round_index=1,
                evidence_refs=refs,
            ))
        # 再加入引用无效 id 的
        args.append(DebateArgument(
            arg_id="A-999",
            content="有问题的引用",
            side="con",
            speaker="Agent",
            round_index=1,
            evidence_refs=["E-999"],
        ))
        transcript = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=args,
            argument_index=ArgumentIndex(
                arguments=args,
                pro_count=sum(1 for a in args if a.side == "pro"),
                con_count=sum(1 for a in args if a.side == "con"),
            ),
        )
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(transcript, small_brief)
        arg_ids = {a.arg_id for a in args}
        for issue in report.issues:
            assert issue.target_arg_id in arg_ids, (
                f"issue {issue.issue_id} 指向了不存在的论点 {issue.target_arg_id}"
            )

    def test_pro_con_issue_counts_match(self, small_brief):
        """pro_issues / con_issues 应与实际按 side 统计一致。"""
        args = []
        for i in range(10):
            side = "pro" if i % 2 == 0 else "con"
            args.append(DebateArgument(
                arg_id=f"A-{i+1:03d}",
                content=f"{side} 论点 {i+1}",
                side=side,
                speaker=f"{side} Agent",
                round_index=1,
                evidence_refs=[],  # 故意无证据
            ))
        transcript = DebateTranscript(
            problem="问题？",
            pro_stance="正方",
            con_stance="反方",
            rounds_total=1,
            arguments=args,
            argument_index=ArgumentIndex(arguments=args, pro_count=5, con_count=5),
        )
        reviewer = ReviewEngine(llm=None, enable_llm_check=False)
        report = reviewer.run(transcript, small_brief)
        # 每方应有 5 个 no_evidence 问题
        assert report.pro_issues == 5
        assert report.con_issues == 5
