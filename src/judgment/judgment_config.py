"""ParaJudge 裁决与辩论核心配置。

所有魔法数字统一在此管理，方便调参与实验复现。
使用时：
    from src.judgment.judgment_config import CFG
    if score_diff > CFG.WINNER_THRESHOLD:
        ...
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgmentConfig:
    """裁决相关配置（不可变，防止运行时修改）。"""

    # ── 获胜判定阈值 ──────────────────────────────────────
    # 正方/反方得分差大于此值才判定该方获胜
    # 差值 < 阈值 → 平局
    WINNER_THRESHOLD: float = 5.0

    # ── Moderator 惩罚分（论点被标记违规后的分数扣减）─────
    PENALTY_OFF_TOPIC: float = -4.0      # 每条离题论点扣分
    PENALTY_DUPLICATE: float = -3.0      # 每条重复论点扣分
    PENALTY_TOO_LONG: float = -1.0      # 每条超长论点扣分
    PENALTY_CAP: float = -15.0          # 每方惩罚上限（绝对值）

    # ── Moderator 违规检测阈值 ─────────────────────────────
    OFF_TOPIC_THRESHOLD: float = 0.4     # 关键词重叠率低于此值 → 离题
    DUPLICATE_THRESHOLD: float = 0.85    # Jaccard 相似度高于此值 → 重复
    MAX_CHARS_PER_TURN: int = 800        # 单轮最大字符数（超过 → 超长）

    # ── T3 KS 早停检验参数 ─────────────────────────────────
    KS_STAGNATION_RATIO: float = 0.20    # 新增 token / 前轮 < 此值 → 停滞
    KS_ABSOLUTE_MIN: int = 5             # 绝对新增 token 下限（低于此值 → 早停）

    # ── 法官评分范围 ──────────────────────────────────────
    SCORE_MIN: float = 0.0
    SCORE_MAX: float = 100.0
    SCORE_DEFAULT: float = 50.0           # LLM 解析失败时的回退分数

    # ── 辩论轮次 ──────────────────────────────────────────
    DEFAULT_ROUNDS: int = 2
    MIN_ROUNDS: int = 1
    MAX_ROUNDS: int = 10

    # ── 证据包大小 ─────────────────────────────────────────
    DEFAULT_MAX_EVIDENCE: int = 5
    MAX_EVIDENCE_IN_DEBATER_PROMPT: int = 15
    MAX_EVIDENCE_IN_JUDGE_PROMPT: int = 10

    # ── DS 融合参数（启发式，非真正 Dempster-Shafer）──────
    # 当前实现是"加权平均 + renormalize"，不是 DS 正交和
    # 详见 innovation.py 的 docstring
    DS_AGREEMENT_SIGMA: float = 25.0   # 法官一致性公式分母（std 缩放因子）
    DS_LOW_CONFIDENCE: float = 0.6     # 置信度低于此值 → "势均力敌"
    DS_HIGH_CONFIDENCE: float = 0.85    # 置信度高于此值 → "明确胜出"

    # ── 法官分歧报告阈值 ──────────────────────────────────
    JUDGE_SPREAD_WARN: float = 25.0     # 最高-最低法官评分差 > 此值 → 报告分歧

    # ── 反驳检测 ─────────────────────────────────────────
    REBUTTAL_REQUIRED: bool = True       # 是否要求每轮必须回应对方最新论点
    REBUTTAL_MIN_KEYWORDS: int = 2      # 反驳中必须包含对方论点的关键词数量


# 全局单例（不可变）
CFG = JudgmentConfig()
