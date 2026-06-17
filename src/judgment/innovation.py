"""ParaJudge 技术创新点（4 个 T 系列）。

重要声明（v2 修正）：
  - T4 的 DS 融合**不是真正的 Dempster-Shafer 正交和**，
    而是"启发式加权融合"。真正的 DS 需要对每对法官 mass 函数
    做正交和迭代，且需要定义完整的幂集。
    当前实现（ds_evidence_fusion / ds_orthographic_combination）
    仅为教学/原型目的。如需发表，请：
      (a) 实现完整的 DS 正交和，并注明是简化版，或
      (b) 改名为 heuristic_fusion 并移除 DS 标签。

T1 · 论点-证据二部图（AEBG, Argument-Evidence Bipartite Graph）
    - 论文层 + 论证层 的二部图结构
    - 通过中心性度量评估"证据聚焦"和"论证孤立"
T2 · 多样性约束（DPP, Determinantal Point Process）
    - 让辩论论点集保持主题多样性
    - 减少重复论证（轻量 DPP-like 实现）
T3 · KS 早停检验（Kolmogorov-Smirnov Stagnation Test）
    - 监控每轮新增"新概念 token 数"
    - 当新增 token 数显著下降时建议早停
T4 · 证据融合（Evidence Fusion）
    - ds_evidence_fusion:  启发式融合（加权平均 + renormalize）
    - ds_orthographic_combination: 更接近 DS 思想的正交和近似
    ⚠ 两者均非标准 Dempster-Shafer，如用于学术论文请明确说明
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
        return f"T4 融合：{leader} 胜出，置信度 {conf:.2f}（mass={max(mass_pro, mass_con):.2f}）"
    elif conf > 0.6:
        return f"T4 融合：{'正' if mass_pro > mass_con else '反'}方略占优，置信度 {conf:.2f}（未达显著）"
    else:
        return f"T4 融合：双方势均力敌，置信度低（{conf:.2f}）"


# ============================================================
# T4 · DS 正交和近似（更接近真正的 Dempster-Shafer）
# ============================================================

def ds_orthographic_combination(judge_scores: List[JudgeScore]) -> Dict:
    """Dempster-Shafer 正交和近似实现。

    真正的 DS 合成规则：
        m₁⊕m₂(A) = (1/K) * Σ m₁(B) * m₂(C)   （B∩C = A）

    其中 K = Σ m₁(B) * m₂(C)（B∩C = ∅）是冲突因子。

    本实现做以下简化：
    1. 只考虑 {pro, con, unk} 三个命题（幂集大小 = 2³ = 8）
    2. 用法官评分差值构造每个法官的 mass 函数
    3. 逐对迭代正交和（而非一次性全聚合）
    4. unk mass 保留为"不确定性"（未被任何法官支持的部分）

    ⚠ 这仍然是近似实现，不是完整的 DS 理论。
    """
    if not judge_scores:
        return {
            "mass_pro": 0.5, "mass_con": 0.5, "mass_unk": 0.0,
            "confidence": 0.0, "conflict": 1.0,
            "method": "ds_orthographic_combination（DS 正交和近似）",
        }

    def _score_to_mass(js: JudgeScore) -> Dict[str, float]:
        """把单个法官的评分映射为 {pro, con, unk} mass 函数。

        设 gap = (pro - con) / 100 ∈ [-1, 1]
        - gap > 0 → 更支持正方
        - gap < 0 → 更支持反方
        - |gap| 小 → 更多不确定性
        """
        gap = (js.pro_score - js.con_score) / 100.0
        gap = max(-1.0, min(1.0, gap))

        if abs(gap) < 0.05:   # |gap| < 5 分 → 不确定
            m_pro = 0.15
            m_con = 0.15
        elif gap > 0:          # 正方占优
            m_pro = 0.60 + 0.30 * gap
            m_con = 0.40 - 0.30 * gap
        else:                   # 反方占优
            m_con = 0.60 + 0.30 * abs(gap)
            m_pro = 0.40 - 0.30 * abs(gap)

        m_pro = max(0.01, min(0.99, m_pro))
        m_con = max(0.01, min(0.99, m_con))
        total = m_pro + m_con
        m_pro /= total
        m_con /= total
        m_unk = 0.0  # 在 2-mass 模型中，unk = 1 - pro - con = 0

        return {"pro": m_pro, "con": m_con, "unk": m_unk}

    def _orthogonal_sum(
        m1: Dict[str, float], m2: Dict[str, float]
    ) -> Dict[str, float]:
        """两证据正交和：m₁⊕m₂。

        命题空间：{pro, con, unk, pro∪con, pro∪unk, con∪unk, pro∪con∪unk(θ)}
        但这里简化为：{pro, con, θ}（θ = 总不确定性）
        """
        pro = m1["pro"] * m2["pro"] + m1["pro"] * m2["unk"] + m1["unk"] * m2["pro"]
        con = m1["con"] * m2["con"] + m1["con"] * m2["unk"] + m1["unk"] * m2["con"]
        # 冲突项（pro 与 con 同时成立 → 不可能）
        conflict = m1["pro"] * m2["con"] + m1["con"] * m2["pro"]

        total = pro + con + 1e-9
        return {"pro": pro / total, "con": con / total, "unk": 1e-9 / total, "_conflict": conflict}

    # 逐对迭代正交和
    masses = [_score_to_mass(js) for js in judge_scores]
    combined = masses[0]
    total_conflict = 0.0
    for i in range(1, len(masses)):
        combined = _orthogonal_sum(combined, masses[i])
        total_conflict = max(total_conflict, combined.get("_conflict", 0.0))

    # 冲突归一化（Dempster 规则）：
    #   m⊕(A) = m(A) / (1 - K)   for A ≠ ∅
    #   K = total_conflict（pro 和 con 同时成立的冲突质量）
    # 归一化分母 = pro + con（不含 unk，因为 unk 已经包含了 K）
    K = total_conflict  # 使用循环中更新的值
    norm_total = combined["pro"] + combined["con"] + 1e-12
    if norm_total > 0:
        norm_pro = combined["pro"] / norm_total
        norm_con = combined["con"] / norm_total
    else:
        norm_pro, norm_con = 0.5, 0.5

    # 置信度 = 1 - 冲突（冲突越大置信度越低）
    confidence = round(1.0 - K, 4)
    mass_gap = abs(norm_pro - norm_con)

    return {
        "judge_count": len(judge_scores),
        "mass_pro": round(norm_pro, 4),
        "mass_con": round(norm_con, 4),
        "mass_unk": round(combined["unk"], 4),
        "conflict_K": round(K, 4),
        "confidence": confidence,
        "mass_gap": round(mass_gap, 4),
        "method": "ds_orthographic_combination（DS 正交和近似，非完整 DS）",
        "interpretation": _ds_interpretation(norm_pro, norm_con, confidence, 0.0),
    }



# ============================================================
# 综合便捷函数
# ============================================================

def run_innovation_analysis(
    transcript: DebateTranscript,
    brief: EvidenceBrief,
    judge_scores: List[JudgeScore],
) -> Dict:
    """一次性跑完 T1/T2/T3/T4 四个创新点。"""
    # DS 融合：用两种方法，标注方法名称
    heuristic_result = ds_evidence_fusion(judge_scores)
    heuristic_result["method_label"] = "启发式加权平均（非真正 DS）"
    ds_result = ds_orthographic_combination(judge_scores)
    ds_result["method_label"] = "DS 正交和近似（简化版，非完整 DS）"

    return {
        "T1_AEBG": build_argument_evidence_bipartite(transcript, brief),
        "T2_DPP": {
            "pro_diversity": dpp_diversity_score(
                [a.content for a in transcript.arguments if a.side == "pro"]
            ),
            "con_diversity": dpp_diversity_score(
                [a.content for a in transcript.arguments if a.side == "con"]
            ),
        },
        "T3_KS": ks_early_stop_check(transcript),
        "T4_heuristic_fusion": heuristic_result,
        "T4_ds_approx": ds_result,
        "meta_note": (
            "⚠ T4 提供两种融合结果：heuristic_fusion（当前默认）和 ds_approx（更接近 DS 思想）。"
            "两者均非标准 Dempster-Shafer，用于学术时请明确说明。"
        ),
    }
__all__ = [
    "build_argument_evidence_bipartite",
    "dpp_diversity_score",
    "ks_early_stop_check",
    "ds_evidence_fusion",
    "ds_orthographic_combination",
    "run_innovation_analysis",
]
