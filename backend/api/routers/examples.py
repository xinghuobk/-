"""示例问题库（来自附录 A）"""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas_api import ExampleQuestion, ExampleQuestionListResponse

router = APIRouter(prefix="/api/examples", tags=["examples"])

# 来自 ParaJudge 设计报告的示例问题
QUESTIONS = [
    ExampleQuestion(id="ex-001", category="AGI / AI 影响", text="LLM 是否会取代人类大部分工作？", difficulty="hard", expected_rounds=5),
    ExampleQuestion(id="ex-002", category="技术架构", text="Transformer 架构是否会被新模型取代？", difficulty="medium", expected_rounds=3),
    ExampleQuestion(id="ex-003", category="量子计算", text="量子计算能否在 10 年内实现商业化？", difficulty="hard", expected_rounds=4),
    ExampleQuestion(id="ex-004", category="AGI / AI 影响", text="AGI 是否会在 2030 年前实现？", difficulty="hard", expected_rounds=5),
    ExampleQuestion(id="ex-005", category="AI 与学术", text="AI 科研是否降低了学术创新的门槛？", difficulty="medium", expected_rounds=3),
    ExampleQuestion(id="ex-006", category="AI 哲学", text="大模型是否真正理解语言，还是仅是统计拟合？", difficulty="hard", expected_rounds=4),
    ExampleQuestion(id="ex-007", category="AI 安全", text="AI 对齐问题是否可解？", difficulty="hard", expected_rounds=5),
    ExampleQuestion(id="ex-008", category="技术架构", text="RAG 是否会取代微调成为主流？", difficulty="medium", expected_rounds=3),
    ExampleQuestion(id="ex-009", category="伦理", text="AI 生成内容是否应受到版权保护？", difficulty="medium", expected_rounds=3),
    ExampleQuestion(id="ex-010", category="经济", text="AI 创造的新岗位是否能抵消被替代的岗位？", difficulty="medium", expected_rounds=3),
    ExampleQuestion(id="ex-011", category="教育", text="AI 辅助教学会取代传统教师吗？", difficulty="easy", expected_rounds=2),
    ExampleQuestion(id="ex-012", category="AI 与学术", text="AI 写论文是否应被认定为学术不端？", difficulty="medium", expected_rounds=3),
]


@router.get("/questions", response_model=ExampleQuestionListResponse)
async def list_questions(category: str | None = None) -> ExampleQuestionListResponse:
    items = [q for q in QUESTIONS if category is None or q.category == category]
    return ExampleQuestionListResponse(questions=items, total=len(items))
