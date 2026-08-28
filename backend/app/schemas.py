from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    service: str = Field(min_length=2, max_length=80)
    environment: str = "production"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    message: str = Field(min_length=4, max_length=4000)
    error_code: str = Field(min_length=2, max_length=80)
    trace_id: str | None = None
    attributes: dict = Field(default_factory=dict)
    occurred_at: datetime | None = None


class EventRead(EventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_id: str
    occurred_at: datetime


class ActionPlan(BaseModel):
    action_type: str
    target: str
    summary: str
    risk: Literal["low", "sensitive", "prohibited"]
    parameters: dict = Field(default_factory=dict)
    evidence_ids: list[str] = Field(min_length=1)


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    service: str
    environment: str
    severity: str
    status: str
    event_count: int
    first_seen: datetime
    last_seen: datetime
    root_cause: str | None
    confidence: float | None
    evidence: list[dict]
    recommended_action: dict | None
    policy_decision: dict | None
    created_at: datetime
    updated_at: datetime


class IncidentDetail(IncidentRead):
    events: list[EventRead]


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_id: str
    action_type: str
    status: str
    requested_by: str
    decided_by: str | None
    reason: str | None
    created_at: datetime
    decided_at: datetime | None


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    decided_by: str = Field(min_length=2)
    reason: str = Field(min_length=3)


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_id: str | None
    actor: str
    action: str
    outcome: str
    details: dict
    created_at: datetime


class DashboardSummary(BaseModel):
    open_incidents: int
    critical_incidents: int
    pending_approvals: int
    resolved_today: int
    retrieval_engine: str
    evidence_coverage: float


class ExecutionResult(BaseModel):
    incident_id: str
    action_type: str
    target: str
    before_state: dict
    after_state: dict
    observed_outcome: str
    status: str
