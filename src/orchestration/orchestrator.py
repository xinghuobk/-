"""ParaJudge 主编排器（Orchestrator）。

Phase 0 · 证据构建 → Phase 1 · 辩论 → Phase 2.0 · 事实核查 → Phase 2.1 · 审理 → Phase 2.2 · 裁决
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from backend.models.schemas import FullPipelineOutput, EvidenceBrief
from src.debate.evidence_builder import build_evidence_brief
from src.debate.simple_debate import SimpleDebate
from src.debate.moderator import Moderator, ModeratorConfig, ModeratorStrictness
from src.judgment.fact_checker import FactChecker
from src.judgment.review_engine import ReviewEngine
from src.judgment.judgment_engine import JudgmentEngine
from src.writer.llm_client import LLMClient


def run_parajudge(
    problem: str,
    provider: str = "mock",
    model: str = "mock-model",
    api_key: Optional[str] = None,
    rounds: int = 3,
    max_evidence: int = 20,
    enable_llm_review: bool = True,
    enable_moderator: bool = True,
    moderator_strictness: str = "normal",
    enable_t1_aebg: bool = True,
    enable_t3_ks: bool = True,
    enable_t4_ds: bool = True,
    use_judge_v2: bool = False,
    enable_fact_check: bool = False,
) -> FullPipelineOutput:
    """执行完整的 ParaJudge 流程。

    Args:
        problem: 待辩论的问题文本
        provider: LLM 提供商（mock / openai / dashscope / ollama）
        model: 具体模型名称
        api_key: 可选的 API Key（Ollama 模式可留空）
        rounds: 辩论轮数（每轮 = 正方 + 反方各发言一次）
        max_evidence: Phase 0 证据包的最大条数
        enable_llm_review: 是否启用 LLM 辅助的审理检查
        enable_moderator: 是否启用主持人
        moderator_strictness: 主持人严格度 loose / normal / strict
        enable_t1_aebg: 是否启用 T1 论点-证据二部图创新点
        enable_t3_ks: 是否启用 T3 KS 早停检验
        enable_t4_ds: 是否启用 T4 DS 证据理论融合

    Returns:
        FullPipelineOutput: 包含所有阶段产物的结构化输出
    """
    t_start = time.perf_counter()

    # 初始化 LLM 客户端
    llm = LLMClient(provider=provider, model=model, api_key=api_key)

    # ── Phase 0 · 证据构建 ─────────────────────────────
    brief: EvidenceBrief = build_evidence_brief(problem, max_papers=max_evidence)

    # ── Phase 1 · 辩论（含主持人）────────────────────
    moderator: Optional[Moderator] = None
    if enable_moderator:
        try:
            strict_enum = ModeratorStrictness(moderator_strictness)
        except ValueError:
            strict_enum = ModeratorStrictness.NORMAL
        moderator = Moderator(
            config=ModeratorConfig(strictness=strict_enum),
            llm=llm,
        )
    debater = SimpleDebate(llm, rounds=rounds, moderator=moderator)
    transcript = debater.run(problem, brief)

    # ── T1 AEBG（论点-证据二部图）─ 可选附加分析 ──────
    if enable_t1_aebg:
        try:
            from src.judgment.innovation import build_argument_evidence_bipartite
            aebg_summary = build_argument_evidence_bipartite(transcript, brief)
            # 注入到 moderator_report 元数据（保持原结构兼容）
            if transcript.moderator_report is None:
                transcript.moderator_report = {}
            transcript.moderator_report["t1_aebg"] = aebg_summary
        except Exception as e:
            # 创新点失败不应阻断主流程
            if transcript.moderator_report is None:
                transcript.moderator_report = {}
            transcript.moderator_report["t1_aebg_error"] = str(e)

    # ── T3 KS 早停检验 ───────────────────────────────
    if enable_t3_ks:
        try:
            from src.judgment.innovation import ks_early_stop_check
            ks_result = ks_early_stop_check(transcript)
            if transcript.moderator_report is None:
                transcript.moderator_report = {}
            transcript.moderator_report["t3_ks"] = ks_result
        except Exception as e:
            if transcript.moderator_report is None:
                transcript.moderator_report = {}
            transcript.moderator_report["t3_ks_error"] = str(e)

    # ── Phase 2.0 · 事实核查（可选）──────────────────
    fact_check = None
    if enable_fact_check:
        checker = FactChecker(llm)
        fact_check = checker.run(transcript, problem)

    # ── Phase 2.1 · 审理 ───────────────────────────────
    reviewer = ReviewEngine(llm=llm, enable_llm_check=enable_llm_review)
    review = reviewer.run(transcript, brief)

    # ── Phase 2.2 · 裁决（含 T4 DS 融合可选）─────────
    judge = JudgmentEngine(llm, use_judge_v2=use_judge_v2)
    judgment = judge.run(transcript, brief, review)

    # ── T4 双路证据融合 ────────────────────────────────
    if enable_t4_ds:
        try:
            from src.judgment.innovation import (
                ds_evidence_fusion,
                ds_orthographic_combination,
            )

            # 路径 1：启发式融合（加权平均 + renormalize）
            heuristic = ds_evidence_fusion(judgment.judge_scores)
            heuristic_label = heuristic.get("interpretation", "")

            # 路径 2：DS 正交和近似
            ds_approx = ds_orthographic_combination(judgment.judge_scores)
            ds_approx_label = ds_approx.get("interpretation", "")

            # 注入不确定性信息
            if judgment.uncertainties is None:
                judgment.uncertainties = []
            judgment.uncertainties.append(
                f"T4 启发式融合：{heuristic_label} "
                f"（confidence={heuristic.get('confidence', 0):.2f}）"
            )
            judgment.uncertainties.append(
                f"T4 DS 正交和近似：{ds_approx_label} "
                f"（confidence={ds_approx.get('confidence', 0):.2f}, K冲突={ds_approx.get('conflict_K', 0):.2f}）"
            )
            # 存储两路结果（供 JSONL 输出）
            judgment._t4_heuristic = heuristic
            judgment._t4_ds_approx = ds_approx

        except Exception as e:
            if judgment.uncertainties is None:
                judgment.uncertainties = []
            judgment.uncertainties.append(f"T4 融合失败: {e}")

    return FullPipelineOutput(
        run_id=str(uuid.uuid4())[:8],
        problem=problem,
        evidence_brief=brief,
        transcript=transcript,
        fact_check=fact_check,
        review=review,
        judgment=judgment,
        total_time_sec=round(time.perf_counter() - t_start, 2),
    )


def render_console(output: FullPipelineOutput) -> str:
    """将 FullPipelineOutput 渲染为控制台可读的文本报告。"""
    j = output.judgment
    t = output.transcript
    r = output.review
    b = output.evidence_brief

    winner_label = {
        "pro": "✅ 正方胜出",
        "con": "✅ 反方胜出",
        "tie": "⚖  平局（无明显胜者）",
    }.get(j.winner, j.winner)

    lines = [
        "",
        "=" * 68,
        f"  ParaJudge 报告｜问题：{output.problem}",
        "=" * 68,
        f"  Run ID : {output.run_id}",
        f"  总耗时 : {output.total_time_sec}s（Phase 0 {b.build_time_sec}s / "
        f"Phase 1 {t.generation_time}s / Phase 2 {r.generation_time + j.generation_time}s）",
        f"  证据包 : {b.total_count} 条 / 关键词 {', '.join(b.query_terms)[:40]}",
        f"  辩论轮 : {t.rounds_total} 轮 / 论点 {len(t.arguments)} 个",
        f"  审理问题 : 严重 {r.critical_count} / 警告 {r.warning_count}",
        "",
    ]

    # ── 主持人报告 ──
    if t.moderator_report:
        mr = t.moderator_report
        lines.extend([
            "─" * 68,
            f"  🎙️  主持人报告",
            "─" * 68,
            f"  干预次数: {mr.get('interventions', 0)} | 警告次数: {mr.get('warnings', 0)}",
            f"  辩论总时长: {mr.get('total_debate_sec', 0)}s | 平均轮时长: {mr.get('avg_turn_sec', 0)}s",
        ])
        # 显示最近 5 条主持人 notes
        for n in mr.get("notes", [])[:5]:
            sev_icon = "❌" if n.get("severity") == "critical" else ("⚠️" if n.get("severity") == "warn" else "ℹ️")
            lines.append(
                f"   {sev_icon} [{n.get('action', '?')}] R{n.get('round_index', '?')}: {n.get('message', '')[:100]}"
            )
        # 创新点数据
        if "t1_aebg" in mr:
            aebg = mr["t1_aebg"]
            lines.extend([
                "",
                f"  【T1 论点-证据二部图】",
                f"    节点 {aebg.get('nodes', {}).get('total', 0)} / 边 {aebg.get('edges', 0)} / 密度 {aebg.get('density', 0):.2%}",
                f"    正引 {aebg.get('pro_cited_count', 0)} 条 / 反引 {aebg.get('con_cited_count', 0)} 条 / 共引 {aebg.get('shared_evidence_count', 0)} 条",
                f"    {aebg.get('comment', '')}",
            ])
        if "t3_ks" in mr:
            ks = mr["t3_ks"]
            stop_icon = "🛑" if ks.get("suggest_early_stop") else "▶️"
            lines.extend([
                "",
                f"  【T3 KS 早停检验】{stop_icon}",
                f"    每轮新增 token: {ks.get('per_round_new_tokens', [])}",
                f"    停滞比例: {ks.get('stagnation_ratio', 'N/A')} | {ks.get('reason', '')}",
            ])
        lines.append("")

    lines.extend([
        "─" * 68,
        f"  ★ 裁决结论：{winner_label}",
        f"    正方 {j.pro_final_score:>5.1f}   vs   反方 {j.con_final_score:>5.1f}",
        "─" * 68,
        "",
        "  【各法官评分】",
    ])
    for js in j.judge_scores:
        lines.append(
            f"   - {js.judge_name:12s}｜正方 {js.pro_score:>5.1f} / 反方 {js.con_score:>5.1f}｜{js.reasoning[:50]}"
        )

    lines.extend([
        "",
        "  【关键论点 · 正方】",
    ])
    for p in j.key_points_pro:
        lines.append(f"   · {p[:140]}")
    lines.append("")
    lines.append("  【关键论点 · 反方】")
    for p in j.key_points_con:
        lines.append(f"   · {p[:140]}")

    if j.uncertainties:
        lines.extend(["", "  【不确定性 / 需要注意】"])
        for u in j.uncertainties:
            lines.append(f"   ⚠  {u}")

    if r.issues:
        lines.extend(["", "  【审理问题清单（前 5 条）】"])
        for issue in r.issues[:5]:
            tag = "❌" if issue.severity == "critical" else "⚠"
            lines.append(
                f"   {tag} [{issue.issue_type}] 论点 {issue.target_arg_id} — "
                f"{issue.description[:100]}"
            )

    # 推理链（摘要）
    if j.reasoning_chain_pro:
        lines.extend([
            "",
            "  【推理链 · 正方摘要（前 4 节点）】",
        ])
        for node in j.reasoning_chain_pro[:4]:
            tag = "主张" if node.source_type == "claim" else "证据"
            lines.append(f"   [{tag}] {node.content[:100]}")

    lines.extend([
        "",
        "=" * 68,
        "  使用真实 LLM：将 provider 设置为 'openai' 或 'dashscope'，",
        "  并配置对应的 API Key，即可获得更高质量的论证与裁决。",
        "=" * 68,
        "",
    ])
    return "\n".join(lines)


def render_markdown(output: FullPipelineOutput) -> str:
    """将 FullPipelineOutput 渲染为 Markdown 裁决书。"""
    j = output.judgment
    t = output.transcript
    r = output.review
    b = output.evidence_brief

    winner_cn = {"pro": "正方胜出", "con": "反方胜出", "tie": "平局"}.get(j.winner, j.winner)

    parts = [
        f"# ParaJudge 裁决报告",
        "",
        f"**问题**：{output.problem}  ",
        f"**Run ID**: `{output.run_id}`  ",
        f"**总耗时**: {output.total_time_sec}s",
        "",
        f"## 裁决结论",
        "",
        f"- **胜方**：**{winner_cn}**",
        f"- **正方最终评分**：{j.pro_final_score:.1f} / 100",
        f"- **反方最终评分**：{j.con_final_score:.1f} / 100",
        "",
        f"| 法官 | 正方评分 | 反方评分 | 法官推理 |",
        f"| --- | --- | --- | --- |",
    ]
    for js in j.judge_scores:
        parts.append(
            f"| {js.judge_name} | {js.pro_score:.1f} | {js.con_score:.1f} | "
            f"{js.reasoning[:80]} |"
        )

    parts.extend([
        "",
        f"## 正方核心论点",
        "",
    ])
    for p in j.key_points_pro:
        parts.append(f"- {p}")

    parts.extend(["", f"## 反方核心论点", ""])
    for p in j.key_points_con:
        parts.append(f"- {p}")

    if j.uncertainties:
        parts.extend(["", "## 不确定性与限制", ""])
        for u in j.uncertainties:
            parts.append(f"- ⚠ {u}")

    # ── Phase 2.0 · 事实核查报告 ───────────────────────
    fc = output.fact_check
    if fc and fc.claims:
        parts.extend(["", "## 事实核查报告", ""])
        parts.append(f"**结论**：{fc.summary}")
        parts.extend(["", "| 声明 | 类别 | 裁决 | 置信度 |", "| --- | --- | --- | --- |"])
        verdict_map = {
            "verified": "✅ 已验证",
            "refuted": "❌ 已证伪",
            "uncertain": "❓ 证据不足",
            "out_of_scope": "💭 价值/观点",
        }
        for c in fc.claims[:15]:
            v = verdict_map.get(c.verdict.value, c.verdict.value)
            is_fact = "事实" if c.is_factual else "价值"
            parts.append(
                f"| {c.content[:60]}... | {is_fact} | {v} | {c.confidence:.2f} |"
            )

    if r.issues:
        parts.extend(["", "## 审理发现的问题", ""])
        for issue in r.issues:
            severity = "严重" if issue.severity == "critical" else "警告"
            parts.append(
                f"- **[{severity}]** `{issue.issue_type}`（论点 `{issue.target_arg_id}`）："
                f"{issue.description[:200]}"
            )

    parts.extend([
        "",
        "## 推理链（正方）",
        "",
        "| 节点类型 | 内容 | 引用证据 |",
        "| --- | --- | --- |",
    ])
    for node in j.reasoning_chain_pro:
        tag = "**主张**" if node.source_type == "claim" else "证据"
        refs = ", ".join(node.ref_ids) if node.ref_ids else "—"
        parts.append(f"| {tag} | {node.content[:120]} | {refs} |")

    parts.extend([
        "",
        "## 证据包",
        "",
        "| # | 证据 | 年份 | 相关性 |",
        "| --- | --- | --- | --- |",
    ])
    for item in b.items[:15]:
        title = item.title[:80]
        year = item.year or "—"
        parts.append(
            f"| {item.evidence_id} | {title} | {year} | {item.relevance_score} |"
        )

    parts.extend([
        "",
        "---",
        "*本报告由 ParaJudge 多智能体系统生成。切换为真实 LLM 可显著提升质量。*",
        "",
    ])
    return "\n".join(parts)


__all__ = ["run_parajudge", "render_console", "render_markdown"]
