"""这是一个 Python 脚本，可在 Jupyter 中以 %run 执行，也可直接用 python 执行。

示例 01：统一论文搜索（arXiv / Crossref / Semantic Scholar）。
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

from src.search import SearchQuery, SearchSource, unified_search


console = Console()


def print_result_table(result, max_rows: int = 10) -> None:
    table = Table(
        title=f"[bold cyan]搜索结果[/bold cyan]：keyword={result.query.keyword}  "
        f"total={result.total_count}  耗时={result.used_time:.3f}s",
        show_lines=True,
    )
    table.add_column("#", justify="right", style="bold white", no_wrap=True)
    table.add_column("年份", justify="right", style="yellow", no_wrap=True)
    table.add_column("标题", style="bold magenta")
    table.add_column("引用数", justify="right", style="green")
    table.add_column("来源", justify="center", style="cyan")
    table.add_column("DOI", style="blue")

    for idx, paper in enumerate(result.papers[:max_rows], start=1):
        title = paper.title or "(未知标题)"
        if len(title) > 80:
            title = title[:77] + "..."
        venue = paper.venue or paper.source or ""
        doi = paper.doi or ""
        citations = paper.citation_count if paper.citation_count is not None else 0
        year = paper.year if paper.year is not None else "-"
        table.add_row(
            str(idx),
            str(year),
            title,
            str(citations),
            str(paper.source or ""),
            doi,
        )
    console.print(table)


def save_result_json(result, output_path: Path) -> None:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_count": result.total_count,
        "used_time_seconds": result.used_time,
        "query": result.query.model_dump(),
        "papers": [
            {
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract,
                "year": p.year,
                "venue": p.venue,
                "doi": p.doi,
                "url": p.url,
                "citation_count": p.citation_count,
                "source": p.source,
                "tags": p.tags,
            }
            for p in result.papers
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    console.print(f"[green]已保存 JSON 到：[/green] {output_path}")


def run_demo() -> None:
    console.rule("[bold cyan]Demo 01：论文统一搜索")

    keyword = os.environ.get("SEARCH_KEYWORD", "retrieval augmented generation")
    max_results = int(os.environ.get("SEARCH_MAX", "10"))

    query = SearchQuery(
        keyword=keyword,
        max_results=max_results,
        sources=[SearchSource.ARXIV, SearchSource.CROSSREF, SearchSource.SEMANTIC_SCHOLAR],
    )

    console.print(
        f"[dim]构造查询：keyword={keyword!r}, max_results={max_results}, "
        f"sources=[{', '.join(s.value for s in query.sources)}]"
    )

    result = unified_search(query)
    print_result_table(result, max_rows=min(15, max_results))

    output = Path(os.environ.get("OUTPUT_DIR", str(WORKSPACE_ROOT / "data"))) / "search_result.json"
    save_result_json(result, output)


if __name__ == "__main__":
    run_demo()
