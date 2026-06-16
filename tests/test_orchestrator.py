"""测试 Phase 0→1→2 全流程编排（Orchestrator）。

覆盖点：
- run_parajudge 返回完整的 FullPipelineOutput
- render_console / render_markdown 输出非空字符串
- CLI 子命令 parajudge run 可正常执行
"""
from __future__ import annotations

import pytest
from backend.models.schemas import FullPipelineOutput
from src.orchestration.orchestrator import run_parajudge, render_console, render_markdown


# ======================================================================
# run_parajudge 全流程（使用 mock provider，不访问真实网络）
# ======================================================================

class TestRunParaJudge:
    def test_full_pipeline_returns_valid_output(self):
        output = run_parajudge(
            "LLM 是否会取代人类大部分工作？",
            provider="mock",
            rounds=2,
            max_evidence=5,
            enable_llm_review=True,
        )
        assert isinstance(output, FullPipelineOutput)
        # 核心字段类型
        assert output.problem
        assert output.run_id
        assert output.total_time_sec >= 0
        # 各阶段产物应被填充
        assert output.evidence_brief.total_count >= 0
        assert output.transcript.rounds_total == 2
        assert len(output.judgment.judge_scores) == 5

    def test_run_id_unique_across_invocations(self):
        """多次调用应返回不同 run_id。"""
        run_ids = []
        for _ in range(3):
            out = run_parajudge("测试问题", provider="mock", rounds=1, max_evidence=3)
            run_ids.append(out.run_id)
        assert len(set(run_ids)) == 3, f"run_id 不应重复: {run_ids}"

    def test_without_llm_review_still_works(self):
        """关闭 LLM review 时也应正常生成报告。"""
        output = run_parajudge(
            "测试问题",
            provider="mock",
            rounds=1,
            max_evidence=3,
            enable_llm_review=False,
        )
        assert output.review.critical_count + output.review.warning_count >= 0
        # 判决不应抛异常
        assert output.judgment.winner in ("pro", "con", "tie")


# ======================================================================
# 控制台 & Markdown 渲染
# ======================================================================

class TestRender:
    def test_console_output_is_non_empty(self):
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        text = render_console(output)
        assert isinstance(text, str)
        assert len(text.strip()) > 0

    def test_console_output_contains_winner(self):
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        text = render_console(output)
        winner_label_map = {"pro": "正方胜出", "con": "反方胜出", "tie": "平局"}
        expected = winner_label_map.get(output.judgment.winner, output.judgment.winner)
        assert expected in text or output.judgment.winner.lower() in text.lower()

    def test_console_output_contains_score_summary(self):
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        text = render_console(output)
        # 应能在报告中找到评分相关信息
        assert str(int(output.judgment.pro_final_score)) in text or \
               "正方" in text

    def test_markdown_output_non_empty(self):
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        md = render_markdown(output)
        assert isinstance(md, str)
        assert len(md.strip()) > 0

    def test_markdown_output_has_headings(self):
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        md = render_markdown(output)
        assert md.startswith("#")
        # 至少有一个二级标题
        assert "\n## " in md

    def test_markdown_contains_judge_table(self):
        """裁决书的 Markdown 中应该包含法官评分表。"""
        output = run_parajudge("问题", provider="mock", rounds=1, max_evidence=3)
        md = render_markdown(output)
        # 表格特征：每行有 | 分隔符，且至少有评分列
        lines_with_pipe = [l for l in md.splitlines() if l.strip().startswith("|")]
        assert len(lines_with_pipe) >= 3, "应至少有 header、分隔符、若干数据行"


# ======================================================================
# CLI 子命令
# ======================================================================

class TestCLI:
    def test_cli_help_works(self, capsys):
        """python -m pytest 下使用 typer.CliRunner 会更稳定，但这里直接用 subprocess 更简单。"""
        import subprocess
        result = subprocess.run(
            ["python", str(_project_root() / "cli.py"), "parajudge", "--help"],
            capture_output=True,
            text=True,
            cwd=str(_project_root()),
            timeout=30,
        )
        assert result.returncode == 0
        assert "parajudge" in result.stdout.lower()

    def test_cli_parajudge_run_mock(self, tmp_path, capsys):
        """CLI 子命令应能执行 mock 全流程并返回。"""
        import subprocess
        out_md = tmp_path / "out.md"
        out_json = tmp_path / "out.json"
        result = subprocess.run(
            [
                "python", str(_project_root() / "cli.py"),
                "parajudge", "run",
                "LLM 是否会取代人类大部分工作？",
                "--rounds", "1",
                "--save-md", str(out_md),
                "--save-json", str(out_json),
            ],
            capture_output=True,
            text=True,
            cwd=str(_project_root()),
            timeout=120,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out_md.exists()
        assert out_json.exists()
        # Markdown 非空
        assert out_md.read_text(encoding="utf-8").strip()
        # JSON 能被解析
        import json
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert "run_id" in data
        assert "judgment" in data
        assert data["judgment"]["winner"] in ("pro", "con", "tie")


def _project_root():
    from pathlib import Path
    return Path(__file__).resolve().parent.parent
