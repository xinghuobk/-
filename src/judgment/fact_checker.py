"""Phase 2.0 · 事实核查模块（FactChecker）。

职责：
1. 从辩论记录中提取原子事实声明
2. 判断声明类型（事实 vs 价值/观点）
3. 使用 LLM 作为核查引擎（模拟外部知识库查询）
4. 生成 ClaimVerdict + 置信度

设计原则：
- 独立于辩论引擎（只读 transcript）
- 支持 mock provider（无外部依赖）
- 核查结果注入 Moderator 作为信号
"""
from __future__ import annotations

import time
import uuid
from typing import List, Dict, Optional

from backend.models.schemas import (
    DebateTranscript,
    FactCheckReport,
    FactClaim,
    ClaimVerdict,
)
from src.writer.llm_client import LLMClient


VERDICT_PROMPT = """你是一个严谨的事实核查员。请对以下辩论论点中的事实声明进行核查。

【待核查论点】
{argument_content}

【背景问题】
{problem}

【核查要求】
1. 识别论点中的所有原子事实声明（可检验真伪的陈述，排除价值观、观点、预测性声明）
2. 对每条声明，给出 verdict：
   - verified：有可靠证据支撑该声明为真
   - refuted：有可靠证据证明该声明为假
   - uncertain：证据不足或无法判断
   - out_of_scope：该声明非事实性（价值观/观点/预测），无需核查
3. 对每条声明，给出 confidence（0.0-1.0），越高表示核查员对 verdict 越有信心
4. 简要列出 supporting_evidence（支持证据）和 contradicting_evidence（反驳证据）

【输出格式】（严格 JSON）
{{
  "claims": [
    {{
      "content": "声明的原文内容",
      "verdict": "verified | refuted | uncertain | out_of_scope",
      "confidence": 0.85,
      "supporting_evidence": ["证据摘要1", "证据摘要2"],
      "contradicting_evidence": ["矛盾证据摘要1"],
      "is_factual": true
    }}
  ],
  "summary": "总体核查结论（1-2句话）"
}}
"""


class FactChecker:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, transcript: DebateTranscript, problem: str) -> FactCheckReport:
        """对辩论记录中的所有论点进行事实核查。"""
        t0 = time.perf_counter()

        all_args = transcript.argument_index.arguments
        claims: List[FactClaim] = []
        claim_id_counter = 1

        for arg in all_args:
            arg_claims = self._check_argument(arg.content, problem, arg.side, arg.arg_id, claim_id_counter)
            for c in arg_claims:
                c.claim_id = f"FC-{claim_id_counter:03d}"
                claim_id_counter += 1
            claims.extend(arg_claims)

        # 统计
        verified = sum(1 for c in claims if c.verdict == ClaimVerdict.VERIFIED)
        refuted = sum(1 for c in claims if c.verdict == ClaimVerdict.REFUTED)
        uncertain = sum(1 for c in claims if c.verdict == ClaimVerdict.UNCERTAIN)
        out_of_scope = sum(1 for c in claims if c.verdict == ClaimVerdict.OUT_OF_SCOPE)
        factual = sum(1 for c in claims if c.is_factual)
        total = len(claims)
        factuality_ratio = factual / total if total > 0 else 0.0

        summary = self._build_summary(verified, refuted, uncertain, out_of_scope, total, factual)

        return FactCheckReport(
            claims=claims,
            verified_count=verified,
            refuted_count=refuted,
            uncertain_count=uncertain,
            out_of_scope_count=out_of_scope,
            factuality_ratio=factuality_ratio,
            summary=summary,
            generation_time=round(time.perf_counter() - t0, 3),
        )

    def _check_argument(
        self,
        content: str,
        problem: str,
        side: str,
        arg_id: str,
        start_counter: int,
    ) -> List[FactClaim]:
        """使用 LLM 核查单个论点的所有声明。"""
        prompt = VERDICT_PROMPT.format(
            argument_content=content,
            problem=problem,
        )
        response = self.llm.call_json(prompt, max_tokens=800, temperature=0.2)

        if not isinstance(response, dict) or "claims" not in response:
            # LLM 解析失败：降级为单个 uncertain 声明
            return [FactClaim(
                claim_id=f"FC-{start_counter:03d}",
                source_arg_id=arg_id,
                source_side=side,
                content=content[:300],
                verdict=ClaimVerdict.UNCERTAIN,
                supporting_evidence=[],
                contradicting_evidence=[],
                confidence=0.1,
                is_factual=True,
            )]

        raw_claims = response.get("claims", [])
        result: List[FactClaim] = []
        for rc in raw_claims:
            try:
                verdict_str = rc.get("verdict", "uncertain")
                verdict = ClaimVerdict(verdict_str)
            except ValueError:
                verdict = ClaimVerdict.UNCERTAIN

            result.append(FactClaim(
                claim_id=f"FC-{start_counter:03d}",
                source_arg_id=arg_id,
                source_side=side,
                content=str(rc.get("content", "")),
                verdict=verdict,
                supporting_evidence=rc.get("supporting_evidence", []),
                contradicting_evidence=rc.get("contradicting_evidence", []),
                confidence=float(rc.get("confidence", 0.5)),
                is_factual=rc.get("is_factual", verdict != ClaimVerdict.OUT_OF_SCOPE),
            ))

        return result

    @staticmethod
    def _build_summary(
        verified: int,
        refuted: int,
        uncertain: int,
        out_of_scope: int,
        total: int,
        factual: int,
    ) -> str:
        if total == 0:
            return "无事实声明可核查。"
        parts = []
        if verified > 0:
            parts.append(f"{verified} 条声明已验证为真")
        if refuted > 0:
            parts.append(f"{refuted} 条声明被证伪")
        if uncertain > 0:
            parts.append(f"{uncertain} 条声明证据不足")
        if out_of_scope > 0:
            parts.append(f"{out_of_scope} 条为价值/观点声明")
        return f"共核查 {total} 条声明（{factual} 条事实性，{', '.join(parts)}）。"


__all__ = ["FactChecker"]
