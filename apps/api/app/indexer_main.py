from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import OpsAssistError
from app.schemas.models import KnowledgeSearchRequest, RetrievedChunk
from app.services.retrieval import RetrievalService, load_markdown_documents

settings = get_settings()
app = FastAPI(title="OpsAssist Semantic Indexer", version="1.0.0")
index = RetrievalService(Path(settings.index_dir))


def authorize(value: str | None) -> None:
    if settings.indexer_shared_key and value != settings.indexer_shared_key:
        raise OpsAssistError("FORBIDDEN", "Invalid indexer service credential.", 403)


@app.on_event("startup")
def startup() -> None:
    if settings.environment == "production" and not settings.indexer_shared_key:
        raise RuntimeError("OPSASSIST_INDEXER_SHARED_KEY is required in production")
    if not index.load():
        index.build(load_markdown_documents(Path(settings.data_dir) / "runbooks"), persist=True)


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "healthy", "backend": index.backend, "chunks": len(index.chunks)}


@app.post("/search", response_model=list[RetrievedChunk])
def search(body: KnowledgeSearchRequest, x_opsassist_indexer_key: str | None = Header(default=None)) -> list[RetrievedChunk]:
    authorize(x_opsassist_indexer_key)
    return index.search(body)


@app.post("/rebuild")
def rebuild(x_opsassist_indexer_key: str | None = Header(default=None)) -> dict[str, object]:
    authorize(x_opsassist_indexer_key)
    count = index.build(load_markdown_documents(Path(settings.data_dir) / "runbooks"), persist=True)
    return {"status": "promoted", "backend": index.backend, "chunks": count}


@app.exception_handler(OpsAssistError)
def opsassist_error(_request: Request, exc: OpsAssistError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
