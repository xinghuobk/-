"""学术论文工具链：检索 / 解析 / 引用 / 写作。

基于 Typer 构建的命令行工具，通过子命令的形式整合四大功能模块：
- search：在 arXiv、Crossref、Semantic Scholar 等来源检索论文。
- parse：解析 PDF，提取文本、章节、参考文献与元数据。
- ref：管理 BibTeX 文献库（添加、搜索、导出）。
- write：写作辅助（摘要、翻译、润色、综述、大纲）。
"""
from __future__ import annotations

import json
import os
import sys
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from src.parse import PDFParseResult, parse_pdf
from src.reference.bibtex_manager import (
    BibEntry,
    BibTeXManager,
    PaperMeta as BibPaperMeta,
    generate_bibtex_from_paper,
)
from src.search import PaperMeta, SearchQuery, SearchResult, SearchSource, unified_search
from src.utils.io import ensure_dir, save_json, save_text
from src.writer.llm_helper import AcademicWriter


_DATA_DIR = "./data"

app = typer.Typer(
    help="学术论文工具链：检索 / 解析 / 引用 / 写作",
    add_completion=False,
    no_args_is_help=True,
)
search_app = typer.Typer(help="文献检索：多源论文搜索", no_args_is_help=True)
parse_app = typer.Typer(help="PDF 解析：文本 / 章节 / 参考文献", no_args_is_help=True)
ref_app = typer.Typer(help="引用管理：BibTeX 库操作", no_args_is_help=True)
write_app = typer.Typer(help="写作辅助：摘要 / 翻译 / 润色 / 综述 / 大纲", no_args_is_help=True)

app.add_typer(search_app, name="search")
app.add_typer(parse_app, name="parse")
app.add_typer(ref_app, name="ref")
app.add_typer(write_app, name="write")

console = Console()


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------
def _print_search_result(result: SearchResult) -> None:
    table = Table(
        title=f"[bold cyan]搜索结果[/bold cyan]：共 {result.total_count} 篇，耗时 {result.used_time:.2f}s",
        show_lines=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("标题", style="bold", overflow="fold")
    table.add_column("年份", justify="right", width=6)
    table.add_column("作者", overflow="fold")
    table.add_column("引用", justify="right", width=6)
    table.add_column("DOI", style="blue", overflow="fold")

    for idx, paper in enumerate(result.papers, start=1):
        authors = "; ".join(paper.authors[:3])
        if len(paper.authors) > 3:
            authors += f" 等 {len(paper.authors)} 人"
        table.add_row(
            str(idx),
            paper.title or "—",
            str(paper.year) if paper.year else "—",
            authors or "—",
            str(paper.citation_count) if paper.citation_count is not None else "—",
            paper.doi or "—",
        )
    console.print(table)


def _parse_sources(sources: Optional[str]) -> List[SearchSource]:
    if not sources:
        return [SearchSource.ARXIV, SearchSource.CROSSREF, SearchSource.SEMANTIC_SCHOLAR]
    mapping = {
        "arxiv": SearchSource.ARXIV,
        "crossref": SearchSource.CROSSREF,
        "semantic": SearchSource.SEMANTIC_SCHOLAR,
        "semantic_scholar": SearchSource.SEMANTIC_SCHOLAR,
        "google_scholar": SearchSource.GOOGLE_SCHOLAR,
        "openalex": SearchSource.OPENALEX,
    }
    parsed: List[SearchSource] = []
    for token in sources.split(","):
        key = token.strip().lower()
        if key in mapping and mapping[key] not in parsed:
            parsed.append(mapping[key])
    return parsed or [SearchSource.ARXIV]


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------
@search_app.command("run")
def search_run(
    keyword: str = typer.Argument(..., help="搜索关键词"),
    sources: Optional[str] = typer.Option(
        None, "--sources", help="搜索来源，逗号分隔：arxiv,crossref,semantic"
    ),
    max_results: int = typer.Option(10, "--max", help="每来源最多返回条数"),
    year_min: Optional[int] = typer.Option(None, "--year-min", help="起始年份过滤"),
    year_max: Optional[int] = typer.Option(None, "--year-max", help="结束年份过滤"),
    output: Optional[str] = typer.Option(None, "--output", help="将结果保存为 JSON 文件"),
) -> None:
    """检索学术论文，并以漂亮表格输出。"""
    try:
        query = SearchQuery(
            keyword=keyword,
            year_min=year_min,
            year_max=year_max,
            max_results=max_results,
            sources=_parse_sources(sources),
        )
        console.print(
            f"[bold green]->[/bold green] 正在检索：[cyan]{keyword}[/cyan] "
            f"(sources={', '.join(s.value for s in query.sources)})"
        )
        result = unified_search(query)
        _print_search_result(result)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(result.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:  # pragma: no cover
        typer.secho(f"检索失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------
@parse_app.command("run")
def parse_run(
    pdf_path: str = typer.Argument(..., help="待解析的 PDF 文件路径"),
    summary: bool = typer.Option(False, "--summary", help="仅展示摘要信息（默认开启详细视图）"),
    sections: bool = typer.Option(False, "--sections", help="展示识别出的章节列表"),
    output_text: Optional[str] = typer.Option(
        None, "--output-text", help="将提取出的全文保存为文本文件"
    ),
    output_json: Optional[str] = typer.Option(
        None, "--output-json", help="将解析结果保存为 JSON 文件"
    ),
) -> None:
    """解析 PDF 并输出章节、参考文献、关键词等摘要信息。"""
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"文件不存在：{pdf_path}")
        console.print(f"[bold green]->[/bold green] 正在解析 PDF：[cyan]{pdf_path}[/cyan]")
        result: PDFParseResult = parse_pdf(pdf_path)

        table = Table(title="[bold cyan]解析摘要[/bold cyan]", header_style="bold magenta")
        table.add_column("字段", style="bold")
        table.add_column("值", overflow="fold")

        meta = result.metadata
        table.add_row("标题", (meta.title if meta else "") or "—")
        table.add_row("作者", "; ".join(meta.authors) if meta and meta.authors else "—")
        table.add_row("年份", str(meta.year) if meta and meta.year else "—")
        table.add_row("DOI", (meta.doi if meta else "") or "—")
        table.add_row("章节数", str(len(result.sections)))
        table.add_row("参考文献数", str(len(result.references)))
        table.add_row(
            "关键词",
            ", ".join(result.keywords[:10]) if result.keywords else "—",
        )
        table.add_row("总页数", str(len(result.pages)))
        console.print(table)

        if sections and result.sections:
            sec_table = Table(
                title="[bold cyan]章节列表[/bold cyan]", header_style="bold magenta", show_lines=True
            )
            sec_table.add_column("章节", style="bold")
            sec_table.add_column("预览（前 120 字）", overflow="fold")
            for name, content in list(result.sections.items())[:20]:
                preview = (content.strip()[:120] + "…") if len(content) > 120 else content.strip()
                sec_table.add_row(name, preview)
            console.print(sec_table)

        if not summary:
            if result.references:
                ref_preview = "\n".join(f"  - {r[:160]}" for r in result.references[:5])
                console.print(
                    f"[bold cyan]参考文献示例（共 {len(result.references)} 条）[/bold cyan]\n{ref_preview}"
                )
            if result.keywords:
                console.print(
                    "[bold cyan]关键词 Top 10：[/bold cyan]"
                    + ", ".join(result.keywords[:10])
                )

        if output_text:
            out_path = output_text if os.path.isabs(output_text) else os.path.join(_DATA_DIR, output_text)
            save_text(result.full_text or "", out_path)
            console.print(f"[bold green]->[/bold green] 全文已保存到 [magenta]{out_path}[/magenta]")

        if output_json:
            out_path = output_json if os.path.isabs(output_json) else os.path.join(_DATA_DIR, output_json)
            save_json(result.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 解析结果已保存到 [magenta]{out_path}[/magenta]")

    except Exception as exc:
        typer.secho(f"解析失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# ref
# ---------------------------------------------------------------------------
@ref_app.command("add")
def ref_add(
    paper: str = typer.Argument(..., help="论文标题或 PDF 路径"),
    authors: Optional[str] = typer.Option(
        None, "--authors", help="作者列表，用分号分隔，例如 'A; B; C'"
    ),
    year: Optional[str] = typer.Option(None, "--year", help="发表年份"),
    bib: str = typer.Option("library.bib", "--bib", help="目标 BibTeX 库文件路径"),
    journal: str = typer.Option("", "--journal", help="期刊名"),
) -> None:
    """向 BibTeX 库新增一条引用条目。"""
    try:
        manager = BibTeXManager()
        if os.path.exists(bib):
            manager.load_file(bib)

        paper_title: str = paper
        pdf_meta_authors: List[str] = []
        pdf_year: Optional[str] = None
        doi: str = ""
        if paper.lower().endswith(".pdf") and os.path.exists(paper):
            console.print(f"[bold green]->[/bold green] 尝试从 PDF 读取元数据：[cyan]{paper}[/cyan]")
            try:
                parsed = parse_pdf(paper)
                parsed_meta = parsed.metadata
                paper_title = (parsed_meta.title if parsed_meta else "") or paper
                pdf_meta_authors = list(parsed_meta.authors) if parsed_meta and parsed_meta.authors else []
                pdf_year = str(parsed_meta.year) if parsed_meta and parsed_meta.year else None
                doi = (parsed_meta.doi if parsed_meta else "") or ""
            except Exception:
                paper_title = paper

        author_list: List[str] = []
        if authors:
            author_list = [a.strip() for a in authors.split(";") if a.strip()]
        if not author_list and pdf_meta_authors:
            author_list = pdf_meta_authors

        paper_meta = BibPaperMeta(
            title=paper_title,
            authors=author_list,
            year=year or pdf_year or "",
            journal=journal,
            doi=doi,
        )
        bib_text = generate_bibtex_from_paper(paper_meta)
        console.print("[bold cyan]生成的 BibTeX 条目：[/bold cyan]")
        console.print(bib_text)

        entry_lines = bib_text.strip().splitlines()
        entry_type, key = "article", ""
        first = entry_lines[0].strip()
        if first.startswith("@"):
            brace_idx = first.find("{")
            if brace_idx >= 0:
                entry_type = first[1:brace_idx].strip().lower()
                key = first[brace_idx + 1:].rstrip(",").strip()

        fields: dict = {}
        for line in entry_lines[1:-1]:
            line = line.strip().rstrip(",")
            if "=" in line:
                name, _, value = line.partition("=")
                fields[name.strip().lower()] = value.strip().strip("{}")

        manager.add_entry(BibEntry(entry_type=entry_type, key=key or f"auto{len(manager.entries)+1}", fields=fields))
        ensure_dir(bib)
        manager.save_file(manager.entries, bib)
        console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{bib}[/magenta]（总数 {len(manager.entries)}）")
    except Exception as exc:
        typer.secho(f"添加引用失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@ref_app.command("list")
def ref_list(
    bib: str = typer.Argument(..., help="BibTeX 库文件路径"),
    keyword: Optional[str] = typer.Option(None, "--keyword", help="按关键词过滤条目"),
) -> None:
    """列出并搜索 BibTeX 条目。"""
    try:
        if not os.path.exists(bib):
            raise FileNotFoundError(f"文件不存在：{bib}")
        manager = BibTeXManager()
        manager.load_file(bib)
        hits = manager.search(keyword) if keyword else list(manager.entries)

        table = Table(
            title=f"[bold cyan]BibTeX 条目[/bold cyan]：共 {len(hits)} / 库中 {len(manager.entries)}",
            header_style="bold magenta",
            show_lines=True,
        )
        table.add_column("#", style="dim", justify="right", width=4)
        table.add_column("Key", style="bold")
        table.add_column("Type", style="yellow")
        table.add_column("Title", overflow="fold")
        table.add_column("Year", justify="right", width=6)

        for idx, entry in enumerate(hits, start=1):
            table.add_row(
                str(idx),
                entry.key,
                entry.entry_type,
                entry.fields.get("title", "—"),
                entry.fields.get("year", "—"),
            )
        console.print(table)
    except Exception as exc:
        typer.secho(f"读取 BibTeX 失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@ref_app.command("export")
def ref_export(
    bib: str = typer.Argument(..., help="BibTeX 库文件路径"),
    fmt: str = typer.Option("apa", "--format", help="导出格式：apa / gb7714 / bibtex"),
    out: Optional[str] = typer.Option(None, "--out", help="输出文件路径，留空则打印到终端"),
    keyword: Optional[str] = typer.Option(None, "--keyword", help="按关键词过滤后再导出"),
) -> None:
    """将 BibTeX 条目导出为指定引用格式。"""
    try:
        if not os.path.exists(bib):
            raise FileNotFoundError(f"文件不存在：{bib}")
        manager = BibTeXManager()
        manager.load_file(bib)
        hits = manager.search(keyword) if keyword else list(manager.entries)

        fmt_key = (fmt or "apa").strip().lower()
        lines: List[str] = []
        for idx, entry in enumerate(hits, start=1):
            if fmt_key == "apa":
                lines.append(f"[{idx}] {manager.to_apa(entry)}")
            elif fmt_key in ("gb7714", "gb", "gb-t"):
                lines.append(f"[{idx}] {manager.to_gb7714(entry)}")
            elif fmt_key == "bibtex":
                header = "@" + entry.entry_type + "{" + entry.key + ","
                field_lines = ["  " + k + " = {" + v + "}," for k, v in entry.fields.items()]
                lines.append("\n".join([header] + field_lines + ["}"]))
            else:
                raise ValueError(f"未知格式：{fmt}")

        content = "\n\n".join(lines)
        if out:
            out_path = out if os.path.isabs(out) else os.path.join(_DATA_DIR, out)
            save_text(content, out_path)
            console.print(f"[bold green]->[/bold green] 已导出 {len(hits)} 条到 [magenta]{out_path}[/magenta]")
        else:
            console.print(f"[bold cyan]导出结果（格式：{fmt_key}）[/bold cyan]")
            console.print(content)
    except Exception as exc:
        typer.secho(f"导出失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------
def _read_text_or_file(text_or_file: str) -> str:
    if os.path.exists(text_or_file):
        with open(text_or_file, "r", encoding="utf-8") as f:
            return f.read()
    return text_or_file


@write_app.command("summary")
def write_summary(
    text_or_file: str = typer.Argument(..., help="文本内容或文本文件路径"),
    provider: str = typer.Option("mock", "--provider", help="LLM 提供商：mock / openai / dashscope"),
    model: str = typer.Option("mock-model", "--model", help="具体模型名"),
    output: Optional[str] = typer.Option(None, "--output", help="保存结果到文件"),
    max_sentences: int = typer.Option(5, "--sentences", help="摘要句数"),
) -> None:
    """生成一段文本的学术摘要。"""
    try:
        text = _read_text_or_file(text_or_file)
        writer = AcademicWriter(provider=provider, model=model)
        console.print(f"[bold green]->[/bold green] 使用 [cyan]{provider}/{model}[/cyan] 生成摘要…")
        resp = writer.summarize_text(text, max_sentences=max_sentences)
        console.print("[bold cyan]摘要[/bold cyan]")
        console.print(resp.output)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(resp.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:
        typer.secho(f"生成摘要失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@write_app.command("translate")
def write_translate(
    text: str = typer.Argument(..., help="待翻译文本"),
    target_lang: str = typer.Option("zh-CN", "--target-lang", help="目标语言，例如 zh-CN / en"),
    provider: str = typer.Option("mock", "--provider"),
    model: str = typer.Option("mock-model", "--model"),
    output: Optional[str] = typer.Option(None, "--output"),
) -> None:
    """学术翻译。"""
    try:
        content = _read_text_or_file(text)
        writer = AcademicWriter(provider=provider, model=model)
        console.print(f"[bold green]->[/bold green] 使用 [cyan]{provider}/{model}[/cyan] 翻译为 {target_lang}…")
        resp = writer.translate_academic(content, target_lang=target_lang)
        console.print("[bold cyan]翻译结果[/bold cyan]")
        console.print(resp.output)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(resp.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:
        typer.secho(f"翻译失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@write_app.command("polish")
def write_polish(
    text: str = typer.Argument(..., help="待润色的段落或文件路径"),
    style: str = typer.Option("academic", "--style", help="目标风格：academic / formal"),
    provider: str = typer.Option("mock", "--provider"),
    model: str = typer.Option("mock-model", "--model"),
    output: Optional[str] = typer.Option(None, "--output"),
) -> None:
    """段落润色。"""
    try:
        content = _read_text_or_file(text)
        writer = AcademicWriter(provider=provider, model=model)
        console.print(f"[bold green]->[/bold green] 使用 [cyan]{provider}/{model}[/cyan] 润色…")
        resp = writer.polish_paragraph(content, style=style)
        console.print("[bold cyan]润色结果[/bold cyan]")
        console.print(resp.output)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(resp.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:
        typer.secho(f"润色失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@write_app.command("review")
def write_review(
    summaries_file: str = typer.Argument(..., help="包含多篇论文摘要的文本文件（每段一篇）"),
    topic: str = typer.Option(..., "--topic", help="综述主题"),
    provider: str = typer.Option("mock", "--provider"),
    model: str = typer.Option("mock-model", "--model"),
    output: Optional[str] = typer.Option(None, "--output"),
) -> None:
    """基于多篇论文摘要生成文献综述。"""
    try:
        if not os.path.exists(summaries_file):
            raise FileNotFoundError(f"文件不存在：{summaries_file}")
        with open(summaries_file, "r", encoding="utf-8") as f:
            raw = f.read()
        summaries = [p.strip() for p in raw.split("\n\n") if p.strip()]
        if not summaries:
            raise ValueError("输入文件中未找到任何段落")

        writer = AcademicWriter(provider=provider, model=model)
        console.print(
            f"[bold green]->[/bold green] 使用 [cyan]{provider}/{model}[/cyan] 围绕「{topic}」生成综述（{len(summaries)} 篇论文）…"
        )
        resp = writer.generate_literature_review(summaries, topic=topic)
        console.print("[bold cyan]文献综述[/bold cyan]")
        console.print(resp.output)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(resp.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:
        typer.secho(f"生成综述失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


@write_app.command("outline")
def write_outline(
    topic: str = typer.Argument(..., help="论文主题"),
    sections: int = typer.Option(6, "--sections", help="大纲章节数（2-12）"),
    provider: str = typer.Option("mock", "--provider"),
    model: str = typer.Option("mock-model", "--model"),
    output: Optional[str] = typer.Option(None, "--output"),
) -> None:
    """生成论文大纲。"""
    try:
        writer = AcademicWriter(provider=provider, model=model)
        console.print(f"[bold green]->[/bold green] 使用 [cyan]{provider}/{model}[/cyan] 生成「{topic}」大纲（{sections} 章）…")
        resp = writer.generate_outline(topic, sections=sections)
        console.print("[bold cyan]大纲[/bold cyan]")
        console.print(resp.output)
        if output:
            out_path = output if os.path.isabs(output) else os.path.join(_DATA_DIR, output)
            save_json(resp.model_dump(), out_path)
            console.print(f"[bold green]->[/bold green] 已保存到 [magenta]{out_path}[/magenta]")
    except Exception as exc:
        typer.secho(f"生成大纲失败：{exc}", fg="red", err=True)
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
