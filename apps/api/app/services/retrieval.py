from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import faiss  # type: ignore[import-not-found]
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
except ImportError:  # The transparent TF-IDF backend keeps the offline demo runnable.
    faiss = None
    SentenceTransformer = None

from app.core.errors import OpsAssistError
from app.schemas.models import KnowledgeDocumentIn, KnowledgeSearchRequest, RetrievedChunk


INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|the) previous instructions", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"reveal .*secret", re.I),
    re.compile(r"execute .*command", re.I),
]


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    document_version: str
    section: str
    content: str
    service_ids: list[str]
    document_type: str
    trust_level: str
    created_at: str
    checksum: str


def detect_prompt_injection(text: str) -> list[str]:
    return [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]


class RetrievalService:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix: Any = None
        self.faiss_index: Any = None
        self.embedding_model: Any = None
        self.backend = "tfidf"

    def chunk_document(self, document: KnowledgeDocumentIn, words: int = 90, overlap: int = 20) -> list[Chunk]:
        tokens = document.content.split()
        chunks: list[Chunk] = []
        cursor = 0
        part = 1
        while cursor < len(tokens):
            content = " ".join(tokens[cursor : cursor + words])
            checksum = hashlib.sha256(content.encode()).hexdigest()
            chunks.append(Chunk(
                chunk_id=f"{document.document_id}-v{document.version}-chunk-{part}",
                document_id=document.document_id,
                document_version=document.version,
                section=str(part),
                content=content,
                service_ids=document.service_ids,
                document_type=document.document_type,
                trust_level=document.trust_level,
                created_at=datetime.now(UTC).isoformat(),
                checksum=checksum,
            ))
            cursor += max(1, words - overlap)
            part += 1
        return chunks

    def build(self, documents: list[KnowledgeDocumentIn], persist: bool = False) -> int:
        self.chunks = [chunk for document in documents for chunk in self.chunk_document(document)]
        if not self.chunks:
            return 0
        requested_backend = os.getenv("OPSASSIST_EMBEDDING_BACKEND", "tfidf")
        if requested_backend == "sentence_transformer":
            if SentenceTransformer is None or faiss is None:
                raise RuntimeError("sentence-transformers and faiss-cpu are required for the semantic backend")
            model_name = os.getenv("OPSASSIST_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            vectors = np.asarray(self.embedding_model.encode([chunk.content for chunk in self.chunks], normalize_embeddings=True), dtype="float32")
            self.faiss_index = faiss.IndexFlatIP(vectors.shape[1])
            self.faiss_index.add(vectors)
            self.backend = "sentence_transformer_faiss"
        else:
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
            self.matrix = self.vectorizer.fit_transform([chunk.content for chunk in self.chunks])
            self.backend = "tfidf"
        if persist:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            (self.index_dir / "chunks.json").write_text(json.dumps([asdict(item) for item in self.chunks], indent=2))
            (self.index_dir / "manifest.json").write_text(json.dumps({"backend": self.backend, "chunks": len(self.chunks)}, indent=2))
            if self.faiss_index is not None:
                faiss.write_index(self.faiss_index, str(self.index_dir / "faiss.index"))
        return len(self.chunks)

    def load(self) -> bool:
        path = self.index_dir / "chunks.json"
        if not path.exists():
            return False
        self.chunks = [Chunk(**item) for item in json.loads(path.read_text())]
        manifest_path = self.index_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"backend": "tfidf"}
        if manifest.get("backend") == "sentence_transformer_faiss":
            if SentenceTransformer is None or faiss is None:
                raise RuntimeError("The persisted index requires sentence-transformers and faiss-cpu")
            model_name = os.getenv("OPSASSIST_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            self.faiss_index = faiss.read_index(str(self.index_dir / "faiss.index"))
            self.backend = "sentence_transformer_faiss"
            return True
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform([chunk.content for chunk in self.chunks])
        self.backend = "tfidf"
        return True

    def search(self, request: KnowledgeSearchRequest) -> list[RetrievedChunk]:
        matches = detect_prompt_injection(request.query)
        if matches:
            raise OpsAssistError("PROMPT_INJECTION_BLOCKED", "The query matched prompt-injection policy.", 400, {"matches": matches})
        if not self.chunks and not self.load():
            return []
        if self.backend == "sentence_transformer_faiss":
            vector = np.asarray(self.embedding_model.encode([request.query], normalize_embeddings=True), dtype="float32")
            semantic_scores, semantic_indices = self.faiss_index.search(vector, len(self.chunks))
            ranked = [(int(index), float(score)) for index, score in zip(semantic_indices[0], semantic_scores[0], strict=True) if index >= 0]
        else:
            assert self.vectorizer is not None and self.matrix is not None
            query_vector = self.vectorizer.transform([request.query])
            scores = np.asarray((self.matrix @ query_vector.T).toarray()).reshape(-1)
            ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)
        results: list[RetrievedChunk] = []
        for index, score in ranked:
            chunk = self.chunks[index]
            if request.service_ids and not set(request.service_ids).intersection(chunk.service_ids):
                continue
            if chunk.trust_level not in request.trust_levels:
                continue
            if score <= 0:
                continue
            results.append(RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_version=chunk.document_version,
                section=chunk.section,
                content=chunk.content,
                retrieval_score=round(float(score), 4),
                trust_level=chunk.trust_level,
                metadata={"services": chunk.service_ids, "document_type": chunk.document_type, "checksum": chunk.checksum},
            ))
            if len(results) >= request.limit:
                break
        return results


def load_markdown_documents(runbook_dir: Path) -> list[KnowledgeDocumentIn]:
    documents: list[KnowledgeDocumentIn] = []
    for path in sorted(runbook_dir.glob("*.md")):
        content = path.read_text()
        header, _, body = content.partition("\n---\n")
        metadata: dict[str, str] = {}
        for line in header.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        documents.append(KnowledgeDocumentIn(
            document_id=metadata.get("document_id", path.stem),
            version=metadata.get("version", "1.0"),
            title=metadata.get("title", path.stem.replace("_", " ").title()),
            content=body or content,
            service_ids=[item.strip() for item in metadata.get("services", "").split(",") if item.strip()],
            document_type=metadata.get("type", "runbook"),
            trust_level=metadata.get("trust", "reviewed"),
        ))
    return documents
