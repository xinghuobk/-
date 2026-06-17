"""ParaJudge FastAPI 应用入口。

启动方式：
    uvicorn backend.api.server:app --reload --port 8000

OpenAPI 文档：
    http://localhost:8000/docs
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from backend.api.routers import health, parajudge, judges, examples

logger = logging.getLogger("parajudge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

app = FastAPI(
    title="ParaJudge API",
    description="多智能体辩论与裁决系统的 HTTP 接口",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS（默认开放，生产可收紧白名单）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Job-Id", "X-Trace-Id"],
)

# 路由注册
app.include_router(health.router)
app.include_router(parajudge.router)
app.include_router(judges.router)
app.include_router(examples.router)


# 统一错误处理
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {
            "code": "INVALID_ARGUMENT",
            "message": "请求参数校验失败",
            "details": exc.errors(),
        }},
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    import traceback
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {
            "code": "INTERNAL_ERROR",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }},
    )


# 静态资源（前端）
import os
_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
    logger.info("Frontend mounted at /ui → %s", _FRONTEND_DIR)


@app.get("/", tags=["root"])
async def root():
    return {
        "name": "ParaJudge",
        "version": "0.1.0",
        "docs": "/docs",
        "ui": "/ui/index.html" if os.path.isdir(_FRONTEND_DIR) else None,
        "endpoints": {
            "health": "/api/health",
            "version": "/api/version",
            "parajudge_sync": "POST /api/parajudge/run",
            "parajudge_async": "POST /api/parajudge/jobs",
            "judges": "GET /api/judges",
            "examples": "GET /api/examples/questions",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.server:app", host="0.0.0.0", port=8000, reload=True)
