"""ParaJudge 主编排器（v0.3.0）。

Phase 0 · 证据构建 → Phase 1 · 辩论 → Phase 2.1 · 审理 → Phase 2.2 · 裁决
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from backend.models.schemas import (
    FullPipelineOutput,
    LLMSessionSummary,
    EvidenceBrief,
)
from src.debate.evidence_builder import build_evidence_brief
from src.debate.simple_debate import SimpleDebate
from src.judgment.review_engine import ReviewEngine
from src.judgment.judgment_engine import JudgmentEngine
from src.writer.llm_client import LLMClient


PARAJUDGE_VERSION = "0.3.0"


def run_parajudge(
    problem: str,
    provider: str = "mock",
    model: str = "mock-model",
    api_key: Optional[str] = None,
    rounds: int = 3,
    max_evidence: int = 20,
    enable_llm_review: bool = True,
    debater_temperature: Optional[float] = None,
    judge_temperature: Optional[float] = None,
    review_temperature: Optional[float] = None,
) -> FullPipelineOutput:
    """执行完整的 ParaJudge 流程。

    v0.3.0 — 支持真实 LLM 调用 + 完整成本统计 + 版本号

    Args:
        problem: 待辩论的问题文本
        provider: LLM 提供商（mock / openai / dashscope）
        model: 具体模型名称
        api_key: 可选的 API Key（如为 None 会从环境变量读取）
        rounds: 辩论轮数
        max_evidence: Phase 0 证据包的最大条数
        enable_llm_review: 是否启用 LLM 辅助的审理检查
        debater_temperature: 辩论者温度（影响创造性）
        judge_temperature: 法官温度
        review_temperature: 审理温度
    """
    t_start = time.perf_counter()

    # 配置记录（用于实验数据复现）
    config: Dict[str, Any] = {
        "version": PARAJUDGE_VERSION,
        "provider": provider,
        "model": model,
        "rounds": rounds,
        "max_evidence": max_evidence,
        "enable_llm_review": enable_llm_review,
        "debater_temperature": debater_temperature,
        "judge_temperature": judge_temperature,
        "review_temperature": review_temperature,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z",
    }

    # 初始化共享的 LLM 客户端
    llm = LLMClient(provider=provider, model=model, api_key=api_key)

    # ── Phase 0 · 证据构建
    brief: EvidenceBrief = build_evidence_brief(problem, max_papers=max_evidence)

    # ── Phase 1 · 辩论
    debater = SimpleDebate(llm, rounds=rounds)
    transcript = debater.run(problem, brief)

    # ── Phase 2.1 · 审理
    reviewer = ReviewEngine(llm=llm, enable_llm_check=enable_llm_review)
    review = reviewer.run(transcript, brief)

    # ── Phase 2.2 · 裁决
    judge = JudgmentEngine(llm)
    judgment = judge.run(transcript, brief, review)

    # ── 汇总 LLM 统计
    calls_by_role: Dict[str, int] = {}
    for record in llm.stats.calls:
        calls_by_role[record.role] = calls_by_role.get(record.role, 0) + 1

    llm_summary = LLMSessionSummary(
        total_calls=len(llm.stats.calls),
        total_prompt_tokens=llm.stats.total_prompt_tokens,
        total_completion_tokens=llm.stats.total_completion_tokens,
        total_tokens=llm.stats.total_prompt_tokens + llm.stats.total_completion_tokens,
        total_cost_cny=round(llm.stats.total_cost_cny, 6),
        calls_by_role=calls_by_role,
    )

    output = FullPipelineOutput(
        version=PARAJUDGE_VERSION,
        run_id=str(uuid.uuid4())[:8],
        problem=problem,
        config=config,
        evidence_brief=brief,
        transcript=transcript,
        review=review,
        judgment=judgment,
        total_time_sec=round(time.perf_counter() - t_start, 2),
        llm_stats=llm_summary,
    )
    return output


def save_experiment(
    output: FullPipelineOutput,
    output_dir: Optional[str] = None,
) -> str:
    """将一次完整运行保存到 `experiments/` 目录（或指定目录。

    每个运行保存为独立子目录，包含：
    - output.json: 完整结构化数据
    - report.md: Markdown 裁决报告
    - llm_stats.json: LLM 调用明细
    """
    output_dir = output_dir or os.environ.get("EXPERIMENT_OUTPUT_DIR", "./experiments")
    run_dir = Path(output_dir) / f"run_{output.run_id}_{time.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. output.json
    (run_dir / "output.json").write_text(
        output.model_dump_json(indent=2), encoding="utf-8"
    )

    # 2. report.md
    (run_dir / "report.md").write_text(render_markdown(output), encoding="utf-8")

    # 3. config.json
    config_copy = dict(output.config)
    (run_dir / "config.json").write_text(
        json.dumps(config_copy, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # 4. llm_stats.json
    llm_records = [
        {
            "role": c.role,
            "prompt_tokens": c.prompt_tokens,
            "completion_tokens": c.completion_tokens,
            "total_tokens": c.total_tokens,
            "cost_cny": c.cost_cny,
            "latency_ms": c.latency_ms,
            "success": c.success,
            "provider": c.provider,
            "model": c.model,
        }
        for c in []
    ]
    (run_dir / "llm_stats_summary.json").write_text(
        json.dumps(
            {
                "summary": output.llm_stats.model_dump(),
                "records": llm_records,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8"
    )

    return str(run_dir)


def render_console(output: FullPipelineOutput) -> str:
    """渲染为控制台可读的文本报告。"""
    j = output.judgment
    t = output.transcript
    r = output.review
    b = output.evidence_brief

    winner_label = {
        "pro": "✅ 正方胜出",
        "con": "✅ 反方胜出",
        "tie": "⚖ 平局（无明显胜者）",
    }.get(j.winner, j.winner)

    lines = [
        "",
        "=" * 70,
        f"  ParaJudge v{output.version}｜问题：{output.problem}",
        "=" * 70,
        f"  Run ID      : {output.run_id}",
        f"  Provider    : {output.config.get('provider', 'unknown')} / {output.config.get('model', 'unknown')}",
        f"  总耗时      : {output.total_time_sec}s  "
        f"（Phase 0 {b.build_time_sec}s / Phase 1 {t.generation_time}s / "
        f"Phase 2 {r.generation_time + j.generation_time}s）",
        f"  证据包    : {b.total_count} 条",
        f"  辩论轮    : {t.rounds_total} 轮 / {len(t.arguments)} 个论点",
        f"  审理问题  : 严重 {r.critical_count} / 警告 {r.warning_count}",
        f"  LLM 调用  : {output.llm_stats.total_calls} 次, "
        f"({output.llm_stats.total_tokens:,} tokens, "
        f"¥{output.llm_stats.total_cost_cny:.4f}",
        "",
        "─" * 70,
        f"  ★ 裁决结论：{winner_label}",
        f"    正方 {j.pro_final_score:>5.1f}   vs   反方 {j.con_final_score:>5.1f}",
        "─" * 70,
        "",
        "  【各法官评分】",
    ]

    for js in j.judge_scores:
        lines.append(
            f"   - {js.judge_name:12s}｜正方 {js.pro_score:>5.1f} / 反方 {js.con_score:>5.1f}｜{js.reasoning[:60]}"
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
        lines.extend(["", "  【审理问题清单（前 5 条）"])
        for issue in r.issues[:5]:
            tag = "❌" if issue.severity == "critical" else "⚠"
            lines.append(
                f"   {tag} [{issue.issue_type}] 论点 {issue.target_arg_id} — "
                f"{issue.description[:100]}"
            )

    if j.reasoning_chain_pro:
        lines.extend([
            "",
            "  【推理链 · 正方摘要（前 4 节点）",
        ])
        for node in j.reasoning_chain_pro[:4]:
            lines.append(f"   [{node.source_type}] {node.content[:100]}")

    lines.extend([
        "",
        "=" * 70,
        "  使用真实 LLM：设置 provider=dashscope（通义千问），配置 DASHSCOPE_API_KEY",
        "  或 provider=openai（配置 OPENAI_API_KEY）",
        "=" * 70,
        "",
    ])
    return "\n".join(lines)


def render_markdown(output: FullPipelineOutput) -> str:
    """将 FullPipelineOutput 渲染为 Markdown 裁决书。"""
    j = output.judgment
    t = output.transcript
    r = output.review
    b = output.evidence_brief

    winner_cn = {"pro": "**正方胜出**", "con": "**反方胜出**", "tie": "**平局**"}.get(
        j.winner, j.winner)

    parts = [
        f"# ParaJudge 裁决报告",
        "",
        f"- **版本**：v{output.version}",
        f"- **Run ID**：`{output.run_id}`",
        f"- **问题**：{output.problem}",
        f"- **Provider**：{output.config.get('provider', 'unknown')} / {output.config.get('model', 'unknown')}",
        f"- **总耗时**：{output.total_time_sec}s",
        f"- **总 LLM 调用**：{output.llm_stats.total_calls} 次，{output.llm_stats.total_tokens:,} tokens，约 ¥{output.llm_stats.total_cost_cny:.4f}",
        "",
        f"## 裁决结论",
        "",
        f"- **胜方**：{winner_cn}",
        f"- **正方最终评分**：{j.pro_final_score:.1f} / 100",
        f"- **反方最终评分**：{j.con_final_score:.1f} / 100",
        "",
        "| 法官 | 正方 | 反方 | 推理 |",
        "| --- | ---:| ---:| --- |",
    ]
    for js in j.judge_scores:
        parts.append(f"| {js.judge_name} | {js.pro_score:.1f} | {js.con_score:.1f} | {js.reasoning[:80]} |")

    parts.extend([
        "", "## 论点流", ""])
    args = t.arguments
    parts.append(f"共 {len(args)} 个论点，{t.rounds_total} 轮辩论。")
    parts.append("")
    parts.append("| # | 立场 | 论点内容 | 引用证据 |")
    parts.append("| --- | --- | --- | --- |")
    for i, a in enumerate(args):
        refs = ", ".join(a.evidence_refs) or "—"
        side = "🟢 正方" if a.side == "pro" else "🔴 反方"
        parts.append(f"| {i+1} | {side} | {a.content[:80]} | {refs} |")

    parts.extend([
        "", "## 推理链（正方）", "",
        "| 节点类型 | 内容 | 引用证据 |",
        "| --- | --- | --- |",
    ])
    for node in j.reasoning_chain_pro:
        tag = "**主张**" if node.source_type == "claim" else node.source_type
        refs = ", ".join(node.ref_ids) if node.ref_ids else "—"
        parts.append(f"| {tag} | {node.content[:120]} | {refs} |")

    if r.issues:
        parts.extend(["", "## 审理发现", ""])
        for issue in r.issues:
            severity = "严重" if issue.severity == "critical" else "警告"
            parts.append(
                f"- **[{severity}]** `{issue.issue_type}`（论点 `{issue.target_arg_id}`）："
                f"{issue.description[:200]}"
            )

    parts.extend([
        "", "## 证据包", "",
        "| # | 标题 | 相关性 |",
        "| --- | --- | --- |",
    ])
    for item in b.items[:20]:
        title = item.title[:80]
        parts.append(f"| {item.evidence_id} | {title} | {item.relevance_score} |")

    parts.extend([
        "", "## 关键论点", "",
        "### 正方", ""
    ])
    for p in j.key_points_pro:
        parts.append(f"- {p}")
    parts.extend(["", "### 反方", ""])
    for p in j.key_points_con:
        parts.append(f"- {p}")

    if j.uncertainties:
        parts.extend(["", "## 不确定性与限制", ""])
        for u in j.uncertainties:
            parts.append(f"- ⚠ {u}")

    parts.extend([
        "", "---", "",
        f"*本报告由 ParaJudge v{output.version} 生成。*",
        f"*生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}*", "",
    ])
    return "\n".join(parts)


__all__ = ["run_parajudge", "render_console", "render_markdown", "save_experiment", "PARAJUDGE_VERSION"]
