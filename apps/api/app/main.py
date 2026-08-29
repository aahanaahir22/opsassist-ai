from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import router
from app.core.config import get_settings
from app.core.errors import OpsAssistError
from app.core.logging import configure_logging
from app.db.base import create_schema


settings = get_settings()
configure_logging()
logger = logging.getLogger("opsassist.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.ai_mode not in {"offline", "ollama", "openai_compatible"}:
        raise RuntimeError(f"Unsupported AI mode: {settings.ai_mode}")
    create_schema()
    logger.info("startup complete", extra={"event_type": "system.ready"})
    yield


app = FastAPI(
    title="OpsAssist AI API",
    description="Evidence-backed incident intelligence over versioned synthetic datasets. Simulator only.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "X-Request-ID"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:16]}")
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled request error", extra={"request_id": request_id})
        raise
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(OpsAssistError)
async def opsassist_error(request: Request, exc: OpsAssistError) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:16]}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "request_id": request_id, "details": exc.details}},
    )


@app.exception_handler(ValueError)
async def validation_error(request: Request, exc: ValueError) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:16]}")
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_INPUT", "message": str(exc), "request_id": request_id, "details": {}}},
    )
