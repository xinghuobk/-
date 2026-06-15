# ParaJudge 多智能体辩论系统 — 软件需求规格说明书 (SRS)

## 第 2 部分：接口需求 + 外部服务 + 设计约束 + 验收标准 + 参考实现位置

> **文档版本**：v1.1
> **更新日期**：2026-06-15
>
> **版本历史**：
> - v1.1（2026-06-15）：新增 Moderator（主持人）角色完整接口规格、配置项与验收测试矩阵（CLI `--moderator-strictness`、`--*-rounds`、REST `config.moderator_*`、内部接口 `Moderator` 方法、F-310.x~F-314.x 用例、F-101 端到端）。
> - v1.0（2026-06-15）：初始版本，覆盖接口需求、外部服务、设计约束、验收标准与参考实现位置。

---

## 目录（第 2 部分）

7. [接口需求](#7-接口需求)
8. [外部接口与第三方服务](#8-外部接口与第三方服务)
9. [设计约束与假设](#9-设计约束与假设)
10. [验收标准](#10-验收标准)
11. [附录：参考实现位置与模块负责人清单](#11-附录参考实现位置)

---

## 7. 接口需求

### 7.1 命令行接口 (CLI)

#### 7.1.1 命令结构

```
parajudge [GLOBAL_OPTIONS] <COMMAND> [ARGS]

GLOBAL_OPTIONS:
  --provider TEXT     LLM Provider: mock|openai|dashscope  [默认: mock]
  --model TEXT        模型名                              [默认: mock-model]
  --temperature FLOAT 温度 0-2                          [默认: 0.7]
  --seed INT          随机种子（仅影响 Mock Provider）   [默认: 42]
  --language TEXT     输出语言 auto|zh|en                [默认: auto]
  --verbose / -v      详细模式
  --config PATH       自定义配置文件路径 (YAML/JSON)
  --help              显示帮助

COMMAND:
  run                 执行完整辩论流程
  evidence            仅构建证据包（Phase 0）
  debate              执行辩论（Phase 1）
  review              执行审理（Phase 2.1）
  judge               执行裁决（Phase 2.2）
  config show         显示当前配置
  config set K V     设置配置项
  list                列出历史运行记录
  view RUN_ID         查看某次运行的裁决书
  benchmark           运行基准测试
```

#### 7.1.2 `parajudge run` 子命令规格

```
parajudge run <PROBLEM> [OPTIONS]

ARGUMENTS:
  PROBLEM            问题文本（10-1000字符）

OPTIONS:
  --problem-type TYPE   强制指定问题类型: fact|decision|innovation|open
                        （默认: auto，由问题识别器决定）
  --domain PATH         指定领域知识库 YAML 文件
  --brief-size INT      Evidence Brief 条目数         [默认: 25]
  --max-rounds INT      每方最大发言轮数              [默认: 5]
  --speakers INT        每方 Speaker 数               [默认: 2]
  --enable-poi / --no-poi     是否启用 POI 段间质询  [默认: enable]
  --enable-review / --no-review  是否启用审理阶段     [默认: enable]
  --moderator-strictness 主持人严格度 loose|normal|strict [默认: normal]
  --max-total-seconds INT  Phase 1 总时长上限（秒）  [默认: 1800]
  --opening-rounds INT   立论（OPENING）阶段最大发言轮数    [默认: 2]
  --cross-exam-rounds INT 交叉质询（CROSS_EXAM）阶段最大发言轮数 [默认: 4]
  --closing-rounds INT   结辩（CLOSING）阶段最大发言轮数    [默认: 2]
  --save PATH            输出目录，保存裁决书/状态    [默认: data/runs/{auto_id}/]
  --format FMT           裁决书格式: html|md|json|all [默认: all]
  --token-budget INT     单次运行 token 预算，超限告警
  --json                 以 JSON 输出摘要（方便管道调用）

EXIT_CODE:
  0  成功
  1  参数错误 / 配置错误
  2  LLM 调用失败（所有 Provider 均失败）
  3  检索 API 全部失败（无法构建 Evidence Brief）
  4  断言错误（内部状态不一致）
  5  超时
```

#### 7.1.3 CLI 输出示例（正常路径）

```
$ parajudge run "GPT-4 级别的多智能体推理系统是否应当开源给学术界免费使用？"
[INFO] 问题类型识别: decision
[INFO] Phase 0: 构建 Evidence Brief ...  共 25 条证据（arXiv 18 / SS 6 / Crossref 1）
[INFO] Phase 1: 辩论阶段（正反各 2 名 Speaker，最多 5 轮）
  · Round 1: Pro Speaker #1 完成（引用 E-003, E-018）
  · Round 1: Con Speaker #1 完成（引用 E-007, E-022）
  · POI 被触发：Con 对 Pro 论点 arg-001 提出质询 → Pro 回应
  · Round 2: Pro Speaker #2 完成 ...
  · [总结] 辩论阶段共 12 次发言，生成 21 条论点
[INFO] Phase 2.1: 审理阶段
  · 检察官发现 4 处漏洞（1 处证据缺失 / 2 处逻辑跳跃 / 1 处未验证假设）
  · 辩护律师回应 + 补充证据 E-025, E-026
[INFO] Phase 2.2: 裁决阶段（5 位专业法官并行评估）
  · E-Judge（证据）: overall_score=82
  · L-Judge（逻辑）: overall_score=76
  · P-Judge（原则）: overall_score=71
  · C-Judge（案例）: overall_score=68
  · I-Judge（创新）: overall_score=85
  · Final-Judge 加权整合（decision 权重: evidence 0.25 / logic 0.25 / principle 0.15 / case 0.20 / innovation 0.15）
[INFO] ✓ 裁决书已生成: data/runs/run-20260615-091234/report.html
[INFO] ✓ 状态已保存: data/runs/run-20260615-091234/state.json
[INFO] Token 消耗总计: 24,380 (input) / 12,470 (output)
```

### 7.2 REST API 接口（FastAPI + Pydantic v2）

#### 7.2.1 全局规格

- Base URL: `/api/v1/parajudge`
- 文档: `GET /docs`（Swagger UI）/ `GET /redoc`
- 数据格式: JSON（请求和响应均为 JSON）
- 认证: Phase 1 无认证；Phase 2 可选 API Key（预留）
- 错误响应: 统一格式 `{"detail": "错误信息", "error_code": "...", "suggestion": "..."}`

#### 7.2.2 `/run` — 启动辩论（异步任务）

```
POST /api/v1/parajudge/run
Content-Type: application/json

{
  "problem": "问题文本（必填，10-1000字符）",
  "problem_type": "auto",     // auto|fact|decision|innovation|open
  "config": {                 # （可选）覆盖默认配置
    "model_provider": "mock", # mock|openai|dashscope
    "model_name": "mock-model",
    "temperature": 0.7,
    "max_rounds": 5,
    "speaker_count_per_side": 2,
    "enable_poi": true,
    "enable_review_phase": true,
    "evidence_brief_size": 25,
    "moderator_strictness": "normal",  # loose|normal|strict
    "max_total_seconds": 1800,         # Phase 1 总时长上限
    "opening_max_rounds": 2,           # 立论阶段最大发言轮数（由 Moderator 驱动）
    "cross_exam_max_rounds": 4,        # 交叉质询阶段最大发言轮数
    "closing_max_rounds": 2,           # 结辩阶段最大发言轮数
    "domain_kb_path": null
  },
  "options": {                // （可选）运行参数
    "format": "html",         // html|md|json|all
    "save_to_disk": true,
    "token_budget": 50000
  }
}

响应（HTTP 201 Created）:
{
  "task_id": "task-20260615-091234-abcdef",
  "status": "submitted",     // submitted|in_progress|done|failed
  "created_at": "2026-06-15T09:12:34Z",
  "poll_url": "/api/v1/parajudge/task/task-20260615-091234-abcdef"
}

后端实现要点:
  · 用 asyncio.create_task() 启动后台任务，立即返回 task_id
  · 任务状态用内存字典保存（可持久化到 SQLite/Pydantic BaseModel）
  · 任务失败写入 traceback 到任务记录，status="failed"
```

#### 7.2.3 `/task/{task_id}` — 查询任务状态

```
GET /api/v1/parajudge/task/{task_id}

响应（HTTP 200）:
{
  "task_id": "task-20260615-091234-abcdef",
  "status": "done",          // submitted|phase_0|phase_1|phase_2_1|phase_2_2|done|failed
  "phase": "phase_2_2",      // 当前阶段（仅在 in_progress 时非 null）
  "progress": 0.75,          // 0-1
  "started_at": "2026-06-15T09:12:34Z",
  "updated_at": "2026-06-15T09:14:12Z",
  "eta": "2026-06-15T09:14:30Z",
  "token_consumed": 36850,
  "error": null,             // 如果失败则有错误信息
  "output_urls": {           // 完成后可访问
    "html": "/api/v1/parajudge/task/{task_id}/report.html",
    "markdown": "/api/v1/parajudge/task/{task_id}/report.md",
    "json": "/api/v1/parajudge/task/{task_id}/report.json",
    "state": "/api/v1/parajudge/task/{task_id}/state.json"
  }
}

HTTP 404（task_id 不存在）: {"detail": "Task not found", "error_code": "E_TASK_NOT_FOUND"}
```

#### 7.2.4 `/task/{task_id}/report.{fmt}` — 获取裁决书

```
GET /api/v1/parajudge/task/{task_id}/report.html    → HTML 页面
GET /api/v1/parajudge/task/{task_id}/report.md      → Markdown
GET /api/v1/parajudge/task/{task_id}/report.json    → 结构化裁决 JSON
GET /api/v1/parajudge/task/{task_id}/state.json     → 完整运行状态 JSON
```

#### 7.2.5 `/tasks` — 任务列表

```
GET /api/v1/parajudge/tasks?limit=20&offset=0&status=done
→ 返回分页列表
```

#### 7.2.6 `/health` — 健康检查

```
GET /health

{
  "status": "healthy",
  "services": {
    "llm_provider_mock": "ok",
    "llm_provider_openai": "ok",
    "llm_provider_dashscope": "timeout",  // 异常时标注
    "arxiv_api": "ok",
    "semantic_scholar_api": "rate_limited"
  },
  "version": "0.1.0"
}
```

#### 7.2.7 `/evidence/query` — 证据查询/补充检索

```
POST /api/v1/parajudge/evidence/query
{
  "query": "检索关键词",
  "max_results": 25
}
→ 返回 Evidence Brief 列表（JSON）
```

### 7.3 内部模块接口（约定）

```
每个主要模块对外暴露一个 public 函数，保持稳定签名：

src.knowledge.evidence.build(problem: str, config: DebateConfig) -> EvidenceBrief
src.knowledge.classifier.classify(problem: str) -> str  # 返回 problem_type
src.knowledge.domain_kb.load(path: str) -> DomainKB

src.debate.coach.plan(problem: str, brief: EvidenceBrief, side: str) -> CoachPlan
src.debate.speaker.speak(problem: str, brief: EvidenceBrief, plan: CoachPlan, speaker_id: str) -> Argument
src.debate.moderator.run_phase(brief: EvidenceBrief, speakers: List[Speaker], coaches: List[Coach], config: ModeratorConfig) -> DebateSummary  # ★ Moderator 主入口
src.debate.moderator.Moderator(config, brief, speakers, coaches) -> DebateSummary                # ★ Moderator 主方法签名（类级别：状态机 + 质量守门 + 汇总产出）
src.debate.moderator.Moderator._should_advance_phase(current_phase: str, turns_in_phase: int) -> bool  # 判断是否推进到下一阶段
src.debate.moderator.Moderator._check_duplicate(argument: Argument) -> float               # 返回与已有论点的相似度（≥阈值即 duplicate）
src.debate.poi_engine.query(argument: Argument, brief: EvidenceBrief, opponent_id: str) -> POIInteraction
src.debate.workflow.run(problem: str, brief: EvidenceBrief, config: DebateConfig) -> DebateState

src.review.prosecutor.scan(argument_index: ArgumentIndex, brief: EvidenceBrief) -> List[ReviewItem]
src.review.defense.defend(review_items: List[ReviewItem], argument_index: ArgumentIndex, brief: EvidenceBrief) -> ReviewReport
src.review.workflow.run(argument_index: ArgumentIndex, brief: EvidenceBrief) -> ReviewReport

src.judgment.judges.evidence_judge.evaluate(...) -> JudgeReport
src.judgment.judges.logic_judge.evaluate(...) -> JudgeReport
... (principle / case / innovation judges)
src.judgment.final_judge.integrate(judge_reports: List[JudgeReport], problem_type: str) -> FinalVerdict
src.judgment.reasoning_chain.build(verdict: FinalVerdict, brief: EvidenceBrief, kb: DomainKB) -> List[ReasoningStep]
src.judgment.report_generator.render(...) -> str  # HTML / Markdown / JSON

src.llm.providers.LLMProvider.chat(prompt: str, system_prompt: str | None = None, **kwargs) -> str
src.llm.prompt_library.get_template(role: str, lang: str) -> str  # 返回模板字符串，含 {variable} 占位符
```

---

## 8. 外部接口与第三方服务

### 8.1 LLM Provider

| 服务 | 方式 | 用途 | 关键参数 | 成本估算 | 可用性 |
|:---|:---|:---|:---|:---|:---|
| **Mock Provider** | 纯本地规则模拟 | 开发测试 | seed, 固定 token 成本 | 零成本 | 100% |
| **OpenAI (Chat Completions)** | `openai` SDK，异步调用 | 生产模型 | `OPENAI_API_KEY`, `model` (gpt-4o-mini / o3-mini) | ≈ $2.5 / 10^6 tokens (input) | ≥ 99.9% |
| **DashScope (通义千问)** | `dashscope` SDK | 中文优先 / 备用 | `DASHSCOPE_API_KEY`, `model` (qwen-plus / qwen-max) | ≈ ¥3-12 / 10^6 tokens | ≥ 99.5% |
| **(可选) 本地部署 (vLLM / llama.cpp)** | OpenAI 兼容接口 | 离线场景 | `BASE_URL` + `MODEL_NAME` | 一次性 GPU 成本 | 视部署而定 |

**调用流程**:

```
Agent 调用 LLM 的统一流程（在 src.llm.providers 中实现）:

1. 构建 system_prompt（角色/目标）+ user_prompt（当前任务输入）
2. 调用 LLMProvider.chat(system_prompt=, prompt=, **kwargs)
3. tenacity 装饰器最多 3 次指数退避重试
4. tiktoken 记录 input/output token 数
5. 结构化解析返回（JSON → Pydantic 模型）
6. 若连续失败，按配置的 fallback_provider 顺序切换，最终回退 Mock
```

### 8.2 学术检索 API

| 服务 | 方式 | 用途 | 配额 / 限制 | 关键实现 |
|:---|:---|:---|:---|:---|
| **arXiv API** | HTTP GET → XML → JSON | 核心论文元数据检索 | 无 API Key，但建议 ≤ 1 req/3s | `src/search/arxiv_client.py`（已有，沿用） |
| **Semantic Scholar API** | HTTP GET → JSON | 引用数 / 引用图 | API Key 可选（提升配额） | `src/search/semantic_scholar_client.py`（已有，沿用） |
| **Crossref API** | HTTP GET → JSON | DOI 元数据 / 出版信息 | polite 邮箱可选（提升配额） | `src/search/crossref_client.py`（已有，沿用） |
| **(可选) OpenAlex** | HTTP GET → JSON | 大规模引文索引 | 无 Key | 已有 `pyalex` 引用 |

**统一入口**: `src/search/engine.py::unified_search(keyword, year_min, year_max, sources, max_results)`
**输出规范**: `List[PaperMeta]`（`backend/models/schemas.py` 已定义）

### 8.3 文件系统接口

| 路径模式 | 用途 | 格式 | 生命周期 |
|:---|:---|:---|:---|
| `data/runs/{run_id}/evidence_brief.json` | 证据包 | JSON | 永久 |
| `data/runs/{run_id}/argument_index.json` | 论点索引 | JSON | 永久 |
| `data/runs/{run_id}/review_report.json` | 审理报告 | JSON | 永久 |
| `data/runs/{run_id}/final_verdict.json` | 裁决结果 | JSON | 永久 |
| `data/runs/{run_id}/report.html` | 裁决书（HTML） | HTML | 永久 |
| `data/runs/{run_id}/report.md` | 裁决书（Markdown） | MD | 永久 |
| `data/runs/{run_id}/state.json` | 完整运行状态 | JSON | 永久 |
| `logs/parajudge-{date}.log` | 运行日志 | JSON Lines | 按天滚动，保留 30 天 |
| `data/domain_kb/{domain}.yaml` | 领域知识库 | YAML | 永久（版本化） |
| `data/cache/evidence/{hash}.json` | 证据包缓存 | JSON | TTL 7 天，可配置 |

### 8.4 (可选) 外部服务扩展

- **向量数据库**: ChromaDB / FAISS（已有依赖），用于 Evidence Brief 的语义去重和检索增强
- **知识图谱**: networkx（已有依赖），用于论点关系可视化
- **持久化数据库**: SQLite（`sqlite3` 标准库），用于任务历史、缓存、Checkpointer

---

## 9. 设计约束与假设

### 9.1 硬性约束

1. **Python 3.10+ 唯一支持语言**: 所有核心代码必须在 Python 3.10/3.11/3.12/3.13/3.14 下运行；不引入非 Python 实现的关键模块
2. **Pydantic v2 作为唯一数据模型方案**: 所有内部接口输入/输出必须是 Pydantic 模型或基本类型
3. **LangGraph 作为唯一编排框架**: Agent 交互必须通过 LangGraph StateGraph 节点表达，禁止"裸写"复杂状态管理
4. **敏感信息永不入仓库**: `.env`、真实 API Key、用户输入敏感数据不得提交 git；`.gitignore` 已有规则
5. **必须支持 Mock Provider 零 API Key 运行**: 系统在仅安装 Python 依赖且无任何外部服务时，应能完成完整流程（只是输出为模拟结果）
6. **PEP 8 代码风格**: 所有新增代码必须通过 `ruff check`（无严重告警）；函数必须有 docstring；参数/返回必须有类型注解

### 9.2 软约束（推荐但非强制）

1. **模块化优先于继承**: 各 Agent 尽量通过组合方式（Pydantic 配置 + LLMProvider 注入）实现差异化，避免深层类继承
2. **Provider 适配层**: 新增 Provider 只需实现 `LLMProvider` 协议，不改任何 Agent 代码
3. **Prompt 模板集中管理**: 所有 Agent Prompt 放在 `src/llm/prompt_library.py`，按 `role.language.template_name` 命名
4. **单一职责原则**: 一个 Agent 一个文件（如 `src/debate/speaker.py` 只包含 Speaker Agent 实现）
5. **结构化日志**: 用 `logging.info({"event": "speak_done", "speaker_id": "pro-speaker-1", "tokens": 1200})` 形式
6. **测试优先**: 核心模块（EvidenceBuilder、Judge 评分逻辑、FinalJudge 权重整合）应有 ≥ 1 个单元测试

### 9.3 关键假设

1. **假设 A: LLM 响应格式可控**: Agent 可要求 LLM 输出 JSON / Markdown 结构，并被 Pydantic 解析；偶发失败可通过重试或 fallback 处理
2. **假设 B: Evidence Brief 质量上限**: arXiv/Semantic Scholar 的检索结果质量基本足以支撑辩论；但对前沿/冷领域（< 10 篇公开论文），系统应优雅降级为"弱证据"标注（credibility 低但流程可完成）
3. **假设 C: 中文 Prompt 质量不低于英文**: 对于 qwen / gpt-4o-mini 等模型，中文 Prompt 质量与英文相当
4. **假设 D: token 预算充足**: 一次完整辩论预计消耗 20K-80K tokens（取决于问题复杂度和轮数）；生产环境应有预算管理（已在 FR-607/FR-608 定义）
5. **假设 E: 单次运行时间用户可接受 3-8 分钟**: 多 Agent 多阶段必然耗时；UI/API 设计需体现"异步任务 + 轮询"模式
6. **假设 F: 法官评分主观性不可消除，系统目标是"可解释"而非"绝对正确"**: 各 Judge Score 是辅助信号；推理链比数值更重要

---

## 10. 验收标准

### 10.1 功能性验收（按模块分层验证）

#### 10.1.1 Phase 0 证据构建验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-01 | 关键词提取 | 对 10 条基准问题，提取的关键词与人类标注的 Jaccard 相似度 ≥ 0.4 |
| F-02 | 多源检索成功 | ≥ 90% 的问题可从 ≥ 2 个源中检索到 ≥ 10 篇候选论文 |
| F-03 | Evidence Brief 生成 | 输出符合 `EvidenceBrief` Pydantic 模型；25 条条目全部非空；`credibility` 覆盖 [0.1, 1.0] 区间 |
| F-04 | 缓存有效性 | 同一问题连续提交 2 次，第 2 次命中缓存且耗时 ≤ 第 1 次的 10% |

#### 10.1.2 Phase 1 辩论引擎验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-11 | Coach 规划 | 正反双方 Coach 产出结构化计划（含主题焦点 / 证据分配 / 策略） |
| F-12 | Speaker 发言 | 每名 Speaker 每次发言 150-400 tokens，结构清晰 |
| F-12.1 | 时间片约束 | 单条发言 token 数超过 `max_tokens_per_turn` 时被截断 |
| F-13 | 证据引用验证 | 全部论点的 `evidence_refs` 均指向实际存在的 EvidenceItem ID |
| F-14 | 论点索引完整性 | 辩论结束后，`ArgumentIndex.arguments` 非空且每条有唯一 id |
| F-14.1 | 论点去重 | 构造两条几乎相同的论点，Moderator 标记第二条为 duplicate，且第二条不出现在 ArgumentIndex 中 |
| F-14.2 | 主题漂移检测 | 注入 5 条明显偏离主题的发言，Moderator 检测到 ≥ 4 条（在 normal/strict 模式） |
| F-14.3 | Moderator 警告系统 | 每条违规发言都生成 `ModeratorWarning`，包含 speaker_id / type / message |
| F-14.4 | DebateSummary 格式合规 | 产出 `DebateSummary` 模型，含 key_arguments / phase_durations / warnings / total_duration |
| F-15 | POI 触发机制 | 对 ≥ 30% 的高风险论点触发 POI；响应与质询内容相关（人工评估或关键词重合度） |
| F-15.1 | POI 批准控制 | 在无 POI 的阶段（如 closing_statements），所有 POI 请求被自动拒绝 |
| F-16 | 问题漂移检测 | 注入 5 条明确偏离主题的发言，Coach 检测到 ≥ 4 条 |
| F-16.1 | Moderator 状态机正确性 | 5 个标准配置运行，状态均按 OPENING → CROSS_EXAM → FREE_DEBATE → CLOSING → DONE 顺序迁移，无跳阶段或死循环 |
| F-16.2 | 强制超时终止 | 配置 `max_total_seconds = 10`，10 秒内 Phase 1 必须终止并产出 DebateSummary（即使未完成所有阶段） |
| F-17 | 辩论自适应终止 | 对于简单问题，实际轮数 ≤ 配置 `max_rounds` |
| F-17.1 | ModeratorConfig 可配置性 | 使用 FAST vs DEEP 两种不同配置运行同一问题，轮数和耗时差异 ≥ 2× |
| F-310.1 | Moderator 状态机正确性（多配置） | 在 3 个标准配置（FAST / STANDARD / DEEP）上运行同一问题，Moderator 状态均按 `OPENING → CROSS_EXAM → CLOSING → DONE` 顺序正确迁移，无跳阶段 / 死循环 |
| F-310.2 | 阶段超时检测（强制终止） | 设置 `max_total_seconds=3`，在第 3.5 秒之前 Moderator 必须强制终止 Phase 1，状态进入 DONE，并产出 `DebateSummary`（含 `phase_durations`） |
| F-311.1 | 论点去重检测（相似度） | 构造 2 条几乎相同的论点（embedding 相似度 > 0.85），第 2 条被 Moderator 标记为 `duplicate`，且不进入最终 `ArgumentIndex` |
| F-311.2 | 主题漂移检测（分模式） | 注入偏离问题主题的发言，被 Moderator 标记为 `off_topic`；在 `strict` 模式下该类发言被拒绝，不进入后续阶段 |
| F-312.1 | 时间片截断（token） | 当发言 token 数超过 `max_tokens_per_turn=400` 时，发言被截断并在 `DebateSummary.warnings` 中留下 `token_trim` 记录 |
| F-312.2 | 发言超时（时长） | 设置 `max_seconds_per_turn=2`，超过 2 秒的发言被 Moderator 标记为 `timeout`，进入 warnings 列表，不影响整体流程 |
| F-313.1 | POI 批准机制（阶段感知） | 正方在交叉质询（CROSS_EXAM）阶段发起 POI → 被批准；在立论（OPENING）阶段发起 POI → 被拒绝；拒绝/批准记录写入 DebateSummary |
| F-314.1 | DebateSummary 强制产出 | Phase 1 结束后必须产出结构化 `DebateSummary`，包含 `key_arguments`、`warnings`、`phase_durations` 三个字段且均非空 |
| F-314.2 | warnings 审计（字段合规） | 每次违规触发的警告均写入 `warnings` 列表，每条包含 `speaker_id`、`warning_type`、`message`、`timestamp` 四个字段 |

#### 10.1.3 Phase 2.1 审理引擎验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-21 | 检察官漏洞识别 | 在人工设计的含 10 处缺陷的测试集中，检出率 ≥ 70% |
| F-22 | 辩护律师回应覆盖 | 对 ≥ 80% 检察官指出的漏洞给出实质回应（非空泛） |
| F-23 | 审理独立性 | 审理阶段 Agent 不访问辩论发言原文（代码审查：Prompt 模板仅包含结构化索引 + Moderator 产出的 DebateSummary） |
| F-24 | ReviewReport 格式合规 | 输出符合 ReviewReport 模型；含 5 个 issue_type 的各类样本 |

#### 10.1.4 Phase 2.2 裁决引擎验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-31 | 五法官并行执行 | 日志确认 5 位 Judge 并行启动；总耗时 ≈ max(各法官耗时) 而非 sum |
| F-32 | 评分一致性 | 同一输入多次运行（固定 seed + Mock Provider），各法官分数差异 ≤ ±5 |
| F-33 | 推理链完整性 | FinalVerdict 中每条结论都能被追溯到 ≥ 1 个 JudgeReport / ≥ 1 个证据条目 |
| F-34 | 创新保护 | 在创新型问题上，I-Judge 分数显著高于 C-Judge（P-Judge先例依赖）；`innovation_protection_notes` 非空 |
| F-35 | 不确定性标注 | ≥ 60% 裁决书包含 ≥ 1 条不确定性说明 |
| F-36 | 裁决书三种格式 | HTML / Markdown / JSON 三文件均生成且内容一一对应；HTML 可直接在浏览器打开无乱码 |
| F-37 | 权重配置生效 | 用不同 `problem_type` 运行相同问题，Final Judge 的加权总分有可观察差异 |

#### 10.1.5 Provider 与基础设施验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-41 | Mock Provider 可复现 | 相同 input + seed → 逐字符相同 output（10 次） |
| F-42 | OpenAI 调用与降级 | 注入网络异常，系统回退到 Mock；失败计数 < 3 且最终正常完成 |
| F-43 | Token 计数精度 | 对一组 100 条实际调用，tiktoken 报告值与实际值差异 < 5% |
| F-44 | 日志与脱敏 | `logs/*.log` 中不出现 API Key；所有请求响应不打印用户输入全文 |

#### 10.1.6 CLI 与 API 验收

| 编号 | 验收项 | 通过标准 |
|:---|:---|:---|
| F-51 | CLI 子命令完整性 | `parajudge run/evidence/debate/review/judge/config/list/view/benchmark --help` 均无异常 |
| F-52 | CLI 端到端 | `parajudge run "测试问题" --provider mock --max-rounds 2 --moderator-strictness normal` ≤ 30 秒完成，产出裁决书；`data/runs/{id}/state.json` 含 DebateSummary 与 Moderator warnings |
| F-52.1 | Moderator 配置开关 | `--moderator-strictness loose|normal|strict` 三档在同一问题上产生不同数量的 warnings，strict 最严格 |
| F-101  | 端到端（E2E）测试 | `parajudge run "测试问题" --provider mock --moderator-strictness normal --max-rounds 2 --opening-rounds 1 --cross-exam-rounds 2 --closing-rounds 1` ≤ 30 秒完成，产出裁决书；`data/runs/{id}/state.json` 含 `DebateSummary` 与 Moderator `warnings` |
| F-53 | API 健康检查 | `curl /health` → HTTP 200，含 version 与 service 状态 |
| F-53.1 | Moderator 状态接口 | `GET /api/v1/parajudge/task/{id}` 返回的 state 中包含 `current_phase` 和 `phase_durations` |
| F-54 | API 异步任务 | `POST /run` → 返回 task_id；轮询 `GET /task/{id}` → 状态推进正确 → 完成后 `GET /report.html` 正常返回 |
| F-55 | API 错误处理 | 非法参数 → HTTP 422；非法 task_id → HTTP 404；LLM 全部失败 → HTTP 503 |

### 10.2 非功能性验收

| 编号 | 验收项 | 目标值 | 测试方法 |
|:---|:---|:---|:---|
| NF-01 | 单次端到端时间（Mock Provider） | ≤ 30 秒（简单问题） | `time parajudge run "..." --provider mock` |
| NF-02 | 单次端到端时间（真实 Provider） | ≤ 8 分钟（中等问题） | 与 NF-01 同测试但用 OpenAI/DashScope |
| NF-03 | API 响应 P95 | ≤ 300ms（非 LLM 等待接口） | locust/httpx 基准测试 |
| NF-04 | 并行任务支持 | 同时 ≥ 10 个任务并发完成 | 脚本并发提交 10 个任务观察 |
| NF-05 | Python 版本兼容 | 3.10 / 3.11 / 3.12 / 3.14 均可运行 | 多版本 tox / 手动测试 |
| NF-06 | 代码质量（ruff） | 无 error / warning（可配置忽略项） | `ruff check src/ backend/` |
| NF-07 | 类型注解覆盖率 | ≥ 80% 公共函数有完整签名注解 | `mypy src/ --ignore-missing-imports` 辅助检查 |
| NF-08 | 单元测试覆盖率 | ≥ 50% 核心代码；Phase 2.2 裁决逻辑 ≥ 70% | `pytest --cov=src --cov-report=html` |
| NF-09 | 敏感信息保护 | 代码库中 grep `api[_-]?key\|sk-\|das` 无任何真实 token 命中 | 脚本 + 人工抽查 |
| NF-10 | 可复现性（Mock Provider 10 次） | 10 次运行输出 verdict 文本完全一致；Phase 1 的 `phase_durations` 顺序一致，Moderator warnings 内容和数量一致 | 脚本循环运行 + diff |

### 10.3 端到端验收场景（用例测试）

```
场景 A: 事实核查
  问题: "2024 年美国总统大选中，特朗普是否真的被认定为 '不受选举人团资格约束'？"
  期望:
    · Phase 0 构建包含 ≥ 5 条可信权威来源（官方公告/主流媒体/选举机构报告）的 Evidence Brief
    · Phase 1 正反双方各自引用不同来源
    · Phase 2 审理发现 ≥ 2 处论点引用弱来源或存在选择性呈现
    · Phase 2.2 裁决 → E-Judge / L-Judge 高分；推理链明确给出证据来源与判断依据
    · 最终结论准确（"特朗普参与并获得选举人票，但关于 '不受资格约束' 的表述需核查..."）

场景 B: 决策分析
  问题: "一家中等规模 AI 公司应将其自研大模型开源吗？"
  期望:
    · Phase 0 检索到 Llama/Mistral/BLOOM/LLaMA-2/Qwen 等开源案例 + 商业开源文献
    · Phase 1 Pro 强调社区贡献、人才吸引力、安全性透明；Con 强调商业模式、泄露风险、竞争力下降
    · Phase 2 审理发现 Pro 方忽略 "开源后商业受损的案例"，Con 方忽略 "闭源模型安全风险"
    · Phase 2.2 裁决综合五维度分数，给出"建议在特定许可（Apache 2.0 + 商业附加条款）下开源"结论
    · 推理链明确列出每条建议背后的证据（E-*）、原则（P-*）、案例（C-*）

场景 C: 创新评估
  问题: "多智能体辩论系统是否代表 AI 推理的新范式？"
  期望:
    · Phase 0 证据包含 MAD 框架文献、LangGraph 论文、AutoGen 工作、HumanEval 基准
    · Phase 1 双方讨论 "范式级创新" vs "工程改进"
    · Phase 2.1 审理指出"先例稀少本身可能是创新信号"
    · Phase 2.2 I-Judge 给出高创新分；Final-Judge 对创新维度有明显加权；
      `innovation_protection_notes` 包含对"先例缺失不=缺陷"的说明
    · 裁决输出"仍处于早期，但具备新范式的多项特征"

场景 D: 空引用测试（压力场景）
  问题: "一个极端冷门问题（如 'X 星球 Y 生物的睡眠周期'，无公开数据）"
  期望:
    · Phase 0 证据检索返回 0-3 条低置信度相关条目，`credibility` 普遍 < 0.3
    · Phase 1 辩论 Agent 能够"基于弱证据展开推理"，且每条论点显式标注 "弱证据 / 无直接证据 / 基于类比"
    · Phase 2.1 审理阶段大量指出 "无直接证据" 问题
    · Phase 2.2 E-Judge 打低分；不确定性标注占比 ≥ 50%；最终结论以 "目前无足够证据支持 / 反对" 为主
    · 系统不崩溃、不产生幻觉性结论、不假装拥有答案

场景 E: 中文/英文双语切换
  操作: 对相同问题分别以中文和英文运行
  期望:
    · CLI 输出语言与问题语言匹配（auto 模式）
    · Prompt 模板在 zh/en 两套之间切换
    · 裁决书语言与问题语言匹配
```

### 10.4 性能验收与资源使用

| 指标 | 目标（Mock Provider） | 目标（真实 Provider） | 测试方法 |
|:---|:---|:---|:---|
| 单次运行 wall clock | ≤ 30 秒 | ≤ 8 分钟 | `time parajudge run ...` |
| CPU 占用（单核基准） | ≤ 50% | ≤ 50%（主要等待 I/O） | `htop` 峰值观察 |
| 内存占用 | ≤ 512 MB | ≤ 1 GB | `psutil` 峰值记录 |
| 磁盘写入 / 次 | ≤ 3 MB | ≤ 5 MB | `du -s data/runs/{id}/` |
| 单次 token 消耗 | ~0（Mock Provider 不计费） | 20K-80K tokens | 日志 token 计数求和 |

### 10.5 质量基准目标

**与现有技术基线对比**（目标值，需通过 experiments 模块验证）：

| 基线 | 目标相对提升 |
|:---|:---|
| 标准 MAD（简单投票） | ParaJudge 裁决质量 ≥ 标准 MAD 人工评估 +10% |
| 单 Agent 推理 (Chain-of-Thought) | 在需要多视角/证据核查的任务上，准确率提升 ≥ 15% |
| 人工专家参考（小规模标注集） | ParaJudge 裁决与人工专家裁决的一致性 ≥ 75% |

---

## 11. 附录：参考实现位置

> 本附录记录 SRS 对应功能在代码仓库中的位置（文件路径 / 关键类 / 函数签名），以及规划中的模块实现方案。

### 11.1 目录结构（完整设计）

```
/workspace
├── cli.py                              # 入口：Typer CLI（parajudge 子命令组）
├── api.py                              # 入口：FastAPI（/api/v1/parajudge/*）
├── main.py                             # 最简脚本入口（legacy，保留）
│
├── src/
│   ├── __init__.py
│   │
│   ├── knowledge/                      # 知识管理与证据构建（Phase 0）
│   │   ├── __init__.py
│   │   ├── evidence.py                 # EvidenceItem / EvidenceBrief + build()
│   │   ├── classifier.py               # 问题类型识别器（ProblemClassifier）
│   │   ├── domain_kb.py                # PrincipleItem / CaseItem / DomainKB + YAML loader
│   │   └── evidence_cache.py           # 证据缓存（hash-based，TTL=7 天）
│   │
│   ├── debate/                         # 辩论引擎（Phase 1）
│   │   ├── __init__.py
│   │   ├── agent_base.py               # ParaJudgeAgent 基类（RunnableSerializable）
│   │   ├── coach.py                    # Coach（正方/反方规划）
│   │   ├── speaker.py                  # Speaker Agent
│   │   ├── moderator.py                # ★ 主持人 Moderator（状态机 + 时间片 + 质量守门；v1.1 明确：P0 / 约 0.8 人月，依赖 agent_base + speaker + argument_index）
│   │   ├── poi_engine.py               # Point-of-Information 段间质询
│   │   ├── evidence_closure.py         # 证据闭包与引用验证
│   │   ├── argument_index.py           # 论点索引维护 + 漂移检测
│   │   └── workflow.py                 # Phase 1 LangGraph 工作流
│   │
│   ├── review/                         # 审理引擎（Phase 2.1）
│   │   ├── __init__.py
│   │   ├── prosecutor.py               # Prosecutor（检察官）
│   │   ├── defense.py                  # Defense Attorney（辩护律师）
│   │   └── workflow.py                 # Phase 2.1 LangGraph 工作流
│   │
│   ├── judgment/                       # 裁决引擎（Phase 2.2）
│   │   ├── __init__.py
│   │   ├── judges.py                   # Evidence/Logic/Principle/Case/Innovation Judges
│   │   ├── final_judge.py              # Final Judge（加权整合）
│   │   ├── reasoning_chain.py          # 推理链构建
│   │   ├── uncertainty.py              # 不确定性标注
│   │   ├── innovation_protect.py       # 创新保护逻辑
│   │   ├── report_generator.py         # HTML/MD/JSON 裁决书生成
│   │   └── report_template.html        # Jinja2 HTML 模板
│   │
│   ├── llm/                            # LLM Provider 适配层
│   │   ├── __init__.py
│   │   ├── providers.py                # LLMProvider 抽象基类 + Mock/OpenAI/DashScope
│   │   ├── prompt_library.py           # 所有 Agent 的 Prompt 模板（按 role.lang 组织）
│   │   ├── token_counter.py            # tiktoken 封装 + 成本估算
│   │   └── retry.py                    # tenacity 重试策略
│   │
│   ├── orchestration/                  # 全局编排（LangGraph 大图）
│   │   ├── __init__.py
│   │   ├── state.py                    # GraphState 定义
│   │   └── graph.py                    # 构建 StateGraph，集成 Phase 0/1/2.1/2.2
│   │
│   ├── utils/                          # 工具
│   │   ├── __init__.py
│   │   ├── logging_config.py           # JSON Formatter + 文件/控制台输出
│   │   └── io.py                       # JSON 读写辅助
│   │
│   ├── search/                         # 学术检索（已有模块，保持不变）
│   │   ├── engine.py                   # 统一入口
│   │   ├── arxiv_client.py             # arXiv
│   │   ├── semantic_scholar_client.py  # SS
│   │   └── crossref_client.py          # Crossref
│   │
│   ├── parse/                          # PDF/文档解析（已有模块，保持不变）
│   │   └── pdf_parser.py
│   │
│   ├── reference/                      # 引用管理（已有模块，保持不变）
│   │   └── bibtex_manager.py
│   │
│   └── writer/                         # 写作辅助（已有模块，保持不变）
│       └── llm_helper.py
│
├── backend/
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                  # ★ 核心：所有 Pydantic 模型定义
│   │                                   # 已存在 DebateConfig / Argument / JudgeReport
│   │                                   # / FinalVerdict / EvidenceBrief 等
│   │
│   └── app.py                          # FastAPI 应用组装（替代简单 api.py）
│
├── experiments/                        # 评估实验管线（P2 / P3）
│   ├── benchmarks/
│   │   ├── gsm8k_loader.py
│   │   ├── politifact_loader.py
│   │   └── custom_loader.py
│   ├── baselines/
│   │   ├── single_llm_cot.py
│   │   ├── self_consistency.py
│   │   └── standard_mad.py
│   ├── ablations/
│   │   ├── ab1_no_coach.py
│   │   ├── ab2_no_poi.py
│   │   ├── ab3_single_judge.py
│   │   └── ab4_no_review.py
│   ├── metrics/
│   │   ├── accuracy.py
│   │   ├── evidence_coverage.py
│   │   └── citation_accuracy.py
│   └── scripts/
│       ├── run_parajudge.py
│       ├── run_baselines.py
│       └── aggregate_results.py
│
├── tests/                              # 单元测试与集成测试（新增）
│   ├── __init__.py
│   ├── test_evidence_builder.py
│   ├── test_problem_classifier.py
│   ├── test_speaker_evidence_closure.py
│   ├── test_review_engine.py
│   ├── test_judges.py
│   ├── test_final_judge_weights.py
│   ├── test_reasoning_chain.py
│   ├── test_mock_provider_reproducibility.py
│   ├── test_cli_run.py
│   └── test_api_routes.py
│
├── data/
│   ├── runs/                           # 运行输出（每个 run 一个子目录）
│   ├── cache/evidence/                 # 证据检索缓存
│   ├── domain_kb/
│   │   ├── math.yaml
│   │   ├── medical.yaml
│   │   ├── law.yaml
│   │   ├── engineering.yaml
│   │   ├── factcheck.yaml
│   │   └── general.yaml
│   └── custom_papers/
│
├── notebooks/parajudge_tutorial.ipynb  # 演示 Notebook
│
├── docs/                               # 项目文档
│   ├── ARCHITECTURE.md                 # 架构设计文档
│   ├── AGENT_DESIGN.md                 # Agent 设计规范（含 Prompt 模板约定）
│   ├── API_DESIGN.md                   # API 设计说明与示例
│   └── EVALUATION_DESIGN.md            # 评估方案与指标
│
├── requirements.txt                    # ★ 核心依赖（含新增 langgraph/Jinja2/PyYAML/tiktoken/pytest）
├── requirements-experimental.txt       # 实验依赖（sentence-transformers 等）
├── .env.example                        # 模板（含 DASHSCOPE_API_KEY / OPENAI_API_KEY 示例）
├── .gitignore                          # 已有 + 新增 data/runs / logs/*.log
└── README.md                           # 已更新，加入 ParaJudge 设计说明
```

### 11.2 关键模块与负责人规划

| 模块 | 负责人（占位） | 实现优先级 | 预估人周 | 依赖的前置模块 |
|:---|:---|:---|:---|:---|
| `backend/models/schemas.py` 扩展 | - | P0 | 0.5 | 无（直接扩展现有文件） |
| `src/llm/providers.py` | - | P0 | 1.0 | schemas |
| `src/llm/prompt_library.py` | - | P0 | 0.5 | providers |
| `src/knowledge/evidence.py` | - | P0 | 1.0 | `src/search/engine.py`（已有） |
| `src/knowledge/classifier.py` | - | P0 | 0.5 | providers |
| `src/debate/agent_base.py` | - | P0 | 0.5 | providers |
| `src/debate/coach.py` | - | P0 | 1.0 | agent_base + evidence |
| `src/debate/speaker.py` | - | P0 | 1.0 | coach |
| `src/debate/moderator.py` | - | P0 | 0.8 | agent_base + speaker + argument_index（v1.1 更新） |
| `src/debate/evidence_closure.py` | - | P0 | 0.5 | speaker |
| `src/debate/argument_index.py` | - | P0 | 0.5 | speaker |
| `src/debate/workflow.py` (Phase 1 Graph) | - | P0 | 1.0 | coach+speaker |
| `src/review/prosecutor.py` | - | P0 | 1.0 | agent_base |
| `src/review/defense.py` | - | P0 | 0.5 | prosecutor |
| `src/review/workflow.py` | - | P0 | 0.5 | prosecutor + defense |
| `src/judgment/judges.py` (5 Judges) | - | P0 | 1.5 | agent_base |
| `src/judgment/final_judge.py` | - | P0 | 1.0 | judges.py |
| `src/judgment/reasoning_chain.py` | - | P0 | 0.5 | final_judge |
| `src/judgment/report_generator.py` + Jinja2 模板 | - | P0 | 1.0 | final_judge + reasoning_chain |
| `src/orchestration/graph.py`（LangGraph 大图） | - | P0 | 1.0 | 以上全部 Phase 子图 |
| `cli.py` 扩展 | - | P0 | 1.0 | orchestration |
| `api.py` 扩展（FastAPI 路由） | - | P0 | 1.0 | orchestration |
| `src/knowledge/domain_kb.py` + 初始 YAML | - | P1 | 1.0 | 无依赖 |
| `src/debate/poi_engine.py` | - | P1 | 1.0 | speaker + workflow |
| `src/judgment/innovation_protect.py` | - | P1 | 0.5 | judges.py |
| `src/judgment/uncertainty.py` | - | P1 | 0.5 | judges.py |
| `utils/logging_config.py` | - | P1 | 0.5 | 无依赖 |
| `tests/` 单元测试 | - | P1 | 2.0 | 所有 P0 模块 |
| `experiments/` 基准测试 | - | P2 | 3.0 | 所有 P1 模块 |
| `notebooks/parajudge_tutorial.ipynb` | - | P2 | 0.5 | 所有 P0 |

### 11.3 里程碑计划

| 里程碑 | 时间 | 交付物 | 通过标准 |
|:---|:---|:---|:---|
| **M1: Week 1-2** | 第 1-2 周 | Pydantic 模型扩展 + LLM Provider + Phase 0（证据构建） | 可运行 `parajudge evidence "问题"` |
| **M2: Week 3-5** | 第 3-5 周 | Phase 1（辩论引擎核心 Coach+Speaker+Moderator） | 可运行 `parajudge debate`；Moderator 状态机 + 质量守门 + DebateSummary 完整产出 |
| **M3: Week 6-7** | 第 6-7 周 | Phase 2.1（审理引擎）+ Phase 2.2（裁决引擎基础版） | 可跑通端到端 `parajudge run`（Mock Provider） |
| **M4: Week 8** | 第 8 周 | CLI + API 完整打磨 + 裁决书 HTML | `parajudge run` 可交互使用；API 文档可浏览 |
| **M5: Week 9-10** | 第 9-10 周 | P1 增强：POI、创新保护、Domain KB | 端到端测试 5 个场景均通过 |
| **M6: Week 11-12** | 第 11-12 周 | 评估实验 + 性能优化 + 文档完善 | 基准测试可运行；人工评估模板就绪 |

---

**文档结束**。如需进一步展开特定模块的详细设计（如 Agent Prompt 模板的具体内容、LangGraph 节点伪代码、Judge 的评分算法细节），请指定要深入的章节。
