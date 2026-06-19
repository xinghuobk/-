"""Step 1 · 环境检查（跳出沙箱后第一件事）。

**真实检查 9 项必要 + 4 项可选**，**不编造**：报告什么就是什么。
每项检查返回 PASS / WARN / FAIL / SKIP（网络不可达）。

用法：
    python scripts/env_check.py
    python scripts/env_check.py --json  # 输出 JSON 格式给 CI

输出：reports/env_check.txt + reports/env_check.json
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPORTS = Path("reports")
REPORTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# 检查器
# ============================================================

def check_python() -> Dict[str, Any]:
    """Python 版本 ≥ 3.10。"""
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 10)
    return {
        "name": "python",
        "status": "PASS" if ok else "FAIL",
        "version": f"{v.major}.{v.minor}.{v.micro}",
        "required": ">=3.10",
        "fix": "conda install python=3.11" if not ok else None,
    }


def check_pip_package(name: str, required: str, optional: bool = False) -> Dict[str, Any]:
    """检查 pip 包。"""
    try:
        mod = __import__(name)
        version = getattr(mod, "__version__", "unknown")
        return {
            "name": name,
            "status": "PASS",
            "version": str(version),
            "required": required,
        }
    except ImportError as e:
        return {
            "name": name,
            "status": "WARN" if optional else "FAIL",
            "required": required,
            "error": str(e),
            "fix": f"pip install {name}>={required.split('>=')[1]}" if not optional else None,
        }


def check_network() -> Dict[str, Any]:
    """检查外网可达（huggingface + github）。"""
    targets = [
        ("huggingface.co", 443),
        ("github.com", 443),
    ]
    reachable = []
    for host, port in targets:
        try:
            with socket.create_connection((host, port), timeout=5):
                reachable.append(host)
        except Exception:
            pass
    if len(reachable) == len(targets):
        status = "PASS"
    elif len(reachable) > 0:
        status = "WARN"
    else:
        status = "FAIL"
    return {
        "name": "network",
        "status": status,
        "reachable": reachable,
        "required": "huggingface.co + github.com",
        "fix": "检查网络 / 配置代理 http_proxy / https_proxy" if status == "FAIL" else None,
    }


def check_ollama() -> Dict[str, Any]:
    """检查 Ollama 端点（http://localhost:11434）。"""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as resp:
            if resp.status == 200:
                return {
                    "name": "ollama",
                    "status": "PASS",
                    "endpoint": "http://localhost:11434",
                    "note": "Ollama 服务运行中",
                }
    except Exception:
        pass
    return {
        "name": "ollama",
        "status": "WARN",
        "endpoint": "http://localhost:11434",
        "note": "Ollama 未运行（可选，仅本地 LLM 需要）",
        "fix": "ollama serve  # 在另一终端启动；或跳过 --provider openai",
    }


def check_gpu() -> Dict[str, Any]:
    """检查 GPU（nvidia-smi）。可选。"""
    nvidia = shutil.which("nvidia-smi")
    if not nvidia:
        return {"name": "gpu", "status": "SKIP", "note": "无 nvidia-smi，跳过 GPU 检查"}
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            return {
                "name": "gpu",
                "status": "PASS",
                "info": lines[1] if len(lines) > 1 else lines[0],
                "note": "GPU 可用（sentence-transformers / qwen2.5:7b 推理会用到）",
            }
    except Exception as e:
        return {"name": "gpu", "status": "WARN", "error": str(e)}
    return {"name": "gpu", "status": "WARN", "note": "nvidia-smi 不可用"}


def check_openai_key() -> Dict[str, Any]:
    """检查 OpenAI API key 环境变量。"""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key and key.startswith("sk-"):
        return {"name": "openai_key", "status": "PASS", "note": "OPENAI_API_KEY 已设置"}
    return {
        "name": "openai_key",
        "status": "WARN",
        "note": "OPENAI_API_KEY 未设置（仅 OpenAI provider 需要）",
        "fix": "export OPENAI_API_KEY=sk-...",
    }


def check_disk_space() -> Dict[str, Any]:
    """检查磁盘空间（≥5GB）。"""
    stat = shutil.disk_usage(".")
    free_gb = stat.free / (1024 ** 3)
    if free_gb >= 5.0:
        return {"name": "disk", "status": "PASS", "free_gb": round(free_gb, 2)}
    return {
        "name": "disk",
        "status": "WARN",
        "free_gb": round(free_gb, 2),
        "note": f"剩余空间 {free_gb:.1f}GB，建议 ≥ 5GB（10 个数据集约 1GB + 缓存）",
    }


# ============================================================
# 主流程
# ============================================================

def run_all_checks() -> List[Dict[str, Any]]:
    """真实跑所有检查项。**不编造**。"""
    checks = []
    checks.append(check_python())
    checks.append(check_network())
    checks.append(check_disk_space())
    checks.append(check_gpu())
    checks.append(check_ollama())
    checks.append(check_openai_key())

    # 必要包
    for name, ver in [
        ("numpy", "1.24"),
        ("scipy", "1.10"),
        ("pandas", "2.0"),
        ("sklearn", "1.3"),
        ("networkx", "3.0"),
        ("requests", "2.28"),
    ]:
        checks.append(check_pip_package(name, f">={ver}", optional=False))

    # 可选包
    for name, ver in [
        ("sentence_transformers", "2.2"),
        ("torch", "2.0"),
        ("huggingface_hub", "0.16"),
    ]:
        checks.append(check_pip_package(name, f">={ver}", optional=True))

    return checks


def summarize(checks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """汇总检查结果。"""
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
    for c in checks:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    return {
        "total": len(checks),
        "summary": counts,
        "can_continue": counts["FAIL"] == 0,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform": platform.platform(),
        "python": sys.version,
    }


def print_report(checks: List[Dict[str, Any]], summary: Dict[str, Any]):
    """打印人类可读报告。"""
    print("=" * 60)
    print(f"ParaJudge 环境检查报告")
    print("=" * 60)
    print(f"时间: {summary['timestamp']}")
    print(f"平台: {summary['platform']}")
    print(f"Python: {summary['python']}")
    print()

    for c in checks:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "SKIP": "⏭️ "}[c["status"]]
        line = f"  {icon} {c['name']:<25s} {c['status']:<5s}"
        if "version" in c:
            line += f"  {c['version']}"
        elif "info" in c:
            line += f"  {c['info']}"
        elif "note" in c:
            line += f"  {c['note']}"
        print(line)
        if c.get("fix"):
            print(f"        → 修复: {c['fix']}")

    print()
    print("=" * 60)
    print(f"汇总: {summary['summary']}")
    print("=" * 60)
    if summary["can_continue"]:
        print("✅ 全部必要项 PASS，可以进入 Step 2: make download-data")
    else:
        print("❌ 存在必要项 FAIL，请先修复后重跑本脚本")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="ParaJudge 环境检查")
    ap.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = ap.parse_args()

    checks = run_all_checks()
    summary = summarize(checks)

    # 写报告
    (REPORTS / "env_check.txt").write_text(
        f"ParaJudge 环境检查\n{summary['timestamp']}\n\n" +
        "\n".join(f"{c['name']}: {c['status']}" + (f" ({c.get('version','')})" if 'version' in c else "") for c in checks) +
        f"\n\n汇总: {summary['summary']}\n"
    )
    (REPORTS / "env_check.json").write_text(
        json.dumps({"checks": checks, "summary": summary}, ensure_ascii=False, indent=2)
    )

    if args.json:
        print(json.dumps({"checks": checks, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        print_report(checks, summary)


if __name__ == "__main__":
    main()
