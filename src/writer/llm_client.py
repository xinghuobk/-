"""统一的 LLM 调用客户端。

支持三种 provider：
- mock:     离线测试，不消耗 API 配额，返回结构化 mock 结果
- dashscope: 通义千问原生 SDK
- openai:   OpenAI Chat Completion API（或任何兼容该协议的端点）

同时维护：
- 每次调用的 token 使用量
- 累计成本估算
- 结构化 JSON 提取与回退

v0.3.0
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# 成本估算（元 / 1K tokens）—— 2025 年公开价格，粗略估
# ============================================================
_PRICE_PER_1K: Dict[str, Dict[str, float]] = {
    "qwen-turbo": {"prompt": 0.002, "completion": 0.006},
    "qwen-plus": {"prompt": 0.008, "completion": 0.024},
    "qwen-max": {"prompt": 0.040, "completion": 0.120},
    "gpt-3.5-turbo": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o": {"prompt": 0.035, "completion": 0.105},
    "gpt-4o-mini": {"prompt": 0.00175, "completion": 0.00525},
    "mock-model": {"prompt": 0.0, "completion": 0.0},
}


@dataclass
class LLMCallRecord:
    """单次 LLM 调用记录（用于实验数据追踪）"""
    role: str                        # 调用者角色：debater_pro / debater_con / review / judge_evidence / ...
    prompt_preview: str              # prompt 前 200 字
    response_preview: str            # response 前 200 字
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_cny: float = 0.0            # 估算成本（人民币）
    latency_ms: int = 0              # 延迟（毫秒）
    success: bool = True
    error: str = ""
    timestamp: float = field(default_factory=time.time)
    provider: str = ""
    model: str = ""


@dataclass
class LLMSessionStats:
    """一次完整 ParaJudge 运行的 LLM 统计"""
    calls: List[LLMCallRecord] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_cny: float = 0.0

    def add(self, record: LLMCallRecord) -> None:
        self.calls.append(record)
        self.total_prompt_tokens += record.prompt_tokens
        self.total_completion_tokens += record.completion_tokens
        self.total_cost_cny += record.cost_cny


class LLMClient:
    """统一的 LLM 调用客户端。

    用法：
        client = LLMClient(provider="dashscope", model="qwen-max", api_key="sk-xxx")
        text = client.call("请简单解释量子纠缠。")
        result = client.call_json("请输出 JSON: {\"key\": \"value\"}")

    实验统计：
        client.stats 会记录每次调用的 token、成本、延迟
    """

    def __init__(
        self,
        provider: str = "mock",
        model: str = "mock-model",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        track_stats: bool = True,
    ):
        # provider 规范化
        self.provider = (provider or "mock").strip().lower()
        self.model = model.strip()
        self.temperature = temperature
        self.track_stats = track_stats
        self.stats = LLMSessionStats()

        # 尝试从环境变量读取 API key
        if not api_key:
            if self.provider == "dashscope":
                api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
            elif self.provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.api_key = api_key or None

        # base_url 读取
        if not base_url and self.provider == "openai":
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.base_url = base_url

        # provider 降级：如果配置了 provider 但没有 API key，降级为 mock
        if self.provider != "mock" and not self.api_key:
            # 降级为 mock 但保留 provider 标识
            self._fallback_to_mock = True
            self._fallback_reason = (
                f"未检测到 {self.provider.upper()} 的 API key，已降级为 mock 模式。"
                f"请在 .env 文件或环境变量中设置 {'DASHSCOPE_API_KEY' if self.provider == 'dashscope' else 'OPENAI_API_KEY'}。"
            )
        else:
            self._fallback_to_mock = False
            self._fallback_reason = ""

    # ---------- 公开 API ----------

    def call(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        role: str = "general",
    ) -> str:
        """返回纯文本响应。"""
        t0 = time.perf_counter()
        content = ""
        record = LLMCallRecord(
            role=role,
            prompt_preview=prompt[:200],
            response_preview="",
            provider=self.provider,
            model=self.model,
        )

        try:
            if self.provider == "mock" or self._fallback_to_mock:
                content = self._call_mock(prompt)
                # mock 也估算 token（按中文字数粗算）
                self._estimate_and_fill_mock(prompt, content, record)
            elif self.provider == "dashscope":
                content = self._call_dashscope(prompt, max_tokens, temperature or self.temperature or 0.7, record)
            elif self.provider == "openai":
                content = self._call_openai(prompt, max_tokens, temperature or self.temperature or 0.7, record)
            else:
                content = f"(unsupported provider: {self.provider} — 请使用 mock / dashscope / openai)"
                record.success = False
                record.error = f"unsupported provider: {self.provider}"
        except Exception as e:
            record.success = False
            record.error = str(e)
            content = f"(LLM 调用失败: {e})"

        record.response_preview = content[:200]
        record.latency_ms = int((time.perf_counter() - t0) * 1000)

        if self.track_stats:
            self.stats.add(record)

        # 如果是降级模式，第一次调用时输出提示（写入到返回内容前缀）
        if self._fallback_to_mock:
            self._fallback_to_mock = False  # 只提示一次
            prefix = f"【注意：{self._fallback_reason} 以下为 mock 模式输出】\n\n"
            content = prefix + content

        return content

    def call_json(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        role: str = "general",
    ) -> Dict[str, Any]:
        """返回 dict 结构。

        优先尝试：
        1. 从响应中提取 JSON（```json ... ```、{...}、[...]）
        2. 如果是 mock，直接构造结构化返回
        3. 失败时返回 error dict，使调用方仍能继续执行
        """
        if self.provider == "mock":
            return self._call_mock_json(prompt, role, max_tokens)

        if self._fallback_to_mock:
            return self._call_mock_json(prompt, role, max_tokens)

        text = self.call(prompt, max_tokens=max_tokens, temperature=temperature, role=role)
        extracted = self._extract_json(text)
        if extracted is not None:
            try:
                return json.loads(extracted)
            except Exception:
                pass

        # 仍然失败：降级为合理默认值（由调用方决定）
        return {
            "error": "json_parse_failed",
            "raw_response": text[:500],
            "_fallback": True,
        }

    # ---------- Mock 实现 ----------

    def _call_mock(self, prompt: str) -> str:
        """纯文本 mock 回复。"""
        p = prompt.lower()
        if "辩论" in prompt or "debate" in p or "论点" in prompt:
            return "这是一条模拟的辩论回复。"
        if "法官" in prompt or "评分" in prompt or "judge" in p or "score" in p:
            return "模拟法官回复：正方 75 分，反方 65 分。"
        if "审理" in prompt or "审查" in prompt or "review" in p:
            return "模拟审理回复：未发现严重问题。"
        return "这是一条默认的模拟回复。"

    def _call_mock_json(self, prompt: str, role: str, max_tokens: int) -> Dict[str, Any]:
        """结构化 mock 回复。"""
        t0 = time.perf_counter()
        record = LLMCallRecord(
            role=role, prompt_preview=prompt[:200], response_preview="",
            provider="mock", model=self.model,
        )

        result: Dict[str, Any] = {}
        p_lower = prompt.lower()

        # —— 法官评分 prompt ——
        if any(k in prompt for k in ["法官", "评分"]) or "judge" in p_lower or "score" in p_lower:
            # 根据角色给出不同的基础评分（避免全部平局）
            base_pro = 70.0
            base_con = 60.0
            if "证据法" in prompt:
                base_pro, base_con = 72, 65
            elif "逻辑" in prompt:
                base_pro, base_con = 70, 62
            elif "原则" in prompt:
                base_pro, base_con = 75, 60
            elif "案例" in prompt:
                base_pro, base_con = 74, 68
            elif "创新" in prompt or "创新性" in prompt:
                base_pro, base_con = 78, 63
            # 加入小幅扰动
            import random
            rng = random.Random(hash(prompt[:50]) & 0xFFFFFFFF)
            pro_score = round(base_pro + rng.uniform(-5, 5), 1)
            con_score = round(base_con + rng.uniform(-5, 5), 1)
            pro_score = max(0.0, min(100.0, pro_score))
            con_score = max(0.0, min(100.0, con_score))
            result = {
                "pro_score": pro_score,
                "con_score": con_score,
                "pro_feedback": f"正方论点总体清晰，证据引用基本合理（基础分 {pro_score:.1f}）。",
                "con_feedback": f"反方论点有一定说服力，但部分论证有待加强（基础分 {con_score:.1f}）。",
                "reasoning": "综合考虑证据权威度、论证逻辑严密性与创新价值，给出评分。",
            }

        # —— 审理 prompt ——
        elif "审理" in prompt or "invalid_cite" in prompt or "weak_support" in prompt:
            result = {
                "issues": [
                    {
                        "issue_type": "weak_support",
                        "target_arg_id": "A-002",
                        "excerpt": "部分论点引用的证据描述过于笼统。",
                        "description": "该论点仅提供定性描述，缺乏定量数据或具体引用页码。",
                        "severity": "warning",
                    }
                ]
            }

        # —— 辩论者 prompt（默认分支） ——
        else:
            import random
            rng = random.Random(hash(prompt[:40]) & 0xFFFFFFFF)
            is_pro = "正方" in prompt or "pro" in p_lower or "主张问题的答案为「是」" in prompt
            stance = "正方" if is_pro else "反方"
            arg_templates = [
                f"基于学术研究的共识，{stance}认为该问题的答案更倾向于{'「是」' if is_pro else '「否」'}（E-001）。",
                f"根据最近发表的实证数据，{stance}的核心立场得到了多个独立研究的支持（E-002）。",
                f"从方法论角度审视，{stance}所采用的论证路径具有更高的内在一致性（E-003）。",
            ]
            # 取 2 条
            chosen = [arg_templates[i % len(arg_templates)] for i in range(2)]
            result = {
                "reasoning": f"作为{stance}，选择最直接支撑立场的证据作为开场，并准备交叉质询。",
                "arguments": [
                    {"content": c, "evidence_refs": [f"E-00{i+1:02d}"]}
                    for i, c in enumerate(chosen)
                ],
            }

        # 估算 mock token & cost
        response_text = json.dumps(result, ensure_ascii=False)
        self._estimate_and_fill_mock(prompt, response_text, record)
        record.latency_ms = int((time.perf_counter() - t0) * 1000)
        record.response_preview = response_text[:200]
        if self.track_stats:
            self.stats.add(record)

        return result

    # ---------- DashScope 实现 ----------

    def _call_dashscope(self, prompt: str, max_tokens: int, temperature: float, record: LLMCallRecord) -> str:
        """调用通义千问原生 SDK。"""
        try:
            import dashscope
        except ImportError:
            raise RuntimeError(
                "未安装 dashscope SDK。请运行：pip install dashscope"
            )

        dashscope.api_key = self.api_key
        messages = [{"role": "user", "content": prompt}]

        response = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            result_format="message",
        )

        if response.status_code != 200:
            raise RuntimeError(f"DashScope API 错误: {response.status_code} — {response.message}")

        content = ""
        try:
            content = response.output.choices[0]["message"]["content"]
        except Exception:
            content = str(response.output)

        # token 统计
        try:
            usage = response.usage
            record.prompt_tokens = int(usage.get("input_tokens", 0))
            record.completion_tokens = int(usage.get("output_tokens", 0))
            record.total_tokens = record.prompt_tokens + record.completion_tokens
        except Exception:
            self._estimate_and_fill_mock(prompt, content, record)

        # 成本估算
        record.cost_cny = self._estimate_cost(self.model, record.prompt_tokens, record.completion_tokens)

        return content

    # ---------- OpenAI 实现 ----------

    def _call_openai(self, prompt: str, max_tokens: int, temperature: float, record: LLMCallRecord) -> str:
        """调用 OpenAI Chat Completion API。"""
        try:
            import requests
        except ImportError:
            raise RuntimeError("请先安装 requests: pip install requests")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        resp = requests.post(url, headers=headers, json=payload, timeout=120)

        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # token 统计
        usage = data.get("usage", {})
        record.prompt_tokens = int(usage.get("prompt_tokens", 0))
        record.completion_tokens = int(usage.get("completion_tokens", 0))
        record.total_tokens = int(usage.get("total_tokens", 0))
        if record.total_tokens == 0:
            self._estimate_and_fill_mock(prompt, content, record)

        record.cost_cny = self._estimate_cost(self.model, record.prompt_tokens, record.completion_tokens)

        return content

    # ---------- 工具方法 ----------

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """从任意文本中提取 JSON 子串。

        返回原始 JSON 字符串，或 None。
        """
        if not text or not text.strip():
            return None

        # 策略 1：```json ... ```
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1)
        m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
        if m:
            return m.group(1)

        # 策略 2：首个 { ... } 或 [ ... ]
        for start, end in [("{", "}"), ("[", "]")]:
            first = text.find(start)
            last = text.rfind(end)
            if first != -1 and last != -1 and last > first:
                candidate = text[first:last + 1]
                # 快速验证是否可解析
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    pass

        # 策略 3：逐字符扫描，找到最大可解析的子串
        # （为避免复杂逻辑，此处直接返回）
        return None

    @staticmethod
    def _estimate_and_fill_mock(prompt: str, content: str, record: LLMCallRecord) -> None:
        """按中文字符数粗估 token（≈ 1 token / 1.7 汉字 或 4 个英文单词）。"""
        import math
        # 粗估：prompt token ≈ len(prompt) / 2，completion token ≈ len(content) / 2
        pt = max(1, len(prompt) // 2)
        ct = max(1, len(content) // 2)
        record.prompt_tokens = pt
        record.completion_tokens = ct
        record.total_tokens = pt + ct

    @staticmethod
    def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """估算一次调用的成本（元）。"""
        key = model if model in _PRICE_PER_1K else "qwen-max"
        prices = _PRICE_PER_1K[key]
        return round(
            prices["prompt"] * prompt_tokens / 1000.0
            + prices["completion"] * completion_tokens / 1000.0,
            6,
        )

    def print_summary(self, title: str = "LLM 调用统计") -> None:
        """打印本次会话的统计摘要（用于 CLI 输出）。"""
        s = self.stats
        print(f"\n{'=' * 50}")
        print(f"  {title}")
        print(f"  Provider        : {self.provider}")
        print(f"  Model           : {self.model}")
        print(f"  Total calls     : {len(s.calls)}")
        print(f"  Prompt tokens   : {s.total_prompt_tokens:,}")
        print(f"  Completion tkns : {s.total_completion_tokens:,}")
        print(f"  Total tokens    : {s.total_prompt_tokens + s.total_completion_tokens:,}")
        print(f"  Est. cost (CNY) : ¥{s.total_cost_cny:.4f}")
        print(f"{'=' * 50}\n")


__all__ = ["LLMClient", "LLMCallRecord", "LLMSessionStats"]
