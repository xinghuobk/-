"""Phase 2.2 · 裁决引擎（JudgmentEngine）。

MVP 策略：
- 5 位法官独立评分（evidence / logic / principle / case / innovation）
- 简单加权平均（等权重）
- 生成推理链节点（从论点回溯到证据）

演进方向：
- DS 证据理论融合（替代加权平均）
- 推理链图谱化（支持可视化裁决树）
"""
from __future__ import annotations

import time
from typing import List, Dict

from backend.models.schemas import (
    EvidenceBrief,
    DebateTranscript,
    ReviewReport,
    JudgmentResult,
    JudgeScore,
    ReasoningNode,
)
from src.writer.llm_client import LLMClient
from src.debate.prompts import build_judge_prompt, JUDGE_ROLES


JUDGE_TYPES = list(JUDGE_ROLES.keys())  # ["evidence", "logic", "principle", "case", "innovation"]


class JudgmentEngine:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(
        self,
        transcript: DebateTranscript,
        brief: EvidenceBrief,
        review: ReviewReport,
    ) -> JudgmentResult:
        t0 = time.perf_counter()

        # 收集正反方论点（简化为 dict 列表）
        pro_args = [
            {"id": a.arg_id, "content": a.content, "evidence_refs": a.evidence_refs}
            for a in transcript.argument_index.arguments
            if a.side == "pro"
        ]
        con_args = [
            {"id": a.arg_id, "content": a.content, "evidence_refs": a.evidence_refs}
            for a in transcript.argument_index.arguments
            if a.side == "con"
        ]

        # 构建审理摘要（供法官参考）
        review_summary = self._build_review_summary(review)

        # 五位法官
        scores: List[JudgeScore] = []
        for judge_type in JUDGE_TYPES:
            score = self._single_judge(judge_type, transcript.problem, brief, pro_args, con_args, review_summary)
            scores.append(score)

        # 融合
        pro_final = round(sum(s.pro_score for s in scores) / len(scores), 1)
        con_final = round(sum(s.con_score for s in scores) / len(scores), 1)

        winner = "tie"
        if pro_final - con_final > 2.0:
            winner = "pro"
        elif con_final - pro_final > 2.0:
            winner = "con"

        # 推理链
        reasoning_pro = self._build_reasoning_chain("pro", pro_args, brief)
        reasoning_con = self._build_reasoning_chain("con", con_args, brief)

        # 关键要点
        key_points_pro = [a["content"] for a in pro_args[:3]]
        key_points_con = [a["content"] for a in con_args[:3]]

        # 不确定性 / 审理问题
        uncertainties = []
        if review.critical_count > 0:
            first_critical = next((i for i in review.issues if i.severity == "critical"), None)
            if first_critical:
                uncertainties.append(
                    f"存在 {review.critical_count} 个严重问题（如论点 {first_critical.target_arg_id}: {first_critical.issue_type}）。"
                )
        # 法官分歧较大
        if scores:
            pro_scores = [s.pro_score for s in scores]
            spread = max(pro_scores) - min(pro_scores) if pro_scores else 0
            if spread > 25:
                uncertainties.append(
                    f"法官对正方评分分歧较大（{min(pro_scores)} ~ {max(pro_scores)}），表明论证质量不稳定。"
                )
            con_scores = [s.con_score for s in scores]
            spread_c = max(con_scores) - min(con_scores) if con_scores else 0
            if spread_c > 25:
                uncertainties.append(
                    f"法官对反方评分分歧较大（{min(con_scores)} ~ {max(con_scores)}）。"
                )

        return JudgmentResult(
            winner=winner,
            pro_final_score=pro_final,
            con_final_score=con_final,
            judge_scores=scores,
            reasoning_chain_pro=reasoning_pro,
            reasoning_chain_con=reasoning_con,
            key_points_pro=key_points_pro,
            key_points_con=key_points_con,
            uncertainties=uncertainties,
            generation_time=round(time.perf_counter() - t0, 3),
        )

    # ------------------------------------------------------------------
    # 单法官评分
    # ------------------------------------------------------------------
    def _single_judge(
        self,
        judge_type: str,
        problem: str,
        brief: EvidenceBrief,
        pro_args: List[Dict],
        con_args: List[Dict],
        review_summary: str,
    ) -> JudgeScore:
        judge_name = JUDGE_ROLES.get(judge_type, ("通用法官", ""))[0]
        prompt = build_judge_prompt(
            judge_type=judge_type,
            problem=problem,
            evidence_items=brief.items,
            pro_arguments=pro_args,
            con_arguments=con_args,
            review_summary=review_summary,
        )
        response = self.llm.call_json(prompt, max_tokens=500, temperature=0.2)

        # 回退逻辑：如果失败，给一个中性评分
        if not isinstance(response, dict) or "pro_score" not in response:
            return JudgeScore(
                judge_type=judge_type,
                judge_name=judge_name,
                pro_score=50.0,
                con_score=50.0,
                pro_feedback="（LLM 未能返回有效评分，使用默认值）",
                con_feedback="（LLM 未能返回有效评分，使用默认值）",
                reasoning="解析失败，使用系统回退评分。",
            )

        def _safe_float(x, default: float = 50.0) -> float:
            try:
                return float(x)
            except (TypeError, ValueError):
                return default

        pro_score = max(0.0, min(100.0, _safe_float(response.get("pro_score"), 50.0)))
        con_score = max(0.0, min(100.0, _safe_float(response.get("con_score"), 50.0)))
        return JudgeScore(
            judge_type=judge_type,
            judge_name=judge_name,
            pro_score=round(pro_score, 1),
            con_score=round(con_score, 1),
            pro_feedback=str(response.get("pro_feedback", "")),
            con_feedback=str(response.get("con_feedback", "")),
            reasoning=str(response.get("reasoning", "")),
        )

    # ------------------------------------------------------------------
    # 推理链构建
    # ------------------------------------------------------------------
    def _build_reasoning_chain(
        self,
        side: str,
        args: List[Dict],
        brief: EvidenceBrief,
    ) -> List[ReasoningNode]:
        """从论点回溯到证据，构建一条可读的推理链节点列表。"""
        evidence_by_id = {e.evidence_id: e for e in brief.items}
        nodes: List[ReasoningNode] = []
        nid = 1

        # 取前 3 个论点作为主张节点
        for arg in args[:3]:
            nodes.append(ReasoningNode(
                node_id=f"N-{nid:03d}",
                content=arg["content"][:200],
                source_type="claim",
                ref_ids=list(arg.get("evidence_refs", []))[:3],
            ))
            nid += 1

            # 为每条引用的证据添加一个节点（避免重复）
            for ref in arg.get("evidence_refs", [])[:3]:
                ev = evidence_by_id.get(ref)
                if ev:
                    nodes.append(ReasoningNode(
                        node_id=f"N-{nid:03d}",
                        content=f"{ev.title}（{ev.year or 'N/A'}） · {ev.abstract_excerpt[:120]}",
                        source_type="evidence",
                        ref_ids=[ref],
                    ))
                    nid += 1

        return nodes

    # ------------------------------------------------------------------
    # 审理摘要构建
    # ------------------------------------------------------------------
    @staticmethod
    def _build_review_summary(review: ReviewReport) -> str:
        if not review.issues:
            return "未发现显著问题。"
        parts = [f"共发现 {len(review.issues)} 个问题（严重 {review.critical_count}，警告 {review.warning_count}）。"]
        for issue in review.issues[:5]:  # 最多列 5 个
            parts.append(f"- [{issue.issue_id}] {issue.severity}·{issue.issue_type}（论点 {issue.target_arg_id}）：{issue.description[:100]}")
        return "\n".join(parts)


__all__ = ["JudgmentEngine"]
