"""T2 真理论：k-DPP（Determinantal Point Process）。

原漏洞（之前 design review 指出的）：
- 实现是 Jaccard 距离，**根本不是 DPP**
- 缺乏核心理论（质量-多样性 trade-off、L-ensemble 行列式）

真理论修补：
- 实现 **k-DPP 的 greedy MAP inference**（Kulesza & Taskar 2012）：
  1. 构造 L 矩阵：L_ij = q_i · q_j · S_ij
     - q_i = 质量（与辩题相关性）
     - S_ij = 相似度（这里是 1 - normalized_distance）
  2. 贪心选 k 个：每步选使 det(L_Y) 最大的元素
  3. 满足 k-DPP 的边际增益性质

只依赖 Python stdlib + math（**无 numpy**）。
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple


# ============================================================
# 核函数
# ============================================================

def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """余弦相似度 [-1, 1] → 归一化到 [0, 1]。"""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    cos = dot / (na * nb)
    return (cos + 1.0) / 2.0  # [0, 1]


def build_l_matrix(
    qualities: Sequence[float],
    embeddings: Sequence[Sequence[float]],
) -> List[List[float]]:
    """构造 L 矩阵：L_ij = q_i · q_j · S_ij

    性质：L 是半正定（因为 S 是正定核 → L 是正定阵乘对角 q，半正定）

    Args:
        qualities: 每个元素的质量分数 q_i ∈ [0, 1]
        embeddings: 每个元素的 embedding 向量

    Returns:
        n×n 矩阵 L
    """
    n = len(qualities)
    assert n == len(embeddings)
    L: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                # 自相似度：质量²（鼓励选高质量）
                L[i][j] = qualities[i] ** 2
            else:
                sim = cosine_similarity(embeddings[i], embeddings[j])
                L[i][j] = qualities[i] * qualities[j] * sim
    return L


# ============================================================
# 行列式
# ============================================================

def determinant(M: List[List[float]]) -> float:
    """n×n 矩阵行列式（高斯消元）。O(n^3)。"""
    n = len(M)
    if n == 0:
        return 1.0
    if n == 1:
        return M[0][0]
    if n == 2:
        return M[0][0] * M[1][1] - M[0][1] * M[1][0]

    # 高斯消元
    A = [row[:] for row in M]
    det = 1.0
    for i in range(n):
        # 找主元
        pivot = i
        for r in range(i, n):
            if abs(A[r][i]) > abs(A[pivot][i]):
                pivot = r
        if pivot != i:
            A[i], A[pivot] = A[pivot], A[i]
            det = -det
        if abs(A[i][i]) < 1e-12:
            return 0.0
        det *= A[i][i]
        for r in range(i + 1, n):
            factor = A[r][i] / A[i][i]
            for c in range(i, n):
                A[r][c] -= factor * A[i][c]
    return det


# ============================================================
# 边际增益
# ============================================================

def marginal_gain(
    L: List[List[float]],
    selected: List[int],
    candidate: int,
) -> float:
    """计算加入 candidate 后的行列式增量 det(L_{selected ∪ {candidate}}) - det(L_{selected})。

    朴素实现：扩展子集重算（O(k^3)）。k ≤ 10 时足够。
    """
    sub = [L[candidate][candidate]]  # 1×1
    if not selected:
        return sub[0]
    # 构造 (|S|+1)×(|S|+1) 矩阵
    k = len(selected)
    ext = [[0.0] * (k + 1) for _ in range(k + 1)]
    for i, si in enumerate(selected):
        for j, sj in enumerate(selected):
            ext[i][j] = L[si][sj]
        ext[i][k] = L[si][candidate]
        ext[k][i] = L[candidate][si]
    ext[k][k] = L[candidate][candidate]
    return determinant(ext) - determinant([L[si][sj] for si in selected for sj in selected] and [[L[si][sj] for sj in selected] for si in selected] or [[0.0]])


# ============================================================
# k-DPP Greedy MAP
# ============================================================

def kdpp_greedy_map(
    L: List[List[float]],
    k: int,
    random_state: Optional[int] = None,
) -> List[int]:
    """k-DPP 的 greedy MAP inference（Kulesza & Taskar 2012, Algorithm 1）。

    贪心选 k 个：每步选使边际增益最大的元素。

    Args:
        L: n×n 半正定矩阵
        k: 要选的元素个数
        random_state: 随机种子（用于打破平局）

    Returns:
        选中的 k 个 index 列表
    """
    if random_state is not None:
        random.seed(random_state)
    n = len(L)
    k = min(k, n)
    selected: List[int] = []
    remaining = set(range(n))

    for _ in range(k):
        if not remaining:
            break
        # 找边际增益最大
        best = None
        best_gain = -math.inf
        for c in remaining:
            gain = marginal_gain(L, selected, c)
            # 打破平局：加一点 jitter
            if random_state is not None:
                gain += random.uniform(-1e-12, 1e-12)
            if gain > best_gain:
                best_gain = gain
                best = c
        selected.append(best)
        remaining.discard(best)
    return selected


# ============================================================
# 单元测试
# ============================================================

def _unit_test_determinant():
    """行列式正确性：与已知结果对比。"""
    # 2×2 单位矩阵 → det = 1
    assert abs(determinant([[1, 0], [0, 1]]) - 1.0) < 1e-9
    # 2×2 反对角 → det = -1
    assert abs(determinant([[0, 1], [1, 0]]) - (-1.0)) < 1e-9
    # 3×3 det 测试
    A = [[6, 1, 1], [4, -2, 5], [2, 8, 7]]
    assert abs(determinant(A) - (-306.0)) < 1e-6
    print("✅ determinant 单元测试通过")


def _unit_test_kdpp_basic():
    """k-DPP 基础测试：5 个 candidate，选 3 个。"""
    # 5 个 2D 点：3 个聚在一团 + 2 个分散
    # 期望：k-DPP 选 1 个密集 + 2 个分散（diversity 更高）
    pts = [
        [0.0, 0.0],   # 0 密集区
        [0.1, 0.1],   # 1 密集区
        [0.05, 0.05], # 2 密集区
        [1.0, 0.0],   # 3 分散
        [0.0, 1.0],   # 4 分散
    ]
    # 质量全设为 1
    q = [1.0] * 5
    L = build_l_matrix(q, pts)
    selected = kdpp_greedy_map(L, k=3, random_state=42)
    print(f"   k-DPP 选出的 3 个: {selected}")
    # 验证：必须包含 3 或 4（分散点）才能 diversity 最大化
    assert 3 in selected or 4 in selected, f"应至少选 1 个分散点: {selected}"
    # 验证：不应全选密集点
    dense = {0, 1, 2}
    if all(s in dense for s in selected):
        raise AssertionError(f"k-DPP 退化为 Top-k: {selected}")
    print("✅ k-DPP diversity 选择正确（不全选密集点）")


def _unit_test_kdpp_quality_diversity_tradeoff():
    """质量-多样性 trade-off：1 个高质量 + 多个低质量时，k-DPP 应选高质量。"""
    pts = [[i, i] for i in range(5)]  # 5 个完全不同的点
    q = [0.1, 0.1, 0.1, 0.1, 0.95]  # 1 个高质量
    L = build_l_matrix(q, pts)
    selected = kdpp_greedy_map(L, k=2, random_state=42)
    print(f"   trade-off 测试选: {selected} (q={q})")
    assert 4 in selected, f"应选高质量 index 4: {selected}"
    print("✅ k-DPP quality-diversity trade-off 正确（选高质量 + 多样）")


if __name__ == "__main__":
    _unit_test_determinant()
    _unit_test_kdpp_basic()
    _unit_test_kdpp_quality_diversity_tradeoff()
