"""批量实验脚本：对一组问题运行 ParaJudge 并输出结果。

用法：
    python scripts/run_batch.py --provider ollama --model qwen2.5:7b \\
        --questions 1 2 3 --rounds 3

输出：
    experiments/batch_<timestamp>/results.jsonl
    experiments/batch_<timestamp>/summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

# 24 题测试集（来自附录 A）
ALL_QUESTIONS = {
    1: "LLM 是否会取代人类大部分工作？",
    2: "AGI 是否会在 2030 年前实现？",
    3: "量子计算能否在 10 年内实现商业化？",
    4: "Transformer 架构是否会被新模型取代？",
    5: "RAG 是否会取代微调成为主流？",
    6: "AI 科研是否降低了学术创新的门槛？",
    7: "AI 创造的新岗位是否能抵消被替代的岗位？",
    8: "AI 辅助教学会取代传统教师吗？",
    9: "AI 生成内容是否应受到版权保护？",
    10: "AI 写论文是否应被认定为学术不端？",
    11: "大模型是否真正理解语言，还是仅是统计拟合？",
    12: "AI 对齐问题是否可解？",
    13: "推理模型（如 o1/R1）是否代表新范式？",
    14: "多模态是否是 LLM 的必然方向？",
    15: "开源 LLM 是否会超越闭源？",
    16: "AI 决策的\"黑箱\"是否能被法律接受？",
    17: "AI 是否会加剧社会不平等？",
    18: "AI 大模型的训练数据是否应被公开？",
    19: "AI 监管是否应该全球统一？",
    20: "7B 本地模型能完成怎样的推理？",
    21: "中小模型在垂直领域是否优于大模型？",
    22: "模型量化（4-bit）对推理质量的影响？",
    23: "本地推理的隐私优势是否值得性能损失？",
    24: "CPU 推理是否仍是可行的方案？",
}


def run_batch(
    question_ids: List[int],
    provider: str,
    model: str,
    rounds: int,
    max_evidence: int,
    base_url: str | None,
    output_dir: Path,
    temperature: float = 0.7,
) -> dict:
    """运行一批实验并保存结果。"""
    from src.orchestration.orchestrator import run_parajudge

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    t_start = time.time()

    for qid in question_ids:
        question = ALL_QUESTIONS.get(qid)
        if not question:
            print(f"  [SKIP] 未知题号 {qid}")
            continue

        print(f"\n[{qid:02d}/24] {question}")
        print(f"  provider={provider} model={model} rounds={rounds}")

        t0 = time.time()
        try:
            result = run_parajudge(
                problem=question,
                provider=provider,
                model=model,
                rounds=rounds,
                max_evidence=max_evidence,
            )
            elapsed = time.time() - t0

            record = {
                "question_id": qid,
                "question": question,
                "run_id": result.run_id,
                "elapsed_sec": round(elapsed, 2),
                "winner": result.judgment.winner,
                "pro_score": result.judgment.pro_final_score,
                "con_score": result.judgment.con_final_score,
                "pro_args_count": result.transcript.argument_index.pro_count,
                "con_args_count": result.transcript.argument_index.con_count,
                "review_critical": result.review.critical_count,
                "review_warning": result.review.warning_count,
                "evidence_count": len(result.evidence_brief.items),
            }
            print(f"  → winner={result.judgment.winner} "
                  f"pro={result.judgment.pro_final_score} "
                  f"con={result.judgment.con_final_score} "
                  f"({elapsed:.1f}s)")
        except Exception as e:
            record = {
                "question_id": qid,
                "question": question,
                "error": str(e),
            }
            print(f"  [ERROR] {e}")

        results.append(record)
        # 实时落盘
        with open(output_dir / "results.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 总结
    total_sec = time.time() - t_start
    summary = {
        "config": {
            "provider": provider,
            "model": model,
            "rounds": rounds,
            "max_evidence": max_evidence,
            "temperature": temperature,
            "base_url": base_url,
        },
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(results),
        "total_time_sec": round(total_sec, 2),
        "avg_time_sec": round(total_sec / max(len(results), 1), 2),
        "winners": {
            "pro": sum(1 for r in results if r.get("winner") == "pro"),
            "con": sum(1 for r in results if r.get("winner") == "con"),
            "tie": sum(1 for r in results if r.get("winner") == "tie"),
            "error": sum(1 for r in results if "error" in r),
        },
        "avg_pro_score": round(
            sum(r.get("pro_score", 0) for r in results) / max(len(results), 1), 2
        ),
        "avg_con_score": round(
            sum(r.get("con_score", 0) for r in results) / max(len(results), 1), 2
        ),
    }
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n=== 批量完成 ===")
    print(f"  题目: {summary['total_questions']}")
    print(f"  耗时: {summary['total_time_sec']}s（平均 {summary['avg_time_sec']}s/题）")
    print(f"  胜方: pro={summary['winners']['pro']} con={summary['winners']['con']} "
          f"tie={summary['winners']['tie']} error={summary['winners']['error']}")
    print(f"  输出: {output_dir}/")
    return summary


def main():
    parser = argparse.ArgumentParser(description="ParaJudge 批量实验")
    parser.add_argument("--questions", nargs="+", type=int, default=[1, 2, 3, 4, 5],
                        help="题号列表（1-24）")
    parser.add_argument("--provider", default="mock", help="LLM provider")
    parser.add_argument("--model", default="mock-model", help="模型名")
    parser.add_argument("--base-url", default=None, help="OpenAI 兼容端点")
    parser.add_argument("--rounds", type=int, default=3, help="辩论轮数")
    parser.add_argument("--max-evidence", type=int, default=10, help="证据上限")
    parser.add_argument("--temperature", type=float, default=0.7, help="温度")
    parser.add_argument("--output", default=None, help="输出目录")
    args = parser.parse_args()

    # 默认输出目录
    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        args.output = f"experiments/batch_{args.provider}_{ts}"

    output_dir = Path(args.output)
    print(f"=== ParaJudge 批量实验 ===")
    print(f"  输出目录: {output_dir}")
    print(f"  题数: {len(args.questions)}")
    print()

    summary = run_batch(
        question_ids=args.questions,
        provider=args.provider,
        model=args.model,
        rounds=args.rounds,
        max_evidence=args.max_evidence,
        base_url=args.base_url,
        output_dir=output_dir,
        temperature=args.temperature,
    )

    return 0 if summary["winners"]["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
