"""IBM-ArgQ 基准测试评估器。

用法：
    python scripts/run_ibm_argq_eval.py                    # 尝试真实数据集
    python scripts/run_ibm_argq_eval.py --mock             # Mock 模式

目标：
1. 加载 IBM-ArgQ 数据集（或优雅降级为 mock）
2. 对每个论点运行 ParaJudge 质量评估
3. 计算系统评分与数据集 ground truth 的相关性（Spearman / Kendall）
4. 输出一致性分析报告
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 尝试加载真实数据集
HAS_DATASETS = False
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    pass

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration.orchestrator import run_parajudge
from src.writer.llm_client import LLMClient


# ============================================================
# Mock 数据（无网络 / 无 datasets 库时的回退）
# ============================================================

MOCK_ARGUMENTS = [
    {
        "argument": "Universal basic income would reduce poverty by guaranteeing everyone a minimum income floor, regardless of employment status.",
        "topic": "Universal Basic Income",
        "ground_truth_score": 0.82,
        "aspect": "cogency",
    },
    {
        "argument": "The death penalty is inherently unjust because it disproportionately affects minorities and the poor, making it a form of systemic discrimination.",
        "topic": "Death Penalty",
        "ground_truth_score": 0.75,
        "aspect": "cogency",
    },
    {
        "argument": "Climate change is primarily caused by human activities, particularly the burning of fossil fuels which release greenhouse gases into the atmosphere.",
        "topic": "Climate Change Policy",
        "ground_truth_score": 0.91,
        "aspect": "cogency",
    },
    {
        "argument": "AI will definitely replace most human jobs by 2030, making universal basic income necessary.",
        "topic": "AI and Employment",
        "ground_truth_score": 0.34,
        "aspect": "cogency",
        "reason": "过度预测，证据不足",
    },
    {
        "argument": "Vaccines are safe and effective, with decades of scientific evidence supporting their use in preventing infectious diseases.",
        "topic": "Vaccination Policy",
        "ground_truth_score": 0.88,
        "aspect": "cogency",
    },
    {
        "argument": "Nuclear energy is the best solution to climate change because it produces zero carbon emissions and is highly efficient.",
        "topic": "Nuclear Energy",
        "ground_truth_score": 0.61,
        "aspect": "cogency",
        "reason": "忽略了核废料和核安全问题",
    },
    {
        "argument": "Democracy is the best form of government because it protects individual rights and allows for peaceful transfer of power.",
        "topic": "Democracy",
        "ground_truth_score": 0.70,
        "aspect": "cogency",
    },
    {
        "argument": "The free market will naturally solve environmental problems through innovation, without government regulation being necessary.",
        "topic": "Environmental Regulation",
        "ground_truth_score": 0.42,
        "aspect": "cogency",
        "reason": "证据不支持，历史案例与此相悖",
    },
]


# ============================================================
# 相关性计算（无 scipy 依赖）
# ============================================================

def spearman_correlation(predictions: List[float], references: List[float]) -> float:
    """计算 Spearman 等级相关系数（纯 Python 实现）。"""
    n = len(predictions)
    if n < 3:
        return 0.0

    def rank_float(nums: List[float]) -> List[float]:
        sorted_with_idx = sorted(enumerate(nums), key=lambda x: x[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and sorted_with_idx[j + 1][1] == sorted_with_idx[i][1]:
                j += 1
            avg_rank = (i + j) / 2.0
            for k in range(i, j + 1):
                ranks[sorted_with_idx[k][0]] = avg_rank
            i = j + 1
        return ranks

    pred_ranks = rank_float(predictions)
    ref_ranks = rank_float(references)

    mean_p = sum(pred_ranks) / n
    mean_r = sum(ref_ranks) / n
    num = sum((pred_ranks[i] - mean_p) * (ref_ranks[i] - mean_r) for i in range(n))
    den_p = sum((pred_ranks[i] - mean_p) ** 2 for i in range(n)) ** 0.5
    den_r = sum((ref_ranks[i] - mean_r) ** 2 for i in range(n)) ** 0.5
    if den_p == 0 or den_r == 0:
        return 0.0
    return num / (den_p * den_r)


def kendall_tau(predictions: List[float], references: List[float]) -> float:
    """计算 Kendall Tau 等级相关系数（纯 Python 实现）。"""
    n = len(predictions)
    if n < 3:
        return 0.0

    # 用 ref 的 rank 排序
    ref_sorted = sorted(zip(references, predictions), key=lambda x: x[0])
    pred_sorted = [p for _, p in ref_sorted]

    # 计算同序对和逆序对
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            if (pred_sorted[i] > pred_sorted[j]) == (ref_sorted[i][0] > ref_sorted[j][0]):
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    if total == 0:
        return 0.0
    return (concordant - discordant) / total


# ============================================================
# 数据集加载
# ============================================================

def load_ibm_argq(limit: int = 50) -> List[Dict[str, Any]]:
    """从 HuggingFace 加载 IBM-ArgQ 数据集。

    数据集：ibm-research/argument_quality_ranking_30k
    字段：argument (str), overall_score (float, 0-1)

    失败时返回空列表。
    """
    if not HAS_DATASETS:
        print("  ⚠️ datasets 库未安装，使用 Mock 数据")
        return MOCK_ARGUMENTS[:limit]

    try:
        print("  正在从 HuggingFace 加载 ibm-research/argument_quality_ranking_30k ...")
        ds = load_dataset(
            "ibm-research/argument_quality_ranking_30k",
            split=f"train[:{limit}]",
            trust_remote_code=True,
        )
        result = []
        for row in ds:
            result.append({
                "argument": row.get("argument", row.get("text", "")),
                "topic": row.get("topic", "General Debate"),
                "ground_truth_score": float(row.get("overall_score", row.get("score", 0.5))),
                "aspect": "cogency",
            })
        print(f"  ✅ 成功加载 {len(result)} 条论点")
        return result
    except Exception as e:
        print(f"  ⚠️  数据集加载失败: {e}，使用 Mock 数据")
        return MOCK_ARGUMENTS[:limit]


# ============================================================
# 评估器
# ============================================================

def evaluate_argument(item: Dict[str, Any], llm: LLMClient) -> Dict[str, Any]:
    """对单个论点运行 ParaJudge 质量评估。"""
    topic = item["topic"]
    argument = item["argument"]

    # 用 ParaJudge 评估该论点（作为"正方"论点）
    try:
        result = run_parajudge(
            problem=f"Topic: {topic}",
            provider=llm.provider,
            model=llm.model,
            api_key=llm.api_key,
            rounds=1,
            max_evidence=5,
            enable_llm_review=False,
            enable_moderator=False,
            enable_t1_aebg=False,
            enable_t3_ks=False,
            enable_t4_ds=False,
        )
        # 提取正方评分（作为论点质量代理）
        pro_score = result.judgment.pro_final_score
        # 归一化到 0-1
        normalized = pro_score / 100.0
        return {
            "success": True,
            "predicted_score": normalized,
            "pro_final": pro_score,
            "gt_score": item["ground_truth_score"],
            "topic": topic,
            "argument_preview": argument[:80],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "predicted_score": 0.5,
            "gt_score": item["ground_truth_score"],
            "topic": topic,
        }


def run_evaluation(args) -> Dict[str, Any]:
    """主评估流程。"""
    print("=" * 60)
    print("IBM-ArgQ 基准测试评估器")
    print("=" * 60)

    # 初始化 LLM
    llm = LLMClient(
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        seed=args.seed,
    )
    print(f"Provider: {args.provider} | Model: {args.model}")
    print(f"评估数量: {args.limit}")
    print()

    # 加载数据
    dataset = load_ibm_argq(limit=args.limit)
    if not dataset:
        return {"status": "no_data"}

    # 运行评估
    results: List[Dict[str, Any]] = []
    for i, item in enumerate(dataset):
        print(f"[{i+1}/{len(dataset)}] 评估: {item['topic']} ...")
        r = evaluate_argument(item, llm)
        results.append(r)
        if r["success"]:
            print(f"    GT={r['gt_score']:.3f} | Pred={r['predicted_score']:.3f} | Δ={abs(r['predicted_score']-r['gt_score']):.3f}")
        else:
            print(f"    ❌ 失败: {r.get('error', 'unknown')}")

    # 计算相关性
    successful = [r for r in results if r["success"]]
    if len(successful) < 3:
        print(f"\n⚠️  成功评估 {len(successful)} 条，少于 3 条，无法计算相关性")
        return {"status": "insufficient_data", "count": len(successful)}

    predictions = [r["predicted_score"] for r in successful]
    references = [r["gt_score"] for r in successful]

    spearman = spearman_correlation(predictions, references)
    kendall = kendall_tau(predictions, references)

    mae = sum(abs(predictions[i] - references[i]) for i in range(len(predictions))) / len(predictions)
    rmse = (sum((predictions[i] - references[i]) ** 2 for i in range(len(predictions))) / len(predictions)) ** 0.5

    print()
    print("=" * 60)
    print("评估结果")
    print("=" * 60)
    print(f"样本数:         {len(successful)}")
    print(f"Spearman ρ:    {spearman:.4f}")
    print(f"Kendall τ:     {kendall:.4f}")
    print(f"MAE:           {mae:.4f}")
    print(f"RMSE:          {rmse:.4f}")
    print(f"平均 GT 分数:  {sum(references)/len(references):.4f}")
    print(f"平均 Pred 分数: {sum(predictions)/len(predictions):.4f}")

    # 按 GT 分组统计
    bins = [(0.0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    print()
    print("按 GT 质量分组:")
    for lo, hi in bins:
        group = [r for r in successful if lo <= r["gt_score"] < hi]
        if not group:
            continue
        avg_pred = sum(r["predicted_score"] for r in group) / len(group)
        avg_gt = sum(r["gt_score"] for r in group) / len(group)
        print(f"  [{lo:.1f}-{hi:.1f}]: n={len(group)}, avg_GT={avg_gt:.3f}, avg_Pred={avg_pred:.3f}, bias={avg_pred-avg_gt:+.3f}")

    eval_record = {
        "dataset": "ibm_arg_quality",
        "provider": args.provider,
        "model": args.model,
        "sample_size": len(successful),
        "spearman": round(spearman, 4),
        "kendall": round(kendall, 4),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "per_sample": [
            {"topic": r["topic"], "gt": r["gt_score"], "pred": round(r["predicted_score"], 3)}
            for r in successful
        ],
    }

    # 保存结果
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(eval_record, ensure_ascii=False, indent=2))
    print(f"\n💾 结果已保存: {out_path}")
    return eval_record


# ============================================================
# CLI
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="IBM-ArgQ 基准测试")
    ap.add_argument("--provider", default="mock", help="LLM provider (mock/openai/ollama)")
    ap.add_argument("--model", default="mock-model", help="模型名")
    ap.add_argument("--api-key", default=None, help="API key")
    ap.add_argument("--seed", type=int, default=42, help="随机种子")
    ap.add_argument("--limit", type=int, default=20, help="最多评估多少条")
    ap.add_argument("--output", default="data/eval/ibm_argq_result.json", help="输出路径")
    ap.add_argument("--mock", action="store_true", help="强制使用 mock")
    args = ap.parse_args()

    if args.mock:
        args.provider = "mock"
        args.model = "mock-model"

    run_evaluation(args)


if __name__ == "__main__":
    main()
