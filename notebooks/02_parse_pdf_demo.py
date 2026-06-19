"""这是一个 Python 脚本，可在 Jupyter 中以 %run 执行，也可直接用 python 执行。

示例 02：PDF 解析（或示例文本解析）。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))


from rich.console import Console
from rich.table import Table

from src.parse import parse_pdf
from src.utils.io import ensure_dir, save_json, save_text


console = Console()


SAMPLE_TEXT = """Abstract
Retrieval Augmented Generation (RAG) combines large language models
with external knowledge retrieval to improve factual accuracy.

Introduction
Recent advances in large language models (LLMs) have led to remarkable
performance across many natural language understanding tasks. However,
LLMs are prone to hallucinating facts and cannot incorporate new
knowledge after training. Retrieval-Augmented Generation (RAG) addresses
these limitations by retrieving relevant documents from an external
corpus and conditioning generation on those documents.

Method
We propose a modular RAG pipeline consisting of three components: a
sparse retriever based on BM25, a dense retriever fine-tuned with
contrastive learning, and a generative re-ranker. Documents are chunked
with overlaps of 128 tokens and embedded using a sentence-transformer.

Results
On the HotpotQA benchmark, our approach improves F1 by 5.3 points over
vanilla LLM baselines. On a proprietary enterprise QA dataset covering
200 documents, we observe a 12.1% reduction in hallucination rate.

Discussion
These results suggest that hybrid retrieval and lightweight re-ranking
offer a strong cost-quality trade-off. Future work should explore
multi-hop retrieval and long-context summarization.

References
[1] Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive
NLP Tasks. NeurIPS, 2020.
[2] Gao et al. Retrieval-Augmented Generation for Large Language Models:
A Survey. arXiv preprint arXiv:2312.10997, 2023.
[3] Izacard et al. Leveraging Passage Retrieval with Generative Models
for Open Domain Question Answering. EACL, 2021.

Keywords
RAG, large language models, information retrieval, question answering,
knowledge base, factuality, hallucination mitigation.
"""


def print_sections(sections):
    if not sections:
        console.print("[yellow]（未检测到章节）[/yellow]")
        return
    table = Table(title="[bold cyan]章节摘要", show_lines=True)
    table.add_column("章节", style="bold magenta")
    table.add_column("预览内容", style="white")
    for name, content in sections.items():
        preview = (content.strip().replace("\n", " "))[:160]
        if len(preview) >= 160:
            preview += "..."
        table.add_row(name, preview)
    console.print(table)


def print_keywords(keywords):
    if not keywords:
        console.print("[yellow]（未提取到关键词）[/yellow]")
        return
    table = Table(title="[bold cyan]高频关键词", show_header=True, header_style="bold")
    for i, kw in enumerate(keywords, start=1):
        table.add_column(str(i), justify="center", style="cyan")
    values = [kw for kw in keywords[:10]]
    table.add_row(*values)
    console.print(table)


def save_outputs(sections, keywords, references, meta, data_dir: Path) -> None:
    ensure_dir(str(data_dir))
    save_text(SAMPLE_TEXT, str(data_dir / "sample_text.txt"))
    save_json(
        {
            "sections": {k: v for k, v in sections.items()},
            "keywords": keywords,
            "references": references,
            "metadata": {
                "title": meta.get("title"),
                "authors": meta.get("authors"),
                "year": meta.get("year"),
            },
        },
        str(data_dir / "parsed_sample.json"),
    )
    console.print(f"[green]解析结果已保存到目录：[/green] {data_dir}")


def try_parse_pdf(pdf_path: str):
    try:
        return parse_pdf(pdf_path)
    except FileNotFoundError:
        console.print(f"[yellow]未找到 PDF 文件：{pdf_path}，将使用内置示例文本。[/yellow]")
        return None
    except Exception as exc:  # pragma: no cover - 演示环境
        console.print(f"[red]解析 PDF 时出错：[/red] {exc}")
        return None


def parse_sample_text(text: str):
    lines = [ln.rstrip() for ln in text.splitlines()]
    sections = {}
    current = None
    buffer = []
    headings = {
        "Abstract": "abstract",
        "Introduction": "introduction",
        "Method": "method",
        "Results": "results",
        "Discussion": "discussion",
        "References": "references",
        "Keywords": "keywords",
    }
    for line in lines:
        stripped = line.strip()
        if stripped in headings:
            if current is not None and buffer:
                sections[current] = "\n".join(buffer).strip()
            current = headings[stripped]
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None and buffer:
        sections[current] = "\n".join(buffer).strip()

    references = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and "]" in s:
            references.append(s)

    keywords = []
    if "keywords" in sections:
        for part in sections["keywords"].split(","):
            part = part.strip().strip(".")
            if part:
                keywords.append(part)

    meta = {
        "title": "Retrieval Augmented Generation (Sample)",
        "authors": ["Demo Author"],
        "year": 2024,
        "source": "sample_text",
    }
    return sections, keywords, references, meta


def run_demo() -> None:
    console.rule("[bold cyan]Demo 02：PDF 解析 / 示例文本解析")

    pdf_env = os.environ.get("DEMO_PDF_PATH")
    data_dir = Path(os.environ.get("OUTPUT_DIR", str(WORKSPACE_ROOT / "data")))

    sections = {}
    keywords = []
    references = []
    meta = {}
    pages_info = []

    if pdf_env and Path(pdf_env).exists():
        console.print(f"[dim]检测到 PDF_PATH={pdf_env}，正在解析...[/dim]")
        parse_result = try_parse_pdf(pdf_env)
        if parse_result is not None:
            sections = parse_result.sections or {}
            keywords = parse_result.keywords or []
            references = parse_result.references or []
            pages_info = [
                {"page_number": p.page_number, "char_count": p.char_count}
                for p in (parse_result.pages or [])
            ]
            meta = {
                "title": getattr(parse_result, "title", None)
                or (parse_result.meta.title if hasattr(parse_result, "meta") else None),
                "authors": getattr(parse_result, "authors", []) or [],
                "year": getattr(parse_result, "year", None),
                "source": "pdf",
                "pages": pages_info,
            }
    else:
        console.print(
            "[dim]未提供 PDF 路径（设置 DEMO_PDF_PATH 环境变量可启用），"
            "使用内置示例文本演示。[/dim]"
        )
        sections, keywords, references, meta = parse_sample_text(SAMPLE_TEXT)

    print_sections(sections)
    print_keywords(keywords)

    if references:
        console.print(
            f"[bold cyan]参考文献 ({len(references)})：[/bold cyan] "
            + "; ".join(references[:3]) + (" ..." if len(references) > 3 else "")
        )

    meta_payload = dict(meta)
    meta_payload.setdefault("generated_at", datetime.utcnow().isoformat() + "Z")
    save_outputs(sections, keywords, references, meta_payload, data_dir)


if __name__ == "__main__":
    run_demo()
