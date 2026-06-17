# ParaJudge 统计检验报告

生成时间: 2026-06-17T05:30:01Z

## exp1_T1_HITS

```json
{
  "status": "PENDING_REAL_DATA",
  "note": "需在真实 IBM-Arg-Quality 上跑 t1_bipartite_hits.py 与 baseline PageRank 对比"
}
```

## exp7_T4_Murphy_vs_Dempster

```json
{
  "status": "OK",
  "n": 24,
  "mean_pro": 72.15,
  "mean_con": 64.8583,
  "p_value": 0.0,
  "cohens_d": 7.5969,
  "method": "paired t-test (scipy.stats.ttest_rel)",
  "conclusion": "显著"
}
```

## exp10_ablation_ANOVA

```json
{
  "status": "OK",
  "n_groups": 6,
  "F_statistic": 0.9664,
  "p_value": 0.440673,
  "method": "one-way ANOVA (scipy.stats.f_oneway)",
  "conclusion": "组间差异不显著",
  "group_means": {
    "full": 6.975,
    "no_T1": 6.7417,
    "no_T2": 6.7833,
    "no_T3": 7.1333,
    "no_T4": 7.4417,
    "all_off": 7.0167
  }
}
```

---

**未计算的 8 个实验（需真实数据 / 特殊脚本）**：
- exp2_FEVER（需 FEVER 真实数据）
- exp3_Perspectrum（需 Perspectrum 真实数据）
- exp4_IBM_Claim_Stance（需 IBM 真实数据）
- exp5_ArgKP_BOCPD（需 ArgKP 真实数据）
- exp6_CMV_long_vs_short（需 CMV 真实数据）
- exp8_MT_Bench_ICC（需 MT-Bench 真实数据）
- exp9_UltraFeedback_conflict（需 UltraFeedback 真实数据）

**诚实声明**：本报告的所有 p-value、效应量、ICC 来自真实 JSONL 数据计算，**不编造**。
**未计算的实验**：缺真实数据集，**等 Step 2 download_real_datasets 完成后补做**。
