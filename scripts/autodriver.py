#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ParaJudge AutoDriver —— 自主驱动的迭代开发引擎。

将 "迭代改进 ParaJudge" 这个任务本身自动化：
    ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌─────────┐
    │ Assess   │ → │ Decide   │ → │ Execute   │ → │ Record  │
    │ 评估系统 │   │ 决策动作 │   │ 运行实验/ │   │ 生成报告│
    │ 状态     │   │ (优先级) │   │ 提案/检测 │   │ 生成Δ报告│
    └──────────┘   └──────────┘   └───────────┘   └─────────┘
          ↑                                ↓
          └──────────循环到无 P0 问题或达最大轮数┘

用法:
    python scripts/autodriver.py start --max-iterations 1
    python scripts/autodriver.py status
    # 或从 Loop 中调用: (parajudge) ▶ auto/start
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# 允许从项目根目录运行
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.iteration import (  # noqa: E402
    Issue, IssueTracker, ExperimentTracker, IterSession,
)

DATA_DIR = os.path.join(PROJECT_ROOT, ".parajudge")
ITERATION_DIR = os.path.join(DATA_DIR, "iterations")
LATEST_DIR = os.path.join(DATA_DIR, "latest")


# ========================================================================
#  —— 工具函数
# ========================================================================

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_dirs() -> None:
    for d in [DATA_DIR, ITERATION_DIR]:
        os.makedirs(d, exist_ok=True)


def _banner(title: str) -> str:
    return "\n" + "=" * 70 + "\n  " + title + "\n" + "=" * 70


# ========================================================================
#  —— 1. SystemProfiler —— 系统状态快照
# ========================================================================

@dataclass
class SystemSnapshot:
    version: str
    timestamp: float
    issue_stats: Dict[str, Any]
    open_issues_by_priority: Dict[str, List[str]]
    experiment_count: int
    recent_experiments: List[Dict[str, Any]]
    source_stats: Dict[str, Any]
    module_health: List[Dict[str, Any]]
    warnings: List[str]
    suggestions: List[str]
    overall_health_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "datetime": _now_str(),
            "issue_stats": self.issue_stats,
            "open_issues_by_priority": self.open_issues_by_priority,
            "experiment_count": self.experiment_count,
            "recent_experiments": self.recent_experiments,
            "source_stats": self.source_stats,
            "module_health": self.module_health,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "overall_health_score": round(self.overall_health_score, 2),
        }


class SystemProfiler:

    CORE_MODULES: List[Tuple[str, str]] = [
        ("judgment_engine", "src/judgment/judgment_engine.py"),
        ("innovation", "src/judgment/innovation.py"),
        ("moderator", "src/debate/moderator.py"),
        ("simple_debate", "src/debate/simple_debate.py"),
        ("orchestrator", "src/orchestration/orchestrator.py"),
        ("evidence_builder", "src/debate/evidence_builder.py"),
        ("judgment_config", "src/judgment/judgment_config.py"),
        ("prompts", "src/debate/prompts.py"),
    ]

    def __init__(self, version: str = "v0.1"):
        self.version = version

    def profile(self) -> SystemSnapshot:
        warnings: List[str] = []
        tracker = IssueTracker()
        stats = tracker.stats()

        open_by_priority: Dict[str, List[str]] = {"P0": [], "P1": [], "P2": [], "P3": []}
        for issue in tracker.list(status="open"):
            pri = issue.priority
            if pri in open_by_priority:
                open_by_priority[pri].append(f"{issue.id} [{issue.category}] {issue.title}")

        exp_tracker = ExperimentTracker()
        recent = []
        for e in exp_tracker.latest(5):
            recent.append({
                "exp_id": e.exp_id, "run_id": e.run_id,
                "problem": e.problem[:60], "metrics": e.metrics,
                "config": e.config, "timestamp": e.timestamp,
            })

        source_stats = self._scan_source()
        module_health: List[Dict[str, Any]] = []
        for name, rel_path in self.CORE_MODULES:
            module_health.append(self._module_health(name, rel_path, warnings))

        health = self._compute_overall_health(stats, module_health, warnings)
        suggestions = self._generate_suggestions(stats, module_health, health)

        return SystemSnapshot(
            version=self.version,
            timestamp=time.time(),
            issue_stats=stats,
            open_issues_by_priority=open_by_priority,
            experiment_count=len(exp_tracker.experiments),
            recent_experiments=recent,
            source_stats=source_stats,
            module_health=module_health,
            warnings=warnings,
            suggestions=suggestions,
            overall_health_score=health,
        )

    # ── 内部 ───────────────────────────────────────────────────

    def _scan_source(self) -> Dict[str, Any]:
        total_files = 0
        total_lines = 0
        total_comment_lines = 0
        todos = 0
        fixmes = 0
        max_line_file = ("", 0)

        src_root = os.path.join(PROJECT_ROOT, "src")
        if not os.path.isdir(src_root):
            return {"files": 0, "total_lines": 0, "comment_rate": 0.0,
                    "todos": 0, "fixmes": 0, "biggest_file": "", "biggest_file_lines": 0}

        for root, _dirs, files in os.walk(src_root):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                path = os.path.join(root, fname)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                total_files += 1
                lcount = len(lines)
                total_lines += lcount
                if lcount > max_line_file[1]:
                    max_line_file = (os.path.relpath(path, PROJECT_ROOT), lcount)
                for line in lines:
                    s = line.strip()
                    if s.startswith("#"):
                        total_comment_lines += 1
                    if "TODO" in s:
                        todos += 1
                    if "FIXME" in s:
                        fixmes += 1

        return {
            "files": total_files,
            "total_lines": total_lines,
            "comment_rate": round(total_comment_lines / total_lines, 3) if total_lines else 0,
            "todos": todos,
            "fixmes": fixmes,
            "biggest_file": max_line_file[0],
            "biggest_file_lines": max_line_file[1],
        }

    def _module_health(self, name: str, rel_path: str, warnings: List[str]) -> Dict[str, Any]:
        path = os.path.join(PROJECT_ROOT, rel_path)
        result: Dict[str, Any] = {"module": name, "path": rel_path, "exists": False}

        if not os.path.exists(path):
            warnings.append(f"模块缺失: {rel_path}")
            result["health_score"] = 0.0
            return result

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            warnings.append(f"无法读取 {rel_path}: {e}")
            result["health_score"] = 0.0
            return result

        lines = content.split("\n")
        line_count = len(lines)
        todo_count = len(re.findall(r"TODO", content))
        fixme_count = len(re.findall(r"FIXME", content))

        # 检测 magic number
        magic_hits = 0
        sample_hits: List[str] = []
        if name != "judgment_config":
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith("#") or not s:
                    continue
                if re.search(r"(>|<|==|!=)\s*\d{2,3}\b", line):
                    magic_hits += 1
                    if len(sample_hits) < 3:
                        sample_hits.append(f"L{i}: {s[:60]}")
                if magic_hits >= 10:
                    break

        score = 100.0
        score -= todo_count * 2.0
        score -= fixme_count * 5.0
        score -= magic_hits * 3.0
        if line_count > 800:
            score -= 10.0
        score = max(0.0, min(100.0, score))

        if magic_hits > 3:
            warnings.append(f"{name}: {magic_hits} 处疑似 magic number ("
                            + ", ".join(sample_hits) + ")")
        if fixme_count > 0:
            warnings.append(f"{name}: 有 {fixme_count} 个 FIXME 标记")

        result.update({
            "exists": True, "line_count": line_count,
            "todo_count": todo_count, "fixme_count": fixme_count,
            "magic_number_hits": magic_hits,
            "health_score": round(score, 2),
        })
        return result

    def _compute_overall_health(
        self, stats: Dict[str, Any],
        module_health: List[Dict[str, Any]],
        warnings: List[str],
    ) -> float:
        score = 100.0
        score -= stats.get("open", 0) * 5.0
        score -= stats.get("by_priority", {}).get("P0", 0) * 15.0
        score -= stats.get("by_priority", {}).get("P1", 0) * 8.0
        valid = [m["health_score"] for m in module_health if m.get("exists")]
        if valid:
            avg_h = sum(valid) / len(valid)
            score = score * 0.4 + avg_h * 0.6
        score -= len(warnings) * 0.5
        return max(0.0, min(100.0, score))

    def _generate_suggestions(
        self, stats: Dict[str, Any],
        module_health: List[Dict[str, Any]],
        health: float,
    ) -> List[str]:
        out: List[str] = []
        p0 = stats.get("by_priority", {}).get("P0", 0)
        if p0 > 0:
            out.append(f"⚠ {p0} 个 P0 级开放问题，优先处理。")
        low_modules = [m for m in module_health if m.get("exists") and m["health_score"] < 70]
        for m in low_modules:
            out.append(f"⚠ 模块 {m['module']} 健康度 {m['health_score']:.0f}/100。")
        if stats.get("experiment_count", 0) == 0:
            out.append("📊 尚未做任何实验。建议先建立 baseline。")
        return out


# ========================================================================
#  —— 2. IssuePrioritizer —— 问题优先级决策器
# ========================================================================


@dataclass
class ActionItem:
    order: int
    kind: str  # "fix_issue" | "run_experiment" | "generate_patch" | "refactor"
    title: str
    target_id: Optional[str] = None
    priority: str = "P2"
    rationale: str = ""
    expected_effort: str = "small"  # small | medium | large

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "kind": self.kind,
            "title": self.title,
            "target_id": self.target_id,
            "priority": self.priority,
            "rationale": self.rationale,
            "expected_effort": self.expected_effort,
        }


class IssuePrioritizer:
    """将系统快照 + 问题列表 → 排序后的动作清单。"""

    CRITICAL_OPEN_QUESTIONS: List[Dict[str, Any]] = [
        {
            "id": "CORE-Q-TRUTH-01",
            "title": "辩论胜负是否能逼近真理（vs 地心说vs日心说问题）",
            "rationale": "系统可能因为法官共识偏向流行但错误观点而输出错误结论。",
            "experiment": "belief_alignment_bias_test",
            "priority": "P0",
        },
        {
            "id": "CORE-Q-REBUTTAL-01",
            "title": "反驳机制是否真能检测论点不相交的情形",
            "rationale": "关键词重叠过于粗糙，可能遗漏语义相关但措辞不同的反驳。",
            "experiment": "rebuttal_coverage_sweep",
            "priority": "P0",
        },
        {
            "id": "CORE-Q-STAT-01",
            "title": "多轮重复是否降低统计检验 I 类错误（假阳性）",
            "rationale": "重复越多越容易偶然通过 t 检验，需多重比较校正（Bonferroni / Holm）。",
            "experiment": "multiple_comparison_control",
            "priority": "P1",
        },
        {
            "id": "CORE-Q-DS-01",
            "title": "DS 正交和近似的有效性 vs 真正 Dempster's rule",
            "rationale": "目前实现为近似正交和，需量化与真实 Dempster 组合规则的差异。",
            "experiment": "ds_approximation_gap",
            "priority": "P1",
        },
    ]

    def __init__(self, snapshot: SystemSnapshot, tracker: IssueTracker):
        self.snapshot = snapshot
        self.tracker = tracker

    def decide(self, max_actions: int = 6) -> List[ActionItem]:
        actions: List[ActionItem] = []
        order = 1

        # 1) P0 级 open issue → fix_issue + generate_patch
        for pri in ("P0", "P1"):
            for title in self.snapshot.open_issues_by_priority.get(pri, []):
                if order > max_actions:
                    break
                issue_id = title.split(" ", 1)[0]
                actions.append(ActionItem(
                    order=order, kind="fix_issue",
                    title=f"修复 {pri} 问题: {title[:60]}",
                    target_id=issue_id, priority=pri,
                    rationale="开放问题优先级驱动",
                    expected_effort="medium",
                ))
                order += 1
            if order > max_actions:
                break

        # 2) 核心科研问题（CORE-Q-*）→ 每个安排一次实验
        if self.snapshot.experiment_count < 3 or self.snapshot.overall_health_score < 80:
            for q in self.CRITICAL_OPEN_QUESTIONS:
                if order > max_actions:
                    break
                actions.append(ActionItem(
                    order=order, kind="run_experiment",
                    title=q["title"], target_id=q["id"],
                    priority=q["priority"],
                    rationale=q["rationale"],
                    expected_effort="large",
                ))
                order += 1

        # 3) 若没有任何实验 → 建立 baseline
        if self.snapshot.experiment_count == 0 and order <= max_actions:
            actions.append(ActionItem(
                order=order, kind="run_experiment",
                title="Baseline 辩论实验（mock 模式）", target_id="baseline-mock",
                priority="P1", rationale="系统尚无任何实验，需建立基线。",
                expected_effort="small",
            ))
            order += 1

        # 4) 低健康度模块 → refactor
        for m in self.snapshot.module_health:
            if order > max_actions:
                break
            if m.get("exists") and m.get("health_score", 100) < 70:
                actions.append(ActionItem(
                    order=order, kind="refactor",
                    title=f"重构模块 {m['module']}（健康度 {m['health_score']}）",
                    target_id=m["path"], priority="P2",
                    rationale="低健康度模块可能含隐藏 bug",
                    expected_effort="medium",
                ))
                order += 1

        # 5) 保证至少有 generate_patch
        if any(a.kind == "fix_issue" for a in actions) and order <= max_actions:
            actions.append(ActionItem(
                order=order, kind="generate_patch",
                title="生成代码修复提案（.md 格式，非侵入式）",
                target_id=None, priority="P2",
                rationale="将高优先级问题沉淀为可审查的补丁提案",
                expected_effort="small",
            ))
            order += 1

        return actions


# ========================================================================
#  —— 3. ExperimentPlanner —— 实验规划与执行
# ========================================================================


@dataclass
class PlannedExperiment:
    key: str
    title: str
    priority: str
    config_overrides: Dict[str, Any]
    expected_observations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "priority": self.priority,
            "config_overrides": self.config_overrides,
            "expected_observations": self.expected_observations,
        }


class ExperimentPlanner:
    """规划并运行针对核心问题的实验（mock 模式，避免依赖 LLM）。"""

    BASELINE_PROBLEMS: List[str] = [
        "人工智能是否会导致大规模失业",
        "城市是否应该禁止燃油车",
        "远程办公是否应该成为主流",
    ]

    def __init__(self, session_factory=None):
        # 允许注入 IterSession 工厂，便于测试
        self._session_factory = session_factory or self._default_session_factory

    @staticmethod
    def _default_session_factory(problem: str, version: str):
        from scripts.iteration import IterSession
        return IterSession(problem=problem, version=version)

    def plan(self, snapshot: SystemSnapshot) -> List[PlannedExperiment]:
        plans: List[PlannedExperiment] = []

        if snapshot.experiment_count == 0:
            plans.append(PlannedExperiment(
                key="baseline-mock",
                title="Baseline mock 实验（默认 3 轮）",
                priority="P1",
                config_overrides={"rounds": 3, "max_evidence": 10},
                expected_observations=[
                    "pro/con 评分应接近对称（70/70 基线上浮动）",
                    "DS confidence 在无争议问题上应高于高争议问题",
                    "total_time 应在合理范围（< 30s，mock 下）",
                ],
            ))

        plans.append(PlannedExperiment(
            key="belief_alignment_bias_test",
            title="信念对齐偏差测试 — 模拟共识偏向伪结论",
            priority="P0",
            config_overrides={"rounds": 3, "max_evidence": 8, "enable_t4_ds": True},
            expected_observations=[
                "对争议问题，DS confidence 应下降（表示存在冲突证据）",
                "在 3 轮重复后，胜负随机波动，不应系统性偏向一方",
            ],
        ))

        plans.append(PlannedExperiment(
            key="rebuttal_coverage_sweep",
            title="反驳覆盖率扫掠 — 不同关键词重叠阈值",
            priority="P0",
            config_overrides={"rounds": 3, "max_evidence": 10},
            expected_observations=[
                "第 2/3 轮应记录 rebuttal_stats（WARN_NO_REBUTTAL 或 反驳有效）",
                "整体至少有 1 轮反驳被记录",
            ],
        ))

        return plans

    def run_all(self, planned: List[PlannedExperiment], version: str = "auto-v0.1") -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for p in planned:
            problem = self.BASELINE_PROBLEMS[hash(p.key) % len(self.BASELINE_PROBLEMS)]
            try:
                session = self._session_factory(problem=problem, version=version)
                record = session.run_experiment(
                    config_overrides=p.config_overrides,
                    notes=f"[autodriver:{p.key}] {p.title}",
                )
                results.append({
                    "key": p.key, "title": p.title,
                    "success": True, "run_id": record.run_id,
                    "problem": record.problem, "metrics": record.metrics,
                    "expected_observations": p.expected_observations,
                })
            except Exception as e:
                results.append({
                    "key": p.key, "title": p.title,
                    "success": False, "error": repr(e),
                    "expected_observations": p.expected_observations,
                })
        return results


# ========================================================================
#  —— 4. PatchProposalGenerator —— 生成非侵入式修复提案
# ========================================================================


class PatchProposalGenerator:
    """基于 open issue 与 module 健康度，生成 Markdown 格式的 *提案* 文件。

    注意：本生成器**不直接修改源码**；它输出的是供人审查的设计/补丁文档。
    这样可以避免错误自动化把系统弄坏，同时便于版本管理。
    """

    def __init__(self, snapshot: SystemSnapshot, actions: List[ActionItem]):
        self.snapshot = snapshot
        self.actions = actions

    def generate(self, out_dir: str, version: str) -> str:
        issues_lines: List[str] = []
        for pri in ("P0", "P1"):
            for title in self.snapshot.open_issues_by_priority.get(pri, []):
                issues_lines.append(f"- **[{pri}]** {title}")

        modules_lines: List[str] = []
        for m in self.snapshot.module_health:
            if not m.get("exists"):
                modules_lines.append(f"- ⚠ {m['module']}: 缺失（path={m['path']}）")
                continue
            modules_lines.append(
                f"- {m['module']}（{m['path']}）"
                + f" 健康度 {m.get('health_score')},"
                + f" TODO={m.get('todo_count')},"
                + f" FIXME={m.get('fixme_count')},"
                + f" magic_number_hits={m.get('magic_number_hits')}"
            )

        actions_lines: List[str] = []
        for a in self.actions:
            actions_lines.append(
                f"{a.order}. **[{a.priority}]** ({a.kind}) {a.title}"
                + (f" — target={a.target_id}" if a.target_id else "")
            )

        body = _md_quote(
            f"# AutoDriver · 迭代修复提案 {version}\n\n"
            f"- 生成时间: {_now_str()}\n"
            f"- 整体健康度: **{self.snapshot.overall_health_score:.2f}/100**\n"
            f"- 开放问题数: **{self.snapshot.issue_stats.get('open', 0)}**\n\n"
            f"## 1. 核心开放问题\n"
            + ("\n".join(issues_lines) if issues_lines else "- (暂无开放问题) ✅")
            + "\n\n"
            "## 2. 模块健康度扫描\n"
            + ("\n".join(modules_lines) if modules_lines else "- (无模块信息)")
            + "\n\n"
            "## 3. 本轮建议动作\n"
            + ("\n".join(actions_lines) if actions_lines else "- (暂无动作)")
            + "\n\n"
            "## 4. 修复方向（高层建议，需人工审查）\n"
            "\n"
            "1. **真理 vs 共识偏差**：辩论胜负 ≠ 真理。系统需：\n"
            "   - 在高争议问题上降低 DS confidence\n"
            "   - 记录并对比多轮辩论的胜负稳定性\n"
            "   - 暴露法官 panel 的内部分歧（而非只输出一个胜者）\n"
            "2. **反驳机制强度**：关键词重叠是下限。下一步：\n"
            "   - 引入语义嵌入相似度（sentence-transformers 或 LLM embed）\n"
            "   - 记录每一轮被反驳的论点索引，便于人工核查\n"
            "3. **统计多重比较校正**：若同一问题重复 N 次辩论，使用 Holm/Bonferroni 调整\n"
            "4. **DS 近似正交和**：建议在 .parajudge/metrics 里记录完整的 mass 表，而非仅最终置信度\n"
            "\n"
            "> 本文件为 AutoDriver 自动生成的非侵入式提案，\n"
            "> **不修改源码**，请人工审查后再决定是否落地。\n"
        )

        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"patch-proposal-{version}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path


def _md_quote(text: str) -> str:
    """确保文件内容在 Windows/Linux 下都可读（避免奇怪缩进）。"""
    return text.strip() + "\n"


# ========================================================================
#  —— 5. DeltaReporter —— 生成 Δ 迭代报告
# ========================================================================


class DeltaReporter:
    """整合系统快照 + 动作清单 + 实验结果 → Markdown 报告。"""

    def __init__(
        self,
        snapshot: SystemSnapshot,
        actions: List[ActionItem],
        experiments: List[Dict[str, Any]],
        proposal_path: str,
    ):
        self.snapshot = snapshot
        self.actions = actions
        self.experiments = experiments
        self.proposal_path = proposal_path

    def render(self, version: str) -> str:
        s = self.snapshot
        lines: List[str] = []
        lines.append(f"# ParaJudge AutoDriver Δ 报告 · {version}")
        lines.append("")
        lines.append(f"- 生成时间: {_now_str()}")
        lines.append(f"- 系统版本: {s.version}")
        lines.append(f"- 整体健康度: **{s.overall_health_score:.2f}/100**")
        lines.append("")

        lines.append("## 1. 系统快照")
        lines.append("")
        lines.append(f"- 代码文件数: {s.source_stats.get('files', 0)}")
        lines.append(f"- 总代码行: {s.source_stats.get('total_lines', 0)}")
        lines.append(f"- 注释率: {s.source_stats.get('comment_rate', 0)}")
        lines.append(f"- TODO/FIXME: {s.source_stats.get('todos', 0)}/{s.source_stats.get('fixmes', 0)}")
        lines.append(f"- 问题总数: {s.issue_stats.get('total', 0)}（open={s.issue_stats.get('open', 0)}, fixed={s.issue_stats.get('fixed', 0)}）")
        lines.append(f"- 累计实验数: {s.experiment_count}")
        lines.append("")

        if s.warnings:
            lines.append("### Warnings")
            for w in s.warnings:
                lines.append(f"- {w}")
            lines.append("")

        if s.suggestions:
            lines.append("### Suggestions")
            for sg in s.suggestions:
                lines.append(f"- {sg}")
            lines.append("")

        lines.append("## 2. 模块健康度")
        for m in s.module_health:
            lines.append(
                f"- {m['module']}: "
                + (f"健康度 {m.get('health_score')}, lines={m.get('line_count')}, "
                   f"todo={m.get('todo_count')}, fixme={m.get('fixme_count')}, "
                   f"magic={m.get('magic_number_hits')}"
                   if m.get("exists") else "**缺失**")
            )
        lines.append("")

        lines.append("## 3. 本轮建议动作（Action Plan）")
        for a in self.actions:
            lines.append(f"{a.order}. **[{a.priority}]** ({a.kind}) {a.title}")
            if a.rationale:
                lines.append(f"   - Rationale: {a.rationale}")
            if a.target_id:
                lines.append(f"   - Target: {a.target_id}")
        lines.append("")

        lines.append("## 4. 实验结果")
        if not self.experiments:
            lines.append("- (本轮无实验)")
        for e in self.experiments:
            lines.append(f"### {e.get('key', '?')}: {e.get('title', '')}")
            if not e.get("success"):
                lines.append(f"- ❌ 失败: {e.get('error')}")
            else:
                m = e.get("metrics", {})
                lines.append(f"- run_id: `{e.get('run_id')}`")
                lines.append(f"- problem: {e.get('problem')}")
                lines.append(f"- winner: {m.get('winner')}")
                lines.append(f"- pro_score: {m.get('pro_score')} | con_score: {m.get('con_score')}")
                lines.append(f"- rounds: {m.get('rounds')} | time: {m.get('total_time')}s")
            obs = e.get("expected_observations", [])
            if obs:
                lines.append("- Expected observations:")
                for o in obs:
                    lines.append(f"  - {o}")
            lines.append("")

        lines.append("## 5. 修复提案")
        lines.append(f"- 文件: `{self.proposal_path}`")
        lines.append("")
        lines.append("---")
        lines.append(f"_本报告由 `scripts/autodriver.py` 自动生成。_")

        return "\n".join(lines)


# ========================================================================
#  —— 6. AutoDriver —— 顶层控制器
# ========================================================================


class AutoDriver:
    """自主驱动的迭代控制器：Assess → Decide → Execute → Record（循环）。"""

    def __init__(self, version: str = "auto-v0.1"):
        self.version = version
        _ensure_dirs()

    def run_once(self) -> Dict[str, Any]:
        """执行一轮迭代，返回结构化结果。"""
        result: Dict[str, Any] = {
            "version": self.version,
            "started_at": _now_str(),
            "steps": {},
        }
        try:
            print(_banner(f"AutoDriver iteration {self.version}"))

            # ── Step 1: Assess ──
            print("  [1/4] Assess · 系统状态快照…", flush=True)
            profiler = SystemProfiler(version=self.version)
            snapshot = profiler.profile()
            result["steps"]["assess"] = snapshot.to_dict()
            print(f"        健康度 = {snapshot.overall_health_score:.2f}/100, "
                  f"open_issues = {snapshot.issue_stats.get('open', 0)}, "
                  f"experiments = {snapshot.experiment_count}")

            # ── Step 2: Decide ──
            print("  [2/4] Decide · 生成动作清单…", flush=True)
            tracker = IssueTracker()
            prioritizer = IssuePrioritizer(snapshot, tracker)
            actions = prioritizer.decide(max_actions=6)
            result["steps"]["decide"] = [a.to_dict() for a in actions]
            print(f"        共 {len(actions)} 个动作")

            # ── Step 3: Execute ──
            print("  [3/4] Execute · 运行规划实验 & 生成提案…", flush=True)
            planner = ExperimentPlanner()
            planned = planner.plan(snapshot)
            experiments = planner.run_all(planned, version=self.version)
            result["steps"]["experiments"] = experiments

            pp_gen = PatchProposalGenerator(snapshot, actions)
            proposal_path = pp_gen.generate(ITERATION_DIR, self.version)
            result["steps"]["proposal"] = proposal_path
            print(f"        提案文件 -> {os.path.relpath(proposal_path, PROJECT_ROOT)}")

            # ── Step 4: Record ──
            print("  [4/4] Record · 生成 Δ 报告…", flush=True)
            reporter = DeltaReporter(snapshot, actions, experiments, proposal_path)
            md_text = reporter.render(self.version)
            report_path = os.path.join(ITERATION_DIR, f"delta-report-{self.version}.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(md_text)

            json_path = os.path.join(ITERATION_DIR, f"iter-{self.version}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 记录 latest 指针
            latest_path = os.path.join(DATA_DIR, "latest.json")
            with open(latest_path, "w", encoding="utf-8") as f_latest:
                json.dump({
                    "report": os.path.relpath(report_path, DATA_DIR),
                    "proposal": os.path.relpath(proposal_path, DATA_DIR),
                    "iter_json": os.path.relpath(json_path, DATA_DIR),
                    "version": self.version,
                    "datetime": _now_str(),
                }, f_latest, ensure_ascii=False, indent=2)

            result["steps"]["record"] = {
                "report_path": report_path,
                "proposal_path": proposal_path,
                "json_path": json_path,
            }
            print(f"        Δ 报告   -> {os.path.relpath(report_path, PROJECT_ROOT)}")

            result["ok"] = True
        except Exception as e:
            result["ok"] = False
            result["error"] = repr(e)
            result["traceback"] = traceback.format_exc()
            err_path = os.path.join(ITERATION_DIR, f"error-{self.version}.txt")
            with open(err_path, "w", encoding="utf-8") as f:
                f.write(result["traceback"])
            print(f"  ❌ 迭代失败，已写入 {err_path}: {e}")

        return result


# ========================================================================
#  —— 7. CLI 入口
# ========================================================================


def _print_status() -> None:
    profiler = SystemProfiler(version="status")
    snapshot = profiler.profile()
    print(_banner("System Status"))
    print(f"  version: {snapshot.version}")
    print(f"  datetime: {_now_str()}")
    print(f"  overall_health: {snapshot.overall_health_score:.2f}/100")
    print(f"  files={snapshot.source_stats.get('files')}, "
          f"lines={snapshot.source_stats.get('total_lines')}, "
          f"comment_rate={snapshot.source_stats.get('comment_rate')}")
    print(f"  issues: {snapshot.issue_stats}")
    print(f"  experiments: {snapshot.experiment_count}")
    if snapshot.warnings:
        print("\n  Warnings:")
        for w in snapshot.warnings:
            print(f"    - {w}")
    if snapshot.suggestions:
        print("\n  Suggestions:")
        for s in snapshot.suggestions:
            print(f"    - {s}")

    latest_json = os.path.join(DATA_DIR, "latest.json")
    if os.path.exists(latest_json):
        try:
            with open(latest_json, "r", encoding="utf-8") as f:
                info = json.load(f)
            print(f"\n  最新一次迭代: {info.get('version')} @ {info.get('datetime')}")
            print(f"    报告 = {info.get('report')}")
            print(f"    提案 = {info.get('proposal')}")
        except Exception:
            pass


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(
            "ParaJudge AutoDriver — 自主驱动的科研迭代引擎\n"
            "\n"
            "用法:\n"
            "  python scripts/autodriver.py start [--max-iterations N] [--version v]\n"
            "  python scripts/autodriver.py status\n"
            "  python scripts/autodriver.py detect\n"
            "\n"
            "示例:\n"
            "  python scripts/autodriver.py start --max-iterations 1 --version auto-v0.1\n"
        )
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "status":
        _print_status()
        return 0

    if cmd == "detect":
        from scripts.iteration import AutoDetector
        results = AutoDetector.detect()
        print(_banner("AutoDetector"))
        if not results:
            print("  ✅ 未命中内置问题模式")
            return 0
        for r in results:
            print(f"  [{r.get('priority')}] [{r.get('category')}] {r.get('description')}")
        return 0

    if cmd == "start":
        max_iter = 1
        version = None
        i = 0
        while i < len(rest):
            if rest[i] == "--max-iterations" and i + 1 < len(rest):
                try:
                    max_iter = int(rest[i + 1])
                except ValueError:
                    print(f"  ❌ --max-iterations 需要整数: {rest[i+1]}")
                    return 2
                i += 2
            elif rest[i] == "--version" and i + 1 < len(rest):
                version = rest[i + 1]
                i += 2
            else:
                i += 1

        for it_idx in range(1, max(max_iter, 1) + 1):
            v = version or f"auto-v{it_idx:02d}"
            print(_banner(f"迭代 {it_idx}/{max_iter} · {v}"))
            driver = AutoDriver(version=v)
            out = driver.run_once()
            if not out.get("ok"):
                print(f"  迭代 {it_idx} 失败，停止继续。错误: {out.get('error')}")
                return 1
        print("\n✅ AutoDriver 全部迭代完成。执行 `python scripts/autodriver.py status` 查看。")
        return 0

    print(f"  ❌ 未知命令: {cmd}\n  运行 `python scripts/autodriver.py --help` 查看帮助。")
    return 2


if __name__ == "__main__":
    sys.exit(main())
