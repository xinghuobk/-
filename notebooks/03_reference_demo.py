"""这是一个 Python 脚本，可在 Jupyter 中以 %run 执行，也可直接用 python 执行。

示例 03：参考文献管理（生成 BibTeX、加载检索、导出 APA / GB7714）。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))


from rich.console import Console
from rich.table import Table

from src.reference.bibtex_manager import (
    BibEntry,
    BibTeXManager,
    PaperMeta as BibPaperMeta,
    generate_bibtex_from_paper,
)
from src.utils.io import ensure_dir, save_text


console = Console()


SAMPLE_PAPERS = [
    BibPaperMeta(
        title="Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        authors=["Patrick Lewis", "Ethan Perez", "Aleksandra Piktus", "Fabio Petroni"],
        year="2020",
        journal="NeurIPS",
        doi="10.48550/arXiv.2005.11401",
        entry_type="article",
    ),
    BibPaperMeta(
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        year="2017",
        journal="NeurIPS",
        doi="10.48550/arXiv.1706.03762",
        entry_type="article",
    ),
    BibPaperMeta(
        title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        authors=["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        year="2019",
        journal="NAACL",
        doi="10.48550/arXiv.1810.04805",
        entry_type="article",
    ),
]


def build_bibtex_strings(papers) -> list[str]:
    return [generate_bibtex_from_paper(p) for p in papers]


def save_bib_file(entries: list[str], path: Path) -> None:
    ensure_dir(str(path.parent))
    content = "\n\n".join(entries) + "\n"
    save_text(content, str(path))
    console.print(f"[green]BibTeX 文件已保存：[/green] {path} (共 {len(entries)} 条)")


def load_and_search(bib_path: Path, keyword: str) -> list[BibEntry]:
    manager = BibTeXManager()
    manager.load_file(str(bib_path))
    console.print(f"[dim]已加载 {len(manager.entries)} 条 BibTeX 条目。[/dim]")
    hits = manager.search(keyword)
    console.print(f"[cyan]查询关键词：[/cyan] {keyword!r} → [green]{len(hits)}[/green] 条命中")
    return hits


def print_hits_table(hits: list[BibEntry]) -> None:
    if not hits:
        return
    table = Table(title="[bold cyan]BibTeX 检索命中", show_lines=True)
    table.add_column("#", justify="right", style="bold white")
    table.add_column("Key", style="bold magenta", no_wrap=True)
    table.add_column("Type", justify="center", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Year", justify="right", style="yellow")

    for idx, entry in enumerate(hits, start=1):
        fields = entry.fields or {}
        title = fields.get("title", "(无标题)")
        if len(title) > 80:
            title = title[:77] + "..."
        table.add_row(
            str(idx),
            entry.key,
            entry.entry_type,
            title,
            fields.get("year", ""),
        )
    console.print(table)


def print_exports(hits: list[BibEntry]) -> None:
    if not hits:
        return
    manager = BibTeXManager()
    apa_lines = [manager.to_apa(e) for e in hits]
    gb_lines = [manager.to_gb7714(e) for e in hits]

    console.rule("[bold green]APA 7th 风格")
    for line in apa_lines:
        console.print("  • " + line)

    console.rule("[bold green]GB/T 7714-2015 格式")
    for line in gb_lines:
        console.print("  • " + line)


def run_demo() -> None:
    console.rule("[bold cyan]Demo 03：参考文献管理")

    data_dir = Path(os.environ.get("OUTPUT_DIR", str(WORKSPACE_ROOT / "data")))
    bib_path = data_dir / "demo_references.bib"

    bibtex_entries = build_bibtex_strings(SAMPLE_PAPERS)
    save_bib_file(bibtex_entries, bib_path)

    keyword = os.environ.get("REF_KEYWORD", "retrieval")
    hits = load_and_search(bib_path, keyword)
    print_hits_table(hits)
    print_exports(hits)


if __name__ == "__main__":
    run_demo()
