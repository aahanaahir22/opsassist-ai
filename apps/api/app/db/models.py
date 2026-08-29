from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("usr"))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("role"))
    name: Mapped[str] = mapped_column(String(80), unique=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)


class Service(Base, TimestampMixin):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class Dependency(Base):
    __tablename__ = "dependencies"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("dep"))
    source_id: Mapped[str] = mapped_column(ForeignKey("services.id"), index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("services.id"), index=True)
    kind: Mapped[str] = mapped_column(String(80), default="synchronous")
    __table_args__ = (UniqueConstraint("source_id", "target_id", name="uq_dependency_edge"),)


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("tel"))
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"), index=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (Index("ix_telemetry_service_time", "service_id", "timestamp"),)


class LogEvent(Base):
    __tablename__ = "log_events"
    id: Mapped[str] = mapped_column(ForeignKey("telemetry_events.id"), primary_key=True)
    message: Mapped[str] = mapped_column(Text)
    normalized_template: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), index=True)


class MetricPoint(Base):
    __tablename__ = "metric_points"
    id: Mapped[str] = mapped_column(ForeignKey("telemetry_events.id"), primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(160), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(40))


class TraceSpan(Base):
    __tablename__ = "trace_spans"
    id: Mapped[str] = mapped_column(ForeignKey("telemetry_events.id"), primary_key=True)
    span_id: Mapped[str] = mapped_column(String(128), index=True)
    parent_span_id: Mapped[str | None] = mapped_column(String(128))
    operation: Mapped[str] = mapped_column(String(160))
    duration_ms: Mapped[float] = mapped_column(Float)


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"
    id: Mapped[str] = mapped_column(ForeignKey("telemetry_events.id"), primary_key=True)
    version_from: Mapped[str] = mapped_column(String(80))
    version_to: Mapped[str] = mapped_column(String(80))
    commit_sha: Mapped[str] = mapped_column(String(80), index=True)


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("alt"))
    fingerprint: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"))
    count: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSON)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("inc"))
    scenario_id: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), index=True, default="OPEN")
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    seed: Mapped[int] = mapped_column(Integer)
    state: Mapped[dict] = mapped_column(JSON, default=dict)


class IncidentChildMixin(TimestampMixin):
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)


class Evidence(Base, IncidentChildMixin):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ev"))
    kind: Mapped[str] = mapped_column(String(40))
    source_id: Mapped[str] = mapped_column(String(160), index=True)
    stance: Mapped[str] = mapped_column(String(24))
    reliability: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)


class Hypothesis(Base, IncidentChildMixin):
    __tablename__ = "hypotheses"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    label: Mapped[str] = mapped_column(String(240))
    score: Mapped[float] = mapped_column(Float, index=True)
    components: Mapped[dict] = mapped_column(JSON)


class AgentRun(Base, IncidentChildMixin):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("agent"))
    agent_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40))
    output: Mapped[dict] = mapped_column(JSON)


class Runbook(Base, TimestampMixin):
    __tablename__ = "runbooks"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    trust_level: Mapped[str] = mapped_column(String(40), index=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(80), index=True)
    document_version: Mapped[str] = mapped_column(String(40))
    section: Mapped[str] = mapped_column(String(80))
    content: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64), unique=True)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class ProposedAction(Base, IncidentChildMixin):
    __tablename__ = "proposed_actions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("act"))
    action_type: Mapped[str] = mapped_column(String(80))
    target_service: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(40))
    parameters: Mapped[dict] = mapped_column(JSON)


class SimulationRun(Base, IncidentChildMixin):
    __tablename__ = "simulation_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("sim"))
    action_id: Mapped[str] = mapped_column(ForeignKey("proposed_actions.id"))
    seed: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSON)


class Approval(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("apr"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id"), index=True)
    actor_id: Mapped[str] = mapped_column(String(120))
    actor_role: Mapped[str] = mapped_column(String(80))
    signature: Mapped[str] = mapped_column(String(64), unique=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Execution(Base, IncidentChildMixin):
    __tablename__ = "executions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("exe"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id"))
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    state: Mapped[str] = mapped_column(String(40), index=True)
    result: Mapped[dict] = mapped_column(JSON)


class Verification(Base, IncidentChildMixin):
    __tablename__ = "verifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ver"))
    execution_id: Mapped[str] = mapped_column(ForeignKey("executions.id"), unique=True)
    windows_observed: Mapped[int] = mapped_column(Integer)
    criteria: Mapped[dict] = mapped_column(JSON)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("aud"))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    detail: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)


class Postmortem(Base, IncidentChildMixin):
    __tablename__ = "postmortems"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("pm"))
    content: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("eval"))
    dataset_version: Mapped[str] = mapped_column(String(40), index=True)
    seed: Mapped[int] = mapped_column(Integer)
    git_commit: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)
