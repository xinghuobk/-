# ParaJudge 前后端接口设计文档

> **版本**：v0.1.0
> **设计日期**：2026-06-17
> **适用范围**：ParaJudge 多智能体辩论评估系统
> **读者**：前后端开发工程师、系统架构师

---

## 一、设计原则

| 原则 | 说明 |
| --- | --- |
| **RESTful** | 资源导向、HTTP 语义清晰、前后端解耦 |
| **同步 + 异步双通道** | 同步接口（POST /api/parajudge/run）适用于短任务；异步接口（POST /api/parajudge/jobs）适用于长任务并支持进度查询 |
| **类型安全** | 后端基于 Pydantic 2.x，前端基于 TypeScript 风格的 JSDoc + 静态字段约定 |
| **可流式输出** | 通过 Server-Sent Events（SSE）实时推送辩论过程（Phase / 评分 / 法官反馈） |
| **可缓存** | GET 类接口支持 ETag / Cache-Control；POST 结果可保存为 snapshot |
| **跨域** | CORS 默认开放 `*`，生产环境收紧为白名单 |

---

## 二、技术栈选型

| 层 | 技术 | 版本 | 理由 |
| --- | --- | --- | --- |
| 后端框架 | **FastAPI** | 0.110+ | 原生异步、自动 OpenAPI 文档、Pydantic 深度集成、Type hints 驱动 |
| 异步任务 | **asyncio + 后台 Task** | 内置 | 短期任务无需引入 Celery/Redis；保留接口扩展位 |
| LLM 客户端 | **LLMClient** | 自研 | 统一 mock/openai/dashscope，结构化 JSON 输出 |
| 数据模型 | **Pydantic v2** | 2.6+ | 比 v1 性能更好，model_validate_json 更快 |
| 服务端推送 | **SSE** | 内置 | 比 WebSocket 简单，比轮询更实时，适合单向状态推送 |
| 前端 | **原生 HTML/CSS/JS** | ES2020+ | 不依赖打包工具，便于演示与本地阅读 |
| 跨域 | **fastapi.middleware.cors** | 内置 | 仅生产时配置白名单 |

---

## 三、URL 路由总览

| 方法 | 路径 | 描述 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查（探活） |
| `GET` | `/api/version` | 服务版本与已注册模块 |
| `POST` | `/api/parajudge/run` | **同步执行**完整 ParaJudge 流程 |
| `POST` | `/api/parajudge/jobs` | **创建异步任务**，返回 job_id |
| `GET` | `/api/parajudge/jobs/{job_id}` | 查询异步任务状态 / 进度 |
| `GET` | `/api/parajudge/jobs/{job_id}/stream` | **SSE 流**实时推送进度 |
| `GET` | `/api/parajudge/jobs/{job_id}/result` | 获取最终结果（FullPipelineOutput） |
| `POST` | `/api/parajudge/run/phase/0` | 单独执行 Phase 0（证据构建） |
| `POST` | `/api/parajudge/run/phase/1` | 单独执行 Phase 1（辩论） |
| `POST` | `/api/parajudge/run/phase/2.1` | 单独执行 Phase 2.1（审理） |
| `POST` | `/api/parajudge/run/phase/2.2` | 单独执行 Phase 2.2（裁决） |
| `GET` | `/api/judges` | 列出系统注册的五位法官元数据 |
| `GET` | `/api/llm/providers` | 列出可用 LLM provider 及其状态 |
| `GET` | `/api/examples/questions` | 列出示例问题（来自附录 A） |

---

## 四、数据模型（请求 / 响应）

> 所有时间戳使用 ISO-8601；评分范围 0–100。

### 4.1 同步执行请求 `POST /api/parajudge/run`

```json
{
  "problem": "LLM 是否会在未来 10 年内取代人类在知识工作中的大部分岗位？",
  "pro_stance": "主张 LLM 将大幅取代人类知识工作",
  "con_stance": "主张 LLM 不会真正取代人类知识工作",
  "rounds": 3,
  "max_evidence": 20,
  "enable_llm_review": true,
  "llm": {
    "provider": "mock",
    "model": "mock-model",
    "api_key": null,
    "temperature": 0.7
  },
  "moderator": {
    "strictness": "normal",
    "duplicate_threshold": 0.85,
    "off_topic_threshold": 0.4
  }
}
```

| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `problem` | string | ✅ | — | 待辩论的问题 |
| `pro_stance` | string | ❌ | 自动生成 | 正方立场 |
| `con_stance` | string | ❌ | 自动生成 | 反方立场 |
| `rounds` | int 1–8 | ❌ | 3 | 辩论轮数（每轮 = 正方 + 反方各一次） |
| `max_evidence` | int 1–50 | ❌ | 20 | Phase 0 证据包最大条数 |
| `enable_llm_review` | bool | ❌ | true | 是否启用 LLM 辅助审理 |
| `llm.provider` | enum | ❌ | mock | mock / openai / dashscope |
| `llm.model` | string | ❌ | mock-model | 具体模型名 |
| `llm.api_key` | string | ❌ | null | 留空则读环境变量 |
| `llm.temperature` | float 0–2 | ❌ | 0.7 | 创造性 |
| `moderator.strictness` | enum | ❌ | normal | loose / normal / strict |
| `moderator.duplicate_threshold` | float 0.5–1.0 | ❌ | 0.85 | 重复警告阈值 |
| `moderator.off_topic_threshold` | float 0.1–0.9 | ❌ | 0.4 | 跑题警告阈值 |

### 4.2 同步执行响应 `200 OK`

```json
{
  "run_id": "pj-20240617-abc123",
  "problem": "...",
  "evidence_brief": { "...": "EvidenceBrief" },
  "transcript": { "...": "DebateTranscript" },
  "review": { "...": "ReviewReport" },
  "judgment": { "...": "JudgmentResult" },
  "total_time_sec": 8.42,
  "metadata": {
    "started_at": "2026-06-17T10:23:45Z",
    "finished_at": "2026-06-17T10:23:53Z",
    "llm_provider": "mock",
    "phase_durations": {
      "phase_0_evidence": 2.31,
      "phase_1_debate": 4.50,
      "phase_2_1_review": 0.92,
      "phase_2_2_judgment": 0.69
    }
  }
}
```

### 4.3 异步任务创建请求 `POST /api/parajudge/jobs`

与 `4.1` 一致；额外支持：

```json
{
  "callback_url": "https://your.app/webhook",  // 可选，完成时回调
  "stream": true                                 // 是否启用 SSE
}
```

### 4.4 异步任务创建响应 `202 Accepted`

```json
{
  "job_id": "job-20240617-xyz789",
  "status": "queued",
  "created_at": "2026-06-17T10:23:45Z",
  "stream_url": "/api/parajudge/jobs/job-20240617-xyz789/stream",
  "result_url": "/api/parajudge/jobs/job-20240617-xyz789/result"
}
```

### 4.5 任务状态 `GET /api/parajudge/jobs/{job_id}`

```json
{
  "job_id": "job-...",
  "status": "running",       // queued / running / completed / failed / cancelled
  "current_phase": "phase_1_debate",
  "progress": 0.55,          // 0.0–1.0
  "phase_durations": { "...": "..." },
  "estimated_remaining_sec": 4.1,
  "error": null
}
```

### 4.6 SSE 流事件（EventStream）

事件类型：

| event | data 内容 | 触发时机 |
| --- | --- | --- |
| `job.started` | `{ run_id, started_at }` | 任务开始 |
| `phase.started` | `{ phase: "phase_0_evidence" }` | 进入某阶段 |
| `phase.progress` | `{ phase, progress, message }` | 阶段内子进度 |
| `argument.added` | `{ arg_id, side, content, evidence_refs, round_index }` | 新论点产生 |
| `review.issue` | `{ issue_id, severity, issue_type, target_arg_id }` | 审理发现问题 |
| `judge.scored` | `{ judge_type, pro_score, con_score }` | 某位法官完成评分 |
| `phase.finished` | `{ phase, duration_sec }` | 阶段完成 |
| `job.completed` | `{ result_url, total_time_sec }` | 任务完成 |
| `job.failed` | `{ error_code, error_message, traceback }` | 任务失败 |

### 4.7 错误响应

```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "problem 字段不能为空",
    "field": "problem",
    "trace_id": "tr-20240617-001"
  }
}
```

| 错误码 | HTTP | 含义 |
| --- | --- | --- |
| `INVALID_ARGUMENT` | 422 | 请求参数校验失败 |
| `LLM_PROVIDER_ERROR` | 502 | LLM provider 调用失败 |
| `LLM_RATE_LIMIT` | 429 | 触发限流 |
| `JOB_NOT_FOUND` | 404 | job_id 不存在 |
| `JOB_ALREADY_RUNNING` | 409 | job 已被占用 |
| `INTERNAL_ERROR` | 500 | 未捕获的异常 |

---

## 五、字段引用映射（前端字段 ↔ 后端模型）

| 前端字段 | 后端模型 | 位置 |
| --- | --- | --- |
| `runId` | `run_id` | FullPipelineOutput |
| `problem` | `problem` | FullPipelineOutput |
| `evidenceList` | `evidence_brief.items` | EvidenceBrief |
| `transcript` | `transcript.arguments` | DebateTranscript |
| `reviewIssues` | `review.issues` | ReviewReport |
| `judges` | `judgment.judge_scores` | JudgmentResult |
| `winner` | `judgment.winner` | JudgmentResult |
| `proScore` | `judgment.pro_final_score` | JudgmentResult |
| `conScore` | `judgment.con_final_score` | JudgmentResult |
| `reasoningChain` | `judgment.reasoning_chain_pro/con` | JudgmentResult |

---

## 六、状态机

```
                    ┌──────────────┐
        创建 ───▶   │   QUEUED     │
                    └──────┬───────┘
                           │ 调度
                           ▼
                    ┌──────────────┐
                    │   RUNNING    │──┐
                    │              │  │ cancel
                    └──────┬───────┘  │
        ┌──────────────────┤          │
        │                  │          ▼
        ▼                  │   ┌──────────────┐
  ┌──────────┐             │   │  CANCELLED   │
  │ COMPLETED│             │   └──────────────┘
  └──────────┘             │
        ▲                  ▼
        │           ┌──────────────┐
        └───────────│   FAILED     │
        (retry)     └──────────────┘
```

---

## 七、安全与限流

| 项 | 策略 |
| --- | --- |
| API Key | 不在 URL 中传递；后端从环境变量或请求体读取；日志中脱敏 |
| CORS | 默认 `*`，生产可配置白名单 |
| 限流 | `/api/parajudge/run` 默认 10 req/min/IP（基于内存计数器） |
| 输入长度 | `problem` ≤ 1000 字符，`rounds` ≤ 8 |
| 输出体积 | 单论点 ≤ 1500 字符，防止 prompt injection |
| 日志 | 不记录 LLM 完整响应，仅记录 hash + 长度 |

---

## 八、前端调用约定

- **Base URL**：`http://localhost:8000`（开发），`https://api.parajudge.cn`（生产）
- **超时**：同步接口 60s；异步创建接口 5s
- **Content-Type**：`application/json; charset=utf-8`
- **错误处理**：捕获 4xx/5xx，统一通过 `notify.error(...)` 提示
- **重试**：仅对 502/503/504 自动重试 1 次，间隔 2s
- **SSE**：使用 `EventSource` 原生 API，断线自动重连

---

## 九、文件结构

```
backend/
  api/
    __init__.py
    server.py             # FastAPI 入口
    routers/
      health.py
      parajudge.py
      judges.py
      llm.py
      examples.py
    schemas_api.py        # API 层数据模型（请求/响应）
    job_manager.py        # 异步任务管理
    sse.py                # SSE 事件生成器
  models/
    schemas.py            # 已有核心数据模型
```

---

## 十、后续演进

1. 引入 Redis 持久化 job（崩溃恢复）
2. 引入 WebSocket 替代 SSE（双向）
3. 支持流式 LLM 输出（chunked 推送到前端）
4. 增加 `/api/parajudge/runs` 历史列表接口
5. 增加 OpenTelemetry 追踪（trace_id 贯穿全链路）
