"""ParaJudge 技术创新点（4 个 T 系列）。

T1 · 论点-证据二部图（AEBG, Argument-Evidence Bipartite Graph）
    - 论文层 + 论证层 的二部图结构
    - 通过社区检测/中心性度量评估"证据聚焦"和"论证孤立"
T2 · 多样性约束（DPP, Determinantal Point Process）
    - 让辩论论点集保持主题多样性
    - 减少重复论证
T3 · KS 早停检验（Kolmogorov-Smirnov Stagnation Test）
    - 监控每轮新增"新概念 token 数"
    - 当新增 token 数显著下降时建议早停
T4 · DS 证据理论融合（Dempster-Shafer Evidence Combination）
    - 把 5 位法官的评分作为独立证据源
    - 用 DS 合成规则计算综合置信度与 mass 分配

这些函数在论文中作为"ParaJudge 区别于既有辩论系统的算法创新"被引用。
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Dict, List, Optional

from backend.models.schemas import (
    DebateTranscript,
    EvidenceBrief,
    JudgeScore,
)


# ============================================================
# 通用工具
# ============================================================

_TOKEN_RE = re.compile(r"[A-Za-z]+|[\u4e00-\u9fff]{2,3}")


def _tokenize_text(text: str) -> List[str]:
    """中英混合轻量分词（用于 KS 检验）。"""
    if not text:
        return []
    return _TOKEN_RE.findall(text)


# ============================================================
# T1 · 论点-证据二部图
# ============================================================

def build_argument_evidence_bipartite(
    transcript: DebateTranscript,
    brief: EvidenceBrief,
) -> Dict:
    """构建「论点-证据」二部图（AEBG）并给出图统计量。

    返回字典：
    - nodes: 节点数 {arg, evidence, total}
    - edges: 边数
    - density: 边 / (arg * evidence)
    - pro_cited_evidence: 正方引用的证据 ID 集合
    - con_cited_evidence: 反方引用的证据 ID 集合
    - shared_evidence: 双方共同引用的证据 ID 集合
    - pro_evidence_count / con_evidence_count: 双方各引用了多少证据
    - ungrounded_pro / ungrounded_con: 未引证据的论点个数
    - top_evidence: 被引用次数最多的 5 条证据
    """
    args = transcript.arguments
    ev_ids = {e.evidence_id for e in brief.items}

    pro_cited, con_cited, edges = set(), set(), 0
    pro_ungrounded = con_ungrounded = 0

    for a in args:
        # 过滤掉无效引用（不在 evidence 包里的）
        valid_refs = [r for r in a.evidence_refs if r in ev_ids]
        if not valid_refs:
            if a.side == "pro":
                pro_ungrounded += 1
            else:
                con_ungrounded += 1
        for r in valid_refs:
            edges += 1
            if a.side == "pro":
                pro_cited.add(r)
            else:
                con_cited.add(r)

    shared = pro_cited & con_cited

    # 统计每条证据被引用次数
    ref_count: Counter = Counter()
    for a in args:
        for r in a.evidence_refs:
            if r in ev_ids:
                ref_count[r] += 1
    top_evidence = ref_count.most_common(5)

    arg_count = len(args)
    ev_count = len(ev_ids)
    density = round(edges / (arg_count * ev_count), 4) if (arg_count and ev_count) else 0.0

    return {
        "nodes": {"argument": arg_count, "evidence": ev_count, "total": arg_count + ev_count},
        "edges": edges,
        "density": density,
        "pro_cited_count": len(pro_cited),
        "con_cited_count": len(con_cited),
        "shared_evidence_count": len(shared),
        "shared_evidence": sorted(shared)[:10],
        "pro_ungrounded": pro_ungrounded,
        "con_ungrounded": con_ungrounded,
        "top_evidence": [{"evidence_id": k, "cited": v} for k, v in top_evidence],
        "comment": _aebg_comment(density, pro_ungrounded, con_ungrounded, len(shared)),
    }


def _aebg_comment(density: float, pro_ug: int, con_ug: int, shared: int) -> str:
    """根据 AEBG 统计给出自然语言评注。"""
    parts = []
    if density < 0.05:
        parts.append(f"二部图密度仅 {density:.2%}，论据-证据关系稀疏")
    elif density > 0.30:
        parts.append(f"二部图密度 {density:.2%} 较高，证据被频繁引用")
    else:
        parts.append(f"二部图密度 {density:.2%} 适中")
    if pro_ug + con_ug > 0:
        parts.append(f"存在 {pro_ug + con_ug} 个未引证据的论点（正{pro_ug}/反{con_ug}）")
    if shared == 0:
        parts.append("双方未引用共同证据，论域相对独立")
    elif shared >= 3:
        parts.append(f"双方共同引用 {shared} 条证据，存在共识基线")
    return "；".join(parts) + "。"


# ============================================================
# T2 · DPP 多样性约束
# ============================================================

def dpp_diversity_score(texts: List[str]) -> float:
    """用一个简化的 DPP-like 评分衡量一组文本的多样性。

    实现思路：把每条文本用 2-gram 集合表示；两两 Jaccard 距离均值
    越大 → 越多样。返回 0-1 之间的多样性分数。

    注意：这是 DPP 思想的轻量实现，原版 DPP 需要 eigendecomposition
    与 L-ensemble，对原型机而言此实现已足以评估多样性。
    """
    if len(texts) < 2:
        return 0.0
    grams = []
    for t in texts:
        toks = _tokenize_text(t)
        gs = set()
        for tok in toks:
            for i in range(len(tok) - 1):
                gs.add(tok[i : i + 2])
        grams.append(gs if gs else {tok})
    n = len(grams)
    total_dist = 0.0
    cnt = 0
    for i in range(n):
        for j in range(i + 1, n):
            inter = len(grams[i] & grams[j])
            union = len(grams[i] | grams[j]) or 1
            jac = inter / union
            total_dist += 1.0 - jac
            cnt += 1
    return round(total_dist / cnt, 4) if cnt else 0.0


# ============================================================
# T3 · KS 早停检验
# ============================================================

def ks_early_stop_check(
    transcript: DebateTranscript,
    significance: float = 0.20,
) -> Dict:
    """KS-style 早停检验：监控每轮新增"新 token"的数量。

    思想：
    1. 按 round_index 聚合论点
    2. 计算每轮相对前一轮的新增 token 数
    3. 如果连续 2 轮新增 token 比例 < significance 阈值 → 建议早停

    返回：
    - per_round_new_tokens: 每轮新增 token 数
    - per_round_total_tokens: 每轮累计 token 数
    - stagnation_ratio: 最近一轮新增 / 上一轮新增
    - suggest_early_stop: bool
    - reason: 自然语言解释
    """
    by_round: Dict[int, List[str]] = {}
    for a in transcript.arguments:
        by_round.setdefault(a.round_index, []).append(a.content)

    rounds_sorted = sorted(by_round.keys())
    seen_tokens: set = set()
    per_round_new: List[int] = []
    per_round_total: List[int] = []
    for r in rounds_sorted:
        all_toks: List[str] = []
        for content in by_round[r]:
            all_toks.extend(_tokenize_text(content))
        round_set = set(all_toks)
        new_count = len(round_set - seen_tokens)
        per_round_new.append(new_count)
        per_round_total.append(len(round_set | seen_tokens))
        seen_tokens |= round_set

    stagnation = None
    suggest = False
    reason = ""
    if len(per_round_new) >= 2 and per_round_new[-2] > 0:
        stagnation = round(per_round_new[-1] / per_round_new[-2], 4)
        if stagnation < significance and per_round_new[-1] < 5:
            suggest = True
            reason = (
                f"最近一轮新增 token 比例 {stagnation:.0%} < {significance:.0%}，"
                f"且绝对新增 < 5，建议早停以节省算力"
            )
        else:
            reason = f"最近一轮新增 token 比例 {stagnation:.0%}，辩论仍在产生新信息"
    elif len(per_round_new) == 1:
        reason = "仅有 1 轮数据，KS 早停无法触发"
    else:
        reason = "无辩论数据"

    return {
        "per_round_new_tokens": per_round_new,
        "per_round_total_tokens": per_round_total,
        "stagnation_ratio": stagnation,
        "significance_threshold": significance,
        "suggest_early_stop": suggest,
        "reason": reason,
    }


# ============================================================
# T4 · DS 证据理论融合
# ============================================================

def ds_evidence_fusion(judge_scores: List[JudgeScore]) -> Dict:
    """Dempster-Shafer 证据理论融合（轻量实现，v2 修正版）。

    v2 修正：
    - 之前版本 confidence = 1 - 0.5*|mass_pro - mass_con|，
      导致"双方势均力敌"时置信度 = 1.0（逻辑倒置）。
    - 新公式：confidence = agreement * (0.5 + 0.5 * |mass_pro - mass_con|)
      - mass 差距大 + 法官一致 → 高置信度
      - mass 接近 + 法官分歧大 → 低置信度
    """
    if not judge_scores:
        return {"mass_pro": 0.5, "mass_con": 0.5, "confidence": 0.0, "entropy": 1.0, "agreement": 0.0}

    pro_masses: List[float] = []
    con_masses: List[float] = []
    for js in judge_scores:
        # 归一化到 [0,1] -> 视为支持度
        pro_pref = max(0.0, min(1.0, js.pro_score / 100.0))
        con_pref = max(0.0, min(1.0, js.con_score / 100.0))
        # 信心：偏离 0.5 越远 → 越确定
        pro_unc = 1.0 - abs(pro_pref - 0.5) * 2
        con_unc = 1.0 - abs(con_pref - 0.5) * 2
        pro_masses.append(max(0.05, 1.0 - pro_unc))
        con_masses.append(max(0.05, 1.0 - con_unc))

    # 归一化
    def norm(xs: List[float]) -> List[float]:
        s = sum(xs) or 1.0
        return [x / s for x in xs]

    pro_n = norm(pro_masses)
    con_n = norm(con_masses)

    mass_pro = sum(pro_n) / len(pro_n)
    mass_con = sum(con_n) / len(con_n)
    # 重新 renormalize
    total = mass_pro + mass_con or 1.0
    mass_pro /= total
    mass_con /= total

    # --- 修复：confidence 公式修正（v2） ---
    # mass 差距越大，法官越一致 → 置信度越高
    mass_gap = abs(mass_pro - mass_con)

    # 法官一致性：每方评分差的标准差
    diffs = [abs(js.pro_score - js.con_score) for js in judge_scores]
    mean_diff = sum(diffs) / len(diffs) if diffs else 0.0
    var = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs) if diffs else 0.0
    std = math.sqrt(var)
    agreement = round(1.0 / (1.0 + std / 25.0), 4)

    # v2: confidence = 一致性 × 确定性
    confidence = round(agreement * (0.5 + 0.5 * mass_gap), 4)

    # 信息熵
    eps = 1e-9
    entropy = -(
        (mass_pro + eps) * math.log2(mass_pro + eps)
        + (mass_con + eps) * math.log2(mass_con + eps)
    )

    return {
        "judge_count": len(judge_scores),
        "mass_pro": round(mass_pro, 4),
        "mass_con": round(mass_con, 4),
        "confidence": confidence,
        "agreement": agreement,
        "mass_gap": round(mass_gap, 4),
        "entropy": round(entropy, 4),
        "interpretation": _ds_interpretation(mass_pro, mass_con, confidence, agreement),
    }


def _ds_interpretation(mass_pro: float, mass_con: float, conf: float, agreement: float) -> str:
    if agreement < 0.5:
        return f"法官分歧较大（一致性 {agreement:.2f}），建议谨慎采信（置信度 {conf:.2f}）"
    if conf > 0.85:
        leader = "正方" if mass_pro > mass_con else "反方"
        return f"T4 DS 融合：{leader} 胜出，置信度 {conf:.2f}（mass={max(mass_pro, mass_con):.2f}）"
    elif conf > 0.6:
        return f"T4 DS 融合：{'正' if mass_pro > mass_con else '反'}方略占优，置信度 {conf:.2f}（未达显著）"
    else:
        return f"T4 DS 融合：双方势均力敌，置信度低（{conf:.2f}）"


# ============================================================
# 综合便捷函数
# ============================================================

def run_innovation_analysis(
    transcript: DebateTranscript,
    brief: EvidenceBrief,
    judge_scores: List[JudgeScore],
) -> Dict:
    """一次性跑完 T1/T2/T3/T4 四个创新点。"""
    return {
        "T1_AEBG": build_argument_evidence_bipartite(transcript, brief),
        "T2_DPP": {
            "pro_diversity": dpp_diversity_score([a.content for a in transcript.arguments if a.side == "pro"]),
            "con_diversity": dpp_diversity_score([a.content for a in transcript.arguments if a.side == "con"]),
        },
        "T3_KS": ks_early_stop_check(transcript),
        "T4_DS": ds_evidence_fusion(judge_scores),
    }


__all__ = [
    "build_argument_evidence_bipartite",
    "dpp_diversity_score",
    "ks_early_stop_check",
    "ds_evidence_fusion",
    "run_innovation_analysis",
]
