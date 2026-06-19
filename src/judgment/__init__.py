"""ParaJudge 审理与裁决模块（Phase 2.1 + Phase 2.2）。

- review_engine.py: 审理引擎（程序化 + LLM 检查）
- judgment_engine.py: 裁决引擎（5 位法官独立评分 + 推理链）
- innovation.py: T1-T4 技术创新点实现（AEBG / DPP / KS / DS）
"""
from .review_engine import ReviewEngine
from .judgment_engine import JudgmentEngine
from .innovation import (
    build_argument_evidence_bipartite,
    dpp_diversity_score,
    ks_early_stop_check,
    ds_evidence_fusion,
    run_innovation_analysis,
)

__all__ = [
    "ReviewEngine",
    "JudgmentEngine",
    "build_argument_evidence_bipartite",
    "dpp_diversity_score",
    "ks_early_stop_check",
    "ds_evidence_fusion",
    "run_innovation_analysis",
]
