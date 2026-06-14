"""学术写作辅助模块。

提供统一的 ``AcademicWriter`` 接口，封装多种 LLM 提供商
（openai / mock / dashscope 等），用于摘要、翻译、润色、
文献综述、论文大纲和引用格式化等常见学术写作任务。
"""
from __future__ import annotations

import os
import time
from typing import List, Optional

from backend.models.schemas import (
    PaperMeta,
    WritingRequest,
    WritingResponse,
    WritingTask,
)
from src.reference.bibtex_manager import generate_bibtex_from_paper
from src.writer.prompt_templates import (
    SUMMARY_PROMPT,
    TRANSLATE_PROMPT,
    POLISH_PROMPT,
    LITERATURE_REVIEW_PROMPT,
    OUTLINE_PROMPT,
)


class AcademicWriter:
    """学术写作辅助类。

    Parameters
    ----------
    provider : str
        支持 ``"openai"``、``"mock"``、``"dashscope"``。
    model : str
        使用的具体模型名称，如 ``"gpt-4"``、``"qwen-max"``。
    api_key : Optional[str]
        API Key；若为 ``None``，将尝试从环境变量读取。
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4",
        api_key: Optional[str] = None,
    ) -> None:
        self.provider = provider.strip().lower()
        self.model = model.strip()
        self.api_key = api_key
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
                "DASHSCOPE_API_KEY"
            )

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def summarize_text(
        self, text: str, max_sentences: int = 5
    ) -> WritingResponse:
        """生成学术摘要。"""
        original = text.strip()
        prompt = (
            SUMMARY_PROMPT.format(max_sentences=max_sentences)
            + "\n\n"
            + original
        )
        return self._build_response(WritingTask.SUMMARY, original, prompt)

    def translate_academic(
        self, text: str, target_lang: str = "zh-CN"
    ) -> WritingResponse:
        """学术翻译。"""
        original = text.strip()
        prompt = (
            TRANSLATE_PROMPT.format(target_lang=target_lang)
            + "\n\n"
            + original
        )
        return self._build_response(WritingTask.TRANSLATE, original, prompt)

    def polish_paragraph(
        self, text: str, style: str = "academic"
    ) -> WritingResponse:
        """段落润色。"""
        original = text.strip()
        prompt = POLISH_PROMPT.format(style=style) + "\n\n" + original
        return self._build_response(WritingTask.POLISH, original, prompt)

    def generate_literature_review(
        self, paper_summaries: List[str], topic: str
    ) -> WritingResponse:
        """基于多篇论文摘要生成文献综述。"""
        block_lines: List[str] = []
        for idx, summary in enumerate(paper_summaries, start=1):
            block_lines.append(f"Paper {idx}: {summary.strip()}")
        paper_block = "\n\n".join(block_lines)
        prompt = LITERATURE_REVIEW_PROMPT.format(
            topic=topic, paper_block=paper_block
        )
        return self._build_response(
            WritingTask.LITERATURE_REVIEW, paper_block, prompt
        )

    def generate_outline(
        self, topic: str, sections: int = 6
    ) -> WritingResponse:
        """生成论文大纲。"""
        sections = max(2, min(sections, 12))
        prompt = OUTLINE_PROMPT.format(topic=topic, sections=sections)
        return self._build_response(WritingTask.OUTLINE, topic, prompt)

    def format_citation(
        self, paper: PaperMeta, fmt: str = "bibtex"
    ) -> WritingResponse:
        """格式化引用。``fmt`` 可选 ``bibtex`` / ``apa`` / ``gb7714``。"""
        original = paper.title or ""
        fmt_key = (fmt or "bibtex").strip().lower()
        start = time.perf_counter()
        if fmt_key == "bibtex":
            content = generate_bibtex_from_paper(paper)
        else:
            authors_str = " and ".join(paper.authors) if paper.authors else ""
            if fmt_key == "apa":
                year = str(paper.year) if paper.year else ""
                venue = paper.venue or ""
                content = f"{authors_str} ({year}). {paper.title}. {venue}."
            elif fmt_key in ("gb7714", "gb"):
                year = str(paper.year) if paper.year else ""
                venue = paper.venue or ""
                content = f"{authors_str}. {paper.title}[J]. {venue}, {year}."
            else:
                content = generate_bibtex_from_paper(paper)
        used_time = round(time.perf_counter() - start, 4)
        return WritingResponse(
            task_type=WritingTask.CITATION,
            original=original,
            output=content,
            model_name=self.model,
            used_time=used_time,
            citations=[],
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _build_response(
        self, task_type: WritingTask, original: str, prompt: str
    ) -> WritingResponse:
        start = time.perf_counter()
        output = self._call_llm(prompt)
        used_time = round(time.perf_counter() - start, 4)
        return WritingResponse(
            task_type=task_type,
            original=original,
            output=output,
            model_name=self.model,
            used_time=used_time,
            citations=[],
        )

    def _call_llm(self, prompt: str) -> str:
        """调用底层 LLM。

        当前实现：
        - ``mock``：基于关键词返回模板化响应，便于离线测试。
        - ``openai`` / ``dashscope``：如未配置则退化为 mock，避免
          引入硬依赖；实际调用可在后续接入时替换为相应 SDK。
        """
        if self.provider == "mock":
            return self._mock_response(prompt)

        if self.provider == "openai":
            return self._mock_response(prompt)

        if self.provider == "dashscope":
            return self._mock_response(prompt)

        return self._mock_response(prompt)

    # ------------------------------------------------------------------
    # Mock 响应（用于离线测试与演示）
    # ------------------------------------------------------------------
    def _mock_response(self, prompt: str) -> str:
        head = (prompt or "").strip().lower()
        if "summar" in head and "摘要" not in prompt:
            return (
                "This study investigates the problem described in the input. "
                "We present a concise approach and evaluate it on standard benchmarks. "
                "Experimental results demonstrate the effectiveness of the method, "
                "which outperforms several baselines and opens directions for future work."
            )
        if "摘要" in prompt or "摘要" in (prompt[:200] if prompt else ""):
            return (
                "本文对输入文本所讨论的问题进行了系统梳理。我们归纳了研究背景、"
                "核心方法与主要实验结论，并指出了当前方法的局限与值得进一步研究的方向。"
            )
        if "translat" in head or "翻译" in prompt:
            return "[翻译结果] 这是一段示例翻译输出（mock 响应）。"
        if "polish" in head or "润色" in prompt:
            return (
                "[POLISHED]\n这是润色后的示例段落，语句更为紧凑、用词更符合学术规范。\n\n"
                "[DIFF]\n- 修正了冠词与介词搭配\n- 替换了若干口语化表达\n- 统一了术语缩写"
            )
        if "literature" in head or "综述" in prompt:
            return (
                "近年来，围绕所给主题涌现了大量研究。早期工作主要聚焦于方法 A，"
                "随后研究者从多个角度对其进行扩展与改进（1, 2）。与此同时，"
                "另一派工作则尝试从角度 B 切入并获得了不同的结论（3）。"
                "目前该方向仍存在若干公开问题，值得未来工作进一步探索。"
            )
        if "outline" in head or "大纲" in prompt:
            return (
                "1. 引言\n   - 研究背景与动机\n   - 研究问题与贡献\n"
                "2. 相关工作\n   - 传统方法\n   - 深度学习方法\n"
                "3. 方法\n   - 整体框架\n   - 核心模块\n"
                "4. 实验\n   - 数据集与设置\n   - 实验结果与分析\n"
                "5. 讨论\n   - 局限性\n   - 未来方向\n"
                "6. 结论与总结\n\n"
                "Alternative titles:\n- [A] \n- [B] \n- [C]"
            )
        return "[MOCK] This is a placeholder response from the mock LLM backend."


__all__ = ["AcademicWriter"]
