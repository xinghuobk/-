# 论文查找与智能写作辅助工具 — 项目规划与环境准备

> 目标：搭建一个覆盖「检索 → 筛选 → 阅读 → 笔记 → 写作 → 导出」全流程的论文查找与写作辅助工具链。当前阶段先不启动具体开发，聚焦于工具选型、环境搭建与方案规划。

---

## 1. 方案总览

| 模块 | 能力 | 主要 GitHub / PyPI 工具 |
|------|------|--------------------------|
| 论文检索 | 关键词 / 作者 / 引用 / DOI 检索，批量下载 PDF | `arxiv`、`scholarly`、`semanticscholar`、`crossref-commons`、`pyalex` |
| PDF 解析 | PDF → 文本 / Markdown / 结构化章节 | `PyMuPDF`、`pdfplumber`、`marker`(optional)、`nougat`(optional) |
| 向量化检索 | 语义检索、本地库快速查找 | `ChromaDB`、`FAISS`、`sentence-transformers` |
| 文献管理 | 引用网络、Zotero 同步、BibTeX | `pyzotero`、`bibtexparser`、`networkx` |
| LLM 写作辅助 | 大纲、续写、综述、润色 | `LangGraph` + `LangChain` + OpenAI / 通义千问 |
| 知识图谱 | 论文引用关系可视化 | `networkx` + `matplotlib` |
| 服务层 | API 接口与 CLI | `FastAPI`、`Uvicorn`、`Typer`、`Rich` |
| 实验层 | Notebook 交互分析 | `JupyterLab`、`Pandas` |

---

## 2. 关键 GitHub 开源工具参考（可 clone 学习，不强制纳入依赖）

| 项目 | 用途 | 说明 |
|------|------|------|
| **vikhyat/marker** | PDF → Markdown 高质量解析 | 学术论文专用，离线模型，体积较大，按需 clone |
| **facebookresearch/nougat** | 学术 PDF → Markdown OCR | Meta 出品，适合数学公式密集的论文 |
| **allenai/s2orc-doc2json** | Semantic Scholar 原始数据解析 | 学习数据清洗与结构化方法 |
| **Ir1d/Paper_Chat** | 论文问答演示项目 | 参考 PDF + LangChain + 向量库的端到端实现 |
| **chatchat-space/Langchain-Chatchat** | 本地化知识库问答 | 参考中文 RAG 项目架构与检索增强写法 |
| **zotero/zotero** | 文献管理 | 作为导入/导出的参考系统 |

> 以上仓库仅作参考，先不直接 clone；核心能力通过 pip 包即可覆盖，降低维护成本。

---

## 3. 依赖清单

- 开发环境：见 [requirements.txt](file:///workspace/requirements.txt)
- 实验环境（Notebook + 高级 PDF 解析）：见 [requirements-experimental.txt](file:///workspace/requirements-experimental.txt)

### 3.1 核心分组

- **Core Framework**：LangGraph / LangChain，构建多智能体写作流程
- **Paper Search**：arXiv / Semantic Scholar / Google Scholar / Crossref / OpenAlex
- **PDF 解析**：PyMuPDF / pdfplumber / PyPDF（默认）；marker / nougat（可选）
- **向量存储**：ChromaDB + FAISS + sentence-transformers
- **文献管理**：pyzotero + bibtexparser + networkx
- **Web / CLI**：FastAPI + Typer + Rich
- **LLM**：OpenAI、通义千问（dashscope）

---

## 4. 开发环境准备

### 4.1 Python 版本与虚拟环境

当前主机检测到 `Python 3.14.4`，未安装 conda/mamba。建议使用标准 `venv` 作为起步方案；如后续需要复杂科学计算栈，可再迁移到 conda-forge。

### 4.2 快速起步命令

```bash
cd /workspace

# 1) 创建虚拟环境
python3 -m venv .venv

# 2) 激活
source .venv/bin/activate        # Linux/macOS
# 或 Windows: .venv\Scripts\activate

# 3) 升级工具链
pip install --upgrade pip setuptools wheel

# 4) 安装开发依赖
pip install -r requirements.txt

# 5) 按需安装实验依赖（Jupyter + marker/nougat）
pip install -r requirements-experimental.txt
```

### 4.3 环境变量（在 `/workspace/.env` 中配置）

```dotenv
OPENAI_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx          # 通义千问
# ZOTERO_LIBRARY_ID=              # 如需 Zotero 同步
# ZOTERO_API_KEY=
```

---

## 5. 实验环境准备

- **Notebook 目录**：`/workspace/notebooks/`（后续创建）
- **论文本地仓库**：`/workspace/data/papers/`
- **向量数据库目录**：`/workspace/data/chroma/`
- **引用图谱输出**：`/workspace/data/graphs/`

实验初始步骤规划（非当前阶段执行）：

1. 用 `arxiv` / `scholarly` 抓取关键词 → 元数据 JSON
2. 用 `PyMuPDF` 解析 PDF → 章节级 Markdown
3. 用 `sentence-transformers` 向量化 → 存入 `ChromaDB`
4. JupyterLab 中做检索质量评估
5. 基于 `LangGraph` 设计「检索 agent + 写作 agent」的双流协同

---

## 6. 下一步计划（供讨论）

- [ ] 确定首版目标用例（例如「给定关键词 → 生成 5 篇论文对比综述」）
- [ ] 设计 LangGraph 的 agent 节点与状态机
- [ ] 准备首批示例论文数据，做端到端冒烟测试
- [ ] 决定是否引入 `marker` / `nougat` 做 OCR 增强
- [ ] 设计 CLI / API 接口并落地初版原型代码

---

## 7. 目录结构建议

```text
/workspace
├── requirements.txt                # 开发依赖
├── requirements-experimental.txt   # 实验依赖
├── README.md
├── .env                            # 不入库
├── backend/
│   └── models/schemas.py           # 已有雏形
├── src/                            # （后续）核心代码
│   ├── search/
│   ├── parse/
│   ├── rag/
│   ├── graph/
│   └── writer/
├── notebooks/                      # （后续）实验 notebook
└── data/
    ├── papers/
    ├── chroma/
    └── graphs/
```

当前阶段保持最小改动，等环境与目标用例确认后再进入具体编码。

---

## 8. 项目实现进度

以下为项目各核心能力的当前落地状态：

| 模块 | 说明 | 已完成 | 待完成 |
|------|------|--------|--------|
| 统一文献检索（engine） | 多源并发、去重、按引用/年份排序 | ✅ | 增加 Google Scholar / OpenAlex 接入，查询结果缓存 |
| arXiv 客户端 | Atom XML 解析、离线 mock | ✅ | 按作者 / 分类检索 |
| Semantic Scholar 客户端 | Graph API 论文搜索 | ✅ | 引用/被引网络可视化 |
| Crossref 客户端 | REST API 元数据查询 | ✅ | DOI 元数据反查接口 |
| PDF 解析（PDFParser） | 文本提取、章节识别、表格图注、元数据推断 | ✅ | marker / nougat 集成以提升公式与扫描 PDF 质量 |
| PDF 文本清理工具 | 连字符、页眉页脚、摘要抽取 | ✅ | 中文论文专有清洗规则 |
| BibTeX 管理器 | 解析、保存、搜索、APA / GB7714 导出 | ✅ | Zotero 双向同步（pyzotero） |
| AcademicWriter | 摘要、翻译、润色、综述、大纲、引用格式化 | ✅ | 接入真实 OpenAI / dashscope SDK，支持流式输出 |
| Prompt 模板 | 五类中英混写模板 | ✅ | 按领域定制模板（医学、法律、CS） |
| 向量检索 / RAG | — | ❌ | ChromaDB / FAISS + sentence-transformers 初版 |
| 知识图谱 / 引用网络 | — | ❌ | NetworkX 绘制引用图、度中心性分析 |
| 多智能体辩论流程 | （仅 schemas） | ⏳ | LangGraph 驱动的 Agent 流程实现 |
| FastAPI 服务端 | — | ⏳ | `backend/app.py` 路由实现与鉴权 |
| Typer CLI | — | ⏳ | `src/__main__.py` 子命令实现（search/parse/reference/writer） |

**图例**：`✅` 已有可运行实现，`⏳` 仅定义模型/接口骨架，`❌` 未开始。

---

## 9. API 接口一览

> 接口以 FastAPI 实现，所有请求/响应均使用 `backend/models/schemas.py` 中的 Pydantic 模型。路由定义将集中在 `backend/app.py`（如尚未创建，可按下列签名快速落地）。

| 方法 | 路径 | 请求体 / 参数 | 返回体 | 说明 |
|------|------|----------------|--------|------|
| `GET`  | `/health` | — | `{"status":"ok","version":"..."}` | 健康检查，用于监控 |
| `POST` | `/api/search` | `SearchQuery`（`keyword`、`max_results`、`sources`、`year_min`、`year_max`、`venue`） | `SearchResult`（`total_count`、`papers`、`query`、`used_time`） | 多源统一文献检索 |
| `GET`  | `/api/search` | query 传参：`keyword`、`sources`（逗号分隔）、`max_results`、`year_min`、`year_max` | `SearchResult` | GET 版检索接口，便于浏览器调试 |
| `POST` | `/api/parse/pdf` | multipart form：`file`（PDF），query：`extract_sections=true/false` | `PDFParseResult`（`pages`、`sections`、`references`、`metadata`、`keywords`） | 上传 PDF 并解析为结构化 JSON |
| `POST` | `/api/reference/bibtex/parse` | multipart form：`file`（.bib）或 JSON `{"text":"...","search":""}` | `{"entries": [...],"count":int}` | 解析 BibTeX 并可选按关键字搜索 |
| `POST` | `/api/reference/format` | JSON `{"key":"...","fields":{...},"format":"bibtex\|apa\|gb7714"}` | `{"content": "..."}` | 按指定格式格式化引用 |
| `POST` | `/api/writer/summarize` | `WritingRequest`（`input_text`、`max_sentences`、`model_name`） | `WritingResponse`（`content`、`model_name`、`used_time`） | 生成学术摘要 |
| `POST` | `/api/writer/translate` | `WritingRequest`（`input_text`、`target_lang`） | `WritingResponse` | 学术翻译 |
| `POST` | `/api/writer/polish` | `WritingRequest`（`input_text`、`extra_args.style`） | `WritingResponse` | 段落润色 |
| `POST` | `/api/writer/literature-review` | JSON `{"topic":"...","paper_summaries":[...],"model_name":""}` | `WritingResponse` | 基于多篇摘要生成文献综述 |
| `POST` | `/api/writer/outline` | JSON `{"topic":"...","sections":6,"model_name":""}` | `WritingResponse` | 生成论文大纲 |
| `POST` | `/api/writer/citation` | JSON `{"paper":{...},"format":"bibtex\|apa\|gb7714"}` | `WritingResponse` | 论文元数据 → 引用字符串（本地实现，免 API） |
| `GET`  | `/api/models` | — | `[{"provider":"openai","models":[...]},...]` | 列出当前可用的 LLM 提供商与模型 |

> **设计约定**：所有 POST 接口的 `WritingRequest` 遵循 `backend.models.schemas.WritingRequest` 的字段名；`SearchSource` / `ReferenceFormat` 等枚举值直接传入字符串字面量（如 `"arxiv"`、`"semantic_scholar"`、`"crossref"`、`"bibtex"`、`"apa"`、`"gb7714"`）。

---

## 10. CLI 命令一览

CLI 使用 `Typer` + `Rich` 实现，统一入口为 `python -m src`（建议在 `src/__main__.py` 中组装子命令）。下表列出计划中的全部子命令及其常用参数：

| 子命令 | 子子命令 | 主要参数 | 输出 | 说明 |
|--------|----------|----------|------|------|
| `search` | — | `keyword`、`--sources`（arxiv/semantic_scholar/crossref）、`--max-results N`、`--year-min YYYY`、`--year-max YYYY`、`--output PATH` | 终端表格 / JSON 文件 | 多源文献检索 |
| `parse` | `pdf` | `PDF_PATH`、`--output PATH`、`--sections`、`--tables`、`--figures`、`--include-text` | JSON / Markdown | 解析单篇 PDF |
| `reference` | `parse` | `BIB_PATH`、`--search KEYWORD`、`--format bibtex\|apa\|gb7714` | 终端表格 / 文件 | 解析并导出 BibTeX 条目 |
| `reference` | `format` | `--title`、`--authors "a;b"`、`--year`、`--journal`、`--format bibtex\|apa\|gb7714` | 引用字符串 | 按元数据直接生成引用 |
| `writer` | `summarize` | `--input`（文本文件或 `-`）、`--output PATH`、`--max-sentences 5`、`--provider mock\|openai\|dashscope`、`--model qwen-max` | Markdown 摘要文件 | 生成学术摘要 |
| `writer` | `translate` | `--input`、`--output`、`--target-lang zh-CN\|en`、`--provider`、`--model` | 翻译后的文本文件 | 学术翻译 |
| `writer` | `polish` | `--input`、`--output`、`--style academic\|clear\|fluent`、`--provider`、`--model` | 润色后的文本文件 | 段落润色（含 DIFF） |
| `writer` | `literature-review` | `--topic`、`--summaries FILE1 FILE2 ...`、`--output`、`--provider`、`--model` | Markdown 综述 | 多篇摘要 → 文献综述 |
| `writer` | `outline` | `--topic`、`--sections 6`、`--output`、`--provider`、`--model` | Markdown 大纲 | 生成论文大纲 |
| `writer` | `citation` | `--title`、`--authors "a;b"`、`--year`、`--journal`、`--format bibtex\|apa\|gb7714` | 引用字符串 | 纯本地实现，无需 API Key |
| `serve` | — | `--host 0.0.0.0`、`--port 8000`、`--reload` | 启动 FastAPI 进程 | 启动后端服务 |
| `version` | — | — | `Academic Paper Toolkit v0.1.0` | 版本信息 |

> **使用提示**：所有子命令均支持 `-h/--help` 查看完整参数说明；对文件路径支持 `~` 展开与相对路径解析（由 `src/utils/io.py` 中的 `ensure_dir` 辅助）。如需接入真实 LLM，请在 `.env` 中配置 `OPENAI_API_KEY` 或 `DASHSCOPE_API_KEY`，并给 `--provider` 传入对应值。
