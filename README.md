# ParaJudge - 议会制辩论·合议庭裁决：面向高质量推理的多阶段多角色 LLM 系统

> **项目代号**：ParaJudge（Parliamentary Debate + Judgment Bench）
>
> 以真实议会制辩论与合议庭审判为灵感，构建一个三阶段多角色系统，为高风险决策场景提供透明、可审计、可质疑的 AI 推理能力。

---

## 一、项目定位

**ParaJudge** 是一个基于 **LangGraph** 的多智能体推理框架，旨在解决当前单一 LLM 及简单多智能体辩论（MAD）系统的若干核心问题：

| 问题 | ParaJudge 的方法 |
|------|-----------------|
| 同质化推理偏差 | 通过为每个 Agent 设置差异化目标函数（目标驱动异质性）产生推理多样性 |
| 论证质量缺乏制衡 | 引入检察官-辩护律师独立审理阶段，系统性发现辩论策略性遗漏 |
| 裁决黑箱化 | 5 位专业法官并行评估，裁决官输出类判决书推理链，每条结论标注证据来源 |
| 证据幻觉 | 证据闭包：所有论证必须引用预构建的 Evidence Brief 中的证据，系统自动核验引用 |
| 创新问题天然保守 | 创新保护机制：缺乏先例不扣分，未验证假设显式标注 + 可信度评估 |

---

## 二、系统架构（三阶段流程）

```
┌──────────────────────────────────────────────────────────────────────┐
│ 阶段 0: 证据与知识库准备                                              │
│   ├── ProblemClassifier 识别问题类型（事实/决策/创新/开放）           │
│   ├── Evidence Brief: 统一检索（arXiv + S2 + Crossref）               │
│   ├── Domain KB: 领域原则库 + 历史案例库                               │
└──────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌──────────────────────────────────────▼─────────────────────────────────┐
│ 阶段 1: 议会制团队辩论（8 个 Agent: 2 教练 + 6 辩手）                   │
│                                                                         │
│  正方: [PC 教练-不对外发言] → PM/MG/GW 辩手（构建框架 → 深化 → 总结）    │
│  反方: [OC 教练-不对外发言] → LO/MO/OW 辩手（攻击 → 深入 → 总结）       │
│    ↑                                                               ↑     │
│    └─────────────── POI 段间质询（交叉质询） ──────────────────────┘     │
│    └─────────────── 证据闭包 + 引用验证 ────────────────────────────┘     │
│                                                                         │
│  输出: 完整辩论记录 + 结构化论点索引（Argument Index） + POI 交互日志    │
└──────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌──────────────────────────────────────▼─────────────────────────────────┐
│ 阶段 2.1: 检察官-辩护律师独立审理（2 个 Agent，独立于阶段 1）              │
│                                                                         │
│  [Prosecutor 检察官] 扫描阶段 1 论点 → 发现论证漏洞 + 证据选择性呈现    │
│  [Defense Attorney 辩护律师] 为被攻击论点提供最佳辩护 + 补充证据         │
│  ↔ 2-3 轮对质交互                                                       │
│                                                                         │
│  输出: 审理报告（降级/升级论点清单） + 补充证据发现列表                   │
└──────────────────────────────────────┬─────────────────────────────────┘
                                        │
┌──────────────────────────────────────▼─────────────────────────────────┐
│ 阶段 2.2: 五维度专业化法官裁决（6 个 Agent 并行评估）                     │
│                                                                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │ E-Judge   │  │ L-Judge   │  │ P-Judge   │  │ C-Judge   │  │ I-Judge │ │
│  │ 证据审查   │  │ 逻辑审查   │  │ 原则审查   │  │ 案例审查   │  │ 创新审查  │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │
│                                    ↓                                        │
│                              [F-Judge 裁决官]                               │
│                                · 综合评分权重分配                            │
│                                · 推理链生成（每条结论标注证据/原则/案例）    │
│                                · 不确定性标注                               │
│                                · 类判决书 HTML/PDF 输出                      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 核心创新点（与标准 MAD 对比）

| 机制 | 标准 MAD | ParaJudge |
|------|---------|-----------|
| 异质性来源 | 相同模型，不同 Prompt/多模型，同质 | 目标驱动异质性：每个 Agent 有明确不同的目标函数 |
| 角色设计 | 正方 vs 反方，简单二分类 | 教练-辩手双角色 + 检察官-辩护律师 + 五维专业法官（共 16 个角色） |
| 论证交互 | 轮流独白 | 支持 POI 段间质询，发言人必须即时响应 |
| 证据使用 | Agent 自发引用，可能幻觉 | 证据闭包：只能使用 Evidence Brief 中的证据，系统强制核验 |
| 审理阶段 | 无 | 独立检察官-辩护律师审理，发现策略性遗漏 |
| 裁决机制 | 简单投票或整体评分 | 五维度专业化法官并行评估，裁决官输出推理链 |
| 创新问题 | 天然保守，先例越少越否定 | 创新保护机制，假设显式标注，暂定结论保护 |
| 可追溯性 | 黑箱，结论不可追溯 | 类判决书推理链，每条结论标注证据/原则/案例来源 |
| 不确定性管理 | 不显式处理 | 系统主动标注"本结论基于哪些未验证假设" |

---

## 三、目录结构

```
/workspace/
├── OPENING_REPORT.md                 # 开题报告（完整学术文档）
├── PROJECT_PROPOSAL.md              # 项目计划书（详细开发计划）
├── PROJECT_PLAN.md                  # 开发进度与模块规划
├── research_report.md              # MAD 领域调研报
├── README.md                       # 本文件：项目总览
├── requirements.txt                # 核心依赖
├── requirements-experimental.txt   # Jupyter 等扩展依赖
│
├── cli.py                          # CLI 入口（Typer）
├── api.py                          # FastAPI 入口
│
├── src/                            # 核心算法与业务模块
│   ├── search/
│   │   ├── engine.py              # 统一文献检索（arXiv/S2/Crossref）
│   │   ├── arxiv_client.py
│   │   ├── semantic_scholar_client.py
│   │   └── crossref_client.py
│   ├── parse/
│   │   ├── pdf_parser.py          # PDF 解析（PyMuPDF + pdfplumber）
│   │   └── text_cleaner.py
│   ├── reference/
│   │   └── bibtex_manager.py      # BibTeX 管理与 APA/GB7714 导出
│   ├── writer/
│   │   ├── llm_helper.py          # LLM 写作辅助（摘要/翻译/润色/综述/大纲）
│   │   └── prompt_templates.py
│   ├── knowledge/                 # 知识管理（Evidence Brief + Domain KB）
│   │   ├── evidence.py            # Evidence Brief 构建
│   │   ├── domain_kb.py           # 原则库 + 案例库
│   │   ├── classifier.py          # 问题类型分类器
│   │   └── __init__.py
│   ├── debate/                    # 辩论引擎（阶段 1）
│   │   ├── roles.py               # 角色定义与 Prompt
│   │   ├── coach.py              # 教练逻辑（战术协调）
│   │   ├── speaker.py            # 辩手逻辑（发言）
│   │   ├── poi.py                # POI 段间质询机制
│   │   ├── evidence.py           # 证据闭包与引用验证
│   │   ├── engine.py             # LangGraph 编排主流程
│   │   └── __init__.py
│   ├── review/                    # 审理引擎（阶段 2.1）
│   │   ├── prosecutor.py          # 检察官
│   │   ├── defense.py            # 辩护律师
│   │   ├── engine.py             # 审理主流程
│   │   └── __init__.py
│   ├── judgment/                  # 裁决引擎（阶段 2.2）
│   │   ├── judges.py             # E/L/P/C/I 五位法官
│   │   ├── innov_protect.py      # 创新保护机制
│   │   ├── verdict_chain.py      # 类判决书推理链生成
│   │   ├── engine.py             # 裁决主流程
│   │   ├── report_generator.py   # HTML/PDF 裁决报告
│   │   └── __init__.py
│   └── utils/
│       └── io.py                  # JSON/文本读写工具
│
├── backend/                        # 服务层
│   ├── app.py                     # FastAPI 应用（含辩论/裁决 API）
│   └── models/
│       ├── __init__.py
│       └── schemas.py             # Pydantic 模型（所有数据结构定义）
│
├── experiments/                   # 评估实验
│   ├── benchmarks/                # 基准数据集加载
│   ├── ablations/                 # 消融实验 A1-A8
│   ├── scripts/                   # 实验脚本
│   └── reports/                   # 评估报告输出
│
├── data/                          # 知识库与数据集
│   ├── evidence/                  # Evidence Brief
│   └── domain_kb/                 # 领域原则库（math/medical/law/factcheck/engineering YAML）
│
├── notebooks/                     # Notebook 演示与分析
└── tests/                         # 单元测试与集成测试
```

---

## 四、快速开始

### 环境要求

- **Python** ≥ 3.10（项目在 3.14 下开发验证）
- **LLM API**：OpenAI API 兼容或通义千问（dashscope）
- **网络**：能够访问 arXiv/Semantic Scholar/Crossref API

### 安装依赖

```bash
cd /workspace
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 如需 Notebook：
# pip install -r requirements-experimental.txt
```

### 配置环境变量（可选）

```bash
# 在 /workspace/.env 中配置
OPENAI_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx           # 通义千问
```

---

## 五、核心功能与示例

### 1. 文献检索（Search - 已有）

```python
from backend.models.schemas import SearchQuery, SearchSource
from src.search.engine import unified_search

result = unified_search(SearchQuery(
    keyword="multi-agent debate",
    year_min=2023,
    max_results=20,
    sources=[SearchSource.ARXIV, SearchSource.SEMANTIC_SCHOLAR, SearchSource.CROSSREF],
))
print(f"命中 {result.total_count} 篇，耗时 {result.used_time:.2f}s")
```

### 2. PDF 解析（Parse - 已有）

```bash
python -m src parse paper.pdf --output paper.json --sections
```

### 3. 引用管理（Reference - 已有）

```bash
python -m src reference library.bib --search "multi-agent" --format apa
```

### 4. LLM 写作辅助（Writer - 已有）

```bash
python -m src writer summarize --input paper_text.txt --output summary.md --max-sentences 5
```

### 5. ParaJudge 三阶段推理（阶段 1-5 开发）

```python
from src.knowledge.evidence import EvidenceBrief
from src.knowledge.classifier import ProblemClassifier
from src.debate.engine import DebateEngine
from src.review.engine import ReviewEngine
from src.judgment.engine import JudgmentEngine

# 0. 问题与证据准备
problem = "多智能体辩论系统能否提升数学推理的准确性？"
evidence_brief = EvidenceBrief.build_from_search(problem, max_evidence=20)
problem_type = ProblemClassifier.classify(problem)

# 1. 阶段 1：团队辩论（含 POI）
debate_state = DebateEngine().run(problem, evidence_brief)

# 2. 阶段 2.1：独立审理
review_state = ReviewEngine().run(debate_state, evidence_brief)

# 3. 阶段 2.2：五维法官裁决
verdict = JudgmentEngine().run(review_state, evidence_brief, problem_type)

# 输出类判决书（类判决书 HTML）
from src.judgment.report_generator import generate_verdict_report
generate_verdict_report(verdict, output_path="verdict.html")
```

### 6. CLI 入口

```bash
# 辩论子命令（后续实现）
python -m src parajudge debate \
    --problem "多智能体辩论系统能否提升数学推理的准确性？" \
    --evidence evidence.json \
    --output debate.json

# 审理子命令
python -m src parajudge review \
    --debate debate.json \
    --output review.json

# 裁决子命令
python -m src parajudge judge \
    --review review.json \
    --output verdict.html

# 端到端推理（三阶段）
python -m src parajudge reason \
    --problem "..." \
    --output report.html
```

---

## 六、主要依赖

| 分组 | 包名 | 版本建议 | 用途 |
|------|------|----------|------|
| 编排层 | LangGraph | ≥ 0.2.0 | 有状态图工作流，辩论流程编排 |
| LLM | LangChain | ≥ 0.3.0 | LLM 调用、工具链 |
| PDF | PyMuPDF | ≥ 1.24.0 | PDF 文本提取（`fitz`） |
| 检索 | arxiv | ≥ 2.1.0 | arXiv API 封装 |
| 引用 | bibtexmanager | — | BibTeX 管理与 APA/GB7714 导出 |
| Web 服务 | FastAPI | ≥ 0.111.0 | 现代类型安全的 API 框架 |
| CLI | Typer | ≥ 0.12.0 | 基于类型注解的现代 CLI 框架 |
| CLI | Rich | ≥ 13.7.0 | 终端彩色输出 |
| 数据 | Pydantic | v2 | 结构化数据定义 |

---

## 七、开发路线与里程碑

| 阶段 | 时间 | 交付物 | 验收标准 |
|------|------|--------|----------|
| **P1** | 第 1-2 月 | 知识管理 + 阶段 1 辩论引擎 | 10 个示例问题冒烟测试通过 |
| **P2** | 第 3 月 | 审理引擎 + POI 机制完善 | 阶段 1+2.1 端到端可运行 |
| **P3** | 第 4 月 | 裁决引擎 + 推理链输出 | 三阶段完整流程，输出类判决书 |
| **P4** | 第 5 月 | 创新保护 + 多领域适配 | 创新问题可得到"非保守"评估 |
| **P5** | 第 6-7 月 | 评估实验与基线对比 | 完整评估报告，实验结论可复现 |
| **P6** | 第 8-9 月 | 论文 + 代码 Release | 主论文投稿 + 开源 Release |
| **P7** | 第 10-12 月 | 扩展与应用 | 可部署原型系统 |

详细开发计划见 [PROJECT_PLAN.md](file:///workspace/PROJECT_PLAN.md) 与 [PROJECT_PROPOSAL.md](file:///workspace/PROJECT_PROPOSAL.md)。

---

## 八、评估指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 推理准确率 | ≥ 标准 MAD + 5-10% | MATH / MedQA / POLITIFACT 基准 |
| 证据引用准确率 | ≥ 95% | 系统自动核验 |
| 裁决可追溯性评分 | ≥ 80% | 人工评估 |
| 创新问题相关性 | 显著高于标准 MAD (p<0.05) | 与人类专家评估对比 |
| 测试覆盖率 | ≥ 80% | pytest-cov |

详细评估方案与消融实验设计见 [OPENING_REPORT.md](file:///workspace/OPENING_REPORT.md) 的第七、八章。

---

## 九、学术背景与参考文献

核心论文领域：

- **AI Safety via Debate**（Irving et al., 2018）—— 奠基性论文
- **Improving Factuality and Reasoning through Multi-Agent Debate**（Du et al., 2023）—— 现代 MAD 框架（MIT）
- **Should we be going MAD?**（Smit et al., 2024）—— 批判性评估
- **MALLM: Persona-Driven Multi-Agent Debate**（Becker et al., 2025）
- **ARMOR-MAD**（Niu & Zhang, 2026）—— 异质智能体 + 专家混合路由
- **Measuring and Mitigating Identity Bias via Anonymization**（Choi et al., 2025）
- **The Confident Liar**（Hu et al., 2026）—— 辩论过程可信度

完整调研报告见 [research_report.md](file:///workspace/research_report.md)。

---

## 十、文档索引

| 文档 | 内容 |
|------|------|
| [OPENING_REPORT.md](file:///workspace/OPENING_REPORT.md) | 开题报告：背景、创新点、评估方案、预期贡献 |
| [PROJECT_PROPOSAL.md](file:///workspace/PROJECT_PROPOSAL.md) | 项目计划书：架构、模块规划、资源预算、风险管理 |
| [PROJECT_PLAN.md](file:///workspace/PROJECT_PLAN.md) | 详细开发计划：模块进度、API/CLI 一览 |
| [research_report.md](file:///workspace/research_report.md) | MAD 领域调研：论文综述、技术栈、类似项目分析 |
| [README.md](file:///workspace/README.md) | 本文件：项目总览、快速开始、功能示例 |

---

## 十一、贡献说明

欢迎提交 Issue 与 Pull Request。

1. **保持小而清晰的变更**：每个 PR 聚焦一个功能点或问题修复
2. **遵循现有风格**：模块按 `src/<domain>/xxx.py` 组织，公共模型放在 `backend/models/`
3. **提供最小可运行示例**：对于新加入的 API 或 CLI 子命令，附上简短调用示例
4. **文档同步**：新增功能请同步更新本 README 与 `PROJECT_PLAN.md` 的相应章节

---

## License

本项目采用 **MIT License** 开源，允许商业与非商业使用。
