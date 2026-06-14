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
