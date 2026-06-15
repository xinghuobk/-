# ParaJudge 多智能体辩论系统 — 软件需求规格说明书 (SRS)

## 第 1 部分：引言 + 总体描述 + 功能需求 + 非功能需求 + 数据模型 + 详细技术栈

> **项目代号**：ParaJudge
> **文档版本**：v1.0
> **生成日期**：2026-06-15
> **设计依据**：基于 259 篇 MAD 领域论文 + 5 篇系统性综述的分析结果

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
- 检察官-辩护律师审理（Prosecutor-Defense Review）
- 五维专业化法官裁决（5-Dimension Specialized Judges）
- 创新保护机制（Innovation Protection）
- 类判决书推理链输出（Judgment-Style Reasoning Chain）

### 1.3 定义与缩略语

| 缩写 | 定义 |
|:---|:---|
| **MAD** | Multi-Agent Debate，多智能体辩论 |
| **Agent** | 具有特定目标的 LLM 智能体，在 LangGraph 中表现为一个节点 |
| **POI** | Point of Information，段间质询 |
| **Evidence Brief** | 辩论前构建的统一证据包（所有辩论必须引用其中条目） |
| **Domain KB** | 领域知识库（原则库 + 案例库） |

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

### 6.2 各层依赖详表

| 分层 | 包名 | 最低版本 | 用途 | P 级别 | 现有状态 |
|:---|:---|:---|:---|:---|:---|
| **编排层** | **langgraph** | 0.2.0 | **核心**：StateGraph 工作流编排、并行节点、Checkpointer | P0 | 待引入 |
| 编排层 | langchain | 0.3.0 | Runnable 抽象、Agent 模板 | P0 | `requirements.txt` 已有 |
| 编排层 | langchain-core | 0.3.0 | 核心抽象 | P0 | 已有 |
| 编排层 | langchain-openai | 0.2.0 | OpenAI 兼容 Provider 集成 | P0 | 已有 |
| 编排层 | langchain-community | 0.3.0 | 社区 Provider 扩展 | P1 | 已有 |
| **Web 框架** | **fastapi** | 0.111.0 | **核心**：REST API、类型安全、自动文档 | P0 | 已有 |
| Web 框架 | uvicorn[standard] | 0.30.0 | ASGI 服务器 | P0 | 已有 |
| **CLI** | **typer** | 0.12.0 | **核心**：子命令、参数解析 | P0 | 已有 |
| CLI | rich | 13.7.0 | 彩色终端输出 | P1 | 已有 |
| **数据模型** | **pydantic** | 2.5.0 | **核心**：全栈类型安全、JSON 序列化 | P0 | 已有（2.x） |
| 数据模型 | pydantic-settings | 2.5.0 | 配置管理（YAML/环境变量） | P0 | 已有 |
| **LLM 调用** | **openai** | 1.40.0 | **核心**：Chat Completions + 兼容协议 | P0 | 已有 |
| LLM 调用 | dashscope | 1.20.0 | 通义千问 SDK | P1 | 已有 |
| LLM 调用 | tiktoken | 0.7.0 | token 精确计数（OpenAI 系列模型） | P1 | 待引入 |
| **重试** | **tenacity** | 9.0.0 | 指数退避 + 可配置重试策略 | P0 | 已有 |
| **HTTP 客户端** | **httpx** | 0.27.0 | 现代异步 HTTPS 客户端（外部 API 调用） | P0 | 已有 |
| HTTP 客户端 | requests | 2.32.0 | 同步脚本模式 | - | 已有 |
| **学术检索** | **arxiv** | 2.1.0 | arXiv Python 客户端 | P0 | 已有 |
| 学术检索 | semanticscholar | 0.5.0 | （可选）Semantic Scholar 客户端 | P2 | 已有 |
| 学术检索 | scholarly | 1.7.11 | （可选）Google Scholar | P3 | 已有 |
| 学术检索 | crossref-commons | 0.2.0 | （可选）Crossref 客户端 | P2 | 已有 |
| 学术检索 | pyalex | 0.2.0 | （可选）OpenAlex 客户端 | P3 | 已有 |
| **PDF 解析** | **pymupdf** | 1.24.0 | PDF 文本 / 元数据提取 | P1 | 已有 |
| PDF 解析 | pypdf | 5.0.0 | 辅助提取 | P2 | 已有 |
| PDF 解析 | pdfplumber | 0.11.0 | 表格提取能力强 | P2 | 已有 |
| **Office / 文本** | python-docx | 1.1.0 | Word 文档解析 | P3 | 已有 |
| Office / 文本 | markdownify | 0.13.0 | HTML → Markdown 转换 | P2 | 已有 |
| **HTML/XML** | beautifulsoup4 | 4.12.0 | HTML/XML 解析 | P1 | 已有 |
| HTML/XML | lxml | 5.3.0 | 高性能 XML 解析器 | P1 | 已有 |
| **引用管理** | pyzotero | 1.5.25 | Zotero API | P3 | 已有 |
| 引用管理 | bibtexparser | 1.4.1 | .bib 文件解析 | P2 | 已有 |
| **环境变量** | python-dotenv | 1.0.0 | `.env` 加载 | P0 | 已有 |
| **进度条** | tqdm | 4.66.0 | CLI 进度显示 | P2 | 已有 |
| **终端颜色** | colorama | 0.4.6 | Windows 颜色兼容 | P2 | 已有 |
| **模板渲染** | **Jinja2** | 3.1.0 | **裁决书 HTML 模板** | P1 | 待显式声明 |
| **YAML 加载** | **PyYAML** | 6.0 | **Domain KB 加载器** | P1 | 待显式引入 |
| **绘图（可选）** | networkx | 3.3.0 | 论点关系图 | P3 | 已有 |
| 绘图（可选） | matplotlib | 3.8.0 | 评估结果图表 | P3 | 已有 |
| **向量库（可选）** | chromadb | 0.5.0 | 本地向量数据库 | P3 | 已有 |
| 向量库（可选） | faiss-cpu | 1.8.0 | Facebook AI Similarity Search | P3 | 已有 |
| 向量库（可选） | langchain-chroma | 0.1.4 | LangChain Chroma 集成 | P3 | 已有 |
| **嵌入（可选）** | sentence-transformers | 3.0.0 | 本地语义嵌入模型 | P3 | 已有 |
| **数值工具** | numpy | 1.26.0 | 数值计算 / 评估统计 | P1 | 已有 |
| **测试（待引入）** | pytest | 8.0 | 测试框架 | P1 | 待引入 |
| 测试（待引入） | pytest-asyncio | 0.23 | 异步测试 | P1 | 待引入 |

### 6.3 LangGraph StateGraph 架构设计（关键）

```
状态 Schema：
{
  "config": DebateConfig,
  "problem": str,
  "problem_type": str,
  "evidence_brief": EvidenceBrief,
  "debate_state": DebateState,
  "argument_index": ArgumentIndex,
  "review_report": ReviewReport,
  "judge_reports": List[JudgeReport],
  "final_verdict": FinalVerdict,
  "current_phase": Literal["phase0", "phase1", "phase2.1", "phase2.2", "done"]
}

节点定义：
  node_evidence_builder       → 调用 src.knowledge.evidence
  node_problem_classifier      → 调用 src.knowledge.classifier
  node_debate_coach            → 调用 src.debate.coach（正反双方 Coach）
  node_debate_speakers         → 调用 src.debate.speaker（内部循环 N 轮）
  node_poi_engine              → 调用 src.debate.poi_engine（条件：enable_poi）
  node_review_prosecutor       → 调用 src.review.prosecutor
  node_review_defense          → 调用 src.review.defense（循环 2-3 次）
  node_judge_evidence          ┐
  node_judge_logic             │  并行组（LangGraph parallel node）
  node_judge_principle         │  同时执行五位专业法官
  node_judge_case              │
  node_judge_innovation        ┘
  node_final_judge             → 综合裁决官（加权整合 + 推理链）
  node_report_generator        → 裁决书生成（HTML/MD/JSON）

路由边：
  START → node_evidence_builder → node_problem_classifier
  node_problem_classifier → node_debate_coach
  node_debate_coach → node_debate_speakers（循环 N 次，内部状态推进）
  node_debate_speakers → node_poi_engine（条件：enable_poi=True）
  node_poi_engine → node_review_prosecutor（或直接跳过）
  node_review_prosecutor → node_review_defense（循环 2-3 次）
  node_review_defense → [node_judge_evidence, ..., node_judge_innovation]（并行）
  全部法官完成 → node_final_judge → node_report_generator → END

Checkpointer（LangGraph 内置）：
  · MemorySaver（开发期，内存）
  · SQLiteSaver（生产期，磁盘持久化到 data/checkpoints.sqlite）
```

### 6.4 与现有代码的衔接策略

| 现有模块 | 作用 | 改造动作 |
|:---|:---|:---|
| `src/search/arxiv_client.py` + `semantic_scholar_client.py` + `crossref_client.py` | 学术检索 | **保持不变**，作为 EvidenceBuilder 的底层调用 |
| `src/search/engine.py::unified_search` | 多源检索统一入口 | **保持不变**，由 EvidenceBuilder 调用 |
| `src/parse/pdf_parser.py` | PDF 提取 | 保留，可选用于 EvidenceBuilder 的"自定义 PDF 上传"增强 |
| `src/reference/bibtex_manager.py` | BibTeX 解析 | 保留，用于 Evidence Brief 中的引用格式化 |
| `src/writer/llm_helper.py` | 写作辅助 | 保留，可选用于裁决书润色 |
| `backend/models/schemas.py` | Pydantic 数据模型 | **扩展**：新增 EvidenceItem/ArgumentIndex/ReviewReport/JudgeReport/FinalVerdict/DomainKB 等 |
| `cli.py` | CLI 入口 | **扩展**：新增 `parajudge` 子命令组 |
| `api.py` | FastAPI 入口 | **扩展**：新增 `/api/v1/parajudge/*` 路由 |
| `requirements.txt` | 依赖清单 | **扩展**：显式声明 `Jinja2`、`PyYAML`、`tiktoken`、`pytest` |
| `.env.example` | 环境变量模板 | **扩展**：增加 ParaJudge 专用配置（DASHSCOPE_API_KEY 等） |

### 6.5 引入 LangGraph 的理由（与替代方案对比）

| 方案 | 优点 | 缺点 | ParaJudge 推荐度 |
|:---|:---|:---|:---|
| **LangGraph**（推荐） | 1. StateGraph 原生支持状态管理；2. parallel node 天然支持五法官并行；3. Checkpointer 免费获得状态持久化；4. 与 LangChain 生态深度集成；5. 可视化调试工具 | 1. 有学习曲线；2. 版本尚在 0.x（但已稳定使用） | ⭐⭐⭐⭐⭐ **核心推荐** |
| **AutoGen** | 1. 多 Agent 对话模式成熟；2. 内置工具调用 | 1. 对结构化流程的控制不如 LangGraph 精细；2. 微软重写中（v0.4 架构变动大） | ⭐⭐⭐（备选） |
| **CrewAI** | 1. Role/Goal/Tool 模式直观；2. 文档友好 | 1. 适合任务执行，对辩论-裁决这种复杂多阶段不够灵活 | ⭐⭐（备选） |
| **自研编排（asyncio 状态机）** | 1. 完全可控；2. 零外部依赖 | 1. 需要从零构建并行/检查点/调度等；2. 维护成本高；3. 无可视化/调试工具 | ⭐⭐（仅在极端约束下考虑） |

**关键决策**：采用 **LangGraph** 作为编排层（已写入 P0）。原因：五法官并行评估的场景几乎与 LangGraph 的 parallel node 设计完美契合；状态管理复杂多阶段流程（Phase 0/1/2.1/2.2）时可以渐进式实现。

### 6.6 关键版本锁定（确保可复现）

```
# 严格锁定核心版本（避免不兼容升级）
langgraph==0.2.22           # 编排层（当前较新的稳定 0.2.x）
langchain==0.3.10            # LangChain 主包
langchain-core==0.3.15       # 核心抽象（非常重要，需与 langgraph 兼容）
langchain-openai==0.2.10     # OpenAI 集成
fastapi==0.111.1             # Web 框架
uvicorn[standard]==0.30.6    # ASGI
pydantic==2.9.2              # 数据模型
pydantic-settings==2.5.2     # 配置管理
openai==1.43.0               # OpenAI SDK
httpx==0.27.2                # 异步 HTTP
tenacity==9.0.0              # 重试
typer==0.12.5                # CLI
rich==13.7.1                 # 彩色终端
Jinja2==3.1.4                # 裁决书模板
PyYAML==6.0.2                # Domain KB 加载器
tiktoken==0.7.0              # Token 计数
python-dotenv==1.0.1         # .env 加载
tqdm==4.66.5                 # 进度条
requests==2.32.3             # 同步 HTTP
arxiv==2.1.3                 # arXiv 客户端
pymupdf==1.24.10             # PDF 解析
numpy==1.26.4                # 数值工具

# 开发依赖（可选）
pytest==8.3.2                # 测试框架
pytest-asyncio==0.23.8       # 异步测试
ruff==0.6.2                  # lint + format
```

### 6.7 技术栈风险与备选方案

| 风险 | 概率 | 影响 | 缓解策略 / 备选方案 |
|:---|:---|:---|:---|
| **LangGraph 版本变更** | 中 | 中 | 严格锁定 `langgraph==0.2.22` + `langchain-core==0.3.15`；重要 API 封装在 `src/llm/` 适配层，变更只影响适配层 |
| **OpenAI API 价格 / 可用性** | 中 | 高 | 1. 支持 DashScope 作为主力中文模型；2. Mock Provider 保证开发不受外部影响；3. token 预算控制（FR-607） |
| **PDF 解析依赖过重** | 低 | 低 | 已有 pymupdf / pypdf / pdfplumber 三种可选；PDF 非核心流程，降级不影响辩论功能 |
| **asyncio 复杂度** | 中 | 中 | Phase 1 用同步实现；Phase 2 起逐步引入 asyncio；FastAPI 的 `async def` 天然支持异步 Handler |
| **Pydantic v2 vs v3 迁移** | 低 | 中 | 当前使用 v2，稳定；如 v3 发布，通过适配层渐进迁移 |
| **第三方检索 API 稳定性** | 中 | 低 | 多源检索天然容错；某个检索源失败时自动降级为"仅使用其他可用源"，并在日志中记录 |

---

### 6.8 关键技术选型决策记录（ADR 风格）

> 本小节记录对架构有长期影响的核心决策，便于后续回溯与变更管理。每条记录格式：**标题 / 状态 / 背景 / 决策 / 后果 / 备选**。

#### ADR-001：使用 LangGraph 作为编排层（而非 AutoGen / CrewAI / 自研状态机）

- **状态**：已采纳（P0，核心）
- **背景**：ParaJudge 是四阶段工作流（Phase 0 → 1 → 2.1 → 2.2），最后阶段需 5 位 Judges 并行评估，整体需状态持久化与可观察性。
- **决策**：采用 LangGraph StateGraph，使用 `parallel node` 实现五法官并行，使用内置 MemorySaver / SQLiteSaver 作为 Checkpointer。
- **后果**：
  - 正：LangChain 生态直接复用，零成本获得状态图可视化、异步流式接口、Checkpoint 断点续跑
  - 负：团队需学习 LangGraph 概念（Pregel / State / Node / Edge）；0.x 版本需严格锁定
- **备选**：AutoGen（对话模式强，但结构化流程控制弱）、CrewAI（Role/Goal 直观，但状态持久化弱）、自研 asyncio 状态机（零外部依赖，但工作量 ≥ 3 人月）

#### ADR-002：使用 Pydantic v2 作为全栈数据模型标准

- **状态**：已采纳（P0，核心）
- **背景**：辩论状态、论点索引、裁决书、证据包等均需 JSON 序列化、类型校验、FastAPI 自动文档生成。
- **决策**：所有业务数据结构统一继承 `pydantic.BaseModel`，禁止使用 `dict` 直接传递结构化数据。
- **后果**：
  - 正：编译期类型检查 + 运行期校验；FastAPI 自动生成 Schema 文档；可直接 `model_dump_json()` 持久化
  - 负：Pydantic v1/v2/v3 之间 API 存在差异，需长期锁定版本（当前 v2.9.2）
- **备选**：dataclass（序列化能力弱）、TypedDict（无运行期校验）、Msgspec（轻量但生态小）

#### ADR-003：LLM 调用通过统一 Provider 抽象（非直接调用 SDK）

- **状态**：已采纳（P0）
- **背景**：直接在 Agent 代码中调用 `openai.ChatCompletion` 或 `dashscope.Generation` 会导致"代码与 SDK 强耦合"，切换模型需大面积改动。
- **决策**：在 `src/llm/providers.py` 中定义 `LLMProvider` 基类（含 `chat(prompt, **kwargs)` / `astream(prompt, **kwargs)`），并实现 MockProvider / OpenAIProvider / DashScopeProvider。所有 Agent 只调用该基类接口。
- **后果**：新增 Provider 只需实现子类（≤ 200 行）；Mock Provider 让开发与 CI 彻底离线可运行；真实模型切换通过配置文件即可。
- **备选**：直接调用 openai SDK（耦合重）、通过 LangChain ChatModel 封装（与 LangChain 强绑定，LangChain 本身也可能迁移）

#### ADR-004：持久化采用文件系统（JSON + YAML），而非数据库

- **状态**：已采纳（P0）
- **背景**：ParaJudge v0.1.0 的数据规模为"每次运行 ≤ 1MB 的裁决书 + 状态文件"，频次为单用户研究型，无需高并发。
- **决策**：
  - `data/runs/{run_id}/` 存放单次运行的 evidence_brief.json、argument_index.json、final_verdict.json、report.html / .md
  - `data/domain_kb/*.yaml` 存放领域知识库
  - `data/checkpoints.sqlite`（可选）存放 LangGraph Checkpointer 的 SQLite
- **后果**：零运维成本、可直接 Git 版本化管理知识文件；写入瓶颈为磁盘单文件 IO，≤ 100 次/分钟完全够用。
- **备选**：PostgreSQL（太重量级）、MongoDB（文档型，但对 JSON 结构无强制校验优势）、Redis（仅缓存，不可持久化冷数据）

#### ADR-005：裁决书渲染采用 Jinja2（而非 React/Vue 前端）

- **状态**：已采纳（P1）
- **背景**：裁决书是"结构化报告"，需 JSON → HTML / Markdown 双格式输出，内容静态，无复杂交互。
- **决策**：使用 Jinja2 模板渲染 HTML；Markdown 由 Python 字符串模板生成；最终同时输出两份文件。
- **后果**：轻量（约 100-150 行模板）；无 Node.js 依赖；裁决书可离线查看。
- **备选**：React SPA（过重，且需额外构建链）、Rich 终端输出（仅 CLI 友好，不可分享）

---

### 6.9 MVP 启动子集 vs 完整版分层对比

> 明确"**先能跑**"与"**完整能力**"之间的技术栈梯度，避免一次性引入过重依赖。

| 分层 | **MVP 启动子集（≈ 15 包，必装）** | **完整版（≈ 40 包，推荐）** | 补齐内容 |
|:---|:---|:---|:---|
| **编排层** | `langgraph==0.2.22`, `langchain-core==0.3.15`, `langchain==0.3.10` | 增加 `langchain-openai==0.2.10`, `langchain-community==0.3.0` | OpenAI SDK 的 LangChain 桥接；社区扩展 Provider |
| **用户接口层** | `fastapi==0.111.1`, `uvicorn[standard]==0.30.6`, `typer==0.12.5`, `rich==13.7.1` | 增加 `Jinja2==3.1.4` | 裁决书 HTML 渲染（MVP 可仅输出纯 Markdown） |
| **数据 / 配置层** | `pydantic==2.9.2`, `pydantic-settings==2.5.2`, `python-dotenv==1.0.1`, `PyYAML==6.0.2` | 不变 | MVP 阶段这层已完备 |
| **LLM 调用层** | `openai==1.43.0`（Mock 模式可跳过） | 增加 `dashscope==1.20.0`, `tiktoken==0.7.0` | 中文模型支持；精确 token 计数 |
| **网络 / 工具层** | `httpx==0.27.2`, `tenacity==9.0.0`, `tqdm==4.66.5` | 增加 `requests==2.32.3`, `numpy==1.26.4`, `colorama==0.4.6` | 脚本模式 HTTP；评估指标统计；Windows 终端彩色兼容 |
| **学术检索层** | `arxiv==2.1.3` | 增加 `semanticscholar==0.5.0`, `crossref-commons==0.2.0`, `pyalex==0.2.0` | 三源检索（MVP 阶段仅用 arXiv 也可完成证据构建） |
| **PDF / 文档处理层** | 无 | `pymupdf==1.24.10`, `pypdf==5.0.0`, `pdfplumber==0.11.4`, `python-docx==1.1.0`, `beautifulsoup4==4.12.3`, `lxml==5.3.0`, `markdownify==0.13.1` | 增强证据包：上传自定义论文/网页作为证据 |
| **引用管理层** | 无 | `pyzotero==1.5.26`, `bibtexparser==1.4.1` | BibTeX / Zotero 导入参考文献 |
| **向量库（P3 实验）** | 无 | `chromadb==0.5.0`, `faiss-cpu==1.8.0`, `langchain-chroma==0.1.4`, `sentence-transformers==3.0.0` | 本地语义检索，作为"除了关键词搜索之外的证据增强" |
| **关系图可视化** | 无 | `networkx==3.3`, `matplotlib==3.8.4` | 论点攻击/支持关系可视化；评估结果对比图 |
| **测试 / 质量** | 无 | `pytest==8.3.2`, `pytest-asyncio==0.23.8`, `pytest-cov==5.0.0`, `ruff==0.6.2`, `mypy==1.11.2` | 单元测试、覆盖率、Lint、类型检查 |

**MVP 阶段的端到端路径（最小闭环）：**

```
CLI `parajudge run` 
  → ProblemClassifier（关键词识别）
  → EvidenceBuilder（仅 arXiv 检索，构建证据包）
  → DebateEngine（1 Coach + 2 Speakers 正反，1 轮辩论）
  → JudgmentEngine（2 位简化 Judges + FinalJudge）
  → ReportGenerator（Markdown 输出，跳过 Jinja2 HTML）
  → 存入 data/runs/{run_id}/report.md
```

---

### 6.10 依赖 → 代码模块的映射表

> 让开发者一眼看到"**每个第三方包被哪些代码模块消费**"，便于做依赖精简与影响分析。

| 包 / 库 | 主要消费模块 | 用途示例 | 影响面（若移出） |
|:---|:---|:---|:---|
| `langgraph` | `src/orchestration/graph.py`, `src/debate/workflow.py`, `src/review/workflow.py`, `src/judgment/judges.py` | StateGraph 节点定义、parallel node 并行法官、Checkpointer 状态保存 | **核心不可移除**；需重写整个编排框架 |
| `langchain-core` | 同上 + `src/debate/agent_base.py` | Runnable 基类、RunnableSerializable 序列化 | 与 langgraph 绑定，不可独立移除 |
| `fastapi` | `api.py`（全局入口）、`backend/models/schemas.py` | REST 路由定义、Request/Response 模型自动校验 | 不可移除（除非退回纯 CLI） |
| `uvicorn[standard]` | —（通过 `uvicorn api:app` 启动） | ASGI HTTP 服务器 | 不可移除；可替换为 hypercorn 但收益小 |
| `typer` | `cli.py` | 子命令解析、`--help` 自动生成 | 不可移除；可替换为 argparse/click 但需重写 CLI |
| `rich` | `cli.py`、`src/utils/logging_config.py` | 彩色输出、表格、进度条装饰 | 可降级为 plain text；但体验下降 |
| `pydantic` | `backend/models/schemas.py`（所有业务模型） | DebateConfig、EvidenceBrief、ArgumentIndex、JudgeReport、FinalVerdict | **核心不可移除** |
| `pydantic-settings` | `src/utils/config.py`（新增） | 从 `.env` + YAML 加载结构化配置 | 可退为 `os.environ` 读取；但丧失类型安全 |
| `python-dotenv` | `api.py`, `cli.py` 启动阶段 | 自动 load `.env` 文件 | 可手动 `export X=...`；但不方便 |
| `PyYAML` | `src/knowledge/domain_kb.py` | YAML 原则库 / 案例库加载 | 不可移除（除非改成 JSON 存知识库） |
| `Jinja2` | `src/judgment/report_generator.py` | 裁决书 HTML 模板渲染 | MVP 阶段可跳过；完整版必需 |
| `openai` | `src/llm/providers.py::OpenAIProvider` | Chat Completions 调用（含自托管兼容端点） | Mock Provider 存在时可暂不装 |
| `dashscope` | `src/llm/providers.py::DashScopeProvider` | 通义千问调用（中文场景主力） | 中文场景推荐；英文-only 可跳过 |
| `tiktoken` | `src/llm/token_counter.py` | OpenAI 系列模型的 token 精确计数 | 可降级为"按字符估算"；但成本估算误差大 |
| `httpx` | `src/llm/providers.py`、`src/search/arxiv_client.py`（可选） | 异步 HTTPS 请求（外部 API） | 可换成 requests + asyncio，但 httpx 更现代 |
| `tenacity` | `src/llm/retry.py` | 指数退避重试（LLM 网络抖动时自动重试） | 可退为自写 5 行 `for i in range(3)`；但丧失策略可配置性 |
| `requests` | 脚本 / CLI 辅助 | 简单同步请求 | 可只装 httpx；requests 仅为兼容已有代码 |
| `arxiv` | `src/search/arxiv_client.py` | arXiv API 客户端（封装了 HTTP/XML） | 可退为 httpx 直连 arXiv API；但需要手写 XML 解析 |
| `pymupdf` | `src/parse/pdf_parser.py` | PDF 文本 / 元数据 / 标题提取 | MVP 可跳过；仅在"用户上传自定义 PDF"时需要 |
| `numpy` | `src/judgment/` 评估统计逻辑 | 评分均值 / 标准差 / 加权 | 可手算；但 1MB 的包不值得精简 |
| `tqdm` | `cli.py` | 进度提示条 | 可移除；体验下降 |
| `networkx` | `src/debate/argument_index.py`（可选） | 论点关系图（攻击 / 支持 / 中立） | P3；可推迟到 v0.2 |
| `matplotlib` | `experiments/`（评估脚本） | 多系统对比图、评分曲线图 | P3；纯开发工具 |
| `pytest` / `pytest-asyncio` | `tests/`（新增目录） | 单元测试、异步测试 | 非运行时依赖；但 CI 必需 |
| `ruff` | —（开发期 lint / format 工具） | 统一代码风格 | 开发工具；对运行无影响 |

---

**第 1 部分结束**。第 2 部分（接口需求 + 外部服务 + 设计约束 + 验收标准 + 参考实现位置）见 `docs/SRS_02_接口与验证.md`。
