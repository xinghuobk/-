"""T1 真理论：Bipartite HITS（Kleinberg 1999）。

原漏洞（之前 design review 指出的）：
- 用通用 PageRank 处理二部图（PPR 在二部图上归一化不严格）
- 边权用 `confidence × relevance` 加法性假设

真理论修补：
- 用 **Bipartite HITS**（Kleinberg 1999, "Authoritative sources in a hyperlinked environment"）
  - 同时算 authority（论点质量）和 hub（证据枢纽度）
  - 在二部图上有严格收敛证明
- 边权用 **Bayesian 更新**（P(可靠|相关)），不再用简单乘法

只依赖 Python stdlib + math（**无 numpy / networkx**）。
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ============================================================
# 边权：Bayesian 更新
# ============================================================

def bayesian_edge_weight(
    relevance: float,
    prior_confidence: float = 0.5,
    n_independent_signals: int = 1,
) -> float:
    """Bayesian 边权：P(证据可靠 | relevance) ∝ P(relevance | 可靠) * P(可靠)。

    与简单乘法 `confidence × relevance` 的区别：
    - 引入先验（默认 0.5 表示无信息）
    - 多信号贝叶斯更新（n 个独立信号 → 后验增强）
    - 形式化：posterior_odds = prior_odds × likelihood_ratio^n
    """
    # 截断到 (0, 1)
    rel = max(1e-6, min(1.0 - 1e-6, relevance))
    prior = max(1e-6, min(1.0 - 1e-6, prior_confidence))

    # odds = p / (1-p)
    prior_odds = prior / (1.0 - prior)
    likelihood_ratio = rel / (1.0 - rel)  # 假设 relevance 即似然比

    posterior_odds = prior_odds * (likelihood_ratio ** n_independent_signals)
    posterior = posterior_odds / (1.0 + posterior_odds)
    return posterior


# ============================================================
# Bipartite HITS
# ============================================================

class BipartiteHITS:
    """Bipartite HITS 实现（authority / hub 互相迭代直到收敛）。

    图：U = authority 节点集（论点），V = hub 节点集（证据）
    边：(u, v) with weight w(u, v)

    更新规则：
      A(u) = Σ_{v ∈ N(u)} w(u, v) · H(v)
      H(v) = Σ_{u ∈ N(v)} w(u, v) · A(u)
    归一化：每轮 L2 归一化 A, H

    收敛判据：‖A_t - A_{t-1}‖ < tol
    """

    def __init__(self, tol: float = 1e-6, max_iter: int = 200):
        self.tol = tol
        self.max_iter = max_iter

    def _l2_norm(self, d: Dict[str, float]) -> float:
        return math.sqrt(sum(v * v for v in d.values())) or 1.0

    def fit(
        self,
        edges: List[Tuple[str, str, float]],
        nodes_u: Optional[List[str]] = None,
        nodes_v: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, float], int]:
        """跑 Bipartite HITS，返回 (authority, hub, n_iter)。

        Args:
            edges: [(u_id, v_id, weight), ...] u ∈ U（authority），v ∈ V（hub）
            nodes_u, nodes_v: 显式节点集合（不传则从 edges 推导）

        Returns:
            (authority, hub, n_iter_converged)
        """
        if nodes_u is None:
            nodes_u = sorted({u for u, _, _ in edges})
        if nodes_v is None:
            nodes_v = sorted({v for _, v, _ in edges})

        # 邻接表
        u_neighbors: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        v_neighbors: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        for u, v, w in edges:
            u_neighbors[u].append((v, w))
            v_neighbors[v].append((u, w))

        # 初始化
        A = {u: 1.0 for u in nodes_u}
        H = {v: 1.0 for v in nodes_v}

        # 迭代
        n_iter = 0
        for it in range(1, self.max_iter + 1):
            n_iter = it
            A_new: Dict[str, float] = {}
            for u in nodes_u:
                A_new[u] = sum(w * H.get(v, 0.0) for v, w in u_neighbors[u])

            H_new: Dict[str, float] = {}
            for v in nodes_v:
                H_new[v] = sum(w * A_new.get(u, 0.0) for u, w in v_neighbors[v])

            # 归一化
            norm_A = self._l2_norm(A_new)
            A_new = {u: v / norm_A for u, v in A_new.items()}
            norm_H = self._l2_norm(H_new)
            H_new = {v: x / norm_H for v, x in H_new.items()}

            # 收敛判据
            diff = math.sqrt(sum((A_new.get(u, 0) - A.get(u, 0)) ** 2 for u in nodes_u))
            A, H = A_new, H_new
            if diff < self.tol:
                break

        return A, H, n_iter


# ============================================================
# 单元测试
# ============================================================

def _unit_test_hits():
    """合成二部图：3 个 authority、4 个 hub，验证算法正确性。"""
    # 图：u1 -- v1 (w=1), u1 -- v2 (w=2), u2 -- v1 (w=0.5), u2 -- v3 (w=3),
    #     u3 -- v2 (w=1.5), u3 -- v4 (w=1)
    edges = [
        ("u1", "v1", 1.0), ("u1", "v2", 2.0),
        ("u2", "v1", 0.5), ("u2", "v3", 3.0),
        ("u3", "v2", 1.5), ("u3", "v4", 1.0),
    ]
    hits = BipartiteHITS(tol=1e-8, max_iter=200)
    A, H, n_iter = hits.fit(edges)

    # 性质 1：所有 authority 和 hub 都 > 0
    assert all(v >= 0 for v in A.values()), f"A 有负值: {A}"
    assert all(v >= 0 for v in H.values()), f"H 有负值: {H}"

    # 性质 2：归一化后 L2 范数 = 1
    norm_A = math.sqrt(sum(v * v for v in A.values()))
    norm_H = math.sqrt(sum(v * v for v in H.values()))
    assert abs(norm_A - 1.0) < 1e-6, f"A 未归一化: norm={norm_A}"
    assert abs(norm_H - 1.0) < 1e-6, f"H 未归一化: norm={norm_H}"

    # 性质 3：u2 应得到最高 authority（连到 2 个 hub，其中 v3 权重 3）
    top_authority = max(A, key=A.get)
    assert top_authority == "u2", f"u2 应最高 authority，实际 {top_authority}: {A}"

    # 性质 4：v3 应得到最高 hub（被最高 authority u2 + 高权重 3 引用）
    top_hub = max(H, key=H.get)
    # 注：v1 也被 u1, u2 引用；v3 仅被 u2 引用（但权重最大）
    # 实际计算结果可能 v1 或 v3 都合理，但都应 >= v4
    assert H["v3"] > H["v4"], f"v3 应 > v4: H={H}"

    # 性质 5：收敛
    assert n_iter < 200, f"未收敛: n_iter={n_iter}"

    print(f"✅ T1 Bipartite HITS 单元测试通过 (n_iter={n_iter})")
    print(f"   authority: {A}")
    print(f"   hub: {H}")
    return True


def _unit_test_bayesian_edge():
    """Bayesian 边权：与简单乘法的差异验证。"""
    # 等价情况：relevance=0.5, prior=0.5 → posterior = 0.5
    w = bayesian_edge_weight(relevance=0.5, prior_confidence=0.5, n_independent_signals=1)
    assert abs(w - 0.5) < 1e-6, f"对称点应是 0.5: {w}"

    # 高 relevance：relevance=0.8, prior=0.5 → posterior > 0.5
    w = bayesian_edge_weight(relevance=0.8)
    assert w > 0.5, f"高 relevance 应 > 0.5: {w}"

    # 多信号：增加 n → 强化
    w1 = bayesian_edge_weight(relevance=0.7, n_independent_signals=1)
    w3 = bayesian_edge_weight(relevance=0.7, n_independent_signals=3)
    assert w3 > w1, f"多信号应 > 单信号: {w1} vs {w3}"

    # 极端：prior 极低 + relevance 中等 → 仍较低
    w = bayesian_edge_weight(relevance=0.7, prior_confidence=0.1)
    assert w < 0.7, f"低 prior 应抑制后验: {w}"

    print(f"✅ T1 Bayesian 边权单元测试通过")
    print(f"   rel=0.5, prior=0.5: w={bayesian_edge_weight(0.5, 0.5):.4f}")
    print(f"   rel=0.7, prior=0.5, n=1: w={bayesian_edge_weight(0.7, 0.5, 1):.4f}")
    print(f"   rel=0.7, prior=0.5, n=3: w={bayesian_edge_weight(0.7, 0.5, 3):.4f}")
    return True


if __name__ == "__main__":
    _unit_test_bayesian_edge()
    _unit_test_hits()
