# -*- coding: utf-8 -*-
"""ParaJudge AutoDriver · 自主研发 agent 模块（七步循环扩展）。

新架构（相对原版的四步循环扩展为七步）：
    ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌──────────┐
    │  Assess  │ → │ Reflect  │ → │   Search   │ → │ Creative │
    │  评估系统│   │  自我反思│   │  外部检索  │   │  Planner  │
    └──────────┘   └──────────┘   └────────────┘   └────┬─────┘
                                                         ↓
    ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌──────────┐
    │  Record  │ ← │CodeEditor│ ← │  Execute   │ ← │  (cont)  │
    │  Δ报告  │   │  生成&应用│   │  运行实验  │   │          │
    └──────────┘   └──────────┘   └────────────┘   └──────────┘

模块入口通过 scripts.autodriver.main() 驱动。
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# try: 可选依赖
try:
    from src.writer.llm_client import LLMClient as _ProjectLLMClient  # type: ignore
    _HAS_PROJECT_LLM = True
except Exception:
    _HAS_PROJECT_LLM = False

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False


# ========================================================================
# 1. LLMHelper — 统一 LLM 调用入口（真实 LLM / mock 回退 + 结果缓存）
# ========================================================================


@dataclass
class LLMConfig:
    provider: str = "mock"              # mock | ollama | openai | dashscope
    model: str = "mock-model"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    timeout: float = 120.0
    use_cache: bool = True

    def available(self) -> bool:
        if self.provider == "mock":
            return True
        return _HAS_REQUESTS and self.provider in ("ollama", "openai", "dashscope")


class LLMHelper:
    """统一 LLM 客户端。provider=mock 或网络异常时自动回退到确定性 mock。"""

    CACHE_DIR = os.path.join(PROJECT_ROOT, ".parajudge", "llm_cache")

    def __init__(self, cfg: Optional[LLMConfig] = None):
        self.cfg = cfg or LLMConfig()
        self._client = None
        if self.cfg.provider != "mock" and _HAS_PROJECT_LLM:
            try:
                self._client = _ProjectLLMClient(
                    provider=self.cfg.provider,
                    model=self.cfg.model,
                    api_key=self.cfg.api_key,
                    base_url=self.cfg.base_url,
                    timeout=self.cfg.timeout,
                )
            except Exception:
                self._client = None
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    # ── public ─────────────────────────────────────────────────
    def ask(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        key = self._cache_key(prompt, system)
        cached = self._read_cache(key)
        if cached is not None and self.cfg.use_cache:
            return cached
        text = None
        if self.cfg.provider != "mock" and self._client is not None:
            try:
                text = self._real_call(prompt, system, max_tokens)
            except Exception as e:
                print(f"    [LLM] 真实调用失败({self.cfg.provider}/{self.cfg.model}): {e}；回退到 mock")
        if text is None:
            text = self._mock_call(prompt, system)
        if self.cfg.use_cache:
            self._write_cache(key, text)
        return text

    def ask_json(self, prompt: str, system: str = "", max_tokens: int = 2048) -> Dict[str, Any]:
        extra = (system + "\n\n" if system else "") + (
            "你必须严格返回合法 JSON 对象，不要包含任何解释文字。"
            "可以用 ```json ... ``` 包裹，也可以裸 JSON。"
        )
        raw = self.ask(prompt, extra, max_tokens)
        data = _extract_json(raw)
        return data if data is not None else self._mock_json(prompt)

    # ── private: real LLM paths ──────────────────────────────────
    def _real_call(self, prompt: str, system: str, max_tokens: int) -> str:
        if self.cfg.provider == "ollama":
            return self._ollama_call(prompt, system, max_tokens)
        if self.cfg.provider in ("openai", "dashscope"):
            return self._openai_like_call(prompt, system, max_tokens)
        raise RuntimeError(f"不支持的 provider: {self.cfg.provider}")

    def _ollama_call(self, prompt: str, system: str, max_tokens: int) -> str:
        url = self.cfg.base_url or "http://localhost:11434/api/generate"
        payload = {
            "model": self.cfg.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"temperature": self.cfg.temperature, "num_predict": max_tokens},
        }
        r = requests.post(url, json=payload, timeout=self.cfg.timeout)
        r.raise_for_status()
        return r.json().get("response", "")

    def _openai_like_call(self, prompt: str, system: str, max_tokens: int) -> str:
        default_base = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        }.get(self.cfg.provider, "")
        base = self.cfg.base_url or default_base
        if not base:
            raise RuntimeError(f"未知 provider: {self.cfg.provider}")
        headers = {"Authorization": f"Bearer {self.cfg.api_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.cfg.model, "messages": messages,
            "temperature": self.cfg.temperature, "max_tokens": max_tokens,
        }
        r = requests.post(base, headers=headers, json=payload, timeout=self.cfg.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    # ── private: deterministic mock fallback ─────────────────
    def _mock_call(self, prompt: str, system: str) -> str:
        seed = _hash_int(prompt + "|" + system)
        rnd = random.Random(seed)
        pl = prompt.lower()
        if "反思" in prompt or "reflect" in pl:
            return (
                "上一轮实验平局率偏高（3/3 tie），judge 一致性不足。"
                "建议：①给 judge panel 增加 diversity prompt；"
                "②降低 DS 正交和近似的冲突阈值；"
                "③反驳覆盖率阈值改为可调参数。"
            )
        if "实验" in prompt or "experiment" in pl:
            return (
                "建议设计 3 个实验：\n"
                "1) belief_alignment_sweep — 不同 judge prompt 下的胜负偏差；\n"
                "2) temperature_sweep — temperature 0.0~1.2；\n"
                "3) multi_round_stats — 5 次重复同一问题看统计显著性。"
            )
        if "patch" in pl or "代码" in prompt or "修改" in prompt:
            return (
                "建议修改：\n"
                "- judgment_engine.py: 给 judge 增加 diversity prompt 标记；\n"
                "- moderator.py: 用语义相似度替代关键词重叠；\n"
                "- iteration.py: 增加 Holm-Bonferroni 多重比较校正。"
            )
        bits = rnd.choice([
            "继续深挖『辩论胜负≠真理』核心问题。",
            "引入更多元的 judge 多样性，避免共识偏差。",
            "下一个迭代尝试语义相似度替代关键词重叠。",
        ])
        return f"[mock-llm] {bits}\n[seed={seed}]"

    def _mock_json(self, prompt: str) -> Dict[str, Any]:
        seed = _hash_int(prompt)
        rnd = random.Random(seed)
        _ = rnd.random()  # 消耗一次随机，保证不同 prompt 不同序列
        return {
            "summary": "mock 反思：上一轮实验平局偏多，建议增加 judge 多样性",
            "strengths": ["端到端可跑", "有证据链"],
            "weaknesses": ["关键词重叠粗糙", "无多重比较校正", "judge 多样性不足"],
            "priorities": [
                {"id": "judge_diversity", "title": "给 judge panel 增加 diversity prompt",
                 "rationale": "降低共识偏差是最大风险", "effort": "medium"},
                {"id": "semantic_rebuttal", "title": "语义反驳替代关键词重叠",
                 "rationale": "关键词太粗糙", "effort": "large"},
                {"id": "multi_compare_correction", "title": "多重比较校正",
                 "rationale": "统计检验假阳性风险", "effort": "small"},
            ],
            "new_experiments": [
                {"key": "belief_alignment_sweep", "title": "信念对齐扫掠",
                 "config_overrides": {"rounds": 3, "max_evidence": 8},
                 "rationale": "看不同 judge prompt 下胜负分布"},
                {"key": "temperature_sweep", "title": "temperature 参数扫掠",
                 "config_overrides": {"rounds": 3, "max_evidence": 10},
                 "rationale": "看 temperature 对结论稳定性影响"},
            ],
            "code_patches": [
                {"target_file": "src/judgment/judgment_engine.py",
                 "description": "给 judge 增加 diversity prompt 标记"},
                {"target_file": "src/debate/moderator.py",
                 "description": "用语义相似度替代关键词重叠"},
            ],
            "search_queries": [
                "dempster-shafer combination rule debate judgment",
                "argumentation mining rebuttal semantic similarity",
                "multiple comparison correction debate evaluation",
            ],
            "next_iteration_focus": "增加 judge 多样性 + 语义反驳",
        }

    # ── cache helpers ────────────────────────────────────────
    def _cache_key(self, prompt: str, system: str) -> str:
        raw = f"{self.cfg.provider}|{self.cfg.model}|{system[:200]}|{prompt[:500]}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[str]:
        p = os.path.join(self.CACHE_DIR, key + ".txt")
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def _write_cache(self, key: str, text: str) -> None:
        try:
            with open(os.path.join(self.CACHE_DIR, key + ".txt"), "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass


def _hash_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 1_000_000


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    candidate = text.strip()
    # 优先尝试 ```json ... ``` 包裹
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", candidate)
    if not m:
        first = candidate.find("{")
        last = candidate.rfind("}")
        if first >= 0 and last > first:
            candidate = candidate[first:last + 1]
        else:
            return None
    else:
        candidate = m.group(1)
    try:
        return json.loads(candidate)
    except Exception:
        return None


# ========================================================================
# 2. SearchProvider — arxiv / 外部知识检索（无网络时回退到内置摘要）
# ========================================================================


@dataclass
class SearchResult:
    source: str              # "arxiv" | "web (online)" | "web (offline)"
    title: str
    snippet: str
    url: str
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "title": self.title,
                "snippet": self.snippet, "url": self.url, "score": self.score}


class SearchProvider:
    """arxiv API（可选）+ 离线摘要回退。"""

    ARXIV_API = "http://export.arxiv.org/api/query"
    USER_AGENT = "ParaJudgeAutoDriver/1.0 (research agent)"

    def __init__(self, llm: Optional[LLMHelper] = None, enabled: bool = True):
        self.llm = llm
        self.enabled = enabled and _HAS_REQUESTS

    def search(self, queries: List[str], max_per_query: int = 3) -> List[SearchResult]:
        out: List[SearchResult] = []
        if not queries:
            return out
        for q in queries:
            got: List[SearchResult] = []
            if self.enabled:
                try:
                    got = self._arxiv(q, max_per_query)
                except Exception as e:
                    print(f"    [Search] arxiv 查询失败：{e}；回退到离线摘要")
                    got = []
            if not got:
                got = self._offline([q], max_per_query)
            out.extend(got)
        seen = set()
        dedup: List[SearchResult] = []
        for r in out:
            if r.url in seen:
                continue
            seen.add(r.url)
            dedup.append(r)
        return dedup

    # ── internals ───────────────────────────────────────────
    def _arxiv(self, query: str, max_results: int) -> List[SearchResult]:
        params = {"search_query": "all:" + query, "start": 0,
                  "max_results": max_results, "sortBy": "relevance", "sortOrder": "descending"}
        headers = {"User-Agent": self.USER_AGENT}
        r = requests.get(self.ARXIV_API, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        results: List[SearchResult] = []
        entries = re.findall(r"<entry>(.*?)</entry>", r.text, re.DOTALL)
        for e in entries[:max_results]:
            t = re.search(r"<title>(.*?)</title>", e, re.DOTALL)
            s = re.search(r"<summary>(.*?)</summary>", e, re.DOTALL)
            id_ = re.search(r"<id>(.*?)</id>", e, re.DOTALL)
            if not (t and s and id_):
                continue
            title = re.sub(r"\s+", " ", t.group(1)).strip()
            summary = re.sub(r"\s+", " ", s.group(1)).strip()
            url = id_.group(1).strip()
            results.append(SearchResult(source="arxiv", title=title,
                                         snippet=summary[:300], url=url, score=1.0))
        return results

    def _offline(self, queries: List[str], max_per_query: int) -> List[SearchResult]:
        canned: Dict[str, List[tuple]] = {
            "dempster": [
                ("Dempster-Shafer evidence theory 与 Zadeh 悖论",
                 "经典 Dempster 组合规则在高冲突证据下会出现反直觉结论（Zadeh 悖论）。"
                 "ParaJudge 当前用近似正交和应谨慎对待冲突情形。",
                 "https://en.wikipedia.org/wiki/Dempster%27s_rule_of_combination"),
                ("DS theory 用于多源融合",
                 "DS 理论在辩论系统中融合多位 judge 评分时，冲突权重调整非常关键。",
                 "https://www.sciencedirect.com/"),
            ],
            "rebuttal": [
                ("Argumentation mining 中的反驳检测",
                 "现代论点-反驳关系检测一般采用句子嵌入（如 sentence-transformers），"
                 "关键词重叠只是基线方法，通常相关度在 0.3~0.5 之间。",
                 "https://aclanthology.org/"),
                ("Semantic similarity for argumentative text",
                 "all-MiniLM-L6-v2 在论点-反驳匹配上显著优于关键词重叠。",
                 "https://www.sbert.net/"),
            ],
            "multiple": [
                ("Holm-Bonferroni 多重比较校正",
                 "同一问题重复多次统计检验时，需要控制 family-wise error rate。",
                 "https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method"),
                ("Familywise error rate overview",
                 "辩论系统 multi-run setting 下 α 控制是严谨科研的必要条件。",
                 "https://en.wikipedia.org/wiki/Family-wise_error_rate"),
            ],
            "alignment": [
                ("Debate systems & judge bias",
                 "多模型辩论中 judge 共识偏差是已知问题；panel diversity、temperature 扰动、跨模型 ensemble 是常用缓解手段。",
                 "https://arxiv.org/abs/2305.14325"),
                ("LLM alignment via debate",
                 "多轮辩论 + 自博弈 + 模型多样性，是缓解共识偏差的常见技术。",
                 "https://arxiv.org/abs/2402.06796"),
            ],
            "debate": [
                ("AI Debate 综述",
                 "辩论系统常见问题：正反方协作作弊、judge 先验偏差、证据检索范围受限。",
                 "https://en.wikipedia.org/wiki/AI_debate"),
            ],
        }
        out: List[SearchResult] = []
        for q in queries:
            key = q.lower()
            matched: Optional[List[tuple]] = None
            for k, items in canned.items():
                if k in key:
                    matched = items
                    break
            if matched is None:
                matched = canned["debate"]
            for title, snippet, url in matched[:max_per_query]:
                out.append(SearchResult(source="web (offline)", title=title,
                                         snippet=snippet, url=url, score=0.5))
        return out


# ========================================================================
# 3. Reflector — 自我反思（读上一轮结果 → 给出改进建议 JSON）
# ========================================================================


_REFLECTOR_PROMPT = """你是一位批判性科研助理。请阅读以下 ParaJudge 辩论系统上一轮迭代的结果，
并给出具体可操作的改进建议。

【系统快照】
{system_snapshot}

【上一轮实验结果】
{previous_experiments}

【核心科研问题】
1. 辩论胜负是否逼近真理（vs 地心说问题）
2. 反驳机制是否能检测论点不相交
3. 多轮重复的统计显著性（假阳性风险）
4. DS 正交和近似与真正 Dempster 规则差距

请严格按以下 JSON 结构返回（只输出一个 JSON 对象）：
{{
  "summary": "一句话总结上一轮核心发现",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["弱点1", "弱点2"],
  "priorities": [
    {{"id": "str", "title": "str", "rationale": "str", "effort": "small|medium|large"}}
  ],
  "new_experiments": [
    {{"key": "str", "title": "str", "config_overrides": {{"rounds": 3}}, "rationale": "str"}}
  ],
  "code_patches": [
    {{"target_file": "相对路径", "description": "做什么修改", "rationale": "为什么"}}
  ],
  "search_queries": ["检索关键词1", "检索关键词2"],
  "next_iteration_focus": "一句话，50字以内"
}}
"""


class Reflector:
    def __init__(self, llm: LLMHelper):
        self.llm = llm

    def reflect(
        self,
        snapshot_dict: Dict[str, Any],
        experiments: List[Dict[str, Any]],
        previous_report: str = "",
    ) -> Dict[str, Any]:
        snap_text = json.dumps(snapshot_dict, ensure_ascii=False, indent=2)[:2000]
        if experiments:
            exp_lines = []
            for e in experiments:
                metrics = e.get("metrics", {})
                exp_lines.append(
                    f"- {e.get('key', '?')}: winner={metrics.get('winner', '?')} "
                    f"pro={metrics.get('pro_score')} con={metrics.get('con_score')}"
                )
            exp_text = "\n".join(exp_lines)[:1500]
        else:
            exp_text = "(无历史实验)"
        prev = (previous_report or "")[:800]
        prompt = _REFLECTOR_PROMPT.format(
            system_snapshot=snap_text,
            previous_experiments=exp_text + "\n\n[上一轮报告摘要]: " + prev,
        )
        result = self.llm.ask_json(prompt, system="你是一位严谨的科研反思者。")
        defaults = {
            "summary": "mock 反思完成", "strengths": [], "weaknesses": [],
            "priorities": [], "new_experiments": [], "code_patches": [],
            "search_queries": [], "next_iteration_focus": "继续探索",
        }
        for k, v in defaults.items():
            if k not in result or result[k] is None:
                result[k] = v
        return result


# ========================================================================
# 4. CreativePlanner — 由反思结论生成创造性实验设计
# ========================================================================


_PLANNER_PROMPT = """基于以下反思结论，为 ParaJudge 辩论系统设计下一轮迭代的实验计划。

【反思结论】
{reflection_text}

【当前系统快照】
{system_snapshot}

请严格按如下 JSON 结构返回（只输出一个 JSON 对象）：
{{
  "experiments": [
    {{
      "key": "简短英文 key",
      "title": "中文标题",
      "config_overrides": {{"rounds": 3, "max_evidence": 8, "provider": "mock/ollama/openai/dashscope", "model": "模型名"}},
      "rationale": "为什么做这个实验"
    }}
  ],
  "rationales": ["整体设计思路"],
  "search_queries": ["需要外部检索的关键词"]
}}
要求 experiments 至少 2 个、不超过 4 个。
"""


@dataclass
class CreativePlan:
    experiments: List[Dict[str, Any]]
    rationales: List[str]
    search_queries: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"experiments": self.experiments,
                "rationales": self.rationales,
                "search_queries": self.search_queries}


class CreativePlanner:
    def __init__(self, llm: LLMHelper):
        self.llm = llm

    def plan(
        self, reflection: Dict[str, Any], snapshot_dict: Dict[str, Any],
        default_cfg: Dict[str, Any],
    ) -> CreativePlan:
        rtext = json.dumps(reflection, ensure_ascii=False, indent=2)[:2000]
        stext = json.dumps(snapshot_dict, ensure_ascii=False, indent=2)[:1000]
        prompt = _PLANNER_PROMPT.format(reflection_text=rtext, system_snapshot=stext)
        data = self.llm.ask_json(prompt, system="你是一位有创造力的实验设计者。")
        exps = data.get("experiments") or []
        normalized: List[Dict[str, Any]] = []
        for i, e in enumerate(exps):
            if not isinstance(e, dict):
                continue
            cfg = e.get("config_overrides") or {}
            for k, v in (default_cfg or {}).items():
                cfg.setdefault(k, v)
            normalized.append({
                "key": e.get("key") or f"creative_exp_{i+1}",
                "title": e.get("title") or f"创造性实验 {i+1}",
                "config_overrides": cfg,
                "rationale": e.get("rationale") or "",
            })
        if not normalized:
            normalized.append({
                "key": "creative_fallback", "title": "反思驱动实验",
                "config_overrides": dict(default_cfg or {}), "rationale": "fallback",
            })
        return CreativePlan(
            experiments=normalized[:4],
            rationales=data.get("rationales") or [],
            search_queries=data.get("search_queries") or [],
        )


# ========================================================================
# 5. CodeEditor — 生成代码修改提案（默认不落盘；auto_apply=True 时在文件尾部附加改动）
# ========================================================================


@dataclass
class PatchSpec:
    target_file: str
    description: str
    rationale: str = ""
    auto_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"target_file": self.target_file,
                "description": self.description,
                "rationale": self.rationale,
                "auto_applied": self.auto_applied}


_PATCH_HEADER = """# Patch Proposal · {version}

- 目标文件: `{target}`
- 描述: {description}
- 理由: {rationale}

## 变更说明

"""


class CodeEditor:
    """代码修改建议器。

    安全策略（默认）：只写 `.patch.md` 人类可读提案，不改源码。
    危险模式（`auto_apply=True`）：从提案中提取 ```python``` 代码块追加到目标文件尾部（文件会被先复制一份 `.bak`）。
    """

    def __init__(self, llm: Optional[LLMHelper] = None, auto_apply: bool = False):
        self.llm = llm
        self.auto_apply = auto_apply

    def generate_and_maybe_apply(
        self, specs_input: List[Dict[str, Any]], version: str,
        out_dir: str, search_hits: Optional[List[SearchResult]] = None,
    ) -> List[PatchSpec]:
        os.makedirs(out_dir, exist_ok=True)
        results: List[PatchSpec] = []
        hits = search_hits or []
        for i, spec in enumerate(specs_input):
            target = str(spec.get("target_file", ""))
            desc = str(spec.get("description", ""))
            rationale = str(spec.get("rationale", ""))
            full_path = os.path.join(PROJECT_ROOT, target) if target else None
            if not target or not full_path or not os.path.exists(full_path):
                results.append(PatchSpec(
                    target_file=target or f"unknown_{i}",
                    description=desc or "(跳过：目标文件不存在)",
                    rationale=rationale, auto_applied=False))
                continue
            body = self._compose_body(target, desc, rationale, hits, full_path)
            filename = f"patch-{version}-{i+1:02d}-{_safe_name(target)}.md"
            path = os.path.join(out_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(_PATCH_HEADER.format(
                    version=version, target=target,
                    description=desc, rationale=rationale))
                f.write(body)
                f.write("\n\n---\n> 由 scripts.autodriver_agents.CodeEditor 自动生成\n")
            applied = False
            if self.auto_apply:
                applied = self._apply(full_path, body, desc)
            results.append(PatchSpec(
                target_file=target, description=desc,
                rationale=rationale, auto_applied=applied))
        return results

    # ── internals ───────────────────────────────────────────
    def _compose_body(
        self, target: str, description: str, rationale: str,
        hits: List[SearchResult], full_path: str,
    ) -> str:
        if self.llm is not None and self.llm.cfg.provider != "mock":
            prompt = (
                f"请阅读 Python 源码路径 `{target}` 并给出修改建议。\n\n"
                f"目标: {description}\n理由: {rationale}\n"
            )
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    source = f.read()
                prompt += f"\n当前源码（截断到前 2000 字符）:\n```python\n{source[:2000]}\n```\n"
                if hits:
                    prompt += "\n相关文献摘要：\n" + "\n".join(
                        f"- {h.title}: {h.snippet}" for h in hits[:3]
                    )
                prompt += (
                    "\n请输出 Markdown，包含：1) 修改点列表 2) 修改前后的代码对比 "
                    "3) 风险与回滚方式。不要输出有害或非法代码。"
                )
            except Exception as e:
                prompt += f"\n（无法读取源码: {e}，请给高层修改思路。）"
            return self.llm.ask(prompt, system="你是谨慎的 Python 代码审查员。")
        # mock / offline：给结构化建议
        lines = [
            "## 高层修改建议（mock/离线模式下不生成具体代码 diff）",
            "",
            f"- **目标**: {description}",
            f"- **理由**: {rationale}",
            "- 请人工审查后手动实现，或切换到真实 LLM（provider=ollama/openai/dashscope）再跑一次以生成具体代码。",
            "",
        ]
        if hits:
            lines.append("参考文献：")
            for h in hits[:3]:
                lines.append(f"- [{h.source}] {h.title} — {h.snippet[:80]}...  ({h.url})")
        return "\n".join(lines)

    def _apply(self, full_path: str, body: str, description: str) -> bool:
        """从 body 中提取第一个 ```python``` 代码块，追加到目标文件尾部（先备份 .bak）。"""
        try:
            shutil.copy2(full_path, full_path + ".bak")
        except Exception as e:
            print(f"    [CodeEditor] 备份 {full_path} 失败: {e}")
            return False
        m = re.search(r"```python\n([\s\S]*?)\n```", body)
        if not m:
            print(f"    [CodeEditor] {os.path.relpath(full_path, PROJECT_ROOT)}: "
                  "未找到 ```python``` 代码块，仅保留 patch 文件。")
            return False
        snippet = m.group(1).strip()
        if not snippet:
            return False
        try:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n\n# >>> AutoDriver 自动插入开始（" + description + "）\n")
                f.write(snippet + "\n")
                f.write("# <<< AutoDriver 自动插入结束\n")
            return True
        except Exception as e:
            print(f"    [CodeEditor] 写入 {full_path} 失败: {e}；尝试回滚到 .bak")
            try:
                shutil.copy2(full_path + ".bak", full_path)
            except Exception:
                pass
            return False


def _safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_") or "patch"


# ========================================================================
# public export（供 scripts.autodriver 从外部 import）
# ========================================================================

__all__ = [
    "LLMConfig", "LLMHelper",
    "SearchProvider", "SearchResult",
    "Reflector",
    "CreativePlanner", "CreativePlan",
    "CodeEditor", "PatchSpec",
]
