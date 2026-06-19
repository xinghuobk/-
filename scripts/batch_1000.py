# -*- coding: utf-8 -*-
"""1000 轮压力测试（安静模式）。

使用：
    python scripts/batch_1000.py              # 默认 1000 轮，mock 模式
    python scripts/batch_1000.py --rounds 500 # 自定义轮数
    python scripts/batch_1000.py --provider ollama --model qwen2.5:7b  # 真实 LLM

产物位置：
    .parajudge/iterations/FINAL-REPORT.json  # 完整汇总
    .parajudge/iterations/batch-NNN.json     # 每 100 轮批次报告
"""
from __future__ import annotations

import argparse
import io
import json
import os
import resource
import shutil
import sys
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.autodriver_agents import LLMConfig, LLMHelper, Reflector, CreativePlanner
from scripts.iteration import IterSession, ExperimentTracker, IssueTracker


def run_quiet_experiment(problem: str, version: str, llm_cfg: LLMConfig) -> dict:
    """跑一次实验，但把所有 print 输出吞掉，只返回关键指标。"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        session = IterSession(problem=problem, version=version)
        record = session.run_experiment(config_overrides={"provider": llm_cfg.provider,
                                                           "model": llm_cfg.model},
                                        notes=f"stress:{version}")
        return {"run_id": record.run_id, "problem": record.problem,
                "metrics": record.metrics, "ok": True}
    except Exception as e:
        return {"ok": False, "error": repr(e)}
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=1000)
    p.add_argument("--provider", type=str, default="mock",
                   choices=["mock", "ollama", "openai", "dashscope"])
    p.add_argument("--model", type=str, default="mock-model")
    p.add_argument("--batch", type=int, default=100, help="每多少轮输出一次进度")
    p.add_argument("--search", action="store_true", help="开启外部检索（仅 provider!=mock 时有用）")
    p.add_argument("--no-clean", action="store_true", help="不清理历史产物")
    args = p.parse_args()

    TOTAL_ROUNDS = args.rounds
    BATCH_SIZE = args.batch

    # 清理历史（可选）
    if not args.no_clean:
        for p in ['.parajudge/iterations', '.parajudge/llm_cache']:
            if os.path.isdir(p): shutil.rmtree(p)
        for f in ['.parajudge/latest.json', '.parajudge/issues.json',
                  '.parajudge/experiments.json', '.parajudge/versions.json']:
            if os.path.isfile(f): os.remove(f)
    os.makedirs('.parajudge/iterations', exist_ok=True)

    # 初始化
    llm_cfg = LLMConfig(provider=args.provider, model=args.model)
    llm = LLMHelper(cfg=llm_cfg)
    reflector = Reflector(llm=llm)
    planner = CreativePlanner(llm=llm)
    exp_tracker = ExperimentTracker()

    problems = ["AI 是否会导致大规模失业？", "城市是否应禁止燃油车？", "远程办公是否应成为主流？"]

    t0_total = time.time()
    round_times = []
    batch_results = []
    winner_dist = {}
    score_sum_pro = 0.0
    score_sum_con = 0.0
    failed = 0

    # 静默模式下不打印到终端，把进度直接写文件
    progress_file = ".parajudge/iterations/PROGRESS.log"
    with open(progress_file, "w", buffering=1) as pf:
        pf.write(f"# ParaJudge AutoDriver · {TOTAL_ROUNDS} 轮压力测试\n")
        pf.write(f"# provider={args.provider}, model={args.model}, batch={BATCH_SIZE}\n")
        pf.write(f"# started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        pf.write("# round | ms/round | disk_KB | mem_MB | winner | pro | con\n")

        # 启动 banner
        banner = ("=" * 70 + "\n"
                  f"  ParaJudge AutoDriver · {TOTAL_ROUNDS} 轮压力测试\n"
                  f"  provider={args.provider}, model={args.model}\n"
                  f"  开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                  + "=" * 70 + "\n")
        print(banner)

        for i in range(1, TOTAL_ROUNDS + 1):
            t0 = time.time()

            # ---- 1-2. 评估 & 反思（mock 模式下是确定性 JSON）----
            try:
                reflection = reflector.reflect(
                    snapshot_dict={"version": f"stress-v{i:04d}",
                                   "experiment_count": i},
                    experiments=[], previous_report="")
            except Exception:
                reflection = {"summary": "reflect_error", "code_patches": []}

            # ---- 3-4. 规划（mock 模式下结果固定，检索跳过）----
            try:
                plan = planner.plan(
                    reflection=reflection,
                    snapshot_dict={"version": f"stress-v{i:04d}"},
                    default_cfg={"rounds": 3, "provider": args.provider},
                )
            except Exception:
                plan = type('_DummyPlan', (), {
                    "experiments": [{"key": f"exp-{i}", "title": "fallback",
                                      "config_overrides": {}}],
                    "search_queries": [], "rationales": []
                })()

            # ---- 5. 执行实验（安静模式：吞掉 print）----
            result = run_quiet_experiment(problems[i % len(problems)],
                                          f"stress-v{i:04d}", llm_cfg)
            winner = result["metrics"].get("winner", "?") if result["ok"] else "FAILED"
            pro_score = result["metrics"].get("pro_score", 0.0) if result["ok"] else 0.0
            con_score = result["metrics"].get("con_score", 0.0) if result["ok"] else 0.0

            # 记录实验（用 ExperimentTracker，方便后续分析）
            if result["ok"]:
                try:
                    exp_tracker.log(run_id=result["run_id"], problem=result["problem"],
                                    config={"round": i, "provider": args.provider},
                                    metrics=result["metrics"],
                                    notes=f"stress-v{i:04d}")
                except Exception:
                    pass
            else:
                failed += 1

            # 统计
            elapsed = time.time() - t0
            round_times.append(elapsed)
            winner_dist[winner] = winner_dist.get(winner, 0) + 1
            score_sum_pro += pro_score
            score_sum_con += con_score

            # ---- 进度报告：每 BATCH_SIZE 轮打印一次 ----
            if i == 1 or i % BATCH_SIZE == 0 or i == TOTAL_ROUNDS:
                batch_times = round_times[-(BATCH_SIZE if i > BATCH_SIZE else i):]
                avg = sum(batch_times) / len(batch_times)
                total_so_far = time.time() - t0_total
                disk_bytes = 0
                file_count = 0
                for root, dirs, files in os.walk('.parajudge'):
                    for f in files:
                        file_count += 1
                        try: disk_bytes += os.path.getsize(os.path.join(root, f))
                        except: pass
                mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

                # 当前批次胜负分布
                batch_winners = {}
                recent = exp_tracker.experiments[-len(batch_times):] if hasattr(exp_tracker, 'experiments') else []
                for e in recent:
                    w = e.metrics.get("winner", "?")
                    batch_winners[w] = batch_winners.get(w, 0) + 1

                # 写批次 JSON
                batch_json = {
                    "batch": i // BATCH_SIZE + (1 if i % BATCH_SIZE != 0 else 0),
                    "round_start": i - len(batch_times) + 1,
                    "round_end": i,
                    "avg_time_ms": round(avg * 1000, 1),
                    "total_time_sec": round(total_so_far, 1),
                    "disk_kb": round(disk_bytes / 1024, 1),
                    "memory_mb": round(mem_mb, 1),
                    "winner_distribution": batch_winners,
                    "total_experiments_logged": len(getattr(exp_tracker, 'experiments', [])),
                    "failed_rounds": failed,
                }
                batch_path = f'.parajudge/iterations/batch-{i:04d}.json'
                with open(batch_path, 'w') as bf:
                    json.dump(batch_json, bf, ensure_ascii=False, indent=2)

                # 写进度日志 & 打印进度条
                pct = i / TOTAL_ROUNDS * 100
                eta = (TOTAL_ROUNDS - i) * avg if avg > 0 else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                line = (f"  [{bar}] {i:4d}/{TOTAL_ROUNDS} ({pct:5.1f}%) | "
                        f"{avg*1000:.0f} ms/轮 | "
                        f"磁盘 {disk_bytes/1024:.0f} KB | "
                        f"内存 {mem_mb:.0f} MB | "
                        f"ETA {eta/60:.1f} min | "
                        f"胜: {batch_winners}")
                pf.write(line + "\n")
                print(line, flush=True)

    # 最终报告
    total_time = time.time() - t0_total
    disk_bytes = 0
    file_count = 0
    for root, dirs, files in os.walk('.parajudge'):
        for f in files:
            file_count += 1
            try: disk_bytes += os.path.getsize(os.path.join(root, f))
            except: pass

    n = max(1, TOTAL_ROUNDS - failed)
    final_report = {
        "total_rounds": TOTAL_ROUNDS,
        "failed_rounds": failed,
        "successful_rounds": TOTAL_ROUNDS - failed,
        "total_time_sec": round(total_time, 1),
        "total_time_min": round(total_time / 60, 2),
        "avg_time_per_round_ms": round(total_time / n * 1000, 1),
        "min_round_ms": round(min(round_times) * 1000, 1),
        "max_round_ms": round(max(round_times) * 1000, 1),
        "disk_usage_kb": round(disk_bytes / 1024, 1),
        "disk_usage_mb": round(disk_bytes / 1024 / 1024, 3),
        "total_files": file_count,
        "provider": args.provider,
        "model": args.model,
        "winner_distribution_total": winner_dist,
        "avg_pro_score": round(score_sum_pro / n, 2),
        "avg_con_score": round(score_sum_con / n, 2),
        "batches": batch_results,
        "finished_at": time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    final_path = '.parajudge/iterations/FINAL-REPORT-1000.json'
    with open(final_path, 'w') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    summary = ("\n" + "=" * 70 + "\n"
               f"  ✅ {TOTAL_ROUNDS} 轮完成！\n" + "=" * 70 + "\n"
               f"  总耗时:     {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)\n"
               f"  平均耗时:   {total_time/n*1000:.1f} ms/轮\n"
               f"  最快/最慢:  {min(round_times)*1000:.0f} / {max(round_times)*1000:.0f} ms\n"
               f"  磁盘占用:   {disk_bytes/1024:.1f} KB ({disk_bytes/1024/1024:.3f} MB)\n"
               f"  文件数量:   {file_count} 个\n"
               f"  失败轮数:   {failed}\n"
               f"  胜负分布:   {winner_dist}\n"
               f"  平均正方分: {final_report['avg_pro_score']}\n"
               f"  平均反方分: {final_report['avg_con_score']}\n"
               f"  报告位置:   {final_path}\n"
               + "=" * 70 + "\n")
    print(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
