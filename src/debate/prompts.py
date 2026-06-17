"""ParaJudge 辩论与裁决的 Prompt 模板集合。

所有 Prompt 以函数方式提供，方便组合，并注入结构化的 context（如证据包、论点历史等）。

使用时只需要：
  prompt = build_debater_prompt(side="pro", problem="...", brief=evidence_brief, history=...)
  response_text = llm.call(prompt, expect_json=True)
"""
from __future__ import annotations

from typing import List, Optional


# ============================================================
# Phase 1 · 辩论者 Prompt
# ============================================================

DEBATER_ROLE_INTRO = """你是一位严谨、基于证据推理的辩论者。你只使用下方「证据包」中提供的证据来支持你的论点。
- 每个论点必须引用至少一条证据（标注为 [引用 E-xxx]）
- 不要编造证据包中没有的事实或数据
- 论点要具体（引用年份、数据、案例），避免空泛陈述
"""


def _format_evidence_list(items) -> str:
    """将证据摘要包格式化为易读的列表。"""
    lines = []
    for it in items:
        cite = it.citation_count if it.citation_count is not None else "N/A"
        year = f"{it.year}" if it.year else "N/A"
        venue = f"{it.venue}" if it.venue else ""
        url = it.url or ""
        lines.append(
            f"[{it.evidence_id}] {it.title}\n"
            f"    年份: {year}  引用数: {cite}  来源: {venue}\n"
            f"    摘要: {it.abstract_excerpt}\n"
            f"    链接: {url}"
        )
    return "\n\n".join(lines)


def build_debater_prompt(
    side: str,                   # "pro" 或 "con"
    problem: str,
    evidence_items,              # List[EvidenceItem]
    history_text: str = "",      # 已有发言的摘要（用于交叉质询）
    max_items_in_prompt: int = 15,  # 最多注入多少条证据（避免 prompt 过长）
) -> str:
    """构建辩论者发言 Prompt。返回值期望 LLM 输出 JSON。"""
    stance_cn = "正方（主张问题为「是」）" if side == "pro" else "反方（主张问题为「否」）"

    items_str = _format_evidence_list(evidence_items[:max_items_in_prompt])

    history_block = ""
    if history_text:
        history_block = (
            "\n\n【辩论历史（用于交叉质询）】\n"
            f"{history_text}\n"
            "\n你可以指出对方论点中证据不支持的地方，或提出新的独立论点。"
        )

    return (
        DEBATER_ROLE_INTRO
        + f"\n\n【你的立场】\n{stance_cn}\n"
        f"\n【待辩论问题】\n{problem}\n"
        f"\n【证据包】\n{items_str}\n"
        + history_block
        + "\n\n【输出格式（严格 JSON，不要写任何说明文字）】\n"
        "{\n"
        '  "reasoning": "你对如何选择论点和证据的简短推理（不超过 100 字）",\n'
        '  "arguments": [\n'
        '    {"content": "第一条论点正文，包含具体主张和数据引用（[引用 E-xxx]）","evidence_refs": ["E-001"]},\n'
        '    {"content": "第二条论点正文","evidence_refs": ["E-002"]}\n'
        "  ]\n"
        "}\n"
    )


# ============================================================
# Phase 2.1 · 检察官（审理）Prompt
# ============================================================

def build_review_prompt(
    problem: str,
    evidence_items,
    arguments_text: str,       # 所有论点（含 arg_id）的格式化文本
) -> str:
    """构建检察官审理 Prompt。检查 weak_support / circular / contradiction。"""
    items_str = _format_evidence_list(evidence_items[:15])

    return (
        "你是一位严谨的辩论检察官。你的任务是检查辩论者提出的论点是否存在以下问题：\n"
        "1. invalid_cite: 论点引用了证据包中不存在的 evidence_id\n"
        "2. no_evidence: 论点完全没有引用任何证据\n"
        "3. weak_support: 虽然引用了证据，但证据的实际内容并不直接支持该论点\n"
        "4. circular: 循环论证（论点以自身为前提）\n"
        "5. contradiction: 同一个辩论者的多个论点之间互相矛盾\n\n"
        f"【问题】\n{problem}\n"
        f"\n【证据包】\n{items_str}\n"
        f"\n【待审论点】\n{arguments_text}\n"
        "\n【输出格式（严格 JSON）】\n"
        "{\n"
        '  "issues": [\n'
        '    {"issue_type": "weak_support", "target_arg_id": "A-00X", "description": "证据 E-00Y 仅讨论了 A，但论点声称了 B"}\n'
        "  ]\n"
        "}\n"
        "\n如果没有发现问题，返回 {\"issues\": []}。"
    )


# ============================================================
# Phase 2.2 · 法官评分 Prompt
# ============================================================

JUDGE_ROLES = {
    "evidence": (
        "证据法法官",
        "你关注证据的权威性、相关性和覆盖面。高分论点应该引用高引用数、近年发表、直接相关的证据。",
    ),
    "logic": (
        "逻辑分析法官",
        "你关注推理链的完整性和逻辑有效性。循环论证、稻草人谬误、无因果推论应当扣分。",
    ),
    "principle": (
        "原则性法官",
        "你关注论点是否符合公认的基本原则与长期影响，是否公平考虑了多方利益相关者。",
    ),
    "case": (
        "案例法法官",
        "你关注论点是否有具体案例或实证数据支持，反例是否被忽略。",
    ),
    "innovation": (
        "创新性法官",
        "你关注论点是否提出新颖的观点或综合方式，即便证据尚不完全支持。",
    ),
}


def build_judge_prompt(
    judge_type: str,              # "evidence" | "logic" | "principle" | "case" | "innovation"
    problem: str,
    evidence_items,
    pro_arguments: List[dict],    # 每个元素：{"id": "A-001", "content": "...", "evidence_refs": [...]}
    con_arguments: List[dict],
    review_summary: str = "",     # 审理阶段发现的问题摘要
) -> str:
    """构建单一法官评分 Prompt。"""
    judge_name, criteria = JUDGE_ROLES.get(
        judge_type,
        ("通用法官", "你综合评估论点的质量与说服力"),
    )

    def _fmt_args(args, label):
        if not args:
            return f"{label}:（无）"
        parts = []
        for a in args:
            refs = ", ".join(a.get("evidence_refs", [])) or "无"
            parts.append(f"  - [{a.get('id', '?')}] {a.get('content', '')}  [引用: {refs}]")
        return f"{label}:\n" + "\n".join(parts)

    pro_text = _fmt_args(pro_arguments, "正方论点")
    con_text = _fmt_args(con_arguments, "反方论点")
    items_str = _format_evidence_list(evidence_items[:10])

    review_block = ""
    if review_summary:
        review_block = (
            "\n\n【审理报告（以下论点在评分时应被降权）】\n"
            f"{review_summary}\n"
        )

    return (
        f"你是一位「{judge_name}」。{criteria}\n\n"
        f"【问题】\n{problem}\n"
        f"\n【证据包】\n{items_str}\n"
        f"\n【{pro_text}】\n"
        f"\n【{con_text}】\n"
        + review_block
        + "\n\n【输出格式（严格 JSON）】\n"
        "{\n"
        '  "pro_score": <0-100 整数评分>,\n'
        '  "con_score": <0-100 整数评分>,\n'
        '  "pro_feedback": "对正方的简短中文反馈（不超过 100 字）",\n'
        '  "con_feedback": "对反方的简短中文反馈（不超过 100 字）",\n'
        '  "reasoning": "你对评分依据的简短说明（不超过 150 字）"\n'
        "}\n"
    )


__all__ = [
    "build_debater_prompt",
    "build_review_prompt",
    "build_judge_prompt",
    "build_judge_prompt_v2",   # 含事实/价值论证区分
    "JUDGE_ROLES",
    "JUDGE_ROLES_V2",           # 新版含事实/价值指导
]


# ============================================================
# 新版法官 Prompt（含事实/价值论证区分）
# ============================================================

FACT_VALUE_CATEGORIZATION_INSTRUCTION = """
【重要：区分事实论证与价值论证】

在评分前，请先识别并区分论点中的两类声明：

  📌 事实声明（F）：可以用外部证据验证真假的陈述
    识别词：数据、年份、统计数字、事件名称、因果关系
    评估标准：① 是否可验证 ② 证据是否充分 ③ 是否存在反例

  ⚖️ 价值声明（V）：关于"应该/不应该"、"好/坏"、"重要/不重要"的判断
    识别词：道德判断、政策建议、美学评价、优先级排序
    评估标准：① 前提假设是否清晰 ② 是否承认价值多元性 ③ 是否平衡多方利益

评分策略：
  - 事实声明：基于可验证性评分（假事实直接判 0-30 分）
  - 价值声明：基于论证质量评分（考虑价值多元性和前提假设）
  - 混合声明：分别评分后加权平均
  - 无论事实还是价值，证据质量始终重要

【输出格式（严格 JSON，同时输出事实/价值分类）】\n
{\n
  "pro_score": <0-100 整数评分>,\n
  "con_score": <0-100 整数评分>,\n
  "pro_fact_score": <0-100 整数，正方事实声明得分>,\n
  "pro_value_score": <0-100 整数，正方价值声明得分>,\n
  "con_fact_score": <0-100 整数，反方事实声明得分>,\n
  "con_value_score": <0-100 整数，反方价值声明得分>,\n
  "pro_fact_claims": ["正方的事实声明1", "正方的事实声明2"],\n
  "con_fact_claims": ["反方的事实声明1"],\n
  "pro_feedback": "对正方的简短中文反馈（不超过 100 字）",\n
  "con_feedback": "对反方的简短中文反馈（不超过 100 字）",\n
  "reasoning": "你的评分依据和事实/价值分类说明（不超过 200 字）"\n
}\n
"""


def build_judge_prompt_v2(
    judge_type: str,
    problem: str,
    evidence_items: List[Dict],
    pro_arguments: List[Dict],
    con_arguments: List[Dict],
    review_summary: Optional[str] = None,
) -> str:
    """新版法官 Prompt（v2）：包含事实/价值论证区分。

    用法：
        judge_prompt = build_judge_prompt_v2(
            judge_type="evidence",
            problem="...",
            evidence_items=[...],
            pro_arguments=[...],
            con_arguments=[...],
            review_summary="...",
        )
    """
    name, criteria = JUDGE_ROLES.get(judge_type, ("通用法官", "综合评估"))

    def _get_field(obj, key, default):
        """同时支持 dict.get() 和 Pydantic model getattr。"""
        if hasattr(obj, "get"):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _format_evidence_list(items):
        if not items:
            return "（无证据）"
        lines = []
        for it in items[:15]:
            lines.append(
                f"  - [{_get_field(it, 'evidence_id', '?')}] "
                f"{_get_field(it, 'title', '无标题')} | "
                f"{_get_field(it, 'abstract_excerpt', '')[:120]}..."
            )
        return "\n".join(lines)

    def _fmt_args(args, label):
        if not args:
            return f"{label}:（无）"
        parts = []
        for a in args:
            refs = ", ".join(_get_field(a, "evidence_refs", [])) or "无"
            parts.append(f"  - [{_get_field(a, 'id', '?')}] {_get_field(a, 'content', '')}  [引用: {refs}]")
        return f"{label}:\n" + "\n".join(parts)

    pro_text = _fmt_args(pro_arguments, "正方论点")
    con_text = _fmt_args(con_arguments, "反方论点")
    items_str = _format_evidence_list(evidence_items[:10])

    review_block = ""
    if review_summary:
        review_block = (
            "\n\n【审理报告（以下论点在评分时应被降权）】\n"
            f"{review_summary}\n"
        )

    return (
        f"你是一位「{name}」。{criteria}\n\n"
        f"【问题】\n{problem}\n"
        f"\n【证据包】\n{items_str}\n"
        f"\n【{pro_text}】\n"
        f"\n【{con_text}】\n"
        + review_block
        + FACT_VALUE_CATEGORIZATION_INSTRUCTION
    )
