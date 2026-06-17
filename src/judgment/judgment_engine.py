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
from src.judgment.judgment_config import CFG
from src.writer.llm_client import LLMClient
from src.debate.prompts import build_judge_prompt, build_judge_prompt_v2, JUDGE_ROLES


JUDGE_TYPES = list(JUDGE_ROLES.keys())  # ["evidence", "logic", "principle", "case", "innovation"]


class JudgmentEngine:
    def __init__(self, llm: LLMClient, use_judge_v2: bool = False):
        self.llm = llm
        self.use_judge_v2 = use_judge_v2

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(
        self,
        transcript: DebateTranscript,
        brief: EvidenceBrief,
        review: ReviewReport,
        use_judge_v2: bool = False,
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

        # --- 修复：从 moderator report 提取违规信息用于惩罚 ---
        penalty = self._extract_moderator_penalty(transcript)

        # 构建审理摘要（供法官参考）
        review_summary = self._build_review_summary(review)

        # 五位法官
        scores: List[JudgeScore] = []
        for judge_type in JUDGE_TYPES:
            if use_judge_v2 or self.use_judge_v2:
                score = self._single_judge_v2(judge_type, transcript.problem, brief, pro_args, con_args, review_summary)
            else:
                score = self._single_judge(judge_type, transcript.problem, brief, pro_args, con_args, review_summary)
            scores.append(score)

        # 融合（LLM 法官评分）
        pro_raw = sum(s.pro_score for s in scores) / len(scores)
        con_raw = sum(s.con_score for s in scores) / len(scores)

        # --- 修复：应用 moderator 惩罚（离题论点扣分） ---
        pro_final = round(max(0.0, pro_raw + penalty["pro"]), 1)
        con_final = round(max(0.0, con_raw + penalty["con"]), 1)

        # --- 修复：获胜阈值从 2.0 提高到 5.0（使用 CFG 配置）---
        winner = "tie"
        if pro_final - con_final > CFG.WINNER_THRESHOLD:
            winner = "pro"
        elif con_final - pro_final > CFG.WINNER_THRESHOLD:
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
            if spread > CFG.JUDGE_SPREAD_WARN:
                uncertainties.append(
                    f"法官对正方评分分歧较大（{min(pro_scores)} ~ {max(pro_scores)}），表明论证质量不稳定。"
                )
            con_scores = [s.con_score for s in scores]
            spread_c = max(con_scores) - min(con_scores) if con_scores else 0
            if spread_c > CFG.JUDGE_SPREAD_WARN:
                uncertainties.append(
                    f"法官对反方评分分歧较大（{min(con_scores)} ~ {max(con_scores)}）。"
                )

        # --- 修复：记录 moderator 惩罚 ---
        if penalty["pro_off_topic"] > 0 or penalty["con_off_topic"] > 0:
            uncertainties.append(
                f"Moderator 离题惩罚：正方 -{abs(penalty['pro']):.1f} "
                f"（{penalty['pro_off_topic']} 个论点离题），"
                f"反方 -{abs(penalty['con']):.1f} "
                f"（{penalty['con_off_topic']} 个论点离题）。"
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
    # Moderator 惩罚提取
    # ------------------------------------------------------------------
    def _extract_moderator_penalty(self, transcript) -> Dict:
        """从 moderator report 提取离题/重复等违规并计算惩罚分（使用 CFG 配置）。

        规则（每项独立累加，上限 CFG.PENALTY_CAP 分/方）：
        - warn_off_topic: 每个违规论点扣 CFG.PENALTY_OFF_TOPIC 分
        - warn_no_rebuttal: 每个未反驳论点扣 CFG.PENALTY_OFF_TOPIC 分
        - warn_duplicate: 每个重复论点扣 CFG.PENALTY_DUPLICATE 分
        - warn_too_long: 每个超长论点扣 CFG.PENALTY_TOO_LONG 分
        """
        report = getattr(transcript, "moderator_report", None)
        if not report:
            return {"pro": 0.0, "con": 0.0, "pro_off_topic": 0, "con_off_topic": 0}

        notes = report.get("notes", []) if isinstance(report, dict) else []
        pro_off_topic = 0
        con_off_topic = 0
        pro_penalty = 0.0
        con_penalty = 0.0

        for note in notes:
            action = note.get("action") if isinstance(note, dict) else None
            side = note.get("target_side") if isinstance(note, dict) else None
            if not action or not side:
                continue

            if action in ("warn_off_topic", "warn_no_rebuttal"):
                delta = CFG.PENALTY_OFF_TOPIC
                if side == "pro":
                    pro_off_topic += 1
                    pro_penalty += delta
                else:
                    con_off_topic += 1
                    con_penalty += delta
            elif action == "warn_duplicate":
                delta = CFG.PENALTY_DUPLICATE
                if side == "pro":
                    pro_penalty += delta
                else:
                    con_penalty += delta
            elif action == "warn_too_long":
                delta = CFG.PENALTY_TOO_LONG
                if side == "pro":
                    pro_penalty += delta
                else:
                    con_penalty += delta

        return {
            "pro": max(pro_penalty, CFG.PENALTY_CAP),
            "con": max(con_penalty, CFG.PENALTY_CAP),
            "pro_off_topic": pro_off_topic,
            "con_off_topic": con_off_topic,
        }

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

        # 回退逻辑：如果失败，给一个中性评分（使用 CFG）
        if not isinstance(response, dict) or "pro_score" not in response:
            return JudgeScore(
                judge_type=judge_type,
                judge_name=judge_name,
                pro_score=CFG.SCORE_DEFAULT,
                con_score=CFG.SCORE_DEFAULT,
                pro_feedback="（LLM 未能返回有效评分，使用默认值）",
                con_feedback="（LLM 未能返回有效评分，使用默认值）",
                reasoning="解析失败，使用系统回退评分。",
            )

        def _safe_float(x, default: float = CFG.SCORE_DEFAULT) -> float:
            try:
                return float(x)
            except (TypeError, ValueError):
                return default

        pro_score = max(CFG.SCORE_MIN, min(CFG.SCORE_MAX, _safe_float(response.get("pro_score"), CFG.SCORE_DEFAULT)))
        con_score = max(CFG.SCORE_MIN, min(CFG.SCORE_MAX, _safe_float(response.get("con_score"), CFG.SCORE_DEFAULT)))
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
    # 单法官评分 v2（事实/价值论证区分）
    # ------------------------------------------------------------------
    def _single_judge_v2(
        self,
        judge_type: str,
        problem: str,
        brief: EvidenceBrief,
        pro_args: List[Dict],
        con_args: List[Dict],
        review_summary: str,
    ) -> JudgeScore:
        """v2 法官：区分事实声明与价值声明，分别评分。"""
        judge_name = JUDGE_ROLES.get(judge_type, ("通用法官", ""))[0]
        prompt = build_judge_prompt_v2(
            judge_type=judge_type,
            problem=problem,
            evidence_items=brief.items,
            pro_arguments=pro_args,
            con_arguments=con_args,
            review_summary=review_summary,
        )
        response = self.llm.call_json(prompt, max_tokens=600, temperature=0.2)

        def _safe_float(x, default: float = CFG.SCORE_DEFAULT) -> float:
            try:
                return float(x)
            except (TypeError, ValueError):
                return default

        # 解析事实/价值评分（可选字段，容错）
        pro_fact = _safe_float(response.get("pro_fact_score"), None)
        con_fact = _safe_float(response.get("con_fact_score"), None)
        pro_value = _safe_float(response.get("pro_value_score"), None)
        con_value = _safe_float(response.get("con_value_score"), None)

        pro_score = max(CFG.SCORE_MIN, min(CFG.SCORE_MAX, _safe_float(response.get("pro_score"), CFG.SCORE_DEFAULT)))
        con_score = max(CFG.SCORE_MIN, min(CFG.SCORE_MAX, _safe_float(response.get("con_score"), CFG.SCORE_DEFAULT)))

        return JudgeScore(
            judge_type=judge_type,
            judge_name=judge_name,
            pro_score=round(pro_score, 1),
            con_score=round(con_score, 1),
            pro_feedback=str(response.get("pro_feedback", "")),
            con_feedback=str(response.get("con_feedback", "")),
            reasoning=str(response.get("reasoning", "")),
            pro_fact_score=pro_fact,
            con_fact_score=con_fact,
            pro_value_score=pro_value,
            con_value_score=con_value,
            pro_fact_claims=response.get("pro_fact_claims", []),
            con_fact_claims=response.get("con_fact_claims", []),
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
