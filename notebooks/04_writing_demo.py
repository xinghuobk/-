"""这是一个 Python 脚本，可在 Jupyter 中以 %run 执行，也可直接用 python 执行。

示例 04：写作辅助（摘要、翻译、润色、大纲、文献综述）。
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
from rich.text import Text

from src.reference.bibtex_manager import PaperMeta as BibPaperMeta
from src.utils.io import ensure_dir, save_json
from src.writer.llm_helper import AcademicWriter, WritingResponse


console = Console()


SAMPLE_INPUT = """
Recent advances in large language models have led to remarkable
performance across many natural language understanding tasks. However,
LLMs are prone to hallucinating facts and cannot incorporate new
knowledge after training. Retrieval-Augmented Generation (RAG) addresses
these limitations by retrieving relevant documents from an external
corpus and conditioning generation on those documents. Our experiments
demonstrate that RAG improves factuality on open-domain QA benchmarks,
reducing hallucination rates by up to 12.1%. We further show that hybrid
retrieval strategies combining sparse and dense signals provide a strong
cost-quality trade-off. These findings suggest that retrieval-augmented
approaches are a promising direction for grounding language models in
external knowledge bases.
""".strip()


SAMPLE_PAPERS_SUMMARIES = [
    "Lewis et al. propose Retrieval-Augmented Generation, which retrieves "
    "relevant documents from a parametric memory and uses them to condition "
    "generation. Evaluated on open-domain QA and fact verification.",
    "Gao et al. survey recent progress in retrieval-augmented generation, "
    "providing a taxonomy of retrieval strategies, generation methods, and "
    "common benchmarks.",
    "Izacard et al. study leveraging passage retrieval with generative "
    "models for open-domain question answering, with a focus on "
    "jointly-trained retrievers and generators.",
]


def pretty(label: str, response: WritingResponse) -> None:
    content = response.content.strip()
    styled = Text()
    styled.append(f"{label}\n", style="bold cyan")
    styled.append(content, style="white")
    console.print(
        Panel(
            styled,
            border_style="cyan",
            title=f"[bold]{label}[/bold]",
            title_align="left",
        )
    )
    console.print(
        f"[dim]模型：{response.model_name or 'mock'}  耗时：{response.used_time:.3f}s[/dim]"
    )


def run_demo() -> None:
    console.rule("[bold cyan]Demo 04：写作辅助（摘要 / 翻译 / 润色 / 大纲 / 综述）")

    provider = os.environ.get("WRITER_PROVIDER", "mock").strip().lower()
    model = os.environ.get("WRITER_MODEL", "mock-model").strip()

    writer = AcademicWriter(provider=provider, model=model)
    console.print(
        f"[dim]使用 provider={provider}, model={model}（在 mock 模式下将返回模板化响应）[/dim]"
    )

    summary = writer.summarize_text(SAMPLE_INPUT, max_sentences=5)
    pretty("摘要（Summary）", summary)

    translate = writer.translate_academic(SAMPLE_INPUT, target_lang="zh-CN")
    pretty("学术翻译（中译）", translate)

    polish = writer.polish_paragraph(SAMPLE_INPUT, style="academic")
    pretty("段落润色", polish)

    topic = os.environ.get("OUTLINE_TOPIC", "Retrieval-Augmented Generation")
    outline = writer.generate_outline(topic, sections=6)
    pretty(f"论文大纲（主题：{topic}）", outline)

    review = writer.generate_literature_review(SAMPLE_PAPERS_SUMMARIES, topic=topic)
    pretty("文献综述", review)

    citation_paper = BibPaperMeta(
        title=topic,
        authors=["Demo Author"],
        year="2024",
        journal="Demo Journal",
        doi="10.0000/demo",
    )
    bibtex_cite = writer.format_citation(citation_paper, fmt="bibtex")
    apa_cite = writer.format_citation(citation_paper, fmt="apa")
    gb_cite = writer.format_citation(citation_paper, fmt="gb7714")

    console.rule("[bold green]引用格式化示例")
    console.print("[bold]BibTeX:[/bold]")
    console.print(bibtex_cite.content)
    console.print()
    console.print("[bold]APA:[/bold] " + apa_cite.content)
    console.print("[bold]GB7714:[/bold] " + gb_cite.content)

    data_dir = Path(os.environ.get("OUTPUT_DIR", str(WORKSPACE_ROOT / "data")))
    ensure_dir(str(data_dir))
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "model": model,
        "input": SAMPLE_INPUT,
        "summary": summary.content,
        "translation": translate.content,
        "polish": polish.content,
        "outline": outline.content,
        "literature_review": review.content,
        "citations": {
            "bibtex": bibtex_cite.content,
            "apa": apa_cite.content,
            "gb7714": gb_cite.content,
        },
    }
    save_json(payload, str(data_dir / "writing_demo_output.json"))
    console.print(f"[green]写作结果已保存：[/green] {data_dir / 'writing_demo_output.json'}")


if __name__ == "__main__":
    run_demo()
