"""ParaJudge 路由：完整流程与单阶段执行。"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from backend.api.job_manager import JOB_MANAGER, Job, JobEvent
from backend.api.schemas_api import (
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
    ParaJudgeRunRequest,
    ParaJudgeRunResponse,
    Phase0Request,
    Phase1Request,
    Phase21Request,
    Phase22Request,
)
from backend.api.sse import stream_job_events

router = APIRouter(prefix="/api/parajudge", tags=["parajudge"])


# ============================================================
# 同步执行
# ============================================================

@router.post("/run", response_model=ParaJudgeRunResponse)
async def run_sync(req: ParaJudgeRunRequest) -> ParaJudgeRunResponse:
    """同步执行完整 ParaJudge 流程（适合短任务）。"""
    from src.orchestration.orchestrator import run_parajudge

    try:
        t_start = time.time()
        result = await asyncio.to_thread(
            run_parajudge,
            problem=req.problem,
            provider=req.llm.provider,
            model=req.llm.model,
            api_key=req.llm.api_key,
            rounds=req.rounds,
            max_evidence=req.max_evidence,
            enable_llm_review=req.enable_llm_review,
            enable_moderator=req.enable_moderator,
            moderator_strictness=req.moderator_strictness,
            enable_t1_aebg=req.enable_t1_aebg,
            enable_t3_ks=req.enable_t3_ks,
            enable_t4_ds=req.enable_t4_ds,
        )
        t_end = time.time()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "LLM_PROVIDER_ERROR", "message": str(e)},
        )

    return ParaJudgeRunResponse(
        run_id=result.run_id,
        problem=result.problem,
        evidence_brief=result.evidence_brief.model_dump(),
        transcript=result.transcript.model_dump(),
        review=result.review.model_dump(),
        judgment=result.judgment.model_dump(),
        total_time_sec=result.total_time_sec,
        metadata={
            "started_at": t_start,
            "finished_at": t_end,
            "llm_provider": req.llm.provider,
            "llm_model": req.llm.model,
            "phase_durations": {
                "phase_0_evidence": result.evidence_brief.build_time_sec,
                "phase_1_debate": result.transcript.generation_time,
                "phase_2_1_review": result.review.generation_time,
                "phase_2_2_judgment": result.judgment.generation_time,
            },
            "moderator_report": result.transcript.moderator_report,
        },
    )


# ============================================================
# 异步任务
# ============================================================

@router.post("/jobs", response_model=JobCreateResponse, status_code=202)
async def create_job(req: JobCreateRequest) -> JobCreateResponse:
    """创建异步任务，返回 job_id。"""
    from src.orchestration.orchestrator import run_parajudge

    job = JOB_MANAGER.create_job()
    job.push_event(JobEvent("job.queued", {"problem": req.problem[:80]}))

    async def runner(j: Job) -> Dict[str, Any]:
        from src.orchestration.orchestrator import run_parajudge
        loop = asyncio.get_event_loop()

        # Phase 0
        j.current_phase = "phase_0_evidence"
        j.push_event(JobEvent("phase.started", {"phase": "phase_0_evidence"}))
        t0 = time.time()
        result = await loop.run_in_executor(
            None,
            lambda: run_parajudge(
                problem=req.problem,
                provider=req.llm.provider,
                model=req.llm.model,
                api_key=req.llm.api_key,
                rounds=req.rounds,
                max_evidence=req.max_evidence,
                enable_llm_review=req.enable_llm_review,
                enable_moderator=req.enable_moderator,
                moderator_strictness=req.moderator_strictness,
                enable_t1_aebg=req.enable_t1_aebg,
                enable_t3_ks=req.enable_t3_ks,
                enable_t4_ds=req.enable_t4_ds,
            )
        )
        j.phase_durations["phase_0_evidence"] = round(time.time() - t0, 2)
        j.progress = 0.25
        # 实际上 orchestration 一次性跑完；为模拟分阶段进度，按时间比例累加
        j.phase_durations["phase_1_debate"] = result.transcript.generation_time
        j.phase_durations["phase_2_1_review"] = result.review.generation_time
        j.phase_durations["phase_2_2_judgment"] = result.judgment.generation_time
        j.progress = 1.0

        # 推送结果事件
        for arg in result.transcript.arguments:
            j.push_event(JobEvent("argument.added", {
                "arg_id": arg.arg_id,
                "side": arg.side,
                "content": arg.content,
                "evidence_refs": arg.evidence_refs,
                "round_index": arg.round_index,
            }))
        for issue in result.review.issues:
            j.push_event(JobEvent("review.issue", issue.model_dump()))
        for score in result.judgment.judge_scores:
            j.push_event(JobEvent("judge.scored", {
                "judge_type": score.judge_type,
                "pro_score": score.pro_score,
                "con_score": score.con_score,
            }))
        for ph, dur in j.phase_durations.items():
            j.push_event(JobEvent("phase.finished", {"phase": ph, "duration_sec": dur}))

        # 回调（可选）
        if req.callback_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(req.callback_url, json={"job_id": j.job_id, "status": "completed"})
            except Exception:
                pass  # 回调失败不影响主流程

        return {
            "run_id": result.run_id,
            "problem": result.problem,
            "evidence_brief": result.evidence_brief.model_dump(),
            "transcript": result.transcript.model_dump(),
            "review": result.review.model_dump(),
            "judgment": result.judgment.model_dump(),
            "total_time_sec": result.total_time_sec,
        }

    await JOB_MANAGER.run_job(job, runner)

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status.value,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        stream_url=f"/api/parajudge/jobs/{job.job_id}/stream",
        result_url=f"/api/parajudge/jobs/{job.job_id}/result",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    job = JOB_MANAGER.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"job {job_id} 不存在"})

    elapsed = (job.finished_at or time.time()) - (job.started_at or time.time())
    remaining = None
    if job.status.value == "running" and job.progress > 0:
        remaining = round(elapsed * (1 - job.progress) / job.progress, 1)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        current_phase=job.current_phase,
        progress=job.progress,
        phase_durations=job.phase_durations,
        estimated_remaining_sec=remaining,
        error=job.error,
        result_url=f"/api/parajudge/jobs/{job.job_id}/result" if job.status.value == "completed" else None,
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """SSE 流式推送 job 进度。"""
    job = JOB_MANAGER.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"job {job_id} 不存在"})

    return StreamingResponse(
        stream_job_events(JOB_MANAGER, job),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """获取任务的最终结果。"""
    job = JOB_MANAGER.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": f"job {job_id} 不存在"})
    if job.status.value != "completed":
        raise HTTPException(
            status_code=409,
            detail={"code": "JOB_NOT_READY", "message": f"job 状态为 {job.status.value}，尚未完成"},
        )
    return job.result


# ============================================================
# 单阶段执行（调试 / 重跑用）
# ============================================================

@router.post("/run/phase/0")
async def run_phase0(req: Phase0Request):
    from src.debate.evidence_builder import build_evidence_brief
    brief = await asyncio.to_thread(build_evidence_brief, req.problem, req.max_papers)
    return brief.model_dump()


@router.post("/run/phase/1")
async def run_phase1(req: Phase1Request):
    from backend.models.schemas import EvidenceBrief
    from src.debate.simple_debate import SimpleDebate
    from src.writer.llm_client import LLMClient

    brief = EvidenceBrief.model_validate(req.brief)
    llm = LLMClient(provider=req.llm.provider, model=req.llm.model, api_key=req.llm.api_key)
    debate = SimpleDebate(llm, rounds=req.rounds)
    transcript = await asyncio.to_thread(debate.run, req.problem, brief)
    return transcript.model_dump()


@router.post("/run/phase/2.1")
async def run_phase21(req: Phase21Request):
    from backend.models.schemas import DebateTranscript, EvidenceBrief
    from src.judgment.review_engine import ReviewEngine
    from src.writer.llm_client import LLMClient

    brief = EvidenceBrief.model_validate(req.brief)
    transcript = DebateTranscript.model_validate(req.transcript)
    llm = LLMClient(provider=req.llm.provider, model=req.llm.model, api_key=req.llm.api_key) if req.enable_llm_check else None
    engine = ReviewEngine(llm=llm, enable_llm_check=req.enable_llm_check)
    review = await asyncio.to_thread(engine.run, transcript, brief)
    return review.model_dump()


@router.post("/run/phase/2.2")
async def run_phase22(req: Phase22Request):
    from backend.models.schemas import DebateTranscript, EvidenceBrief, ReviewReport
    from src.judgment.judgment_engine import JudgmentEngine
    from src.writer.llm_client import LLMClient

    brief = EvidenceBrief.model_validate(req.brief)
    transcript = DebateTranscript.model_validate(req.transcript)
    review = ReviewReport.model_validate(req.review)
    llm = LLMClient(provider=req.llm.provider, model=req.llm.model, api_key=req.llm.api_key)
    engine = JudgmentEngine(llm)
    judgment = await asyncio.to_thread(engine.run, transcript, brief, review)
    return judgment.model_dump()
