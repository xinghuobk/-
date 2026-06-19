"""法官与 LLM Provider 元数据"""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas_api import (
    JudgeInfo,
    JudgeListResponse,
    LLMProviderInfo,
    LLMProviderListResponse,
)

router = APIRouter(prefix="/api", tags=["metadata"])

# 五位法官的元数据（与 src/judgment/judgment_engine.py 中的 JUDGE_TYPES 对齐）
JUDGES = [
    JudgeInfo(
        code="evidence",
        name="证据法法官",
        name_en="Evidence Law",
        description="严格审查每条论点的证据来源与引用质量",
        avatar="📊",
        color="#00b4d8",
        weight=1.2,
    ),
    JudgeInfo(
        code="logic",
        name="逻辑分析法官",
        name_en="Logic Analysis",
        description="检查论证的因果链与逻辑谬误",
        avatar="🧠",
        color="#b794f4",
        weight=1.0,
    ),
    JudgeInfo(
        code="principle",
        name="原则性法官",
        name_en="Principle",
        description="从一般性原则判断论证合理性",
        avatar="⚡",
        color="#ffd166",
        weight=0.9,
    ),
    JudgeInfo(
        code="case",
        name="案例法法官",
        name_en="Case Precedent",
        description="参照历史案例与先例进行评判",
        avatar="📚",
        color="#ff4d6d",
        weight=1.0,
    ),
    JudgeInfo(
        code="innovation",
        name="创新性法官",
        name_en="Innovation",
        description="评估论证视角的新颖性与创造性",
        avatar="🚀",
        color="#06d6a0",
        weight=0.8,
    ),
]

PROVIDERS = [
    LLMProviderInfo(
        code="mock",
        name="Mock（离线演示）",
        available=True,
        models=["mock-model", "mock-pro", "mock-con", "mock-judge"],
        requires_api_key=False,
        description="无需 API Key，根据 prompt 内容返回合理的模拟响应，用于离线测试与演示",
    ),
    LLMProviderInfo(
        code="openai",
        name="OpenAI / 兼容协议",
        available=True,
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        requires_api_key=True,
        description="支持 OpenAI ChatCompletion 及兼容 OpenAI 协议的所有端点（如 vLLM、Ollama）",
    ),
    LLMProviderInfo(
        code="dashscope",
        name="通义千问（DashScope）",
        available=True,
        models=["qwen-max", "qwen-plus", "qwen-turbo"],
        requires_api_key=True,
        description="阿里云通义千问原生 SDK",
    ),
    LLMProviderInfo(
        code="ollama",
        name="Ollama（本地免费）",
        available=True,
        models=["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "deepseek-r1:7b"],
        requires_api_key=False,
        description="本地免费 LLM：先安装 Ollama（https://ollama.com），再 ollama pull qwen2.5:7b 即可，OpenAI 兼容协议 http://localhost:11434/v1",
    ),
]


@router.get("/judges", response_model=JudgeListResponse)
async def list_judges() -> JudgeListResponse:
    return JudgeListResponse(judges=JUDGES, total=len(JUDGES))


@router.get("/judges/{code}", response_model=JudgeInfo)
async def get_judge(code: str) -> JudgeInfo:
    for j in JUDGES:
        if j.code == code:
            return j
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"judge {code} 不存在")


@router.get("/llm/providers", response_model=LLMProviderListResponse)
async def list_providers() -> LLMProviderListResponse:
    return LLMProviderListResponse(providers=PROVIDERS, default="mock")
