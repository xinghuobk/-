#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ParaJudge AutoDriver —— 自主驱动的科研迭代引擎（7 步循环）。

    ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌───────────┐
    │ Assess   │ → │ Reflect  │ → │  Search    │ → │  Creative │
    │ 系统快照 │   │ 自我反思 │   │ 外部检索   │   │  Planner  │
    └──────────┘   └──────────┘   └────────────┘   └────┬──────┘
                                                         ↓
    ┌──────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Record  │ ← │ CodeEditor│ ← │  Execute  │ ← │ (cont)    │
    │ 生成Δ报告│   │ 代码修改  │   │ 运行实验  │   │           │
    └──────────┘   └───────────┘   └───────────┘   └───────────┘

循环终止条件：达到 max-iterations 或连续两轮“无新增问题 + 无新增实验”。

用法（常用场景）：
    python scripts/autodriver.py start --max-iterations 1
    python scripts/autodriver.py start --max-iterations 3 --version auto-v2 \
        --provider ollama --model qwen2.5:7b --search --auto-apply
    python scripts/autodriver.py status
    python scripts/autodriver.py detect
    python scripts/autodriver.py clean
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.iteration import IssueTracker  # noqa: E402

# 新模块（self-reflection / search / creative-planning / code-editor）
from scripts.autodriver_agents import (  # noqa: E402
    LLMConfig, LLMHelper,
    SearchProvider, SearchResult,
    Reflector,
    CreativePlanner, CreativePlan,
    CodeEditor, PatchSpec,
)

DATA_DIR = os.path.join(PROJECT_ROOT, ".parajudge")
ITERATION_DIR = os.path.join(DATA_DIR, "iterations")


# ========================================================================
# 工具函数
# ========================================================================

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _banner(title: str) -> str:
    return "\n" + "=" * 70 + "\n  " + title + "\n" + "=" * 70


# ========================================================================
# 1. SystemProfiler —— 系统状态快照（保留原实现，略做压缩）
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
    CORE_MODULES: List[str] = [
        "src/judgment/judgment_engine.py",
        "src/judgment/judgment_config.py",
        "src/debate/moderator.py",
        "src/debate/simple_debate.py",
        "src/debate/prompts.py",
        "src/debate/evidence_builder.py",
        "src/orchestration/orchestrator.py",
        "src/writer/llm_client.py",
    ]

    def __init__(self, version: str = "dev"):
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

        try:
            from scripts.iteration import ExperimentTracker
            exp_tracker = ExperimentTracker()
            recent = [
                {"exp_id": e.exp_id, "run_id": e.run_id, "problem": e.problem[:60],
                 "metrics": e.metrics, "config": e.config, "timestamp": e.timestamp}
                for e in exp_tracker.latest(5)
            ]
            experiment_count = len(exp_tracker.experiments)
        except Exception:
            recent = []
            experiment_count = 0

        source_stats = self._scan_source()
        module_health = self._module_health(warnings)
        health = self._compute_overall_health(stats, module_health, warnings)
        suggestions = self._suggestions(stats, module_health, health)

        return SystemSnapshot(
            version=self.version,
            timestamp=time.time(),
            issue_stats=stats,
            open_issues_by_priority=open_by_priority,
            experiment_count=experiment_count,
            recent_experiments=recent,
            source_stats=source_stats,
            module_health=module_health,
            warnings=warnings,
            suggestions=suggestions,
            overall_health_score=health,
        )

    # internals
    def _scan_source(self) -> Dict[str, Any]:
        src_root = os.path.join(PROJECT_ROOT, "src")
        if not os.path.isdir(src_root):
            return {"files": 0, "total_lines": 0, "comment_rate": 0.0,
                    "todos": 0, "fixmes": 0, "biggest_file": "", "biggest_file_lines": 0}
        files = 0
        lines = 0
        comments = 0
        todos = 0
        fixmes = 0
        biggest_rel = ""
        biggest_lines = 0
        for root, _, fnames in os.walk(src_root):
            for fn in fnames:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.readlines()
                except Exception:
                    continue
                files += 1
                lines += len(content)
                if len(content) > biggest_lines:
                    biggest_lines = len(content)
                    biggest_rel = os.path.relpath(path, PROJECT_ROOT)
                for line in content:
                    s = line.lstrip()
                    if s.startswith("#"):
                        comments += 1
                    if "TODO" in s:
                        todos += 1
                    if "FIXME" in s:
                        fixmes += 1
        return {
            "files": files, "total_lines": lines,
            "comment_rate": round(comments / max(1, lines), 3),
            "todos": todos, "fixmes": fixmes,
            "biggest_file": biggest_rel, "biggest_file_lines": biggest_lines,
        }

    def _module_health(self, warnings: List[str]) -> List[Dict[str, Any]]:
        results = []
        for rel in self.CORE_MODULES:
            entry: Dict[str, Any] = {"module": rel, "exists": False}
            abs_path = os.path.join(PROJECT_ROOT, rel)
            if not os.path.exists(abs_path):
                warnings.append(f"模块缺失: {rel}")
                entry["health_score"] = 0.0
                results.append(entry)
                continue
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception as e:
                warnings.append(f"无法读取 {rel}: {e}")
                entry["health_score"] = 0.0
                results.append(entry)
                continue
            todo_cnt = sum(1 for l in lines if "TODO" in l)
            fixme_cnt = sum(1 for l in lines if "FIXME" in l)
            magic_hits = sum(1 for l in lines if re.search(r"(>|<|==|!=)\s*\d{2,3}\b", l))
            score = 100.0
            score -= todo_cnt * 2.0
            score -= fixme_cnt * 5.0
            score -= magic_hits * 3.0
            if len(lines) > 800:
                score -= 10.0
            score = max(0.0, min(100.0, score))
            if magic_hits > 3:
                warnings.append(f"{rel}: {magic_hits} 处疑似 magic number")
            if fixme_cnt > 0:
                warnings.append(f"{rel}: 有 {fixme_cnt} 个 FIXME 标记")
            entry.update({"exists": True, "lines": len(lines),
                          "todo_count": todo_cnt, "fixme_count": fixme_cnt,
                          "magic_number_hits": magic_hits,
                          "health_score": round(score, 2)})
            results.append(entry)
        return results

    def _compute_overall_health(
        self, stats: Dict[str, Any],
        module_health: List[Dict[str, Any]], warnings: List[str],
    ) -> float:
        score = 100.0
        score -= stats.get("open", 0) * 5.0
        score -= stats.get("by_priority", {}).get("P0", 0) * 15.0
        score -= stats.get("by_priority", {}).get("P1", 0) * 8.0
        valid = [m.get("health_score", 0.0) for m in module_health if m.get("exists")]
        if valid:
            avg_h = sum(valid) / len(valid)
            score = score * 0.4 + avg_h * 0.6
        score -= len(warnings) * 0.5
        return max(0.0, min(100.0, score))

    def _suggestions(
        self, stats: Dict[str, Any],
        module_health: List[Dict[str, Any]], health: float,
    ) -> List[str]:
        out: List[str] = []
        if stats.get("by_priority", {}).get("P0", 0) > 0:
            out.append("⚠ 存在 P0 级开放问题，优先处理")
        low = [m for m in module_health if m.get("exists") and m.get("health_score", 100) < 70]
        for m in low:
            out.append(f"模块 {m.get('module')}: 健康度 {m.get('health_score')}")
        if stats.get("experiment_count", 0) == 0:
            out.append("尚未做任何实验，建议建立基线 baseline")
        return out


# ========================================================================
# 2. IssuePrioritizer —— 问题优先级排序 & 输出动作清单（保留原实现，简化）
# ========================================================================

@dataclass
class ActionItem:
    order: int
    kind: str
    title: str
    target_id: Optional[str] = None
    priority: str = "P2"
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order, "kind": self.kind,
            "title": self.title, "target_id": self.target_id,
            "priority": self.priority, "rationale": self.rationale,
        }


class IssuePrioritizer:
    def __init__(self, snapshot: SystemSnapshot, tracker: IssueTracker):
        self.snapshot = snapshot
        self.tracker = tracker

    def decide(self, max_actions: int = 6) -> List[ActionItem]:
        actions: List[ActionItem] = []
        order = 1
        # P0/P1 open issues → fix_issue
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
                ))
                order += 1
            if order > max_actions:
                break
        # 如果实验数不足，建议 baseline
        if self.snapshot.experiment_count == 0 and order <= max_actions:
            actions.append(ActionItem(
                order=order, kind="run_experiment",
                title="Baseline 辩论实验（mock 模式）",
                target_id="baseline-mock", priority="P1",
                rationale="系统尚无任何实验，先建立基线",
            ))
            order += 1
        return actions


# ========================================================================
# 3. 实验执行器 —— 调用 IterSession.run_experiment，供多个上层使用
# ========================================================================

def _run_iter_session_experiment(
    problem: str, config_overrides: Dict[str, Any], notes: str,
) -> Optional[Dict[str, Any]]:
    """调用 scripts.iteration.IterSession.run_experiment 跑一次辩论。

    返回：{'key': str, 'title': str, 'metrics': dict, 'run_id': str,
           'problem': str, 'notes': str, 'success': True/False, 'error': str}"""
    try:
        from scripts.iteration import IterSession
        session = IterSession(problem=problem, version="autodriver")
        record = session.run_experiment(config_overrides=dict(config_overrides or {}),
                                       notes=notes)
        return {
            "success": True,
            "key": config_overrides.get("experiment_key", "experiment"),
            "title": config_overrides.get("experiment_title", notes or "experiment"),
            "run_id": record.run_id,
            "problem": record.problem,
            "metrics": record.metrics,
            "notes": notes,
        }
    except Exception as e:
        return {
            "success": False, "error": repr(e),
            "problem": problem, "notes": notes,
            "metrics": {}, "run_id": "unknown",
            "key": config_overrides.get("experiment_key", "experiment") if config_overrides else "experiment",
            "title": config_overrides.get("experiment_title", notes) if config_overrides else notes,
        }


def run_creative_experiments(
    plan: CreativePlan, snapshot: SystemSnapshot, version: str,
    default_problems: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """按 CreativePlan 跑实验；每一个 experiment 会在 3 个不同问题上各跑一次，观察稳定性。"""
    problems = default_problems or [
        "AI 是否会导致大规模失业？",
        "城市是否应禁止燃油车？",
        "远程办公是否应成为主流？",
    ]
    results: List[Dict[str, Any]] = []
    # 为保证可复现，用 hash 决定问题映射
    for idx, exp in enumerate(plan.experiments):
        key = exp.get("key") or f"exp_{idx}"
        title = exp.get("title") or f"实验 {idx}"
        cfg = exp.get("config_overrides") or {}
        problem = problems[abs(hash(key)) % len(problems)]
        notes = f"[autodriver:{version}/{key}] {title}"
        result = _run_iter_session_experiment(problem, cfg, notes)
        if result is None:
            continue
        # 保留 key/title，其他字段由 run_experiment 产出
        result["key"] = key
        result["title"] = title
        results.append(result)
    return results


# ========================================================================
# 4. AutoDriver —— 顶层控制器（7 步循环）
# ========================================================================

class AutoDriver:
    """七步主控制器：Assess → Reflect → Search → CreativePlan → Execute → CodeEditor → Record"""

    def __init__(
        self,
        version: str = "auto-v0.1",
        llm_cfg: Optional[LLMConfig] = None,
        enable_search: bool = False,
        auto_apply: bool = False,
    ):
        self.version = version
        self.llm_cfg = llm_cfg or LLMConfig()
        self.enable_search = enable_search
        self.auto_apply = auto_apply
        os.makedirs(ITERATION_DIR, exist_ok=True)

    def run_once(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"version": self.version,
                                  "started_at": _now_str(), "steps": {}}
        t0 = time.time()
        try:
            print(_banner(f"AutoDriver iteration {self.version}"))

            # ── 1. Assess ──
            print("  [1/7] Assess · 系统状态快照…", flush=True)
            snapshot = SystemProfiler(version=self.version).profile()
            result["steps"]["assess"] = snapshot.to_dict()
            print(f"        健康度 = {snapshot.overall_health_score:.2f}/100, "
                  f"open_issues = {snapshot.issue_stats.get('open', 0)}, "
                  f"experiments = {snapshot.experiment_count}")

            # ── 2. Reflect ──
            print("  [2/7] Reflect · 自我反思（读上一轮实验结果）…", flush=True)
            llm = LLMHelper(cfg=self.llm_cfg)
            reflector = Reflector(llm=llm)
            prev_report = _read_latest_report()
            reflection = reflector.reflect(
                snapshot_dict=snapshot.to_dict(),
                experiments=snapshot.recent_experiments,
                previous_report=prev_report,
            )
            result["steps"]["reflection"] = reflection
            print(f"        摘要: {reflection.get('summary')}")
            print(f"        焦点: {reflection.get('next_iteration_focus')}")

            # ── 3. Search ──
            hits: List[SearchResult] = []
            if self.enable_search:
                queries = list(reflection.get("search_queries") or [])
                if not queries:
                    queries = ["debate judgment evaluation", "dempster-shafer", "rebuttal detection"]
                print(f"  [3/7] Search · 外部检索（{len(queries)} 个关键词）…", flush=True)
                searcher = SearchProvider(llm=llm, enabled=True)
                hits = searcher.search(queries, max_per_query=2)
                print(f"        命中 {len(hits)} 条记录")
            else:
                print("  [3/7] Search · 未启用（--search 可开启），使用内置离线摘要")
                searcher = SearchProvider(llm=llm, enabled=False)
                queries = ["debate", "rebuttal", "multiple"]
                hits = searcher.search(queries, max_per_query=2)
            result["steps"]["search"] = [h.to_dict() for h in hits]

            # ── 4. CreativePlanner ──
            print("  [4/7] CreativePlanner · 设计本轮实验（由反思+检索驱动）…", flush=True)
            planner = CreativePlanner(llm=llm)
            default_cfg = {
                "rounds": 3,
                "max_evidence": 8,
                "provider": self.llm_cfg.provider,
                "model": self.llm_cfg.model,
            }
            plan = planner.plan(reflection=reflection,
                                snapshot_dict=snapshot.to_dict(),
                                default_cfg=default_cfg)
            result["steps"]["plan"] = plan.to_dict()
            print(f"        共 {len(plan.experiments)} 个实验，搜索关键词: {len(plan.search_queries)}")

            # ── 5. Execute ──
            print("  [5/7] Execute · 运行规划的实验…", flush=True)
            experiments = run_creative_experiments(
                plan=plan, snapshot=snapshot, version=self.version,
            )
            # 同时跑 IssuePrioritizer 动作（用于报告展示）
            tracker = IssueTracker()
            prioritizer = IssuePrioritizer(snapshot=snapshot, tracker=tracker)
            actions = prioritizer.decide(max_actions=6)
            result["steps"]["experiments"] = experiments
            result["steps"]["actions"] = [a.to_dict() for a in actions]
            succ = sum(1 for e in experiments if e.get("success"))
            print(f"        {succ}/{len(experiments)} 个实验成功")

            # ── 6. CodeEditor ──
            print("  [6/7] CodeEditor · 生成代码修改提案"
                  + ("（--auto-apply 已开启，自动落盘）" if self.auto_apply else "（仅提案，不落盘）")
                  + "…", flush=True)
            editor = CodeEditor(llm=llm, auto_apply=self.auto_apply)
            patches_input = list(reflection.get("code_patches") or [])
            # 保证每个 patch 有 target_file/description/rationale
            for p in patches_input:
                p.setdefault("rationale", reflection.get("next_iteration_focus", ""))
            patches = editor.generate_and_maybe_apply(
                specs_input=patches_input, version=self.version,
                out_dir=ITERATION_DIR, search_hits=hits,
            )
            result["steps"]["patches"] = [p.to_dict() for p in patches]
            applied = sum(1 for p in patches if p.auto_applied)
            print(f"        共 {len(patches)} 个 patch 提案，自动落盘 {applied} 个")

            # ── 7. Record ──
            print("  [7/7] Record · 生成 Δ 报告与结构化 JSON…", flush=True)
            report_path = _write_delta_report(
                version=self.version, snapshot=snapshot,
                reflection=reflection, plan=plan, experiments=experiments,
                patches=patches, hits=hits,
            )
            json_path = os.path.join(ITERATION_DIR, f"iter-{self.version}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            # latest 指针
            _write_latest_pointer(report_path=report_path,
                                  json_path=json_path,
                                  version=self.version,
                                  search_hits=hits,
                                  proposal_count=len(patches))
            result["steps"]["record"] = {
                "report_path": os.path.relpath(report_path, PROJECT_ROOT),
                "json_path": os.path.relpath(json_path, PROJECT_ROOT),
                "search_hit_count": len(hits),
                "patch_count": len(patches),
                "auto_apply": self.auto_apply,
            }
            print(f"        Δ 报告 -> {os.path.relpath(report_path, PROJECT_ROOT)}")
            print(f"        JSON    -> {os.path.relpath(json_path, PROJECT_ROOT)}")

            result["ok"] = True
        except Exception as e:
            result["ok"] = False
            result["error"] = repr(e)
            result["traceback"] = traceback.format_exc()
            err_path = os.path.join(ITERATION_DIR, f"error-{self.version}.txt")
            try:
                with open(err_path, "w", encoding="utf-8") as f:
                    f.write(result["traceback"])
                print(f"  ❌ 迭代失败，已写入 {os.path.relpath(err_path, PROJECT_ROOT)}: {e}")
            except Exception:
                print(f"  ❌ 迭代失败，且无法写入日志: {e}")

        result["duration_sec"] = round(time.time() - t0, 2)
        return result


# ========================================================================
# 5. 报告 & 指针文件工具
# ========================================================================

def _read_latest_report() -> str:
    path = os.path.join(DATA_DIR, "latest.json")
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        report_rel = data.get("report")
        if not report_rel:
            return ""
        abs_path = os.path.join(DATA_DIR, report_rel)
        if not os.path.exists(abs_path):
            return ""
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()[:2000]
    except Exception:
        return ""


def _write_delta_report(
    version: str, snapshot: SystemSnapshot, reflection: Dict[str, Any],
    plan: CreativePlan, experiments: List[Dict[str, Any]],
    patches: List[PatchSpec], hits: List[SearchResult],
) -> str:
    lines: List[str] = []
    lines.append(f"# ParaJudge AutoDriver Δ 报告 · {version}")
    lines.append("")
    lines.append(f"- 生成时间: {_now_str()}")
    lines.append(f"- 系统版本: {snapshot.version}")
    lines.append(f"- 整体健康度: **{snapshot.overall_health_score:.2f}/100**")
    lines.append(f"- 本轮实验数: {len(experiments)}")
    lines.append(f"- 本轮 patch 数: {len(patches)}")
    lines.append(f"- 外部检索命中: {len(hits)}")
    lines.append("")

    # 1. 系统快照
    lines.append("## 1. 系统快照")
    lines.append(f"- 源码文件: {snapshot.source_stats.get('files')}")
    lines.append(f"- 总代码行: {snapshot.source_stats.get('total_lines')}")
    lines.append(f"- 注释率: {snapshot.source_stats.get('comment_rate')}")
    lines.append(f"- TODO/FIXME: {snapshot.source_stats.get('todos')}/{snapshot.source_stats.get('fixmes')}")
    lines.append(f"- 问题总数: {snapshot.issue_stats.get('total')}"
                 f" (open={snapshot.issue_stats.get('open', 0)}"
                 f" fixed={snapshot.issue_stats.get('fixed', 0)})")
    lines.append(f"- 累计实验: {snapshot.experiment_count}")
    if snapshot.warnings:
        lines.append("")
        lines.append("**Warnings**:")
        for w in snapshot.warnings:
            lines.append(f"- {w}")
    if snapshot.suggestions:
        lines.append("")
        lines.append("**Suggestions**:")
        for s in snapshot.suggestions:
            lines.append(f"- {s}")
    lines.append("")

    # 2. 模块健康度
    lines.append("## 2. 模块健康度")
    for m in snapshot.module_health:
        if m.get("exists"):
            lines.append(f"- `{m.get('module')}`: 健康度 {m.get('health_score')}, "
                         f"lines={m.get('lines')}, TODO={m.get('todo_count')}, "
                         f"FIXME={m.get('fixme_count')}, magic={m.get('magic_number_hits')}")
        else:
            lines.append(f"- ❌ `{m.get('module')}`: 缺失")
    lines.append("")

    # 3. 反思
    lines.append("## 3. 自我反思")
    lines.append(f"- summary: {reflection.get('summary')}")
    lines.append(f"- next_iteration_focus: **{reflection.get('next_iteration_focus')}**")
    for k, vv in [("strengths", "优势"), ("weaknesses", "弱点")]:
        values = reflection.get(k) or []
        if values:
            lines.append(f"- {vv}:" + "; ".join(f"{v}" for v in values[:5]))
    priorities = reflection.get("priorities") or []
    if priorities:
        lines.append("")
        lines.append("### 反思优先级建议")
        for p in priorities[:6]:
            if isinstance(p, dict):
                lines.append(f"- [{p.get('effort','?')}] "
                             f"**{p.get('title','?')}** — {p.get('rationale','')}")
            else:
                lines.append(f"- {p}")
    lines.append("")

    # 4. 检索命中
    lines.append("## 4. 外部检索")
    if hits:
        for h in hits[:10]:
            lines.append(f"- [{h.source}] **{h.title}** — {h.snippet[:120]} ({h.url})")
    else:
        lines.append("- （本轮无检索命中；可用 --search 开启）")
    lines.append("")

    # 5. 实验
    lines.append("## 5. 实验结果")
    if experiments:
        for i, e in enumerate(experiments, 1):
            lines.append(f"### {i}. `{e.get('key')}` — {e.get('title')}")
            if not e.get("success"):
                lines.append(f"- ❌ failed: {e.get('error')}")
            else:
                m = e.get("metrics") or {}
                lines.append(f"- run_id: `{e.get('run_id')}`")
                lines.append(f"- problem: {e.get('problem')}")
                lines.append(f"- winner: {m.get('winner')}")
                lines.append(f"- pro_score: {m.get('pro_score')} / con_score: {m.get('con_score')}")
                lines.append(f"- rounds: {m.get('rounds')} / total_time: {m.get('total_time')}s")
            lines.append("")
    else:
        lines.append("- （本轮未跑实验）")
    lines.append("")

    # 6. patch
    lines.append("## 6. 代码修改提案")
    if patches:
        for p in patches:
            if p.auto_applied:
                mark = "✅ 已应用"
            else:
                mark = "📄 仅提案"
            lines.append(f"- {mark} `{p.target_file}`: {p.description}"
                         + (f" — {p.rationale[:60]}" if p.rationale else ""))
    else:
        lines.append("- （本轮无 patch 提案）")
    lines.append("")

    lines.append("---")
    lines.append(f"_由 scripts.autodriver.AutoDriver 于 {_now_str()} 生成_")
    report_path = os.path.join(ITERATION_DIR, f"delta-report-{version}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


def _write_latest_pointer(
    report_path: str, json_path: str, version: str,
    search_hits: List[SearchResult], proposal_count: int,
) -> str:
    data = {
        "version": version,
        "datetime": _now_str(),
        "report": os.path.relpath(report_path, DATA_DIR),
        "iter_json": os.path.relpath(json_path, DATA_DIR),
        "search_hit_count": len(search_hits),
        "proposal_count": proposal_count,
    }
    path = os.path.join(DATA_DIR, "latest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# ========================================================================
# 6. CLI
# ========================================================================

def _print_status() -> None:
    profiler = SystemProfiler(version="status")
    snapshot = profiler.profile()
    print(_banner("System Status"))
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
            print(f"\n  最近一次迭代: {info.get('version')} @ {info.get('datetime')}")
            print(f"    报告 = {info.get('report')}")
            print(f"    JSON = {info.get('iter_json')}")
            print(f"    检索命中 = {info.get('search_hit_count')}, patch 提案 = {info.get('proposal_count')}")
        except Exception:
            pass
    else:
        print("  (尚未跑过任何迭代，使用 `scripts/autodriver.py start` 开始)")


def _print_detect() -> None:
    from scripts.iteration import AutoDetector
    print(_banner("AutoDetector"))
    results = AutoDetector.detect()
    if not results:
        print("  ✅ 未命中内置问题模式")
        return
    for r in results:
        print(f"  [{r.get('priority', '?')}] [{r.get('category', '?')}] "
              f"{r.get('description', '')[:120]}")


def _print_clean(dry_run: bool) -> None:
    print(_banner("Clean"))
    targets = []
    if os.path.isdir(ITERATION_DIR):
        for name in os.listdir(ITERATION_DIR):
            targets.append(os.path.join(ITERATION_DIR, name))
    latest = os.path.join(DATA_DIR, "latest.json")
    if os.path.exists(latest):
        targets.append(latest)
    if not targets:
        print("  (无需清理)")
        return
    for t in targets:
        rel = os.path.relpath(t, PROJECT_ROOT)
        if dry_run:
            print(f"  [dry] 将删除: {rel}")
            continue
        try:
            if os.path.isdir(t):
                shutil.rmtree(t)
            else:
                os.remove(t)
            print(f"  已删除: {rel}")
        except Exception as e:
            print(f"  删除失败: {rel}: {e}")
    if dry_run:
        print("  重跑去掉 --dry-run 来真正删除。")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scripts/autodriver.py",
        description="ParaJudge AutoDriver —— 自主驱动的科研迭代引擎（7 步循环）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python scripts/autodriver.py start --max-iterations 1 \n"
            "  python scripts/autodriver.py start --max-iterations 3 --provider ollama \\\n"
            "      --model qwen2.5:7b --search --auto-apply\n"
            "  python scripts/autodriver.py status\n"
            "  python scripts/autodriver.py detect\n"
        ),
    )
    sub = p.add_subparsers(dest="command")

    sp_start = sub.add_parser("start", help="启动一次或多次迭代")
    sp_start.add_argument("--max-iterations", type=int, default=1,
                          help="最多执行多少轮迭代（默认 1）")
    sp_start.add_argument("--version", type=str, default=None,
                          help="本次迭代版本号前缀。省略时将按轮次自动命名为 auto-v01 / auto-v02 …")
    sp_start.add_argument("--provider", type=str, default="mock",
                          choices=["mock", "ollama", "openai", "dashscope"],
                          help="LLM provider（mock 表示确定性 mock，不调用任何外部 LLM）")
    sp_start.add_argument("--model", type=str, default="mock-model",
                          help="LLM 模型名（provider=mock 时忽略）")
    sp_start.add_argument("--api-key", type=str, default=None,
                          help="openai/dashscope API key（ollama 不用）")
    sp_start.add_argument("--base-url", type=str, default=None,
                          help="覆盖默认 API base URL，方便指向本地 ollama 或代理")
    sp_start.add_argument("--search", action="store_true",
                          help="开启外部知识检索（arxiv/网络）；缺省仅使用离线摘要")
    sp_start.add_argument("--auto-apply", action="store_true",
                          help="开启代码自动修改（由 Reflector 产出的 code_patches 会被落盘；目标文件会先 .bak 备份）")
    sp_start.add_argument("--temperature", type=float, default=0.7,
                          help="LLM temperature（default 0.7）")

    sub.add_parser("status", help="打印系统状态 + 最近一次迭代的信息")
    sub.add_parser("detect", help="触发内置问题检测器，不跑完整循环")
    sp_clean = sub.add_parser("clean", help="清理所有迭代产物（保留实验记录 issues/experiments）")
    sp_clean.add_argument("--dry-run", action="store_true",
                          help="仅列出将删除的文件，不实际删除")

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "status":
        _print_status()
        return 0
    if args.command == "detect":
        _print_detect()
        return 0
    if args.command == "clean":
        _print_clean(dry_run=args.dry_run)
        return 0

    if args.command == "start":
        llm_cfg = LLMConfig(
            provider=args.provider, model=args.model,
            api_key=args.api_key, base_url=args.base_url,
            temperature=args.temperature,
        )
        max_iterations = max(1, int(args.max_iterations))
        prefix = args.version or "auto-v"

        # 连续多轮循环：每轮的 version 会带上轮次
        for it_idx in range(1, max_iterations + 1):
            version = args.version if (args.version and max_iterations == 1) else f"{prefix}{it_idx:02d}"
            driver = AutoDriver(
                version=version, llm_cfg=llm_cfg,
                enable_search=args.search, auto_apply=args.auto_apply,
            )
            out = driver.run_once()
            if not out.get("ok"):
                print(f"\n❌ 第 {it_idx} 轮迭代失败，停止后续：{out.get('error')}")
                return 1
            # 小休，避免写文件顺序不可预测
            time.sleep(0.2)

        print("\n✅ AutoDriver 完成。使用 `python scripts/autodriver.py status` 查看结果。")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
