# 学术论文工具链 - Academic Paper Toolkit

> 一套面向科研工作者的开源工具，覆盖文献检索、PDF 解析、引用管理、LLM 辅助写作四大核心场景。

Academic Paper Toolkit（以下简称 APT）将学术工作流程中分散的能力，统一封装到一个 Python 代码库内。它同时提供 **程序化 API**（FastAPI）与 **命令行工具**（Typer + Rich），既可以作为独立服务运行，也可以直接导入为 Python 模块，嵌入到你的 Notebook 或工作流脚本中。

---

## 主要功能

### 1. 文献检索（Search）

统一入口 `src.search.engine.unified_search` 面向 arXiv、Semantic Scholar、Crossref 三个公开 API，在一个请求内并发查询、按引用数与年份去重、排序并返回结构化结果。

- 关键词 / 作者 / 年份过滤（依赖于数据源能力）
- 多源结果去重（以 DOI 或归一化标题为 key）
- 返回 `PaperMeta` Pydantic 模型（title / authors / abstract / year / venue / doi / citation_count / source 等）
- 离线可用：当网络不可用时，arXiv 客户端自动返回 mock 数据，便于本地演示

```python
from backend.models.schemas import SearchQuery, SearchSource
from src.search.engine import unified_search

result = unified_search(SearchQuery(
    keyword="graph neural networks",
    year_min=2020,
    max_results=15,
    sources=[SearchSource.ARXIV, SearchSource.SEMANTIC_SCHOLAR, SearchSource.CROSSREF],
))
print(f"命中 {result.total_count} 篇，耗时 {result.used_time:.2f}s")
```

### 2. PDF 解析（Parse）

核心解析器 `src.parse.pdf_parser.PDFParser` 基于 PyMuPDF（fitz），并在可用时自动使用 pdfplumber 提取表格。解析器具备：

- 逐页文本提取，自动处理连字符换行与多余空白
- 章节识别（基于常见章节标题正则，兼容中英文论文）
- 参考文献条目抽取（合并多行、识别编号与作者开头）
- 图注与表格文本抽取
- 元数据推断（标题、作者、年份、DOI、关键词段落）
- 词频式关键词提取（内置英文停用词表，中文可接入 jieba）

便捷函数 `parse_pdf(pdf_path)` 一行代码返回结构化的 `PDFParseResult`。

### 3. 引用管理（Reference）

`src.reference.bibtex_manager.BibTeXManager` 负责：

- 解析 `.bib` 文件（处理嵌套大括号，容错性强）
- 新增 / 保存条目
- 按关键词检索（覆盖 cite key 与全部字段值）
- 格式转换：`to_apa`（APA 7th）、`to_gb7714`（GB/T 7714-2015）
- 便捷函数 `generate_bibtex_from_paper`：从论文元数据生成 BibTeX 条目字符串

### 4. LLM 辅助写作（Writer）

`src.writer.llm_helper.AcademicWriter` 封装六类常见写作任务：

- 学术摘要（summarize_text）
- 中英互译（translate_academic）
- 段落润色（polish_paragraph）
- 文献综述（generate_literature_review）
- 论文大纲（generate_outline）
- 引用格式化（format_citation，纯本地实现，免 API）

底层 LLM 提供商目前以 mock 形式给出（便于离线测试），后续可接入 OpenAI 与通义千问（dashscope）SDK。Prompt 模板集中维护在 `src/writer/prompt_templates.py`，便于按需定制。

---

## 快速开始

### 环境要求

- Python ≥ 3.10（项目在 3.14 下开发验证）
- 推荐使用虚拟环境管理依赖

### 创建虚拟环境并安装依赖

```bash
cd /workspace
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 如需 Jupyter 与高质量 PDF 解析可选能力：
# pip install -r requirements-experimental.txt
```

### CLI 示例

> 命令行工具面向常见小任务，参数以 `-h` 查看详细帮助。

```bash
# 1) 搜索论文（关键词 + 数据源 + 返回条数）
python -m src search "graph neural networks" \
    --sources arxiv semantic_scholar crossref \
    --max-results 10 \
    --year-min 2020

# 2) 解析 PDF，输出 JSON 到文件
python -m src parse /path/to/paper.pdf \
    --output /path/to/out.json \
    --sections

# 3) 管理 BibTeX：在指定 .bib 中搜索并以 APA 打印
python -m src reference /path/to/library.bib \
    --search "transformer" \
    --format apa

# 4) 论文写作辅助（mock LLM，无需 API Key）
python -m src writer summarize \
    --input /path/to/paper_text.txt \
    --output /path/to/summary.md \
    --max-sentences 5

python -m src writer outline \
    --topic "Retrieval-Augmented Generation" \
    --sections 6 \
    --provider mock
```

### 启动 API 服务

FastAPI 应用位于 `backend/app.py`（如尚未创建，可参考 `backend/models/schemas.py` 中的 Pydantic 模型快速搭建路由）：

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

打开浏览器访问 <http://localhost:8000/docs> 即可使用 Swagger UI 调试接口。

---

## 目录结构

```text
/workspace
├── README.md                           # 本文件：项目说明与快速开始
├── PROJECT_PLAN.md                     # 项目规划、模块进度、API/CLI 一览
├── requirements.txt                    # 核心依赖
├── requirements-experimental.txt       # Jupyter、marker 等扩展依赖
├── index.html                          # （可选）前端静态入口
├── .env.example                        # （建议）环境变量示例
│
├── backend/                            # 服务层
│   ├── app.py                          # FastAPI 应用入口（按需创建）
│   └── models/
│       ├── __init__.py                 # 公共导出
│       └── schemas.py                  # Pydantic 模型：论文、搜索、写作、辩论
│
├── src/                                # 核心算法与业务模块
│   ├── __init__.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── engine.py                   # 统一搜索入口
│   │   ├── arxiv_client.py             # arXiv Atom XML API
│   │   ├── semantic_scholar_client.py  # Semantic Scholar Graph API
│   │   └── crossref_client.py          # Crossref REST API
│   ├── parse/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py               # 主 PDF 解析器（PyMuPDF + pdfplumber）
│   │   └── text_cleaner.py             # 文本清理工具
│   ├── reference/
│   │   ├── __init__.py
│   │   └── bibtex_manager.py           # BibTeX 管理与 APA/GB7714 导出
│   ├── writer/
│   │   ├── __init__.py
│   │   ├── llm_helper.py               # AcademicWriter 与统一写作接口
│   │   └── prompt_templates.py         # 六类写作任务的 Prompt 模板
│   └── utils/
│       ├── __init__.py
│       └── io.py                       # 目录创建、JSON/文本读写
│
├── notebooks/                          # （后续）实验与演示 Notebook
├── data/                               # （后续）论文、向量库、图谱输出目录
└── .venv/                              # 本地虚拟环境（.gitignore 已忽略）
```

---

## 主要依赖

| 分组 | 包名 | 版本建议 | 用途 |
|------|------|----------|------|
| 核心框架 | LangGraph | ≥ 0.2.0 | 构建多智能体写作与辩论流程 |
| 核心框架 | LangChain | ≥ 0.3.0 | LLM 调用、工具链、向量库集成 |
| PDF 解析 | PyMuPDF | ≥ 1.24.0 | 高性能 PDF 文本/元数据提取（`fitz`） |
| 文献检索 | arxiv | ≥ 2.1.0 | arXiv 官方 API Python 封装 |
| 引用管理 | pyzotero | ≥ 1.5.25 | Zotero Web API 双向同步 |
| Web 服务 | FastAPI | ≥ 0.111.0 | 现代、类型安全的 API 框架 |
| Web 服务 | Uvicorn | ≥ 0.30.0 | ASGI 服务器（FastAPI 默认运行时） |
| CLI | Typer | ≥ 0.12.0 | 基于类型注解的现代 CLI 框架 |
| CLI | Rich | ≥ 13.7.0 | 终端彩色输出、表格、进度条 |

核心依赖已在 `requirements.txt` 中给出；项目允许独立安装 `PyMuPDF / arxiv / crossref` 等子模块，按需使用。

---

## 贡献说明

欢迎提交 Issue 与 Pull Request。简单规则：

1. **保持小而清晰的变更**：每个 PR 聚焦一个功能点或问题修复。
2. **遵循现有风格**：模块按 `src/<domain>/xxx.py` 组织，公共模型放在 `backend/models/`。
3. **提供最小可运行示例**：对于新加入的 API 或 CLI 子命令，附上简短调用示例与输出。
4. **文档同步**：新增功能请同步更新本 README 与 `PROJECT_PLAN.md` 的相应章节。

---

## License

本项目采用 **MIT License** 开源，允许商业与非商业使用。使用时请保留版权声明。具体条款见项目根目录下的 `LICENSE` 文件（若尚未创建，则以 MIT 为默认）。

> MIT License：你可以自由复制、修改、分发，只要你在你的副本中保留原作者版权声明与许可声明。
