"""异步任务管理器。

使用内存 dict 存储任务状态；如需持久化可替换为 Redis / SQLite 实现。
"""
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobEvent:
    """SSE 事件"""
    event: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Job:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    current_phase: Optional[str] = None
    progress: float = 0.0
    phase_durations: Dict[str, float] = field(default_factory=dict)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    events: List[JobEvent] = field(default_factory=list)
    _subscribers: List[asyncio.Queue] = field(default_factory=list)
    _lock: asyncio.Lock = field(default=None, repr=False)

    def push_event(self, event: JobEvent) -> None:
        """向所有订阅者广播事件；保留最近 100 条供新订阅者回放。"""
        self.events.append(event)
        if len(self.events) > 100:
            self.events = self.events[-100:]
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


class JobManager:
    """单例任务管理器"""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def create_job(self) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = Job(job_id=job_id)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list(self) -> List[Job]:
        return list(self._jobs.values())

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        """订阅一个 job 的事件流（返回异步队列）。"""
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        # 立即回放历史事件
        for ev in job.events:
            await q.put(ev)
        job._subscribers.append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        job = self.get(job_id)
        if job and q in job._subscribers:
            job._subscribers.remove(q)

    async def run_job(
        self,
        job: Job,
        runner: Callable[[Job], Awaitable[Dict[str, Any]]],
    ) -> None:
        """在后台 Task 中执行 job，由 runner 负责更新 job 状态。"""
        task = asyncio.create_task(self._wrap(job, runner))
        self._tasks[job.job_id] = task

    async def _wrap(
        self,
        job: Job,
        runner: Callable[[Job], Awaitable[Dict[str, Any]]],
    ) -> None:
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        job.push_event(JobEvent("job.started", {"run_id": job.job_id, "started_at": job.started_at}))
        try:
            result = await runner(job)
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.finished_at = time.time()
            job.push_event(JobEvent("job.completed", {
                "result_url": f"/api/parajudge/jobs/{job.job_id}/result",
                "total_time_sec": round(job.finished_at - (job.started_at or job.finished_at), 2),
            }))
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.push_event(JobEvent("job.cancelled", {"job_id": job.job_id}))
        except Exception as e:  # noqa: BLE001
            import traceback
            job.status = JobStatus.FAILED
            job.error = {"code": "INTERNAL_ERROR", "message": str(e), "traceback": traceback.format_exc()}
            job.finished_at = time.time()
            job.push_event(JobEvent("job.failed", job.error))

    def cancel(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def stats(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in JobStatus}
        for j in self._jobs.values():
            counts[j.status.value] = counts.get(j.status.value, 0) + 1
        return counts


# 全局单例
JOB_MANAGER = JobManager()
