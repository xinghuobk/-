# -*- coding: utf-8 -*-
"""ParaJudge 迭代开发套件：问题追踪 + 实验记录 + 迭代流程 + 报告生成。

用于支撑"检测 → 分类 → 修复 → 验证 → 部署"的迭代开发循环。

使用方式:
    from scripts.iteration import IssueTracker, ExperimentTracker, IterSession

    # 问题追踪
    tracker = IssueTracker()
    tracker.add(title="DS融合非真正DS", category="theory", priority="P0", description="...")
    tracker.list()

    # 实验追踪
    et = ExperimentTracker()
    et.log(run_id="abc", config={"rounds": 3}, metrics={"accuracy": 0.82})
    et.compare(["abc", "def"])

    # 迭代会话（组合上面所有）
    session = IterSession(problem="AI是否导致失业")
    session.detect_issues()       # 自动检测当前系统问题
    session.iterate()             # 执行一轮迭代
    session.report()               # 生成报告
"""
from __future__ import annotations

import json
import os
import time
import uuid
import random
import hashlib
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


ISSUE_FILE = ".parajudge/issues.json"
EXP_FILE = ".parajudge/experiments.json"


# ========================================================================
# 问题追踪 (Issue Tracker)
# ========================================================================

class IssueCategory(str, Enum):
    DESIGN = "design"       # 设计缺陷
    LOGIC = "logic"        # 逻辑漏洞
    CODE = "code"          # 编码漏洞
    THEORY = "theory"      # 理论缺陷
    TECH = "tech"          # 技术债务
    CAPABILITY = "capability"  # 能力缺失
    UNKNOWN = "unknown"


class IssuePriority(str, Enum):
    P0_CRITICAL = "P0"     # 必须修复
    P1_HIGH = "P1"         # 高优先级
    P2_MEDIUM = "P2"        # 中优先级
    P3_LOW = "P3"           # 低优先级


class Issue:
    id: str
    title: str
    category: str
    priority: str
    description: str
    status: str  # open / in_progress / fixed / wont_fix
    discovered_in: str  # 迭代版本 / run_id
    fixed_in: Optional[str]
    created_at: float
    updated_at: float
    labels: List[str]

    def __init__(
        self,
        id: str,
        title: str,
        category: str,
        priority: str,
        description: str = "",
        status: str = "open",
        discovered_in: str = "",
        fixed_in: Optional[str] = None,
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        labels: Optional[List[str]] = None,
    ):
        self.id = id
        self.title = title
        self.category = category
        self.priority = priority
        self.description = description
        self.status = status
        self.discovered_in = discovered_in
        self.fixed_in = fixed_in
        self.created_at = created_at if created_at is not None else time.time()
        self.updated_at = updated_at if updated_at is not None else time.time()
        self.labels = labels if labels is not None else []

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "title": self.title, "category": self.category,
            "priority": self.priority, "description": self.description,
            "status": self.status, "discovered_in": self.discovered_in,
            "fixed_in": self.fixed_in, "created_at": self.created_at,
            "updated_at": self.updated_at, "labels": self.labels,
        }


class IssueTracker:
    """轻量级问题追踪（JSON 文件持久化）。

    放在 .parajudge/issues.json，不污染项目根目录。
    """

    def __init__(self, path: str = ISSUE_FILE):
        self.path = path
        self._ensure_dir()
        self.issues: List[Issue] = self._load()

    def _ensure_dir(self) -> None:
        d = os.path.dirname(self.path)
        if d and not os.path.exists(d):
            os.makedirs(d)

    def _load(self) -> List[Issue]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Issue(**item) for item in data]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.issues], f, ensure_ascii=False, indent=2)

    def add(
        self,
        title: str,
        category: str,
        priority: str = "P1",
        description: str = "",
        labels: Optional[List[str]] = None,
        discovered_in: str = "",
    ) -> Issue:
        """添加一个问题。"""
        issue = Issue(
            id=f"issue-{uuid.uuid4().hex[:8]}",
            title=title,
            category=category,
            priority=priority,
            description=description,
            discovered_in=discovered_in,
            labels=labels or [],
        )
        self.issues.append(issue)
        self._save()
        return issue

    def get(self, issue_id: str) -> Optional[Issue]:
        for i in self.issues:
            if i.id == issue_id:
                return i
        return None

    def update(self, issue_id: str, **kwargs) -> Optional[Issue]:
        """更新问题字段。"""
        issue = self.get(issue_id)
        if issue is None:
            return None
        for k, v in kwargs.items():
            if hasattr(issue, k):
                setattr(issue, k, v)
        issue.updated_at = time.time()
        self._save()
        return issue

    def list(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Issue]:
        """过滤并列出问题。"""
        results = self.issues
        if category:
            results = [i for i in results if i.category == category]
        if priority:
            results = [i for i in results if i.priority == priority]
        if status:
            results = [i for i in results if i.status == status]
        return results

    def stats(self) -> Dict[str, Any]:
        """返回统计摘要。"""
        total = len(self.issues)
        by_status = {}
        by_category = {}
        by_priority = {}
        for i in self.issues:
            by_status[i.status] = by_status.get(i.status, 0) + 1
            by_category[i.category] = by_category.get(i.category, 0) + 1
            by_priority[i.priority] = by_priority.get(i.priority, 0) + 1
        return {
            "total": total,
            "open": len([i for i in self.issues if i.status == "open"]),
            "in_progress": len([i for i in self.issues if i.status == "in_progress"]),
            "fixed": len([i for i in self.issues if i.status == "fixed"]),
            "by_status": by_status,
            "by_category": by_category,
            "by_priority": by_priority,
        }

    def render_text(self, issues: Optional[List[Issue]] = None) -> str:
        """将问题列表渲染为可读文本。"""
        if issues is None:
            issues = self.issues

        if not issues:
            return "  (暂无问题记录)"

        lines = []
        priority_colors = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🟢"}
        status_colors = {
            "open": "⚪", "in_progress": "🔵",
            "fixed": "✅", "wont_fix": "❌",
        }

        for i in issues:
            icon_p = priority_colors.get(i.priority, "⚪")
            icon_s = status_colors.get(i.status, "⚪")
            lines.append(
                f"  {icon_p}{i.priority} {icon_s}{i.status:12s} "
                f"[{i.category:10s}] {i.title}"
            )
            if i.description:
                for line in i.description.split("\n")[:2]:
                    lines.append(f"          {line[:80]}")
        return "\n".join(lines)

    def delete(self, issue_id: str) -> bool:
        """删除一个问题。"""
        before = len(self.issues)
        self.issues = [i for i in self.issues if i.id != issue_id]
        if len(self.issues) < before:
            self._save()
            return True
        return False


# ========================================================================
# 实验记录 (Experiment Tracker)
# ========================================================================

class ExperimentRecord:
    exp_id: str
    run_id: str
    problem: str
    config: Dict[str, Any]
    metrics: Dict[str, Any]
    notes: str
    timestamp: float

    def __init__(
        self,
        exp_id: str,
        run_id: str,
        problem: str,
        config: Dict[str, Any],
        metrics: Dict[str, Any],
        notes: str = "",
        timestamp: Optional[float] = None,
    ):
        self.exp_id = exp_id
        self.run_id = run_id
        self.problem = problem
        self.config = config
        self.metrics = metrics
        self.notes = notes
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> Dict:
        return {
            "exp_id": self.exp_id,
            "run_id": self.run_id,
            "problem": self.problem,
            "config": self.config,
            "metrics": self.metrics,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }


class ExperimentTracker:
    """实验记录与对比（JSON 文件持久化）。"""

    def __init__(self, path: str = EXP_FILE):
        self.path = path
        self._ensure_dir()
        self.experiments: List[ExperimentRecord] = self._load()

    def _ensure_dir(self) -> None:
        d = os.path.dirname(self.path)
        if d and not os.path.exists(d):
            os.makedirs(d)

    def _load(self) -> List[ExperimentRecord]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ExperimentRecord(**item) for item in data]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in self.experiments], f, ensure_ascii=False, indent=2)

    def log(
        self,
        run_id: str,
        problem: str,
        config: Dict[str, Any],
        metrics: Dict[str, Any],
        notes: str = "",
        exp_id: Optional[str] = None,
    ) -> ExperimentRecord:
        """记录一次实验。"""
        record = ExperimentRecord(
            exp_id=exp_id or f"exp-{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            problem=problem,
            config=config,
            metrics=metrics,
            notes=notes,
        )
        self.experiments.append(record)
        self._save()
        return record

    def get(self, exp_id: str) -> Optional[ExperimentRecord]:
        for e in self.experiments:
            if e.exp_id == exp_id:
                return e
        return None

    def latest(self, n: int = 10) -> List[ExperimentRecord]:
        """返回最近 n 条实验记录。"""
        return sorted(self.experiments, key=lambda e: e.timestamp, reverse=True)[:n]

    def compare(
        self,
        exp_ids: List[str],
    ) -> Tuple[List[ExperimentRecord], Optional[str]]:
        """对比多条实验记录。

        返回: (找到的记录列表, 错误信息或 None)
        """
        records = []
        missing = []
        for eid in exp_ids:
            rec = self.get(eid)
            if rec:
                records.append(rec)
            else:
                missing.append(eid)
        if missing:
            return records, f"未找到实验记录: {', '.join(missing)}"
        return records, None

    def render_text(self, records: Optional[List[ExperimentRecord]] = None) -> str:
        if records is None:
            records = self.latest()
        if not records:
            return "  (暂无实验记录)"

        lines = []
        for e in records:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.timestamp))
            m_str = " | ".join(f"{k}={self._fmt(v)}" for k, v in e.metrics.items())
            lines.append(
                f"  [{e.exp_id}] {ts} | run={e.run_id} | {e.problem[:40]}\n"
                f"      config: {json.dumps(e.config, ensure_ascii=False)[:80]}"
                f"\n      metrics: {m_str[:100]}"
            )
        return "\n".join(lines)

    @staticmethod
    def _fmt(v: Any) -> str:
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)


# ========================================================================
# 自动问题检测器 (Auto Detector)
# ========================================================================

class AutoDetector:
    """自动检测系统中已知的问题模式。

    基于我们之前的分析，预定义了一套检测规则。
    每次 `detect` 会扫描关键代码/配置，发现问题就返回 Issue 列表。
    """

    # 检测规则: (issue_id_prefix, category, priority, 描述模板, 检测函数)
    RULES: List[Tuple[str, str, str, str, callable]] = []

    @classmethod
    def register(cls, rule: Tuple) -> None:
        cls.RULES.append(rule)

    @classmethod
    def detect(cls) -> List[Dict[str, Any]]:
        """执行所有检测规则。"""
        found = []
        for (eid, cat, pri, desc, fn) in cls.RULES:
            try:
                result = fn()
                if result:
                    found.append({
                        "id": eid,
                        "category": cat,
                        "priority": pri,
                        "description": desc,
                        "details": result,
                    })
            except Exception:
                pass
        return found


# 注册检测规则
def _check_judge_variance() -> Optional[str]:
    """检测法官评分方差是否过小（说明评分缺乏多样性）。"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run
        cfg = LoopConfig(provider="mock", rounds=2, max_evidence=5)
        state = LoopState(cfg)
        cmd_problem(state, ["AI是否会导致大规模失业？"])
        cmd_run(state, [])
        scores = state.judgment.judge_scores
        if not scores:
            return None
        pro_scores = [s.pro_score for s in scores]
        avg = sum(pro_scores) / len(pro_scores)
        variance = sum((x - avg) ** 2 for x in pro_scores) / len(pro_scores)
        if variance < 1.0:
            return f"法官评分方差={variance:.3f}，过小（<1.0）。可能是 Mock 评分过于对称。"
        return None
    except Exception:
        return None


def _check_fact_check_disabled() -> Optional[str]:
    """检测事实核查是否被默认禁用。"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.judgment.judgment_config import CFG
        # 默认启用 = False 是问题
        # 这个检测比较间接，用配置文件检查
        return None
    except Exception:
        return None


def _check_no_diverse_judges() -> Optional[str]:
    """检测是否所有法官使用同一模型（缺乏多样性）。"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.judgment.judgment_engine import JUDGE_TYPES
        # 目前 JUDGE_TYPES 只定义了角色，没有配置不同模型
        return "目前 5 位法官使用同一 LLM 模型/配置，存在共同信念偏见风险（ACL 2026）。"
    except Exception:
        return None


def _check_missing_calibration() -> Optional[str]:
    """检测是否缺少置信度校准机制。"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.judgment.judgment_engine import JudgmentEngine
        # 检查 run 方法是否输出置信度相关信息
        import inspect
        source = inspect.getsource(JudgmentEngine.run)
        if "confidence" not in source.lower() and "calibrat" not in source.lower():
            return "JudgmentEngine.run() 缺少置信度校准输出，高置信度错误无法被检测（CW-POR 建议）。"
        return None
    except Exception:
        return None


def _check_evidence_no_quality_filtering() -> Optional[str]:
    """检测证据构建是否缺少质量过滤。"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.debate.evidence_builder import build_evidence_brief
        import inspect
        source = inspect.getsource(build_idence_brief)
        if "quality" not in source.lower() and "threshold" not in source.lower():
            return "build_evidence_brief 未实现质量阈值过滤，低质量证据可能影响辩论质量。"
        return None
    except Exception:
        return None


# 注册自动检测规则
AutoDetector.register((
    "auto-001", "code", "P1",
    "法官评分方差过小，可能缺乏多样性",
    _check_judge_variance,
))
AutoDetector.register((
    "auto-002", "capability", "P0",
    "所有法官使用同一模型（共同信念偏见风险）",
    _check_no_diverse_judges,
))
AutoDetector.register((
    "auto-003", "capability", "P1",
    "缺少置信度校准，高置信度错误无法被检测",
    _check_missing_calibration,
))
AutoDetector.register((
    "auto-004", "design", "P2",
    "证据构建未实现质量阈值过滤",
    _check_evidence_no_quality_filtering,
))


# ========================================================================
# 迭代会话 (Iteration Session)
# ========================================================================

class IterVersion:
    """一次迭代版本的快照。"""
    version: str  # e.g. "v0.3.1"
    run_id: str
    timestamp: float
    issues_found: int
    issues_fixed: int
    config_snapshot: Dict[str, Any]
    notes: str

    def __init__(
        self,
        version: str,
        run_id: str,
        timestamp: Optional[float] = None,
        issues_found: int = 0,
        issues_fixed: int = 0,
        config_snapshot: Optional[Dict[str, Any]] = None,
        notes: str = "",
    ):
        self.version = version
        self.run_id = run_id
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.issues_found = issues_found
        self.issues_fixed = issues_fixed
        self.config_snapshot = config_snapshot if config_snapshot is not None else {}
        self.notes = notes

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "config_snapshot": self.config_snapshot,
            "notes": self.notes,
        }


class IterSession:
    """组合 IssueTracker + ExperimentTracker + 自动检测的迭代会话。

    使用方式:
        session = IterSession("AI是否导致失业")
        session.detect_issues()          # 自动检测系统问题
        session.iterate()                # 执行修复迭代
        session.report()                 # 生成迭代报告
    """

    def __init__(self, problem: str, version: str = "v0.1"):
        self.problem = problem
        self.version = version
        self.issue_tracker = IssueTracker()
        self.exp_tracker = ExperimentTracker()
        self.versions: List[IterVersion] = self._load_versions()
        self.detected_this_session: List[Dict] = []

    @property
    def version_file(self) -> str:
        return f".parajudge/versions.json"

    def _load_versions(self) -> List[IterVersion]:
        path = self.version_file
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [IterVersion(**v) for v in data]
        except Exception:
            return []

    def _save_versions(self) -> None:
        os.makedirs(".parajudge", exist_ok=True)
        with open(self.version_file, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in self.versions], f, ensure_ascii=False, indent=2)

    def detect_issues(self, auto: bool = True, manual: bool = True) -> List[Dict]:
        """检测问题。

        Args:
            auto: 是否运行自动检测器
            manual: 是否提示手动输入
        """
        self.detected_this_session = []

        # 自动检测
        if auto:
            auto_results = AutoDetector.detect()
            for r in auto_results:
                # 自动检测到的问题 → 添加到 issue tracker
                issue = self.issue_tracker.add(
                    title=r["description"][:80],
                    category=r["category"],
                    priority=r["priority"],
                    description=f"[自动检测] {r.get('details', '')}",
                    discovered_in=self.version,
                    labels=["auto-detected"],
                )
                self.detected_this_session.append({
                    "type": "auto",
                    "issue": issue,
                    "details": r,
                })

        return self.detected_this_session

    def iterate(
        self,
        fix_functions: Optional[List[callable]] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """执行一轮迭代修复。

        Args:
            fix_functions: 可选的修复函数列表，执行后会记录
            notes: 迭代备注

        Returns:
            迭代结果摘要
        """
        # 统计修复前的问题状态
        before_stats = self.issue_tracker.stats()
        open_before = before_stats["open"]

        # 执行修复函数（如果有）
        fixed_issues = []
        if fix_functions:
            for fn in fix_functions:
                try:
                    fn_result = fn()
                    # 假设返回修复的问题 ID 列表
                    if isinstance(fn_result, list):
                        for issue_id in fn_result:
                            self.issue_tracker.update(issue_id, status="fixed", fixed_in=self.version)
                            fixed_issues.append(issue_id)
                except Exception as e:
                    print(f"    ⚠ 修复函数 {fn.__name__} 执行失败: {e}")

        # 记录本次迭代版本
        v = IterVersion(
            version=self.version,
            run_id=uuid.uuid4().hex[:8],
            timestamp=time.time(),
            issues_found=len(self.detected_this_session),
            issues_fixed=len(fixed_issues),
            config_snapshot={},
            notes=notes,
        )
        self.versions.append(v)
        self._save_versions()

        after_stats = self.issue_tracker.stats()

        return {
            "version": self.version,
            "run_id": v.run_id,
            "issues_found_this_iter": len(self.detected_this_session),
            "issues_fixed_this_iter": len(fixed_issues),
            "open_before": open_before,
            "open_after": after_stats["open"],
            "total_issues": after_stats["total"],
        }

    def run_experiment(
        self,
        config_overrides: Optional[Dict[str, Any]] = None,
        notes: str = "",
    ) -> ExperimentRecord:
        """在当前问题上运行一次实验。

        Args:
            config_overrides: 配置覆盖（如 {"rounds": 3, "enable_t4_ds": True}）
            notes: 实验备注
        """
        import sys
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run

        cfg = LoopConfig()
        if config_overrides:
            for k, v in config_overrides.items():
                cfg.apply_set(k, str(v))

        state = LoopState(cfg)
        cmd_problem(state, [self.problem])
        cmd_run(state, [])

        # 提取关键指标
        metrics = {
            "winner": state.judgment.winner,
            "pro_score": round(state.judgment.pro_final_score, 2),
            "con_score": round(state.judgment.con_final_score, 2),
            "total_time": round(state.full_output.total_time_sec, 3) if state.full_output else 0,
            "rounds": state.transcript.rounds_total if state.transcript else 0,
            "n_arguments": len(state.transcript.argument_index.arguments) if state.transcript else 0,
        }

        record = self.exp_tracker.log(
            run_id=state.full_output.run_id if state.full_output else "unknown",
            problem=self.problem,
            config=cfg.to_kwargs(),
            metrics=metrics,
            notes=notes,
        )
        return record

    def report(self) -> str:
        """生成当前迭代状态的文本报告。"""
        stats = self.issue_tracker.stats()
        latest_exp = self.exp_tracker.latest(3)
        vers = sorted(self.versions, key=lambda v: v.timestamp, reverse=True)[:3]

        lines = [
            "=" * 60,
            f"  ParaJudge 迭代状态报告 · {self.problem[:50]}",
            "=" * 60,
            f"  当前版本: {self.version}",
            "",
            "  【问题统计】",
            f"    总问题: {stats['total']}",
            f"    开放:   {stats.get('open', 0)}",
            f"    修复中: {stats.get('in_progress', 0)}",
            f"    已修复: {stats.get('fixed', 0)}",
            "",
            "  【问题分类统计】",
        ]
        for cat, count in stats.get("by_category", {}).items():
            lines.append(f"    {cat:12s}: {count}")
        lines.extend(["", "  【P0 问题（必须修复）】"])
        p0_issues = self.issue_tracker.list(priority="P0", status="open")
        if p0_issues:
            lines.append(self.issue_tracker.render_text(p0_issues))
        else:
            lines.append("    (无 P0 开放问题) ✅")
        lines.extend(["", "  【P1 问题（高优先级）前 5 条】"])
        p1_issues = self.issue_tracker.list(priority="P1", status="open")[:5]
        if p1_issues:
            lines.append(self.issue_tracker.render_text(p1_issues))
        else:
            lines.append("    (无 P1 开放问题) ✅")

        if latest_exp:
            lines.extend(["", "  【最近实验】"])
            lines.append(self.exp_tracker.render_text(latest_exp))

        if vers:
            lines.extend(["", "  【最近迭代版本】"])
            for v in vers:
                ts = time.strftime("%m-%d %H:%M", time.localtime(v.timestamp))
                lines.append(
                    f"    {v.version:8s} | {ts} | "
                    f"发现 {v.issues_found} | 修复 {v.issues_fixed} | {v.notes}"
                )
        lines.append("=" * 60)
        return "\n".join(lines)


# ========================================================================
# 回归测试套件
# ========================================================================

class RegressionSuite:
    """轻量级回归测试套件。

    每次修复后运行，确保不引入新问题。
    """

    class TestCase:
        name: str
        fn: callable
        expected: Any

        def __init__(self, name: str, fn: callable, expected: Any = None):
            self.name = name
            self.fn = fn
            self.expected = expected

    def __init__(self):
        self.cases: List[RegressionSuite.TestCase] = []

    def add(self, name: str, fn: callable, expected: Any = None) -> None:
        self.cases.append(self.TestCase(name=name, fn=fn, expected=expected))

    def run(self) -> Tuple[int, int, List[Dict]]:
        """运行所有测试。返回 (passed, failed, details)。"""
        passed = 0
        failed = 0
        details = []

        for case in self.cases:
            try:
                result = case.fn()
                if case.expected is not None and result != case.expected:
                    failed += 1
                    details.append({
                        "name": case.name,
                        "status": "FAIL",
                        "expected": case.expected,
                        "actual": result,
                        "error": None,
                    })
                else:
                    passed += 1
                    details.append({
                        "name": case.name,
                        "status": "PASS",
                        "result": str(result)[:100],
                    })
            except Exception as e:
                failed += 1
                details.append({
                    "name": case.name,
                    "status": "ERROR",
                    "error": str(e),
                })
        return passed, failed, details

    def render_text(self, passed: int, failed: int, details: List[Dict]) -> str:
        lines = [
            "=" * 60,
            f"  回归测试结果: {passed} passed / {failed} failed",
            "=" * 60,
        ]
        for d in details:
            if d["status"] == "PASS":
                lines.append(f"  ✅ {d['name']}")
            elif d["status"] == "FAIL":
                lines.append(f"  ❌ {d['name']}: expected={d['expected']}, got={d['actual']}")
            else:
                lines.append(f"  💥 {d['name']}: {d['error']}")
        return "\n".join(lines)


def build_default_suite() -> RegressionSuite:
    """构建默认的回归测试套件。"""
    suite = RegressionSuite()

    # 测试 1: 基本导入
    def test_imports():
        import sys
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run, cmd_show
        return True
    suite.add("基本导入", test_imports)

    # 测试 2: LoopConfig 默认值
    def test_cfg_defaults():
        from scripts.loop import LoopConfig
        cfg = LoopConfig()
        assert cfg.provider == "mock"
        assert cfg.rounds >= 1
        return True
    suite.add("LoopConfig 默认值", test_cfg_defaults)

    # 测试 3: IssueTracker 增删改查
    def test_issue_crud():
        tracker = IssueTracker(path="/tmp/test_issues.json")
        before = len(tracker.issues)
        i = tracker.add(title="测试问题", category="code", priority="P2")
        assert len(tracker.issues) == before + 1
        tracker.delete(i.id)
        assert len(tracker.issues) == before
        return True
    suite.add("IssueTracker CRUD", test_issue_crud)

    # 测试 4: ExperimentTracker 记录
    def test_exp_log():
        et = ExperimentTracker(path="/tmp/test_exps.json")
        before = len(et.experiments)
        et.log(run_id="test-001", problem="测试", config={}, metrics={"acc": 0.8})
        assert len(et.experiments) == before + 1
        return True
    suite.add("ExperimentTracker 记录", test_exp_log)

    # 测试 5: 完整 pipeline（mock 模式）
    def test_full_pipeline():
        import sys
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run
        cfg = LoopConfig(provider="mock", rounds=1, max_evidence=3, enable_fact_check=False)
        state = LoopState(cfg)
        cmd_problem(state, ["测试问题"])
        cmd_run(state, [])
        assert state.judgment is not None
        assert state.full_output is not None
        return True
    suite.add("完整 pipeline (mock)", test_full_pipeline)

    # 测试 6: step 逐步执行
    def test_stepwise():
        import sys
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_step
        cfg = LoopConfig(provider="mock", rounds=1, max_evidence=3, enable_fact_check=False)
        state = LoopState(cfg)
        cmd_problem(state, ["逐步测试"])
        for _ in range(5):
            cmd_step(state, [])
        return state.current_phase >= 5
    suite.add("step 逐步执行", test_stepwise)

    # 测试 7: compare 功能
    def test_compare():
        import sys
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run, cmd_compare
        cfg = LoopConfig(provider="mock", rounds=1, max_evidence=3)
        state = LoopState(cfg)
        cmd_problem(state, ["对比测试"])
        cmd_run(state, [])
        id1 = state.history[0].run_id
        cmd_run(state, [])
        id2 = state.history[1].run_id
        out = cmd_compare(state, [id1, id2])
        return isinstance(out, str) and "对比" in out
    suite.add("compare 对比功能", test_compare)

    # 测试 8: export 功能
    def test_export():
        import sys, os, tempfile
        sys.path.insert(0, ".")
        from scripts.loop import LoopConfig, LoopState, cmd_problem, cmd_run, cmd_export
        cfg = LoopConfig(provider="mock", rounds=1, max_evidence=3)
        state = LoopState(cfg)
        cmd_problem(state, ["导出测试"])
        cmd_run(state, [])
        path = tempfile.mktemp(suffix=".json")
        out = cmd_export(state, [path, "json"])
        exists = os.path.exists(path)
        if exists:
            os.remove(path)
        return exists
    suite.add("export 导出功能", test_export)

    return suite
