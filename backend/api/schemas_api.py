"""API 层数据模型（请求 / 响应 DTO）。

与 `backend.models.schemas` 中的领域模型解耦：
- API 模型专注于「协议层」字段（HTTP 友好的 snake_case / 扁平结构）
- 领域模型专注于「业务层」结构（与 Pydantic 类一一对应）
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================
# 通用模型
# ============================================================

class ErrorDetail(BaseModel):
    """统一错误响应"""
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="人类可读错误信息")
    field: Optional[str] = Field(default=None, description="关联字段")
    trace_id: Optional[str] = Field(default=None, description="追踪 ID")


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = Field(..., description="ok / degraded / down")
    version: str
    uptime_sec: float
    modules: Dict[str, bool] = Field(default_factory=dict, description="模块加载情况")


class VersionResponse(BaseModel):
    name: str
    version: str
    api_version: str
    python_version: str
    llm_providers: List[str]


# ============================================================
# LLM 配置
# ============================================================

class LLMConfig(BaseModel):
    provider: str = Field(default="mock", description="mock / openai / dashscope")
    model: str = Field(default="mock-model")
    api_key: Optional[str] = Field(default=None, description="留空从环境变量读取")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, ge=50, le=8000)


# ============================================================
# 主持人配置
# ============================================================

class ModeratorConfigDTO(BaseModel):
    strictness: str = Field(default="normal", description="loose / normal / strict")
    duplicate_threshold: float = Field(default=0.85, ge=0.5, le=1.0)
    off_topic_threshold: float = Field(default=0.4, ge=0.1, le=0.9)
    enable_poi: bool = Field(default=False)
    max_tokens_per_turn: int = Field(default=400, ge=50)
    max_seconds_per_turn: int = Field(default=120, ge=10)


# ============================================================
# 同步执行请求 / 响应
# ============================================================

class ParaJudgeRunRequest(BaseModel):
    problem: str = Field(..., min_length=1, max_length=1000, description="待辩论问题")
    pro_stance: Optional[str] = Field(default=None, description="正方立场，留空自动生成")
    con_stance: Optional[str] = Field(default=None, description="反方立场，留空自动生成")
    rounds: int = Field(default=3, ge=1, le=8)
    max_evidence: int = Field(default=20, ge=1, le=50)
    enable_llm_review: bool = Field(default=True)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    moderator: Optional[ModeratorConfigDTO] = None


class ParaJudgeRunResponse(BaseModel):
    run_id: str
    problem: str
    evidence_brief: Dict[str, Any]
    transcript: Dict[str, Any]
    review: Dict[str, Any]
    judgment: Dict[str, Any]
    total_time_sec: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# 异步任务
# ============================================================

class JobCreateRequest(ParaJudgeRunRequest):
    callback_url: Optional[str] = Field(default=None, description="完成时回调地址")
    stream: bool = Field(default=True, description="是否启用 SSE 推送")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    stream_url: str
    result_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    current_phase: Optional[str] = None
    progress: float = 0.0
    phase_durations: Dict[str, float] = Field(default_factory=dict)
    estimated_remaining_sec: Optional[float] = None
    error: Optional[ErrorDetail] = None
    result_url: Optional[str] = None


# ============================================================
# 单阶段执行（用于调试与重跑）
# ============================================================

class Phase0Request(BaseModel):
    problem: str = Field(..., min_length=1)
    max_papers: int = Field(default=20, ge=1, le=50)


class Phase1Request(BaseModel):
    problem: str = Field(..., min_length=1)
    brief: Dict[str, Any] = Field(..., description="Phase 0 输出的 EvidenceBrief")
    rounds: int = Field(default=3, ge=1, le=8)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class Phase21Request(BaseModel):
    transcript: Dict[str, Any] = Field(..., description="Phase 1 输出的 DebateTranscript")
    brief: Dict[str, Any]
    enable_llm_check: bool = Field(default=True)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class Phase22Request(BaseModel):
    transcript: Dict[str, Any]
    brief: Dict[str, Any]
    review: Dict[str, Any]
    llm: LLMConfig = Field(default_factory=LLMConfig)


# ============================================================
# 法官 / Provider 元数据
# ============================================================

class JudgeInfo(BaseModel):
    code: str
    name: str
    name_en: str
    description: str
    avatar: str
    color: str
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


class JudgeListResponse(BaseModel):
    judges: List[JudgeInfo]
    total: int


class LLMProviderInfo(BaseModel):
    code: str
    name: str
    available: bool
    models: List[str] = Field(default_factory=list)
    requires_api_key: bool
    description: Optional[str] = None


class LLMProviderListResponse(BaseModel):
    providers: List[LLMProviderInfo]
    default: str


# ============================================================
# 示例问题
# ============================================================

class ExampleQuestion(BaseModel):
    id: str
    category: str
    text: str
    difficulty: str = Field(default="medium", description="easy / medium / hard")
    expected_rounds: int = 3


class ExampleQuestionListResponse(BaseModel):
    questions: List[ExampleQuestion]
    total: int
