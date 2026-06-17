"""统一 LLM 调用客户端。

职责：
- 封装多个 provider（mock / openai / dashscope）的底层调用
- 提供结构化 JSON 输出解析（辩论/裁决场景需要）
- 暴露简单接口：call(text) -> str, call_json(text) -> dict

与 AcademicWriter 的关系：
- AcademicWriter 为写作辅助（summarize/translate/polish/review/outline）设计
- LLMClient 为辩论推理场景设计，需要更精细的参数控制和结构化输出
- 两者共享相同的 provider 抽象，但各自独立
"""
from __future__ import annotations

import json
import os
import time
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# 数据结构
# ============================================================

@dataclass
class LLMResponse:
    content: str
    model_name: str
    tokens_used: int = 0
    latency_sec: float = 0.0
    raw_response: Any = None


# ============================================================
# 主客户端
# ============================================================

class LLMClient:
    """统一 LLM 调用客户端。

    provider: 'mock' | 'openai' | 'dashscope' | 'ollama'
        - mock: 离线测试，根据 prompt 内容返回合理的模拟响应
        - openai: OpenAI ChatCompletion（或兼容协议的端点，如 vLLM / OpenRouter）
        - dashscope: 通义千问原生 SDK
        - ollama: 本地 Ollama 服务（OpenAI 兼容协议，默认 http://localhost:11434）
    """

    def __init__(
        self,
        provider: str = "mock",
        model: str = "mock-model",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.provider = provider.strip().lower()
        self.model = self._normalize_model_name(self.provider, model)
        self.api_key = api_key
        self.base_url = (base_url or self._default_base_url(self.provider)).rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _default_base_url(provider: str) -> str:
        return {
            "ollama": "http://localhost:11434/v1",
            "openai": "https://api.openai.com/v1",
            "dashscope": "",
            "mock": "",
        }.get(provider, "")

    @staticmethod
    def _normalize_model_name(provider: str, model: str) -> str:
        """规范化模型名：空/mock-model → 用 provider 默认值。"""
        defaults = {
            "openai": "gpt-3.5-turbo",
            "dashscope": "qwen-max",
            "ollama": "qwen2.5:7b",
            "mock": "mock-model",
        }
        if not model or model == "mock-model":
            return defaults.get(provider, model or "mock-model")
        return model

    # ------------------------------------------------------------------
    # 主接口
    # ------------------------------------------------------------------

    def call(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        expect_json: bool = False,
    ) -> str:
        """调用 LLM 并返回文本。若 expect_json=True，会尝试提取 JSON 结构。"""
        resp = self._call_provider(prompt, max_tokens, temperature)

        if expect_json:
            extracted = self._extract_json(resp.content)
            return extracted if extracted is not None else resp.content
        return resp.content

    def call_json(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """期望返回 JSON 的便捷方法。解析失败时返回 {"error": ..., "raw": content}。"""
        text = self.call(prompt, max_tokens, temperature, expect_json=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                return json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                return {"error": "json_parse_failed", "raw": text}

    # ------------------------------------------------------------------
    # 分发
    # ------------------------------------------------------------------

    def _call_provider(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        t0 = time.perf_counter()
        if self.provider == "mock":
            content = self._mock_response(prompt, max_tokens)
        elif self.provider == "openai":
            content = self._openai_call(prompt, max_tokens, temperature)
        elif self.provider == "ollama":
            content = self._ollama_call(prompt, max_tokens, temperature)
        elif self.provider == "dashscope":
            content = self._dashscope_call(prompt, max_tokens, temperature)
        else:
            content = f"[unsupported provider: {self.provider}]"

        return LLMResponse(
            content=content,
            model_name=self.model,
            latency_sec=round(time.perf_counter() - t0, 3),
        )

    # ------------------------------------------------------------------
    # provider 实现
    # ------------------------------------------------------------------

    def _mock_response(self, prompt: str, max_tokens: int) -> str:
        """
        智能 mock：根据 prompt 关键词返回合理的响应。

        识别模式：
          - 含 "arguments" + "JSON"        → 辩论论点 JSON
          - 含 "issue" + "JSON"           → 审理问题清单 JSON
          - 含 "judge" 或 "pro_score"     → 裁决评分 JSON
          - 含 "review" 或 "evidence"     → 证据审阅 JSON（简单）
          - 其他                          → 纯文本占位
        """
        p_lower = prompt.lower()

        # --- 优先级 1：法官评分（最具体，含法官角色名） ---
        # 必须在 review 之前，因为 review_summary 可能含 "issue_type" 关键词
        if any(kw in prompt for kw in [
            "证据法法官", "逻辑分析法官", "原则性法官", "案例法法官", "创新性法官",
            "通用法官"
        ]) or ("pro_score" in p_lower and "con_score" in p_lower):
            return self._mock_judge_score(prompt)

        # --- 优先级 2：辩论：正反方论点 ---
        if "arguments" in p_lower and ("json" in p_lower or "pro" in p_lower or "con" in p_lower):
            return self._mock_debate_arguments(prompt)

        # --- 优先级 3：审理：问题清单 ---
        if ("issue" in p_lower and "json" in p_lower) or ("invalid_cite" in p_lower or "weak_support" in p_lower):
            return self._mock_review_issues(prompt)

        # --- 默认：返回简短文本提示 ---
        return "[MOCK] This is a placeholder response from the mock LLM backend. Enable a real provider (openai/dashscope) by setting the corresponding API key environment variable."

    # ------------------------------------------------------------------
    # Mock 细节
    # ------------------------------------------------------------------

    def _mock_debate_arguments(self, prompt: str) -> str:
        """返回合理的 mock 辩论 JSON。根据立场给不同内容（启发式）。"""
        # 启发式：如果 prompt 中存在「反方」或「con」，则给出反方论点；否则默认正方
        is_pro = not ("con" in prompt.lower() or "反方" in prompt)
        content1 = (
            "LLM 已在客服、翻译和基础编程等多个职业类别的常规任务中展现出与人类相当或超越人类的水平（E-001）"
            if is_pro else
            "历史上的技术革命（如计算机、互联网）最终都创造了更多新岗位，AI 更可能是工作内容迁移而非净减少（E-005）"
        )
        content2 = (
            "2023-2024 年的多项研究显示，企业采用 LLM 后相关岗位的工时需求下降了 25-40%（E-003）"
            if is_pro else
            "创造力、共情能力和复杂判断等人类核心能力当前的 LLM 尚无法替代，且人类对这些能力的需求在增加（E-007）"
        )
        refs1 = ["E-001"] if is_pro else ["E-005"]
        refs2 = ["E-003"] if is_pro else ["E-007"]

        result = {
            "reasoning": f"选择最直接支持{'正方' if is_pro else '反方'}立场的证据。",
            "arguments": [
                {"content": content1, "evidence_refs": refs1},
                {"content": content2, "evidence_refs": refs2},
            ],
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _mock_review_issues(self, prompt: str) -> str:
        """返回合理的 mock 审理问题清单（可能找到 0-2 个中等问题）。"""
        result = {
            "issues": [
                {
                    "issue_type": "weak_support",
                    "target_arg_id": "A-002",
                    "description": "论点声称 LLM 导致工时下降，但证据 E-003 仅统计了 3 家科技公司样本，代表性有限"
                }
            ]
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _mock_judge_score(self, prompt: str) -> str:
        """返回 mock 法官评分（v2：对称性修正）。

        v2 修正：
        - 5 位法官使用相同的 base 分数（70/70），不系统性偏向任一方
        - 每位法官有独立的随机扰动（±4），模拟不同视角的合理分歧
        - 不根据 prompt 中关键字人为制造正方/反方 bias
        """
        # 5 位法官共用 baseline，但用 judge_type 名注入不同 seed 保证可复现
        import hashlib
        judge_token = ""
        for kw in ["证据法法官", "证据", "逻辑分析法官", "逻辑", "原则性法官",
                   "原则", "案例法法官", "案例", "创新性法官", "创新",
                   "evidence", "logic", "principle", "case", "innovation"]:
            if kw in prompt.lower() or kw in prompt:
                judge_token = kw
                break

        # 用 judge 类型 + prompt hash 生成伪随机 seed（保证同一法官同一问题稳定）
        seed = int(hashlib.md5((judge_token + prompt[:100]).encode("utf-8")).hexdigest(), 16)
        rng = random.Random(seed % (2**31))

        # 对称 base 分数 + ±4 扰动（不再人为偏向一方）
        base_pro, base_con = 70, 70
        pro_score = max(0, min(100, base_pro + rng.randint(-4, 4)))
        con_score = max(0, min(100, base_con + rng.randint(-4, 4)))

        # 反馈信息保持中性
        if pro_score > con_score + 3:
            pro_fb = "论证更有说服力，证据/逻辑/案例综合表现更佳。"
            con_fb = "论证质量一般，论点之间的衔接有待加强。"
        elif con_score > pro_score + 3:
            pro_fb = "论证质量一般，论点之间的衔接有待加强。"
            con_fb = "论证更有说服力，证据/逻辑/案例综合表现更佳。"
        else:
            pro_fb = "论证有一定说服力，但未形成压倒性优势。"
            con_fb = "论证有一定说服力，但未形成压倒性优势。"

        return json.dumps({
            "pro_score": pro_score,
            "con_score": con_score,
            "pro_feedback": pro_fb,
            "con_feedback": con_fb,
            "reasoning": "综合考虑证据权威度、推理链完整性和结论与问题的相关性后给出评分。",
        }, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # provider: openai（若未配置 key 则降级为 mock）
    # ------------------------------------------------------------------

    def _openai_call(self, prompt: str, max_tokens: int, temperature: float) -> str:
        api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return self._mock_response(prompt, max_tokens)

        try:
            import urllib.request
            import urllib.error

            body = json.dumps({
                "model": self.model if self.model != "mock-model" else "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            return f"[openai call failed: {exc}]"

    # ------------------------------------------------------------------
    # provider: dashscope（若未配置 key 则降级为 mock）
    # ------------------------------------------------------------------

    def _dashscope_call(self, prompt: str, max_tokens: int, temperature: float) -> str:
        api_key = self.api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return self._mock_response(prompt, max_tokens)

        try:
            import urllib.request
            import urllib.error

            model = self.model if self.model != "mock-model" else "qwen-max"
            body = json.dumps({
                "model": model,
                "input": {"messages": [{"role": "user", "content": prompt}]},
                "parameters": {"max_tokens": max_tokens, "temperature": temperature},
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("output", {}).get("text", str(data))
        except Exception as exc:
            return f"[dashscope call failed: {exc}]"

    # ------------------------------------------------------------------
    # provider: ollama（本地 LLM，OpenAI 兼容协议）
    # ------------------------------------------------------------------

    def _ollama_call(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """调用本地 Ollama 服务。

        Ollama 提供 OpenAI 兼容 API：POST /v1/chat/completions
        端点默认 http://localhost:11434/v1，无需 API key。

        若本地未启动 Ollama，会降级返回 mock 响应。
        """
        try:
            import urllib.request
            import urllib.error

            body = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key or 'ollama'}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.URLError as exc:
            # 本地 Ollama 未启动 → 降级 mock
            if "Connection refused" in str(exc) or "Errno 111" in str(exc) or "Errno 61" in str(exc):
                return self._mock_ollama_unavailable(prompt, exc)
            return f"[ollama call failed: {exc}]"
        except Exception as exc:
            return f"[ollama call failed: {exc}]"

    def _mock_ollama_unavailable(self, prompt: str, exc: Exception) -> str:
        """当 Ollama 不可用时的降级 mock，明确提示用户启动服务。"""
        return json.dumps({
            "_warning": "ollama_unavailable",
            "_detail": f"无法连接 Ollama ({exc})，请先启动服务：ollama serve",
            "_fallback": True,
            "reasoning": "Ollama 不可用，返回 mock 响应",
            "arguments": [
                {
                    "content": "Ollama 服务未启动，请先运行 'ollama serve' 并执行 'ollama pull qwen2.5:7b' 拉取模型。",
                    "evidence_refs": ["SYSTEM"]
                }
            ]
        }, ensure_ascii=False)

    # ------------------------------------------------------------------
    # 工具：JSON 提取
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """从文本中提取最外层的 { ... } 结构。"""
        if not text:
            return None
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            candidate = text[start:end]
            json.loads(candidate)  # 验证是合法 JSON
            return candidate
        except (ValueError, json.JSONDecodeError):
            return None


__all__ = ["LLMClient", "LLMResponse"]
