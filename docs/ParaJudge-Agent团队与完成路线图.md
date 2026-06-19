# ParaJudge Agent 团队结构与项目完成路线图

> 截至 2026-06-17 · v0.1.0 → v1.0.0 收尾阶段

---

## 一、Agent 团队结构（7 角色）

### 1.1 组织架构图

```
                        ┌──────────────────┐
                        │  架构师 Agent    │ ← 首席
                        │  (Architect)     │
                        └────────┬─────────┘
                                 │
        ┌────────────┬───────────┼────────────┬──────────────┐
        │            │           │            │              │
        ▼            ▼           ▼            ▼              ▼
   ┌────────┐  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────────┐
   │ 后端   │  │ 前端   │  │ 桌面端  │  │ AI 集成│  │ 测试/DevOps│
   │ Agent  │  │ Agent  │  │ Agent   │  │ Agent  │  │   Agent    │
   └────────┘  └────────┘  └─────────┘  └────────┘  └────────────┘
       │            │           │            │              │
       └────────────┴───────────┴────────────┴──────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   文档/PM Agent  │
                        └──────────────────┘
```

### 1.2 七大角色详细职责

| 角色 | 核心职责 | 主要交付物 | 关键技能 | 占用工时 |
| --- | --- | --- | --- | --- |
| **架构师 Architect** | 全栈架构决策、技术选型、API 规范、文档审阅 | 概要设计 / 详细设计 / ADR | 系统设计、DDD、分布式、消息队列 | 持续参与 |
| **后端 Backend** | FastAPI / 核心辩论引擎 / 数据库 / 任务调度 | `backend/api/` `src/debate/` `src/judgment/` `src/orchestration/` | Python 3.10+、Pydantic v2、asyncio、SQLAlchemy | 60% |
| **前端 Frontend** | UI 设计 / 动画 / SSE 客户端 / 状态管理 | `frontend/` | HTML5/CSS3/JS ES2020+、Fetch API、EventSource | 25% |
| **桌面端 Desktop** | PyWebView / 原生 API 桥 / 打包 | `desktop/` | pywebview、PyInstaller、NSIS | 15% |
| **AI 集成 AI-Integration** | 本地 LLM / Prompt 工程 / RAG / 论文检索 | `src/search/` `src/writer/` 集成层 | Ollama、LangChain、HuggingFace、向量库 | 40% |
| **测试/DevOps Test-DevOps** | pytest / 集成测试 / 性能测试 / CI/CD / Docker | `tests/` `.github/workflows/` | pytest、GitHub Actions、Linux、Docker | 25% |
| **文档/PM Doc-PM** | 需求文档 / 用户手册 / 项目计划书 | `docs/` | Markdown、LaTeX、流程图、UI/UX 基础 | 持续参与 |

### 1.3 协作规则

- **代码评审**：任何 PR 必须有 1 个 Architect + 1 个相关角色 Agent 评审通过
- **接口契约**：所有跨角色接口（前后端 API、桥接 API）必须先由 Architect 评审
- **每日同步**：每个 Agent 每日输出 1 份状态更新（已完成 / 进行中 / 阻塞）
- **阻塞升级**：超过 2 小时未解决的阻塞必须升级到 Architect
- **版本号**：每次合并由 Architect 决定是否升级 minor/major

### 1.4 当前任务分配

| 角色 | 当前 P0 任务 | 截止时间 |
| --- | --- | --- |
| Architect | 完成 S3 框架最终评估、确定 v1.0 范围 | D+0 |
| AI-Integration | **集成 Ollama 本地 LLM** | D+1 |
| Backend | 实现 Moderator 角色、KS 早停（Task T3） | D+2 |
| Frontend | 真实 LLM 对接 + 评分动画 | D+3 |
| Test-DevOps | 端到端测试 + GitHub Actions | D+3 |
| Desktop | 验证 Windows 打包 | D+5 |
| Doc-PM | 整合所有文档为最终交付包 | D+5 |

---

## 二、ParaJudge 原型机完成度评估

### 2.1 已完成（v0.1.0）

| 模块 | 完成度 | 位置 |
| --- | --- | --- |
| 核心数据模型 | ✅ 100% | [backend/models/schemas.py](file:///workspace/backend/models/schemas.py) |
| 统一 LLM 客户端（mock/openai/dashscope） | ✅ 100% | [src/writer/llm_client.py](file:///workspace/src/writer/llm_client.py) |
| Phase 0 证据构建器 | ✅ 95% | [src/debate/evidence_builder.py](file:///workspace/src/debate/evidence_builder.py) |
| Phase 1 极简辩论引擎 | ✅ 90% | [src/debate/simple_debate.py](file:///workspace/src/debate/simple_debate.py) |
| Phase 2.1 审理引擎 | ✅ 90% | [src/judgment/review_engine.py](file:///workspace/src/judgment/review_engine.py) |
| Phase 2.2 裁决引擎（五法官） | ✅ 90% | [src/judgment/judgment_engine.py](file:///workspace/src/judgment/judgment_engine.py) |
| 主编排器（orchestrator） | ✅ 95% | [src/orchestration/orchestrator.py](file:///workspace/src/orchestration/orchestrator.py) |
| CLI 入口 | ✅ 100% | [cli.py](file:///workspace/cli.py) |
| FastAPI 后端 | ✅ 100% | [backend/api/](file:///workspace/backend/api/) |
| 异步任务 + SSE 流 | ✅ 100% | [backend/api/job_manager.py](file:///workspace/backend/api/job_manager.py) |
| 前后端接口设计文档 | ✅ 100% | [docs/ParaJudge-前后端接口设计.md](file:///workspace/docs/ParaJudge-前后端接口设计.md) |
| 前端首页 | ✅ 100% | [frontend/index.html](file:///workspace/frontend/index.html) |
| 辩论室页面（SSE 流式） | ✅ 100% | [frontend/pages/debate-room.html](file:///workspace/frontend/pages/debate-room.html) |
| 裁决书页面 | ✅ 100% | [frontend/pages/verdict-report.html](file:///workspace/frontend/pages/verdict-report.html) |
| 前端 API 客户端 | ✅ 100% | [frontend/js/api.js](file:///workspace/frontend/js/api.js) |
| 桌面端 PyWebView 启动器 | ✅ 100% | [desktop/main.py](file:///workspace/desktop/main.py) |
| JS-Python 桥 | ✅ 100% | [desktop/bridge.py](file:///workspace/desktop/bridge.py) |
| PyInstaller 打包配置 | ✅ 100% | [desktop/ParaJudge.spec](file:///workspace/desktop/ParaJudge.spec) |
| NSIS 安装脚本 | ✅ 100% | [desktop/installer.nsi](file:///workspace/desktop/installer.nsi) |

**总计：19/19 模块完成，整体 v0.1.0 完成度 ≈ 88%**

### 2.2 未完成 / 待补完（v1.0 路线）

| 优先级 | 模块 | 原因 | 预计工时 |
| --- | --- | --- | --- |
| 🔴 P0 | **Moderator 角色**（主持人） | 设计已确认，代码未实现 | 1 d |
| 🔴 P0 | **本地 LLM 集成（Ollama）** | 满足"免费下载到本地"要求 | 0.5 d |
| 🔴 P0 | **T1 AEBG** 论点-证据二部图 | 创新点 1 | 1 d |
| 🟡 P1 | **T2 DPP 多样性约束** | 创新点 2 | 1 d |
| 🟡 P1 | **T3 KS 早停检验** | 创新点 3 | 0.5 d |
| 🟡 P1 | **T4 DS 证据理论融合** | 创新点 4 | 1 d |
| 🟢 P2 | pytest 单元测试套件 | 质量保障 | 1 d |
| 🟢 P2 | 端到端真实 LLM 测试 | 数据真实性 | 1 d |
| 🟢 P2 | 评估指标（BERTScore 等） | 论文级实验 | 1 d |

---

## 三、本地免费 LLM 集成方案

### 3.1 选型：Ollama

**理由**：

| 优势 | 说明 |
| --- | --- |
| 完全免费 | Apache 2.0 / MIT 协议 |
| 一键拉取 | `ollama pull qwen2.5:7b` |
| OpenAI 兼容 API | 端点 `http://localhost:11434/v1` |
| 跨平台 | Windows / macOS / Linux |
| 活跃生态 | 支持 100+ 开源模型 |
| 显存友好 | 7B 模型约需 6GB VRAM |

### 3.2 推荐模型矩阵

| 模型 | 大小 | 显存 | 中文 | 推理 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| **qwen2.5:7b** | 4.7 GB | 8GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 中文辩论主力（推荐） |
| **qwen2.5:14b** | 9.0 GB | 16GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 中文高质量 |
| **llama3.1:8b** | 4.9 GB | 8GB | ⭐⭐⭐ | ⭐⭐⭐⭐ | 英文辩论 |
| **mistral:7b** | 4.1 GB | 8GB | ⭐⭐ | ⭐⭐⭐⭐ | 英文轻量 |
| **deepseek-r1:7b** | 4.7 GB | 8GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 推理增强 |
| **gemma2:9b** | 5.4 GB | 10GB | ⭐⭐ | ⭐⭐⭐⭐ | 英文通用 |
| **phi3:medium** | 7.9 GB | 12GB | ⭐⭐⭐ | ⭐⭐⭐⭐ | 微软轻量 |
| **qwen2.5:3b** | 2.0 GB | 4GB | ⭐⭐⭐⭐ | ⭐⭐⭐ | 低显存备选 |

**默认推荐**：`qwen2.5:7b-instruct` （中文辩论最佳性价比）

### 3.3 ParaJudge 中的接入点

`src/writer/llm_client.py` 当前支持：
- `mock`（离线）
- `openai`（OpenAI / 兼容协议）
- `dashscope`（通义千问）

**新增 `ollama` provider**：
- 本质是 `openai` provider 指向 `http://localhost:11434/v1`
- 或独立实现以支持 ollama 特有参数（`num_ctx`, `num_gpu`）
