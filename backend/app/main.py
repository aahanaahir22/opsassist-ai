from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import perf_counter

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import SessionLocal, get_session, init_db
from app.engine import RunbookRetriever, analyze, audit, execute, ingest_event
from app.models import Approval, AuditEntry, Incident
from app.schemas import (
    ApprovalDecision,
    ApprovalRead,
    AuditRead,
    DashboardSummary,
    EventCreate,
    EventRead,
    ExecutionResult,
    IncidentDetail,
    IncidentRead,
)
from app.seed import reset_and_seed, seed_if_empty

retriever = RunbookRetriever(settings.runbook_dir)


@asynccontextmanager
async def lifespan(_):
    init_db()
    retriever.build()
    if settings.seed_demo:
        with SessionLocal() as session:
            seed_if_empty(session, retriever)
    yield


app = FastAPI(
    title="OpsAssist AI",
    version="1.0.0",
    description="Evidence-backed incident diagnosis with policy-gated, simulated remediation.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def auth(x_api_key: str | None = Header(default=None)):
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(401, "Missing or invalid API key")


@app.middleware("http")
async def headers(request: Request, call_next):
    started = perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = f"{(perf_counter() - started) * 1000:.2f}"
    response.headers["X-OpsAssist-Mode"] = "simulated-prototype"
    return response


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "OpsAssist AI",
        "version": "1.0.0",
        "retrieval_engine": retriever.engine,
        "execution_mode": "simulated",
    }


@app.get("/api/v1/dashboard", response_model=DashboardSummary, dependencies=[Depends(auth)])
def dashboard(session: Session = Depends(get_session)):
    analyzed = list(session.scalars(select(Incident).where(Incident.root_cause.is_not(None))))
    return DashboardSummary(
        open_incidents=session.scalar(
            select(func.count()).select_from(Incident).where(Incident.status != "resolved")
        )
        or 0,
        critical_incidents=session.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.status != "resolved", Incident.severity == "critical")
        )
        or 0,
        pending_approvals=session.scalar(
            select(func.count()).select_from(Approval).where(Approval.status == "pending")
        )
        or 0,
        resolved_today=sum(
            1
            for x in session.scalars(select(Incident).where(Incident.status == "resolved"))
            if x.updated_at.date() == datetime.now(timezone.utc).date()
        ),
        retrieval_engine=retriever.engine,
        evidence_coverage=round(sum(bool(x.evidence) for x in analyzed) / len(analyzed), 2)
        if analyzed
        else 1.0,
    )


@app.post(
    "/api/v1/events",
    response_model=EventRead,
    status_code=201,
    dependencies=[Depends(auth)],
)
def create_event(payload: EventCreate, session: Session = Depends(get_session)):
    return ingest_event(session, payload)[0]


@app.get("/api/v1/incidents", response_model=list[IncidentRead], dependencies=[Depends(auth)])
def incidents(status: str | None = None, session: Session = Depends(get_session)):
    query = select(Incident).order_by(desc(Incident.last_seen))
    return list(session.scalars(query.where(Incident.status == status) if status else query))


@app.get(
    "/api/v1/incidents/{incident_id}",
    response_model=IncidentDetail,
    dependencies=[Depends(auth)],
)
def incident_detail(incident_id: str, session: Session = Depends(get_session)):
    item = session.scalar(
        select(Incident).where(Incident.id == incident_id).options(selectinload(Incident.events))
    )
    if not item:
        raise HTTPException(404, "Incident not found")
    return item


@app.post(
    "/api/v1/incidents/{incident_id}/analyze",
    response_model=IncidentRead,
    dependencies=[Depends(auth)],
)
def analyze_route(incident_id: str, session: Session = Depends(get_session)):
    item = session.scalar(
        select(Incident).where(Incident.id == incident_id).options(selectinload(Incident.events))
    )
    if not item:
        raise HTTPException(404, "Incident not found")
    return analyze(session, item, retriever)


@app.get("/api/v1/approvals", response_model=list[ApprovalRead], dependencies=[Depends(auth)])
def approvals(session: Session = Depends(get_session)):
    return list(session.scalars(select(Approval).order_by(desc(Approval.created_at))))


@app.post(
    "/api/v1/approvals/{approval_id}/decision",
    response_model=ApprovalRead,
    dependencies=[Depends(auth)],
)
def decide(approval_id: str, payload: ApprovalDecision, session: Session = Depends(get_session)):
    item = session.get(Approval, approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    if item.status != "pending":
        raise HTTPException(409, "Approval was already decided")
    item.status, item.decided_by, item.reason = (
        payload.decision,
        payload.decided_by,
        payload.reason,
    )
    item.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    incident = session.get(Incident, item.incident_id)
    incident.status = "approved" if payload.decision == "approved" else "needs_review"
    audit(
        session,
        item.incident_id,
        payload.decided_by,
        "approval.decided",
        payload.decision,
        {"approval_id": item.id, "reason": payload.reason},
    )
    session.commit()
    session.refresh(item)
    return item


@app.post(
    "/api/v1/incidents/{incident_id}/execute",
    response_model=ExecutionResult,
    dependencies=[Depends(auth)],
)
def execute_route(incident_id: str, session: Session = Depends(get_session)):
    incident = session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    if not incident.recommended_action:
        raise HTTPException(409, "Analyze the incident before execution")
    if (
        incident.policy_decision.get("decision") == "approval_required"
        and session.scalar(
            select(Approval).where(
                Approval.incident_id == incident.id, Approval.status == "approved"
            )
        )
        is None
    ):
        raise HTTPException(409, "Human approval is required")
    result = execute(incident)
    incident.status = "resolved"
    audit(
        session,
        incident.id,
        "controlled-executor",
        "remediation.executed",
        "verified",
        result.model_dump(),
    )
    session.commit()
    return result


@app.get("/api/v1/audit", response_model=list[AuditRead], dependencies=[Depends(auth)])
def audit_list(
    incident_id: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    query = select(AuditEntry).order_by(desc(AuditEntry.created_at)).limit(limit)
    return list(
        session.scalars(
            query.where(AuditEntry.incident_id == incident_id) if incident_id else query
        )
    )


@app.post("/api/v1/demo/reset", response_model=IncidentRead, dependencies=[Depends(auth)])
def demo_reset(session: Session = Depends(get_session)):
    return reset_and_seed(session, retriever)
