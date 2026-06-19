"""Phase 2.1 · 审理引擎（ReviewEngine）。

两步审理：
  Step 1 · 程序化检查（纯代码，无需 LLM）：
    - invalid_cite：引用了证据包中不存在的 evidence_id
    - no_evidence：完全未引用任何证据

  Step 2 · LLM 检查（使用 LLM 判断）：
    - weak_support：证据的实际内容不直接支持该论点
    - circular：循环论证
    - contradiction：同一方内部论点互相矛盾
"""
from __future__ import annotations

import time
from typing import List

from backend.models.schemas import (
    EvidenceBrief,
    DebateTranscript,
    ReviewReport,
    IssueItem,
)
from src.writer.llm_client import LLMClient
from src.debate.prompts import build_review_prompt


# schemas.py 中 IssueItem.severity 字段定义为 str（见 schemas.py L576）
_SEVERITY_CRITICAL = "critical"
_SEVERITY_WARNING = "warning"
_SEVERITY_INFO = "info"


class ReviewEngine:
    def __init__(self, llm: LLMClient | None = None, enable_llm_check: bool = True):
        self.llm = llm
        self.enable_llm_check = enable_llm_check

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(
        self,
        transcript: DebateTranscript,
        brief: EvidenceBrief,
    ) -> ReviewReport:
        t0 = time.perf_counter()

        issues: List[IssueItem] = []

        # Step 1 · 程序检查
        issues.extend(self._programmatic_check(transcript, brief))

        # Step 2 · LLM 检查
        if self.enable_llm_check and self.llm is not None and transcript.arguments:
            issues.extend(self._llm_check(transcript, brief))

        # 统计
        pro_issues = sum(1 for i in issues if _is_arg_of_side(i.target_arg_id, "pro", transcript))
        con_issues = sum(1 for i in issues if _is_arg_of_side(i.target_arg_id, "con", transcript))
        critical_count = sum(1 for i in issues if i.severity == _SEVERITY_CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == _SEVERITY_WARNING)

        summary = ""
        if issues:
            summary_parts = []
            if critical_count:
                summary_parts.append(f"{critical_count} 个严重问题")
            if warning_count:
                summary_parts.append(f"{warning_count} 个警告")
            summary = "审理发现 " + "、".join(summary_parts or [f"{len(issues)} 个问题"]) + "。"
        else:
            summary = "未发现显著问题。"

        return ReviewReport(
            issues=issues,
            critical_count=critical_count,
            warning_count=warning_count,
            pro_issues=pro_issues,
            con_issues=con_issues,
            summary=summary,
            generation_time=round(time.perf_counter() - t0, 3),
        )

    # ------------------------------------------------------------------
    # Step 1 · 程序化检查
    # ------------------------------------------------------------------
    def _programmatic_check(
        self,
        transcript: DebateTranscript,
        brief: EvidenceBrief,
    ) -> List[IssueItem]:
        issues: List[IssueItem] = []
        valid_ids = {e.evidence_id for e in brief.items}
        issue_counter = 0

        for arg in transcript.arguments:
            # 完全没引用
            if not arg.evidence_refs:
                issue_counter += 1
                issues.append(IssueItem(
                    issue_id=f"R-{issue_counter:03d}",
                    severity=_SEVERITY_WARNING,
                    issue_type="no_evidence",
                    target_arg_id=arg.arg_id,
                    excerpt=arg.content[:80],
                    description="该论点未引用任何证据，属于纯粹的主张（assertion without evidence）。",
                ))
                continue

            # 引用了不存在的 evidence_id
            invalid_refs = [r for r in arg.evidence_refs if r not in valid_ids]
            if invalid_refs:
                issue_counter += 1
                issues.append(IssueItem(
                    issue_id=f"R-{issue_counter:03d}",
                    severity=_SEVERITY_CRITICAL,
                    issue_type="invalid_cite",
                    target_arg_id=arg.arg_id,
                    excerpt=arg.content[:80],
                    description=f"引用了证据包中不存在的证据: {', '.join(invalid_refs)}。证据包只包含以下 evidence_id: {', '.join(sorted(valid_ids))[:80]}",
                ))

        return issues

    # ------------------------------------------------------------------
    # Step 2 · LLM 检查
    # ------------------------------------------------------------------
    def _llm_check(
        self,
        transcript: DebateTranscript,
        brief: EvidenceBrief,
    ) -> List[IssueItem]:
        """使用 LLM 检查 weak_support / circular / contradiction。"""
        if not transcript.arguments:
            return []

        # 格式化论点
        lines = []
        for a in transcript.arguments:
            refs = ", ".join(a.evidence_refs) or "无"
            lines.append(f"[{a.arg_id}] [{a.side}-R{a.round_index}] {a.content}  [引用: {refs}]")
        args_text = "\n".join(lines)

        prompt = build_review_prompt(
            problem=transcript.problem,
            evidence_items=brief.items,
            arguments_text=args_text,
        )

        response = self.llm.call_json(prompt, max_tokens=800, temperature=0.3)

        if not isinstance(response, dict):
            return []

        raw_issues = response.get("issues", [])
        if not isinstance(raw_issues, list):
            return []

        issues: List[IssueItem] = []
        offset = 100  # LLM 生成的问题从 R-101 起编号，便于与程序化检查区分
        for raw in raw_issues:
            if not isinstance(raw, dict):
                continue
            issue_type = str(raw.get("issue_type", "weak_support"))
            target = str(raw.get("target_arg_id", ""))
            description = str(raw.get("description", "")).strip()
            if not description:
                continue
            # severity 映射
            severity = _SEVERITY_WARNING if issue_type in ("weak_support", "circular") else _SEVERITY_CRITICAL
            if issue_type == "contradiction":
                severity = _SEVERITY_CRITICAL
            issues.append(IssueItem(
                issue_id=f"R-{offset + len(issues):03d}",
                severity=severity,
                issue_type=issue_type,
                target_arg_id=target,
                excerpt="",
                description=description,
            ))
        return issues


# ------------------------------------------------------------------
# 工具
# ------------------------------------------------------------------
def _is_arg_of_side(arg_id: str, side: str, transcript: DebateTranscript) -> bool:
    for a in transcript.arguments:
        if a.arg_id == arg_id:
            return a.side == side
    # 若找不到，返回 False（保守）
    return False


__all__ = ["ReviewEngine"]
