"""ParaJudge Web 前端（v0.3.0）。

提供两个访问方式：
1. `python -m parajudge_web` 或运行 `python web_server.py` 启动独立服务器
2. `python cli.py parajudge run` 运行命令行后，访问 `python web_server.py` 查看报告

路由：
  GET  /                  → 辩论主页
  GET  /runs              → 历史运行列表
  GET  /run/{run_id}      → 查看指定运行
  POST /api/run           → 发起一次新的辩论（JSON）
  GET  /static/{file}     → 静态资源
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.orchestration.orchestrator import run_parajudge, render_markdown


PARAJUDGE_VERSION = "0.3.0"

app = FastAPI(title="ParaJudge 多智能体辩论系统", version=PARAJUDGE_VERSION)

# 运行数据存储目录
RUNS_DIR = Path(os.environ.get("EXPERIMENT_OUTPUT_DIR", "./experiments"))
RUNS_DIR.mkdir(parents=True, exist_ok=True)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index():
    """辩论主页：输入问题 → 看到全过程可视化。"""
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return _fallback_index()


@app.get("/runs", response_class=HTMLResponse)
def runs_page():
    """历史运行列表页面。"""
    runs = _list_runs()
    rows_html = ""
    if not runs:
        rows_html = "<tr><td colspan='5' class='empty'>暂无运行记录</td></tr>"
    else:
        for r in runs:
            try:
                data = json.loads((RUNS_DIR / r["dir"] / "output.json").read_text(encoding="utf-8"))
                winner = data["judgment"]["winner"]
                pro = data["judgment"]["pro_final_score"]
                con = data["judgment"]["con_final_score"]
                problem = data["problem"][:80]
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data["timestamp"]))
                cost = data["llm_stats"]["total_cost_cny"] if "llm_stats" in data else 0
                rows_html += (
                    f"<tr onclick=\"location.href='/run/{r['run_id']}'\">"
                    f"<td><code>{r['run_id']}</code></td>"
                    f"<td>{problem}</td>"
                    f"<td>{winner.upper()} (P{pro:.1f}/C{con:.1f})</td>"
                    f"<td>¥{cost:.4f}</td>"
                    f"<td>{ts}</td></tr>"
                )
            except Exception:
                pass
    html = (STATIC_DIR / "runs.html").read_text(encoding="utf-8") if (STATIC_DIR / "runs.html").exists() else None
    if html:
        return html.replace("<!--RUNS_ROWS-->", rows_html)
    return _fallback_runs_page(rows_html)


@app.get("/run/{run_id}", response_class=HTMLResponse)
def run_detail_page(run_id: str):
    """查看指定运行的完整可视化报告。"""
    run_path = _find_run_dir(run_id)
    if run_path is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} 不存在")
    output_json = run_path / "output.json"
    data = json.loads(output_json.read_text(encoding="utf-8"))
    data_json = json.dumps(data, ensure_ascii=False)

    html_path = STATIC_DIR / "run_detail.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8").replace(
            "<!--RUN_DATA-->", f"<script>window.__PARAJUDGE_RUN__ = {data_json};</script>"
        )
    return _fallback_run_detail_html(data)


@app.post("/api/run")
def api_run(payload: Dict[str, Any]):
    """异步发起一次辩论 + 返回 FullPipelineOutput JSON。"""
    problem = payload.get("problem", "").strip()
    if not problem:
        return JSONResponse(status_code=400, content={"error": "问题不能为空"})

    provider = payload.get("provider", "mock")
    model = payload.get("model", "mock-model")
    rounds = int(payload.get("rounds", 3))
    max_evidence = int(payload.get("max_evidence", 20))
    api_key = payload.get("api_key") or None
    enable_llm_review = bool(payload.get("enable_llm_review", True))

    try:
        output = run_parajudge(
            problem=problem,
            provider=provider,
            model=model,
            api_key=api_key,
            rounds=rounds,
            max_evidence=max_evidence,
            enable_llm_review=enable_llm_review,
        )

        # 保存到 experiments 目录
        from src.orchestration.orchestrator import save_experiment
        save_experiment(output)

        return json.loads(output.model_dump_json())
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )


@app.get("/api/runs")
def api_list_runs():
    return {"runs": _list_runs()}


@app.get("/api/run/{run_id}")
def api_get_run(run_id: str):
    run_path = _find_run_dir(run_id)
    if run_path is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} 不存在")
    data = json.loads((run_path / "output.json").read_text(encoding="utf-8"))
    return data


# ── 辅助函数 ────────────────────────────────────────

def _list_runs() -> List[Dict[str, Any]]:
    """列出 experiments 下的所有运行记录（按时间倒序）。"""
    if not RUNS_DIR.exists():
        return []
    dirs = [d for d in RUNS_DIR.iterdir() if d.is_dir() and (d / "output.json").exists()]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    runs = []
    for d in dirs[:50]:  # 最多显示 50 条
        try:
            data = json.loads((d / "output.json").read_text(encoding="utf-8"))
            runs.append({
                "run_id": data.get("run_id", d.name),
                "dir": d.name,
                "problem": data.get("problem", ""),
                "timestamp": data.get("timestamp", d.stat().st_mtime),
            })
        except Exception:
            pass
    return runs


def _find_run_dir(run_id: str) -> Optional[Path]:
    for d in RUNS_DIR.iterdir():
        if not d.is_dir():
            continue
        if run_id in d.name:
            return d
    return None


# ── Fallback HTML（以防 static 文件缺失）───────────

def _fallback_index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8") if (STATIC_DIR / "index.html").exists() else """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>ParaJudge</title></head>
<body style="font-family:system-ui"><h1>ParaJudge 多智能体辩论系统</h1>
<p>正在加载前端资源...</p></body></html>"""


def _fallback_runs_page(rows_html: str) -> str:
    return f"""
<!doctype html>
<html><head><meta charset="utf-8"><title>ParaJudge · 历史运行</title></head>
<body style="font-family:system-ui">
<h1>历史运行</h1><table border="1">
<tr><th>Run ID</th><th>问题</th><th>裁决</th><th>成本</th><th>时间</th></tr>
{rows_html}
</table></body></html>"""


def _fallback_run_detail_html(data: Dict[str, Any]) -> str:
    md = render_markdown.__globals__.get("render_markdown", None)
    from src.orchestration.orchestrator import render_markdown as _rmd
    md_text = _rmd(_dict_to_output(data))
    return f"<html><head><meta charset='utf-8'><title>ParaJudge · {data.get('run_id','')}</title></head><body><pre>{md_text}</pre></body></html>"


def _dict_to_output(data):
    """将 dict 转换为对象以便 render_markdown 调用。"""
    class _Obj:
        def __init__(self, d):
            self._d = d
            for k, v in d.items():
                if isinstance(v, dict):
                    setattr(self, k, _Obj(v))
                elif isinstance(v, list):
                    setattr(self, k, [_Obj(x) if isinstance(x, dict) else x for x in v])
                else:
                    setattr(self, k, v)
    return _Obj(data)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    print(f"🌐 ParaJudge v{PARAJUDGE_VERSION} Web 控制台")
    print(f"  访问 http://127.0.0.1:{port}/")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
