# ParaJudge 需求分析与技术栈文档索引

> **生成日期**: 2026-06-15

---

## 目录

1. [新增文档清单](#1-新增文档清单)
2. [需求分析与技术栈的核心结论](#2-需求分析与技术栈的核心结论)
3. [下一步动作清单](#3-下一步动作清单)
4. [实现优先级与依赖关系图](#4-实现优先级与依赖关系图)

---

## 1. 新增文档清单

以下是本次任务生成/更新的文档列表，全部位于 `docs/` 目录与项目根目录：

| 序号 | 文件路径 | 类型 | 说明 | 大小（约） |
|:---|:---|:---|:---|:---|
| 1 | [`PARAJUDGE_DESIGN_REPORT.md`](docs/PARAJUDGE_DESIGN_REPORT.md) | **核心** | ParaJudge 四阶段设计理念 + 架构图 + 24 周里程碑 + 7 个技术空白 | 15KB / 约 400 行 |
| 2 | [`SRS_01_Introduction_And_TechStack.md`](docs/SRS_01_Introduction_And_TechStack.md) | **核心** | 软件需求规格说明书 Part 1：引言 / 总体描述 / 功能需求 / 非功能需求 / 数据模型 / 详细技术栈 | 22KB |
| 3 | [`SRS_02_Interface_And_Validation.md`](docs/SRS_02_Interface_And_Validation.md) | **核心** | 软件需求规格说明书 Part 2：接口需求 / 外部服务 / 设计约束 / 60+ 条验收标准 / 完整目录结构 | 25KB |
| 4 | [`TECH_STACK_SUMMARY.md`](docs/TECH_STACK_SUMMARY.md) | **速查** | 技术栈汇总清单：分层详表 + 版本锁定 + 新增/已有模块对比 + LangGraph 替代方案评估 + MVP 最小子集 + 风险替代 | 18KB |
| 5 | [`requirements.txt`](requirements.txt) | 已更新 | 核心依赖声明（新增 langgraph/Jinja2/PyYAML/tiktoken/tenacity） | 约 1KB |

合计：**5 份文档 / 约 61KB 文字说明**

---

## 2. 需求分析与技术栈的核心结论

### 2.1 核心设计理念（一句话）

**ParaJudge** = **四阶段结构化辩论**（证据构建 → Coach+Speakers 辩论 → 检察官-辩护律师审理 → 五维专业法官裁决） × **目标驱动 Agent 异质性** × **证据闭包约束** × **创新保护机制** × **类判决书推理链输出**

### 2.2 技术栈核心选型（一张表）

| 维度 | 选型 | 理由 |
|:---|:---|:---|
| **工作流编排** | **LangGraph 0.2.22** | StateGraph 完美契合四阶段流程；parallel node 支持五法官并行；Checkpointer 免费获得状态持久化 |
| **用户接口** | FastAPI 0.111 + Typer 0.12 + Jinja2 3.1 | FastAPI 自动文档/类型安全；Typer 与 FastAPI 同团队；Jinja2 零学习成本渲染裁决书 |
| **数据模型** | **Pydantic v2 2.9.2** | 全栈唯一数据模型；与 FastAPI/Typer 原生集成；JSON 序列化自动完成 |
| **LLM Provider** | **`openai` 1.43 SDK** + **`dashscope` 1.20** + **自研 Mock Provider** | 统一抽象 → 新增 Provider 仅需实现 `LLMProvider.chat()` 一个函数；Mock 保证零 API Key 也能端到端运行 |
| **配置管理** | **pydantic-settings 2.5** + **PyYAML 6.0** + **python-dotenv 1.0** | 支持 .env 环境变量 + 结构化 DebateConfig + YAML 领域知识库，三套配置全栈打通 |
| **可靠性** | **tenacity 9.0**（指数退避重试） + **httpx 0.27**（现代异步 HTTP 客户端） | 每次外部调用都有 ≥3 次自动重试；失败自动降级到 Mock Provider |
| **学术检索** | **arxiv 2.1** + **Semantic Scholar API** + **Crossref API** | 三源检索覆盖大多数论文；JSON 结果 → EvidenceBrief Pydantic 模型 |
| **成本/监控** | **tiktoken 0.7**（OpenAI 官方分词器） + JSON 结构化日志 | 每次 LLM 调用精确记录 input/output token，可配置预算告警自动邮件通知 |

### 2.3 功能需求矩阵（FR-xxx 编号）

```
Phase 0: 证据构建 (10 FRs)
  FR-01 关键词提取            FR-02 三源并行检索
  FR-03 去重与评分排序        FR-04 EvidenceBrief 生成
  FR-05 证据可信度计算        FR-06 领域知识库加载
  FR-07 问题类型识别          FR-08 领域知识库加载
  FR-09 检索缓存              FR-10 冷领域降级

Phase 1: 辩论引擎 (17 FRs)
  FR-11 Coach 角色定义        FR-12 Speaker 角色定义
  FR-13 论点生成              FR-14 证据引用验证
  FR-15 反驳生成              FR-16 多轮对话管理
  FR-17 POI 段间质询          FR-18 发言内容摘要
  FR-19 结构化论点摘要        FR-20 辩论元数据统计
  FR-21 ~ FR-27 详细见 SRS Part 1 3.2 节

Phase 2.1: 审理引擎 (7 FRs)
  FR-31 检察官识别证据缺失    FR-32 检察官识别逻辑漏洞
  FR-33 检察官识别选择性呈现  FR-34 检察官识别未验证假设
  FR-35 辩护律师最佳辩护      FR-36 2-3 轮交叉质询
  FR-37 审理总结输出

Phase 2.2: 裁决引擎 (18 FRs)
  FR-41 E-Judge 证据法官      FR-42 L-Judge 逻辑法官
  FR-43 P-Judge 原则法官      FR-44 C-Judge 案例法官
  FR-45 I-Judge 创新法官      FR-46 Final Judge 加权整合
  FR-47 推理链构建            FR-48 不确定性标注
  FR-49 创新保护逻辑          FR-50 HTML/MD/JSON 三格式裁决书
  FR-51 ~ FR-58 详细见 SRS Part 1 3.4 节

用户接口 (8 FRs)
  FR-61 CLI 子命令组          FR-62 CLI 彩色输出
  FR-63 CLI 配置管理          FR-64 REST API 路由
  FR-65 异步任务与轮询        FR-66 JSON 响应格式
  FR-67 健康检查接口          FR-68 异常处理与错误代码

配置与持久化 (5 FRs)
  FR-71 环境变量与配置文件    FR-72 YAML 领域知识库
  FR-73 运行状态 JSON 持久化  FR-74 裁决书文件保存
  FR-75 JSON 结构化日志
```

### 2.4 非功能需求重点（NF-xxx 编号）

| 编号 | 指标 | 目标值 | 如何验证 |
|:---|:---|:---|:---|
| NF-01 | 端到端响应时间（Mock Provider） | ≤ 30 秒 | `time parajudge run` |
| NF-02 | 端到端响应时间（真实 Provider） | ≤ 8 分钟 | 同上，用 OpenAI/DashScope |
| NF-05 | API 响应时间 | 非 LLM 接口 P95 ≤ 300ms | locust/httpx 压力测试 |
| NF-08 | 可复现性（Mock Provider） | 相同 seed 10 次完全一致 | 循环运行 diff |
| NF-11 | 代码质量 | ruff 0 errors；类型注解覆盖 ≥80% | `ruff check src/ backend/` |
| NF-12 | 测试覆盖率 | 核心代码 ≥70%；整体 ≥50% | `pytest --cov=src --cov=backend` |
| NF-13 | 安全（API Key 保护） | 代码库 grep 不到真实 Key；日志不打印 Key | 脚本扫描 |
| NF-14 | Provider 无关性 | 新增 Provider ≤ 50 行代码 | 写一个示例 Provider |
| NF-17 | Python 版本兼容 | 3.10 / 3.12 / 3.14 均能通过 | 多版本 tox 测试 |

### 2.5 验收测试矩阵（AT-xxx）

见 `SRS_02_Interface_And_Validation.md` 第 5 节，共 **30+ 条** 具体可执行测试，涵盖：
- 冒烟测试（模块启动/初始化）
- 端到端场景（事实核查 / 决策分析 / 创新评估 / 空引用压力测试）
- 单元测试（各模块单独功能点）
- 可靠性与压力测试（故障注入 / 并发 10 任务）

---

## 3. 下一步动作清单

### 3.1 本周可立即执行的动作（优先级 P0，顺序编号按依赖）

```
Step 1: 检查代码库当前状态
  $ cd /workspace
  $ ls -la
  $ grep -r "TODO" docs/ --include="*.md"   # 查看文档中标记的 TODO
  Action: 确认本任务输出的 5 份文档都在 docs/ 目录

Step 2: 验证依赖声明完整性
  $ cat requirements.txt | head -30
  Action: 确认 langgraph/Jinja2/PyYAML/tiktoken/tenacity 已在 requirements.txt
  Action: 在本机测试能否安装（可选）
    $ python3 -m venv .venv && source .venv/bin/activate
    $ pip install -r requirements.txt

Step 3: 扩展 backend/models/schemas.py（P0 第 1 件编码任务）
  参考 SRS Part 1 第 4 节中的模型清单，新增/扩写：
    · EvidenceItem, EvidenceBrief
    · ArgumentIndex, ReviewItem, ReviewReport
    · JudgeDimension, DimensionScore, JudgeReport
    · ReasoningStep, FinalVerdict, VerdictReasoning, JudgmentReport
    · DomainKB, PrincipleItem, CaseItem
    · DebateConfig（增强版，含 weight_profiles）
    · ProblemType, JudgeType（StrEnum）
  Action: 直接编辑 backend/models/schemas.py，保持风格与现有 DebateConfig 一致

Step 4: 实现 src/llm/providers.py（Mock/OpenAI/DashScope 三 Provider）
  Action: 定义抽象基类 LLMProvider，三个实现；
          openai 用 async chat.completions；dashscope 用官方 Generation.call

Step 5: 实现 src/knowledge/evidence.py（Phase 0 证据构建器）
  Action: 直接调用已有 src/search/engine.py::unified_search()，
          然后去重/评分/封装为 EvidenceBrief

Step 6: 实现 src/knowledge/classifier.py（问题类型识别）
  Action: 用启发式规则 + LLM 辅助的两步识别器

Step 7: 完成 SRS 中未细化的部分
  - 在 SRS Part 1 4.1 节补充具体权重公式（FR-46 Final Judge）
  - 在 SRS Part 2 5.2 节补充 Judge 评分算法细节
  - 在 SRS Part 2 5.3 节补充推理链构建算法伪代码
```

### 3.2 下一周动作（P1，依赖 Step 3-6 完成后）

```
Step 8: Agent 基类 + Coach/Speaker 实现（src/debate/）
Step 9: LangGraph Phase 1 子图编排（src/debate/workflow.py）
Step 10: 检察官/辩护律师（src/review/）+ Phase 2.1 子图
Step 11: 5 位法官（src/judgment/judges.py）+ Phase 2.2 子图
Step 12: Final Judge 加权整合 + 推理链 + 不确定性标注
Step 13: 裁决书生成（HTML/MD/JSON）
Step 14: 全局编排大图（src/orchestration/graph.py）
Step 15: CLI 扩展（parajudge 命令组）
Step 16: FastAPI 路由扩展（/api/v1/parajudge/*）
```

### 3.3 文档维护动作（每次代码变更后）

```
· 当新增/修改 Agent Prompt 时 → 更新 TECH_STACK_SUMMARY.md §5.2 的模块状态
· 当新增外部 API 调用时 → 更新 SRS Part 2 §8（外部接口与第三方服务）
· 当调整辩论/裁决算法时 → 更新 PARAJUDGE_DESIGN_REPORT.md 对应章节
· 当达到里程碑（如 M1/M2/M3）→ 在 SRS Part 2 §6 打勾记录
```

---

## 4. 实现优先级与依赖关系图

```
                     ┌─────────────────────┐
                     │  Step 3: Pydantic   │  ★ P0 - 全部依赖根
                     │  schemas.py 扩展    │  ≈ 150 行代码
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │  Step 4: LLMProvider│  ★ P0 - 基础能力
                     │  (Mock/OpenAI/Dash) │  ≈ 200 行
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                   ▼
   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
   │ Step 5:         │ │ Step 6:         │ │ Step 14:        │
   │ EvidenceBuilder │ │ Classifier       │ │ Judgment Engine │
   │ (Phase 0)       │ │ (Phase 0 子)     │ │ (Phase 2.2,     │
   │ ≈100 行         │ │ ≈40 行           │ │ 需 Agent 基类)   │
   └────────┬────────┘ └─────────┬────────┘ └────────┬────────┘
            │                    │                    │
            └────────┬───────────┘                    │
                     ▼                                 │
           ┌─────────────────────┐                     │
           │  Step 8: Agent 基类  │  ★ P0              │
           │  src/debate/agent_  │  ≈80 行             │
           │  base.py             │                     │
           └──────────┬───────────┘                     │
                      ▼                                 │
           ┌─────────────────────┐                     │
           │  Step 9: Phase 1    │ ◄───────────────────┘
           │  Coach+Speaker+Graph │ ★ P0 核心功能
           └──────────┬───────────┘
                      ▼
           ┌─────────────────────┐
           │  Step 10: Phase 2.1 │
           │  Prosecutor+Defense │ ★ P1
           └──────────┬───────────┘
                      ▼
           ┌─────────────────────┐
           │  Step 12: Final     │
           │  Judge + Reasoning  │ ★ P1（推理链创新）
           └──────────┬───────────┘
                      ▼
           ┌─────────────────────┐
           │  Step 13: 裁决书生成 │ ★ P1（渲染/输出）
           └──────────┬───────────┘
           ┌──────────┴───────────┐
           ▼                       ▼
   ┌─────────────────┐   ┌─────────────────┐
   │ Step 15: CLI    │   │ Step 16: API    │
   │ 扩展            │   │ 路由扩展        │
   └─────────────────┘   └─────────────────┘
```

**关键依赖节点**：
1. `schemas.py` 扩展 — 所有模块都读写 Pydantic 模型，**第一件要做**
2. `LLMProvider` 抽象 — 所有 Agent 都要调用它
3. `Phase 0`（evidence + classifier）— 无 Agent 依赖，纯函数，易测试
4. `Agent 基类` — Phase 1/2.1/2.2 的 Agent 实现都要继承它
5. `Phase 1 → Phase 2.1 → Phase 2.2` 顺序依赖 — 前一阶段的输出是后一阶段的输入

---

## 5. 如何使用本文档

### 5.1 作为开发者的快速上手指南

```
新手路径（按顺序阅读）:
  1) PARAJUDGE_DESIGN_REPORT.md  ← 理解"为什么这么设计"
  2) TECH_STACK_SUMMARY.md        ← 快速掌握"用了哪些库"
  3) SRS_01_Introduction_And_TechStack.md ← 通读 3.功能需求 + 5.数据模型
  4) SRS_02_Interface_And_Validation.md  ← 通读 4.接口 + 5.验收测试矩阵
  5) 开始编码（按 3.1 Step 3-6 顺序）

资深开发者/只需决策参考:
  1) TECH_STACK_SUMMARY.md §3（核心选型表） + §7（LangGraph 替代方案评估）
  2) PARAJUDGE_DESIGN_REPORT.md §4（四阶段架构图） + §10（风险与挑战）
```

### 5.2 文档编号索引

```
FR-xxx        功能需求编号          → 见 SRS Part 1 §3
NF-xxx        非功能需求编号        → 见 SRS Part 1 §6
AT-xxx        验收测试编号          → 见 SRS Part 2 §5
PARAJUDGE-xx 设计章节编号           → 见 PARAJUDGE_DESIGN_REPORT.md
```

---

**下次任务建议起点**: `backend/models/schemas.py` 扩展（3.1 Step 3），因为它是所有其他编码任务的上游依赖，且是一个"低风险高价值"任务（纯 Pydantic 定义，易于代码审查和测试）。
