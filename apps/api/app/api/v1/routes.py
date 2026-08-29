from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError, OpsAssistError
from app.db.base import get_session
from app.db.models import AuditEvent, EvaluationRun, Incident, Postmortem, Runbook, Service, TelemetryEvent
from app.schemas.models import (
    ActionRequest,
    ApprovalRecord,
    ApprovalRequest,
    AuditRecord,
    EvaluationReport,
    EventType,
    ExecuteRequest,
    ExecutionResult,
    IncidentDetail,
    IncidentSummary,
    InvestigateResponse,
    KnowledgeDocumentIn,
    KnowledgeSearchRequest,
    PostmortemDocument,
    PostmortemPatch,
    RetrievedChunk,
    ScenarioRequest,
    SimulationResult,
    TelemetryEventIn,
    VerificationResult,
)
from app.services.events import EventBroker
from app.services.policy import PolicyEngine
from app.services.retrieval import RetrievalService, load_markdown_documents
from app.services.workflow import WorkflowService


router = APIRouter()
events = EventBroker()
_requests: dict[str, deque[datetime]] = defaultdict(deque)


def workflow(session: Annotated[Session, Depends(get_session)], settings: Annotated[Settings, Depends(get_settings)]) -> WorkflowService:
    return WorkflowService(session, settings)


def rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = datetime.now(UTC)
    window = _requests[client]
    while window and window[0] < now - timedelta(minutes=1):
        window.popleft()
    if len(window) >= 120:
        raise OpsAssistError("RATE_LIMITED", "Telemetry ingestion limit exceeded.", 429)
    window.append(now)


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "opsassist-api", "mode": "synthetic-simulator"}


@router.get("/ready", tags=["system"])
def ready(session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}


def _ingest_telemetry(event_type: EventType, body: TelemetryEventIn, session: Session) -> dict[str, Any]:
    service = session.get(Service, body.service_id)
    if not service:
        service = Service(id=body.service_id, name=body.service_id.replace("_", " ").title(), synthetic=True)
        session.add(service)
        session.flush()
    event = TelemetryEvent(
        event_type=event_type.value,
        service_id=body.service_id,
        trace_id=body.trace_id,
        timestamp=body.timestamp,
        payload=body.payload,
    )
    session.add(event)
    session.commit()
    return {"id": event.id, "accepted": True, "synthetic": True}


@router.post("/telemetry/logs", tags=["telemetry"], dependencies=[Depends(rate_limit)])
def ingest_logs(body: TelemetryEventIn, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return _ingest_telemetry(EventType.LOG, body, session)


@router.post("/telemetry/metrics", tags=["telemetry"], dependencies=[Depends(rate_limit)])
def ingest_metrics(body: TelemetryEventIn, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return _ingest_telemetry(EventType.METRIC, body, session)


@router.post("/telemetry/traces", tags=["telemetry"], dependencies=[Depends(rate_limit)])
def ingest_traces(body: TelemetryEventIn, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return _ingest_telemetry(EventType.TRACE, body, session)


@router.post("/telemetry/deployments", tags=["telemetry"], dependencies=[Depends(rate_limit)])
def ingest_deployments(body: TelemetryEventIn, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return _ingest_telemetry(EventType.DEPLOYMENT, body, session)


@router.post("/incidents/simulate", response_model=IncidentDetail, tags=["incidents"])
async def simulate_incident(body: ScenarioRequest, service: Annotated[WorkflowService, Depends(workflow)]) -> IncidentDetail:
    try:
        incident = service.create_incident(body.scenario_id, body.seed or service.settings.scenario_seed)
    except FileNotFoundError as exc:
        raise NotFoundError("Scenario", body.scenario_id) from exc
    await events.publish("incident.created", incident.id, incident.model_dump(mode="json"))
    return incident


@router.get("/incidents", response_model=list[IncidentSummary], tags=["incidents"])
def list_incidents(service: Annotated[WorkflowService, Depends(workflow)]) -> list[IncidentSummary]:
    return service.list_incidents()


@router.get("/incidents/{incident_id}", response_model=IncidentDetail, tags=["incidents"])
def get_incident(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> IncidentDetail:
    return service.detail(incident_id)


@router.post("/incidents/{incident_id}/investigate", response_model=InvestigateResponse, tags=["incidents"])
async def investigate(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> InvestigateResponse:
    async def publish(event_type: str, data: dict) -> None:
        await events.publish(event_type, incident_id, data)

    incident = await service.investigate(incident_id, publish)
    return InvestigateResponse(incident=incident, stream_url=f"/api/v1/events?incident_id={incident_id}")


@router.get("/incidents/{incident_id}/evidence", tags=["incidents"])
def incident_evidence(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> Any:
    return service.detail(incident_id).evidence


@router.get("/incidents/{incident_id}/hypotheses", tags=["incidents"])
def incident_hypotheses(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> Any:
    return service.detail(incident_id).hypotheses


@router.get("/incidents/{incident_id}/timeline", tags=["incidents"])
def incident_timeline(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> Any:
    return service.detail(incident_id).timeline


@router.post("/incidents/{incident_id}/simulate-action", response_model=SimulationResult, tags=["actions"])
async def simulate_action(incident_id: str, body: ActionRequest, service: Annotated[WorkflowService, Depends(workflow)]) -> SimulationResult:
    result = service.simulate_action(incident_id, body)
    await events.publish("simulation.completed", incident_id, result.model_dump(mode="json"))
    return result


@router.post("/incidents/{incident_id}/approve", response_model=ApprovalRecord, tags=["actions"])
async def approve_action(incident_id: str, body: ApprovalRequest, service: Annotated[WorkflowService, Depends(workflow)]) -> ApprovalRecord:
    record = service.policy.approve(body.simulation_id, body.actor_id, body.actor_role, body.acknowledgement)
    service.approve(incident_id, record)
    await events.publish("approval.recorded", incident_id, record.model_dump(mode="json"))
    return record


@router.post("/incidents/{incident_id}/execute", response_model=ExecutionResult, tags=["actions"])
async def execute_action(
    incident_id: str,
    body: ExecuteRequest,
    service: Annotated[WorkflowService, Depends(workflow)],
    idempotency_header: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ExecutionResult:
    result = service.execute(incident_id, body.simulation_id, body.approval_id, idempotency_header or body.idempotency_key)
    await events.publish("execution.completed", incident_id, result.model_dump(mode="json"))
    return result


@router.post("/incidents/{incident_id}/verify", response_model=VerificationResult, tags=["actions"])
async def verify_action(incident_id: str, execution_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> VerificationResult:
    result = service.verify(incident_id, execution_id)
    await events.publish("incident.recovered", incident_id, result.model_dump(mode="json"))
    return result


def retrieval(settings: Settings) -> RetrievalService:
    service = RetrievalService(Path(settings.data_dir) / "indexes")
    if not service.load():
        service.build(load_markdown_documents(Path(settings.data_dir) / "runbooks"))
    return service


@router.post("/knowledge/documents", tags=["knowledge"])
def add_document(
    body: KnowledgeDocumentIn,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> dict[str, Any]:
    session.merge(Runbook(id=body.document_id, version=body.version, title=body.title, content=body.content, trust_level=body.trust_level))
    session.commit()
    service = retrieval(settings)
    count = service.build([body], persist=False)
    return {"accepted": True, "chunks": count, "note": "Use build_index.py to persist a complete versioned index."}


@router.post("/knowledge/search", response_model=list[RetrievedChunk], tags=["knowledge"])
def search_knowledge(body: KnowledgeSearchRequest, settings: Annotated[Settings, Depends(get_settings)]) -> list[RetrievedChunk]:
    return retrieval(settings).search(body)


@router.get("/knowledge/documents", tags=["knowledge"])
def list_documents(settings: Annotated[Settings, Depends(get_settings)]) -> list[dict[str, Any]]:
    return [item.model_dump() for item in load_markdown_documents(Path(settings.data_dir) / "runbooks")]


@router.get("/evaluations", response_model=EvaluationReport, tags=["evaluation"])
def get_evaluations(settings: Annotated[Settings, Depends(get_settings)]) -> EvaluationReport:
    path = Path(settings.data_dir) / "evaluation" / "latest.json"
    if not path.exists():
        raise NotFoundError("Evaluation artifact", "latest.json")
    return EvaluationReport.model_validate_json(path.read_text())


@router.get("/system/topology", tags=["system"])
def topology(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    path = Path(settings.data_dir) / "scenarios" / "checkout_pool_exhaustion" / "topology.json"
    return json.loads(path.read_text())


@router.get("/incidents/{incident_id}/postmortem", response_model=PostmortemDocument, tags=["postmortem"])
def get_postmortem(incident_id: str, service: Annotated[WorkflowService, Depends(workflow)]) -> PostmortemDocument:
    return service.postmortem(incident_id)


@router.patch("/incidents/{incident_id}/postmortem", response_model=PostmortemDocument, tags=["postmortem"])
def patch_postmortem(
    incident_id: str,
    body: PostmortemPatch,
    session: Annotated[Session, Depends(get_session)],
    service: Annotated[WorkflowService, Depends(workflow)],
) -> PostmortemDocument:
    current = service.postmortem(incident_id)
    updated = current.model_copy(update={key: value for key, value in body.model_dump().items() if value is not None})
    row = session.scalar(select(Postmortem).where(Postmortem.incident_id == incident_id))
    if not row:
        raise NotFoundError("Postmortem", incident_id)
    row.content = updated.model_dump(mode="json")
    row.version += 1
    session.add(AuditEvent(incident_id=incident_id, event_type="postmortem.updated", actor="editor", detail={"version": row.version}))
    session.commit()
    return updated


@router.get("/incidents/{incident_id}/audit", response_model=list[AuditRecord], tags=["audit"])
def audit(incident_id: str, session: Annotated[Session, Depends(get_session)]) -> list[AuditRecord]:
    if not session.get(Incident, incident_id):
        raise NotFoundError("Incident", incident_id)
    records = session.scalars(select(AuditEvent).where(AuditEvent.incident_id == incident_id).order_by(AuditEvent.created_at)).all()
    return [AuditRecord(id=item.id.split("_")[-1].ljust(32, "0")[:32], incident_id=item.incident_id, event_type=item.event_type, actor=item.actor, detail=item.detail, created_at=item.created_at) for item in records]


@router.websocket("/events")
async def websocket_events(socket: WebSocket, incident_id: str) -> None:
    await events.connect(incident_id, socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        events.disconnect(incident_id, socket)
