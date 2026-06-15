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

参见 [PROJECT_PLAN.md#数据结构定义](file:///workspace/PROJECT_PLAN.md)中的第 7 节。关键 Pydantic 模型：

- `EvidenceItem` / `EvidenceBrief`：证据条目与证据包
- `PrincipleItem` / `CaseItem` / `DomainKB`：原则库与案例库
- `Argument` / `ArgumentIndex`：论点与论点索引
- `POIInteraction`：POI 交互记录
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
│   └─── USAGE.md                   # 使用指南
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
| **src.debate** | 教练-辩手辩论、POI、论点索引 | `Coach`, `Speaker`, `POIEngine`, `EvidenceClosure`, `DebateWorkflow` | `DebateWorkflow.run(problem, evidence_brief)` |
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
| **M2** | 第 10 周末 | 完整辩论引擎（阶段 1） | 8 个 Agent 端到端工作；输出结构化论点索引 |
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

## 十一、附录 A：关键问题与讨论点

以下问题在实现前需要进一步澄清/决策：

| 编号 | 问题 | 候选方案 | 推荐方案 |
|:---|:---|:---|:---|
| **Q1** | 每位辩手每轮应发言多少次？ | A) 固定每方 3 轮；B) 根据问题复杂度动态调整；C) 由 Coach 决定 | B + C 混合（默认 3 轮，Coach 可提前终止） |
| **Q2** | POI 触发规则是硬编码规则还是 Agent 自主决策？ | A) 硬编码（如每 2 轮强制一次 POI）；B) Agent 基于对手发言内容自主决定 | B（更自然，可学习） |
| **Q3** | 创新保护机制中"先例不缺失"的判定谁负责？ | A) I-Judge 独立判定；B) P-Judge（原则审查）辅助判定；C) I-Judge + C-Judge（案例审查）共同判定 | C（案例审查辅助创新审查） |
| **Q4** | 权重配置是固定的还是学习的？ | A) 基于问题类型的固定权重表；B) 基于学习的权重调优；C) 固定+人工可配置 | C（默认固定，允许用户覆盖） |
| **Q5** | Evidence Brief 的证据数量上限是？ | A) 20-30 条；B) 50-100 条；C) 不限（由 Agent 自行选择） | A（20-30，保证 Agent 能逐条审阅，避免信息过载） |
| **Q6** | 是否需要持久化辩论状态？ | A) 仅内存；B) JSON/文件；C) 数据库（SQLite/PostgreSQL） | B（JSON 文件，轻量、可复现） |
| **Q7** | 是否支持中文/英文双语言？ | A) 仅中文；B) 仅英文；C) 双语自适应 | C（根据问题语言自动切换 Agent Prompt 语言） |
| **Q8** | 法官权重是否需要根据"问题复杂度"调整？ | A) 固定；B) 基于问题分类动态调整；C) 基于辩论结果自动调整 | B（简单问题减少创新/案例维度权重） |
| **Q9** | 裁决官的推理链是事后生成还是过程中逐步构建？ | A) 事后（阅读法官报告后一次性生成）；B) 过程中逐步构建 | A（更简单，且可审核） |
| **Q10** | 阶段间的状态传递使用什么结构？ | A) JSON/字典；B) Pydantic 模型；C) LangGraph StateSchema | B + C（Pydantic 嵌入 LangGraph State 中，既类型安全又可编排） |

---

**报告完成日期**：2026 年 6 月 14 日
