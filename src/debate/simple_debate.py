"""Phase 1 · 极简辩论引擎（SimpleDebate）。

策略：
- 固定轮次（默认 3 轮）
- 每轮：正方发言 → 反方发言
- 每个 Agent 通过 LLM 生成 1-2 个论点
- 强制引用 evidence_id
- 收集所有论点到 DebateTranscript / ArgumentIndex
"""
from __future__ import annotations

import time
from typing import List, Optional

from backend.models.schemas import (
    DebateArgument,
    DebateTranscript,
    ArgumentIndex,
    EvidenceBrief,
)
from src.writer.llm_client import LLMClient
from src.debate.prompts import build_debater_prompt
from src.debate.moderator import Moderator


# ============================================================
# 引擎核心
# ============================================================

class SimpleDebate:
    def __init__(
        self,
        llm: LLMClient,
        rounds: int = 3,
        pro_stance: str = "正方：主张问题的答案为「是」",
        con_stance: str = "反方：主张问题的答案为「否」",
        moderator: Optional[Moderator] = None,
    ):
        self.llm = llm
        self.rounds = max(1, rounds)
        self.pro_stance = pro_stance
        self.con_stance = con_stance
        self.moderator = moderator

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def run(self, problem: str, brief: EvidenceBrief) -> DebateTranscript:
        t0 = time.perf_counter()

        all_args: List[DebateArgument] = []
        arg_counter = 0

        for round_idx in range(1, self.rounds + 1):
            # 构建历史摘要（第 2 轮起注入对方发言）
            history_text = ""
            if all_args:
                history_lines = []
                for a in all_args[-6:]:  # 只保留最近 6 个论点
                    refs = ",".join(a.evidence_refs) or "无"
                    history_lines.append(f"[{a.side}-R{a.round_index}] {a.content}  [引用: {refs}]")
                history_text = "\n".join(history_lines)

            # 主持人主动干预判定（在两方发言之间）
            if self.moderator:
                intervention = self.moderator.maybe_intervene(
                    problem=problem,
                    current_round=round_idx,
                    max_rounds=self.rounds,
                    recent_args=all_args,
                )
                # 干预信息不阻断流程，仅记录

            # 正方
            if self.moderator:
                self.moderator.on_turn_start(side="pro", round_index=round_idx)
            pro_args = self._speaker_speak(
                speaker="Pro Agent",
                side="pro",
                round_index=round_idx,
                problem=problem,
                brief=brief,
                history_text=history_text,
                start_arg_id=arg_counter,
            )
            arg_counter += len(pro_args)
            all_args.extend(pro_args)
            # 主持人检查正方发言
            if self.moderator:
                for a in pro_args:
                    self.moderator.check_argument(a, problem, all_args)

            # 反方
            if self.moderator:
                self.moderator.on_turn_start(side="con", round_index=round_idx)
            con_args = self._speaker_speak(
                speaker="Con Agent",
                side="con",
                round_index=round_idx,
                problem=problem,
                brief=brief,
                history_text=history_text,
                start_arg_id=arg_counter,
            )
            arg_counter += len(con_args)
            all_args.extend(con_args)
            # 主持人检查反方发言
            if self.moderator:
                for a in con_args:
                    self.moderator.check_argument(a, problem, all_args)

        # 构建 ArgumentIndex
        pro_args = [a for a in all_args if a.side == "pro"]
        con_args = [a for a in all_args if a.side == "con"]
        argument_index = ArgumentIndex(
            arguments=all_args,
            pro_count=len(pro_args),
            con_count=len(con_args),
        )

        # 主持人总结报告
        moderator_report_dict = None
        if self.moderator:
            moderator_report_dict = self.moderator.on_debate_end(
                DebateTranscript(
                    problem=problem,
                    pro_stance=self.pro_stance,
                    con_stance=self.con_stance,
                    rounds_total=self.rounds,
                    arguments=all_args,
                    argument_index=argument_index,
                    generation_time=round(time.perf_counter() - t0, 3),
                )
            ).to_dict()

        return DebateTranscript(
            problem=problem,
            pro_stance=self.pro_stance,
            con_stance=self.con_stance,
            rounds_total=self.rounds,
            arguments=all_args,
            argument_index=argument_index,
            generation_time=round(time.perf_counter() - t0, 3),
            moderator_report=moderator_report_dict,
        )

    # ------------------------------------------------------------------
    # 单轮发言
    # ------------------------------------------------------------------
    def _speaker_speak(
        self,
        speaker: str,
        side: str,
        round_index: int,
        problem: str,
        brief: EvidenceBrief,
        history_text: str,
        start_arg_id: int,
    ) -> List[DebateArgument]:
        """一个辩论者发言：生成 1-2 个论点。"""
        prompt = build_debater_prompt(
            side=side,
            problem=problem,
            evidence_items=brief.items,
            history_text=history_text,
        )

        # LLM 调用
        response_json = self.llm.call_json(
            prompt,
            max_tokens=600,
            temperature=0.7,
        )

        # 解析失败的回退：构造 1 个默认论点
        if not isinstance(response_json, dict):
            return [self._fallback_argument(speaker, side, round_index, start_arg_id)]

        reasoning = str(response_json.get("reasoning", ""))
        raw_args = response_json.get("arguments", [])
        if not isinstance(raw_args, list):
            return [self._fallback_argument(speaker, side, round_index, start_arg_id)]

        result: List[DebateArgument] = []
        for idx, a in enumerate(raw_args):
            if not isinstance(a, dict):
                continue
            content = str(a.get("content", "")).strip()
            if not content:
                continue
            refs_raw = a.get("evidence_refs", [])
            refs = [str(r).strip() for r in refs_raw] if isinstance(refs_raw, list) else []

            # 清理无效引用（引用必须存在于证据包中）
            valid_ids = {e.evidence_id for e in brief.items}
            valid_refs = [r for r in refs if r in valid_ids]
            if not valid_refs and refs:
                # LLM 提供了引用但全部无效 -> 保留空引用，审理阶段会标记为 invalid_cite
                valid_refs = []

            arg = DebateArgument(
                arg_id=f"A-{start_arg_id + idx + 1:03d}",
                content=content,
                side=side,
                speaker=speaker,
                round_index=round_index,
                evidence_refs=valid_refs,
                reasoning=reasoning,
                timestamp=round(time.perf_counter(), 3),
            )
            result.append(arg)

        # 兜底：至少返回一个论点
        if not result:
            return [self._fallback_argument(speaker, side, round_index, start_arg_id)]
        return result

    # ------------------------------------------------------------------
    # 回退：当 LLM 完全无法输出 JSON 时
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_argument(
        speaker: str, side: str, round_index: int, start_arg_id: int,
    ) -> DebateArgument:
        return DebateArgument(
            arg_id=f"A-{start_arg_id + 1:03d}",
            content="（未能生成结构化论点，建议在完整系统中使用更强的 LLM 或调整 prompt）",
            side=side,
            speaker=speaker,
            round_index=round_index,
            evidence_refs=[],
            reasoning="LLM 输出解析失败，使用回退方案。",
            timestamp=time.perf_counter(),
        )


__all__ = ["SimpleDebate"]
