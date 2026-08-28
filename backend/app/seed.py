from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import SessionLocal, init_db
from app.engine import RunbookRetriever, analyze, ingest_event
from app.models import Approval, AuditEntry, Event, Incident
from app.schemas import EventCreate


def reset_and_seed(session: Session, retriever: RunbookRetriever):
    for model in (AuditEntry, Approval, Event, Incident):
        session.execute(delete(model))
    session.commit()
    start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=7)
    rows = [
        (
            "high",
            "Timed out acquiring PostgreSQL connection after 2000 ms",
            "tr_7ef029a1",
            {"pool_active": 40, "pool_max": 40, "p95_ms": 1840},
        ),
        (
            "critical",
            "Checkout authorization failed: database pool acquisition timeout",
            "tr_7ef029d4",
            {"pool_active": 40, "pool_max": 40, "error_rate": 0.184},
        ),
        (
            "critical",
            "Repeated database connection timeouts; payment latency SLO breached",
            "tr_7ef02ab9",
            {"pool_waiters": 126, "p95_ms": 2310, "slo_breached": True},
        ),
    ]
    incident = None
    for i, (severity, message, trace, attrs) in enumerate(rows):
        _, incident = ingest_event(
            session,
            EventCreate(
                service="payment-api",
                environment="production",
                severity=severity,
                message=message,
                error_code="DB_TIMEOUT",
                trace_id=trace,
                attributes=attrs,
                occurred_at=start + timedelta(minutes=2 * i),
            ),
        )
    incident = session.scalar(
        select(Incident).where(Incident.id == incident.id).options(selectinload(Incident.events))
    )
    return analyze(session, incident, retriever)


def seed_if_empty(session: Session, retriever: RunbookRetriever):
    if session.scalar(select(Incident.id).limit(1)) is None:
        return reset_and_seed(session, retriever)


def main():
    init_db()
    retriever = RunbookRetriever(settings.runbook_dir)
    retriever.build()
    with SessionLocal() as session:
        incident = reset_and_seed(session, retriever)
    print(f"Seeded {incident.id}: {incident.title}")


if __name__ == "__main__":
    main()
