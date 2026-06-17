"""Server-Sent Events (SSE) 工具。

参考：https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from backend.api.job_manager import Job, JobEvent, JobManager


def _format_sse(event: str, data: dict) -> str:
    """格式化为 SSE 协议字符串。"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_job_events(jm: JobManager, job: Job) -> AsyncIterator[str]:
    """订阅 job 的事件流，转换为 SSE 字符串。"""
    q = await jm.subscribe(job.job_id)
    try:
        # 推送一次初始状态
        yield _format_sse("job.snapshot", {
            "job_id": job.job_id,
            "status": job.status.value,
            "current_phase": job.current_phase,
            "progress": job.progress,
        })
        while True:
            try:
                evt: JobEvent = await asyncio.wait_for(q.get(), timeout=15.0)
                yield _format_sse(evt.event, evt.data)
                # 终止条件
                if evt.event in ("job.completed", "job.failed", "job.cancelled"):
                    break
            except asyncio.TimeoutError:
                # 心跳保活
                yield ": heartbeat\n\n"
    finally:
        jm.unsubscribe(job.job_id, q)
