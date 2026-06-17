"""Step 4 · 6 组消融实验。

6 组配置：
  - full    : T1+T2+T3+T4 全开
  - -T1     : 关 T1 Bipartite HITS（用通用 PageRank）
  - -T2     : 关 T2 k-DPP（用随机选）
  - -T3     : 关 T3 BOCPD（固定轮数）
  - -T4     : 关 T4 Murphy（用简单加权平均）
  - all-off : 4 个创新点全关（baseline）

每组 × 24 题 = 144 次完整 ParaJudge 流程。

**不编造**：所有实验真实跑通；失败诚实记录。

输出：experiments/v0.3_real_external/ablation_<timestamp>.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))
EXP_DIR = Path("experiments/v0.3_real_external")
EXP_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 6 组消融配置
# ============================================================

ABLATIONS = [
    {"name": "full",    "T1": True,  "T2": True,  "T3": True,  "T4": True},
    {"name": "no_T1",   "T1": False, "T2": True,  "T3": True,  "T4": True},
    {"name": "no_T2",   "T1": True,  "T2": False, "T3": True,  "T4": True},
    {"name": "no_T3",   "T1": True,  "T2": True,  "T3": False, "T4": True},
    {"name": "no_T4",   "T1": True,  "T2": True,  "T3": True,  "T4": False},
    {"name": "all_off", "T1": False, "T2": False, "T3": False, "T4": False},
]


# 24 题（与 run_real_llm_e2e.py 一致；导入避免重复）
from run_real_llm_e2e import QUESTIONS


def run_one_ablation(abl: Dict[str, Any], q: Dict[str, Any],
                     provider: str, model: str, rounds: int = 2,
                     max_evidence: int = 5) -> Dict[str, Any]:
    """跑 1 组消融 × 1 题。"""
    from src.orchestration.orchestrator import run_parajudge

    t0 = time.perf_counter()
    rec = {
        "ablation": abl["name"],
        "config": {k: v for k, v in abl.items() if k != "name"},
        "question_id": q["id"],
        "category": q["category"],
        "question": q["question"],
        "provider": provider,
        "model": model,
        "rounds": rounds,
        "status": "PENDING",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        out = run_parajudge(
            problem=q["question"],
            provider=provider,
            model=model,
            rounds=rounds,
            max_evidence=max_evidence,
            enable_moderator=abl["T1"],  # 用 T1 字段映射 moderator（统一开关）
            enable_t1_aebg=abl["T1"],
            enable_t3_ks=abl["T3"],
            enable_t4_ds=abl["T4"],
        )
        rec.update({
            "run_id": out.run_id,
            "winner": out.judgment.winner,
            "pro_score": out.judgment.pro_final_score,
            "con_score": out.judgment.con_final_score,
            "n_args": len(out.transcript.arguments),
            "total_time_sec": out.total_time_sec,
            "status": "OK",
        })
    except Exception as e:
        rec["status"] = "ERROR"
        rec["error"] = str(e)
        rec["traceback"] = traceback.format_exc()
    rec["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec["wall_time_sec"] = round(time.perf_counter() - t0, 2)
    return rec


def main():
    ap = argparse.ArgumentParser(description="消融实验")
    ap.add_argument("--provider", required=True, choices=["mock", "ollama", "openai", "dashscope"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--questions", type=int, default=24)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--max-evidence", type=int, default=5)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    default_models = {
        "ollama": "qwen2.5:7b",
        "openai": "gpt-4o-mini",
        "dashscope": "qwen-plus",
        "mock": "mock-model",
    }
    model = args.model or default_models[args.provider]

    print("=" * 60)
    print(f"ParaJudge 消融实验")
    print(f"Provider: {args.provider} | Model: {model}")
    print(f"6 组 × {args.questions} 题 = {6 * args.questions} 次")
    print("=" * 60)

    n = min(args.questions, len(QUESTIONS))
    selected = QUESTIONS[:n]

    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    out_path = Path(args.output) if args.output else EXP_DIR / f"ablation_{args.provider}_{model.replace(':', '-').replace('.', '-')}_{ts}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for abl in ABLATIONS:
            print(f"\n=== 配置: {abl['name']} ===")
            for i, q in enumerate(selected, start=1):
                print(f"  [{i}/{n}] q={q['id']:02d}", end=" ")
                rec = run_one_ablation(abl, q, args.provider, model,
                                       rounds=args.rounds, max_evidence=args.max_evidence)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if rec["status"] == "OK":
                    print(f"winner={rec['winner']} pro={rec['pro_score']:.1f} con={rec['con_score']:.1f} | {rec['wall_time_sec']}s")
                else:
                    print(f"ERROR: {rec.get('error', '')[:80]}")

    print()
    print("=" * 60)
    print(f"完成。结果：{out_path}")
    print(f"共 {6 * n} 条")
    print("=" * 60)
    print(f"下一步: python scripts/run_real_statistics.py --ablation {out_path}")


if __name__ == "__main__":
    main()
