# AutoDriver · 迭代修复提案 auto-v0.1

- 生成时间: 2026-06-19 16:40:39
- 整体健康度: **99.55/100**
- 开放问题数: **0**

## 1. 核心开放问题
- (暂无开放问题) ✅

## 2. 模块健康度扫描
- judgment_engine（src/judgment/judgment_engine.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0
- innovation（src/judgment/innovation.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0
- moderator（src/debate/moderator.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0
- simple_debate（src/debate/simple_debate.py） 健康度 97.0, TODO=0, FIXME=0, magic_number_hits=1
- orchestrator（src/orchestration/orchestrator.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0
- evidence_builder（src/debate/evidence_builder.py） 健康度 97.0, TODO=0, FIXME=0, magic_number_hits=1
- judgment_config（src/judgment/judgment_config.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0
- prompts（src/debate/prompts.py） 健康度 100.0, TODO=0, FIXME=0, magic_number_hits=0

## 3. 本轮建议动作
1. **[P0]** (run_experiment) 辩论胜负是否能逼近真理（vs 地心说vs日心说问题） — target=CORE-Q-TRUTH-01
2. **[P0]** (run_experiment) 反驳机制是否真能检测论点不相交的情形 — target=CORE-Q-REBUTTAL-01
3. **[P1]** (run_experiment) 多轮重复是否降低统计检验 I 类错误（假阳性） — target=CORE-Q-STAT-01
4. **[P1]** (run_experiment) DS 正交和近似的有效性 vs 真正 Dempster's rule — target=CORE-Q-DS-01
5. **[P1]** (run_experiment) Baseline 辩论实验（mock 模式） — target=baseline-mock

## 4. 修复方向（高层建议，需人工审查）

1. **真理 vs 共识偏差**：辩论胜负 ≠ 真理。系统需：
   - 在高争议问题上降低 DS confidence
   - 记录并对比多轮辩论的胜负稳定性
   - 暴露法官 panel 的内部分歧（而非只输出一个胜者）
2. **反驳机制强度**：关键词重叠是下限。下一步：
   - 引入语义嵌入相似度（sentence-transformers 或 LLM embed）
   - 记录每一轮被反驳的论点索引，便于人工核查
3. **统计多重比较校正**：若同一问题重复 N 次辩论，使用 Holm/Bonferroni 调整
4. **DS 近似正交和**：建议在 .parajudge/metrics 里记录完整的 mass 表，而非仅最终置信度

> 本文件为 AutoDriver 自动生成的非侵入式提案，
> **不修改源码**，请人工审查后再决定是否落地。
