# ParaJudge 多智能体辩论系统 — 软件需求规格说明书 (SRS)

## 第 1 部分：引言 + 总体描述 + 功能需求 + 非功能需求 + 数据模型 + 详细技术栈

> **项目代号**：ParaJudge
> **文档版本**：**v1.2**
> **生成日期**：2026-06-15
> **设计依据**：基于 259 篇 MAD 领域论文 + 5 篇系统性综述的分析结果
>
> **版本历史**：
> - **v1.0 (2026-06-15)**：首版 SRS 发布
> - **v1.1 (2026-06-15)**：新增 FR-310 至 FR-315（Moderator 角色/状态机/质量守门/时间片/POI 批准/DebateSummary/配置驱动）；第 6 部分技术栈扩展为 ADR-006 至 ADR-013 深度选型分析；新增 Moderator 状态图子状态、技术栈风险热图
> - **v1.2 (本次)**：引入 **S3（Signal-driven + Structured + Sustainable）统一设计框架**；新增 **T1–T4 四项技术创新点**（AEBG 二部图 / DPP 多样性约束 / KS 检验收敛检测 / DS 证据理论融合）；新增 FR-400 至 FR-405（创新点相关功能需求）与 NF-200 至 NF-205（可解释性/不确定性相关非功能需求）

---

## 目录（第 1 部分）

1. [引言](#1-引言)
2. [总体描述](#2-总体描述)
3. [功能需求](#3-功能需求)
4. [非功能需求](#4-非功能需求)
5. [数据需求与数据模型](#5-数据需求与数据模型)
6. [详细技术栈](#6-详细技术栈)

---

## 1. 引言

### 1.1 目的

本需求规格说明书（Software Requirements Specification, SRS）对 **ParaJudge 多智能体辩论系统** 的功能需求、非功能需求、数据模型、接口需求、设计约束、以及 **详细技术栈选型** 进行系统性的定义和说明。

目标读者：项目决策与立项评审人员、系统架构师、前后端开发人员、质量保证与评估实验人员、未来维护者。

### 1.2 范围

**产品定义**：ParaJudge 是一个基于 **LangGraph 状态图编排 + 多 LLM Agent 协作** 的多智能体辩论与推理系统，采用 "证据准备 → 结构化辩论 → 独立审理 → 多维度裁决" 的四阶段架构，针对复杂推理、事实核查、创新评估等高风险决策场景提供高质量的可审计推理能力。

**关键特征**：
- 证据闭包（Evidence Closure）
- 目标驱动异质性（Objective-Driven Agent Heterogeneity）
- Moderator 主持下的结构化辩论（Phase 1）
- 检察官-辩护律师审理（Prosecutor-Defense Review, Phase 2.1）
- 五维专业化法官裁决（5-Dimension Specialized Judges, Phase 2.2）
- 类判决书推理链输出（Judgment-Style Reasoning Chain）

**v1.2 新增的核心技术创新点**（按 S3 框架组织）：
- **Signal-driven（信号驱动）**：T1（AEBG 论点-证据二部图，用图信号做质量评分）、T3（KS 检验的统计收敛检测）
- **Structured（结构化）**：T1（二部图结构）、T4（DS 证据理论融合，输出得分+不确定性+置信区间）
- **Sustainable（可持续/节算）**：T2（DPP 多样性约束，避免重复论点浪费 token）、T3（KS 检验尽早终止收敛辩论）

### 1.3 定义与缩略语

| 缩写 | 定义 |
|:---|:---|
| **MAD** | Multi-Agent Debate，多智能体辩论 |
| **Agent** | 具有特定目标的 LLM 智能体，在 LangGraph 中表现为一个节点 |
| **POI** | Point of Information，段间质询 |
| **Evidence Brief** | 辩论前构建的统一证据包（所有辩论必须引用其中条目） |
| **Domain KB** | 领域知识库（原则库 + 案例库） |
| **AEBG** | Argument-Evidence Bipartite Graph，论点-证据二部图（T1 创新点） |
| **DPP** | Determinantal Point Process，行列式点过程（T2 创新点，用于控制论点多样性） |
| **KS 检验** | Kolmogorov-Smirnov Test，用于检测辩论评分分布是否收敛（T3 创新点） |
| **DS 证据理论** | Dempster-Shafer Evidence Theory，用于融合多位法官的不确定评分（T4 创新点） |
| **S3 框架** | Signal-driven + Structured + Sustainable，ParaJudge v1.2 的统一设计框架 |

---

## 2. 总体描述

### 2.1 总体架构（高层视图）

```
                    ┌─────────────────────────────────────────┐
                    │     Layer 1：前端 / 接口层                │
                    │  ┌─────────┐   ┌──────────┐   ┌────────┐ │
                    │  │   CLI   │   │  FastAPI │   │  HTML  │ │
                    │  │ (Typer) │   │  (API)   │   │ Report │ │
                    │  └─────────┘   └──────────┘   └────────┘ │
                    └──────────────────┬────────────────────────┘
                                       │
                    ┌──────────────────▼────────────────────────┐
                    │ Layer 2：编排层 — LangGraph StateGraph      │
                    │  Phase 0: Evidence Builder                 │
                    │  Phase 1: Debate Engine (Coach+Speakers)   │
                    │  Phase 2.1: Review Engine (Prosecutor/     │
                    │            Defense Attorney - 交叉质询)     │
                    │  Phase 2.2: Judgment Engine (5 Judges +    │
                    │            Final Judge + 推理链 + 裁决书)   │
                    └──────────────────┬────────────────────────┘
                                       │
                    ┌──────────────────▼────────────────────────┐
                    │ Layer 3：Agent 层 — LLM Provider            │
                    │  LLMProvider 抽象基类                       │
                    │  ├─ MockProvider（本地模拟）                 │
                    │  ├─ OpenAIProvider（兼容协议）               │
                    │  └─ DashScopeProvider（通义千问）            │
                    │  Prompt 模板库 + Token 计数器 + 重试逻辑     │
                    └──────────────────┬────────────────────────┘
                                       │
                    ┌──────────────────▼────────────────────────┐
                    │ Layer 4：数据与知识层                        │
                    │  Evidence Brief · ArgumentIndex            │
                    │  Domain KB (YAML) · 状态持久化 (JSON)       │
                    │  Pydantic v2（全栈类型安全）                  │
                    └───────────────────────────────────────────┘
                                       │
                    [外部 API：arXiv / Semantic Scholar / Crossref /
                              OpenAI / DashScope]
```

---

## 3. 功能需求（Functional Requirements）

### 3.1 问题输入与配置（FR-100）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-101 | 问题文本输入 | P0 | 支持 CLI / API 提交 10-1000 字符问题 |
| FR-102 | 问题类型自动识别 | P0 | 识别 fact / decision / innovation / open 四类 |
| FR-103 | 问题-权重配置 | P1 | 不同问题类型对应不同的法官权重配置 |
| FR-104 | 模型与参数配置 | P0 | 支持 Provider / 模型名 / 温度 / 深度配置 |
| FR-105 | 领域知识库选择 | P1 | 支持预设 KB 或自定义 YAML |
| FR-106 | 证据源开关 | P2 | 可启用/禁用具体检索源 |

### 3.2 证据准备与知识注入（FR-200）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-201 | 关键词提取 | P0 | 3-8 个检索关键词 |
| FR-202 | arXiv 检索 | P0 | 参考 `src/search/arxiv_client.py` |
| FR-203 | Semantic Scholar 检索 | P0 | 参考 `src/search/semantic_scholar_client.py` |
| FR-204 | Crossref 检索 | P1 | 参考 `src/search/crossref_client.py` |
| FR-205 | 多源合并与去重 | P0 | 参考 `src/search/engine.py::unified_search` |
| FR-206 | Evidence Brief 生成 | P0 | 20-30 条结构化证据条目 |
| FR-207 | 证据可信度评分 | P1 | 0-1 可信度 + 相关性评分 |
| FR-208 | Domain KB 加载 | P1 | YAML 原则库/案例库 |
| FR-209 | 证据包缓存 | P2 | 相同关键词 7 天缓存 |

### 3.3 辩论引擎（FR-300）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-301 | Coach 角色（正反双方） | P0 | 分析问题、规划论点、分配证据 |
| FR-302 | Speaker 角色（目标驱动异质性） | P0 | 每方 2-3 名 Speaker，各有独立目标函数 |
| FR-303 | 结构化发言轮次 | P0 | 立论-质询-立论-质询的正式辩论流程 |
| FR-304 | POI 段间质询 | P1 | 对方 Agent 可打断发起质询 |
| FR-305 | 证据闭包检查 | P0 | 每条论点必须引用 ≥ 1 条 Evidence Item |
| FR-306 | 引用验证 | P1 | 检查引用存在性与内容匹配度 |
| FR-307 | 论点索引构建 | P0 | 维护 ArgumentIndex 结构 |
| FR-308 | 问题漂移检测 | P2 | Coach 检测辩论偏离主题并回归 |
| FR-309 | 辩论自适应终止 | P2 | 无新论点时提前结束 |
| **FR-310** | **Moderator 角色 & 五阶段状态机** | **P0** | **管理 OPENING_STATEMENTS / CROSS_EXAMINATION / FREE_DEBATE / CLOSING_STATEMENTS / DONE 五个子阶段，驱动辩论按正式流程推进** |
| **FR-311** | **Moderator 质量守门** | **P0** | **在每次发言后执行：重复论点检测（embedding 相似度）、主题漂移检测（规则+语义）、超时控制（时间片），不符合要求则要求修正或扣分** |
| **FR-312** | **Moderator 时间片控制** | **P1** | **按阶段配置每个 Agent 的发言 token/时间预算；超预算自动截断或警告，并记录到 moderation_log** |
| **FR-313** | **Moderator POI 批准机制** | **P1** | **对方 Agent 发起 POI 时，Moderator 基于阶段/上下文/主题相关性决定"允许/延迟/拒绝"，批准后才进入质询子流程** |
| **FR-314** | **Moderator DebateSummary 产出** | **P0** | **辩论结束（CLOSING_STATEMENTS → DONE）后，生成结构化 DebateSummary：关键论点清单 / 证据覆盖热力图 / 未解决问题列表 / 各方立场摘要，作为 ReviewEngine 与 JudgmentEngine 的输入** |
| **FR-315** | **Moderator 配置驱动** | **P1** | **子阶段顺序、时间片预算、质量守门阈值、POI 允许率均通过 DebateConfig.moderator_profile 可配置，支持 debate_style ∈ {formal/freestyle/academic/judicial} 多预设** |

### 3.4 审理引擎（FR-400）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-401 | 检察官角色 | P0 | 扫描论点索引，识别证据缺失 / 逻辑漏洞 / 未验证假设 / 选择性呈现 |
| FR-402 | 辩护律师角色 | P0 | 为弱势论点提供最佳辩护 + 补充被忽略证据 |
| FR-403 | 交叉质询流程 | P1 | 2-3 轮检察官-辩护律师对质 |
| FR-404 | 审理独立性保证 | P0 | 审理 Agent 仅访问结构化索引，不读辩论发言 |

### 3.5 裁决引擎（FR-500）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-501 | E-Judge 证据法官 | P0 | 证据覆盖率 / 引用准确率 / 质量分布 |
| FR-502 | L-Judge 逻辑法官 | P0 | 形式谬误 / 推理链完整性 / 前提-结论相关性 |
| FR-503 | P-Judge 原则法官 | P1 | 与 Domain KB 原则一致性 |
| FR-504 | C-Judge 案例法官 | P1 | 先例/案例支持 |
| FR-505 | I-Judge 创新法官 | P1 | 创新价值 / 突破潜力 / 非共识价值 |
| FR-506 | Final-Judge 综合裁决官 | P0 | 按问题类型加权整合 |
| FR-507 | 并行评估 | P1 | 5 位法官并行执行（LangGraph parallel node） |
| FR-508 | 推理链构建 | P0 | "结论 → 证据/原则/案例" 可追踪映射 |
| FR-509 | 不确定性标注 | P1 | 标注未验证假设 / 部分冲突证据 |
| FR-510 | 创新保护机制 | P1 | 区分"先例缺失 = 创新" vs "证据不足 = 漏洞" |
| FR-511 | 裁决书生成 | P0 | HTML / Markdown / JSON 三种格式 |
| FR-512 | 裁决书模板引擎 | P2 | Jinja2 HTML 模板自定义 |

### 3.6 LLM Provider 适配（FR-600）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-601 | Provider 抽象基类 | P0 | `LLMProvider.chat(prompt, **kwargs)` 统一接口 |
| FR-602 | Mock Provider | P0 | 本地规则模拟 + seed 控制可复现 |
| FR-603 | OpenAI 兼容 Provider | P0 | Chat Completions API，兼容 vLLM/本地部署 |
| FR-604 | DashScope Provider | P1 | 阿里云通义千问 SDK |
| FR-605 | 多 Provider 降级策略 | P2 | 失败自动切换，最终回退 Mock |
| FR-606 | Prompt 模板库 | P0 | 集中管理所有 Agent 模板 |
| FR-607 | Token 计数与预算控制 | P1 | 统计每次调用的 token 消耗 |
| FR-608 | 成本估算 | P2 | 基于 token 单价的成本估算 |

### 3.7 CLI 接口（FR-700）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-701 | 子命令分组 | P0 | `parajudge run / evidence / judge / config` |
| FR-702 | run 子命令 | P0 | 执行完整四阶段流程 |
| FR-703 | 彩色终端输出 | P1 | rich 彩色/表格/进度条 |
| FR-704 | 输出文件保存 | P0 | HTML / JSON / MD 保存 |

### 3.8 API 接口（FR-800）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-801 | 启动辩论（异步任务） | P0 | `POST /api/v1/parajudge/run` |
| FR-802 | 查询任务状态 | P0 | `GET /api/v1/parajudge/task/{id}` |
| FR-803 | 获取裁决书 | P0 | `GET /api/v1/parajudge/task/{id}/report` |
| FR-804 | 健康检查 | P0 | `GET /health` |
| FR-805 | Swagger API 文档 | P0 | `GET /docs` |

### 3.9 配置与持久化（FR-900）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-901 | 环境变量配置 | P0 | `.env` + python-dotenv，从不提交到仓库 |
| FR-902 | Pydantic Settings | P0 | 结构化配置管理 |
| FR-903 | 辩论状态持久化 | P1 | `data/runs/{id}/state.json` |
| FR-904 | 裁决书保存 | P0 | HTML / MD / JSON 三份 |
| FR-905 | 结构化运行日志 | P1 | `logs/parajudge-{date}.log`，自动脱敏 |

### 3.10 评估与实验管线（FR-1000）

| ID | 需求 | 优先级 | 简要描述 |
|:---|:---|:---|:---|
| FR-1001 | 基准数据集加载器 | P2 | GSM8K / MMLU / PolitiFact |
| FR-1002 | 基线系统实现 | P2 | 单 LLM / Self-Consistency / 标准 MAD |
| FR-1003 | 消融实验脚本 | P3 | 8 种消融配置 |
| FR-1004 | 多维度评估指标 | P2 | 准确性 / 证据覆盖率 / 可追溯性 / 不确定性校准度 |
| FR-1005 | 结果聚合与可视化 | P3 | 自动生成对比报告与图表 |

---

## 4. 非功能需求

### 4.1 性能与可扩展性

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-101 | 端到端响应时间 | P1 | 普通问题 ≤ 5 分钟 |
| NFR-102 | 并行辩论支持 | P2 | ≥ 10 个独立任务同时运行 |
| NFR-103 | API 响应延迟 | P1 | P95 ≤ 300ms（不含 LLM 等待） |
| NFR-104 | 简单问题加速路径 | P2 | token 节省 ≥ 40% |
| NFR-105 | 分层模型策略 | P2 | Coach/法官用强模型，Speaker/POI 用轻模型 |

### 4.2 可靠性与可用性

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-201 | LLM 调用重试（tenacity） | P0 | 指数退避最多 3 次 |
| NFR-202 | 优雅降级 | P1 | 单个 Agent 失败不导致整体崩溃 |
| NFR-203 | 可复现性（Mock+seed） | P1 | 相同输入 → 相同输出 |
| NFR-204 | 健康检查接口 | P1 | `GET /health` 检查 Provider 连通性 |
| NFR-205 | 请求幂等性 | P2 | 相同请求仅执行一次（基于输入 hash） |

### 4.3 安全性

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-301 | API Key 保护 | P0 | 仅从环境变量读取，不在日志/输出中出现 |
| NFR-302 | 输入验证（Pydantic） | P0 | 长度 / 字符集 / 格式严格校验 |
| NFR-303 | 统一 HTTPS 客户端（httpx） | P0 | 禁止裸 HTTP；支持代理配置 |
| NFR-304 | 权限隔离（可扩展） | P2 | 预留 OAuth2 接口 |
| NFR-305 | 依赖安全审计 | P1 | 使用 `pip-audit` 定期扫描 |

### 4.4 可维护性与可扩展性

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-401 | 模块化设计 | P0 | 模块间仅通过 Pydantic 模型/公开函数交互 |
| NFR-402 | Provider 无关性 | P1 | 新增 Provider 无需改 Agent 代码 |
| NFR-403 | 代码风格（PEP 8 + 类型注解） | P0 | ruff check 无严重告警 |
| NFR-404 | 明确错误信息 | P1 | 错误类型 + 可能原因 + 建议操作 |
| NFR-405 | 可插拔 Agent | P2 | 遵循基类即可新增 Agent 角色 |

### 4.5 可观测性与日志

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-501 | JSON 结构化日志 | P1 | 可被 ELK/Loki 直接解析 |
| NFR-502 | Token 消耗监控 | P1 | 每次调用记录 input/output token |
| NFR-503 | 阶段性能埋点 | P1 | Phase 0/1/2.1/2.2 各自耗时 |
| NFR-504 | 外部 API 审计日志 | P2 | 记录外部请求来源与状态 |

### 4.6 兼容性与可移植性

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-601 | Python 版本支持 | P0 | 3.10 / 3.11 / 3.12 / 3.13 / 3.14 |
| NFR-602 | 操作系统支持 | P1 | Linux 100% / macOS 冒烟 / Windows 最佳努力 |
| NFR-603 | 容器化（Docker） | P2 | 提供 Dockerfile |
| NFR-604 | 中文双语支持 | P1 | Prompt / 裁决书 / CLI 自动切换中英文 |

### 4.7 法律与合规

| ID | 需求 | 优先级 | 目标值 |
|:---|:---|:---|:---|
| NFR-701 | 第三方 API 合规 | P1 | 遵守使用政策，设置合理速率限制与 User-Agent |
| NFR-702 | 数据隐私 | P0 | 用户输入不用于训练；不外传到 LLM 外的服务 |
| NFR-703 | 开源许可证兼容性 | P1 | 避免 GPL 强传染依赖；使用 MIT/Apache-2.0 友好依赖 |

---

## 5. 数据需求与数据模型

### 5.1 核心模型一览

全栈使用 **Pydantic v2**。顶层结构：

```
DebateRun
├── config (DebateConfig)
├── problem_type (str)
├── evidence_brief (EvidenceBrief)
├── debate_state (DebateState)
│   ├── coach_plans
│   ├── rounds: List[DebateRound]
│   └── argument_index (ArgumentIndex)
├── review_report (ReviewReport)
├── final_verdict (FinalVerdict)
│   ├── judge_reports: List[JudgeReport]
│   ├── reasoning_chain: List[ReasoningStep]
│   └── uncertainty_annotations
└── run_metadata (RunMetadata)
```

### 5.2 关键模型定义（摘要）

**EvidenceItem / EvidenceBrief**：
```
EvidenceItem: id, title, summary, source_type, citation_info,
              credibility, relevance_score, year, authors, raw_url
EvidenceBrief: query, extracted_keywords, items, retrieval_sources,
               total_retrieved, generated_at
```

**Argument / ArgumentIndex**：
```
Argument: id, side, speaker_id, content, argument_type,
          evidence_refs, round_num, supports, attacks, poi_interactions
ArgumentIndex: arguments, unresolved_issues, evidence_coverage_ratio, total_rounds
```

**ReviewItem / ReviewReport**：
```
ReviewIssueType: evidence_gap / logic_flaw / unverified_assumption /
                 selective_presentation / contradiction
ReviewItem: id, type, target_argument_id, description, suggested_evidence,
            severity, prosecutor_note, defense_response
ReviewReport: items, prosecutor_summary, defense_summary, cross_examination_transcript
```

**JudgeReport / FinalVerdict**：
```
JudgeDimension: evidence / logic / principle / case / innovation
DimensionScore: score, reasoning, key_insights
JudgeReport: judge_type, dimension_scores, overall_score, key_insights,
             referenced_evidence_ids / principle_ids / case_ids
ReasoningStep: conclusion_fragment, evidence_refs, principle_refs,
               case_refs, confidence, is_assumption_based
FinalVerdict: overall_conclusion, overall_confidence, judge_reports,
              reasoning_chain, uncertainty_annotations, innovation_protection_notes,
              final_score, weight_config, problem_type
```

**DomainKB（YAML）**：
```
PrincipleItem: id, principle, domain, rationale
CaseItem: id, case_title, description, outcome, domain, year, relevance_tags
DomainKB: domain, principles, cases
```

**DebateConfig**：
```
DebateConfig: model_provider, model_name, temperature, max_rounds,
              speaker_count_per_side, enable_poi, enable_review_phase,
              judge_dimensions, evidence_brief_size, domain_kb_path,
              weight_profiles (fact/decision/innovation/open -> 各维度权重)
```

### 5.3 数据存储概览

| 数据 | 格式 | 位置模式 | 典型大小 |
|:---|:---|:---|:---|
| Evidence Brief | JSON | `data/runs/{id}/evidence_brief.json` | 50-100 KB |
| Argument Index | JSON | `data/runs/{id}/argument_index.json` | 30-80 KB |
| Review Report | JSON | `data/runs/{id}/review_report.json` | 10-30 KB |
| Final Verdict | JSON | `data/runs/{id}/final_verdict.json` | 20-50 KB |
| 裁决书（HTML） | HTML | `data/runs/{id}/report.html` | 20-50 KB |
| 裁决书（MD） | Markdown | `data/runs/{id}/report.md` | 10-30 KB |
| 完整状态 | JSON | `data/runs/{id}/state.json` | 200-500 KB |
| 运行日志 | JSON Lines | `logs/parajudge-{date}.log` | 100-500 KB/次 |
| Domain KB | YAML | `data/domain_kb/{domain}.yaml` | 5-20 KB |

---

## 6. 详细技术栈

### 6.1 技术栈分层总览

```
Layer 1：前端 / 接口层
  ├── CLI：Typer 0.12+ + rich 13.7+
  ├── REST API：FastAPI 0.111+ + uvicorn[standard] 0.30+
  └── HTML Report：Jinja2 3.1+ 模板渲染

Layer 2：编排层（核心）
  ├── LangGraph 0.2.x（StateGraph 状态图 / parallel node 并行节点）
  ├── langchain 0.3.x（Runnable 抽象）
  ├── langchain-core 0.3.x
  ├── langchain-openai 0.2.x（OpenAI 集成）
  ├── langchain-community 0.3.x
  └── MemorySaver / SQLiteSaver（Checkpointer 状态持久化）

Layer 3：Agent 层
  ├── LLM Provider 抽象（含 Mock/OpenAI/DashScope 三种实现）
  ├── openai Python SDK 1.40+（异步/流式）
  ├── dashscope 1.20+（通义千问）
  ├── tiktoken（token 计数）
  ├── tenacity 9.0+（LLM 调用重试）
  ├── httpx 0.27+（异步 HTTP 客户端）
  ├── requests 2.32+（脚本模式）
  └── Prompt 模板库（纯文本 + {变量} 注入）

Layer 4：数据与知识层
  ├── Pydantic v2 2.5+（全栈数据模型）
  ├── pydantic-settings 2.5+（配置管理）
  ├── python-dotenv 1.0+（.env 加载）
  ├── PyYAML 6.0+（Domain KB 加载）
  ├── JSON（Python 标准库，零额外依赖）
  ├──（可选）networkx 3.3+：论点关系图
  └──（可选）matplotlib 3.8+：评估结果绘图

外部 API
  ├── arXiv API（原生 HTTP/XML）
  ├── Semantic Scholar API（原生 HTTP/JSON）
  ├── Crossref API（原生 HTTP/JSON）
  ├── OpenAI Chat Completions / 兼容端点（vLLM / 本地部署）
  └── DashScope（阿里云通义千问）

学术检索 / 解析 / 引用管理
  ├── arxiv 2.1+（arXiv Python 客户端）
  ├──（可选）semanticscholar 0.5+
  ├──（可选）scholarly 1.7+（Google Scholar）
  ├──（可选）pyalex 0.2+（OpenAlex）
  ├── pymupdf 1.24+（PDF 文本提取）
  ├── pypdf 5.0+
  ├── pdfplumber 0.11+
  ├── python-docx 1.1+（Word）
  ├── beautifulsoup4 4.12+ + lxml 5.3+（HTML/XML 解析）
  ├── markdownify 0.13+（HTML→MD）
  ├── pyzotero 1.5+（Zotero API）
  └── bibtexparser 1.4+（.bib 解析）

基础设施 / 开发工具
  ├── 编程语言：Python 3.10+（推荐 3.11/3.12）
  ├── 包管理：pip（requirements.txt），可选 poetry/uv
  ├── 代码质量：ruff（lint+format），可选 mypy
  ├── 测试：pytest 8.x + pytest-asyncio
  ├── 日志：Python logging + JSON Formatter
  ├── 容器化：Docker（P2）
  ├── CI/CD：GitHub Actions（P2）
  ├── 文档：Markdown + FastAPI 自动 Swagger/ReDoc
  └── 进度条：tqdm 4.66+
```

### 6.2 技术选型深度分析表（各层依赖 + 选型理由 + 替代方案对比）

> 在 6.1 分层总览基础上，对每个**核心技术**补充"选型理由"与"替代方案对比"，便于决策回溯。

| 分层 | 包名 | 最低版本 | 用途 | P 级别 | **选型理由 / 为什么是它** | **替代方案对比** |
|:---|:---|:---|:---|:---|:---|:---|
| **编排层** | **langgraph** | 0.2.0 | **核心**：StateGraph 工作流编排、并行节点、Checkpointer | P0 | **状态图模型天然匹配四阶段+五法官并行+Moderator五阶段子状态机**；`parallel node` 几乎无代码获得并行；Checkpointer 免费获得断点续跑 | AutoGen（对话强但状态控制弱）；CrewAI（Role/Goal直观，状态持久化弱）；自研asyncio状态机（≥3人月，无调试工具） |
| 编排层 | langchain | 0.3.0 | Runnable抽象、Agent模板 | P0 | 与langgraph强绑定，`Runnable`抽象是langgraph的节点可直接消费 | 纯prompt模板+自定义（失去LangChain生态链） |
| 编排层 | langchain-core | 0.3.0 | 核心抽象 | P0 | langgraph的状态序列化依赖`langchain-core`的`RunnableSerializable`；两者版本必须严格匹配 | 无实用替代 |
| 编排层 | langchain-openai | 0.2.0 | OpenAI兼容Provider集成 | P0 | 让LangGraph节点可以通过`ChatOpenAI`消费OpenAI SDK，便于Runnable链组合 | 直接用原生openai SDK（失去LangChain链组合能力） |
| 编排层 | langchain-community | 0.3.0 | 社区Provider扩展 | P1 | DashScope/社区工具链可按需引入 | 不装；直接实现适配器即可，但工作量增加 |
| **Web框架** | **fastapi** | 0.111.0 | **核心**：REST API、类型安全、自动文档 | P0 | **ASGI+Pydantic原生集成**；与本项目Pydantic v2全栈模型无缝衔接；`/docs`自动生成Swagger | Flask（同步为主，类型注解需手动）；Django（过重，ORM无用）；Tornado（异步但文档与生态不如FastAPI）；Starlette（FastAPI的底层，手写路由更多） |
| Web框架 | uvicorn[standard] | 0.30.0 | ASGI服务器 | P0 | FastAPI官方推荐；`--reload`开发体验好 | hypercorn（可替代，但生态更小） |
| **CLI** | **typer** | 0.12.0 | **核心**：子命令、参数解析 | P0 | **类型注解自动生成CLI**，与Pydantic哲学一致；`parajudge run/config`子命令自然映射为`@app.command()` | click（typer底层）；argparse（标准库但样板多） |
| CLI | rich | 13.7.0 | 彩色终端输出 | P1 | 彩色表格/进度条让CLI体验好 | plain text（降级可用） |
| **数据模型** | **pydantic** | 2.5.0 | **核心**：全栈类型安全、JSON序列化 | P0 | **v2使用Rust核心**，比v1快5-50x；FastAPI自动文档+校验；`model_dump_json()`一行持久化 | dataclasses（无运行期校验，序列化需手搓）；TypedDict（纯类型提示，运行期无作用）；attrs（灵活但生态小）；msgspec（轻量但缺少FastAPI自动集成） |
| 数据模型 | pydantic-settings | 2.5.0 | 配置管理（YAML/环境变量） | P0 | 与Pydantic模型同一生态；类型安全的`.env+YAML`加载 | `os.environ`手读（无校验） |
| **LLM调用** | **openai** | 1.40.0 | **核心**：Chat Completions+兼容协议 | P0 | **OpenAI协议是行业事实标准**，vLLM/LM Studio/本地推理均实现兼容端点；`AsyncOpenAI`可异步流式 | Anthropic Claude SDK（单Vendor Lock-in）；Google Gemini SDK（同上）；纯httpx手写（重复造轮子） |
| LLM调用 | dashscope | 1.20.0 | 通义千问SDK | P1 | 中文效果好；阿里生态支持内部部署 | 不装（用OpenAI兼容端点也行） |
| LLM调用 | tiktoken | 0.7.0 | token精确计数（OpenAI系列模型） | P1 | **精确token预算与成本估算**，Moderator时间片控制依赖 | 按字符估算（误差15-30%） |
| **重试** | **tenacity** | 9.0.0 | 指数退避+可配置重试策略 | P0 | **成熟、与async/await原生支持**；LLM调用网络抖动是常态 | 5行for循环手写（不可配置策略） |
| **HTTP客户端** | **httpx** | 0.27.0 | 现代异步HTTPS客户端（外部API调用） | P0 | 同时支持同步/异步；HTTP/2；`async with httpx.AsyncClient()`；代理友好 | requests（仅同步，对异步配合asyncio需线程池，性能差） |
| HTTP客户端 | requests | 2.32.0 | 同步脚本模式 | - | 已有代码兼容 | 仅用httpx即可（requests可逐步移除） |
| **学术检索** | **arxiv** | 2.1.0 | arXiv Python客户端 | P0 | 官方/接近官方的封装，避免手写XML解析 | httpx直连arXiv API+XML解析（样板多） |
| 学术检索 | semanticscholar | 0.5.0 | （可选）Semantic Scholar客户端 | P2 | 元数据更完整（引用数/作者） | 同上 |
| 学术检索 | scholarly | 1.7.11 | （可选）Google Scholar | P3 | 补充谷歌学术来源 | 无稳定官方API |
| 学术检索 | crossref-commons | 0.2.0 | （可选）Crossref客户端 | P2 | DOI元数据查询 | httpx直连Crossref REST API |
| 学术检索 | pyalex | 0.2.0 | （可选）OpenAlex客户端 | P3 | OpenAlex开放索引 | httpx直连 |
| **PDF解析** | **pymupdf** | 1.24.0 | PDF文本/元数据提取 | P1 | **在Python PDF提取中速度/准确性综合最佳** | pypdf（宽松协议但质量差）；pdfplumber（表格强但文本提取速度慢） |
| PDF解析 | pypdf | 5.0.0 | 辅助提取 | P2 | 宽松协议（MIT），用作pymupdf的备份 |  |
| PDF解析 | pdfplumber | 0.11.0 | 表格提取能力强 | P2 | 对"表格型证据"特别有用 |  |
| **Office/文本** | python-docx | 1.1.0 | Word文档解析 | P3 | 解析.docx证据文件 | 无（其他方案无） |
| Office/文本 | markdownify | 0.13.0 | HTML→Markdown转换 | P2 | 网页抓取后转MD便于LLM处理 | 手写HTML→text（丢失格式信息） |
| **HTML/XML** | beautifulsoup4 | 4.12.0 | HTML/XML解析 | P1 | 易用+成熟；结合lxml可高性能 | lxml直接（性能好但API不直观） |
| HTML/XML | lxml | 5.3.0 | 高性能XML解析器 | P1 | beautifulsoup4的lxml backend；XPath支持 | 标准库xml.etree（慢且脆弱） |
| **引用管理** | pyzotero | 1.5.25 | Zotero API | P3 | Zotero文献库整合 | 不装（可选） |
| 引用管理 | bibtexparser | 1.4.1 | .bib文件解析 | P2 | BibTeX导入参考文献 | 手写解析（易错） |
| **环境变量** | python-dotenv | 1.0.0 | `.env`加载 | P0 | **零侵入**加载`.env`到`os.environ` | 手动export（不方便多人开发） |
| **进度条** | tqdm | 4.66.0 | CLI进度显示 | P2 | 简单直观的进度提示 | 可移除 |
| **终端颜色** | colorama | 0.4.6 | Windows颜色兼容 | P2 | Windows终端ANSI兼容 | 非Windows可跳过 |
| **模板渲染** | **Jinja2** | 3.1.0 | **裁决书HTML模板** | P1 | **Python模板事实标准**；语法熟悉；模板继承；过滤器 | React SSR（太重，Node额外依赖）；字符串拼接（不可维护，安全风险大）；纯Markdown（结构与样式弱） |
| **YAML加载** | **PyYAML** | 6.0 | **Domain KB加载器** | P1 | **标准库级成熟**；YAML对人类可读性远好于JSON写长列表 | JSON（括号多，难手写）；TOML（嵌套结构弱） |
| **绘图（可选）** | networkx | 3.3.0 | 论点关系图 | P3 | 图数据结构与可视化 | 手写dict of lists |
| 绘图（可选） | matplotlib | 3.8.0 | 评估结果图表 | P3 | 生成PNG/SVG对比图 | plotly（交互但依赖大） |
| **向量库（可选）** | chromadb | 0.5.0 | 本地向量数据库 | P3 | 本地语义检索，实验性 | faiss（内存中更快，但需额外管理文件） |
| 向量库（可选） | faiss-cpu | 1.8.0 | Facebook AI Similarity Search | P3 | 超大规模相似度搜索（论文10k+时用） |  |
| 向量库（可选） | langchain-chroma | 0.1.4 | LangChain Chroma集成 | P3 | 与LangGraph链组合 | 不装（直接用chromadb） |
| **嵌入（可选）** | sentence-transformers | 3.0.0 | 本地语义嵌入模型 | P3 | **离线/隐私场景下embedding相似度判断**，Moderator质量守门依赖 | 使用远程OpenAI embedding（需联网+成本） |
| **数值工具** | numpy | 1.26.0 | 数值计算/评估统计 | P1 | 与matplotlib/评分统计工具 | 手算（≤50行） |
| **测试（待引入）** | pytest | 8.0 | 测试框架 | P1 | Python社区事实标准 | unittest（标准库但样板多） |
| 测试（待引入） | pytest-asyncio | 0.23 | 异步测试 | P1 | 支持`async def test_*()` | 无 |

---

### 6.3 ADR-006：为什么选择Python 3.10+（对比Node.js / Go / Java）

- **状态**：已采纳（P0，核心）
- **背景**：ParaJudge的核心工作是"学术检索+LLM调用+文本处理+结构化推理链构建"，核心数据量中等（单运行≤1MB），但需要快速原型与可审计。
- **决策**：采用**Python 3.10+（推荐3.11/3.12）**作为首选语言，最低支持3.10（match/case、PEP 604 `X | Y`联合类型、`dataclass(slots=True)`）。
- **后果**：
  - 正：**LangChain/LangGraph/FastAPI/Pydantic/PyTorch生态最强**；学术研究人员上手成本最低；原型→生产路径平滑；`match/case`让Moderator子状态机代码极简洁
  - 负：Python GIL对CPU密集并行不友好（本项目是IO密集，影响小）；运行时类型注解需严格discipline；包管理历史混乱（本项目用标准pip+requirements.txt回避）
- **备选方案对比**：

| 备选语言 | 优点 | 缺点 | 对ParaJudge的适配度 |
|:---|:---|:---|:---|
| **Node.js / TypeScript** | 异步IO强；TypeScript类型系统优秀；Vite/Next.js前端生态 | **LLM代理生态弱于Python**；学术检索PDF/XML解析库少；Node版本碎片化；与LangGraph（Python原生）需跨进程 | ⭐⭐⭐ |
| **Go** | 编译型、性能极高、并发模型goroutine优雅 | **无LangGraph等价生态**；泛型刚成熟但生态小；调试LLM推理链需要大量文本处理的样板代码 | ⭐⭐ |
| **Java / Kotlin** | 强类型、JVM生态企业级成熟 | 原型速度慢；Spring框架重；**学术研究场景社区小**；LLM代理链需大量手写 | ⭐⭐ |
| **Rust** | 内存安全、性能极致 | 学习曲线极陡；**LLM代理生态几乎为零**；开发速度极低 | ⭐ |

- **推荐理由**：ParaJudge的80%工作量都在"调用LLM→解析文本→构建结构化数据"，这正是Python生态的绝对主场。Python 3.10+的match/case与PEP 604让状态机代码可读性显著提升。LangGraph/Pydantic/FastAPI三件套在此版本下表现最佳。

---

### 6.4 ADR-007：为什么选择FastAPI（对比Flask / Django / Tornado / Starlette）

- **状态**：已采纳（P0，核心）
- **背景**：ParaJudge需要一个轻量REST API，用于提交辩论任务、查询进度、下载裁决书。所有输入/输出都是Pydantic模型。
- **决策**：采用**FastAPI 0.111+**作为Web框架。
- **后果**：
  - 正：**ASGI原生异步**（`async def`与LangGraph的`ainvoke`天然匹配）；**Pydantic v2自动集成**（请求/响应模型自动校验+文档）；自动`/docs`（Swagger UI）与`/redoc`；OpenAPI自动生成；性能接近Node.js/Go水平；依赖注入简洁
  - 负：FastAPI是Starlette+Pydantic的上层封装，若需极端自定义Starlette原生可直接降级
- **备选方案对比**：

| 备选 | 优点 | 缺点 |
|:---|:---|:---|
| **Flask** | 简单、学习曲线低 | 同步WSGI为主；异步需事件循环桥接；Pydantic需第三方；自动文档需第三方 |
| **Django** | 全栈、ORM/admin强 | **严重过重**：ORM/admin对ParaJudge无用；同步设计与异步LLM调用链的配合需额外桥接 |
| **Tornado** | 原生异步Web框架 | 生态萎缩；文档与工具链弱于FastAPI；无自动Pydantic集成 |
| **Starlette** | 是FastAPI的底层；完全可控 | 无自动Pydantic；需手写路由与文档；样板代码多 |

- **推荐理由**：FastAPI恰好是"**异步+类型安全+自动文档**"的最小解。对于一个研究型项目来说，它让API代码与LLM异步调用链天然同构，零桥接成本。

---

### 6.5 ADR-008：为什么选择Pydantic v2（对比dataclasses / TypedDict / attrs / msgspec）

- **状态**：已采纳（P0，核心）
- **背景**：ParaJudge全栈需要统一的"输入校验→JSON序列化→FastAPI文档→状态持久化"，必须有一种数据建模标准。
- **决策**：**所有业务数据模型统一继承`pydantic.BaseModel`（Pydantic v2 2.5+）**。
- **后果**：
  - 正：**Rust核心（pydantic-core）**比v1快5-50x；`Annotated`元数据；`Field(..., ge=..., le=...)`字段约束；`model_dump_json()`一行持久化；FastAPI自动Schema；`ConfigDict(extra="forbid")`防止多余字段
  - 负：v1→v2 API已断裂；v3未来可能再次迁移（通过适配层渐进迁移）
- **备选方案对比**：

| 备选 | 优点 | 缺点 |
|:---|:---|:---|
| **dataclasses** | 标准库；零额外依赖 | 无运行期校验；JSON序列化需手搓`asdict()`+`json.dumps`；FastAPI需额外转换 |
| **TypedDict** | 纯类型提示 | 运行期无校验；零运行时效果 |
| **attrs** | 灵活；轻量 | 生态小；FastAPI非原生 |
| **msgspec** | 极快（C扩展）；轻量 | 社区小；生态集成FastAPI需第三方 |

- **推荐理由**：Pydantic v2的"**快+强类型+FastAPI原生**"是唯一让研发效率最高的选项。对于研究型项目，它让数据建模、API校验、持久化三者天然共享同一套Schema，消除了"Model→DTO→JSON"的重复劳动。

---

### 6.6 ADR-009：为什么选择LangGraph作为编排层（深度对比AutoGen / CrewAI / Camel / 自研asyncio状态机 / Prefect & Airflow）

> 扩展原6.5内容，加入**StateGraph vs DAG、parallel node、Checkpointer细节**。

- **状态**：已采纳（P0，核心）
- **背景**：ParaJudge的编排挑战包含**复杂多阶段（Phase 0→1→2.1→2.2）**+**Phase 1内部Moderator五阶段子状态（OPENING_STATEMENTS/CROSS_EXAMINATION/FREE_DEBATE/CLOSING_STATEMENTS/DONE）**+**Phase 2.2需要五位专业法官并行**；整体需要状态持久化与可观察性。
- **决策**：采用**LangGraph StateGraph**作为编排层，使用`add_node()`/`add_edge()`/`add_conditional_edges()`定义路由；使用`parallel node`实现五法官并行；使用**MemorySaver（开发）/SQLiteSaver（生产）**作为Checkpointer。
- **关键技术点**：

| 概念 | 在ParaJudge的用法 |
|:---|:---|
| **StateGraph vs DAG** | DAG（Airflow/Prefect）是**有向无环图**，节点只能单向流动，不可循环；而StateGraph是**状态机**，节点可循环、可条件分支、可回退。ParaJudge的"**辩论循环（N轮，每轮正反发言→Moderator守门→下一轮）**"天然适合StateGraph。DAG无法优雅表达"同一节点多次执行"的情况 |
| **parallel node** | `node_judge_evidence/node_judge_logic/node_judge_principle/node_judge_case/node_judge_innovation`五个节点通过`StateGraph.add_node(..., parallel=True)`（或通过条件边到多个节点同时执行）并行执行，LangGraph的Pregel引擎自动并发调度，输出合并 |
| **Checkpointer** | LangGraph在每个节点执行后自动将state序列化写入SQLite（`data/checkpoints.sqlite`），天然支持**断点续跑**、**从任意节点恢复**、**状态可视化**。传统数据库（PostgreSQL/MongoDB）需要手写schema与序列化，Moderator的子状态需要额外写表与迁移脚本 |
| **条件边（Conditional Edges）** | `current_phase`的值决定"是否进入POI、是否进入Review、是否完成"；Moderator的子状态机也是通过条件边实现"当前子阶段"判断 |

- **后果**：
  - 正：**LangChain生态直接复用**；零成本获得状态图可视化、异步流式接口、Checkpoint断点续跑、Human-in-the-loop可扩展
  - 负：团队需学习LangGraph概念（Pregel/State/Node/Edge/Channel）；0.x版本需严格锁定
- **备选方案深度对比**：

| 方案 | 状态管理 | 并行能力 | 检查点 | 与ParaJudge适配度 | 主要问题 |
|:---|:---|:---|:---|:---|:---|
| **LangGraph**（推荐） | StateGraph状态机；TypedDict/Pydantic state | parallel node原生并行五位法官；线程安全 | MemorySaver/SQLiteSaver自动 | ⭐⭐⭐⭐⭐ | 0.x版本需锁定 |
| **AutoGen** | GroupChat对话式；隐式状态存对话历史 | 通过`max_round`控制；非结构化状态；可并行Agent | 需手动持久化对话 | ⭐⭐⭐ | 微软v0.4架构大改，**结构化流程控制不如LangGraph精细** |
| **CrewAI** | Role/Goal/Tool模式；状态靠`Task.output`管理 | Crew→Task顺序执行；parallel需自定义 | 无内置checkpoint | ⭐⭐⭐ | 更适合任务执行类Agent生态；**辩论-裁决复杂多阶段不够灵活** |
| **Camel** | 角色对话模式；以RolePlaying为核心 | 主要两方对话 | 无 | ⭐⭐ | 偏学术demo；对"五法官并行+多阶段编排"不支持 |
| **自研asyncio状态机** | 完全可控手写state dict/dataclass | `asyncio.gather()`手写并发 | 需手动序列化JSON/数据库 | ⭐⭐ | 从零构建≥3人月工作量；无调试工具；维护成本高 |
| **Prefect / Airflow** | DAG模型；无环 | 任务级并行 | 有任务级 | ⭐⭐ | 偏数据管道调度；对LLM链状态精细控制弱；DAG对"循环辩论"需要hack |

- **推荐理由**：**StateGraph与ParaJudge的"循环辩论+并行裁决"完美契合**。LangGraph的`parallel node`让五位法官并行写≤5行代码实现；Checkpointer让Moderator子状态机断点续跑天然免费。相比之下，AutoGen/CrewAI对结构化流程的控制力显著弱于LangGraph；自研asyncio状态机虽然零外部依赖，但工作量≥3人月且无可视化调试工具；Prefect/Airflow的DAG模型不适合循环型辩论。

---

### 6.7 ADR-010：为什么选择Mock+OpenAI+DashScope多Provider架构（对比Anthropic Claude / Google Gemini / 本地模型Llama/Qwen / 纯单模型）

- **状态**：已采纳（P0）
- **背景**：LLM调用是ParaJudge的核心成本与风险点：价格、可用性、中文效果、隐私合规、速率限制都可能成为单点故障。
- **决策**：采用**`LLMProvider`统一抽象+多Provider实现+配置驱动切换**（MockProvider本地模拟；OpenAIProvider兼容协议；DashScopeProvider通义千问）。
- **后果**：
  - 正：**供应商锁-in解除**；成本/可用性双保险；中文/英文双主模型；开发与CI可完全离线；新增Provider仅需实现子类（≤200行）
  - 负：需维护统一抽象；不同Provider的system prompt行为差异需要适配层
- **备选方案深度对比**：

| 方案 | 中文效果 | 英文效果 | 价格 | 可用性 | 隐私/离线 | 对ParaJudge的适配 |
|:---|:---|:---|:---|:---|:---|:---|
| **纯OpenAI（GPT-4o）** | 中 | 极佳 | 中高 | 较稳定 | 外网；数据外传 | 纯单Vendor Lock-in；中文辩论的中文术语理解差于DashScope |
| **纯Anthropic Claude** | 中 | 极佳 | 高 | 较稳定 | 外网；数据外传 | Prompt长上下文友好；**中国合规风险**（Anthropic中国政策） |
| **纯Google Gemini** | 中 | 极佳 | 中 | 波动 | 外网 | 中国合规风险（Google中国政策） |
| **本地Llama 3 / Qwen 2** | 中（Qwen好） | 好（Llama好） | 低（一次GPU成本） | 极高 | 完全离线/隐私 | **部署与维护成本高**；推理速度慢（70B需≥24GB VRAM）；长上下文能力弱于云端 |
| **多Provider架构（推荐）** | 佳（DashScope） | 佳（OpenAI） | 可按任务选便宜者 | 高（自动切换） | 可配置 | **研究可离线+生产可云端** |

- **推荐理由**：**多Provider架构是研究型项目的最佳实践**。对于中文辩论场景，DashScope在中文术语/案例/原则理解上优于OpenAI；对于英文证据与严谨推理OpenAI更强；Mock Provider让开发/CI彻底离线，消除了LLM调用的单点故障。Provider抽象层让切换成本最低化。

---

### 6.8 ADR-011：为什么选择JSON+YAML文件持久化（对比SQLite / PostgreSQL / MongoDB / Redis）

- **状态**：已采纳（P0）
- **背景**：ParaJudge v0.1.0的数据规模为"每次运行≤1MB的裁决书+状态文件"，频次为单用户研究型，无需高并发。核心操作是"写一次、读多次、版本化、可审计"。
- **决策**：
  - `data/runs/{run_id}/`存放单次运行的`evidence_brief.json`、`argument_index.json`、`final_verdict.json`、`debate_summary.json`、`report.html`/`.md`、`moderation_log.jsonl`
  - `data/domain_kb/*.yaml`存放领域知识库（原则库+案例库）
  - `data/checkpoints.sqlite`（可选）存放LangGraph Checkpointer的SQLite
- **后果**：
  - 正：**零运维成本**；可直接Git版本化管理知识文件；写入瓶颈为磁盘单文件IO，≤100次/分钟完全够用；YAML对人类可读性远好于JSON写长列表
  - 负：并发写入冲突（通过`run_id`隔离，单用户场景无问题）；查询复杂需写脚本（研究场景下通过文件目录+Python脚本轻松解决）
- **备选方案深度对比**：

| 方案 | 优点 | 缺点 | 对ParaJudge的适配度 |
|:---|:---|:---|:---|
| **JSON/YAML文件（推荐）** | 零运维；Git版本化；人类可读YAML；与Pydantic `.model_dump_json()`天然配合 | 无查询索引；并发冲突 | ⭐⭐⭐⭐⭐ |
| **SQLite** | 零服务；单文件；SQL查询能力 | 需要schema迁移；Domain KB YAML仍需额外存储；对本项目数据规模查询优势不明显 | ⭐⭐⭐ |
| **PostgreSQL** | 企业级；强类型；JSONB类型 | 太重（需要Docker或服务守护进程）；运维成本高；对研究型项目过度工程化 | ⭐⭐ |
| **MongoDB** | 文档型；无schema；灵活 | 文档数据库但对JSON结构无强制校验优势；运维成本 | ⭐⭐ |
| **Redis** | 内存缓存极快；键值查询 | 仅缓存不可持久化冷数据（需TTL）；无法审计/版本化 | ⭐ |

- **推荐理由**：**文件系统是最简单、最可审计、最易版本化的持久化方案**。研究型项目的核心数据规模（单运行≤1MB ×数千次运行=数百MB到数GB）完全在单文件IO瓶颈之外。Git管理Domain KB让原则库和案例库天然版本化，便于回溯与评审。

---

### 6.9 ADR-012：为什么选择Jinja2做裁决书（对比HTML字符串拼接 / React SSR / 纯Markdown）

- **状态**：已采纳（P1）
- **背景**：裁决书是"结构化报告"，需`FinalVerdict`→HTML/Markdown双格式输出，内容静态，无复杂交互。核心需求是：模板可维护、样式可定制、输出可分享、可离线查看。
- **决策**：使用**Jinja2模板**渲染HTML；Markdown由Python字符串模板生成；最终同时输出两份文件。
- **后果**：
  - 正：**轻量**（约100-150行模板）；无Node.js依赖；裁决书可离线查看；模板继承与过滤器让表格/列表/条件显示等简洁
  - 负：模板非类型安全（需测试覆盖）；复杂交互不可做（裁决书不需要）
- **备选方案对比**：

| 方案 | 优点 | 缺点 | 适配度 |
|:---|:---|:---|:---|
| **Jinja2（推荐）** | Python事实标准；模板继承；过滤器；可维护 | 非类型安全 | ⭐⭐⭐⭐⭐ |
| **HTML字符串拼接** | 零依赖 | **不可维护**（引号转义地狱）；XSS安全风险；样式不可维护 | ⭐ |
| **React SSR（Next.js）** | 交互强；组件化 | 太重；需要Node.js构建链；离线查看需要打包静态文件 | ⭐⭐ |
| **纯Markdown** | 最简；文本友好 | 结构与样式弱；表格/样式受限；无交互 | ⭐⭐⭐ |

- **推荐理由**：裁决书是"结构化报告"，Jinja2是**轻量+可维护+零额外运行时依赖**的最佳选择。对于研究型项目，裁决书的核心价值是"可审计推理链"与"人类可读性"，Jinja2的模板继承让评审人可专注于内容与逻辑，而非构建链。

---

### 6.10 ADR-013：Moderator质量守门技术选型——为什么用embedding相似度+规则混合（对比纯LLM调用 / 纯关键词 / 向量数据库）

- **状态**：已采纳（P1）
- **背景**：Moderator的核心质量守门包含**重复论点检测**、**主题漂移检测**、**超时控制**三类任务。重复论点需要语义相似度判断；主题漂移需要语义+规则双重检查；超时控制是纯规则。
- **决策**：采用**embedding相似度（sentence-transformers本地模型或OpenAI text-embedding-3-small）+规则混合**的策略：
  - **重复论点检测**：将新论点的embedding与已有论点的embedding做余弦相似度，相似度≥0.85判定为重复；记录到`moderation_log`
  - **主题漂移检测**：规则层（关键词匹配问题statement中的domain关键词覆盖率<30%）+语义层（新论点embedding与problem statement embedding的余弦相似度<0.6）双重判断
  - **超时控制**：纯规则（token计数或时间片预算，记录超预算自动截断）
- **后果**：
  - 正：**成本低**（sentence-transformers本地零成本/OpenAI embedding比LLM调用便宜10-100x）；**速度快**（embedding推理毫秒级 vs LLM秒级）；**可审计**（相似度阈值可配置、可解释、可调）
  - 负：embedding模型对中文术语理解不如LLM；需要维护阈值配置
- **备选方案深度对比**：

| 方案 | 成本 | 速度 | 可解释性 | 对Moderator的适配 |
|:---|:---|:---|:---|:---|
| **embedding+规则混合（推荐）** | 极低（本地零成本/云端`$0.00002/1k token`） | 极快（毫秒级） | 高（相似度阈值可见） | ⭐⭐⭐⭐⭐ |
| **纯LLM调用判断** | 极高（每次发言后调一次LLM `$0.01-0.1`） | 慢（秒级） | 中（LLM解释不可审计） | ⭐⭐ |
| **纯关键词匹配** | 零 | 极快 | 高 | 极低（同义词/转述无法识别） |
| **向量数据库**（Chroma/FAISS） | 中（需额外存储） | 中（索引+查询） | 中 | 对"单运行内重复检测"场景过重（每次运行仅数百论点，向量数据库杀鸡用牛刀） |

- **推荐理由**：**embedding相似度+规则混合是性价比最高的方案**。对于ParaJudge每次运行仅数百论点，本地sentence-transformers模型即可离线零成本完成重复检测；规则层补全主题漂移的强约束；embedding相似度可解释且可调。纯LLM调用成本/速度劣势显著；向量数据库对单运行内重复检测场景杀鸡用牛刀。

---

### 6.11 LangGraph StateGraph架构设计（增强：加入Moderator五阶段子状态机）

> 增强原6.3内容，明确Phase 1内部的Moderator五阶段子状态。

```
顶层状态Schema：
{
  "config": DebateConfig,
  "problem": str,
  "problem_type": str,
  "evidence_brief": EvidenceBrief,
  "debate_state": DebateState,
  "argument_index": ArgumentIndex,
  "moderator_state": {
    "current_subphase": Literal["OPENING_STATEMENTS", "CROSS_EXAMINATION", "FREE_DEBATE", "CLOSING_STATEMENTS", "DONE"],
    "time_budget_used": Dict[agent_id, tokens/seconds],
    "moderation_log": List[ModerationEvent],
    "poi_requests": List[POIRequest],
    "debate_summary": DebateSummary | None
  },
  "review_report": ReviewReport,
  "judge_reports": List[JudgeReport],
  "final_verdict": FinalVerdict,
  "current_phase": Literal["phase0", "phase1", "phase2.1", "phase2.2", "done"]
}

顶层节点定义：
  node_evidence_builder         → 调用 src.knowledge.evidence
  node_problem_classifier       → 调用 src.knowledge.classifier
  node_moderator_orchestrator   → Phase 1的子状态机驱动（见下方子图）
  node_review_prosecutor        → 调用 src.review.prosecutor
  node_review_defense           → 调用 src.review.defense（循环2-3次）
  node_judge_evidence         ┐
  node_judge_logic             │  并行组（LangGraph parallel node）
  node_judge_principle         │  同时执行五位专业法官
  node_judge_case              │
  node_judge_innovation        ┘
  node_final_judge             → 综合裁决官（加权整合+推理链）
  node_report_generator        → 裁决书生成（HTML/MD/JSON）

顶层路由边：
  START → node_evidence_builder → node_problem_classifier
  node_problem_classifier → node_moderator_orchestrator（Phase 1辩论引擎）
  node_moderator_orchestrator → node_review_prosecutor（Phase 2.1）
  node_review_prosecutor → node_review_defense（循环2-3次）
  node_review_defense → [node_judge_evidence, ..., node_judge_innovation]（并行）
  全部法官完成 → node_final_judge → node_report_generator → END

Phase 1子状态机（Moderator五阶段）：
  OPENING_STATEMENTS
    ├─ Coach规划 → 正方Coach制定开场计划
    ├─ 正方Speaker开场 → Moderator守门（重复/漂移/超时）
    ├─ 反方Coach制定开场计划
    └─ 反方Speaker开场 → Moderator守门
           ↓（条件边：subphase → CROSS_EXAMINATION）
  CROSS_EXAMINATION
    ├─ 正方Speaker立论 → Moderator守门
    ├─ 反方发起POI → Moderator批准/延迟/拒绝
    ├─ 反方Speaker立论 → Moderator守门
    └─ 正方发起POI → Moderator批准/延迟/拒绝
           ↓（条件边：subphase → FREE_DEBATE）
  FREE_DEBATE
    ├─ 自由辩论（N轮循环，内部条件边：rounds_remaining > 0 → 继续）
    └─ 每次发言后Moderator守门
           ↓（条件边：subphase → CLOSING_STATEMENTS）
  CLOSING_STATEMENTS
    ├─ 正方总结陈词 → Moderator守门
    └─ 反方总结陈词 → Moderator守门
           ↓（条件边：subphase → DONE）
  DONE
    └─ Moderator生成DebateSummary → 输出到上层节点

Checkpointer（LangGraph内置）：
  · MemorySaver（开发期，内存）
  · SQLiteSaver（生产期，磁盘持久化到 data/checkpoints.sqlite）
  · 支持断点续跑：从任意subphase节点恢复
```

---

### 6.12 MVP启动子集 vs 完整版分层对比（增强：加入Moderator相关条目）

> 明确"**先能跑**"与"**完整能力**"之间的技术栈梯度，避免一次性引入过重依赖。

| 分层 | **MVP启动子集（≈15包，必装）** | **完整版（≈40包，推荐）** | 补齐内容 |
|:---|:---|:---|:---|
| **编排层** | `langgraph==0.2.22`, `langchain-core==0.3.15`, `langchain==0.3.10` | 增加`langchain-openai==0.2.10`, `langchain-community==0.3.0` | OpenAI SDK的LangChain桥接；社区扩展Provider |
| **用户接口层** | `fastapi==0.111.1`, `uvicorn[standard]==0.30.6`, `typer==0.12.5`, `rich==13.7.1` | 增加`Jinja2==3.1.4` | 裁决书HTML渲染（MVP可仅输出纯Markdown） |
| **数据/配置层** | `pydantic==2.9.2`, `pydantic-settings==2.5.2`, `python-dotenv==1.0.1`, `PyYAML==6.0.2` | 不变 | MVP阶段这层已完备；**ModeratorProfile配置模型**（moderator_profile） |
| **LLM调用层** | `openai==1.43.0`（Mock模式可跳过） | 增加`dashscope==1.20.0`, `tiktoken==0.7.0`, **`sentence-transformers==3.0.0`** | 中文模型支持；精确token计数；**Moderator质量守门的本地embedding相似度**（MVP阶段可降级为"纯规则关键词匹配"） |
| **网络/工具层** | `httpx==0.27.2`, `tenacity==9.0.0`, `tqdm==4.66.5` | 增加`requests==2.32.3`, `numpy==1.26.4`, `colorama==0.4.6` | 脚本模式HTTP；评估指标统计；Windows终端彩色兼容 |
| **学术检索层** | `arxiv==2.1.3` | 增加`semanticscholar==0.5.0`, `crossref-commons==0.2.0`, `pyalex==0.2.0` | 三源检索（MVP阶段仅用arXiv也可完成证据构建） |
| **PDF/文档处理层** | 无 | `pymupdf==1.24.10`, `pypdf==5.0.0`, `pdfplumber==0.11.4`, `python-docx==1.1.0`, `beautifulsoup4==4.12.3`, `lxml==5.3.0`, `markdownify==0.13.1` | 增强证据包：上传自定义论文/网页作为证据 |
| **引用管理层** | 无 | `pyzotero==1.5.26`, `bibtexparser==1.4.1` | BibTeX/Zotero导入参考文献 |
| **向量库（P3实验）** | 无 | `chromadb==0.5.0`, `faiss-cpu==1.8.0`, `langchain-chroma==0.1.4`, `sentence-transformers==3.0.0` | 本地语义检索，作为"除了关键词搜索之外的证据增强" |
| **关系图可视化** | 无 | `networkx==3.3`, `matplotlib==3.8.4` | 论点攻击/支持关系可视化；评估结果对比图 |
| **测试/质量** | 无 | `pytest==8.3.2`, `pytest-asyncio==0.23.8`, `pytest-cov==5.0.0`, `ruff==0.6.2`, `mypy==1.11.2` | 单元测试、覆盖率、Lint、类型检查 |
| **Moderator组件（P0）** | **五阶段状态机（MVP：简化为"单轮辩论"）** | **完整五阶段+质量守门+POI批准+DebateSummary** | MVP阶段可简化为"Coach+Speaker单轮，无Moderator守门"；完整版需实现`src/moderator/`模块（状态机、质量守门、POI批准、DebateSummary生成器） |

**MVP阶段的端到端路径（最小闭环，Moderator简化为"单轮辩论"）**：

```
CLI `parajudge run`
  → ProblemClassifier（关键词识别）
  → EvidenceBuilder（仅arXiv检索，构建证据包）
  → Moderator（MVP简化版：OPENING_STATEMENTS一轮发言，无质量守门）
  → JudgmentEngine（2位简化Judges + FinalJudge）
  → ReportGenerator（Markdown输出，跳过Jinja2 HTML）
  → 存入 data/runs/{run_id}/report.md
```

**完整版Moderator模块分解**（v0.2后逐步补齐）：
- `src/moderator/state_machine.py`：五阶段状态机驱动（OPENING_STATEMENTS→CROSS_EXAMINATION→FREE_DEBATE→CLOSING_STATEMENTS→DONE）
- `src/moderator/quality_gate.py`：重复论点检测/主题漂移检测/超时控制
- `src/moderator/poi_approver.py`：POI请求批准/延迟/拒绝决策
- `src/moderator/debate_summary.py`：DebateSummary生成
- `src/moderator/config.py`：ModeratorProfile配置模型

---

### 6.13 依赖→代码模块映射表（增强：加入Moderator相关）

> 让开发者一眼看到"**每个第三方包被哪些代码模块消费**"，便于做依赖精简与影响分析。

| 包/库 | 主要消费模块 | 用途示例 | 影响面（若移出） |
|:---|:---|:---|:---|
| `langgraph` | `src/orchestration/graph.py`, `src/debate/workflow.py`, `src/review/workflow.py`, `src/judgment/judges.py`, **`src/moderator/state_machine.py`** | StateGraph节点定义、parallel node并行法官、Checkpointer状态保存、**Moderator子状态机** | **核心不可移除**；需重写整个编排框架 |
| `langchain-core` | 同上+`src/debate/agent_base.py` | Runnable基类、RunnableSerializable序列化 | 与langgraph绑定，不可独立移除 |
| `fastapi` | `api.py`（全局入口）、`backend/models/schemas.py` | REST路由定义、Request/Response模型自动校验 | 不可移除（除非退回纯CLI） |
| `uvicorn[standard]` | —（通过`uvicorn api:app`启动） | ASGI HTTP服务器 | 不可移除；可替换为hypercorn但收益小 |
| `typer` | `cli.py` | 子命令解析、`--help`自动生成 | 不可移除；可替换为argparse/click但需重写CLI |
| `rich` | `cli.py`、`src/utils/logging_config.py` | 彩色输出、表格、进度条装饰 | 可降级为plain text；但体验下降 |
| `pydantic` | `backend/models/schemas.py`（所有业务模型）、**`src/moderator/config.py`** | DebateConfig、EvidenceBrief、ArgumentIndex、JudgeReport、FinalVerdict、**ModeratorProfile、ModerationEvent、POIRequest、DebateSummary** | **核心不可移除** |
| `pydantic-settings` | `src/utils/config.py`（新增） | 从`.env`+YAML加载结构化配置 | 可退为`os.environ`读取；但丧失类型安全 |
| `python-dotenv` | `api.py`, `cli.py`启动阶段 | 自动load`.env`文件 | 可手动`export X=...`；但不方便 |
| `PyYAML` | `src/knowledge/domain_kb.py` | YAML原则库/案例库加载 | 不可移除（除非改成JSON存知识库） |
| `Jinja2` | `src/judgment/report_generator.py` | 裁决书HTML模板渲染 | MVP阶段可跳过；完整版必需 |
| `openai` | `src/llm/providers.py::OpenAIProvider` | Chat Completions调用（含自托管兼容端点） | Mock Provider存在时可暂不装 |
| `dashscope` | `src/llm/providers.py::DashScopeProvider` | 通义千问调用（中文场景主力） | 中文场景推荐；英文-only可跳过 |
| `tiktoken` | `src/llm/token_counter.py`、**`src/moderator/quality_gate.py`** | OpenAI系列模型的token精确计数、**Moderator时间片token预算控制** | 可降级为"按字符估算"；但成本估算误差大 |
| `httpx` | `src/llm/providers.py`、`src/search/arxiv_client.py`（可选） | 异步HTTPS请求（外部API） | 可换成requests+asyncio，但httpx更现代 |
| `tenacity` | `src/llm/retry.py` | 指数退避重试（LLM网络抖动时自动重试） | 可退为自写5行`for i in range(3)`；但丧失策略可配置性 |
| `requests` | 脚本/CLI辅助 | 简单同步请求 | 可只装httpx；requests仅为兼容已有代码 |
| `arxiv` | `src/search/arxiv_client.py` | arXiv API客户端（封装了HTTP/XML） | 可退为httpx直连arXiv API；但需要手写XML解析 |
| `pymupdf` | `src/parse/pdf_parser.py` | PDF文本/元数据/标题提取 | MVP可跳过；仅在"用户上传自定义PDF"时需要 |
| `numpy` | `src/judgment/`评估统计逻辑 | 评分均值/标准差/加权 | 可手算；但1MB的包不值得精简 |
| `tqdm` | `cli.py` | 进度提示条 | 可移除；体验下降 |
| `sentence-transformers` | **`src/moderator/quality_gate.py`** | **本地语义嵌入模型；重复论点检测/主题漂移检测的embedding相似度计算** | MVP阶段可降级为"纯规则关键词匹配" |
| `networkx` | `src/debate/argument_index.py`（可选） | 论点关系图（攻击/支持/中立） | P3；可推迟到v0.2 |
| `matplotlib` | `experiments/`（评估脚本） | 多系统对比图、评分曲线图 | P3；纯开发工具 |
| `pytest`/`pytest-asyncio` | `tests/`（新增目录） | 单元测试、异步测试 | 非运行时依赖；但CI必需 |
| `ruff` | —（开发期lint/format工具） | 统一代码风格 | 开发工具；对运行无影响 |

---

### 6.14 技术栈风险热图（新增）

> 用"概率×影响"二维热图可视化各技术的风险等级，便于评审与缓解策略优先级排序。

**风险等级定义**：
- **🟥 高风险**：概率≥70% 或 影响≥高
- **🟧 中风险**：概率30-70% 且 影响中
- **🟨 低风险**：概率≤30% 或 影响≤低

| # | 风险项 | 概率 | 影响 | 等级 | 缓解策略/备选方案 |
|:---|:---|:---|:---|:---|:---|
| R1 | **LangGraph版本变更/0.x API变动** | 中 | 中 | 🟧 | 严格锁定`langgraph==0.2.22`+`langchain-core==0.3.15`；重要API封装在`src/orchestration/adapters.py`适配层，变更只影响适配层 |
| R2 | **OpenAI API价格/可用性/政策变更** | 中 | 高 | 🟥 | 1. **多Provider架构（Mock/OpenAI/DashScope）**；2. Mock Provider保证开发不受外部影响；3. token预算控制（FR-607）；4. 降级策略（失败自动切换） |
| R3 | **Pydantic v2→v3迁移** | 低 | 中 | 🟨 | 当前使用v2，稳定；如v3发布，通过`src/models/adapters.py`适配层渐进迁移 |
| R4 | **PDF解析依赖过重/协议风险** | 低 | 低 | 🟨 | 已有pymupdf/pypdf/pdfplumber三种可选；PDF非核心流程，降级不影响辩论功能 |
| R5 | **asyncio复杂度/并发模型学习曲线** | 中 | 中 | 🟧 | Phase 1用同步实现；Phase 2起逐步引入asyncio；FastAPI的`async def`天然支持异步Handler；`asyncio.run()`封装 |
| R6 | **第三方检索API稳定性（arXiv/Semantic Scholar）** | 中 | 低 | 🟧 | 多源检索天然容错；某个检索源失败时自动降级为"仅使用其他可用源"，并在日志中记录 |
| R7 | **sentence-transformers本地模型资源占用** | 低 | 低 | 🟨 | 本地模型仅在Moderator质量守门时使用；可配置为"使用OpenAI text-embedding-3-small远端embedding"；或降级为"纯规则关键词匹配" |
| R8 | **Jinja2模板安全（XSS/模板注入）** | 低 | 中 | 🟨 | 裁决书为离线静态文件；模板渲染时使用`{{ variable | e }}`自动转义；模板文件不接受用户输入 |
| R9 | **Domain KB YAML解析异常** | 低 | 低 | 🟨 | 使用`pydantic.BaseModel`严格校验YAML结构；加载失败时给出明确错误信息（文件名+字段名+期望类型）；`ruff-yamllint`可选格式检查 |
| R10 | **Moderator质量守门阈值误判（重复论点漏判/主题漂移误判）** | 中 | 中 | 🟧 | 阈值通过`ModeratorProfile`可配置；embedding相似度+规则双重检查；在测试集上做阈值调参；moderation_log记录每一条判决便于后续review |
| R11 | **DashScope合规/中国云服务政策变更** | 低 | 中 | 🟨 | **多Provider架构**天然缓解；中文场景可随时切回OpenAI兼容协议或本地模型 |
| R12 | **FastAPI/uvicorn CVE安全更新** | 低 | 中 | 🟨 | 严格锁定版本；`pip-audit`定期扫描；升级前CI测试 |

**风险热图矩阵（概率×影响）**：

```
          低影响         中影响         高影响
高概率    🟨 R7,R9   🟧 R1,R5,R10 🟥 R2
中概率    🟨 R4        🟧 R6,R3   —
低概率    🟨 —         🟨 R8,R11,R12 —
```

**总体风险评价**：**中低风险**。最高风险项R2（OpenAI可用性/价格）通过多Provider架构已显著缓解；其余风险项均在"中或更低"，且大部分缓解策略已在当前设计中内置。

---

**第1部分结束**。第2部分（接口需求+外部服务+设计约束+验收标准+参考实现位置）见`docs/SRS_02_接口与验证.md`。
