# ParaJudge 测试参数矩阵与实验路线图

> v0.1.0 → v1.0.0 验证阶段 · 2026-06-17

---

## 一、实验目的

通过系统化的实验，确定 ParaJudge 各核心参数的最优配置，并验证 4 个技术创新点（T1-T4）是否真的对裁决质量有提升。

---

## 二、参数矩阵

### 2.1 LLM 推理参数

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `temperature` | 0.0, 0.3, **0.7**, 1.0, 1.3 | 0.7 | 越高越发散；辩论建议 0.7-1.0；裁决建议 0.3 |
| `max_tokens` | 200, **400**, 600, 1000 | 400 | 单次响应上限 |
| `top_p` | 0.5, 0.7, **0.9**, 1.0 | 0.9 | nucleus sampling 阈值 |
| `frequency_penalty` | -1, 0, **0.5**, 1, 2 | 0.5 | 抑制重复 |
| `presence_penalty` | -1, 0, **0.5**, 1, 2 | 0.5 | 鼓励新话题 |

### 2.2 辩论流程参数

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `rounds` | 1, 2, **3**, 5, 8 | 3 | 辩论轮数 |
| `max_evidence` | 5, 10, **20**, 30, 50 | 20 | 证据包最大条数 |
| `pro_stance` | (文本) | 自动生成 | 正方立场描述 |
| `con_stance` | (文本) | 自动生成 | 反方立场描述 |
| `enable_cross_examination` | False, **True** | True | 是否注入对方历史发言 |
| `evidence_diversity` | False, **True** | True | 是否启用 DPP（T2） |

### 2.3 主持人参数

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `strictness` | loose, **normal**, strict | normal | 干预严格度 |
| `duplicate_threshold` | 0.70, 0.80, **0.85**, 0.90, 0.95 | 0.85 | Jaccard 相似度阈值 |
| `off_topic_threshold` | 0.20, 0.30, **0.40**, 0.50, 0.60 | 0.40 | 关键词重合度阈值 |
| `max_seconds_per_turn` | 30, 60, **120**, 180 | 120 | 单轮最长秒数 |
| `max_tokens_per_turn` | 200, **400**, 600, 1000 | 400 | 单轮最长 token |

### 2.4 法官参数

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `judge_count` | 3, **5**, 7 | 5 | 独立法官数量 |
| `judge_weights` | uniform / custom | uniform | 法官权重 |
| `judge_temperature` | 0.0, 0.3, **0.3**, 0.7 | 0.3 | 法官裁决温度 |
| `disagreement_threshold` | 10, **15**, 20, 25 | 15 | 法官分歧阈值（> 此值触发不确定性标记） |

### 2.5 早停参数（T3 KS 检验）

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `enable_ks_test` | False, **True** | True | 是否启用 KS 早停 |
| `ks_alpha` | 0.01, 0.05, **0.10**, 0.15 | 0.10 | KS 检验显著性水平 |
| `min_rounds` | 1, **2**, 3 | 2 | 最少轮数（早停下限） |
| `ks_window` | 2, **3**, 5 | 3 | KS 比较窗口大小 |

### 2.6 DS 证据理论融合参数（T4）

| 参数 | 候选值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `fusion_method` | weighted_avg, **dempster_shafer**, weighted_majority | dempster_shafer | 法官分数融合方式 |
| `uncertainty_decay` | 0.5, **0.7**, 0.9 | 0.7 | 不确定性衰减系数 |
| `bpa_smoothing` | 0.0, 0.01, **0.05**, 0.1 | 0.05 | 零信任 BPA 平滑项 |

---

## 三、实验数据集（真实数据）

### 3.1 论文检索数据集

| 来源 | 用途 | 真实数据量 | 检索方式 |
| --- | --- | --- | --- |
| arXiv | 学术论文 | 200 万+ 篇 | API 检索 + 关键词 |
| Crossref | DOI 元数据 | 1.4 亿+ 条 | REST API |
| Semantic Scholar | 引用与摘要 | 2 亿+ 篇 | API |

### 3.2 辩题测试集（附录 A / 24 题）

#### 类别 A：技术预测（5 题）

1. LLM 是否会取代人类大部分工作？
2. AGI 是否会在 2030 年前实现？
3. 量子计算能否在 10 年内实现商业化？
4. Transformer 架构是否会被新模型取代？
5. RAG 是否会取代微调成为主流？

#### 类别 B：AI 影响（5 题）

6. AI 科研是否降低了学术创新的门槛？
7. AI 创造的新岗位是否能抵消被替代的岗位？
8. AI 辅助教学会取代传统教师吗？
9. AI 生成内容是否应受到版权保护？
10. AI 写论文是否应被认定为学术不端？

#### 类别 C：技术深度（5 题）

11. 大模型是否真正理解语言，还是仅是统计拟合？
12. AI 对齐问题是否可解？
13. 推理模型（如 o1/R1）是否代表新范式？
14. 多模态是否是 LLM 的必然方向？
15. 开源 LLM 是否会超越闭源？

#### 类别 D：伦理与社会（4 题）

16. AI 决策的"黑箱"是否能被法律接受？
17. AI 是否会加剧社会不平等？
18. AI 大模型的训练数据是否应被公开？
19. AI 监管是否应该全球统一？

#### 类别 E：本地模型场景（5 题）

20. 7B 本地模型能完成怎样的推理？
21. 中小模型在垂直领域是否优于大模型？
22. 模型量化对推理质量的影响？
23. 本地推理的隐私优势是否值得性能损失？
24. CPU 推理是否仍是可行的方案？

### 3.3 真实测试问题（含预期答案）

| 题号 | 问题 | 预期胜方 | 难度 | 来源 |
| --- | --- | --- | --- | --- |
| 1 | LLM 是否会取代人类大部分工作？ | 反方 | hard | OECD 2023 报告倾向反方 |
| 11 | 大模型是否真正理解语言？ | 平局/反方 | hard | Bender et al. 2021 倾向反方 |
| 20 | 7B 本地模型推理能力？ | 平局 | medium | 实证研究 |
| 22 | 4-bit 量化对质量影响？ | 平局 | medium | Dettmers 2023 |

---

## 四、评估指标

### 4.1 客观指标

| 指标 | 公式 | 目标 |
| --- | --- | --- |
| **JSON 解析成功率** | 成功解析次数 / 总调用次数 | > 95% |
| **平均响应时间** | Σ latency / N | < 30s（本地）/ < 10s（mock） |
| **证据引用率** | 含 [E-xxx] 的论点 / 总论点 | > 80% |
| **辩手发言长度** | 中位数字数 | 100-300 字 |
| **审理问题发现率** | 发现问题 / 预期问题 | > 70% |

### 4.2 主观指标（人工评分 1-5）

| 维度 | 评分标准 |
| --- | --- |
| 论证质量 | 论据充分、引用准确 |
| 逻辑严谨 | 因果链清晰、无谬误 |
| 立场鲜明 | 明确为正/反方辩护 |
| 反驳有效 | 直接回应对方论点 |
| 表达流畅 | 语言自然、无机器感 |

### 4.3 创新点验证指标

| 创新点 | 验证方式 | 目标改进 |
| --- | --- | --- |
| T1 AEBG | 对比有无 AEBG 的图指标 | 论证结构化评分 +15% |
| T2 DPP | 对比 DPP 启用前后论点多样性 | 重复率 -30% |
| T3 KS 早停 | 对比固定 3 轮 vs 自适应 | 平均轮数 -25%，质量持平 |
| T4 DS 融合 | 对比加权平均 vs DS 融合 | 法官一致性 +10% |

---

## 五、实验路线图

### 5.1 时间安排（5 天）

| Day | 实验 | 输出 |
| --- | --- | --- |
| D1 | LLM provider × 24 辩题 baseline | `results/baseline/` |
| D2 | 主持人参数调优 | `results/moderator_tune/` |
| D3 | T1-T4 创新点消融 | `results/ablation/` |
| D4 | 法官融合与早停 | `results/fusion/` |
| D5 | 真实 LLM 端到端 | `results/real_llm/` |

### 5.2 实验脚本

```bash
# 1. 准备实验目录
mkdir -p experiments/{baseline,moderator_tune,ablation,fusion,real_llm}

# 2. Mock baseline（全 24 题）
python scripts/run_batch.py \
    --config experiments/baseline/config.json \
    --output experiments/baseline/results.json

# 3. 主持人调优
python scripts/run_grid.py \
    --param moderator.duplicate_threshold \
    --values 0.70,0.80,0.85,0.90,0.95 \
    --questions 6 11 20 22 \
    --output experiments/moderator_tune/duplicate.json

# 4. T3 KS 早停消融
python scripts/run_ablation.py \
    --feature ks_early_stop \
    --questions 1 2 3 4 5 \
    --output experiments/ablation/ks.json
```

---

## 六、关键参数推荐（基于文献与初步实验）

| 场景 | 推荐配置 |
| --- | --- |
| **快速演示** | rounds=1, max_evidence=5, temperature=0.7 |
| **日常使用** | rounds=3, max_evidence=20, temperature=0.7, ks_alpha=0.1 |
| **学术研究** | rounds=5, max_evidence=30, temperature=0.5, ks_alpha=0.05, ds_fusion=true |
| **本地 7B 模型** | rounds=3, max_evidence=15, temperature=0.7, max_tokens=300（更短 prompt） |
| **中文辩题** | provider=ollama, model=qwen2.5:7b |
| **英文辩题** | provider=ollama, model=llama3.1:8b |

---

## 七、待确认的关键问题

1. **法官权重**：5 位法官权重是 uniform (1/5) 还是差异化（专家级 vs 通用级）？
2. **KS 检验的"分布"是什么**：评分分布、立场分布、还是论证覆盖度？
3. **DS 证据理论的辨识框架**：{pro胜, con胜, 平局} 还是 {质量, 相关性, 创新性}？
4. **AEBG 的边权重**：TF-IDF 余弦还是 sentence-bert 嵌入？
5. **DPP 的"多样性"定义**：基于内容嵌入还是基于证据 ID 集合？

这些问题需要在实验中确定，每个决策都需要 **3 个以上真实 LLM 调用** 作为佐证。
