"""这是一个 Python 脚本，可在 Jupyter 中以 %run 执行，也可直接用 python 执行。

示例 05：端到端流程（搜索 → 生成 BibTeX → 生成文献综述）。
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
from rich.panel import Panel

from src.reference.bibtex_manager import (
    PaperMeta as BibPaperMeta,
    generate_bibtex_from_paper,
)
from src.search import SearchQuery, SearchSource, unified_search
from src.utils.io import ensure_dir, save_json, save_text
from src.writer.llm_helper import AcademicWriter


console = Console()


def run_demo() -> None:
    console.rule("[bold cyan]Demo 05：端到端流程（检索 → 元数据 → BibTeX → 综述）")

    keyword = os.environ.get("SEARCH_KEYWORD", "retrieval augmented generation")
    max_results = int(os.environ.get("SEARCH_MAX", "8"))
    provider = os.environ.get("WRITER_PROVIDER", "mock").strip().lower()
    model = os.environ.get("WRITER_MODEL", "mock-model").strip()

    # Step 1: 搜索
    console.rule("[bold green]Step 1/3  检索论文元数据")
    query = SearchQuery(
        keyword=keyword,
        max_results=max_results,
        sources=[SearchSource.ARXIV, SearchSource.CROSSREF, SearchSource.SEMANTIC_SCHOLAR],
    )
    result = unified_search(query)
    console.print(
        f"[dim]命中 {result.total_count} 篇，耗时 {result.used_time:.3f}s，"
        f"将使用前 {min(len(result.papers), 5)} 篇生成 BibTeX 和综述。[/dim]"
    )

    selected = result.papers[:5]
    if not selected:
        console.print("[yellow]未检索到论文，演示无法继续。可尝试调整关键词或来源。[/yellow]")
        return

    for idx, paper in enumerate(selected, start=1):
        console.print(
            f"  [cyan]{idx}.[/cyan] [magenta]{paper.title or '(无标题)'}[/magenta] "
            f"[yellow]({paper.year or '?'})[/yellow] [dim]citations={paper.citation_count or 0}[/dim]"
        )

    # Step 2: 生成 BibTeX
    console.rule("[bold green]Step 2/3  生成 BibTeX")
    bibtex_entries = []
    bib_papers_meta = []
    for paper in selected:
        meta = BibPaperMeta(
            title=paper.title or "",
            authors=list(paper.authors or []),
            year=str(paper.year) if paper.year else "",
            journal=paper.venue or "",
            doi=paper.doi or "",
            entry_type="article",
        )
        bib_papers_meta.append(meta)
        bibtex_entries.append(generate_bibtex_from_paper(meta))

    bibtex_block = "\n\n".join(bibtex_entries) + "\n"
    console.print(Panel(bibtex_block, title="[bold cyan]BibTeX[/bold cyan]", border_style="cyan"))

    # Step 3: 生成文献综述（基于摘要或标题）
    console.rule("[bold green]Step 3/3  生成文献综述")
    writer = AcademicWriter(provider=provider, model=model)

    summaries = []
    for p in selected:
        abstract = p.abstract or p.title or ""
        title = p.title or "(无标题)"
        authors = ", ".join(p.authors[:2]) if p.authors else "Anonymous"
        year = p.year or "n.d."
        summaries.append(f"{title} ({authors}, {year}): {abstract.strip()[:400]}")

    review = writer.generate_literature_review(summaries, topic=keyword)
    console.print(
        Panel(
            review.content.strip(),
            title=f"[bold cyan]文献综述：{keyword}[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print(f"[dim]模型：{review.model_name or 'mock'}  耗时：{review.used_time:.3f}s[/dim]")

    # 保存输出
    data_dir = Path(os.environ.get("OUTPUT_DIR", str(WORKSPACE_ROOT / "data")))
    ensure_dir(str(data_dir))

    save_text(bibtex_block, str(data_dir / "end_to_end_references.bib"))

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "keyword": keyword,
        "provider": provider,
        "model": model,
        "papers": [
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "venue": p.venue,
                "doi": p.doi,
                "citation_count": p.citation_count,
                "source": p.source,
            }
            for p in selected
        ],
        "bibtex_entries": bibtex_entries,
        "literature_review": review.content,
    }
    save_json(payload, str(data_dir / "end_to_end_output.json"))
    console.print(
        f"[green]端到端结果已保存：[/green] {data_dir / 'end_to_end_output.json'}, "
        f"{data_dir / 'end_to_end_references.bib'}"
    )


if __name__ == "__main__":
    run_demo()
