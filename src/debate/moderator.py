"""主持人（Moderator）角色。

职责：
1. 把控整场辩论的节奏与时间
2. 检查每个发言是否跑题（off-topic）
3. 检测重复论证（duplicate / 抄袭自己/对方）
4. 控制总时长、单轮时长、累计 token
5. 在异常时插入干预 prompt
6. 输出主持人报告（ModeratorReport）

设计原则：
- 不与 DebateEngine 强耦合，作为插件式装饰器存在
- 通过 callback 接入，可独立测试
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from backend.models.schemas import DebateArgument, DebateTranscript
from src.writer.llm_client import LLMClient


# ============================================================
# 配置
# ============================================================

class ModeratorStrictness(str, Enum):
    LOOSE = "loose"           # 仅明显违规才干预
    NORMAL = "normal"         # 默认
    STRICT = "strict"         # 严格模式，更多干预


@dataclass
class ModeratorConfig:
    """主持人配置"""
    strictness: ModeratorStrictness = ModeratorStrictness.NORMAL

    # 重复检测阈值（0.5-1.0）：相似度高于此值视为重复
    duplicate_threshold: float = 0.85

    # 跑题检测阈值（0.1-0.9）：话题相关度低于此值视为跑题
    off_topic_threshold: float = 0.4

    # 单轮最长时间（秒）
    max_seconds_per_turn: int = 120

    # 单轮最多 token
    max_tokens_per_turn: int = 400

    # 是否启用 LLM 辅助判断（更准但更慢）
    enable_poi_llm: bool = False


# ============================================================
# 报告
# ============================================================

class ModeratorAction(str, Enum):
    PASS = "pass"                         # 通过
    WARN_OFF_TOPIC = "warn_off_topic"     # 警告：跑题
    WARN_DUPLICATE = "warn_duplicate"     # 警告：重复
    WARN_TOO_LONG = "warn_too_long"       # 警告：超时/超长
    INTERVENE = "intervene"               # 主持人主动干预
    END_DEBATE = "end_debate"             # 提前结束辩论


@dataclass
class ModeratorNote:
    """单次主持人记录"""
    action: ModeratorAction
    target_arg_id: Optional[str] = None
    target_side: Optional[str] = None
    round_index: Optional[int] = None
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    severity: str = "info"  # info / warn / critical


@dataclass
class ModeratorReport:
    """完整主持人报告"""
    notes: List[ModeratorNote] = field(default_factory=list)
    interventions: int = 0
    warnings: int = 0
    total_debate_sec: float = 0.0
    avg_turn_sec: float = 0.0
    early_termination: bool = False
    early_termination_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "notes": [
                {
                    "action": n.action.value,
                    "target_arg_id": n.target_arg_id,
                    "target_side": n.target_side,
                    "round_index": n.round_index,
                    "message": n.message,
                    "severity": n.severity,
                    "timestamp": n.timestamp,
                }
                for n in self.notes
            ],
            "interventions": self.interventions,
            "warnings": self.warnings,
            "total_debate_sec": round(self.total_debate_sec, 2),
            "avg_turn_sec": round(self.avg_turn_sec, 2),
            "early_termination": self.early_termination,
            "early_termination_reason": self.early_termination_reason,
        }


# ============================================================
# 工具
# ============================================================

def _jaccard_similarity(a: str, b: str) -> float:
    """简单的 Jaccard 相似度（基于词集合）。"""
    if not a or not b:
        return 0.0
    set_a = set(_tokenize(a))
    set_b = set(_tokenize(b))
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def _tokenize(text: str) -> List[str]:
    """极简分词：英文按空格、中文按字符 + 2-gram 混合。"""
    text = text.lower().strip()
    tokens = []
    # 英文词
    for w in text.split():
        w = w.strip(".,;:?!()[]{}\"'")
        if len(w) >= 2:
            tokens.append(w)
    # 中文 2-gram
    chinese = "".join(c for c in text if "\u4e00" <= c <= "\u9fff")
    for i in range(len(chinese) - 1):
        tokens.append(chinese[i:i + 2])
    return tokens


def _keyword_overlap(text: str, problem: str) -> float:
    """话题相关度：text 与 problem 的关键词重合率（0-1）。"""
    if not text or not problem:
        return 1.0
    text_kw = set(_tokenize(text))
    problem_kw = set(_tokenize(problem))
    if not problem_kw:
        return 1.0
    return len(text_kw & problem_kw) / len(problem_kw)


# ============================================================
# Moderator 主类
# ============================================================

class Moderator:
    """主持人

    使用方式：
        moderator = Moderator(config, llm=llm_client)
        note = moderator.check_argument(arg, problem, history)
        if note.action != ModeratorAction.PASS:
            print(note.message)
    """

    def __init__(
        self,
        config: Optional[ModeratorConfig] = None,
        llm: Optional[LLMClient] = None,
    ):
        self.config = config or ModeratorConfig()
        self.llm = llm
        self.report = ModeratorReport()
        self._turn_start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # 主要 hook
    # ------------------------------------------------------------------

    def on_turn_start(self, side: str, round_index: int) -> None:
        """一轮发言开始时调用，重置计时器。"""
        self._turn_start_time = time.time()

    def check_argument(
        self,
        arg: DebateArgument,
        problem: str,
        history: List[DebateArgument],
    ) -> ModeratorNote:
        """检查单个论点，必要时产生干预。

        Args:
            arg: 当前论点
            problem: 辩题
            history: 已有的全部论点（含当前轮之前的）

        Returns:
            ModeratorNote，action=PASS 表示通过
        """
        # 1. 计时
        turn_sec = (time.time() - (self._turn_start_time or time.time()))

        # 2. 长度检查
        if len(arg.content) > self.config.max_tokens_per_turn * 2:
            note = self._make_note(
                ModeratorAction.WARN_TOO_LONG, arg,
                f"本轮发言过长（{len(arg.content)} 字符），建议精炼到 {self.config.max_tokens_per_turn} 字内",
                severity="warn",
            )
            self._record(note)
            return note

        if turn_sec > self.config.max_seconds_per_turn:
            note = self._make_note(
                ModeratorAction.WARN_TOO_LONG, arg,
                f"本轮发言超时（{turn_sec:.1f}s > {self.config.max_seconds_per_turn}s），请控制节奏",
                severity="warn",
            )
            self._record(note)
            return note

        # 3. 跑题检查
        relevance = _keyword_overlap(arg.content, problem)
        if relevance < self.config.off_topic_threshold:
            note = self._make_note(
                ModeratorAction.WARN_OFF_TOPIC, arg,
                f"发言与辩题相关度较低（{relevance:.0%}），请回到主题「{problem[:30]}」",
                severity="warn",
            )
            self._record(note)
            return note

        # 4. 重复检查（与历史所有论点对比）
        for prev in history:
            if prev.arg_id == arg.arg_id:
                continue
            sim = _jaccard_similarity(arg.content, prev.content)
            if sim > self.config.duplicate_threshold:
                note = self._make_note(
                    ModeratorAction.WARN_DUPLICATE, arg,
                    f"本轮发言与 {prev.arg_id}（{prev.side}）相似度过高（{sim:.0%}），请提出新论据",
                    severity="warn",
                )
                self._record(note)
                return note

        # 5. 通过
        note = ModeratorNote(action=ModeratorAction.PASS, target_arg_id=arg.arg_id)
        self._record(note)
        return note

    def on_debate_end(self, transcript: DebateTranscript) -> ModeratorReport:
        """辩论结束时调用，生成总结报告。"""
        # 计算总时长
        if transcript.arguments:
            first_ts = min(a.timestamp for a in transcript.arguments if a.timestamp) if any(a.timestamp for a in transcript.arguments) else None
            last_ts = max(a.timestamp for a in transcript.arguments if a.timestamp) if any(a.timestamp for a in transcript.arguments) else None
            if first_ts and last_ts:
                self.report.total_debate_sec = last_ts - first_ts
                self.report.avg_turn_sec = self.report.total_debate_sec / max(len(transcript.arguments), 1)

        # 统计干预次数
        self.report.interventions = sum(1 for n in self.report.notes if n.action == ModeratorAction.INTERVENE)
        self.report.warnings = sum(1 for n in self.report.notes if n.severity == "warn")
        return self.report

    # ------------------------------------------------------------------
    # 主动干预（可选）
    # ------------------------------------------------------------------

    def maybe_intervene(
        self,
        problem: str,
        current_round: int,
        max_rounds: int,
        recent_args: List[DebateArgument],
    ) -> Optional[ModeratorNote]:
        """判定是否需要主持人主动干预（引导深入 / 总结 / 收束）。

        触发条件（按优先级）：
        1. 辩论进入最后一轮 → 引导总结
        2. 连续 2 轮正反方都没引用新证据 → 引导引用
        3. 时间过半但论证停滞 → 引导深入
        """
        if current_round == max_rounds:
            note = ModeratorNote(
                action=ModeratorAction.INTERVENE,
                round_index=current_round,
                message=f"进入第 {current_round} 轮（共 {max_rounds} 轮），请正反方准备总结性陈述。",
                severity="info",
            )
            self._record(note)
            return note

        # 检查最近 2 轮是否都缺少新证据
        if len(recent_args) >= 4:
            last_4 = recent_args[-4:]
            no_new_evidence = all(
                not a.evidence_refs for a in last_4
            )
            if no_new_evidence:
                note = ModeratorNote(
                    action=ModeratorAction.INTERVENE,
                    round_index=current_round,
                    message="最近两轮发言均未引用证据，请正反方引用具体文献以加强论证。",
                    severity="info",
                )
                self._record(note)
                return note

        return None

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    def _make_note(
        self,
        action: ModeratorAction,
        arg: DebateArgument,
        message: str,
        severity: str = "info",
    ) -> ModeratorNote:
        return ModeratorNote(
            action=action,
            target_arg_id=arg.arg_id,
            target_side=arg.side,
            round_index=arg.round_index,
            message=message,
            severity=severity,
        )

    def _record(self, note: ModeratorNote) -> None:
        self.report.notes.append(note)

    def get_report(self) -> ModeratorReport:
        return self.report


__all__ = [
    "Moderator",
    "ModeratorConfig",
    "ModeratorStrictness",
    "ModeratorAction",
    "ModeratorNote",
    "ModeratorReport",
]
