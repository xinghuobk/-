# ParaJudge · 学术论文工具链

> **项目代号**：ParaJudge（Parliamentary Debate + Judgment Bench）
>
> 提供一整套学术论文处理工具，包括**文献检索、PDF 解析、引用管理、LLM 写作辅助**。
> 规划中的多智能体辩论系统将基于这些工具构建高质量推理框架。

---

## 一、项目定位

**ParaJudge** 项目分为两个层次：

### 1.1 已实现：学术论文工具链

| 模块 | 功能 | 主要依赖 |
|------|------|---------|
| **文献检索** | 多源论文搜索（arXiv、Semantic Scholar、Crossref） | `httpx` + 各平台 API |
| **PDF 解析** | 提取标题、作者、章节、参考文献、元数据 | `PyMuPDF` (`fitz`) |
| **引用管理** | BibTeX 库管理、APA/GB7714 格式导出 | 内置解析器与模板 |
| **写作辅助** | 摘要、翻译、润色、综述、大纲（支持 mock/openai/dashscope） | `LangChain` 框架 |

### 1.2 规划中：多智能体辩论系统

参考真实议会制辩论与合议庭审判流程，构建三阶段多角色推理框架：

- **阶段 1**：团队辩论（教练-辩手双角色，POI 段间质询）
- **阶段 2.1**：检察官-辩护律师独立审理
- **阶段 2.2**：五维度专业化法官裁决

核心创新：**目标驱动异质性**、**证据闭包**、**类判决书推理链**、**创新保护机制**。

*详细设计与研究方案参见 [OPENING_REPORT.md](file:///workspace/OPENING_REPORT.md) 与 [PROJECT_PROPOSAL.md](file:///workspace/PROJECT_PROPOSAL.md)*

---

## 二、目录结构

```
/workspace/
├── OPENING_REPORT.md                 # 开题报告（研究方案）
├── PROJECT_PROPOSAL.md              # 项目计划书（详细规划）
├── PROJECT_PLAN.md                  # 开发规划（模块与进度）
├── research_report.md               # MAD 领域调研
├── requirements.txt                 # 核心依赖
├── requirements-experimental.txt    # 扩展依赖（Jupyter 等）
│
├── cli.py                           # CLI 入口（Typer）
├── api.py                           # FastAPI 入口
├── main.py                          # 调用 cli.main()
│
├── src/                             # 核心算法与业务模块
│   ├── search/                      # 文献检索模块
│   │   ├── engine.py               # 统一搜索入口（去重排序）
│   │   ├── arxiv_client.py         # arXiv API 客户端
│   │   ├── semantic_scholar_client.py  # Semantic Scholar 客户端
│   │   ├── crossref_client.py      # Crossref API 客户端
│   │   └── __init__.py
│   │
│   ├── parse/                       # PDF 解析模块
│   │   ├── pdf_parser.py           # PDFParser（章节/引用/元数据）
│   │   ├── text_cleaner.py         # 文本清洗（页眉页脚/摘要提取）
│   │   └── __init__.py
│   │
│   ├── reference/                   # 引用管理模块
│   │   ├── bibtex_manager.py       # BibTeX 解析/保存/导出
│   │   └── __init__.py
│   │
│   ├── writer/                      # 写作辅助模块
│   │   ├── llm_helper.py           # AcademicWriter（5大功能+3种Provider）
│   │   ├── prompt_templates.py     # Prompt 模板库
│   │   └── __init__.py
│   │
│   └── utils/                       # 工具模块
│       ├── io.py                   # JSON/文本读写
│       └── __init__.py
│
├── backend/                         # 服务层
│   └── models/
│       ├── schemas.py              # Pydantic 模型（所有数据结构定义）
│       └── __init__.py
│
├── notebooks/                       # Jupyter 演示与分析
│   └── ...
│
├── data/                           # 数据文件（如 PDF、BibTeX 输出）
├── docs/                           # 文档（如 USAGE.md）
│
├── index.html                      # 示例前端页面
└── .gitignore                      # Git 忽略规则
```

---

## 三、核心模块说明

### 3.1 文献检索 (`src.search`)

- **多源并发搜索**：同时查询 arXiv、Semantic Scholar、Crossref
- **智能去重**：基于 DOI 和标题相似度去重
- **统一排序**：按引用数排序，最相关优先
- **丰富元数据**：标题、作者、年份、DOI、引用计数、摘要、URL、PDF 链接

### 3.2 PDF 解析 (`src.parse`)

- **PDFParser 类**：基于 PyMuPDF
- **章节识别**：自动识别论文各章节标题与内容
- **引用提取**：识别参考文献列表
- **元数据提取**：标题、作者、关键词、年份、DOI
- **文本清洗**：去除页眉页脚、规范化空白

### 3.3 引用管理 (`src.reference`)

- **BibTeXManager**：读取、保存、搜索 BibTeX 库
- **多种导出格式**：APA 格式、GB7714 格式、原始 BibTeX
- **PDF 自动元数据提取**：从 PDF 解析结果自动生成引用条目

### 3.4 写作辅助 (`src.writer`)

- **AcademicWriter** 类，五大功能：
  - `summarize_text()`：生成学术摘要
  - `translate_academic()`：学术翻译（中英互译）
  - `polish_paragraph()`：润色与风格优化
  - `generate_literature_review()`：基于多篇论文生成综述
  - `generate_outline()`：生成结构化论文大纲
- **三 Provider 支持**：mock（快速原型）、openai、dashscope（通义千问）
- **丰富 Prompt 模板**：中英文混合，覆盖多种学术场景

---

## 四、快速开始

### 4.1 环境要求

- **Python** ≥ 3.10（推荐 3.11+，项目在 3.14 下验证）
- **网络**：能够访问 arXiv / Semantic Scholar / Crossref API
- **可选**：OpenAI API 或 DashScope（通义千问）密钥（用于写作辅助功能）

### 4.2 安装依赖

```bash
cd /workspace
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 如需 Notebook 支持：
# pip install -r requirements-experimental.txt
```

### 4.3 环境变量（可选）

在 `/workspace/.env` 中配置：

```env
OPENAI_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx            # 通义千问
# LLM_PROVIDER=openai               # 可选：默认 mock
# LLM_MODEL=gpt-4o                  # 可选：默认 mock-model
```

### 4.4 验证安装

```bash
cd /workspace
python3 -c "
from src.search import SearchQuery, SearchSource
from src.parse import PDFParseResult, parse_pdf
from src.reference.bibtex_manager import BibTeXManager
from src.writer.llm_helper import AcademicWriter
print('✓ 所有核心模块导入成功')
"
```

---

## 五、使用示例

### 5.1 Python API

```python
# 1) 文献检索
from src.search import unified_search, SearchQuery, SearchSource

result = unified_search(SearchQuery(
    keyword="multi-agent debate",
    year_min=2023,
    max_results=20,
    sources=[SearchSource.ARXIV, SearchSource.SEMANTIC_SCHOLAR, SearchSource.CROSSREF],
))
print(f"命中 {result.total_count} 篇，耗时 {result.used_time:.2f}s")
for paper in result.papers[:5]:
    print(f"- {paper.title} ({paper.year}), DOI: {paper.doi}")

# 2) PDF 解析
from src.parse import parse_pdf

result = parse_pdf("/path/to/paper.pdf")
print(f"标题: {result.metadata.title}")
print(f"作者: {', '.join(result.metadata.authors)}")
print(f"章节数: {len(result.sections)}, 参考文献: {len(result.references)}")

# 3) 引用管理
from src.reference.bibtex_manager import BibTeXManager, generate_bibtex_from_paper

manager = BibTeXManager()
manager.load_file("library.bib")
for entry in manager.search("LLM"):
    print(f"[{entry.key}] {entry.fields.get('title', '')}")

# 导出为 APA 或 GB7714 格式
for entry in manager.entries:
    print(manager.to_apa(entry))

# 4) 写作辅助（默认 mock 模式，无需 API Key）
from src.writer.llm_helper import AcademicWriter

writer = AcademicWriter(provider="mock", model="mock-model")
summary = writer.summarize_text("这里是一段需要摘要的学术文本...")
print(summary.output)

# 也可以使用真实 Provider（需要 API Key）
# writer = AcademicWriter(provider="openai", model="gpt-4o")
# writer = AcademicWriter(provider="dashscope", model="qwen-max")
```

### 5.2 CLI 命令（需要安装 typer、rich 等依赖）

```bash
# 搜索论文
python3 cli.py search run "multi-agent debate" \
    --sources arxiv,crossref,semantic \
    --year-min 2023 --max 15 \
    --output search_results.json

# 解析 PDF
python3 cli.py parse run paper.pdf --sections \
    --output-json paper_parse.json --output-text paper_text.txt

# 引用管理
python3 cli.py ref add "论文标题或 PDF 路径" --authors "A; B; C" --year 2024 --bib mylib.bib
python3 cli.py ref list mylib.bib --keyword "LLM"
python3 cli.py ref export mylib.bib --format apa --out references.txt

# 写作辅助
python3 cli.py writer summary input.txt --provider mock --model mock-model --max-sentences 5
python3 cli.py writer translate "中文或英文段落" --target-lang zh-CN
python3 cli.py writer polish paragraph.txt --style academic
python3 cli.py writer review summaries.txt --topic "多智能体辩论"
python3 cli.py writer outline "论文主题" --sections 8
```

### 5.3 Web API（需要安装 fastapi/uvicorn）

```bash
# 启动 API 服务
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 然后访问：
#   http://localhost:8000/health          — 健康检查
#   http://localhost:8000/docs             — Swagger 文档
#   http://localhost:8000/redoc            — ReDoc 文档
#   http://localhost:8000/openapi.json     — OpenAPI 规范
```

主要 API 端点：

| 方法 | 路径 | 功能 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/v1/search` | 学术论文搜索 |
| `POST` | `/api/v1/parse/pdf` | PDF 解析 |
| `POST` | `/api/v1/reference/generate-bibtex` | 生成 BibTeX |
| `POST` | `/api/v1/reference/to-format` | BibTeX 格式转换 |
| `POST` | `/api/v1/write/summary` | 文本摘要 |
| `POST` | `/api/v1/write/translate` | 学术翻译 |
| `POST` | `/api/v1/write/polish` | 文本润色 |
| `POST` | `/api/v1/write/review` | 文献综述 |
| `POST` | `/api/v1/write/outline` | 生成大纲 |

---

## 六、核心依赖

| 包名 | 用途 |
|------|------|
| **PyMuPDF (`fitz`)** | PDF 文本提取与解析 |
| **httpx** | 现代 HTTP 客户端（访问各平台 API） |
| **pydantic** | 数据模型定义与验证 |
| **fastapi** | Web API 框架 |
| **uvicorn** | ASGI 服务器 |
| **typer** | CLI 框架（基于类型注解） |
| **rich** | 终端彩色输出与表格 |
| **langchain** | LLM 调用框架（写作辅助） |
| **langchain-community** | 社区 Provider 支持 |
| **dashscope** | 通义千问 SDK |
| **python-dotenv** | `.env` 文件加载 |

---

## 七、主要数据结构

所有数据模型定义在 `backend/models/schemas.py` 中：

| 模型 | 用途 | 关键字段 |
|------|------|---------|
| **SearchQuery** | 搜索请求参数 | `keyword`, `sources`, `year_min`, `max_results` |
| **SearchSource** | 搜索源枚举 | `arxiv`, `semantic_scholar`, `crossref`, `openalex`, `google_scholar` |
| **SearchResult** | 搜索结果 | `total_count`, `papers[]`, `used_time` |
| **PaperMeta** | 论文元数据 | `title`, `authors`, `year`, `doi`, `citation_count`, `abstract`, `url`, `pdf_url` |
| **PDFParseResult** | PDF 解析结果 | `metadata`, `sections{str:str}`, `references[]`, `keywords[]`, `pages[]`, `full_text` |
| **WritingRequest** | 写作辅助请求 | `input_text`, `context`, `target_language`, `style`, `topic`, `model_name` |
| **WritingResponse** | 写作辅助响应 | `output`, `provider`, `model`, `tokens_used` |

---

## 八、开发路线

### 已完成 ✅

- 模块 1：多源文献搜索与去重排序
- 模块 2：PDF 解析与文本清洗
- 模块 3：BibTeX 引用管理与格式导出
- 模块 4：LLM 写作辅助（摘要/翻译/润色/综述/大纲）
- 模块 5：CLI 命令行入口
- 模块 6：FastAPI Web API
- 模块 7：Pydantic 数据模型与验证
- 模块 8：项目文档与示例

### 规划中 📋

详见 [PROJECT_PROPOSAL.md](file:///workspace/PROJECT_PROPOSAL.md) 与 [OPENING_REPORT.md](file:///workspace/OPENING_REPORT.md)：

- 模块 A：证据与知识库管理（Evidence Brief、Domain KB）
- 模块 B：辩论引擎（教练-辩手双角色，POI 段间质询，证据闭包）
- 模块 C：审理引擎（检察官-辩护律师独立审理）
- 模块 D：裁决引擎（五位专业法官，类判决书推理链）
- 模块 E：多领域适配与创新保护机制
- 模块 F：评估实验（基准数据集、消融实验）

---

## 九、文档索引

| 文档 | 内容 |
|------|------|
| **OPENING_REPORT.md** | 研究开题报告：背景、目标、创新点、评估方案 |
| **PROJECT_PROPOSAL.md** | 项目计划书：技术架构、模块分工、资源预算 |
| **PROJECT_PLAN.md** | 开发规划：进度安排、API/CLI 设计、测试策略 |
| **research_report.md** | 多智能体辩论（MAD）领域调研：里程碑、技术栈 |
| **README.md** | 本文件：项目总览、快速开始、使用示例 |
| **docs/USAGE.md** | 详细使用文档（如存在） |

---

## 十、贡献说明

欢迎贡献代码！

1. 保持小而清晰的变更
2. 遵循现有代码风格与命名约定
3. 新增功能请同步更新文档与示例
4. 核心模块请添加单元测试

### 4.1 测试策略

- **单元测试**：每个独立函数/类的功能测试
- **集成测试**：模块间协作测试
- **人工评估**：学术写作辅助结果质量评估
- **基线对比**：与标准工具（如 Zotero、Mendeley）对比

### 4.2 代码规范

- 完整的类型注解（使用 `from __future__ import annotations`）
- Docstring 说明功能、参数、返回值、异常
- 模块遵循单一职责原则

---

## 十一、License

本项目采用 **MIT License** 开源，允许商业与非商业使用。
