# ParaJudge：多智能体辩论系统 — 学术论文、案例分析、需求与技术栈规划报告

> **项目代号**：ParaJudge
> **版本**：v0.1.0
> **日期**：2026 年 6 月
> **适用范围**：高风险决策场景（数学推理、工程权衡、医疗辅助、法律分析、事实核查/热点研判）

---

## 一、核心思路回顾

在单一 LLM 或简单多智能体辩论（Standard MAD）中，存在三大核心问题：

1. **同质化推理偏差**：同一模型的多个实例在推理模式上高度重叠，"同一个脑子在重复自己"，难以产生真正的批评性视角（Du et al., 2023; Choi et al., 2025）
2. **论证质量缺乏制衡**：LLM 倾向于**阿谀奉承（sycophancy）**，当一个模型自信地表述错误事实时，其他模型更倾向于赞同而非质疑（Suat, 2025 博客; Hu et al., 2026）
3. **裁决过程黑箱化**：投票或"评委打分"的裁决无法追溯，对创新问题天然保守（Hu et al., 2026; Becker et al., 2025 MALLM）

**ParaJudge 的核心主张**：

> 将辩论过程分解为"证据准备 → 结构化辩论 → 独立审理 → 多维度专业化裁决"四个阶段。
> 其中**目标驱动异质性**（Objective-Driven Heterogeneity）是产生高质量推理的关键机制——各 Agent 因追求不同的目标（"构建框架" vs "找漏洞" vs "核验证据"）而产生真正的差异，而非依赖 Prompt 模板或不同模型。

---

## 二、核心学术论文与分析

### 2.1 里程碑论文（按时间排序）

| 序号 | 论文标题 | 作者/机构 | 年份 | 核心贡献 | 与本项目的关联 |
|:---|:---|:---|:---|:---|:---|
| 1 | **AI Safety via Debate** | Irving, Christiano, Amodei (OpenAI) | 2018 | 奠基性论文，提出辩论范式作为对齐机制 | 项目的方法论源头。确立 "多个 Agent 辩论 → 裁决" 基本范式 |
| 2 | **Improving Factuality and Reasoning through Multi-Agent Debate** | Du, Li, Zheng, Tian, Jurafsky, McAleer, Weld (MIT, Stanford) | 2023 | 定义现代 MAD 框架，在 GSM8K/MMLU 等基准上显著优于单模型；确立 "辩论 → 投票裁决" 模式 | 本项目的基线系统（Standard MAD）。我们在此基础上加入审理阶段、创新保护和多维度裁决 |
| 3 | **Should we be going MAD?** | Smit et al. | 2024 | 批判性评估 MAD：辩论并不必然优于自一致性（self-consistency）；指出机制设计对质量的关键影响 | 为本项目提供重要约束：必须有明确的机制设计证据（例如 POI 交互、证据闭包）来证明改进的必要性，不能假设辩论自动带来质量提升 |
| 4 | **MALLM: Multi-Agent Large Language Models Framework** | Becker, Kaesberg, Bauer, Wahle, Ruas, Gipp (University of Göttingen) | 2025 | 提出模块化 MAD 框架：支持 144+ 配置组合（Agent 人格 × 回应生成器 × 讨论范式 × 决策协议）；集成评估管线 | **本项目的重要参考**。我们将借鉴其"配置驱动"和"评估管线"设计思路，但在辩论范式的结构化程度上超越（议会制辩论），并增加审理阶段 |
| 5 | **Multi-Agent Debate for LLM Judges with Adaptive Stability Detection** | Hu et al. | 2025 | 引入稳定性检测，检测辩论中的振荡与过早收敛；提出自适应终止条件 | 为我们提供工程提示：需要监控辩论状态，防止无效循环。可借鉴其稳定性指标用于辩论状态监控 |
| 6 | **Measuring and Mitigating Identity Bias via Anonymization in MAD** | Choi et al. | 2025 | 指出身份偏见问题：Agent 名称/角色标签会影响裁决，提出匿名化缓解方案 | 为角色设计提供约束。我们将考虑 "匿名辩论"——在辩手发言时仅标记"正方 N 号"而非"专业律师"等标签，以减少标签偏见 |
| 7 | **ARMOR-MAD: Adaptive Routing with Mixture-of-Experts for Reasoning** | Niu & Zhang | 2026 | 引入异质 Agent（不同专家）+ 自适应路由，在数学推理上达到 SOTA | 我们在"法官专业化"上使用类似思路——不同法官负责不同维度评估，而非让一个全能 Agent 做所有事情 |
| 8 | **The Confident Liar: Evaluating and Predicting Credibility During LLM Debate** | Hu et al. | 2026 | 分析辩论中的置信度与正确性的脱钩：LLM 可在错误答案上表现出高置信度 | 直接启发我们的"证据闭包"和"审理阶段"设计——必须有独立于辩论主体的机制来校验引用和主张 |

### 2.2 补充关键论文（应用领域）

| 领域 | 论文 | 核心发现 |
|:---|:---|:---|
| **医疗** | Dialectic-Med（2025） | 多 Agent 辩论在医疗报告生成中优于单一 LLM |
| **法律** | SAMVAD (2025), AgentsCourt (2025) | 法律问答中，辩论式 Agent 可提升法条引用正确率 |
| **事实核查** | PolitiFact/AVEITEC 系列工作 | "事实核查员 Agent"需要独立检索和核验能力 |
| **一般推理** | "Hear Both Sides" 系列（2026） | 多样性意识消息保留机制显著提升辩论质量 |

---

## 三、开源实现案例分析

### 3.1 主要开源项目

| 项目 | 开发者/机构 | Stars | 核心设计 | 与 ParaJudge 的关系 |
|:---|:---|:---|:---|:---|
| **MALLM** | Göttingen University | 中等 | 4 组件模块化：Agent Persona × Response Generator × Discussion Paradigm × Decision Protocol；支持 144+ 配置；内置评估管线 | **主要参考**。我们将学习其模块化设计，但在辩论范式上增加结构化程度（POI、证据闭包），并加入审理阶段 |
| **Multi-Agent-Debate** | Alexandre Sajus | ~数百 | Du et al. 2023 的官方实现；经典 "正方-反方-投票" 模式 | **对比基线**。ParaJudge 的阶段 1 类似此模式，但更复杂（增加教练、POI） |
| **DebateNet** | jinhongzou (开源) | 较小 | 正方/反方辩论 + 主持人；DSPy 框架 | **参考价值**。简单但有效的实现；我们在其基础上增加结构化程度（POI + 证据闭包） |
| **swarm-debate** | capitansuat (开源) | 较小 | 引入**独立事实核查员（Validator Agent）**概念，在每轮辩论后对具体引用进行校验；Validator 不参与辩论，只做事实检查 | **直接启发**。这与我们的"审理阶段检察官"和"证据审查官法官"角色高度契合 |
| **CAMEL** | KAUST (NeurIPS 2023) | 30k+ | 角色驱动的合作 Agent 框架；AI 助手 ↔ AI 用户；任务指定器生成详细步骤 | **参考价值**。其角色工程方法学可借鉴；但 CAMEL 侧重合作而非辩论 |
| **Langroid** | CMU/UW-Madison | 3.2k | 基于 Agent 的通用编程框架；支持工具调用与向量记忆 | **工程框架参考**。可作为生产级 Agent 框架；但 ParaJudge 将基于 LangGraph 实现以保持与 LangChain 生态的深度集成 |
| **AutoGen** | Microsoft | - | Agent 设计模式；MathSolver 实现采用稀疏通信拓扑 + Solver Agents + Aggregator Agent | **设计模式参考**。其 Solver-Aggregator 模式启发我们的"辩手-裁决官"模式 |

### 3.2 关键实现模式对比

| 设计维度 | MALLM | DebateNet | swarm-debate | ParaJudge (目标) |
|:---|:---|:---|:---|:---|
| **角色异质性来源** | 人格/专家标签 (Persona + Expert) | 简单正反标签 | 角色分工（Analyst/Devil/Validator） | **目标函数差异**（核心创新） |
| **讨论范式** | Memory/Relay/Debate/Report 可选 | 简单轮流独白 | 结构化轮流发言 | **议会制 POI 质询** |
| **裁决机制** | 多数/一致/投票/单一法官 可选 | 主持人+裁判 | 综合者 Agent | **五维专业化法官并行评估** |
| **证据校验** | 无特殊设计 | 无特殊设计 | **独立 Validator 实时事实核查** | **证据闭包 + 强制引用验证** |
| **审理阶段** | 无 | 无 | **隐含在 Validator 中** | **独立检察官-辩护律师审理** |
| **创新保护** | 无 | 无 | 无 | **暂定结论保护 + 假设标注** |
| **可追溯性** | 输出最终答案与对话历史 | 简单结论 | 事实检查标注 | **类判决书推理链**（每条结论标注证据/原则/案例来源） |

### 3.3 ParaJudge 的独特定位

综合分析，**ParaJudge 在以下方面区别于现有实现**：

1. **目标驱动异质性**：Agent 的差异来自其目标函数（"构建框架" vs "找漏洞" vs "查证据"），而非简单的人格标签或模型差异
2. **三阶段架构**：辩论→审理→裁决明确分离；现有框架均无独立审理阶段
3. **POI 质询机制**：类似真实议会辩论的中断式回应
4. **创新保护机制**：专门设计用于创新/可行性问题的非保守评估
5. **类判决书输出**：每条裁决结论标注具体证据/原则/案例来源

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



## 五、技术栈规划

### 5.1 完整技术栈图

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

### 5.2 核心依赖与版本

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

### 5.3 项目目录结构（目标设计）

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

### 5.4 模块划分与职责边界

| 模块 | 主要职责 | 核心类/函数 | 对外接口 |
|:---|:---|:---|:---|
| **src.knowledge** | 证据构建、知识库加载、问题识别 | `EvidenceBriefBuilder`, `DomainKBLoader`, `ProblemClassifier` | 提供统一的 `build_evidence_brief(query)` |
| **src.debate** | 教练-辩手辩论、POI、论点索引、**Moderator 流程控制** | `Coach`, `Speaker`, `Moderator`, `POIEngine`, `EvidenceClosure`, `DebateWorkflow`, `ArgumentIndex` | `DebateWorkflow.run(problem, evidence_brief)` |
| **src.review** | 检察官-辩护律师审理 | `Prosecutor`, `DefenseAttorney`, `ReviewWorkflow` | `ReviewWorkflow.run(debate_state, evidence_brief)` |
| **src.judgment** | 五维法官裁决、推理链生成、报告渲染 | `EvidenceJudge`/`LogicJudge`/`PrincipleJudge`/`CaseJudge`/`InnovationJudge`, `FinalJudge`, `ReasoningChainBuilder`, `ReportGenerator` | `JudgmentWorkflow.run(review_state, evidence_brief, domain_kb, problem_type)` |
| **src.llm** | LLM Provider 封装、Prompt 管理、Token 统计 | `LLMProvider`, `PromptLibrary`, `TokenCounter` | `generate(role, prompt, **kwargs)` |
| **backend.models** | Pydantic 数据模型定义 | 所有 `*State`, `*Report`, `*Verdict` 模型 | 数据结构定义 |

---

## 六、实施路线图与里程碑

### 6.1 分阶段实施时间表

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

### 6.2 里程碑验收标准

| 里程碑 | 时间 | 交付物 | 验收标准 |
|:---|:---|:---|:---|
| **M1** | 第 3 周末 | 基础设施 + 证据与知识库 | 给定 10 个问题，可构建 Evidence Brief；DomainKB YAML 可正常加载 |
| **M2** | 第 10 周末 | 完整辩论引擎（阶段 1） | 8 个 Agent 端到端工作；Moderator 状态机驱动完整流程；时间片与去重机制生效；输出结构化 `DebateSummary` + `ArgumentIndex` |
| **M3** | 第 12 周末 | 审理引擎（阶段 2.1） | 审理阶段能在 ≥30% 问题上发现辩论阶段的漏洞或证据缺失 |
| **M4** | 第 15 周末 | 裁决引擎（阶段 2.2） | 五法官+裁决官完整运行；输出类判决书报告 |
| **M5** | 第 20 周末 | 评估实验 | 基准数据集完整运行；消融实验结果可复现；与基线对比有显著优势 |
| **M6** | 第 24 周末 | 优化完善 | 简单问题 Token 消耗 ≤ 标准 MAD 的 40%；完整文档 |

---

## 七、风险与挑战

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

## 八、与现有项目的整合策略

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

## 九、下一步行动清单（Next Steps）

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

## 十、参考文献（用于支撑本设计决策）

### 10.1 核心方法论论文

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

## 十一、附录 A：关键研究问题与实验方案（RQ1–RQ13）

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

## 十二、附录 B：实验主题库（20 题，持续补充）

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
