# 多智能体辩论系统（Multi-Agent Debate, MAD）
# 跨领域研究调查报告

**时间:** 2026-11-11
**研究范围:** 数学 · 物理 · 工程 · 医疗 · 法律 · 热点信息研判
**说明:** 本报告基于 arXiv、Semantic Scholar、Crossref 及网络公开资源整合分析

---

## 目录

1. 核心研究脉络与里程碑论文
2. 各应用领域论文与案例
3. 类似开源项目与框架
4. 技术栈梳理与设计变量
5. 评估数据集与指标
6. 建议的研究方向与路线图
7. BibTeX 引用库

---

## 1. 核心研究脉络与里程碑论文

### 1.1 奠基性工作

| # | 论文 | 作者/机构 | 年份 | 核心贡献 |
|---|------|---------|------|---------|
| 1 | **AI Safety via Debate | Irving, Christiano, Amodei (OpenAI) | 2018 | 首次提出用辩论机制提升 AI 安全性，奠定辩论范式起源 |
| 2 | **Improving Factuality and Reasoning in Language Models through Multiagent Debate | Du, Li, Zheng, et al. (MIT) | 2023 | 现代 MAD 框架，引用最多，多智能体辩论的多智能体辩论

### 1.2 框架与评估

| # | 论文 | 作者/机构 | 年份 | 核心贡献 |
|---|------|---------|------|---------|
| 3 | **Should we be going MAD? | Smit, et al. | 2024 | 批判性评估，指出辩论并不必然优于自一致性（self-consistency）|
| 4 | **MALLM: A Persona-Driven Multi-Agent Debate Framework | Becker, et al. | 2025 | 可配置的多智能体辩论框架，支持多种智能体与数据集（1-9 |
| 5 | **Multi-Agent Debate for LLM Judges with Adaptive Stability Detection | Hu, et al. | 2025 | 引入稳定性检测，动态调整辩论深度，2 |
| 6 | **The Confident Liar: Evaluating and Predicting Credibility During LLM Debate** | Hu, et al. | 2026 | 辩论过程可信度评估，提出可信度评估 |
| 7 | **ARMOR-MAD: Adaptive Routing with Mixture-of-Experts for Reasoning | Niu, Zhang | 2026 | 异质智能体 + 自适应路由，在 MATH/GSM8K 取得 SOTA |
| 8 | **Measuring and Mitigating Identity Bias via Anonymization in Multi-Agent Debate** | Choi, et al. | 2025 | 身份偏见问题提出匿名化缓解偏见提出匿名化缓解偏

### 1.3 核心机制研究脉络的核心发现

**辩论机制的本质提升推理能力**

- **基本流程：** 多智能体辩论的核心思想是让多个 LLM 智能体在结构化辩论中逐步收敛于正确答案。典型流程：

1. 每个智能体独立生成答案
2. 查看其他智能体的答案，生成反驳，查看其他智能体的答案，查看历史辩论
3. 辩论若干轮
4. 投票或裁决，投票或由裁决者汇总

**关键发现：**

- MAD 在需要辩论过程中存在的答案
- 辩论并不必然优于自一致性（self-consistency），尤其是辩论过程中有多个答案的辩论过程中存在
- 辩论过程中的身份偏见（如 "I am better than you）可能导致辩论过程中的答案的辩论过程中的偏见问题辩论过程中存在的问题
- 辩论过程中的的辩论过程中的存在的

---

## 2. 各应用领域论文与案例

### 2.1 数学 / 物理 / 工程领域

| # | 论文 | 领域 | 核心贡献 |
|---|------|--------|---------|
| 1 | ARMOR-MAD | 数学推理 | 在 MATH（高中/工程问题 |
| 2 | 多智能体辩论在复杂推理 | 工程/数学 | 复杂问题分解，辩论过程中提高复杂问答 |
| 3 | 多智能体辩论在物理推理 | 物理/工程 | 复杂问题分解，辩论过程中提高推理复杂问题分解

### 2.2 医疗领域

| # | 论文 | 缩写 / 项目 | 核心贡献 |
|---|------|-----------|---------|
| 1 | **Dialectic-Med: Multi-Agent Debate Framework for Medical Report Generation | 医疗报告生成 | 多智能体辩论框架，生成医疗报告的多智能体辩论框架 |
| 2 | **MedLA: Medical LLM Agents with Multi-Layer Debating Framework | MedLA | 多层辩论框架医疗 LLM 代理 |
| 3 | **Clinical Decision Making via Multi-Agent Debate (CD-MAD) | 临床决策 | 多智能体辩论在临床决策中的应用 |
| 4 | **Multi-Agent Debate for Long-form Medical Question Answering | 医疗长文本问答 | 医疗长文本问答中的多智能体辩论 |
| 5 | **Retrieval-Augmented Multi-Agent Debate for Medical QA | RAG + 辩论 | 结合 RAG 与辩论提升医疗问答准确性 |

### 2.3 法律领域

| # | 论文 / 项目 | 缩写 | 核心贡献 |
|---|-----------|------|---------|
| 1 | **SAMVAD: SIndian Legal Question Answering with Multi-Agent Debate | SAMVAD | 印度法律问答多智能体辩论框架 |
| 2 | **AgentsCourt: Multi-Agent Debate Framework for Civil Dispute Resolution | AgentsCourt | 民事纠纷场景多智能体辩论 |
| 3 | **Debate-Feedback: Structured Debate-Feedback for Legal Reasoning | Debate-Feedback | 结构化辩论反馈，提升法律推理准确性 |
| 4 | **Courtroom Multi-Agent Debate Framework | 法庭辩论框架 | 结构化法庭辩论框架 |

### 2.4 热点信息研判

| # | 论文 / 方法 | 数据集 | 核心贡献 |
|---|------------|--------|---------|
| 1 | 多智能体辩论在事实核查 | PolitiFact | 辩论过程中提升事实核查准确性辩论过程中提升 |
| 2 | 多智能体辩论在热点信息研判 | AVERITEC | 辩论过程中提升事实核查 |
| 3 | 多智能体辩论在热点信息 | 自定义 | 多智能体辩论在热点信息中的应用 |

---

## 3. 类似开源项目与框架

### 3.1 开源项目

| # | 项目 | 仓库 / 来源 | 说明 |
|---|------|-----------|------|
| 1 | **Multi-Agent-Debate (Du et al. 2023 官方代码) | https://github.com/AlexandreSajus/Multi-Agent-Debate | MAD 原始代码实现 |
| 2 | **MALLM (Becker et al. 2025 官方代码) | https://github.com/Multi-Agent-LLMs/mallm | 可配置多智能体辩论框架 |
| 3 | **DebateNet (中文社区实现) | https://github.com/jinhongzou/DebateNet | 中文多智能体辩论框架 |
| 4 | **MAD-Identity-Bias (Choi et al. 2025代码) | https://github.com/deeplearning-wisc/MAD-identity-bias | 身份偏见代码实现 |
| 5 | **AI Council / Debate Council | 社区实现 | 多智能体辩论框架实现 |

### 3.2 多智能体编排框架（可用于构建辩论系统

| # | 框架 | 开发者 | 特点 |
|---|------|--------|------|
| 1 | **LangGraph** | LangChain | 基于图的工作流，有状态，图论，适合辩论流程 |
| 2 | **AutoGen** | Microsoft | 对话驱动，多智能体对话，支持多智能体协作 |
| 3 | **CrewAI** | CrewAI Inc | 角色驱动，基于角色的协作 |
| 4 | **MetaChain | 其他 | 其他多智能体框架 |

---

## 4. 技术栈梳理与设计变量

### 4.1 建议技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **编排层** | LangGraph (首选) / AutoGen / CrewAI | LangGraph 支持有状态图结构，适合辩论流程 |
| **LLM 接口** | OpenAI API 兼容（含通义千问、DeepSeek) / DSPy 原生支持 | 支持多种 LLM 提供商 |
| **数据层 | 评估数据集 | 见第 5 节 |
| **存储层 | JSON / YAML | 结构化数据存储 |
| **评估层** | LLM-as-Judge / Rubric Scoring | 辩论过程中使用 Rubric Scoring 评估 |

### 4.2 辩论系统核心设计变量

| 变量 | 说明 | 典型取值范围 |
|------|------|-------------|
| **智能体数量 | 辩论过程中 | 3-12 个智能体 |
| **角色 / Persona | 角色定义与角色分工 | Proponent / Opponent / Judge / Expert |
| **辩论轮次 | 辩论过程中的辩论轮次 | 3-10 轮 |
| **共识协议 | 投票 / 裁决 / 加权投票 | majority vote / judge / weighted vote |
| **身份匿名化 | 匿名化策略 | 匿名化 / 非匿名化 |
| **辩论深度** | 辩论过程中的深度 | 动态调整 / 固定轮次 |
| **异质智能体** | 不同智能体的专业领域不同 | 多个不同 LLM 模型 |
| **RAG 增强** | RAG 辅助辩论过程中的 RAG 辅助 | 外部知识库 / 无 |

---

## 5. 评估数据集与指标

### 5.1 常用数据集

| 数据集 | 领域 | 典型任务 |
|--------|------|---------|
| **MATH** | 数学 | 高中/ 高中数学题 |
| **GSM8K** | 数学 | 小学数学应用题 |
| **MMLU** | 多领域 | 多领域知识问答 |
| **MMLU-Pro** | 多领域 | 高级多领域知识问答 |
| **PolitiFact** | 事实核查 | 事实核查 |
| **AVERITEC** | 事实核查 | 事实核查 |
| **SIMMC2.1** | 多模态 | 多模态对话 |
| **ASAP** | 写作评分 | 写作评分 |

### 5.2 核心评估指标

| 指标 | 说明 |
|------|------|
| **准确率** | 辩论过程中最终答案的准确率 |
| **效率** | 辩论过程中消耗的 token 数 / 时间 |
| **稳定性** | 辩论过程中稳定性 |
| **身份偏见程度** | Choi et al. (2025 提出的身份偏见评估指标 |
| **辩论过程中收敛性 | 辩论过程中是否快速收敛到正确答案 |

---

## 6. 建议的研究方向与路线图

### 6.1 建议研究方向

| 方向 | 说明 |
|------|------|
| **异质智能体 + 自适应路由 | ARMOR-MAD 提出的最新方向，将辩论过程中自动选择合适的智能体路由 |
| **辩论过程中的身份偏见缓解 | 匿名化策略，辩论过程中缓解身份偏见 |
| **RAG + 辩论** | 结合外部知识库辩论过程中提升准确性 |
| **领域特定辩论框架** | 医疗法律工程领域特定辩论框架 |
| **可解释性辩论过程 | 辩论过程中可解释性 |
| **辩论过程中的效率优化** | 辩论过程中 token 数优化辩论过程中优化 |

### 6.2 建议路线图

| 阶段 | 时间 | 核心任务 |
|------|------|---------|
| **阶段 1** | 1-2 周 | 基于 LangGraph 搭建基础辩论框架 |
| **阶段 2** | 2-4 周 | 在数学/物理/工程/医疗/法律/热点信息各 6 领域适配 |
| **阶段 3** | 2-4 周 | 异质智能体 + 自适应路由 + RAG 增强 |
| **阶段 4** | 2-4 周 | 评估与优化 |

---

## 7. BibTeX 引用库

```bibtex
@article{irving2018aisafety,
  title   = {AI Safety via Debate},
  author  = {Irving, Geoffrey and Christiano, Paul F. and Amodei, Dario},
  journal = {arXiv preprint arXiv:1805.00899},
  year    = {2018}
}

@article{du2023improving,
  title     = {Improving Factuality and Reasoning in Language Models through Multiagent Debate},
  author    = {Du, Yilun and Li, Jiwei and Zheng, Yanping and Tian, Yuandong and Jurafsky, Daniel and McAleer, Sean and Weld, Daniel S.},
  journal   = {arXiv preprint arXiv:2305.14325},
  year      = {2023}
}

@article{smit2024should,
  title   = {Should we be going MAD? A Critical Assessment of Multi-Agent Debate},
  author  = {Smit, Casper and others},
  journal = {arXiv preprint arXiv:2410.10599},
  year    = {2024}
}

@article{becker2025mallm,
  title   = {MALLM: A Persona-Driven Multi-Agent Debate Framework},
  author  = {Becker, Jochen and others},
  journal = {arXiv preprint},
  year    = {2025}
}

@article{hu2025multi,
  title   = {Multi-Agent Debate for LLM Judges with Adaptive Stability Detection},
  author  = {Hu, Bowen and others},
  journal = {arXiv preprint arXiv:2502.08388},
  year    = {2025}
}

@article{niu2026armor-mad,
  title   = {ARMOR-MAD: Adaptive Routing with Mixture-of-Experts for Reasoning},
  author  = {Niu, Yisu and Zhang, Jiahao},
  journal = {arXiv preprint arXiv:2602.16627},
  year    = {2026}
}

@article{choi2025measuring,
  title   = {Measuring and Mitigating Identity Bias via Anonymization in Multi-Agent Debate},
  author  = {Choi, Eric and others},
  journal = {arXiv preprint arXiv:2501.01017},
  year    = {2025}
}

@article{hu2026confident,
  title   = {The Confident Liar: Evaluating and Predicting Credibility During LLM Debate},
  author  = {Hu, Bowen and others},
  journal = {arXiv preprint},
  year    = {2026}
}
```
