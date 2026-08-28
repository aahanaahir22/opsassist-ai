from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Approval, AuditEntry, Event, Incident
from app.schemas import ActionPlan, EventCreate, ExecutionResult

try:
    import faiss
except ImportError:  # pragma: no cover
    faiss = None


@dataclass(frozen=True)
class Chunk:
    evidence_id: str
    title: str
    service: str
    section: str
    content: str


class RunbookRetriever:
    """TF-IDF embeddings searched by a FAISS cosine-similarity index."""

    def __init__(self, runbook_dir: Path):
        self.runbook_dir = runbook_dir
        self.chunks: list[Chunk] = []
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), stop_words="english", sublinear_tf=True
        )
        self.matrix: np.ndarray | None = None
        self.index = None
        self.engine = "not_ready"

    def build(self):
        self.chunks = self._load()
        if not self.chunks:
            raise RuntimeError(f"No runbooks found in {self.runbook_dir}")
        sparse = self.vectorizer.fit_transform(
            [f"{c.service} {c.section} {c.content}" for c in self.chunks]
        )
        self.matrix = normalize(sparse).toarray().astype("float32")
        if faiss is not None:
            self.index = faiss.IndexFlatIP(self.matrix.shape[1])
            self.index.add(self.matrix)
            self.engine = "faiss.IndexFlatIP"
        else:
            self.engine = "numpy cosine fallback"

    def search(self, query: str, service: str, limit: int = 3):
        if self.matrix is None:
            self.build()
        vector = normalize(self.vectorizer.transform([query])).toarray().astype("float32")
        count = min(limit * 4, len(self.chunks))
        if self.index is not None:
            scores, indexes = self.index.search(vector, count)
            ranked = zip(indexes[0].tolist(), scores[0].tolist(), strict=True)
        else:  # pragma: no cover
            similarities = (self.matrix @ vector.T).ravel()
            order = np.argsort(similarities)[::-1][:count]
            ranked = ((int(i), float(similarities[i])) for i in order)
        results = []
        for index, score in ranked:
            if index < 0:
                continue
            chunk = self.chunks[index]
            if chunk.service not in {service, "all"}:
                continue
            results.append(
                {
                    "evidence_id": chunk.evidence_id,
                    "runbook_title": chunk.title,
                    "section": chunk.section,
                    "excerpt": chunk.content[:360],
                    "score": round(max(0.0, min(1.0, float(score))), 3),
                }
            )
            if len(results) == limit:
                break
        return results

    def _load(self):
        output = []
        for path in sorted(self.runbook_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = self._frontmatter(text)
            sections = re.split(r"^##\s+", body, flags=re.MULTILINE)
            for pos, raw in enumerate(sections):
                lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
                if not lines:
                    continue
                section = lines[0] if pos else "Overview"
                content = " ".join(lines[1:] if pos else lines)
                if len(content) < 30:
                    continue
                slug = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
                output.append(
                    Chunk(
                        f"{meta.get('id', path.stem.upper())}#{slug}",
                        meta.get("title", path.stem),
                        meta.get("service", "all"),
                        section,
                        content,
                    )
                )
        return output

    @staticmethod
    def _frontmatter(text):
        if not text.startswith("---"):
            return {}, text
        _, raw, body = text.split("---", 2)
        meta = {}
        for line in raw.strip().splitlines():
            key, _, value = line.partition(":")
            if key and value:
                meta[key.strip()] = value.strip()
        return meta, body


PLAYBOOKS = {
    "DB_TIMEOUT": (
        "PostgreSQL connection-pool exhaustion is the most likely cause: "
        "requests are waiting for a database connection after repeated "
        "acquisition timeouts.",
        0.88,
        "restart_connection_pool_workers",
        "payment-api",
        "Recycle payment API workers in a rolling sequence, then verify pool saturation.",
        {"strategy": "rolling", "max_unavailable": 1, "verify_seconds": 30},
    ),
    "UPSTREAM_503": (
        "Checkout is receiving sustained 503 responses from an upstream dependency.",
        0.81,
        "enable_circuit_breaker",
        "checkout-api",
        "Enable the approved circuit breaker and verify fallback traffic.",
        {"failure_threshold": 8, "recovery_seconds": 45},
    ),
    "MEMORY_PRESSURE": (
        "Worker memory pressure is producing repeated restarts and degraded latency.",
        0.79,
        "scale_service",
        "catalog-api",
        "Add one replica within the allow-listed capacity limit.",
        {"replica_delta": 1, "maximum_replicas": 6},
    ),
}
ALLOW_LIST = {
    "collect_diagnostics",
    "restart_connection_pool_workers",
    "enable_circuit_breaker",
    "scale_service",
}


def audit(
    session: Session,
    incident_id: str | None,
    actor: str,
    action: str,
    outcome: str,
    details=None,
):
    session.add(
        AuditEntry(
            incident_id=incident_id,
            actor=actor,
            action=action,
            outcome=outcome,
            details=details or {},
        )
    )
    session.flush()


def ingest_event(session: Session, payload: EventCreate):
    occurred = payload.occurred_at or datetime.now(timezone.utc)
    if occurred.tzinfo:
        occurred = occurred.astimezone(timezone.utc).replace(tzinfo=None)
    fingerprint = f"{payload.environment}|{payload.service}|{payload.error_code}"
    incident = session.scalar(
        select(Incident)
        .where(
            Incident.fingerprint == fingerprint,
            Incident.status.in_(["investigating", "approval_pending", "approved"]),
            Incident.last_seen >= occurred - timedelta(minutes=settings.incident_window_minutes),
        )
        .order_by(desc(Incident.last_seen))
    )
    created = incident is None
    if created:
        titles = {
            "DB_TIMEOUT": "Payment API latency after database timeouts",
            "UPSTREAM_503": "Checkout failures from upstream 503 responses",
            "MEMORY_PRESSURE": "Catalog workers restarting under memory pressure",
        }
        incident = Incident(
            fingerprint=fingerprint,
            title=titles.get(payload.error_code, f"{payload.service} service degradation"),
            service=payload.service,
            environment=payload.environment,
            severity=payload.severity,
            first_seen=occurred,
            last_seen=occurred,
        )
        session.add(incident)
        session.flush()
    order = ["low", "medium", "high", "critical"]
    incident.event_count += 1
    incident.last_seen = max(incident.last_seen, occurred)
    incident.severity = max((incident.severity, payload.severity), key=order.index)
    event = Event(
        incident_id=incident.id,
        service=payload.service,
        environment=payload.environment,
        severity=payload.severity,
        message=payload.message,
        error_code=payload.error_code,
        trace_id=payload.trace_id,
        attributes=payload.attributes,
        occurred_at=occurred,
    )
    session.add(event)
    session.flush()
    audit(
        session,
        incident.id,
        "event-ingestion",
        "incident.created" if created else "event.grouped",
        "success",
        {"fingerprint": fingerprint, "event_id": event.id},
    )
    session.commit()
    session.refresh(event)
    session.refresh(incident)
    return event, incident


def analyze(session: Session, incident: Incident, retriever: RunbookRetriever):
    query = " ".join(
        [incident.service, incident.title]
        + [f"{e.error_code} {e.message}" for e in incident.events[-5:]]
    )
    evidence = retriever.search(query, incident.service)
    code = incident.fingerprint.split("|")[-1]
    root, confidence, action_type, target, summary, params = PLAYBOOKS.get(
        code,
        (
            "Available evidence is insufficient for autonomous remediation.",
            0.56,
            "collect_diagnostics",
            incident.service,
            "Collect a bounded diagnostic bundle for human review.",
            {"window_minutes": 15},
        ),
    )
    action = ActionPlan(
        action_type=action_type,
        target=target,
        summary=summary,
        risk="sensitive" if action_type != "collect_diagnostics" else "low",
        parameters=params,
        evidence_ids=[x["evidence_id"] for x in evidence] or ["NO-EVIDENCE"],
    )
    if action.action_type not in ALLOW_LIST:
        policy = {
            "decision": "deny",
            "reason": "Action is outside the explicit allow-list.",
            "policy": "OPS-POLICY-003",
        }
    elif confidence < 0.65:
        policy = {
            "decision": "deny",
            "reason": "Confidence is below the execution threshold.",
            "policy": "OPS-POLICY-002",
        }
    elif action.risk == "sensitive":
        policy = {
            "decision": "approval_required",
            "reason": "State-changing remediation requires a named human approver.",
            "policy": "OPS-POLICY-001",
        }
    else:
        policy = {
            "decision": "allow",
            "reason": "Read-only diagnostic collection is permitted.",
            "policy": "OPS-POLICY-LOW",
        }
    incident.root_cause, incident.confidence, incident.evidence = (
        root,
        confidence,
        evidence,
    )
    incident.recommended_action, incident.policy_decision = action.model_dump(), policy
    incident.status = {
        "approval_required": "approval_pending",
        "allow": "approved",
        "deny": "needs_review",
    }[policy["decision"]]
    if (
        policy["decision"] == "approval_required"
        and session.scalar(
            select(Approval).where(
                Approval.incident_id == incident.id, Approval.status == "pending"
            )
        )
        is None
    ):
        session.add(Approval(incident_id=incident.id, action_type=action.action_type))
    audit(
        session,
        incident.id,
        "diagnosis-agent",
        "incident.analyzed",
        "success",
        {
            "confidence": confidence,
            "evidence_ids": action.evidence_ids,
            "policy_decision": policy["decision"],
        },
    )
    session.commit()
    session.refresh(incident)
    return incident


def execute(incident: Incident):
    action = ActionPlan.model_validate(incident.recommended_action)
    state = {
        "restart_connection_pool_workers": {
            "health": "healthy",
            "pool_utilization_percent": 58,
            "p95_latency_ms": 218,
        },
        "enable_circuit_breaker": {
            "health": "healthy",
            "fallback_enabled": True,
            "upstream_error_rate_percent": 1.4,
        },
        "scale_service": {
            "health": "healthy",
            "replicas": 4,
            "memory_utilization_percent": 63,
        },
        "collect_diagnostics": {"health": "degraded", "diagnostic_bundle": "captured"},
    }[action.action_type]
    return ExecutionResult(
        incident_id=incident.id,
        action_type=action.action_type,
        target=action.target,
        before_state={
            "service": action.target,
            "health": "degraded",
            "event_count": incident.event_count,
        },
        after_state={"service": action.target, **state},
        observed_outcome=(
            "Simulator verification observed the expected post-action state. "
            "No production system was contacted."
        ),
        status="verified",
    )
