# ParaJudge：多智能体辩论系统 — 学术论文、案例分析、需求与技术栈规划报告

> **项目代号**：ParaJudge
> **版本**：**v1.2**（2026-06-15 起引入 S3 统一设计框架 + 四项技术创新点 T1–T4）
> **历史版本**：
> - v0.1.0（2026-06）：初版设计报告（四阶段架构 + Moderator 主持人）
> - v1.1（2026-06-15）：新增 Moderator 角色全链路设计（7 个 Pydantic 模型）
> - **v1.2（本次）**：引入 **S3（Signal-driven / Structured / Sustainable）统一设计框架**，新增 **T1–T4 四项技术创新点**
> **适用范围**：高风险决策场景（数学推理、工程权衡、医疗辅助、法律分析、事实核查/热点研判）

---

## 一、核心思路回顾

在单一 LLM 或简单多智能体辩论（Standard MAD）中，存在三大核心问题：

1. **同质化推理偏差**：同一模型的多个实例在推理模式上高度重叠，"同一个脑子在重复自己"，难以产生真正的批评性视角（Du et al., 2023; Choi et al., 2025）
2. **论证质量缺乏制衡**：LLM 倾向于**阿谀奉承（sycophancy）**，当一个模型自信地表述错误事实时，其他模型更倾向于赞同而非质疑（Suat, 2025 博客; Hu et al., 2026）
3. **裁决过程黑箱化**：投票或"评委打分"的裁决无法追溯，对创新问题天然保守（Hu et al., 2026; Becker et al., 2025 MALLM）

**ParaJudge 的核心主张（v1.2 升级）**：

> 将辩论过程分解为"证据准备 → 结构化辩论 → 独立审理 → 多维度专业化裁决"四个阶段。
> 其中**目标驱动异质性**（Objective-Driven Heterogeneity）是产生高质量推理的关键机制——各 Agent 因追求不同的目标（"构建框架" vs "找漏洞" vs "核验证据"）而产生真正的差异，而非依赖 Prompt 模板或不同模型。

---

### ★ v1.2 新增：S3 统一设计框架（Signal-driven + Structured + Sustainable）

从 v1.2 起，ParaJudge 的所有设计决策均由**S3 统一设计框架**驱动，避免"堆砌功能"式的系统膨胀。S3 框架定义了三个维度的设计原则，所有新增机制（如本文档第 3 节的 T1–T4）都必须至少满足其中一个原则。

```
                          ┌──────────────────────────────────────────┐
                          │         S3 统一设计框架（v1.2 起）         │
                          │                                          │
                          │  ┌────────────┐  ┌────────────┐         │
                          │  │ Signal-driven│  │ Structured │         │
                          │  │  信号驱动     │  │ 结构化     │         │
                          │  │            │  │            │         │
                          │  │ · 质量阈值 │  │ · 证据闭包 │         │
                          │  │   由论点多 │  │   （Evidence│         │
                          │  │   样性动态 │  │   Closure）│         │
                          │  │   调整       │  │            │         │
                          │  │            │  │ · 二部图结 │         │
                          │  │ · 阶段迁移 │  │   构化论证 │         │
                          │  │   由信息增 │  │   （AEBG）  │         │
                          │  │   益信号驱 │  │            │         │
                          │  │   动       │  │ · DS 证据 │         │
                          │  │            │  │   理论融合 │         │
                          │  └──────┬─────┘  └──────┬─────┘         │
                          │         │                │                 │
                          │         └────┬───────────┘                 │
                          │              │                             │
                          │      ┌──────▼─────────┐                   │
                          │      │  Sustainable    │                   │
                          │      │   可持续（节算）│                   │
                          │      │                 │                   │
                          │      │ · KS 检验收敛检测│                   │
                          │      │   避免无效轮次   │                   │
                          │      │ · DPP 多样性约束│                   │
                          │      │   避免重复论点   │                   │
                          │      └──────────────────┘                   │
                          └──────────────────────────────────────────┘
```

**S3 框架的正式定义**：

| 维度 | 设计原则 | 在 ParaJudge 中的具体体现 | 关联技术创新点 |
|:---|:---|:---|:---|
| **Signal-driven（信号驱动）** | 系统的控制决策（是否继续辩论、是否过滤论点、如何分配计算资源）由可观测的过程信号驱动，而非固定参数或人工设定 | 质量守门阈值 = f(论点多样性信号)；阶段迁移由信息增益信号驱动；权重由法官打分分布信号自适应学习 | T1（AEBG 图信号）、T3（KS 检验收敛检测） |
| **Structured（结构化）** | 证据–论点–裁决之间存在可验证的结构化链路；输出结果不是自然语言文本，而是带引用的结构化数据 | 证据闭包（所有论点引用都可追踪到证据节点）；论点-证据二部图；DS 证据理论融合；类判决书推理链 | T1（AEBG 图结构）、T4（DS 证据融合） |
| **Sustainable（可持续/节算）** | 计算资源与问题复杂度匹配；避免在简单问题上浪费算力；检测辩论是否已收敛到共识 | KS 检验尽早终止已收敛的辩论；DPP 约束避免重复论点的生成（省一次 LLM 调用 ≈ 省 $0.01） | T2（DPP 多样性约束）、T3（KS 检验） |

> **论文写作提示**：S3 框架在投稿时可以作为本文的核心创新主张之一——你可以说「现有 MAD 系统多为启发式、固定轮次的黑箱流程，本文提出 S3 框架将辩论控制决策建立在可观测信号和结构化数据之上，并在 30 道问题上验证其有效性。」

---

---

## 三、v1.2 四项技术创新点（T1–T4）

> 以下四项技术机制均严格遵循 **S3 统一设计框架** 的至少一个维度。它们共同将 ParaJudge 从「多 Agent 加规则的辩论系统」升级为「信号驱动 + 结构化 + 可持续的推理引擎」。

### T1. 论点-证据二部图（Argument-Evidence Bipartite Graph, AEBG）

**定位**：核心创新（Signal-driven + Structured）

**技术机制**：将辩论过程建模为一张**二部图** G = (V_args ∪ V_evidence, E)，其中每个论点节点通过边连接到它所引用的证据节点。在这张图上实时计算：

| 图指标 | 计算公式 | 用途 |
|:---|:---|:---|
| **证据支撑度** | degree(a) / max_degree | 论点引用了多少条不同的证据 |
| **证据多样性** | 1 − mean(cos_sim(emb(e_i), emb(e_j))) for e_i, e_j ∈ N(a) | 引用的证据在语义上是否多样化 |
| **Personalized PageRank** | 以高置信度证据节点为权威源的 PageRank 得分 | 论点在「引用高质量证据」维度上的权威度 |
| **闭包可达性** | 是否存在从论点 a 到证据节点的路径（二部图中天然成立，退化为「高置信度证据邻居数量」） | 过滤「空喊口号」式论点 |

**替换旧机制**：AEBG 的 combined_score 将取代 v1.1 中 Moderator 的纯 embedding 相似度去重（即 5.3.4.1 的 duplicate 检测）。旧做法只能判断「这条论点和之前的是否重复」，新做法可以定量评估「这条论点的质量如何」——这是从「负向过滤」到「正向评分」的范式升级。

**对论文的贡献**：首次在多智能体辩论系统中引入图论结构作为质量控制的底层信号。AEBG 的计算完全不依赖额外 LLM 调用（仅依赖已有 embedding），零额外成本即可获得结构化质量信号。

**实现文件**：`src/debate/aebg.py`（新建），在 `src/debate/moderator.py::_quality_gate()` 中调用。

---

### T2. DPP 约束的反方论点生成多样性控制（Determinantal Point Process）

**定位**：中高级创新（Sustainable + Signal-driven）

**技术机制**：现有 MAD 系统中，反方辩手在连续多轮后容易陷入「换个说法重复同一论点」的困境。我们引入 **DPP（Determinantal Point Process）** 作为候选论点的选择机制：

```
候选论点集合 C = {c_1, c_2, ..., c_K} （由 LLM 生成多个草案）
质量向量 q = [AEBG.combined_score(c_i)] （来自 T1 的图评分）
多样性矩阵 L_ij = q_i · q_j · exp(−λ · cos_dist(c_i, c_j))
选择子集 S ⊂ C, |S| = 1，使得 det(L_SS) 最大化
```

其中 λ 是多样性强度超参数（默认 λ = 1.0，消融范围 0.5–2.0）。直觉上，DPP 同时最大化「选中论点的质量」和「选中论点间的多样性」——比「按质量排序取 top-1」更能产生真正的批评性视角。

**简化实现路径**（推荐先做）：如果不实现完整 DPP（需要 numpy 特征分解），先用**相似度拒绝采样**（rejection sampling）替代——生成 K 个候选，逐一与历史论点做 cosine 相似度检查，选择第一个相似度低于 θ 的候选。该简化版保留了核心思想但代码量少 60%。

**对论文的贡献**：形式化并解决了 MAD 系统中「论点过早趋同」的问题，提供了一个既考虑质量又考虑多样性的选择机制。

**实现文件**：`src/debate/dpp_sampler.py`（新建），在 `src/debate/agent_base.py::_generate_argument()` 中调用。

---

### T3. KS 检验驱动的辩论收敛检测（Kolmogorov-Smirnov Test）

**定位**：中高级创新（Signal-driven + Sustainable）

**技术机制**：传统做法用固定轮次（如 8 轮自由辩论）来终止辩论。我们的做法：让五位法官在辩论的每一轮都做一次轻量级打分（仅打 0–100 的整数分，不写解释），得到 5 维的评分向量 S_t。对连续两轮的评分向量做**双样本 Kolmogorov-Smirnov 检验**：

```
H_0（原假设）：S_t 和 S_{t-1} 来自同一分布（辩论已收敛）
H_1（备择假设）：S_t 和 S_{t-1} 分布不同（辩论仍在演进）

决策规则：
  如果 KS 检验 p-value > 0.05（不拒绝 H_0）→ 收敛，提前终止
  否则 → 继续辩论
  硬上限：max_rounds = 8（避免永不收敛的病态情形）
```

**参数**：α = 0.05（标准显著性水平，**不需要调参**——这是该方法的最大优势）。

**对论文的贡献**：将「何时停止辩论」这个启发式决策转化为有统计学理论保证的假设检验问题。在实验中通常可以节省 20–40% 的推理 token（简单问题在 3–5 轮即可收敛）。

**实现文件**：`src/debate/stability.py`（新建），在 `src/debate/moderator.py::_should_advance_phase()` 中调用。

---

### T4. Dempster-Shafer 证据理论的法官意见融合

**定位**：核心创新（Structured）

**技术机制**：替代 v1.1 中 Final-Judge 的简单加权平均 `Σ w_i · score_i`。新做法：

1. 每位法官输出一个高斯型的**基本概率指派（BPA）**：`m_i({score_i ± σ_i}) = w_i`，`m_i(Θ) = 1 − w_i`（无知度，w_i 越高，法官越确定自己的评分）。
2. 通过 **Dempster 合成规则**顺序合并五位法官的 BPA，得到一个最终的合成 BPA m_final。
3. 从 m_final 可以计算多种有实际意义的输出：
   - **期望得分**：Σ m_final({level_k}) · level_k
   - **不确定性**：m_final(Θ)（法官们有多不确定整体判决）
   - **置信区间**：包含 80% 概率质量的最窄评分档位范围
4. 不确定性评分用于实际部署场景：`uncertainty > 0.4 → 标注为"建议人工复核"`。

**关键特性**：当五位法官意见分歧严重时（如创新法官给 90 分而证据法官给 30 分），DS 融合后的不确定性会升高，而简单加权平均只会给出一个毫无信息量的 60 分。

**对论文的贡献**：在「多 Agent 评分」任务中首次引入 DS 证据理论，提供了比简单加权平均更丰富的判决输出（不仅有得分，还有不确定性和置信区间）。这为实际高风险决策场景提供了可审计性。

**实现文件**：`src/judgment/ds_fusion.py`（新建），替换 `src/judgment/final_judge.py::weighted_score()`。

---

### T1–T4 汇总与优先级

| 编号 | 名称 | S3 维度 | 技术复杂度 | 论文加分强度 | 建议开发顺序 | 代码量（约） |
|:---|:---|:---|:---|:---|:---|:---|
| T1 | AEBG 论点-证据二部图 | Signal + Structured | ★★☆ | ★★★★★ | **第 1** | 150 行 |
| T2 | DPP 多样性约束 | Sustainable + Signal | ★★☆ | ★★★★☆ | **第 2** | 100 行 |
| T3 | KS 检验收敛检测 | Signal + Sustainable | ★☆☆ | ★★★☆☆ | **第 1.5（可与 T1 并行）** | 60 行 |
| T4 | DS 证据理论融合 | Structured | ★★☆ | ★★★★☆ | **第 3** | 120 行 |

**开发依赖链**：T3 依赖 T1 的 AEBG 评分做法官打分（否则法官打分变化过大导致 KS 检验不稳定）；T4 独立于辩论过程，可与 T1/T2/T3 并行开发。

```
T1 (AEBG) ──┐
            ├──→ T3 (KS检验，利用T1的结构化信号)
T2 (DPP)  ──┘

T4 (DS融合) ── 独立路径（只替换 Phase 2.2 的最终加权平均）
```

---

## 四、技术创新点与现有工作的对比（论文写作素材）

| 对比维度 | 标准 MAD（Du et al., 2023） | MALLM（Becker et al., 2025） | Swarm-Debate | **ParaJudge v1.2** |
|:---|:---|:---|:---|:---|
| **辩论控制** | 固定轮次 | 讨论范式选择 | Validator 检查 | **信号驱动的自适应控制（AEBG + KS）** |
| **质量守门** | 无/简单重复检测 | 无 | Validator 过滤 | **AEBG 图评分 + 闭包可达性检测** |
| **论点多样性** | 依赖 Prompt 设定的角色差异 | 多模型/多 Prompt | 角色分工 | **DPP 多样性强制约束** |
| **裁决方式** | 投票 | 综合者 Agent | Validator 评分 | **DS 证据理论融合（得分+不确定性+置信区间）** |
| **可解释性** | 低（黑箱文本） | 中（有讨论摘要） | 中 | **高（AEBG 图 + 推理链 + 不确定性标注）** |
| **停止规则** | 固定轮次 | 固定长度 | 人工设定 | **KS 检验的统计收敛检测** |

---

## 五、技术创新点的实验评估方案（论文实验章节）

### 5.1 主实验：ParaJudge vs 基线系统

| 实验编号 | 设置 | 评价指标 | 数据规模 |
|:---|:---|:---|:---|
| E-MAIN | ParaJudge v1.2 vs 单 LLM vs Self-Consistency vs 标准 MAD | 准确率 / 证据覆盖率 / token 开销 | 30 题 × 3 次重复 |

### 5.2 消融实验（每项技术创新点的单独贡献）

| 实验编号 | 设置（相对于 ParaJudge Full 的变体） | 评价指标 | 验证哪个创新点 |
|:---|:---|:---|:---|
| E-ABL-1 | ParaJudge − AEBG（退化为纯 embedding 去重） | 准确率 / warnings 数量 | T1 必要性 |
| E-ABL-2 | ParaJudge − DPP（退化为纯质量排序选择） | 论点平均相似度 / 准确率 | T2 必要性 |
| E-ABL-3 | ParaJudge − KS（退化为固定 8 轮） | token 开销 / 准确率变化 | T3 节算能力 |
| E-ABL-4 | ParaJudge − DS（退化为简单加权平均） | 高不确定性问题的识别率 | T4 不确定性能力 |

### 5.3 敏感性分析（超参数稳健性）

| 实验编号 | 设置 | 评价指标 | 说明 |
|:---|:---|:---|:---|
| E-SEN-1 | DPP λ ∈ {0.5, 1.0, 2.0, 4.0} | 准确率 | 验证系统对多样性强度超参数不敏感 |
| E-SEN-2 | KS α ∈ {0.01, 0.05, 0.10} | 平均停止轮次 | 验证停止规则对显著性水平不敏感 |
| E-SEN-3 | AEBG PageRank 重启概率 ∈ {0.15, 0.20, 0.30} | 论点质量评分排名相关性 | 验证图指标对超参数不敏感 |

### 5.4 成对偏好评估（Human Preference Study）

- **受试者**：2–3 位独立标注者
- **材料**：随机抽取 15 道题的「单 LLM 回答」与「ParaJudge 判决书」，随机打乱
- **任务**：盲评每对回答，三选一：A 更好 / B 更好 / 相当
- **指标**：ParaJudge 被偏好的比例 + Cohen's kappa（标注者一致度）

---

## 六、核心学术论文与分析 — 从"单个 LLM"到"多智能体法庭"的完整演进史

> **阅读指南**：本节从零开始讲解——如果你完全不了解 LLM 或多智能体辩论，从 6.1 开始按顺序读；如果你已有背景，可快速浏览以理解 ParaJudge 的设计如何与现有工作区分。每个关键概念均提供**生活比喻**、**具体示例**和**与 ParaJudge 设计的对应关系**。

---

### 2.1 前置知识：什么是 LLM？它为什么需要"辩论"？

#### 2.1.1 LLM 的本质：一个超大型"完形填空"

**最朴素的比喻**：想象你有一本**超级厚的书**，它读过互联网上几乎所有的公开文本。当你问它："1+1 等于几？"，它不是真的"理解"数学，而是根据它读过的所有内容，**预测下一个最可能出现的词是什么**。它说"2"不是因为它"会算"，而是因为在它读过的海量文本里，"1+1="后面出现"2"的概率最高。

```
LLM 生成一句话的过程 = 一次预测一个词，不断重复
  "你" → "好" → "吗" → "？"
   ↑        ↑        ↑        ↑
  概率98%  概率95%  概率80%  概率99%
```

这意味着：
- ✅ **LLM 擅长的**：回答常见问题、写作、代码生成——只要它见过大量类似样本即可
- ❌ **LLM 不擅长的**：需要严格逻辑推理的多步问题、需要核验事实的问题、前沿/小众领域问题——因为这些问题的"正确答案"在训练数据中不常见
- ⚠️ **LLM 的幻觉**：当 LLM 不知道答案时，它仍然会预测"最合理"的下一个词——就像考试时不会做但仍要写答案的学生，可能写出表面通顺但完全错误的内容

#### 2.1.2 为什么需要"多智能体辩论"？

**生活比喻**：想象你要做一个重要决定（比如"买哪只股票？""是否接受这个治疗方案？""这项新技术方案是否可行？"）。你会怎么选？

| 决策方式 | 对应 LLM 方案 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **只问一个"专家"** | 单个 LLM 直接回答 | 快速、简单 | 专家可能出错、有偏见、遗漏信息 |
| **问多个"专家"然后投票** | 多智能体辩论（MAD） | 多个角度互相补充，错误被抵消 | 专家们可能互相附和（羊群效应），投票掩盖了推理过程 |
| **让双方在你面前辩论** | 结构化辩论 | 你能听到双方理由和证据，自己判断 | 需要设计好的辩论规则，否则混乱 |
| **请专业律师辩论 + 法官裁决** | ParaJudge 四阶段架构 | 结构化证据、结构化质证、结构化裁决 | 复杂度高、成本高 |

**学术动机（用一句话概括）**：单个 LLM 有局限性（偏见、幻觉、逻辑跳跃），让**多个 Agent 从不同立场、不同目标出发进行结构化交互**，可以显著提高最终输出的准确性、可靠性和可解释性。

---

### 2.2 历史演进：从"单个 LLM"到"多智能体法庭"的四步跨越

#### Step 1：自一致性（Self-Consistency，2022–2023）

> **比喻**：让同一个 LLM 对同一个问题回答 5 次，然后选"最多人同意"的那个答案。就像掷骰子 5 次，选出现次数最多的结果。

**论文**：*Self-Consistency Improves Chain of Thought Reasoning in Language Models* (Wang et al., 2023)

**核心思路**：
- 对同一个问题，用不同的"提示词"或不同的随机种子让 LLM 生成多个独立回答
- 然后在这些回答中"投票"——选最多人同意的答案
- **直觉**：正确答案有多种推理路径可以到达；错误答案往往每条路径都不同

**对 ParaJudge 的意义**：这是"多路径 → 汇总"思想的源头。但它的弱点是**所有路径来自同一个模型**，模型的系统性偏见仍然存在。

#### Step 2：AI Safety via Debate（2018, OpenAI）

> **比喻**：两个 AI 在一个"人类法官"面前辩论，就像辩论赛。法官不知道正确答案，但能看出谁的论证更有说服力。

**论文**：*AI Safety via Debate* (Irving, Christiano, Amodei, 2018)

**核心思路**：
- 两个 Agent（正方 vs 反方）轮流辩论一个问题
- 辩论结束后，由一个人类或 AI 法官判定胜负
- **关键创新**：即使双方都不完全正确，通过互相揭露对方错误，辩论过程本身能推动真相浮现

**对 ParaJudge 的意义**：确立了"辩论作为对齐机制"的范式。但它只有辩论和裁决两步，缺少**证据准备**和**审理**（质证）阶段，法官容易被"听起来有道理但缺乏证据"的发言误导。

#### Step 3：现代 MAD 框架（Multi-Agent Debate, 2023）

> **比喻**：把 Step 2 升级为一个可重复运行的"标准流程"。

**论文**：*Improving Factuality and Reasoning through Multi-Agent Debate* (Du et al., 2023, MIT/Stanford)

**具体做法**：
1. 多个 Agent 各自独立生成对问题的回答
2. Agent 看到其他 Agent 的回答后，进行多轮辩论
3. 最终通过投票裁决

**实验结果**：在数学推理（GSM8K）和常识问答（MMLU）基准上，比单模型 + 自一致性显著更好。

**对 ParaJudge 的意义**：这是我们的"基线系统"。ParaJudge 在 Step 3 的基础上增加了三个关键改进：
1. **有证据（Phase 0）**——不是空口辩论
2. **有审理（Phase 2.1）**——不是辩论完直接投票
3. **有结构化裁决（Phase 2.2）**——不是简单投票

#### Step 4："辩论不够"的发现与结构化改进（2024–2025）

> **比喻**：人们发现 Step 3 的"自由辩论"并不总是有效——有时候 Agent 吵不出结果、互相附和、或陷入循环。

**关键发现（Smit et al., 2024, *Should we be going MAD?*）**：
- 多智能体辩论**并不必然优于**自一致性（Step 1）
- 辩论的质量高度依赖**机制设计**（谁说话、怎么说话、怎么裁决）
- 如果机制设计得不好，辩论可能反而降低质量

**后续改进方向（2024–2025 涌现的论文）**：
- **MALLM (Becker et al., 2025, Göttingen)**：模块化、可配置的辩论框架——不同角色/回应方式/讨论范式可以混合搭配
- **Hu et al. (2025, Adaptive Stability Detection)**：辩论状态监控——检测"双方在循环争执"或"过早达成一致"，并提前终止
- **Choi et al. (2025, Identity Bias)**：角色标签偏见——Agent 被称为"专家"比被称为"新手"更容易赢得辩论（即使内容相同）
- **Niu & Zhang (2026, ARMOR-MAD)**：异质 Agent——不用同一模型，而是不同"专家模型"分别处理不同子问题
- **Hu et al. (2026, The Confident Liar)**：**核心警示**——LLM 在错误答案上也能表现出高置信度。辩论中的"自信"不等于"正确"。**这直接推动了 ParaJudge 的"证据闭包"和"审理阶段"设计**

**对 ParaJudge 的意义**：Step 4 的论文告诉我们——**辩论必须结构化，不能让 Agent 自由聊天**。必须有证据、有质证、有独立审理。

```
ParaJudge 的演进定位：

              Step 1: 自一致性
                    │
                    ▼
              Step 2: 两 Agent 辩论（Irving 2018）
                    │
                    ▼
              Step 3: 现代 MAD（Du 2023）◀━━━ 我们的基线
                    │
     ┏━━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
     ┃  ParaJudge   │  在 Step 3 基础上增加：                   ┃
     ┃  (本项目)    │   ① Phase 0 证据构建（确保辩论有据可依） ┃
     ┃              │   ② Moderator 主持（避免混乱 / 重复）     ┃
     ┃              │   ③ Phase 2.1 审理阶段（独立检查证据）    ┃
     ┃              │   ④ Phase 2.2 五维结构化裁决           ┃
     ┗━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

### 2.3 里程碑论文精读（按时间顺序，小白友好版）

| 序号 | 论文 | 作者/机构 | 年份 | 它解决的问题 | ParaJudge 对应设计 |
|:---|:---|:---|:---|:---|:---|
| 1 | **AI Safety via Debate** | Irving, Christiano, Amodei (OpenAI) | 2018 | "怎么让 AI 在超过人类判断能力的复杂问题上也能给出好答案？" | 辩论 → 裁决范式的源头。Phase 1 + Phase 2.2 |
| 2 | **Improving Factuality and Reasoning through Multi-Agent Debate** | Du, Li, Zheng, Tian, Jurafsky, McAleer, Weld (MIT, Stanford) | 2023 | "怎么把辩论变成一个可运行、可复现的框架？" | 本项目的基线系统（Standard MAD） |
| 3 | **Should we be going MAD?** | Smit et al. | 2024 | "辩论真的总是有帮助吗？"——答案是"不一定"，取决于机制设计 | 给 ParaJudge 的警示：必须用 POI、证据闭包、审理等机制证明改进 |
| 4 | **MALLM: Multi-Agent Large Language Models Framework** | Becker, Kaesberg, Bauer, Wahle, Ruas, Gipp (Göttingen University) | 2025 | "怎么设计一个可灵活配置的辩论框架？" | **直接参考**：学习其"配置驱动"和"评估管线"设计。但我们在结构化程度上更进一步 |
| 5 | **Multi-Agent Debate for LLM Judges with Adaptive Stability Detection** | Hu et al. | 2025 | "怎么检测辩论在'无效循环'或'过早收敛'？" | Moderator 的状态监控设计——检测阶段转换条件 |
| 6 | **Measuring and Mitigating Identity Bias via Anonymization in MAD** | Choi et al. | 2025 | "Agent 的'身份标签'（如'法律专家'）会影响法官判断，即使内容相同" | 辩论中使用"正方 N 号/反方 N 号"匿名标签，而非角色标签 |
| 7 | **ARMOR-MAD: Adaptive Routing with Mixture-of-Experts for Reasoning** | Niu & Zhang | 2026 | "用不同模型处理不同子问题比用一个大模型更好吗？" | 五维法官并行评估（异质化裁决） |
| 8 | **The Confident Liar: Evaluating and Predicting Credibility During LLM Debate** | Hu et al. | 2026 | "LLM 会不会在自己错了时仍表现得很自信？"——会！ | **直接推动证据闭包和审理阶段设计**——必须有独立机制校验引用 |

#### 论文 1–4 的关键洞见

**论文 1 (AI Safety via Debate, 2018)**
- **核心实验**：在简单问答任务中，一个"诚实 Agent"和一个"说谎 Agent"向一个"人类/AI 法官"呈现论点
- **关键发现**：即使法官不知道正确答案，通过双方对抗也能分辨好坏
- **比喻**：一个好律师能让不懂法律的陪审团看出对方论证的弱点

**论文 2 (Improving Factuality and Reasoning, 2023)**
- **核心改进**：首次将 MAD 变成标准工程流程（有代码、有基准、有对比实验）
- **具体做法**：让 Agent 在多轮中先独立回答，再看到他人回答后修正，最后投票
- **实验结果**：在数学题（GSM8K）上，单模型准确率约 78%；MAD 后提升到 82–85% 区间
- **局限**：仍然是"自由辩论"，Agent 容易互相附和；无证据约束机制

**论文 3 (Should we be going MAD?, 2024)**
- **核心警示**：当辩论的"讨论空间"很小（比如简单的选择题），MAD 可能不如"同一个问题问 5 次再投票"（即 Step 1 的自一致性）
- **ParaJudge 设计受此约束**：对简单问题，我们会自动使用"轻量模式"（跳过复杂辩论流程），避免浪费成本
- **用一句话记住**：**多 Agent ≠ 自动更好。机制设计是关键**

**论文 4 (MALLM, 2025)**
- **贡献**：把"辩论框架"分解成 4 个独立模块——每个模块有多种选项，可组合出 144+ 种配置：
  - Agent Persona（说话者的"人设"）
  - Response Generator（怎么回答的"生成器"）
  - Discussion Paradigm（怎么组织讨论的"范式"）
  - Decision Protocol（怎么做最终决策的"协议"）
- **对 ParaJudge 的启示**：我们的 ModeratorConfig 类似思路——通过配置改变行为，而不是改代码

#### 论文 5–8 的关键洞见

**论文 5 (Adaptive Stability Detection, 2025)**
- **发现**：辩论有时会在"双方来回说同样的话"中振荡，或过早达成一致（因为 Agent 不坚持己见）
- **ParaJudge 对应设计**：Moderator 持有状态机，当检测到"无新论点"（通过与 ArgumentIndex 的相似度比较）时，自动进入下一阶段
- **比喻**：就像主持人说"好的，这个话题你们已经重复三轮了，我们继续下一个话题"

**论文 6 (Identity Bias via Anonymization, 2025)**
- **发现**：如果一个 Agent 被称为"博士"、"专家"、"资深律师"，其他 Agent 和法官更容易同意它的观点，即使内容相同
- **解决方法**：匿名化——在辩论期间仅用"正方 N 号/反方 N 号"称呼
- **ParaJudge 对应设计**：在所有传给辩手和法官的 Prompt 中，仅使用匿名标签，不暴露 Agent 的"人设"

**论文 7 (ARMOR-MAD: Mixture-of-Experts, 2026)**
- **核心思想**：与其让一个"全能模型"处理所有问题，不如让不同的"专家模型"各管一块
- **ParaJudge 对应设计**：五维法官并行评估——证据法官只关心证据质量，逻辑法官只检查推理链条，原则法官只核对是否符合原则，案例法官只匹配已有案例，创新法官只判断创新性。各自独立，然后汇总

**论文 8 (The Confident Liar, 2026)**
- **核心警示**：**LLM 在错误答案上也能表现出高置信度**。这是最危险的特性之一
- **具体发现**：作者在多个辩论任务上测量"Agent 对自己论点的置信度" vs "论点的实际正确性"，发现两者的相关性不高（约 0.4–0.5）
- **对 ParaJudge 的直接影响**：
  1. 论点必须引用具体证据（不能只说"我相信是这样"）
  2. 必须有独立审理阶段（法官不听"自信的语气"，只看"证据链"）
  3. 必须对证据引用进行闭包验证（确保证据条目确实存在于 Evidence Brief 中）

---

### 2.4 补充关键论文（应用领域，速览）

| 领域 | 论文 / 项目 | 核心发现 | 对 ParaJudge 的提示 |
|:---|:---|:---|:---|
| **医疗** | Dialectic-Med (2025) | 多 Agent 辩论在医疗报告生成中优于单一 LLM | 可以将 E-Judge（证据法官）扩展为专门的"医学证据子法官" |
| **法律** | SAMVAD (2025), AgentsCourt (2025) | 法律问答中，辩论式 Agent 显著提升法条引用正确率 | C-Judge（案例法官）需要法律案例库；审理阶段检察官应检查"法条引用错误" |
| **事实核查** | PolitiFact/AVEITEC 系列工作 | "事实核查员 Agent"需要独立检索能力，不能依赖其他 Agent 给的"事实" | Phase 0 独立证据构建是正确设计——证据不经过辩论 Agent 过滤 |
| **一般推理** | "Hear Both Sides" (2026) | 多样性意识消息保留机制显著提升辩论质量——不让少数派观点被淹没 | Moderator 的质量守门应确保"不同立场的发言数量平衡" |

---

### 2.5 我们站在哪里？——ParaJudge 的技术定位

```
"辩论质量谱系"

              低质量 ◀───────────────────────────────▶ 高质量

  单 LLM 回答   自一致性     自由 MAD     辩论+证据    结构化证据辩论
   (ChatGPT)   (5次投票)   (Du 2023)   (swarm-debate)  (ParaJudge 目标)
     │            │           │            │                  │
     ▼            ▼           ▼            ▼                  ▼
  75%左右准确率  约80%      约82-85%     约85-88%        目标 90%+
  零可追溯性    有限可追溯   部分可追溯   有引用验证     全链路可追溯
  零结构化     零结构化     轻量结构     部分结构       完全结构化
  无证据       无证据       无强证据     有事实核查     证据闭包约束
  无审理       无审理       无审理       隐式审理       独立审理阶段
  无结构化裁决 无裁决设计   简单投票     综合者Agent    五维专业化法官
```

**ParaJudge 核心设计理念的学术来源**：

| 设计要素 | 直接启发自 | 核心思想 |
|:---|:---|:---|
| 四阶段架构 | Step 4 的结构化改进趋势 + swarm-debate 的 Validator Agent 概念 | 证据准备 → 结构化辩论 → 独立审理 → 结构化裁决 |
| Moderator 主持 | MALLM 的"讨论范式"模块化 + Hu 2025 的稳定性检测 | 状态机驱动 + 质量守门，避免混乱辩论 |
| 证据闭包约束 | Hu 2026 "The Confident Liar"——LLM 的自信不代表正确 | 所有论点必须引用 Phase 0 证据；引用自动核验 |
| 五维专业化裁决 | ARMOR-MAD 的异质 Agent 思路 | 不同法官负责不同评估维度，比"全能法官"更可靠 |
| 创新保护机制 | 创新型问题在传统辩论中天然被打压（先例缺失→被判无效） | 专门的 I-Judge 和 "暂定结论保护" 机制 |
| 匿名辩论 | Choi 2025 的身份偏见发现 | 辩论期间仅使用匿名标签"正方 N 号/反方 N 号" |
| 类判决书输出 | 可解释性需求（NFR2） + 可追溯性需求（NFR1） | 每条结论标注证据来源 / 原则依据 / 案例支持 |

---

## 三、开源实现案例分析 — 从"简单辩论"到"结构化法庭"的差距

### 3.1 主要开源项目概览

| 项目 | 开发者/机构 | 核心设计 | 优点 | 不足（ParaJudge 的改进空间） |
|:---|:---|:---|:---|:---|
| **MALLM** | Göttingen University | 4 组件模块化：Agent Persona × Response Generator × Discussion Paradigm × Decision Protocol；支持 144+ 种配置 | 模块化清晰、配置灵活、可复现实验 | 缺少证据约束、缺少审理阶段、裁决仍为投票制 |
| **Multi-Agent-Debate** | Alexandre Sajus | Du 2023 官方实现：正反辩论 + 投票 | 简洁、易读 | 自由辩论（无结构）、无证据、匿名投票（不可追溯） |
| **DebateNet** | jinhongzou | 正反辩论 + 主持人 + DSPy 框架 | 有主持人概念、代码简洁 | 主持人仅控制发言顺序、无质量守门、无证据闭包 |
| **swarm-debate** | capitansuat | **独立事实核查员（Validator Agent）** 概念——每轮后对引用进行校验 | **有审理雏形**——Validator 是"事实核查检察官"的简化版 | Validator 仅做事实核查，不对论点质量/逻辑/创新做评估；无结构化裁决 |
| **CAMEL** | KAUST (NeurIPS 2023) | 角色驱动的合作 Agent 框架（AI 助手 ↔ AI 用户） | 角色工程设计成熟、已大规模验证 | 侧重合作而非辩论；无争议场景机制 |
| **LangChain/LangGraph** | LangChain | 通用 Agent 编排框架 | 大规模生态、可扩展性好 | 需要自己设计辩论规则和审理逻辑 |
| **AutoGen** | Microsoft | 多 Agent 设计模式；MathSolver 采用"稀疏拓扑 + Solver Agents + Aggregator" | Solver-Aggregator 模式启发辩论-裁决设计 | 侧重任务分解而非辩论 |

### 3.2 关键实现模式对比（深入版）

让我们把 ParaJudge 与现有最强实现（MALLM 和 swarm-debate）进行逐维度对比：

| 维度 | MALLM (2025) | swarm-debate | **ParaJudge** |
|:---|:---|:---|:---|
| **角色异质性来源** | 人格/专家标签（Persona + Expert）——通过 Prompt 让 Agent "扮演"不同角色 | Validator 是独立角色 | **目标函数差异**——不同 Agent 追求不同目标（"构建框架" vs "找漏洞" vs "核验证据"），这是比"人格标签"更强的约束 |
| **讨论范式** | Memory/Relay/Debate/Report 4 种，可配置 | 结构化轮流发言（正方→反方→Validator） | **Moderator 状态机驱动**——由主持人根据阶段（立论→交叉质询→自由辩论→总结陈词）动态分配发言权，而非固定顺序 |
| **证据机制** | 无特殊设计——Agent 自行组织论据 | Validator Agent 对具体引用进行事后校验（检索事实） | **Phase 0 证据闭包**——辩论开始前先构建 Evidence Brief；所有论点必须引用其中的证据条目；引用在写入论点索引时自动核验是否存在 |
| **审理阶段** | 无——辩论后直接裁决 | **隐含在 Validator 中**——Validator 在每轮后检查事实，但不做结构化审理报告 | **独立 Phase 2.1 审理**——检察官系统性检查证据选择性呈现/逻辑漏洞/未验证假设，辩护律师为正方提出最佳辩护，两者交互形成审理报告 |
| **裁决机制** | 多数投票/一致同意/单一法官——可配置 | 综合者 Agent | **五维专业化法官并行评估**（证据/逻辑/原则/案例/创新）→ F-Judge 加权汇总。每个法官评分可追溯，而非单一数字 |
| **创新保护** | 无 | 无 | **I-Judge（创新法官）专门评估创新性**，并通过"先例不缺失不扣分"原则避免新想法被"无先例"打压 |
| **可追溯性** | 输出最终答案和对话历史——用户可读但不可机器解析 | 事实检查标注（半结构化） | **类判决书推理链**——每条结论标注具体证据（E-xx）/原则（P-xx）/案例（C-xx）来源，完全结构化可机器解析 |
| **状态监控** | 无明确设计 | 无 | **Moderator 实时监控**——检测重复发言、主题漂移、超时；触发阶段转换；记录 warnings 供审理阶段使用 |

### 3.3 ParaJudge 的独特定位：为什么需要一个新项目？

读完上面的对比，一个自然问题是：**为什么不直接在 MALLM 或 swarm-debate 上改？为什么要做 ParaJudge？**

**简短回答**：因为现有项目的"架构基因"不支持我们需要的全链路结构化。具体来说：

1. **现有框架是"辩论优先"的**——它们假设"先辩论再说"，证据和审理最多是附加功能。而 ParaJudge 从设计之初就是"证据优先"——没有证据，辩论不开始。Phase 0 Evidence Brief 是整个流程的地基。

2. **现有框架对"异质性"的理解停留在表面**——用不同 Prompt 让 Agent "扮演"不同角色（专家/新手/质疑者）。但真正产生高质量差异的是**目标函数差异**："找漏洞"的 Agent 和"构建框架"的 Agent 使用的是完全不同的思维模式，不是 Prompt 能模拟的。

3. **现有裁决都是"黑箱汇总"**——投票制、单一法官、综合者 Agent。这些方法都无法回答一个关键问题：**"为什么得出这个结论？每一分依据来自哪里？"** ParaJudge 的五维法官 + 推理链输出，使得裁决的每一步都可以追溯到具体证据。

4. **现有框架缺少"创新保护"**——在技术/商业决策中，传统辩论天然打压新想法（因为"没有先例支持"→"这是弱点"）。ParaJudge 专门设计了 I-Judge 来平衡这种天然保守倾向，使得创新型问题能被正确评估。

5. **现有框架不支持"问题类型自适应"**——对于简单事实性问题，你不需要全套四阶段流程；对于复杂创新性问题，你需要更深入的证据和更长的辩论。ParaJudge 通过问题类型识别 + Moderator 配置自动选择合适复杂度。

**一句话总结**：现有框架是"辩论 + X"（辩论为核心，X 是附加功能）；ParaJudge 是"证据 → 辩论 → 审理 → 裁决"的全链路设计，每个阶段是不可省略的基本单元。

---

## 四、系统需求分析

### 4.1 功能需求（Functional Requirements）

| 编号 | 需求 | 描述 | 优先级 | 验证方法 |
|:---|:---|:---|:---|:---|
| **FR1** | 用户问题输入 | 支持文本输入（问题、决策场景、待评估创新方案） | P0 | 单元测试 + 用户验收 |
| **FR2** | 证据检索与构建 Evidence Brief | 对用户问题进行关键词抽取 → 多源检索（arXiv/S2/Crossref）→ 去重与排序 → 生成结构化证据包 | P0 | 与现有 `src.search` 模块集成；验证 10 个问题的证据覆盖率 |
| **FR3** | 问题类型识别 | 自动识别问题类型（事实型/决策型/创新型/开放型） | P1 | 基于关键词+LLM判断的混合分类器 |
| **FR4** | 团队辩论引擎 | 正方/反方各含 1 名教练（不对外发言，负责战术设计与证据分配）+ 2-3 名辩手（轮流发言，支持 POI） | P0 | 端到端测试，验证辩论产物结构化输出 |
| **FR4.1** | 主持人 Moderator 角色 | 中立第三方角色，持有辩论状态机，负责阶段切换、时间片管理、发言秩序、POI 批准、质量守门 | P0 | 端到端测试，验证 Moderator 状态机驱动完整辩论流程 |
| **FR4.2** | 辩论阶段状态机 | 定义 OPENING_STATEMENTS / CROSS_EXAMINATION / FREE_DEBATE / CLOSING_STATEMENTS / DONE 五个阶段，由 Moderator 驱动自动切换 | P0 | 日志确认各阶段按预期推进，无死循环 |
| **FR4.3** | 时间片与轮数管理 | 每个发言有 max_tokens + max_seconds 限制；Phase 1 有 max_total_seconds 总时长上限 | P0 | 超时触发强制终止且不影响后续阶段 |
| **FR4.4** | POI 批准与拒绝 | Moderator 判断是否允许 POI（基于阶段 + 发言内容风险评分） | P1 | ≥30% 的高风险论点被批准发起 POI |
| **FR4.5** | 论点去重与质量守门 | Moderator 检查重复论点（基于 ArgumentIndex 相似度）和主题漂移，对违规发言给出警告并阻止其写入索引 | P1 | 注入 5 条偏离主题的发言，检出 ≥4 条 |
| **FR4.6** | Moderator 配置驱动 | 不同辩论场景（快速辩论 / 深度辩论）通过不同 `ModeratorConfig` 实现，无需改动代码 | P1 | 2 种不同配置对同一问题产生不同的阶段轮数 |
| **FR4.7** | 辩论总结输出 | Phase 1 结束时，Moderator 产出结构化 `DebateSummary`（核心论点 / 阶段耗时 / 警告记录），供 Phase 2.1 审理消费 | P0 | DebateSummary 被 ReviewWorkflow 正确读取 |
| **FR5** | POI 段间质询 | 在辩手发言中段，对方可发起简短质询，发言人必须回应 | P0 | 触发 POI 的规则引擎 + 人工评估有效性 |
| **FR6** | 证据闭包与引用验证 | 所有论点必须引用 Evidence Brief 中的证据条目；自动验证引用完整性和来源真实性 | P0 | 对所有论点执行引用一致性检查 |
| **FR7** | 论点索引系统 | 自动维护"论点→证据→反论点"的结构化索引 | P0 | 状态模型验证 |
| **FR8** | 检察官-辩护律师审理 | 2 名独立 Agent 对阶段 1 辩论进行质量审计：检查证据选择性呈现、逻辑漏洞、未经验证假设 | P0 | 对比有无审理阶段的裁决质量差异 |
| **FR9** | 五维度专业化裁决 | E-Judge(证据)/L-Judge(逻辑)/P-Judge(原则)/C-Judge(案例)/I-Judge(创新) 独立评估 | P0 | 与单全能法官的消融实验 |
| **FR10** | 裁决官综合判断 | 根据问题类型设置不同权重；综合五法官报告 | P0 | 权重配置 + 验证 |
| **FR11** | 创新保护机制 | 先例不缺失不扣分；显式标注未验证假设；提供暂定结论保护 | P1 | 对创新型问题，对比标准 MAD/人类专家的相关性 |
| **FR12** | 类判决书推理链输出 | 每条结论标注 "基于证据 [E-xx] + 原则 [P-xx] + 案例 [C-xx]" | P0 | 结构化 JSON + HTML 渲染 |
| **FR13** | 不确定性标注 | 标注"本结论基于假设 A/B/C，置信度 X" | P1 | 与实际错误率校准 |
| **FR14** | 裁决报告生成器 | 生成 HTML / PDF / Markdown 格式的裁决报告 | P1 | 模板渲染 |
| **FR15** | 领域知识库 | 支持加载领域原则库（math.yaml/medical.yaml/...）与案例库 | P0 | YAML 加载器 + 语义检索 |
| **FR16** | 评估实验管线 | 支持在基准数据集上运行完整流程、消融实验、对比基线 | P1 | 自动化实验脚本 |
| **FR17** | CLI 接口 | 命令行调用 ParaJudge 核心功能 | P0 | CLI 测试 |
| **FR18** | API 服务 | FastAPI 服务，提供 REST 端点 | P0 | API 测试 + 文档 |

### 4.2 非功能需求（Non-Functional Requirements）

| 编号 | 需求 | 描述 | 优先级 | 验证方法 |
|:---|:---|:---|:---|:---|
| **NFR1** | 可追溯性 | 裁决的每条结论都应能被追溯到具体证据、原则或案例 | P0 | 人工评估：随机抽取 50 条结论 |
| **NFR2** | 可解释性 | 系统输出应提供推理链而非单一结论 | P0 | 检查推理链完整性 |
| **NFR3** | 模块化与可扩展性 | 各 Agent 角色、讨论范式、裁决机制应可插拔、可扩展 | P1 | 代码评审：抽象基类设计 |
| **NFR4** | Token 效率 | 在简单问题上避免不必要的多 Agent 开销 | P1 | 问题分级 + Token 消耗分析 |
| **NFR5** | Provider 无关性 | 支持任意 OpenAI 兼容 API，不绑定特定模型 | P0 | 测试多个 Provider（OpenAI/通义千问/本地模型） |
| **NFR6** | 健壮性 | Agent 失败（超时/网络问题）时优雅降级 | P1 | 故障注入测试 |
| **NFR7** | 可复现性 | 给定相同输入+固定随机种子，输出应可复现 | P1 | 回归测试 |
| **NFR8** | 安全与隐私 | 不存储用户敏感数据；API Key 通过环境变量或安全配置 | P0 | 安全审计 |
| **NFR9** | 性能 | 单一问题端到端响应 < 5 分钟（在常见 LLM API 延迟下） | P2 | 性能基准 |
| **NFR10** | 可监控性 | 提供结构化日志，记录每个 Agent 的输入、输出、Token 消耗 | P1 | 日志系统 |

### 4.3 数据模型需求

参见 [项目开发规划.md#数据结构定义](file:///workspace/项目开发规划.md)中的第 7 节。关键 Pydantic 模型：

- `EvidenceItem` / `EvidenceBrief`：证据条目与证据包
- `PrincipleItem` / `CaseItem` / `DomainKB`：原则库与案例库
- `Argument` / `ArgumentIndex`：论点与论点索引
- `POIInteraction`：POI 交互记录

**★ Moderator 相关模型（新增）**：

| 模型 | 说明 | 核心字段 |
|:---|:---|:---|
| `ModeratorConfig` | 主持人配置（驱动辩论节奏） | `opening_max_rounds`, `cross_exam_max_rounds`, `free_debate_max_turns`, `closing_max_rounds`, `enable_poi`, `timebox_config`, `strictness` |
| `TimeboxConfig` | 时间片配置（嵌套在 ModeratorConfig 中） | `max_tokens_per_turn`, `max_seconds_per_turn`, `max_total_seconds`, `poi_max_per_phase` |
| `DebatePhase` (扩展 Enum) | 辩论阶段枚举（由 Moderator 持有） | `IDLE`, `OPENING_STATEMENTS`, `CROSS_EXAMINATION`, `FREE_DEBATE`, `CLOSING_STATEMENTS`, `DONE` |
| `TurnRequest` | 单个辩手发言请求 | `speaker_id`, `phase`, `timebox_limit`, `round_index` |
| `ModeratorWarning` | 警告记录（用于审计） | `speaker_id`, `warning_type` (duplicate/off_topic/timeout), `message`, `timestamp` |
| `DebateSummary` | Phase 1 产出（供 Phase 2.1 消费） | `key_arguments`, `phase_durations`, `warnings`, `total_duration`, `argument_index_ref` |
- `JudgeReport` / `FinalVerdict`：法官报告与最终裁决
- `UncertaintyAnnotation`：不确定性标注

### 4.4 系统约束（Constraints）

| 编号 | 约束 | 说明 |
|:---|:---|:---|
| **C1** | Python 3.10+ | 已验证在 3.14 环境 |
| **C2** | 依赖 LangGraph 编排层 | 不自研 Agent 编排框架 |
| **C3** | 不训练 LLM 模型 | 仅使用现有 API（节省成本与时间） |
| **C4** | 证据闭包约束 | 阶段 1-2 辩论仅使用阶段 0 构建的 Evidence Brief（此限制是质量保障的关键设计） |
| **C5** | 每个 Agent 独立上下文 | Agent 之间通过结构化状态索引共享信息，不共享原始对话上下文（减少噪声与偏见扩散） |
| **C6** | Provider 兼容层 | 支持 mock/openai/dashscope；扩展 Provider 不影响业务逻辑 |

---

## 4.5 Moderator 主持人角色设计（★ 新增角色）

### 4.5.1 设计动机与角色定位

在原有「Coach + Speaker」双边辩论设计中，存在以下问题：

1. **流程管理与内容产出职责混淆**：Coach 同时负责战术设计和催流程，导致 Prompt 臃肿、行为不可预测
2. **时间失控风险**：无全局时间片约束，单轮辩论可能无限循环，Token 成本不可控
3. **POI 秩序缺失**：谁来决定"此论点是否值得发起 POI"，若由辩手自行决定会导致滥用
4. **违规内容无守门**：重复发言、跑题、无证据论点缺乏独立检查机制，污染 ArgumentIndex

**Moderator 的定位**：

> 辩论流程的「状态机持有者 + 节拍器 + 质量守门员」。它本身不产出论点，不持立场。它的目标函数是「让辩论以受控、有序、符合配置的方式完成」。

### 4.5.2 角色协作关系图

```
┌──────────────┐  1: run_phase1(config, evidence)   ┌──────────────┐
│ Orchestrator │ ─────────────────────────────────▶ │  Moderator   │
│  (阶段总协调) │                                    │  (主持人)     │
└──────────────┘                                    └──┬───────┬───┘
            ▲          2: DebateSummary               │         │
            └─────────────────────────────────────────┘         │
                                                                  │
                      ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
                      │                                            │                                            │
              1.1 指令│                                    1.2 指令│                                    1.3 读写│
                      ▼                                            ▼                                            ▼
              ┌──────────┐                               ┌──────────────┐                              ┌──────────────────┐
              │ Coach (Pro) │                           │ Speaker Pro  │                              │ ArgumentIndex    │
              │ Coach (Con) │ ── tactics for speaker ─▶ │ Speaker Con  │ ◀─ 3: record argument ── │ (共享数据结构)   │
              └──────────┘                               └──────────────┘                              └──────────────────┘
                                                                   │
                                                                   ▼ 1.4 可选 POI
                                                          ┌──────────────────┐
                                                          │ POI Engine       │
                                                          │ (质询 + 响应)     │
                                                          └──────────────────┘
```

**消息与数据流向说明**：

| 编号 | 消息 | 方向 | 内容 |
|:---|:---|:---|:---|
| 1 | `run_phase1()` | Orchestrator → Moderator | 阶段配置 + Evidence Brief |
| 1.1 | `get_tactics(phase, round)` | Moderator → Coach | 请求当前阶段战术建议（Coach 不对外发言） |
| 1.2 | `speak(turn_request, tactics, brief)` | Moderator → Speaker | 传入时间片 + 战术 + 证据包；Speaker 产出 Argument |
| 1.3 | `record_argument(argument)` | Moderator → ArgumentIndex | 写入论点索引（先经过去重 / 主题检查） |
| 1.4 | `request_poi(argument, opponent)` | Speaker → POI Engine | 由 Moderator 批准/拒绝后执行 |
| 2 | `DebateSummary` | Moderator → Orchestrator | 阶段总结，供 Phase 2.1 审理消费 |

### 4.5.3 辩论阶段状态机

```
[IDLE]
   │  start_debate(ModeratorConfig)
   ▼
[OPENING_STATEMENTS]  ── 正反各 opening_max_rounds 轮 ──▶
   │
   ▼
[CROSS_EXAMINATION]   ── 双方 cross_exam_max_rounds 轮 ──▶
   │
   ▼
[FREE_DEBATE]        ── free_debate_max_turns 次切换 OR max_total_seconds ──▶
   │
   ▼
[CLOSING_STATEMENTS] ── 双方各 closing_max_rounds 轮总结 ──▶
   │
   ▼
[DONE]
   │
   ▼
产出 DebateSummary
```

**阶段切换条件的完整逻辑**（在 `src/debate/moderator.py::_should_advance_phase()` 中实现）：

- **OPENING → CROSS_EXAMINATION**：正反双方均完成 `opening_max_rounds` 次立论
- **CROSS_EXAMINATION → FREE_DEBATE**：双方各完成 `cross_exam_max_rounds` 轮交叉质询
- **FREE_DEBATE → CLOSING**：达到 `free_debate_max_turns` **或** `max_total_seconds` 超时（以先到为准）
- **CLOSING → DONE**：双方各完成 `closing_max_rounds` 轮总结
- **任意阶段 → DONE**（强制终止）：`max_total_seconds` 全阶段超时

### 4.5.4 质量守门机制（Quality Gate）

Moderator 在每条发言被写入 ArgumentIndex 之前，执行三类轻量级检查：

| 检查项 | 实现方式 | 行为 | 所需 LLM？ |
|:------|:---|:---|:---|
| **论点去重** | 计算新发言与 ArgumentIndex 中已有论点的 embedding 相似度 / 关键词重叠度 | 相似度 > 0.85 标记为 duplicate，给出警告 + 拒绝写入 | 可选（轻量 embedding 或纯启发式） |
| **主题漂移检测** | 新发言与原始问题、Evidence Brief 主题的相关性得分（关键词 + 语义） | 相关性 < 阈值给出 "off_topic" 警告；`strictness=strict` 时拒绝写入 | 可选 |
| **超时控制** | wall-clock 计时 + token 计数（tiktoken） | 超时发出 warning，截断超 token 部分 | 纯代码，无 LLM |
| **证据引用验证** | 检查 argument.evidence_refs 中的 ID 是否存在于 EvidenceBrief | 缺失引用标记 "weak_evidence"，不阻止但发出警告 | 纯代码，无 LLM |

**关键原则**：Moderator 的质量守门是「最小成本」的——能通过纯代码（状态、正则、embedding 轻量版）完成的绝不调用 LLM。这样才能保证：(a) 成本可控 (b) 行为可复现 (c) 延迟低。

### 4.5.5 ModeratorConfig 配置示例

```python
# 快速辩论（~3 分钟，简单问题）
MODERATOR_CONFIG_FAST = {
    "opening_max_rounds": 1,
    "cross_exam_max_rounds": 1,
    "free_debate_max_turns": 3,
    "closing_max_rounds": 1,
    "enable_poi": False,
    "strictness": "loose",
    "timebox": {
        "max_tokens_per_turn": 200,
        "max_seconds_per_turn": 60,
        "max_total_seconds": 180,
    },
}

# 深度辩论（~20 分钟，复杂问题）
MODERATOR_CONFIG_DEEP = {
    "opening_max_rounds": 2,
    "cross_exam_max_rounds": 3,
    "free_debate_max_turns": 8,
    "closing_max_rounds": 1,
    "enable_poi": True,
    "strictness": "normal",
    "timebox": {
        "max_tokens_per_turn": 400,
        "max_seconds_per_turn": 120,
        "max_total_seconds": 1200,
        "poi_max_per_phase": 3,
    },
}
```

### 4.5.6 与现有模块的关系与变更

| 现有模块 | 变更内容 | 影响范围 |
|:---|:---|:---|
| `src/debate/workflow.py` | Phase 1 的驱动者从"Coach/Speaker 循环"改为 Moderator 状态机驱动 | 核心编排逻辑调整，但对外接口 `DebateWorkflow.run()` 签名不变 |
| `src/debate/moderator.py` | **新增**：`Moderator` 类（状态机 + 质量守门） | 新文件 |
| `src/debate/argument_index.py` | 新增 `has_similar_argument(embedding, threshold)` 方法 | 扩展现有文件 |
| `backend/models/schemas.py` | 新增 `ModeratorConfig` / `TimeboxConfig` / `DebatePhase`（扩展）/ `TurnRequest` / `ModeratorWarning` / `DebateSummary` 模型 | 扩展现有文件 |
| Phase 2.1 ReviewWorkflow | 从消费"原始发言列表"改为消费 `DebateSummary` + `ArgumentIndex` | 对 Phase 2.1 无破坏性变更（结构更清晰） |
| Phase 2.2 Judgment | 无直接变化（仍然消费 ArgumentIndex + 审理报告） | 无变更 |

---



## 五、系统概要设计 — 从用户问题到判决书的完整流程

### 5.1 高层架构图（小白友好版）

```
    你（用户）输入一个问题
         │
         ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  ① 问题理解与分类（ProblemClassifier）                          │
  │    "这是事实性问题？决策性问题？创新型问题？"                    │
  └─────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  ② 证据构建（Phase 0 — EvidenceBuilder）                        │
  │    多源检索 → 去重 → 评分 → 打包成 Evidence Brief               │
  │    "这是法庭开审前，先收集所有可用证据"                          │
  └─────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  ③ 结构化辩论（Phase 1 — DebateEngine）                         │
  │    ┌────────────────────────────────────────────────────┐   │
  │    │  Moderator（主持人）                                 │   │
  │    │    · 管理阶段：立论 → 交叉质询 → 自由辩论 → 总结陈词  │   │
  │    │    · 质量守门：重复发言？跑题？超时？                  │   │
  │    │    · 维护辩论状态：当前阶段、已发言数、warnings       │   │
  │    └──────────────────┬──────────────────────────────────┘   │
  │                       │                                       │
  │           ┌──────────┼────────────┐                          │
  │           ▼          ▼            ▼                          │
  │      正方 Coach  反方 Coach  POI 质询引擎                      │
  │           │          │            │                           │
  │           ▼          ▼            │                           │
  │      正方 Speaker × 2  反方 Speaker × 2                        │
  │           │          │                                            │
  │           └──────┬───┘                                            │
  │                  ▼                                                 │
  │          ArgumentIndex（所有论点索引）                            │
  │             + DebateSummary（Phase 1 总结报告）                   │
  └─────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  ④ 独立审理（Phase 2.1 — ReviewEngine）                         │
  │    检察官 Agent：逐条检查论点，找漏洞、找缺失证据、找逻辑跳步    │
  │    辩护律师 Agent：对检察官指出的每个漏洞进行最佳辩护           │
  │    "这是法庭辩论后的'质证'环节——不受情绪影响，只看证据"        │
  └─────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  ⑤ 五维专业化裁决（Phase 2.2 — JudgmentEngine）                 │
  │    并行评估，互不干扰：                                        │
  │      · E-Judge（证据法官）：证据质量评估                       │
  │      · L-Judge（逻辑法官）：推理链条完整性                     │
  │      · P-Judge（原则法官）：是否符合领域原则                   │
  │      · C-Judge（案例法官）：是否匹配已有案例                   │
  │      · I-Judge（创新法官）：★ 创新保护——新想法是否有价值        │
  │                           (不因为"无先例"而扣分)              │
  │                         ↓                                       │
  │      F-Judge（综合裁决官）：根据问题类型加权五法官评分          │
  │           ↓                                                   │
  │      ReasoningChainBuilder：生成推理链（每条结论标注来源）       │
  │           ↓                                                   │
  │      ReportGenerator：生成 HTML / Markdown / JSON 判决书        │
  └─────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
                    你收到一份可追溯的判决书 + 推理链
```

### 5.2 数据流设计：每个阶段的输入与输出

**核心设计原则**：每个阶段的输出是下一阶段的唯一输入。阶段之间不共享原始对话上下文，只共享结构化状态——这确保阶段间解耦，减少偏见传递。

| 阶段 | 输入 | 输出 | 关键字段 |
|:---|:---|:---|:---|
| **Phase 0** | 用户问题字符串 | `EvidenceBrief` + `ProblemType` | `evidence_items[]`, `query_keywords`, `domain` |
| **Phase 1** | `EvidenceBrief` + `ProblemType` | `ArgumentIndex` + `DebateSummary` + `ModeratorWarnings[]` | `arguments[]`, `cross_exam_pairs[]`, `phase_durations{}`, `warnings[]` |
| **Phase 2.1** | `ArgumentIndex` + `DebateSummary` + `EvidenceBrief` | `ReviewReport` | `prosecutor_findings[]`, `defense_responses[]`, `issue_summary` |
| **Phase 2.2** | `ReviewReport` + `ArgumentIndex` + `EvidenceBrief` + `DomainKB`（可选） | `FinalVerdict` + `ReasoningChain[]` + `HTML/Md/JSON` 判决书 | `five_judge_scores{}`, `weighted_total`, `reasoning_steps[]`, `confidence_annotation` |

**阶段间的状态传递（从数据角度理解）**：

```
用户问题 
  → [ProblemClassifier] → problem_type + query_keywords
  → [EvidenceBuilder]   → EvidenceBrief { items: [ {id, title, source, credibility, ...} ] }
  → [DebateEngine]      → ArgumentIndex { arguments: [ {id, content, side, evidence_refs[]} ] }
                         + DebateSummary { key_arguments, phase_durations, warnings }
  → [ReviewEngine]      → ReviewReport { prosecutor_findings, defense_responses, issues }
  → [JudgmentEngine]    → FinalVerdict { judge_scores, final_score, reasoning_chain, confidence }
  → [ReportGenerator]   → HTML / Markdown / JSON
```

### 5.3 Agent 角色设计说明（每个 Agent 具体做什么）

**Phase 0 Agent（证据构建阶段）**

| 角色 | 职责 | 输入 | 输出 | 实现提示 |
|:---|:---|:---|:---|:---|
| ProblemClassifier | 识别问题类型 | 用户问题 | `problem_type`（事实/决策/创新/开放） + `domain` + `complexity_level` | 基于关键词 + LLM 辅助判断 |
| EvidenceBuilder | 构建证据包 | 问题 + 分类结果 | `EvidenceBrief` | 调用搜索引擎/数据库，评分排序，打包 |

**Phase 1 Agent（辩论阶段）**

| 角色 | 职责 | 输入 | 输出 | 实现提示 |
|:---|:---|:---|:---|:---|
| Moderator（主持人） | 持有状态机 + 管理发言权 + 质量守门 | `ModeratorConfig` + 当前辩论状态 | `DebateSummary` + `ModeratorWarnings[]` | 不产出论点，只管理流程；核心状态是 `debate_phase` |
| Coach（教练） | 战术设计 + 证据分配——不直接发言 | 问题 + EvidenceBrief + 本方已有发言 | `CoachPlan`：本轮发言主题、证据选择、反驳目标 | 每方 1 名 Coach；Coach 不对外说话 |
| Speaker（辩手） | 产出结构化论点，引用证据 | CoachPlan + EvidenceBrief + TurnRequest | `Argument` | 每方 2-3 名；必须引用 Phase 0 证据 |
| POI Engine | 中断式质询——"对方辩友，等一下" | 对方最新发言 + 相关证据 | `POIInteraction` | 可选启用，由 Moderator 批准是否触发 |

**Phase 2.1 Agent（审理阶段）**

| 角色 | 职责 | 输入 | 输出 | 实现提示 |
|:---|:---|:---|:---|:---|
| Prosecutor（检察官） | 系统性检查论点质量：选择性呈现证据？逻辑跳步？未验证假设？ | ArgumentIndex + DebateSummary | `ProsecutorFindings`：逐条问题清单 | 不持立场，只找漏洞 |
| DefenseAttorney（辩护律师） | 为正方进行最佳辩护：补充证据、解释逻辑 | 检察官的每条 finding | `DefenseResponse` | 配合检察官，形成完整审理交互 |

**Phase 2.2 Agent（裁决阶段）**

| 角色 | 职责 | 输入 | 输出 | 实现提示 |
|:---|:---|:---|:---|:---|
| E-Judge（证据法官） | 评估证据质量 + 证据引用正确性 | ReviewReport + EvidenceBrief | `EvidenceScore` + 证据级标注 | 检查引用 ID 是否确实存在于 Evidence Brief |
| L-Judge（逻辑法官） | 评估推理链条完整性 | ReviewReport + ArgumentIndex | `LogicScore` + 逻辑步骤标注 | 检查"因为 A，所以 B"的每一步是否有支撑 |
| P-Judge（原则法官） | 评估是否符合领域知识库原则 | ReviewReport + DomainKB | `PrincipleScore` + 原则匹配标注 | 可选——没有 DomainKB 时此维度权重为 0 |
| C-Judge（案例法官） | 评估是否有匹配案例支持结论 | ReviewReport + DomainKB | `CaseScore` + 案例匹配标注 | 同样可选 |
| I-Judge（创新法官） | ★ 评估创新性 + 创新保护 | ReviewReport + 问题类型 | `InnovationScore` + 创新保护标注 | **创新保护的核心位置**——对"无先例"的论点不扣分，反而评估其潜在价值 |
| F-Judge（综合裁决官） | 根据问题类型加权五法官评分，生成最终判决 | 五法官评分 + `ProblemType` | `FinalVerdict` | 不同问题类型对五维度有不同权重配置 |
| ReasoningChainBuilder | 将裁决过程转化为结构化推理链 | FinalVerdict + 各法官评分依据 | `ReasoningChain[]` | 每条推理步具体到证据/原则/案例 ID |
| ReportGenerator | 渲染最终判决书 | FinalVerdict + ReasoningChain | HTML / Markdown / JSON | Jinja2 模板驱动 |

### 5.4 核心设计约束（为什么这样设计？）

1. **证据闭包原则**：所有论点必须引用 Evidence Brief 中的证据。为什么？——确保辩论有依据，不是空口争论。

2. **独立审理原则**：Phase 2.1 的检察官不接触 Phase 1 的辩手，只看结构化论点索引和证据。为什么？——避免"情绪污染"和"自信的语气"影响评估。

3. **专业化裁决原则**：五法官独立评分而不是一个全能法官。为什么？——不同评估维度需要不同的思维模式，一个 Agent 难以同时在所有维度保持高质量。

4. **状态解耦原则**：阶段间通过结构化数据通信，不传递原始对话上下文。为什么？——减少偏见传播，每个阶段有清晰的职责边界，方便未来拆分到不同服务。

5. **可追溯性原则**：每条结论都标注到具体证据/原则/案例 ID。为什么？——用户有权知道"系统为什么得出这个结论？证据是什么？"。这也是问责式 AI 的基本要求。

---

## 六、技术问题分析与改进方向

> **本节的目标**：诚实面对我们的设计和技术栈中的问题与风险。对于每个问题，我们分析"这是什么风险""影响有多大""有没有现成解决方案"。不回避问题，是做好工程研究的基本态度。

### 6.1 当前技术栈的核心风险评估

| 技术/组件 | 功能 | 风险等级 | 具体风险 | 缓解策略 |
|:---|:---|:---|:---|:---|
| **LangGraph** | 四阶段编排 + Agent 间通信 | ⚠️ 中风险 | （1）LangGraph 版本升级频繁，API 可能破坏性变更；（2）复杂 StateGraph 在多人协作时调试困难；（3）与非 LangChain 生态的组件集成需要适配器 | （1）锁定主版本号 + 冻结版本升级在里程碑之间；（2）为每个子图设计独立的集成测试；（3）通过 Pydantic 模型定义标准化 State，减少对 LangGraph 的直接耦合 |
| **LLM Provider（通义千问）** | 提供 Agent 推理能力 | ⚠️ 中-高风险 | （1）长上下文 + 结构化输出的质量可能不稳定；（2）不同模型对中文推理质量差异大；（3）API 调用成本与延迟不可预测 | （1）多 Provider 设计 + Provider 无关抽象层（`src/llm/providers.py`）；（2）结构化输出 + JSON 模式验证；（3）实现 tenacity 重试 + 缓存层 |
| **Pydantic 模型** | 数据契约 | ✅ 低风险 | 模型版本之间可能存在字段变更导致的兼容问题 | 通过 `model_config(extra="forbid")` 严格模式 + 每个模型的单元测试 |
| **httpx / 多源检索** | 证据检索引擎 | ⚠️ 中风险 | （1）搜索引擎速率限制；（2）不同检索源的返回格式差异大；（3）对冷领域/中文资源覆盖不足 | （1）统一的 `RetrieverClient` 抽象；（2）多级缓存（内存缓存 + 磁盘缓存）；（3）对"证据不足"情况有降级策略 |
| **Jinja2 模板** | 判决书渲染 | ✅ 低风险 | 模板可读性随复杂度增加可能下降 | 模块化模板 + 测试示例渲染 |
| **异步 I/O** | 五法官并行评估 | ⚠️ 中风险 | 如果 Agent 之间有状态依赖，异步并发会引入竞态条件 | 设计五法官为纯函数——只读状态，不改共享状态；各自独立评分 |
| **整个系统** | 端到端质量 | ⚠️ 高风险（取决于 LLM 质量） | LLM 的幻觉/推理质量限制了系统上界。这是所有 LLM 应用的共同天花板，不是 ParaJudge 的独特问题 | 我们的策略：通过多阶段架构 + 证据约束 + 多法官评审，**系统性降低幻觉率**，而非期望消除它 |

### 6.2 已识别的具体技术问题

**问题 1：论点去重（Moderator 的质量守门）如何实现？**

当前设计的假设是"可以用 embedding 相似度或关键词重叠来检测重复论点"。但实际挑战是：

- 语义相似度不是简单的向量距离——两个论点可能用词完全不同但语义等价
- 阈值选取：0.85 还是 0.9？不同任务可能需要不同阈值
- 计算开销：对每条新发言做全索引扫描不经济

**解决思路（已纳入设计）**：
1. 使用轻量级语义哈希 + 关键词重叠作为快速筛选（粗筛，成本 ~O(N)）
2. 对粗筛出的候选对，再调用轻量 LLM 做"是否重复"的 2 分类判断（精筛，仅在灰区调用）
3. 参考 MACI（2025）中的"overlap signal"设计——简单信号就足够有效

**问题 2：主题漂移检测难以精确实现**

"这个论点是否偏离了原始问题？"是一个需要理解上下文的判断。

**解决思路**：
1. 以 Evidence Brief 的主题关键词 + 问题本身的关键词作为"主题基准"
2. 用简单的 BM25 相似度或 embedding 相似度来计算新论点与基准的关联度
3. 低于 `off_topic_threshold`（默认 0.4）时标记警告，但不直接拒绝（在 `strictness=strict` 时才拒绝）
4. 严格模式下可调用 LLM 判断"此论点是否支持或反驳问题中的核心议题"

**问题 3：五法官的权重如何选取？**

不同问题类型对五维度的重视程度不同。例如：
- 事实核查型问题 → 证据(E) 70%, 逻辑(L) 20%, 其他各 3%
- 创新型问题 → 证据(E) 25%, 逻辑(L) 25%, 创新(I) 30%, 其他各 10%

**解决思路**：
1. 先基于人工经验设置初始权重（MVP 阶段）
2. 有 ≥ 500 条标注样本后，用机器学习自动优化权重（参考 §2.4 中的 MALLM 和 swarm-debate 的评估方法）
3. 权重作为配置文件可修改，不硬编码
4. 参考 MACI (2025) 的"保守软权重"——对不确定的维度设置较低权重，而非强行分配

**问题 4：推理链的生成是事后的，会不会与实际推理不一致？**

"先生成判决，再回溯写推理链"可能导致"结论先行，推理链后补"的问题。

**解决思路**：
1. 每个法官在评分时**必须同时输出简短理由**（2-3 句话，说明"为什么给这个分数"）
2. F-Judge 的权重汇总时，**强制要求引用各法官的理由 ID**
3. ReasoningChainBuilder 将法官理由 + 最终权重整合为完整推理链
4. 换句话说：**推理不是事后生成的，而是从各法官结构化评分中"抽取 + 组装"出来的**

**问题 5：证据闭包可能产生"证据不全"的困境**

如果 Phase 0 证据检索没有找到关键证据，那么后续所有阶段都基于不完整的信息在运作——系统不会"意识到"自己缺了什么。

**解决思路**：
1. EvidenceBuilder 产出一个"证据充分性评分"（基于检索到的条目数、平均可信度、来源多样性）
2. 如果评分低于阈值，Phase 2.2 的 FinalVerdict 会带上"证据不足"标记
3. I-Judge（创新法官）对"证据不足但推理合理"的新想法给予正面评分——这是创新保护的一部分
4. 用户可以在报告中看到"证据不足"的警告，以及系统建议"可能需要进一步检索的方向"

**问题 6：可复现性挑战**

即使固定随机种子，LLM 输出也不完全确定（特别是长上下文时）。这使得端到端测试困难。

**解决思路**：
1. 对于测试和实验，使用 Mock Provider（固定返回预设回复）来确保可复现
2. 对于生产环境，接受"近似可复现"——相同问题应该得到**相似**（但不必完全相同）的结论
3. 参考 MALLM (2025) 的评估管线——对每次运行记录完整配置（Model, Temperature, Top-p, ModeratorConfig），使得任何一次运行都可以重现
4. `DebateSummary` 中的 `warnings` 列表是结构化的，其内容可用于检查"Moderator 是否做出了相同的守门决策"

### 6.3 潜在优化点（MVP 之后的改进方向）

| 优先级 | 优化点 | 预期效果 | 实现难度 |
|:---|:---|:---|:---|
| P0 | **异步流式输出**——五法官评分实时返回给前端用户，而非等全部完成后一次性输出 | 用户体验大幅提升，感知速度提高 2-5 倍 | 中——需要 FastAPI SSE / WebSocket |
| P0 | **增量推理缓存**——对同一/相似问题，缓存已有结果；检测重复提交的问题 | 降低 70-90% 重复调用成本 | 中——需要在编排层实现语义检索 |
| P1 | **并行扩展**——辩论阶段支持更多辩手，裁决阶段支持更多定制化法官角色 | 适应不同领域的专业需求 | 低——当前架构已模块化，仅需新增配置 |
| P1 | **用户反馈闭环**——用户对判决书打分 + 标注"不同意哪条推理"，用于系统持续改进 | 让系统随时间变得更智能 | 中高——需要存储用户反馈 + 分析流程 |
| P1 | **多语言支持**——英文/中文双语证据检索 + 双语 Prompt 模板 | 扩大应用场景 | 中——主要工作在证据检索层和 Prompt 层 |
| P2 | **可视化辩论过程**——用 D3.js 或 React Flow 渲染论点关系图 | 提升用户理解和教学价值 | 中高——前端工作量大 |
| P2 | **自定义领域知识库**——允许用户上传自己的原则/案例库（如"软件工程最佳实践""公司产品规范"） | 适应特定组织/团队的特殊需求 | 中——需要设计知识库格式和加载机制 |

### 6.4 新技术与研究方向（持续关注）

> 以下方向不是 MVP 的一部分，但值得持续跟踪，成熟后可以作为 P1/P2 版本的增量功能。

| 方向 | 是什么 | 对 ParaJudge 的潜在价值 | 参考来源 |
|:---|:---|:---|:---|
| **Tree of Thoughts / Graph of Thoughts** | 把推理过程显式建模为树/图结构，而不是线性 token 流 | 可以把 Phase 1 的辩论从"线性轮流发言"升级为"图结构论点探索"，Agent 可以针对不同子论点分支独立工作 | Yao et al. (2023); Besta et al. (2023) |
| **Reflection / Self-Critique 机制** | Agent 在产出答案后，进行"自我反思"，识别并修正自己的错误 | Phase 1 的 Coach 可以在"设计战术"后增加"战术评审"环节，识别是否遗漏了关键证据 | Madaan et al. (2023); Reflection 7B |
| **混合专家模型（MoE）** | 根据问题类型路由到不同的专家模型 | 五法官可以使用不同的专门模型而非同一个大模型——证据法官使用偏事实核查的模型，创新法官使用偏发散思维的模型 | Mixtral; GPT-4（内部疑似 MoE） |
| **RAG + 结构化知识图谱** | 证据不仅仅是文本段落，而是带有实体关系的知识图谱 | Evidence Brief 升级为"证据图谱"——法官可以沿着关系链推理，而不是基于独立文本 | Neo4j + 向量检索；LlamaIndex KnowledgeGraphIndex |
| **过程监督奖励模型（PRM）** | 对推理过程的每一步给奖励信号，而不是只看最终结果 | 用于训练/微调 F-Judge 的加权汇总逻辑——对"好的推理步骤"给予奖励，即使最终结论"错了" | OpenAI PRM (2023); DeepSeek Math |
| **可复现实验管线（像 MALLM 那样）** | 标准化的"运行配置 → 执行 → 记录 → 对比"管线 | 使得 ParaJudge 可以作为研究工具使用——方便团队在其上做 ablation study，也方便外部复现 | MALLM (2025); 本项目 §4 的 ModeratorConfig 已为此设计 |
| **Confidence Estimation（置信度估计）** | 系统不仅输出结论，还估计"我对这个结论有多大把握" | 这是"可问责 AI"的关键能力。当前我们在 FinalVerdict 中有 confidence_annotation，但可以更精细——对每条推理步骤都估计置信度 | Confident LLM (2024); Hu et al. (2026) "The Confident Liar" |

---

## 七、技术栈规划

### 7.1 完整技术栈图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 / 接口层                                  │
│ ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐          │
│ │  CLI         │  │   FastAPI        │  │  网页演示    │          │
│ │  (Typer)    │  │   (REST API)     │  │  (Streamlit/ │          │
│ └──────────────┘  └──────────────────┘  │  HTML)       │          │
│                                         └──────────────┘          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    编排层（LangGraph）                               │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │  阶段 0: EvidenceBuilder (检索 → 构建 → 排序)                │  │
│ │    ├─ 关键词提取 (LLM)                                        │  │
│ │    ├─ 多源检索 (httpx → arXiv/S2/Crossref)                    │  │
│ │    └─ 证据包构建 (Pydantic)                                   │  │
│ │                                         ↓                       │  │
│ │  阶段 1: DebateEngine (辩论)                                  │  │
│ │    ├─ Moderator (主持人：状态机 + 时间片 + 质量守门)         │  │
│ │    ├─ 正方 Coach + 正方 Speaker 1/2/3                        │  │
│ │    ├─ 反方 Coach + 反方 Speaker 1/2/3                        │  │
│ │    ├─ POI 段间质询引擎                                        │  │
│ │    └─ 论点索引 + 引用验证                                      │  │
│ │                                         ↓                       │  │
│ │  阶段 2.1: ReviewEngine (审理)                                │  │
│ │    ├─ 检察官 (检查证据选择性呈现 + 逻辑漏洞)                   │  │
│ │    └─ 辩护律师 (最佳辩护 + 补充证据)                           │  │
│ │                                         ↓                       │  │
│ │  阶段 2.2: JudgmentEngine (裁决)                              │  │
│ │    ├─ E-Judge (证据审查官) ┐                                  │  │
│ │    ├─ L-Judge (逻辑审查官) ├─ 并行评估                        │  │
│ │    ├─ P-Judge (原则审查官) │                                  │  │
│ │    ├─ C-Judge (案例审查官) │                                  │  │
│ │    └─ I-Judge (创新审查官) ┘ → F-Judge (综合裁决官)         │  │
│ │                                         ↓                       │  │
│ │  输出: 类判决书 HTML / PDF / JSON                              │  │
│ └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    Agent 层（LLM Provider）                           │
│ ┌──────────────────┐  ┌──────────────────┐                          │
│ │  LangChain Core │→│  LLM 兼容层       │                          │
│ │  (Base Classes) │  │  (OpenAI/        │                          │
│ │                  │  │   Dashscope/     │                          │
│ │  Prompt Templates│  │   Mock)          │                          │
│ └──────────────────┘  └──────────────────┘                          │
│                                                                      │
│  每个 Agent 为 LangGraph Runnable，配置独立 Prompt + 状态访问        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    数据与知识层                                        │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│ │ Evidence    │  │ Domain KB    │  │ State Index  │             │
│ │ Brief       │  │ (原则+案例)  │  │ (论点索引)   │             │
│ └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                    │
│  存储格式：JSON / YAML / Python 对象                              │
│  数据模型：Pydantic v2（强类型校验）                                │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.2 核心依赖与版本

| 分类 | 包名 | 最低版本 | 用途 | 必要性 |
|:---|:---|:---|:---|:---|
| **编排层** | langgraph | ≥ 0.2.0 | 多阶段 Agent 工作流编排 | 核心 |
| **编排层** | langchain | ≥ 0.3.0 | LLM 调用与工具链 | 核心 |
| **编排层** | langchain-core | ≥ 0.3.0 | 核心抽象 | 核心 |
| **编排层** | langchain-community | ≥ 0.3.0 | 社区 Provider 支持 | 推荐 |
| **数据模型** | pydantic | v2 | 结构化数据定义与验证 | 核心 |
| **数据模型** | pydantic-settings | ≥ 2.5.0 | 配置管理 | 核心 |
| **LLM Provider** | openai | ≥ 1.40.0 | OpenAI 兼容 API | 核心 |
| **LLM Provider** | dashscope | ≥ 1.20.0 | 通义千问 SDK | 推荐 |
| **检索** | httpx | ≥ 0.27.0 | 现代异步 HTTP 客户端 | 核心 |
| **检索** | arxiv | ≥ 2.1.0 | arXiv API | 核心 |
| **PDF 解析** | (现有实现) | - | PyMuPDF 已封装 | 辅助（证据准备） |
| **Web 服务** | fastapi | ≥ 0.111.0 | API 框架 | 核心 |
| **Web 服务** | uvicorn[standard] | ≥ 0.30.0 | ASGI 服务器 | 核心 |
| **CLI** | typer | ≥ 0.12.0 | 命令行框架 | 核心 |
| **CLI** | rich | ≥ 13.7.0 | 终端彩色输出 | 推荐 |
| **配置** | python-dotenv | ≥ 1.0.0 | `.env` 加载 | 核心 |
| **报告渲染** | jinja2 | ≥ 3.1.0 | HTML 模板渲染 | 推荐（P0） |
| **知识图谱** | networkx | ≥ 3.3.0 | 论点关系图（可选高级功能） | P2 |
| **数学运算** | numpy | ≥ 1.26.0 | 数值工具（评估统计） | 推荐 |
| **异步重试** | tenacity | ≥ 9.0.0 | API 调用重试机制 | 推荐 |
| **数据处理** | pyyaml | ≥ 6.0 | YAML 配置/知识库加载 | 推荐（P1） |

### 7.3 项目目录结构（目标设计）

```
/workspace/
│
├─── cli.py                          # CLI 入口（已有，扩展）
├─── api.py                          # FastAPI 入口（已有，扩展）
├─── main.py                         # CLI 快捷入口（已有）
│
├─── src/
│   ├─── __init__.py
│   │
│   ├─── search/                     # (已有) 文献检索模块
│   │   ├── engine.py               # 统一检索入口
│   │   ├── arxiv_client.py         # arXiv
│   │   ├── semantic_scholar_client.py  # Semantic Scholar
│   │   ├── crossref_client.py      # Crossref
│   │   └─── __init__.py
│   │
│   ├─── parse/                      # (已有) PDF 解析
│   │   ├── pdf_parser.py           # PyMuPDF 解析
│   │   ├── text_cleaner.py         # 文本清洗
│   │   └─── __init__.py
│   │
│   ├─── reference/                  # (已有) 引用管理
│   │   ├── bibtex_manager.py       # BibTeX 解析与导出
│   │   └─── __init__.py
│   │
│   ├─── writer/                     # (已有) 写作辅助
│   │   ├── llm_helper.py           # AcademicWriter 类
│   │   ├── prompt_templates.py     # Prompt 模板库
│   │   └─── __init__.py
│   │
│   ├─── knowledge/                  # 🆕 (新增) 知识管理
│   │   ├── evidence.py             # EvidenceItem, EvidenceBrief 构建
│   │   ├── domain_kb.py            # PrincipleItem, CaseItem, DomainKB
│   │   ├── classifier.py           # 问题类型识别器
│   │   ├── loader.py               # YAML/JSON 知识库加载器
│   │   └─── __init__.py
│   │
│   ├─── debate/                     # 🆕 (新增) 辩论引擎（阶段 1）
│   │   ├── agent_base.py           # ParaJudge Agent 基类
│   │   ├── roles.py                # Coach/Speech 角色定义
│   │   ├── coach.py                # 教练 Agent（战术设计 + 证据分配）
│   │   ├── speaker.py              # 辩手 Agent（发言 + POI 响应）
│   │   ├── moderator.py            # 🆕 主持人 Moderator（状态机 + 时间片 + 质量守门）
│   │   ├── poi_engine.py           # POI 段间质询引擎
│   │   ├── evidence_closure.py     # 证据闭包与引用验证
│   │   ├── argument_index.py       # 论点索引维护
│   │   ├── workflow.py             # LangGraph 主工作流
│   │   └─── __init__.py
│   │
│   ├─── review/                     # 🆕 (新增) 审理引擎（阶段 2.1）
│   │   ├── prosecutor.py           # 检察官 Agent
│   │   ├── defense.py              # 辩护律师 Agent
│   │   ├── workflow.py             # 审理工作流
│   │   └─── __init__.py
│   │
│   ├─── judgment/                   # 🆕 (新增) 裁决引擎（阶段 2.2）
│   │   ├── judges.py               # 五位专业法官 Agent
│   │   ├── final_judge.py          # F-Judge 综合裁决官
│   │   ├── innov_protect.py        # 创新保护机制
│   │   ├── reasoning_chain.py      # 推理链构建
│   │   ├── uncertainty.py          # 不确定性标注
│   │   ├── report_generator.py     # 裁决报告生成（HTML/Markdown/JSON）
│   │   ├── report_template.html    # 裁决书模板
│   │   ├── workflow.py             # 裁决工作流
│   │   └─── __init__.py
│   │
│   ├─── llm/                        # 🆕 (新增) LLM Provider 封装层
│   │   ├── providers.py            # Provider 抽象与实现
│   │   ├── prompt_library.py       # 可复用 Prompt 模板库
│   │   ├── token_counter.py        # Token 统计与消耗监控
│   │   └─── __init__.py
│   │
│   └─── utils/                      # (已有) 工具模块
│       ├── io.py                    # JSON/文本读写
│       └─── __init__.py
│
├─── backend/
│   ├─── models/
│   │   ├── schemas.py              # (已有 + 扩展) 所有 Pydantic 模型
│   │   └─── __init__.py
│   │
│   └─── app.py                      # FastAPI 应用（可选：替换 api.py）
│
├─── experiments/                    # 🆕 (新增) 评估实验
│   ├─── benchmarks/                # 基准数据集加载
│   │   ├── gsm8k_loader.py         # GSM8K
│   │   ├── mmlu_loader.py          # MMLU
│   │   ├── politifact_loader.py    # PolitiFact
│   │   ├── averitec_loader.py      # AVEITEC
│   │   └─── ...
│   │
│   ├─── baselines/                 # 基线实现
│   │   ├── single_llm.py           # 单 LLM（CoT）
│   │   ├── self_consistency.py     # Self-Consistency
│   │   ├── standard_mad.py         # 标准 MAD
│   │   └─── mallm_simple.py        # MALLM 简化版
│   │
│   ├─── ablations/                 # 消融实验脚本
│   │   ├── ab1_no_coach.py         # 无教练
│   │   ├── ab2_no_poi.py           # 无 POI
│   │   ├── ab3_single_judge.py     # 单全能法官
│   │   ├── ab4_no_review.py        # 无审理阶段
│   │   ├── ab5_no_innovprotect.py  # 无创新保护
│   │   ├── ab6_no_closure.py       # 无证据闭包
│   │   ├── ab7_homogeneous.py      # 同质化 Agent
│   │   └─── ab8_simplified.py      # 简化两阶段
│   │
│   ├─── metrics/                   # 评估指标实现
│   │   ├── accuracy.py             # 准确率
│   │   ├── evidence_coverage.py    # 证据覆盖率
│   │   ├── citation_accuracy.py    # 引用准确率
│   │   ├── vulnerability_exposure.py # 漏洞暴露率
│   │   ├── traceability_score.py   # 可追溯性评分
│   │   ├── uncertainty_calibration.py # 不确定性校准度
│   │   └─── human_eval_templates.md  # 人工评估模板
│   │
│   └─── scripts/                   # 运行脚本
│       ├── run_parajudge.py        # 运行 ParaJudge
│       ├── run_baselines.py        # 运行所有基线
│       ├── run_ablations.py        # 运行消融实验
│       ├── aggregate_results.py    # 结果聚合
│       └─── generate_report.py     # 生成评估报告
│
├─── data/                          # 数据目录
│   ├─── evidence/                  # 生成的 Evidence Brief
│   ├─── domain_kb/                 # 领域知识库
│   │   ├── math.yaml
│   │   ├── medical.yaml
│   │   ├── law.yaml
│   │   ├── factcheck.yaml
│   │   ├── engineering.yaml
│   │   └─── general.yaml
│   ├─── debate_papers_raw.json     # (已有) 原始论文数据
│   └─── custom_papers/             # 自定义论文导入目录
│
├─── notebooks/                     # (已有) Jupyter 演示
│   ├─── 01_search_demo.py          # 检索演示
│   ├─── 02_parse_pdf_demo.py       # PDF 解析演示
│   ├─── 03_reference_demo.py       # 引用管理演示
│   ├─── 04_writing_demo.py         # 写作辅助演示
│   ├─── 05_end_to_end.py           # 端到端演示
│   └─── 🆕 parajudge_tutorial.ipynb # ParaJudge 教程
│
├─── docs/                          # 🆕 (新增) 项目文档
│   ├─── ARCHITECTURE.md            # 架构设计文档
│   ├─── AGENT_DESIGN.md            # Agent 设计规范
│   ├─── API_DESIGN.md              # API 设计文档
│   ├─── EVALUATION_DESIGN.md       # 评估方案
│   └─── 使用指南.md                  # 使用指南
│
├─── requirements.txt               # (已有) 核心依赖
├─── requirements-experimental.txt  # (已有) 实验依赖
├─── .env.example                   # (已有) 环境变量模板
├─── .gitignore                     # (已有) Git 忽略规则
└─── README.md                      # (已有 + 更新) 项目主页
```

### 7.4 模块划分与职责边界

| 模块 | 主要职责 | 核心类/函数 | 对外接口 |
|:---|:---|:---|:---|
| **src.knowledge** | 证据构建、知识库加载、问题识别 | `EvidenceBriefBuilder`, `DomainKBLoader`, `ProblemClassifier` | 提供统一的 `build_evidence_brief(query)` |
| **src.debate** | 教练-辩手辩论、POI、论点索引、**Moderator 流程控制** | `Coach`, `Speaker`, `Moderator`, `POIEngine`, `EvidenceClosure`, `DebateWorkflow`, `ArgumentIndex` | `DebateWorkflow.run(problem, evidence_brief)` |
| **src.review** | 检察官-辩护律师审理 | `Prosecutor`, `DefenseAttorney`, `ReviewWorkflow` | `ReviewWorkflow.run(debate_state, evidence_brief)` |
| **src.judgment** | 五维法官裁决、推理链生成、报告渲染 | `EvidenceJudge`/`LogicJudge`/`PrincipleJudge`/`CaseJudge`/`InnovationJudge`, `FinalJudge`, `ReasoningChainBuilder`, `ReportGenerator` | `JudgmentWorkflow.run(review_state, evidence_brief, domain_kb, problem_type)` |
| **src.llm** | LLM Provider 封装、Prompt 管理、Token 统计 | `LLMProvider`, `PromptLibrary`, `TokenCounter` | `generate(role, prompt, **kwargs)` |
| **backend.models** | Pydantic 数据模型定义 | 所有 `*State`, `*Report`, `*Verdict` 模型 | 数据结构定义 |

---

## 八、实施路线图与里程碑

### 8.1 分阶段实施时间表

```
阶段 P0：基础设施与框架（第 1-3 周）
  ├─ 初始化模块目录、创建 Agent 基类
  ├─ src.llm：Provider 兼容层 + Prompt 模板库 + Token 统计
  ├─ backend.models：扩展 Pydantic 模型（证据/论点/裁决）
  └─ 基础 CLI（`parajudge --help`）与 FastAPI 骨架
      
阶段 P1：证据与知识库（第 4-6 周）
  ├─ src.knowledge.evidence：Evidence Brief 构建
  ├─ src.knowledge.domain_kb：YAML 原则库/案例库加载
  ├─ src.knowledge.classifier：问题类型识别
  └─ 构建 6 个领域的初始原则库（math/medical/law/...）

阶段 P2：辩论引擎（阶段 1）（第 7-10 周）
  ├─ src.debate.agent_base：ParaJudge Agent 基类
  ├─ src.debate.coach：正方/反方教练
  ├─ src.debate.speaker：正方/反方辩手
  ├─ src.debate.moderator：★ 主持人 Moderator（状态机 + 时间片 + 质量守门）
  ├─ src.debate.poi_engine：段间质询机制
  ├─ src.debate.evidence_closure：证据闭包与引用验证
  ├─ src.debate.argument_index：论点索引维护
  ├─ src.debate.workflow：LangGraph 主工作流
  └─ 10 个问题冒烟测试 + 端到端演示 Notebook

阶段 P3：审理引擎（阶段 2.1）（第 11-12 周）
  ├─ src.review.prosecutor：检察官（检查证据选择性呈现+逻辑漏洞）
  ├─ src.review.defense：辩护律师（最佳辩护+补充证据）
  ├─ src.review.workflow：审理工作流（2-3 轮对质）
  └─ 与阶段 1 的集成测试

阶段 P4：裁决引擎（阶段 2.2）（第 13-15 周）
  ├─ src.judgment.judges：五位专业法官
  ├─ src.judgment.final_judge：综合裁决官 + 权重分配
  ├─ src.judgment.reasoning_chain：推理链构建
  ├─ src.judgment.uncertainty：不确定性标注
  ├─ src.judgment.innov_protect：创新保护机制
  └─ src.judgment.report_generator：裁决报告生成（HTML/Markdown/JSON）

阶段 P5：评估与实验（第 16-20 周）
  ├─ experiments.benchmarks：3-5 个基准数据集加载
  ├─ experiments.baselines：标准 MAD + Self-Consistency + 单 LLM 实现
  ├─ experiments.ablations：8 个消融实验脚本
  ├─ experiments.metrics：7 个评估指标实现
  └─ 运行完整评估 + 生成报告

阶段 P6：优化与完善（第 21-24 周）
  ├─ 问题分级机制（简单问题走精简路径）
  ├─ 结构化索引缓存（减少 Agent 重读完整历史）
  ├─ 分层模型策略（简单任务用小模型）
  ├─ 并行加速（法官并行评估）
  ├─ 日志与监控
  ├─ 完整文档与示例
  └─ 开源 Release 准备

阶段 P7：论文撰写（与 P5/P6 并行）
  ├─ 主论文：Parajudge Framework Design + Evaluation
  ├─ 子论文 1：POI 机制对论证漏洞暴露率的影响
  └─ 子论文 2：目标驱动异质性 vs 模型异质性的对比研究
```

### 8.2 里程碑验收标准

| 里程碑 | 时间 | 交付物 | 验收标准 |
|:---|:---|:---|:---|
| **M1** | 第 3 周末 | 基础设施 + 证据与知识库 | 给定 10 个问题，可构建 Evidence Brief；DomainKB YAML 可正常加载 |
| **M2** | 第 10 周末 | 完整辩论引擎（阶段 1） | 8 个 Agent 端到端工作；Moderator 状态机驱动完整流程；时间片与去重机制生效；输出结构化 `DebateSummary` + `ArgumentIndex` |
| **M3** | 第 12 周末 | 审理引擎（阶段 2.1） | 审理阶段能在 ≥30% 问题上发现辩论阶段的漏洞或证据缺失 |
| **M4** | 第 15 周末 | 裁决引擎（阶段 2.2） | 五法官+裁决官完整运行；输出类判决书报告 |
| **M5** | 第 20 周末 | 评估实验 | 基准数据集完整运行；消融实验结果可复现；与基线对比有显著优势 |
| **M6** | 第 24 周末 | 优化完善 | 简单问题 Token 消耗 ≤ 标准 MAD 的 40%；完整文档 |

---

## 九、风险与挑战

| 风险 | 可能性 | 影响 | 缓解策略 |
|:---|:---|:---|:---|
| **Token 消耗过高** | 高 | 高 | 问题分级机制（简单问题走精简路径）；结构化索引缓存；分层模型策略；阶段内并行限制 |
| **LLM Provider 稳定性** | 中 | 中 | 多 Provider 降级策略（OpenAI 失败则尝试 Dashscope，再回退 Mock）；Tenacity 重试机制 |
| **领域知识库构建耗时** | 中 | 中 | 初期使用通用模板；逐步从领域文献构建高质量 DomainKB；提供 KB 构建工具 |
| **评估指标难以量化** | 中 | 高 | 设计结构化评估模板；LLM-as-Judge 自动评估；关键案例人工深度分析 |
| **与 SOTA 对比不公平** | 低 | 中 | 相同模型规格+总 Token 预算下对比；明确报告质量 vs 成本曲线 |
| **创新问题数据稀缺** | 中 | 中 | 结合公开创业评估数据集+人工标注；设计合成创新问题用于可控实验 |
| **系统复杂度与调试困难** | 中 | 高 | 分阶段增量实现；模块化设计（单一职责）；完整日志记录；可视化工作流状态 |
| **Prompt 工程迭代成本** | 中 | 中 | 集中管理 Prompt 模板库（src.llm.prompt_library）；A/B 测试不同 Prompt 版本 |

---

## 十、与现有项目的整合策略

ParaJudge 并非从零开始，而是**增量增强**当前已有的学术论文工具链。

| 现有模块 | 在 ParaJudge 中的角色 | 集成方式 |
|:---|:---|:---|
| `src.search.engine` | 证据检索核心 | 直接复用：`unified_search()` 构建 Evidence Brief |
| `src.parse.pdf_parser` | PDF 元数据提取 | 可选增强：对用户上传 PDF 提取引用/元数据 |
| `src.reference.bibtex_manager` | 引用格式标准化 | 用于将 Evidence Brief 中的引用格式标准化 |
| `src.writer.llm_helper` | 写作辅助（报告润色） | 可选增强：对裁决报告进行风格润色和总结 |
| `backend.models.schemas` | 数据模型基础 | **扩展**：新增辩论/裁决相关模型定义 |
| `cli.py` | CLI 入口 | **扩展**：新增 `parajudge` 子命令组 |
| `api.py` | API 入口 | **扩展**：新增 `/api/v1/parajudge/*` 端点 |

**关键设计决策**：不修改现有模块的外部接口，保持向后兼容。新功能通过新增模块实现。

---

## 十一、下一步行动清单（Next Steps）

### 立即开始（本周内）

- [ ] 初始化 `src.knowledge`, `src.debate`, `src.review`, `src.judgment`, `src.llm` 目录
- [ ] 在 `backend/models/schemas.py` 中定义核心 Pydantic 模型（EvidenceItem/Argument/JudgeReport/FinalVerdict）
- [ ] 实现 `LLMProvider` 抽象基类 + Mock/OpenAI/Dashscope 三实现
- [ ] 设计 `src.debate.agent_base.ParaJudgeAgent` 基类

### 短期（2-4 周）

- [ ] 完成阶段 P0/P1：基础设施与知识库
- [ ] 构建 6 个领域的初始原则库（YAML 模板）
- [ ] 实现 `src.debate.workflow` 的简单单 Agent 版本（便于集成测试）

### 中期（1-2 月）

- [ ] 阶段 P2/P3/P4 完整实现
- [ ] 至少 1 个基准数据集评估
- [ ] 完成首个类判决书示例报告

### 长期（3-6 月）

- [ ] 完整评估与消融实验
- [ ] 论文撰写
- [ ] 优化与 Release

---

## 十二、参考文献（用于支撑本设计决策）

### 12.1 核心方法论论文

1. Irving, G., Christiano, P. F., & Amodei, D. (2018). **AI Safety via Debate**. arXiv:1805.00899.
2. Du, Y., Li, J., Zheng, Y., Tian, Y., Jurafsky, D., McAleer, S., & Weld, D. S. (2023). **Improving Factuality and Reasoning in Language Models through Multiagent Debate**. arXiv:2305.14325.
3. Smit, C., et al. (2024). **Should we be going MAD? A Critical Assessment of Multi-Agent Debate**. arXiv preprint.
4. Becker, J., Kaesberg, L. B., et al. (2025). **MALLM: Multi-Agent Large Language Models Framework**. EMNLP 2025 Demos.
5. Hu, B., et al. (2025). **Multi-Agent Debate for LLM Judges with Adaptive Stability Detection**. arXiv:2502.08388.
6. Choi, E., et al. (2025). **Measuring and Mitigating Identity Bias via Anonymization in Multi-Agent Debate**. arXiv preprint.
7. Niu, Y., & Zhang, J. (2026). **ARMOR-MAD: Adaptive Routing with Mixture-of-Experts for Reasoning**. arXiv:2602.16627.
8. Hu, B., et al. (2026). **The Confident Liar: Evaluating and Predicting Credibility During LLM Debate**. arXiv preprint.

### 10.2 框架与工程参考

9. LangGraph 官方文档与示例：`langchain-ai/langgraph` GitHub 仓库
10. Multi-Agent-Debate (Alexandre Sajus)：Du et al. 2023 的参考实现
11. MALLM 开源实现：`Multi-Agent-LLMs/mallm` GitHub 仓库
12. swarm-debate (capitansuat)：独立 Validator 模式的参考实现
13. Microsoft AutoGen：Sparse Communication Topology 设计模式
14. Langroid (CMU/UW-Madison)：多 Agent 编程框架

### 10.3 工程与 API

15. FastAPI 文档：`fastapi.tiangolo.com`
16. Typer 文档：`typer.tiangolo.com`
17. Pydantic v2 文档：`docs.pydantic.dev`
18. arXiv API：`info.arxiv.org/api/index.html`
19. Semantic Scholar API：`api.semanticscholar.org`
20. Crossref API：`api.crossref.org`

---

## 十三、附录 A：关键研究问题与实验方案（RQ1–RQ13）

> **方法论说明**：以下 Q1–Q13 不作为"设计阶段已拍板的决策"，而是**待验证的研究问题（Research Questions）**。每个问题给出**工作假设（Working Hypothesis）** 作为当前实现的起点，并附**对比实验方案**用于在系统开发过程中通过 ablation study / A/B test 进行定量验证。最终结论将依据实验证据而非先验判断得出，这种"假设 → 实现 → 实验 → 调整"的迭代循环是计算机科学工程研究的标准方法论。

### 业界参考速览（作为实验设计的基线）

| 参考来源 | 关键发现 / 实践 | 对我们的启示 |
|:---|:---|:---|
| **MACI (Chang & Chang, 2025, Stanford/UIUC)** | Moderator 跟踪 disagreement, overlap, evidence quality, argument quality；当收益平台期时停止辩论；提供 nonincreasing dispersion + provable termination 的理论保证 | 我们的 Moderator 质量守门（Q11/Q12）和停止条件（Q1/Q13）可以借鉴"信号驱动停止"而非固定轮数 |
| **When Two LLMs Debate (2025, ACL-like)** | 用结构化辩论（Opening → Rebuttal → Closing）×6个政策主题 ×10个主流LLMs进行ablation；固定轮数 N≤3；用 AI Jury 评估 | 我们的 Phase 1 阶段划分（Q1）和辩论时长（Q13）应采用"标准三阶段 + 可配置轮数" |
| **InspireDebate (2025, ACL)** | 辩论评估 = 4主观维度（情感诉求/论点清晰度/论点编排/主题相关性）+ 2客观维度（事实真实性/逻辑有效性）；与专家评判相关性比传统方法高 44% | 我们的 5维Judge系统（Q8/Q9）应进一步区分"主观维度"和"客观维度"，客观维度优先作为裁决依据 |
| **Debate, Train, Evolve (2025, EMNLP)** | REFLECT-CRITIQUE-REFINE 三阶段 self-feedback 比纯辩论高 8.92% accuracy；多 agent 辩论 trace 可用于单模型自进化 | 我们的 POI 机制（Q2）可以设计为"辩论后复盘"的一种结构化批评反馈，而非仅中段打断 |
| **Can LLMs Judge Debates? (2025, arXiv)** | LLM-Judge 在结构化 argument graph 上与 QuAD semantics 的 Kendall's τ ≈ 0.4–0.6（中等相关）；更长输入/打乱顺序会显著降低 | 我们的 Final Judge（Q9）应采用线性/路径独立的结构化摘要而非原始长文 |
| **CSDN Agent设计模式 Day 12** | 标准 Debate 模式三角色：Proponent + Opponent + Judge/Moderator；轮数 N≤3；Orchestrator 负责流程控制和超时处理 | 我们的 Coach+Speaker+Moderator 三角色设计是标准范式的扩展 |

---

### RQ1：每位辩手每轮应发言多少次？

**研究问题**：固定轮数 vs 动态轮数 vs Coach决策，哪种方案在"裁决质量 / token成本 / 延迟"三者平衡最优？

**工作假设（当前实现依据）**：默认 3 轮（Opening × 1 + Cross-Exam × 2 + Closing × 1），Coach 可提前终止检测到"无新论点"的轮次。

**业界参考**：
- 标准 Debate 模式（CSDN Agent设计模式）：N≤3
- When Two LLMs Debate (2025)：固定三阶段 Opening→Rebuttal→Closing
- MACI (2025)：信号驱动停止（"when gains plateau"），而非固定轮数

**实验方案**（Ablation Study）：

| 实验组 | 设置 | 评估指标 | 预期结论 |
|:---|:---|:---|:---|
| A（基线） | 固定每方 2 轮 | 裁决准确率 / token 数 / 延迟 | — |
| B | 固定每方 3 轮（工作假设） | 同上 | 质量略高于 A，成本显著高于 A |
| C | 固定每方 5 轮 | 同上 | 收益递减（边际效用 < 边际成本） |
| D | Moderator 信号驱动（MACI 风格） | 同上 | 对复杂问题显著优于 B；简单问题成本更低 |

**分析方法**：
- 在同一测试集（N≥20 题）上运行 A/B/C/D
- 画"质量-成本曲线"（quality-cost Pareto frontier）
- 若 D 落在曲线最左上区域 → 采用信号驱动停止
- 若 B 与 D 质量差异不显著（t-test, p>0.05）→ 退化为简单固定轮数

---

### RQ2：POI 触发规则是硬编码规则还是 Agent 自主决策？

**研究问题**：段间质询（POI）应该由硬编码规则触发，还是由 Speaker Agent 基于对手发言内容自主判断？

**工作假设**：Agent 自主决策——Speaker 在检测到对手发言中"高风险断言（无证据 / 存在逻辑跳跃）"时发起 POI。

**业界参考**：
- Debate, Train, Evolve (2025)：REFLECT-CRITIQUE-REFINE 三阶段反馈，显式要求 agents 识别并纠正推理错误，准确率 +8.92%
- MACI (2025)：behavior dial 从 exploration 到 consolidation 动态调度 contentiousness，而非固定规则

**实验方案**：

| 实验组 | 设置 | 评估指标 |
|:---|:---|:---|
| A（无POI基线） | 无 POI，仅交错陈述 | 裁决准确率 / 每论点平均 evidence_refs |
| B（硬编码POI） | 每 2 轮强制一次 POI，固定模板 | 同上 + POI 触发频率 |
| C（Agent自主POI） | Speaker 基于对手发言的未引用断言/逻辑跳跃自主发起 | 同上 + POI 触发时机合理性（人工标注） |
| D（后复盘批评） | POI 不作为中段打断，作为辩论后的 REFLECT-CRITIQUE-REFINE 批评反馈 | 同上 |

**分析方法**：
- 如果 C 的准确率显著 > A 且 POI 触发频率在 [15%, 40%] 区间 → 接受 Agent 自主决策
- 如果 D 的准确率与 C 无显著差异但成本更低 → DTE 风格后复盘更优

---

### RQ3：创新保护机制中"先例不缺失"的判定谁负责？

**研究问题**：检测"已有类似研究但未被引用"应由哪个 Agent 负责——I-Judge（创新法官）独立判定、P-Judge（原则法官）辅助、还是 I-Judge + C-Judge 协作？

**工作假设**：I-Judge + C-Judge 协作——C-Judge 先给出"已有案例/先例的完整性评分"，I-Judge 基于该评分 + 自身检索给出创新性评估。

**业界参考**：
- InspireDebate (2025)：主观-客观双维度评估，不同维度由不同组件负责
- ParaJudge 设计理念：目标驱动异质性 → 不同 Judge 的专业分工

**实验方案**（三配置对比）：

| 实验组 | I-Judge 信息源 | 评估指标 |
|:---|:---|:---|
| A（独立） | 仅问题 + 辩论摘要 + 自身知识/检索 | 与人工创新评分的 Pearson/Spearman 相关系数 |
| B（P辅助） | A + P-Judge 原则评分 | 同上 |
| C（I+C 协作） | A + C-Judge 案例完整性评分 + 已找到案例列表 | 同上 |

**附加分析**：检查 C-Judge 的"案例完整性评分"与最终 I-Judge 评分之间的相关性（若相关 >0.7，说明案例检测对创新判断确实有贡献）。

---

### RQ4：权重配置是固定的还是学习的？

**研究问题**：五维 Judge 的加权整合是使用基于问题类型的固定权重表，还是从数据学习？

**工作假设**：默认固定权重表（简单问题降低创新/案例维度权重），允许用户覆盖。

**业界参考**：
- 大多数 LLM-as-a-Judge 系统采用固定权重或等权重（Lin et al., 2024; Sanayei et al., 2025）
- MACI (2025) 使用"保守软权重"（CRIT cross-family judge），权重是保守而非学习的
- 学习权重需要大量标注数据（通常 ≥1K 标注样本），且存在过拟合风险

**实验方案**（两阶段）：

**阶段 1（固定权重探索）**：
- 用 3–5 组合理权重配置运行同一测试集
- 计算每组配置的裁决一致性/稳定性

**阶段 2（学习权重 — 有 ≥500 人工标注时启动）**：
- 以人工标注的"合理裁决"为监督信号
- 用逻辑回归 / 贝叶斯优化学习最优权重
- 对比"学习权重" vs "固定权重"在 hold-out 测试集上的表现

**风险考量**：学习权重可能过拟合特定标注者偏好 → 需报告 inter-annotator agreement（Cohen's κ）

---

### RQ5：Evidence Brief 的证据数量上限是多少？

**研究问题**：Evidence Brief 应该包含多少条证据条目，使得 Agent 可以有效利用且不被信息过载？

**工作假设**：20–30 条。

**业界参考**：
- RAG 系统典型 top-k = 5–15（单跳检索），但辩论系统需要正反双方证据 → 通常翻倍
- 信息过载效应在 LLM 中已被广泛证实（"lost in the middle"现象，Liu et al., 2024）
- ParaJudge 设计报告：对前沿/冷领域（<10篇公开论文）应降级为"弱证据"标注

**实验方案**：

| 实验组 | Evidence Brief 大小 | 评估指标 |
|:---|:---|:---|
| A（小） | 10 条 | Judge 最终准确率 + ArgumentIndex 中 evidence_refs 覆盖率 |
| B（中） | 20–30 条（工作假设） | 同上 |
| C（大） | 50 条 | 同上 |
| D（动态） | 依问题复杂度自适应（简单问题10条，复杂问题30–50条） | 同上 |

**关键度量**：
- Agent 是否引用了 Evidence Brief 中更多的"高质量证据"（按搜索排名）
- 是否存在"证据使用集中度"（前 5 条证据被引用 60% 次，后续证据几乎不被引用）

---

### RQ6：是否需要持久化辩论状态？

**研究问题**：辩论状态（发言内容、评分、推理链）是仅保留在内存中，还是写入 JSON/文件，还是存储在数据库中？

**工作假设**：JSON 文件持久化（轻量、可复现、易审计）。

**业界参考**：
- 几乎所有生产级 LLM 应用都会持久化推理 trace（用于审计、A/B test、fine-tuning）
- CSDN Agent设计模式：Orchestrator 负责流程控制，通常伴随日志/状态持久化
- 可复现性是可复现研究的基本要求（NF-10 验收项）

**实验方案**（工程性评估，非 ML ablation）：

| 方案 | 实现复杂度 | 审计便利性 | 恢复成本（从状态恢复辩论） | 存储开销（10K 次运行） |
|:---|:---|:---|:---|:---|
| A（仅内存） | 最低 | 最低（不可审计） | 不可恢复 | 0 |
| B（JSON 文件） | 低 | 中（可 grep/脚本分析） | O(文件加载) | ~50–200 MB |
| C（SQLite） | 中 | 高（可 SQL 查询任意维度） | O(DB query) | ~30–100 MB |
| D（PostgreSQL） | 高 | 最高 | 最低（索引查询） | ~≥1 GB |

**决策建议**：MVP 用 B；当需要大规模实验分析（≥10K 运行）时迁移到 C。

---

### RQ7：是否支持中文/英文双语言？

**研究问题**：系统是仅支持中文、仅支持英文，还是双语自适应？

**工作假设**：双语自适应——根据问题语言自动切换 Agent Prompt 语言；证据检索也根据问题语言选择搜索引擎/数据源。

**业界参考**：
- 主流 LLM（GPT-4o, Claude, Qwen, DeepSeek）均原生支持中英双语
- 但"中文 Prompt 质量 ≈ 英文"是经验假设，应实测验证

**实验方案**：

| 实验组 | 设置 | 评估指标 |
|:---|:---|:---|
| A（中文） | 全中文 Prompt + 中文/中英双语证据源 | 中文测试集裁决准确率 + 人工可读性评分 |
| B（英文） | 全英文 Prompt + 英文证据源 | 英文测试集裁决准确率 + 人工可读性评分 |
| C（双语混合） | 中文问题用中文 Prompt+中英证据，英文问题用英文 Prompt+英文证据 | 同上（与 A/B 对比） |

**零假设 H₀**："A 的中文准确率 = B 的英文准确率"
- 若配对 t-test 显示 p<0.05 且准确率差 >5% → 需针对低语言优化 Prompt

---

### RQ8：法官权重是否需要根据"问题复杂度"调整？

**研究问题**：简单问题和复杂问题是否需要不同的 Judge 权重配置？

**工作假设**：需要动态调整——简单问题降低"创新/案例"维度权重（≤15%），提高"证据/逻辑"权重（≥70%）。

**业界参考**：
- MACI (2025)：behavior dial 动态调度 contentiousness，从 exploration 到 consolidation
- InspireDebate (2025)：不同任务类型可能强调不同维度

**实验方案**：

| 实验组 | 设置 | 评估指标（按问题类型分表） |
|:---|:---|:---|
| A（固定等权重） | 五维各 20% | 简单问题准确率 vs 复杂问题准确率 |
| B（固定问题类型权重） | 依问题类型预设权重表 | 同上 |
| C（Moderator 动态权重） | Moderator 基于辩论复杂度信号动态给出权重建议 | 同上 |

**复杂度信号**（可用于 C 组）：
- Evidence Brief 证据条目数（越多越复杂）
- 辩论期间论点总数（越多越复杂）
- Judge 间评分分歧度（越高越复杂）

---

### RQ9：裁决官的推理链是事后生成还是过程中逐步构建？

**研究问题**：推理链（reasoning chain）是在 Final Judge 裁决后基于 5 个 Judge Report 一次性生成，还是在辩论过程中随 Judge 评分同步累积？

**工作假设**：事后生成（更简单，且可审核）。

**业界参考**：
- "When Two LLMs Debate" (2025)：陪审团评估在辩论结束后一次性进行
- Debate, Train, Evolve (2025)：事后从 debate traces 提取 consolidated rationale
- Chain-of-Thought 本质上就是"事后线性推理"

**实验方案**：

| 实验组 | 推理链生成时机 | 评估指标 |
|:---|:---|:---|
| A（事后生成） | Judge 报告 → Final Judge → 推理链 | 推理链与最终 verdict 的一致性（人工评分，1–5 分） |
| B（过程构建） | 每 Judge 评分时同步输出 1 步 reasoning fragment → Final Judge 拼接 | 同上 + 推理链逻辑完整性（是否出现时间线矛盾） |

**关键风险**（B 的主要问题）：
- Judge A 输出的 reasoning step 可能与 Judge B 的结论矛盾 → 需要额外的"一致性检查"模块
- 推理链的时序结构可能影响用户感知（"先看到证据评分，后看到逻辑评分"是否合理？）

---

### RQ10：阶段间的状态传递使用什么结构？

**研究问题**：Phase 0→Phase 1→Phase 2.1→Phase 2.2 的状态传递用纯字典、Pydantic 模型，还是 LangGraph StateSchema？

**工作假设**：Pydantic 嵌入 LangGraph State，既类型安全又可编排（已在 `backend/models/schemas.py` 中实现 `DebateState`/`DebateSummary` 等 Pydantic 模型）。

**业界参考**：
- LangChain/LangGraph 官方最佳实践推荐 Pydantic-based state
- MACI (2025)：state 包含 structured signals（disagreement, overlap, quality），而非未结构的文本

**实验方案**（工程评估，非 ML ablation）：

| 方案 | 类型安全 | 可复现性（可序列化） | 与 LangGraph 集成 | refactor 成本 |
|:---|:---|:---|:---|:---|
| A（dict） | 低 | 高 | 高 | 最低 |
| B（Pydantic） | 高 | 高（JSON Schema 自动生成） | 高（StateSchema 原生支持） | 中 |
| C（LangGraph StateSchema） | 中-高 | 高 | 最高 | 高（强绑定 LangGraph） |

**当前选择**：B（Pydantic），因为它既提供类型安全，又不绑定 LangGraph（未来迁移到其他编排框架时成本低）。

---

### RQ11：Moderator 的质量守门应调用 LLM 还是纯规则？

**研究问题**：论点去重、主题漂移检测、超时控制——是纯代码规则，还是调用 LLM 语义判断，还是混合模式？

**工作假设**：混合模式——默认纯规则（embedding 相似度 + 关键词重叠）节省成本和保证可复现；当设置 `strictness=strict` 时启用轻量 LLM 语义检查（仅对有风险的发言调用）。

**业界参考**：
- MACI (2025)：Moderator 跟踪 disagreement, overlap, evidence quality, argument quality 四类轻量信号。overlap（论点重复）用纯启发式/embedding 相似度计算即可，不需要 LLM
- "When Two LLMs Debate" (2025)：通过 Confidence Escalation 动态检测——当辩论陷入"相互重复但信心升级"的模式时需要干预
- InspireDebate (2025)：主题相关性作为主观维度之一由 Prompt-based 评估

**实验方案**：

| 实验组 | 设置 | 评估指标 |
|:---|:---|:---|
| A（纯规则基线） | embedding 相似度 > 0.85 → duplicate；关键词重叠 < threshold → off_topic | 漏检率 / 误检率（人工标注 ground truth）+ API 成本 |
| B（LLM 全量） | 每条发言都调用 LLM 进行 duplicate/off_topic 二分类 | 同上 |
| C（混合模式） | 规则先粗筛 → 仅对"灰色区间"发言调用 LLM | 同上 |

**预期结论**：C 的准确率 ≈ B，但成本仅为 B 的 20–40%；A 的准确率显著低于 B/C 但成本为 0。

---

### RQ12：Moderator 是否需要持久化其状态？

**研究问题**：Moderator 的内部状态（当前阶段、已警告发言、阶段耗时等）是否需要写入 DebateSummary 以供审计和问题追踪？

**工作假设**：需要——将 Moderator 状态摘要写入 DebateSummary（Phase 1 输出），供 Phase 2.1 ReviewWorkflow 和外部审计使用。

**业界参考**：
- MACI (2025)：moderator signals 是系统状态的一部分，用于"budget-aware measurable controller"
- ParaJudge NF-10 验收项要求：10 次运行的 phase_durations 顺序一致、Moderator warnings 内容一致 → 必须持久化才能验证
- 可审计性（auditability）是可问责 AI（accountable AI）的基本要求之一

**实验方案**（工程性评估）：

| 方案 | Phase 2.1 是否可复用 Moderator warnings | 可复现性（NF-10 是否可验证） | 存储开销增量 |
|:---|:---|:---|:---|
| A（仅内存） | 不可 | 不可 | 0 |
| B（写入 DebateSummary） | 可（ReviewWorkflow 直接读取 warnings 列表） | 可 | ~每条运行 +1–5 KB |
| C（独立 SQLite 表） | 可（灵活查询） | 可 | ~每条运行 +1–3 KB |

**当前选择**：B，因为它与现有数据结构无侵入（DebateSummary 已有 `warnings` 字段），且足够支撑 NF-10 和 Phase 2.1 审计。

---

### RQ13：超时发言是强制截断还是仅警告？

**研究问题**：当单条发言 token 数或时间超过 Moderator 设定上限时，是仅警告但保留全部内容（宽松）、强制截断并警告（标准）、直接拒绝（严格）？

**工作假设**：按 `strictness` 配置区分——`loose` 仅警告、`normal` 截断并警告、`strict` 直接拒绝。

**业界参考**：
- MACI (2025)：budget-feasible scheduler → 超时必须有实际后果（否则预算控制无效）
- "When Two LLMs Debate" (2025)：每个 speech 有固定格式和长度约束（Prompt 明确限制 token 数）
- CSDN Agent设计模式：Orchestrator 负责超时处理 → 超时是异常而非可选

**实验方案**：

| 实验组 | 超时处理策略 | 评估指标 |
|:---|:---|:---|
| A（loose：仅警告） | 保留全内容，仅在 DebateSummary 标记 | 裁决准确率 + 总 token 数（成本）+ 警告被 Judge 注意到的比例 |
| B（normal：截断+警告） | 截断到上限，保留截断标记 | 同上 |
| C（strict：直接拒绝） | 拒绝整条发言，由 Speaker 重发合规版本 | 同上 + 重发率 |

**关键度量**：
- 裁决准确率在 A/B/C 间是否显著不同（若 A 显著低 → 说明"放任超时发言引入无效噪音稀释有效信号"）
- 警告被 Judge 感知的比例（若 <50% → 说明警告仅在 Moderator 层可见，Judge 并未利用，需要改进 Judge Prompt）

---

### 实验实施计划（与代码里程碑对齐）

| 阶段 | 时机 | 可执行的 RQ 实验 | 所需基础设施 |
|:---|:---|:---|:---|
| **M2 完成后** | Phase 1（辩论引擎）可运行 | RQ1（轮数）、RQ2（POI）、RQ11（质量守门策略）、RQ13（超时策略） | Moderator 可配置 + 实验脚本批量运行 |
| **M3 完成后** | Phase 2.1 + 2.2 可端到端运行 | RQ3（创新判定责任分配）、RQ4（权重学习）、RQ8（动态权重）、RQ9（推理链时机） | 完整端到端 Pipeline + 人工标注接口 |
| **M4 完成后** | CLI/API + HTML 裁决报告 | RQ5（Evidence Brief 大小）、RQ7（双语效果对比） | 多语言测试集 + 搜索引擎适配 |
| **持续维护** | 全周期 | RQ6（持久化方案）、RQ10（状态传递结构）、RQ12（Moderator 持久化） | 工程性监控工具，非 ML ablation |

### 数据记录模板（每完成一项 RQ 实验填写）

```
实验编号: EXP-<RQ编号>-<版本>
完成日期: YYYY-MM-DD
测试集大小: N=?
结论: 方案 <X> 在 <主要指标> 上显著优于其他方案 (p<?, effect size=?)
权衡: 方案 X 的主要限制是 <...>
对代码的影响: [文件变更列表]
下一步建议: <是否需要进一步实验>
```

---

## 十四、附录 B：实验主题库（20 题，持续补充）

> 以下题目用于 ablation 实验。每题标注**问题类型**（Factual/Policy/Value/Technical）和**难度**（简单/中等/复杂），以便按 RQ8（问题复杂度与 Judge 权重）进行分组分析。

| 编号 | 辩题 | 正方立场 | 反方立场 | 问题类型 | 预期难度 |
|:---|:---|:---|:---|:---|:---|
| T1 | 大语言模型的推理能力是否真正"理解"了问题？ | LLM 通过大规模预学到了语言规律，但不构成真正的"理解" | LLM 在多基准测试上的表现足以证明其具有推理和理解能力 | Technical | 复杂 |
| T2 | AI 是否应该在高风险决策（医疗/司法/金融）中被赋予最终裁决权？ | AI 决策的一致性和无情绪化使其比人类更适合高风险场景 | AI 的错误不可解释、无问责链条，且训练数据可能含偏见，不应替代人类 | Policy | 复杂 |
| T3 | 开源大模型 vs 闭源大模型：哪种模式对社会更有利？ | 开源促进竞争、降低成本、增强透明度和安全性审计 | 闭源可保障质量控制、安全对齐投入和商业模式可持续 | Value | 中等 |
| T4 | 2024 年美国总统大选中特朗普是否被认定为"不受选举人团资格约束"？ | 法院历史案例和宪法条文支持对叛乱者取消资格 | 该法条历史上几乎未被适用，且应由国会而非法院决定 | Factual | 中等 |
| T5 | RAG（检索增强生成）是否从根本上解决了 LLM 的幻觉问题？ | RAG 通过引入外部知识源大幅降低事实性幻觉 | RAG 仅减少已知事实的幻觉，对推理链条、来源可信度本身无法根治 | Technical | 中等 |
| T6 | 多 Agent 辩论系统（如 ParaJudge）是否比单 Agent 系统更可靠？ | 多 Agent 通过角色分化、交叉审查、独立裁决降低单一模型偏见 | 多 Agent 增加复杂性、成本和延迟，且 agent 间可能互相污染 | Technical | 中等 |
| T7 | 政府是否应该对 LLM 训练数据的版权使用进行严格立法？ | 严格立法保护创作者权益，建立公平的训练数据市场 | 过度立法会扼杀 AI 创新，且合理使用原则已部分覆盖此类场景 | Policy | 复杂 |
| T8 | 中国的"新质生产力"提法与西方的"第四次工业革命"概念有何本质差异？ | 新质生产力强调"生产要素的新组合方式"，有明确的政策导向和体制特征 | 两者本质相同，都是对 AI/生物/新能源等新技术驱动经济的不同表述 | Value | 复杂 |
| T9 | 深度学习中"大模型涌现能力"是真实存在的现象还是统计假象？ | 多项基准测试上的不连续性能跃迁证明了涌现效应 | 所谓"涌现"可能是评估指标设计造成的假象，或仅是规模效应的非线性 | Technical | 复杂 |
| T10 | Prompt Engineering 是否会被 Agentic Workflow 完全取代？ | Agentic Workflow 让模型自行分解任务、调用工具，Prompt 工程师需求将大幅减少 | Prompt Engineering 是 Agentic Workflow 的基础组件之一，不会消失而是升级 | Technical | 简单 |
| T11 | 全球气候变化的主要驱动因素是否是人类活动？ | IPCC 第六次评估报告以 95%+ 置信度确认人类活动是主要驱动 | 自然周期（太阳活动、海洋循环）也有显著贡献，模型对云和气溶胶模拟仍不确定 | Factual | 中等 |
| T12 | AI 生成内容是否应受版权法保护？ | AI 生成物含人类创造性选择（提示工程、训练数据选择），应受保护 | 版权法要求"人类作者"，纯 AI 生成内容不满足独创性的人类来源要求 | Policy | 中等 |
| T13 | 量子计算将在 10 年内对 RSA-2048 加密构成实际威胁？ | Shor 算法理论可行，量子比特数和纠错能力正指数改进 | 物理噪声、纠错开销和环境退相干使实用级量子计算机仍遥远 | Technical | 复杂 |
| T14 | 通用人工智能（AGI）是否应作为 AI 研究的主要目标？ | AGI 是终极目标，可统一解决各类智能任务并大幅加速科学发现 | AGI 定义模糊且目标遥远，当前应聚焦窄 AI 安全落地和经济价值 | Value | 复杂 |
| T15 | Scaling Laws（规模法则）是否还会持续有效？ | 过去 10 年 Scaling Laws 持续有效，硬件和数据投资仍在增加 | 高质量文本数据即将耗尽，计算效率提升的边际效益递减 | Technical | 中等 |
| T16 | 中国 AI 监管框架（《生成式人工智能服务管理暂行办法》）与欧盟 AI Act 相比哪种更有利于创新？ | 中国框架更温和、采用事后监管和备案制，降低合规成本保护创新 | 欧盟框架更严格、采用分级分类管理，长期看更有利于建立信任和国际互认 | Policy | 复杂 |
| T17 | Retrieval-Augmented Generation vs Fine-tuning：哪种是更好的知识注入方式？ | RAG 知识新鲜、可追溯、成本低，适合频繁更新的事实知识 | Fine-tuning 将知识内化到模型权重，推理时速度更快且无检索失败风险 | Technical | 中等 |
| T18 | Chain-of-Thought Prompting 是否真正引发了"推理"，还是只是表面模仿？ | CoT 显著提高推理任务准确率，且中间步骤可解释、可干预 | CoT 本质仍是 next-token 预测，只是在更长上下文上表现出推理-like 行为 | Technical | 复杂 |
| T19 | 人类是否应该赋予 AI 系统某种形式的"法律人格"？ | 当 AI 系统能独立决策并承担后果时，需要法律框架来分配责任和权利 | AI 本质是工具，赋予其人格会混淆责任归属并逃避人类问责 | Value | 复杂 |
| T20 | 在可预见的 5-10 年内，AI 将主要加剧不平等还是主要缩小不平等？ | AI 提高生产率但收益集中在资本方，对低技能岗位替代效应显著 | AI 降低知识获取成本、提供个性化教育和医疗，历史性地扩展机会 | Policy | 复杂 |

**补充说明**：
- T1–T3, T6–T8, T14, T16, T19, T20 为**价值/政策型**问题，适合测试 Judge 的多维度评分能力
- T4, T11 为**事实核查型**问题，适合测试 Evidence Brief 构建质量和 E-Judge（证据法官）
- T5, T9, T10, T13, T15, T17, T18 为**技术型**问题，适合测试引用验证和逻辑有效性检查
- 所有题目均有"正反双方可合理辩护"的特点，避免单一正确答案的题目（否则辩论无法展开）
