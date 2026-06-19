"""Step 3 · 真实 LLM 端到端实验。

**不编造**：所有 LLM 调用真实发生，结果真实记录。
**预算控制**：超过 --budget 阈值时自动停止（OpenAI 太贵时保护）。

用法：
    python scripts/run_real_llm_e2e.py --provider ollama --model qwen2.5:7b --questions 5
    python scripts/run_real_llm_e2e.py --provider openai --model gpt-4o-mini --questions 24
    python scripts/run_real_llm_e2e.py --provider ollama --questions 24 --budget 100000  # 100k tokens

输出：experiments/v0.3_real_external/llm_e2e_<model>_<timestamp>.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# 保证 src 可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

EXP_DIR = Path("experiments/v0.3_real_external")
EXP_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 24 题自构测试集（沙箱内已有的，可与 v0.1 batch 实验对齐）
# ============================================================

QUESTIONS: List[Dict[str, Any]] = [
    {"id": 1, "category": "技术预测", "question": "2030 年前，AGI 是否会实现？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 2, "category": "技术预测", "question": "量子计算机会在 10 年内取代经典计算机吗？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 3, "category": "AI 影响", "question": "AI 工具能否提高学生批判性思维能力？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 4, "category": "AI 影响", "question": "自动驾驶是否会比人类驾驶更安全？",
     "expected_winner": None, "difficulty": "easy"},
    {"id": 5, "category": "技术深度", "question": "Transformer 是否是通用 AI 的终极架构？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 6, "category": "技术深度", "question": "强化学习是否仍是通向 AGI 的最佳路径？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 7, "category": "伦理社会", "question": "AI 生成内容是否应该被强制标注？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 8, "category": "伦理社会", "question": "AI 是否应该拥有法律人格？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 9, "category": "本地模型", "question": "本地大语言模型能否完全替代云端 API？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 10, "category": "本地模型", "question": "开源 LLM 是否会最终超越闭源 LLM？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 11, "category": "技术预测", "question": "AGI 是否需要具身智能（embodied AI）？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 12, "category": "AI 影响", "question": "AI 辅助诊断是否会取代放射科医生？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 13, "category": "技术深度", "question": "多模态学习是否是 AGI 的必要条件？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 14, "category": "伦理社会", "question": "AI 武器是否应该被国际公约禁止？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 15, "category": "本地模型", "question": "个人电脑能否在 5 年内本地运行 100B 参数模型？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 16, "category": "技术预测", "question": "Web3 与 AI 结合是否会产生新范式？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 17, "category": "AI 影响", "question": "AI 是否会加剧就业不平等？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 18, "category": "技术深度", "question": "神经符号 AI 是否会复兴？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 19, "category": "伦理社会", "question": "数据隐私与 AI 进步如何平衡？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 20, "category": "本地模型", "question": "Ollama 等本地 LLM 工具是否代表了未来？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 21, "category": "技术预测", "question": "AI 训练数据枯竭是真实的瓶颈吗？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 22, "category": "AI 影响", "question": "AI 是否会取代程序员？",
     "expected_winner": None, "difficulty": "medium"},
    {"id": 23, "category": "技术深度", "question": "Mixture-of-Experts 是否优于 dense model？",
     "expected_winner": None, "difficulty": "hard"},
    {"id": 24, "category": "伦理社会", "question": "AI 是否应被赋予创作署名权？",
     "expected_winner": None, "difficulty": "medium"},
]


# ============================================================
# 真实 LLM 调用
# ============================================================

def make_llm_client(provider: str, model: str):
    """构造 LLM 客户端。**真实调用，失败抛异常**。"""
    from src.writer.llm_client import LLMClient
    api_key = None
    base_url = None
    if provider == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 未设置")
        base_url = os.environ.get("OPENAI_BASE_URL", None)
    return LLMClient(provider=provider, model=model, api_key=api_key, base_url=base_url)


def run_single(question: Dict[str, Any], provider: str, model: str,
               enable_moderator: bool = True, enable_t1: bool = True,
               enable_t3: bool = True, enable_t4: bool = True,
               rounds: int = 2, max_evidence: int = 5) -> Dict[str, Any]:
    """真实跑 1 题完整 ParaJudge 流程。"""
    from src.orchestration.orchestrator import run_parajudge

    t0 = time.perf_counter()
    rec: Dict[str, Any] = {
        "question_id": question["id"],
        "category": question["category"],
        "question": question["question"],
        "model": model,
        "provider": provider,
        "rounds": rounds,
        "max_evidence": max_evidence,
        "config": {
            "enable_moderator": enable_moderator,
            "enable_t1_aebg": enable_t1,
            "enable_t3_ks": enable_t3,
            "enable_t4_ds": enable_t4,
        },
        "status": "PENDING",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        out = run_parajudge(
            problem=question["question"],
            provider=provider,
            model=model,
            rounds=rounds,
            max_evidence=max_evidence,
            enable_moderator=enable_moderator,
            enable_t1_aebg=enable_t1,
            enable_t3_ks=enable_t3,
            enable_t4_ds=enable_t4,
        )
        rec["run_id"] = out.run_id
        rec["winner"] = out.judgment.winner
        rec["pro_score"] = out.judgment.pro_final_score
        rec["con_score"] = out.judgment.con_final_score
        rec["n_arguments"] = len(out.transcript.arguments)
        rec["n_judges"] = len(out.judgment.judge_scores)
        rec["total_time_sec"] = out.total_time_sec
        rec["moderator_report"] = out.transcript.moderator_report
        rec["judgment_uncertainties"] = out.judgment.uncertainties
        # T4 双路融合结果
        if hasattr(out.judgment, "_t4_heuristic") and out.judgment._t4_heuristic:
            rec["t4_heuristic"] = out.judgment._t4_heuristic
        if hasattr(out.judgment, "_t4_ds_approx") and out.judgment._t4_ds_approx:
            rec["t4_ds_approx"] = out.judgment._t4_ds_approx
        rec["status"] = "OK"
    except Exception as e:
        rec["status"] = "ERROR"
        rec["error"] = str(e)
        rec["traceback"] = traceback.format_exc()

    rec["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec["wall_time_sec"] = round(time.perf_counter() - t0, 2)
    return rec


# ============================================================
# 主流程
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="真实 LLM 端到端")
    ap.add_argument("--provider", required=True, choices=["mock", "ollama", "openai", "dashscope"])
    ap.add_argument("--model", default=None, help="模型名（不传则用 provider 默认）")
    ap.add_argument("--questions", type=int, default=24, help="跑前 N 题（最多 24）")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--max-evidence", type=int, default=5)
    ap.add_argument("--no-moderator", action="store_true")
    ap.add_argument("--no-t1", action="store_true")
    ap.add_argument("--no-t3", action="store_true")
    ap.add_argument("--no-t4", action="store_true")
    ap.add_argument("--budget", type=int, default=10_000_000, help="token 预算")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    # 选默认模型
    default_models = {
        "ollama": "qwen2.5:7b",
        "openai": "gpt-4o-mini",
        "dashscope": "qwen-plus",
        "mock": "mock-model",
    }
    model = args.model or default_models[args.provider]

    print("=" * 60)
    print(f"ParaJudge 真实 LLM 端到端")
    print(f"Provider: {args.provider} | Model: {model}")
    print(f"Questions: {args.questions} | Rounds: {args.rounds}")
    print(f"Moderator: {not args.no_moderator} | T1: {not args.no_t1} | T3: {not args.no_t3} | T4: {not args.no_t4}")
    print("=" * 60)

    # 真实构造 LLM 客户端（失败立即报错）
    try:
        make_llm_client(args.provider, model)
        print(f"✅ LLM 客户端构造成功：{args.provider}/{model}")
    except Exception as e:
        print(f"❌ LLM 客户端构造失败: {e}")
        print(f"   请检查：")
        if args.provider == "ollama":
            print(f"   - ollama serve 是否在 {os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')} 运行？")
            print(f"   - ollama pull {model} 是否已下载？")
        elif args.provider == "openai":
            print(f"   - OPENAI_API_KEY 是否已 export？")
        sys.exit(1)
    print()

    # 准备输出文件
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    out_path = Path(args.output) if args.output else EXP_DIR / f"llm_e2e_{args.provider}_{model.replace(':', '-').replace('.', '-')}_{ts}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = min(args.questions, len(QUESTIONS))
    selected = QUESTIONS[:n]
    print(f"将跑 {n} 题：")
    for q in selected[:5]:
        print(f"  - [{q['id']:02d}] ({q['category']}) {q['question'][:50]}...")
    if n > 5:
        print(f"  ... 及其他 {n - 5} 题")
    print()

    total_tokens = 0
    with out_path.open("w", encoding="utf-8") as f:
        for i, q in enumerate(selected, start=1):
            if total_tokens >= args.budget:
                print(f"⚠️ 已达 token 预算 {args.budget}，停止")
                break
            print(f"[{i}/{n}] q={q['id']:02d} | {q['question'][:50]}...")
            rec = run_single(
                q, args.provider, model,
                enable_moderator=not args.no_moderator,
                enable_t1=not args.no_t1,
                enable_t3=not args.no_t3,
                enable_t4=not args.no_t4,
                rounds=args.rounds, max_evidence=args.max_evidence,
            )
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            icon = "✅" if rec["status"] == "OK" else "❌"
            if rec["status"] == "OK":
                print(f"  {icon} winner={rec.get('winner')} pro={rec.get('pro_score'):.1f} con={rec.get('con_score'):.1f} | {rec.get('wall_time_sec')}s")
            else:
                print(f"  {icon} ERROR: {rec.get('error', '')[:100]}")
            print()

    print("=" * 60)
    print(f"完成。结果：{out_path}")
    print(f"共 {n} 题，{sum(1 for _ in out_path.open())} 行 JSONL")
    print("=" * 60)


if __name__ == "__main__":
    main()
