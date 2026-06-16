"""ParaJudge 主编排器（Orchestrator）。

Phase 0 · 证据构建 → Phase 1 · 辩论 → Phase 2.1 · 审理 → Phase 2.2 · 裁决
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from backend.models.schemas import FullPipelineOutput, EvidenceBrief
from src.debate.evidence_builder import build_evidence_brief
from src.debate.simple_debate import SimpleDebate
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
) -> FullPipelineOutput:
    """执行完整的 ParaJudge 流程。

    Args:
        problem: 待辩论的问题文本
        provider: LLM 提供商（mock / openai / dashscope）
        model: 具体模型名称
        api_key: 可选的 API Key（如为 None 会从环境变量读取）
        rounds: 辩论轮数（每轮 = 正方 + 反方各发言一次）
        max_evidence: Phase 0 证据包的最大条数
        enable_llm_review: 是否启用 LLM 辅助的审理检查

    Returns:
        FullPipelineOutput: 包含所有阶段产物的结构化输出
    """
    t_start = time.perf_counter()

    # 初始化 LLM 客户端
    llm = LLMClient(provider=provider, model=model, api_key=api_key)

    # ── Phase 0 · 证据构建 ─────────────────────────────
    brief: EvidenceBrief = build_evidence_brief(problem, max_papers=max_evidence)

    # ── Phase 1 · 辩论 ─────────────────────────────────
    debater = SimpleDebate(llm, rounds=rounds)
    transcript = debater.run(problem, brief)

    # ── Phase 2.1 · 审理 ───────────────────────────────
    reviewer = ReviewEngine(llm=llm, enable_llm_check=enable_llm_review)
    review = reviewer.run(transcript, brief)

    # ── Phase 2.2 · 裁决 ───────────────────────────────
    judge = JudgmentEngine(llm)
    judgment = judge.run(transcript, brief, review)

    return FullPipelineOutput(
        run_id=str(uuid.uuid4())[:8],
        problem=problem,
        evidence_brief=brief,
        transcript=transcript,
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
        "─" * 68,
        f"  ★ 裁决结论：{winner_label}",
        f"    正方 {j.pro_final_score:>5.1f}   vs   反方 {j.con_final_score:>5.1f}",
        "─" * 68,
        "",
        "  【各法官评分】",
    ]
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
