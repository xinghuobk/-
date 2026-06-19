#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ParaJudge Loop —— 交互式 REPL。

使用方式:
    python scripts/loop.py                      # 启动 Loop（默认 mock 模式）
    python scripts/loop.py --provider ollama     # 指定 LLM 提供商
    python scripts/loop.py --problem "..."       # 预先设置问题

支持的命令:
    problem <text>            设置 / 查看当前辩论问题
    set <key> <value>         修改运行参数 (provider, model, rounds, max_evidence ...)
    config                    查看当前所有参数配置
    run                       执行完整 pipeline（Phase 0 → 3）
    step [n]                  逐步执行（默认一步，可指定第 n 阶段直接跳到）
    show [phase]              查看某阶段结果 (evidence, debate, review, judgment, all)
    compare <run_id_a> <run_id_b>  对比两次运行结果
    history                   列出本次会话中的所有运行
    export <path> [fmt]       导出最近一次运行结果 (json / md)
    clear                     清空当前状态（保留配置）
    help / ?                  显示本帮助
    quit / exit / ^D         退出 Loop
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

# 允许从项目根目录运行（python scripts/loop.py）
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.orchestration.orchestrator import run_parajudge, render_console  # noqa: E402
from src.debate.evidence_builder import build_evidence_brief  # noqa: E402
from src.debate.simple_debate import SimpleDebate  # noqa: E402
from src.debate.moderator import Moderator, ModeratorConfig, ModeratorStrictness  # noqa: E402
from src.judgment.review_engine import ReviewEngine  # noqa: E402
from src.judgment.judgment_engine import JudgmentEngine  # noqa: E402
from src.judgment.fact_checker import FactChecker  # noqa: E402
from src.writer.llm_client import LLMClient  # noqa: E402
from src.judgment.judgment_config import CFG  # noqa: E402


# ========================================================================
#  —— Loop 的可变配置（与 CFG 不可变的全局参数互补） ——
# ========================================================================

@dataclass
class LoopConfig:
    """**每会话可修改** 的运行参数（按 reset() 初始化）。"""
    provider: str = "mock"
    model: str = "mock-model"
    api_key: Optional[str] = None
    rounds: int = CFG.DEFAULT_ROUNDS
    max_evidence: int = CFG.DEFAULT_MAX_EVIDENCE
    enable_llm_review: bool = True
    enable_moderator: bool = True
    moderator_strictness: str = "normal"
    enable_t1_aebg: bool = True
    enable_t3_ks: bool = True
    enable_t4_ds: bool = True
    use_judge_v2: bool = False
    enable_fact_check: bool = False

    def to_kwargs(self) -> Dict[str, Any]:
        """转为 run_parajudge() 可接收的 kwargs。"""
        d = asdict(self)
        return d

    def dump_pretty(self) -> str:
        lines = []
        for k, v in asdict(self).items():
            v_repr = '"%s"' % v if isinstance(v, str) else v
            lines.append(f"    {k:24s} = {v_repr}")
        return "\n".join(lines)

    def apply_set(self, key: str, value: str) -> Tuple[bool, str]:
        """应用 `set key value`。返回 (是否成功, 消息)。"""
        key = key.strip().lower()
        if key not in asdict(self):
            return False, f"未知参数 '{key}'。用 `config` 查看支持的参数。"
        old = getattr(self, key)
        try:
            if isinstance(old, bool):
                if value.lower() in ("1", "true", "yes", "on"):
                    new = True
                elif value.lower() in ("0", "false", "no", "off"):
                    new = False
                else:
                    return False, f"布尔参数需 true/false，收到 '{value}'"
            elif isinstance(old, int):
                new = int(value)
            elif isinstance(old, float):
                new = float(value)
            else:
                new = value  # 默认字符串
            setattr(self, key, new)
            return True, f"{key}: {old} → {new}"
        except Exception as e:
            return False, f"设置失败: {e}"


# ========================================================================
#  —— 会话状态 ——
# ========================================================================

PHASES = [
    ("phase0", "Phase 0 · 证据构建", "构建问题相关证据包 (EvidenceBrief)"),
    ("phase1", "Phase 1 · 辩论",    "运行多轮辩论 (DebateTranscript)"),
    ("phase1.5", "Phase 1+ · 事实核查", "对论点做事实核查 (FactCheckReport)"),
    ("phase2", "Phase 2 · 审理",    "质量与矛盾检查 (ReviewReport)"),
    ("phase3", "Phase 3 · 裁决",    "五位法官评分 + 结论 (JudgmentResult)"),
]


@dataclass
class RunRecord:
    """单次运行记录，用于 compare / history。"""
    run_id: str
    problem: str
    winner: str
    pro_score: float
    con_score: float
    total_time: float
    config_snapshot: Dict[str, Any]
    output: Any  # FullPipelineOutput


class LoopState:
    """整个 REPL 的可变状态。"""

    def __init__(self, cfg: LoopConfig):
        self.cfg = cfg
        self.problem: Optional[str] = None

        # 逐步执行的中间产物
        self.brief = None
        self.transcript = None
        self.fact_check = None
        self.review = None
        self.judgment = None
        self.current_phase = 0  # 0=未开始, 1..5 对应 PHASES

        # 完整的 pipeline 输出（供 export / show 渲染）
        self.full_output: Optional[Any] = None

        # 历史运行列表（用于 compare）
        self.history: List[RunRecord] = []

    # ─── 工具 ─────────────────────────────────────────

    def require_problem(self) -> Optional[str]:
        """当前无问题时返回错误提示字符串，否则返回 None。"""
        if not self.problem:
            return "尚未设置问题。请先执行 `problem <你的问题文本>`。"
        return None

    def snapshot(self, output: Any) -> None:
        """将一次完整运行记入 history。"""
        winner = output.judgment.winner
        self.history.append(RunRecord(
            run_id=output.run_id,
            problem=self.problem or "(无问题)",
            winner=winner,
            pro_score=output.judgment.pro_final_score,
            con_score=output.judgment.con_final_score,
            total_time=output.total_time_sec,
            config_snapshot=asdict(self.cfg),
            output=output,
        ))
        # history 最多保留 20 条
        if len(self.history) > 20:
            self.history = self.history[-20:]

    def clear(self) -> None:
        """清空阶段中间结果，但保留配置和问题。"""
        self.brief = None
        self.transcript = None
        self.fact_check = None
        self.review = None
        self.judgment = None
        self.current_phase = 0
        self.full_output = None


# ========================================================================
#  —— 颜色 / 控制台工具 ——
# ========================================================================

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    @classmethod
    def wrap(cls, text: str, *codes: str) -> str:
        return "".join(codes) + text + cls.RESET


def banner() -> str:
    return C.wrap(
        "\n╔══════════════════════════════════════════════════════╗\n"
        "║   ParaJudge Loop v1.0 —— 交互式 REPL                  ║\n"
        "╚══════════════════════════════════════════════════════╝",
        C.BOLD, C.CYAN,
    ) + "\n" + C.wrap("  输入 help 查看命令；输入 quit 退出。", C.GRAY)


# ========================================================================
#  —— 逐步执行引擎（把 run_parajudge 的各阶段拆出来可单独调用） ——
# ========================================================================

def make_llm(cfg: LoopConfig) -> LLMClient:
    return LLMClient(provider=cfg.provider, model=cfg.model, api_key=cfg.api_key)


def do_phase0(state: LoopState) -> str:
    assert state.problem
    t0 = time.perf_counter()
    state.brief = build_evidence_brief(state.problem, max_papers=state.cfg.max_evidence)
    state.current_phase = max(state.current_phase, 1)
    return f"  耗时 {time.perf_counter() - t0:.2f}s · 证据 {state.brief.total_count} 条 · 关键词 {state.brief.query_terms}"


def do_phase1(state: LoopState) -> str:
    assert state.problem and state.brief
    cfg = state.cfg
    llm = make_llm(cfg)
    moderator = None
    if cfg.enable_moderator:
        try:
            strict_enum = ModeratorStrictness(cfg.moderator_strictness)
        except ValueError:
            strict_enum = ModeratorStrictness.NORMAL
        moderator = Moderator(config=ModeratorConfig(strictness=strict_enum), llm=llm)
    debater = SimpleDebate(llm, rounds=cfg.rounds, moderator=moderator)

    t0 = time.perf_counter()
    state.transcript = debater.run(state.problem, state.brief)
    state.current_phase = max(state.current_phase, 2)
    return (
        f"  耗时 {time.perf_counter() - t0:.2f}s · "
        f"辩论 {state.transcript.rounds_total} 轮 · "
        f"论点 {len(state.transcript.argument_index.arguments)} 个"
    )


def do_phase15_fact_check(state: LoopState) -> str:
    if not state.cfg.enable_fact_check:
        state.current_phase = max(state.current_phase, 3)
        return "  (未启用事实核查，跳过)"
    assert state.problem and state.transcript
    llm = make_llm(state.cfg)
    checker = FactChecker(llm)
    t0 = time.perf_counter()
    state.fact_check = checker.run(state.transcript, state.problem)
    state.current_phase = max(state.current_phase, 3)
    n = len(getattr(state.fact_check, "claims_checked", []) or [])
    return f"  耗时 {time.perf_counter() - t0:.2f}s · 核查 {n} 个主张"


def do_phase2(state: LoopState) -> str:
    assert state.problem and state.transcript
    llm = make_llm(state.cfg)
    reviewer = ReviewEngine(llm=llm, enable_llm_check=state.cfg.enable_llm_review)
    t0 = time.perf_counter()
    state.review = reviewer.run(state.transcript, state.brief)
    state.current_phase = max(state.current_phase, 4)
    return (
        f"  耗时 {time.perf_counter() - t0:.2f}s · "
        f"严重 {state.review.critical_count} · 警告 {state.review.warning_count}"
    )


def do_phase3(state: LoopState) -> str:
    assert state.problem and state.transcript and state.review
    llm = make_llm(state.cfg)
    judge = JudgmentEngine(llm, use_judge_v2=state.cfg.use_judge_v2)
    t0 = time.perf_counter()
    state.judgment = judge.run(state.transcript, state.brief, state.review)
    state.current_phase = max(state.current_phase, 5)

    # —— 可选: T4 双路融合 ——
    if state.cfg.enable_t4_ds:
        try:
            from src.judgment.innovation import (
                ds_evidence_fusion, ds_orthographic_combination,
            )
            heuristic = ds_evidence_fusion(state.judgment.judge_scores)
            ds_approx = ds_orthographic_combination(state.judgment.judge_scores)
            state.judgment._t4_heuristic = heuristic
            state.judgment._t4_ds_approx = ds_approx
            if state.judgment.uncertainties is None:
                state.judgment.uncertainties = []
            state.judgment.uncertainties.append(
                f"T4 启发式融合: {heuristic.get('interpretation', '')} "
                f"(confidence={heuristic.get('confidence', 0):.2f})"
            )
            state.judgment.uncertainties.append(
                f"T4 DS 正交和近似: {ds_approx.get('interpretation', '')} "
                f"(confidence={ds_approx.get('confidence', 0):.2f}, "
                f"K冲突={ds_approx.get('conflict_K', 0):.2f})"
            )
        except Exception as e:
            if state.judgment.uncertainties is None:
                state.judgment.uncertainties = []
            state.judgment.uncertainties.append(f"T4 融合失败: {e}")

    # —— 可选: T1 AEBG ——
    if state.cfg.enable_t1_aebg:
        try:
            from src.judgment.innovation import build_argument_evidence_bipartite
            aebg = build_argument_evidence_bipartite(state.transcript, state.brief)
            if state.transcript.moderator_report is None:
                state.transcript.moderator_report = {}
            state.transcript.moderator_report["t1_aebg"] = aebg
        except Exception:
            pass

    # —— 可选: T3 KS 早停 ——
    if state.cfg.enable_t3_ks:
        try:
            from src.judgment.innovation import ks_early_stop_check
            ks = ks_early_stop_check(state.transcript)
            if state.transcript.moderator_report is None:
                state.transcript.moderator_report = {}
            state.transcript.moderator_report["t3_ks"] = ks
        except Exception:
            pass

    t1 = time.perf_counter()
    return (
        f"  耗时 {t1 - t0:.2f}s · "
        f"胜者: {state.judgment.winner} · "
        f"正方 {state.judgment.pro_final_score:.1f} / 反方 {state.judgment.con_final_score:.1f}"
    )


# ========================================================================
#  —— 命令处理器 ——
# ========================================================================

Command = Callable[[LoopState, List[str]], Optional[str]]

COMMANDS: Dict[str, Tuple[str, str]] = {
    # cmd: (简要说明, 详细用法)
    "help":     ("显示帮助", "help / ?"),
    "problem":  ("设置辩论问题", "problem <文本>  或仅 `problem` 查看"),
    "set":      ("修改运行参数", "set <key> <value>。用 `config` 查看参数"),
    "config":   ("查看当前配置", "config"),
    "run":      ("执行完整 pipeline", "run"),
    "step":     ("逐步执行 / 跳阶段", "step [n]，n=0~3 对应 Phase 0..3"),
    "show":     ("查看某阶段结果", "show [evidence|debate|review|judgment|all]"),
    "compare":  ("对比两次运行", "compare <run_id_a> <run_id_b>"),
    "history":  ("列出现有运行记录", "history"),
    "export":   ("导出最近结果", "export <path> [json|md]"),
    "clear":    ("清空中间结果", "clear"),
    "quit":     ("退出", "quit / exit / Ctrl-D"),
}


def cmd_help(state: LoopState, args: List[str]) -> Optional[str]:
    lines = [C.wrap("  可用命令:", C.BOLD, C.CYAN)]
    for cmd, (brief, usage) in COMMANDS.items():
        lines.append(
            f"    {C.wrap(f'{cmd:10s}', C.BOLD, C.GREEN)} "
            f"{brief}  "
            f"{C.wrap(usage, C.GRAY)}"
        )
    lines.append("")
    lines.append(
        C.wrap("  典型流程:", C.BOLD, C.CYAN)
        + "\n"
        + C.wrap("    problem <问题文本>  →  show evidence  →  run  →  show judgment", C.GRAY)
    )
    return "\n".join(lines)


def cmd_problem(state: LoopState, args: List[str]) -> Optional[str]:
    if not args:
        if state.problem:
            return C.wrap(f"  当前问题: ", C.BOLD) + state.problem
        return C.wrap("  (未设置问题)", C.RED)
    text = " ".join(args)
    state.problem = text
    state.clear()  # 改了问题就重置各阶段结果
    return C.wrap(f"  ✓ 已设置问题 ({len(text)} 字)", C.GREEN) + "\n" + C.wrap(f"    {text}", C.GRAY)


def cmd_config(state: LoopState, args: List[str]) -> Optional[str]:
    lines = [C.wrap("  当前配置:", C.BOLD, C.CYAN)]
    lines.append(state.cfg.dump_pretty())
    lines.append("")
    lines.append(C.wrap(
        f"  (WINNER_THRESHOLD={CFG.WINNER_THRESHOLD}, "
        f"PENALTY_OFF_TOPIC={CFG.PENALTY_OFF_TOPIC}, "
        f"DEFAULT_ROUNDS={CFG.DEFAULT_ROUNDS})",
        C.GRAY,
    ))
    return "\n".join(lines)


def cmd_set(state: LoopState, args: List[str]) -> Optional[str]:
    if len(args) < 2:
        return C.wrap("  用法: set <key> <value>。用 `config` 查看 key 列表。", C.RED)
    key, value = args[0], " ".join(args[1:])
    ok, msg = state.cfg.apply_set(key, value)
    return C.wrap(f"  {msg}", C.GREEN if ok else C.RED)


def cmd_run(state: LoopState, args: List[str]) -> Optional[str]:
    err = state.require_problem()
    if err:
        return C.wrap(f"  {err}", C.RED)

    # 直接复用 orchestrator 的 run_parajudge 以保证行为一致
    print(C.wrap(f"  运行完整 pipeline（问题: {state.problem[:60]}...）", C.BOLD, C.CYAN))
    print(C.wrap(f"  provider={state.cfg.provider}, model={state.cfg.model}, "
                 f"rounds={state.cfg.rounds}, max_evidence={state.cfg.max_evidence}",
                 C.GRAY))
    try:
        t0 = time.perf_counter()
        output = run_parajudge(
            problem=state.problem,
            **state.cfg.to_kwargs(),
        )
        dt = time.perf_counter() - t0

        state.full_output = output
        state.brief = output.evidence_brief
        state.transcript = output.transcript
        state.fact_check = output.fact_check
        state.review = output.review
        state.judgment = output.judgment
        state.current_phase = 5

        # 记录到 history
        state.snapshot(output)

        print("")
        print(render_console(output))
        return C.wrap(f"\n  ✓ 完成 ({dt:.2f}s) · run_id={output.run_id}", C.GREEN)
    except Exception as e:
        return C.wrap(f"  ✗ 执行失败: {type(e).__name__}: {e}", C.RED)


def cmd_step(state: LoopState, args: List[str]) -> Optional[str]:
    err = state.require_problem()
    if err:
        return C.wrap(f"  {err}", C.RED)

    # 目标阶段: 默认是"当前阶段 +1"
    target = state.current_phase + 1
    if args:
        try:
            target = int(args[0]) + 1  # 用户输入 0 → phase0；输入 3 → phase3
        except ValueError:
            return C.wrap(f"  参数需是整数 0~3，收到 '{args[0]}'", C.RED)

    phases_exec = [
        (1, do_phase0, "Phase 0 · 证据构建"),
        (2, do_phase1, "Phase 1 · 辩论"),
        (3, do_phase15_fact_check, "Phase 1+ · 事实核查"),
        (4, do_phase2, "Phase 2 · 审理"),
        (5, do_phase3, "Phase 3 · 裁决"),
    ]

    out_lines = []
    for phase_idx, fn, title in phases_exec:
        if phase_idx > target:
            break
        if phase_idx <= state.current_phase:
            # 已执行过的阶段，跳过但显示状态
            out_lines.append(C.wrap(f"  [skip] {title}  (已执行过)", C.GRAY))
            continue

        print(C.wrap(f"  ▶ {title}", C.BOLD, C.CYAN), flush=True)
        try:
            msg = fn(state)
            print(C.wrap(msg, C.GREEN))
            out_lines.append(msg)
        except Exception as e:
            return C.wrap(f"  ✗ {title} 失败: {type(e).__name__}: {e}", C.RED)

    # 如果执行到了最后阶段，构造一个 minimal FullPipelineOutput 用于 history
    if state.current_phase >= 5 and state.full_output is None:
        try:
            from backend.models.schemas import FullPipelineOutput
            state.full_output = FullPipelineOutput(
                run_id=f"step-{int(time.time())}",
                problem=state.problem or "",
                evidence_brief=state.brief,
                transcript=state.transcript,
                fact_check=state.fact_check,
                review=state.review,
                judgment=state.judgment,
                total_time_sec=0.0,
            )
            state.snapshot(state.full_output)
        except Exception:
            pass
    return C.wrap(f"\n  已到达阶段 {state.current_phase}", C.GREEN)


def cmd_show(state: LoopState, args: List[str]) -> Optional[str]:
    target = "".join(args).lower() if args else "all"

    if target == "evidence":
        return _show_evidence(state)
    if target == "debate":
        return _show_debate(state)
    if target == "review":
        return _show_review(state)
    if target == "judgment":
        return _show_judgment(state)
    if target == "all":
        parts = [
            _show_evidence(state),
            _show_debate(state),
            _show_review(state),
            _show_judgment(state),
        ]
        return "\n\n".join(p for p in parts if p)
    return C.wrap(f"  未知目标: {target}。可用 evidence / debate / review / judgment / all", C.RED)


def _show_evidence(state: LoopState) -> str:
    if state.brief is None:
        return C.wrap("  [evidence] (暂无 —— 还没跑 Phase 0)", C.GRAY)
    b = state.brief
    lines = [
        C.wrap("  ── 证据包 (Phase 0) ──", C.BOLD, C.CYAN),
        f"  关键词: {b.query_terms}",
        f"  总条数: {b.total_count} · 构建耗时 {b.build_time_sec}s",
        "",
    ]
    items = getattr(b, "items", []) or []
    for i, item in enumerate(items[:10]):
        title = getattr(item, "title", "(无标题)")
        score = getattr(item, "relevance_score", None)
        tag = "支持" if getattr(item, "support", None) == "pro" else ("反方" if getattr(item, "support", None) == "con" else "")
        score_str = f"score={score:.2f} " if isinstance(score, float) else ""
        lines.append(f"    [{i+1:2d}] {score_str}{tag} {title[:80]}")
    if len(items) > 10:
        lines.append(f"    ... 还有 {len(items) - 10} 条")
    return "\n".join(lines)


def _show_debate(state: LoopState) -> str:
    if state.transcript is None:
        return C.wrap("  [debate] (暂无 —— 还没跑 Phase 1)", C.GRAY)
    t = state.transcript
    lines = [
        C.wrap("  ── 辩论记录 (Phase 1) ──", C.BOLD, C.CYAN),
        f"  总轮数: {t.rounds_total} · 论点数: {len(t.argument_index.arguments)}",
        "",
    ]
    args = t.argument_index.arguments
    for i, a in enumerate(args):
        side_icon = C.wrap("🟦 PRO", C.BLUE, C.BOLD) if a.side == "pro" else C.wrap("🟥 CON", C.RED, C.BOLD)
        content = (a.content or "").replace("\n", " ")
        lines.append(
            f"    R{a.round_index} · {side_icon} · {content[:140]}"
            + ("..." if len(content) > 140 else "")
        )
    if t.moderator_report:
        mr = t.moderator_report
        if isinstance(mr, dict):
            lines.append("")
            lines.append(C.wrap("  主持人备注:", C.GRAY))
            for n in mr.get("notes", [])[:5]:
                lines.append(f"    - [{n.get('action', '?')}] {n.get('message', '')[:80]}")
    return "\n".join(lines)


def _show_review(state: LoopState) -> str:
    if state.review is None:
        return C.wrap("  [review] (暂无 —— 还没跑 Phase 2)", C.GRAY)
    r = state.review
    lines = [
        C.wrap("  ── 审理报告 (Phase 2) ──", C.BOLD, C.CYAN),
        f"  严重问题: {r.critical_count} · 警告: {r.warning_count}",
        "",
    ]
    for issue in (r.issues or [])[:8]:
        tag = "❌" if issue.severity == "critical" else "⚠"
        lines.append(f"    {tag} [{issue.issue_type}] {issue.description[:100]}")
    if (r.issues or []).__len__() > 8:
        lines.append(f"    ... (共 {len(r.issues)} 条)")
    return "\n".join(lines)


def _show_judgment(state: LoopState) -> str:
    if state.judgment is None:
        return C.wrap("  [judgment] (暂无 —— 还没跑 Phase 3)", C.GRAY)
    j = state.judgment
    winner_label = {"pro": C.wrap("正方胜出", C.BLUE, C.BOLD),
                    "con": C.wrap("反方胜出", C.RED, C.BOLD),
                    "tie": C.wrap("平局", C.YELLOW, C.BOLD)}.get(j.winner, j.winner)
    lines = [
        C.wrap("  ── 裁决结果 (Phase 3) ──", C.BOLD, C.CYAN),
        f"  胜者: {winner_label}",
        f"  分数: 正方 {j.pro_final_score:.1f}  vs  反方 {j.con_final_score:.1f}",
        "",
        C.wrap("  五位法官评分:", C.GRAY),
    ]
    for js in j.judge_scores:
        lines.append(
            f"    {C.wrap(js.judge_name, C.BOLD):12s}  "
            f"正方 {js.pro_score:>5.1f} / 反方 {js.con_score:>5.1f} · "
            f"{C.wrap((js.reasoning or '')[:60], C.GRAY)}"
        )
    if j.key_points_pro:
        lines.append("")
        lines.append(C.wrap("  正方关键论点:", C.GRAY))
        for p in j.key_points_pro[:4]:
            lines.append(f"    · {p[:100]}")
    if j.key_points_con:
        lines.append("")
        lines.append(C.wrap("  反方关键论点:", C.GRAY))
        for p in j.key_points_con[:4]:
            lines.append(f"    · {p[:100]}")
    if j.uncertainties:
        lines.append("")
        lines.append(C.wrap("  不确定性:", C.YELLOW))
        for u in j.uncertainties:
            lines.append(f"    ⚠ {u}")
    return "\n".join(lines)


def cmd_history(state: LoopState, args: List[str]) -> Optional[str]:
    if not state.history:
        return C.wrap("  (暂无历史运行)", C.GRAY)
    lines = [C.wrap(f"  {'#':>3}  {'run_id':10s}  {'winner':8s}  pro   con    time  problem",
                    C.BOLD, C.CYAN)]
    for i, rec in enumerate(state.history):
        lines.append(
            f"  {i:3d}  {rec.run_id:10s}  {rec.winner:8s}  "
            f"{rec.pro_score:5.1f} {rec.con_score:5.1f}  "
            f"{rec.total_time:6.2f}s  "
            + C.wrap(rec.problem[:60], C.GRAY)
        )
    return "\n".join(lines)


def cmd_compare(state: LoopState, args: List[str]) -> Optional[str]:
    if len(args) < 2:
        return C.wrap("  用法: compare <run_id_a> <run_id_b>。用 `history` 查看 run_id 列表", C.RED)
    a_id, b_id = args[0], args[1]

    def find(rid: str) -> Optional[RunRecord]:
        for r in state.history:
            if r.run_id.startswith(rid):
                return r
        return None

    a, b = find(a_id), find(b_id)
    if a is None or b is None:
        return C.wrap(f"  未找到 run_id '{a_id}' 或 '{b_id}'", C.RED)

    # —— 维度对比 ——
    j_a = a.output.judgment
    j_b = b.output.judgment
    lines = [
        C.wrap(f"  对比 {a.run_id} vs {b.run_id}", C.BOLD, C.CYAN),
        f"    问题 A: {a.problem[:80]}" + ("..." if len(a.problem) > 80 else ""),
        f"    问题 B: {b.problem[:80]}" + ("..." if len(b.problem) > 80 else ""),
        "",
        f"    {'维度':20s} {'A (' + a.run_id + ')':>14s}   {'B (' + b.run_id + ')':>14s}   Δ",
        f"    {'─'*20} {'─'*14}   {'─'*14}   {'─'*8}",
    ]

    def row(name: str, va: Any, vb: Any, is_float: bool = True):
        if is_float:
            try:
                delta = float(vb) - float(va)
                sign = "+" if delta > 0 else ""
                return f"    {name:20s} {va:>14.2f}   {vb:>14.2f}   {sign}{delta:.2f}"
            except (TypeError, ValueError):
                pass
        return f"    {name:20s} {str(va):>14s}   {str(vb):>14s}   -"

    lines.append(row("最终正方分数", j_a.pro_final_score, j_b.pro_final_score))
    lines.append(row("最终反方分数", j_a.con_final_score, j_b.con_final_score))
    lines.append(row("胜者", j_a.winner, j_b.winner, is_float=False))
    lines.append(row("总耗时 (s)", a.total_time, b.total_time))
    lines.append(row("辩论轮数", a.output.transcript.rounds_total, b.output.transcript.rounds_total))
    lines.append(row("证据条数", a.output.evidence_brief.total_count,
                     b.output.evidence_brief.total_count))

    # 法官层面的对比
    scores_a = {js.judge_name: (js.pro_score, js.con_score) for js in j_a.judge_scores}
    scores_b = {js.judge_name: (js.pro_score, js.con_score) for js in j_b.judge_scores}
    if scores_a and scores_b:
        lines.append("")
        lines.append(C.wrap("    法官评分差异 (pro_B - pro_A):", C.GRAY))
        for name in scores_a:
            if name in scores_b:
                pro_a, _ = scores_a[name]
                pro_b, _ = scores_b[name]
                diff = pro_b - pro_a
                arrow = "↗" if diff > 5 else ("↘" if diff < -5 else "→")
                lines.append(f"      {name:14s} {pro_a:6.1f} → {pro_b:6.1f}  Δ{diff:+5.1f} {arrow}")

    # 配置差异
    cfg_a, cfg_b = a.config_snapshot, b.config_snapshot
    diff_keys = [k for k in cfg_a if cfg_a[k] != cfg_b.get(k)]
    if diff_keys:
        lines.append("")
        lines.append(C.wrap("    配置差异:", C.GRAY))
        for k in diff_keys:
            lines.append(f"      {k}: {cfg_a[k]} → {cfg_b[k]}")
    return "\n".join(lines)


def cmd_export(state: LoopState, args: List[str]) -> Optional[str]:
    if len(args) < 1:
        return C.wrap("  用法: export <path> [json|md]。默认 md。", C.RED)
    if state.full_output is None:
        return C.wrap("  尚未有运行结果，无法导出。先执行 `run` 或完整 `step`。", C.RED)

    path = args[0]
    fmt = args[1].lower() if len(args) > 1 else "md"

    try:
        if fmt == "json":
            # 用默认 dict 化方式（dataclass 对象可能需要手动展开）
            obj = {
                "run_id": state.full_output.run_id,
                "problem": state.full_output.problem,
                "winner": state.full_output.judgment.winner,
                "pro_final_score": state.full_output.judgment.pro_final_score,
                "con_final_score": state.full_output.judgment.con_final_score,
                "judge_scores": [
                    {"judge": js.judge_name, "pro": js.pro_score, "con": js.con_score,
                     "reasoning": js.reasoning}
                    for js in state.full_output.judgment.judge_scores
                ],
                "key_points_pro": state.full_output.judgment.key_points_pro,
                "key_points_con": state.full_output.judgment.key_points_con,
                "uncertainties": state.full_output.judgment.uncertainties,
                "total_time_sec": state.full_output.total_time_sec,
                "config": asdict(state.cfg),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            text = render_console(state.full_output)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        size = os.path.getsize(path)
        return C.wrap(f"  ✓ 已导出 ({fmt}) {path} ({size} bytes)", C.GREEN)
    except Exception as e:
        return C.wrap(f"  ✗ 导出失败: {type(e).__name__}: {e}", C.RED)


def cmd_clear(state: LoopState, args: List[str]) -> Optional[str]:
    state.clear()
    return C.wrap("  ✓ 已清空中间结果（问题和配置保留）", C.GREEN)


def cmd_quit(state: LoopState, args: List[str]) -> Optional[str]:
    return "__QUIT__"


# 命令 → 处理器映射
HANDLERS: Dict[str, Command] = {
    "help": cmd_help,
    "?": cmd_help,
    "problem": cmd_problem,
    "config": cmd_config,
    "set": cmd_set,
    "run": cmd_run,
    "step": cmd_step,
    "show": cmd_show,
    "history": cmd_history,
    "compare": cmd_compare,
    "export": cmd_export,
    "clear": cmd_clear,
    "quit": cmd_quit,
    "exit": cmd_quit,
}


# ========================================================================
#  —— 主循环 ——
# ========================================================================

def parse_command(line: str) -> Tuple[str, List[str]]:
    """`set rounds 3` → ('set', ['rounds', '3'])。空行 → ('', [])。"""
    tokens = line.strip().split()
    if not tokens:
        return "", []
    return tokens[0].lower(), tokens[1:]


def main_loop(initial_cfg: LoopConfig, initial_problem: Optional[str]) -> None:
    state = LoopState(initial_cfg)
    if initial_problem:
        state.problem = initial_problem

    print(banner())

    # 启动提示
    print(C.wrap("  启动参数:", C.GRAY))
    print(state.cfg.dump_pretty())
    print("")
    if state.problem:
        print(C.wrap(f"  已预置问题: ", C.GREEN) + state.problem)
    else:
        print(C.wrap("  尚未设置问题。试试: problem AI 是否会大规模失业?", C.YELLOW))
    print()

    while True:
        try:
            prompt = C.wrap(
                f"\n[parajudge {state.current_phase}/5] ",
                C.BOLD, C.MAGENTA,
            ) + C.wrap("▶ ", C.BOLD, C.CYAN)
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            print(C.wrap("  再见 👋", C.GRAY))
            break

        cmd, args = parse_command(line)
        if cmd == "":
            continue
        handler = HANDLERS.get(cmd)
        if handler is None:
            print(C.wrap(f"  未知命令 '{cmd}'。输入 help 查看命令列表。", C.RED))
            continue
        try:
            result = handler(state, args)
        except Exception as e:
            print(C.wrap(f"  ✗ 命令执行异常: {type(e).__name__}: {e}", C.RED))
            continue

        if result == "__QUIT__":
            print(C.wrap("  再见 👋", C.GRAY))
            break
        if result is not None:
            print(result)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ParaJudge Loop —— 交互式 REPL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--provider", default="mock", help="LLM 提供商 mock/ollama/dashscope/openai")
    p.add_argument("--model", default="mock-model", help="具体模型名")
    p.add_argument("--api-key", default=None, help="API Key（Ollama 可留空）")
    p.add_argument("--rounds", type=int, default=CFG.DEFAULT_ROUNDS, help="辩论轮数")
    p.add_argument("--max-evidence", type=int, default=CFG.DEFAULT_MAX_EVIDENCE, help="最大证据数")
    p.add_argument("--problem", default=None, help="预设辩论问题（省略则进入交互设置）")
    p.add_argument("--no-color", action="store_true", help="禁用 ANSI 颜色")
    return p


if __name__ == "__main__":
    args = build_argparser().parse_args()

    # 禁用颜色
    if args.no_color or not sys.stdout.isatty():
        for name in list(vars(C).keys()):
            setattr(C, name, "")

    # 初始化配置
    loop_cfg = LoopConfig(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        rounds=args.rounds,
        max_evidence=args.max_evidence,
    )

    main_loop(loop_cfg, args.problem)
