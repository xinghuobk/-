# ParaJudge AutoDriver Δ 报告 · auto-v32

- 生成时间: 2026-06-19 21:57:06
- 系统版本: auto-v32
- 整体健康度: **99.55/100**
- 本轮实验数: 1
- 本轮 patch 数: 2
- 外部检索命中: 6

## 1. 系统快照
- 源码文件: 37
- 总代码行: 6851
- 注释率: 0.077
- TODO/FIXME: 0/0
- 问题总数: 0 (open=0 fixed=0)
- 累计实验: 31

**Suggestions**:
- 尚未做任何实验，建议建立基线 baseline

## 2. 模块健康度
- `src/judgment/judgment_engine.py`: 健康度 100.0, lines=360, TODO=0, FIXME=0, magic=0
- `src/judgment/judgment_config.py`: 健康度 100.0, lines=69, TODO=0, FIXME=0, magic=0
- `src/debate/moderator.py`: 健康度 100.0, lines=448, TODO=0, FIXME=0, magic=0
- `src/debate/simple_debate.py`: 健康度 97.0, lines=313, TODO=0, FIXME=0, magic=1
- `src/debate/prompts.py`: 健康度 100.0, lines=309, TODO=0, FIXME=0, magic=0
- `src/debate/evidence_builder.py`: 健康度 97.0, lines=201, TODO=0, FIXME=0, magic=1
- `src/orchestration/orchestrator.py`: 健康度 100.0, lines=402, TODO=0, FIXME=0, magic=0
- `src/writer/llm_client.py`: 健康度 100.0, lines=463, TODO=0, FIXME=0, magic=0

## 3. 自我反思
- summary: mock 反思：上一轮实验平局偏多，建议增加 judge 多样性
- next_iteration_focus: **增加 judge 多样性 + 语义反驳**
- 优势:端到端可跑; 有证据链
- 弱点:关键词重叠粗糙; 无多重比较校正; judge 多样性不足

### 反思优先级建议
- [medium] **给 judge panel 增加 diversity prompt** — 降低共识偏差是最大风险
- [large] **语义反驳替代关键词重叠** — 关键词太粗糙
- [small] **多重比较校正** — 统计检验假阳性风险

## 4. 外部检索
- [web (offline)] **Dempster-Shafer evidence theory 与 Zadeh 悖论** — 经典 Dempster 组合规则在高冲突证据下会出现反直觉结论（Zadeh 悖论）。ParaJudge 当前用近似正交和应谨慎对待冲突情形。 (https://en.wikipedia.org/wiki/Dempster%27s_rule_of_combination)
- [web (offline)] **DS theory 用于多源融合** — DS 理论在辩论系统中融合多位 judge 评分时，冲突权重调整非常关键。 (https://www.sciencedirect.com/)
- [web (offline)] **Argumentation mining 中的反驳检测** — 现代论点-反驳关系检测一般采用句子嵌入（如 sentence-transformers），关键词重叠只是基线方法，通常相关度在 0.3~0.5 之间。 (https://aclanthology.org/)
- [web (offline)] **Semantic similarity for argumentative text** — all-MiniLM-L6-v2 在论点-反驳匹配上显著优于关键词重叠。 (https://www.sbert.net/)
- [web (offline)] **Holm-Bonferroni 多重比较校正** — 同一问题重复多次统计检验时，需要控制 family-wise error rate。 (https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method)
- [web (offline)] **Familywise error rate overview** — 辩论系统 multi-run setting 下 α 控制是严谨科研的必要条件。 (https://en.wikipedia.org/wiki/Family-wise_error_rate)

## 5. 实验结果
### 1. `creative_fallback` — 反思驱动实验
- run_id: `1aa9d29e`
- problem: 远程办公是否应成为主流？
- winner: tie
- pro_score: 53.4 / con_score: 54.2
- rounds: 3 / total_time: 1.1s


## 6. 代码修改提案
- 📄 仅提案 `src/judgment/judgment_engine.py`: 给 judge 增加 diversity prompt 标记 — 增加 judge 多样性 + 语义反驳
- 📄 仅提案 `src/debate/moderator.py`: 用语义相似度替代关键词重叠 — 增加 judge 多样性 + 语义反驳

---
_由 scripts.autodriver.AutoDriver 于 2026-06-19 21:57:06 生成_