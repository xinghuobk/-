# ParaJudge AutoDriver Δ 报告 · auto-v0.1

- 生成时间: 2026-06-19 16:40:39
- 系统版本: auto-v0.1
- 整体健康度: **99.55/100**

## 1. 系统快照

- 代码文件数: 37
- 总代码行: 6851
- 注释率: 0.077
- TODO/FIXME: 0/0
- 问题总数: 0（open=0, fixed=0）
- 累计实验数: 0

### Suggestions
- 📊 尚未做任何实验。建议先建立 baseline。

## 2. 模块健康度
- judgment_engine: 健康度 100.0, lines=361, todo=0, fixme=0, magic=0
- innovation: 健康度 100.0, lines=490, todo=0, fixme=0, magic=0
- moderator: 健康度 100.0, lines=449, todo=0, fixme=0, magic=0
- simple_debate: 健康度 97.0, lines=314, todo=0, fixme=0, magic=1
- orchestrator: 健康度 100.0, lines=403, todo=0, fixme=0, magic=0
- evidence_builder: 健康度 97.0, lines=202, todo=0, fixme=0, magic=1
- judgment_config: 健康度 100.0, lines=70, todo=0, fixme=0, magic=0
- prompts: 健康度 100.0, lines=310, todo=0, fixme=0, magic=0

## 3. 本轮建议动作（Action Plan）
1. **[P0]** (run_experiment) 辩论胜负是否能逼近真理（vs 地心说vs日心说问题）
   - Rationale: 系统可能因为法官共识偏向流行但错误观点而输出错误结论。
   - Target: CORE-Q-TRUTH-01
2. **[P0]** (run_experiment) 反驳机制是否真能检测论点不相交的情形
   - Rationale: 关键词重叠过于粗糙，可能遗漏语义相关但措辞不同的反驳。
   - Target: CORE-Q-REBUTTAL-01
3. **[P1]** (run_experiment) 多轮重复是否降低统计检验 I 类错误（假阳性）
   - Rationale: 重复越多越容易偶然通过 t 检验，需多重比较校正（Bonferroni / Holm）。
   - Target: CORE-Q-STAT-01
4. **[P1]** (run_experiment) DS 正交和近似的有效性 vs 真正 Dempster's rule
   - Rationale: 目前实现为近似正交和，需量化与真实 Dempster 组合规则的差异。
   - Target: CORE-Q-DS-01
5. **[P1]** (run_experiment) Baseline 辩论实验（mock 模式）
   - Rationale: 系统尚无任何实验，需建立基线。
   - Target: baseline-mock

## 4. 实验结果
### baseline-mock: Baseline mock 实验（默认 3 轮）
- run_id: `76578ebc`
- problem: 远程办公是否应该成为主流
- winner: tie
- pro_score: 55.0 | con_score: 55.4
- rounds: 3 | time: 2.63s
- Expected observations:
  - pro/con 评分应接近对称（70/70 基线上浮动）
  - DS confidence 在无争议问题上应高于高争议问题
  - total_time 应在合理范围（< 30s，mock 下）

### belief_alignment_bias_test: 信念对齐偏差测试 — 模拟共识偏向伪结论
- run_id: `90dc0c7d`
- problem: 远程办公是否应该成为主流
- winner: tie
- pro_score: 55.0 | con_score: 55.4
- rounds: 3 | time: 1.31s
- Expected observations:
  - 对争议问题，DS confidence 应下降（表示存在冲突证据）
  - 在 3 轮重复后，胜负随机波动，不应系统性偏向一方

### rebuttal_coverage_sweep: 反驳覆盖率扫掠 — 不同关键词重叠阈值
- run_id: `50759379`
- problem: 人工智能是否会导致大规模失业
- winner: tie
- pro_score: 54.0 | con_score: 55.6
- rounds: 3 | time: 3.21s
- Expected observations:
  - 第 2/3 轮应记录 rebuttal_stats（WARN_NO_REBUTTAL 或 反驳有效）
  - 整体至少有 1 轮反驳被记录

## 5. 修复提案
- 文件: `/workspace/.parajudge/iterations/patch-proposal-auto-v0.1.md`

---
_本报告由 `scripts/autodriver.py` 自动生成。_