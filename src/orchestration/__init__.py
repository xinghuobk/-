"""ParaJudge 主编排器（Orchestrator）。

串联 Phase 0 → Phase 1 → Phase 2.1 → Phase 2.2 并生成
FullPipelineOutput、控制台报告与 Markdown 裁决书。
"""
from src.orchestration.orchestrator import run_parajudge, render_console, render_markdown

__all__ = ["run_parajudge", "render_console", "render_markdown"]
