"""健康检查与版本信息"""
from __future__ import annotations

import platform
import time

from fastapi import APIRouter

from backend.api.schemas_api import HealthResponse, VersionResponse

router = APIRouter(prefix="/api", tags=["system"])

_START_TIME = time.time()
_VERSION = "0.1.0"
_API_VERSION = "v1"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """健康检查：探活 + 模块加载情况"""
    modules = {}
    try:
        from src.orchestration.orchestrator import run_parajudge  # noqa: F401
        modules["orchestrator"] = True
    except Exception:
        modules["orchestrator"] = False
    try:
        from src.writer.llm_client import LLMClient  # noqa: F401
        modules["llm_client"] = True
    except Exception:
        modules["llm_client"] = False
    try:
        from backend.models.schemas import FullPipelineOutput  # noqa: F401
        modules["schemas"] = True
    except Exception:
        modules["schemas"] = False

    is_ok = all(modules.values())
    return HealthResponse(
        status="ok" if is_ok else "degraded",
        version=_VERSION,
        uptime_sec=round(time.time() - _START_TIME, 1),
        modules=modules,
    )


@router.get("/version", response_model=VersionResponse)
async def version() -> VersionResponse:
    return VersionResponse(
        name="ParaJudge",
        version=_VERSION,
        api_version=_API_VERSION,
        python_version=platform.python_version(),
        llm_providers=["mock", "openai", "dashscope", "ollama"],
    )
