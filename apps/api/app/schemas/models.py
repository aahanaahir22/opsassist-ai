from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EventType(StrEnum):
    LOG = "log"
    METRIC = "metric"
    TRACE = "trace"
    DEPLOYMENT = "deployment"


class ActionType(StrEnum):
    ROLLBACK = "rollback_deployment"
    RESTART = "restart_service"
    SCALE = "scale_replicas"
    INCREASE_POOL = "increase_connection_pool"
    DISABLE_INTEGRATION = "disable_downstream_integration"
    DELETE_DATABASE = "delete_database"


class ExecutionState(StrEnum):
    PROPOSED = "PROPOSED"
    SIMULATED = "SIMULATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    BLOCKED = "BLOCKED"


class TelemetryEventIn(Model):
    service_id: str = Field(min_length=1, max_length=80)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str | None = None
    payload: dict[str, Any]


class AnomalyResult(Model):
    detector: str
    metric: str
    service_id: str
    timestamp: datetime
    observed_value: float
    baseline_value: float
    score: float
    threshold: float
    is_anomaly: bool
    explanation: str


class Evidence(Model):
    id: str
    kind: str
    label: str
    source_id: str
    timestamp: datetime
    reliability: float = Field(ge=0, le=1)
    stance: Literal["supports", "contradicts", "neutral"]
    excerpt: str
    explanation: str


class RankingComponents(Model):
    temporal_precedence: float
    anomaly_severity: float
    dependency_centrality: float
    trace_relationship: float
    deployment_proximity: float
    historical_similarity: float
    runbook_relevance: float
    agent_agreement: float
    contradiction_penalty: float


class RankedHypothesis(Model):
    hypothesis_id: str
    label: str
    score: float
    rank: int = 0
    components: RankingComponents
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    uncertainty: float


class AgentFinding(Model):
    agent_name: str
    task: str
    input_references: list[str]
    evidence_ids: list[str]
    finding: str
    proposed_hypothesis: str | None = None
    confidence: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)
    contradictions: list[str] = []
    duration_ms: int
    status: Literal["completed", "partial", "failed"]
    error: str | None = None


class IncidentSummary(Model):
    id: str
    scenario_id: str
    title: str
    status: str
    synthetic: bool = True
    created_at: datetime
    updated_at: datetime


class IncidentDetail(IncidentSummary):
    anomalies: list[AnomalyResult] = []
    evidence: list[Evidence] = []
    hypotheses: list[RankedHypothesis] = []
    agent_findings: list[AgentFinding] = []
    timeline: list[dict[str, Any]] = []


class ScenarioRequest(Model):
    scenario_id: str = "checkout_pool_exhaustion"
    seed: int | None = None


class InvestigateResponse(Model):
    incident: IncidentDetail
    stream_url: str


class ActionRequest(Model):
    action_type: ActionType
    target_service: str
    parameters: dict[str, Any] = {}
    seed: int | None = None


class SimulationResult(Model):
    id: str = Field(default_factory=lambda: f"sim_{uuid4().hex[:12]}")
    incident_id: str
    action: ActionRequest
    estimated_recovery_probability: float
    uncertainty: float
    confidence_interval: tuple[float, float]
    expected_latency_improvement_pct: float
    expected_error_rate_improvement_pct: float
    blast_radius: list[str]
    expected_downtime_seconds: int
    rollback_feasibility: Literal["low", "medium", "high"]
    preconditions: list[str]
    assumptions: list[str]
    failure_outcome: str
    simulation_seed: int
    estimate_label: str = "Synthetic digital-twin estimate; not a production guarantee."


class ApprovalRequest(Model):
    simulation_id: str
    actor_id: str
    actor_role: str
    acknowledgement: bool


class ApprovalRecord(Model):
    id: str
    simulation_id: str
    actor_id: str
    actor_role: str
    approved_at: datetime
    signature: str


class ExecuteRequest(Model):
    simulation_id: str
    approval_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=120)


class ExecutionResult(Model):
    id: str
    incident_id: str
    state: ExecutionState
    action_type: ActionType
    started_at: datetime
    completed_at: datetime | None = None
    simulator_only: bool = True
    detail: str
    post_action_telemetry: list[dict[str, float]] = []


class VerificationResult(Model):
    incident_id: str
    execution_id: str
    state: ExecutionState
    windows_observed: int
    windows_required: int
    conditions: dict[str, bool]
    observed_windows: list[dict[str, float]] = []
    verified_at: datetime | None = None


class KnowledgeDocumentIn(Model):
    document_id: str
    version: str
    title: str
    content: str
    service_ids: list[str] = []
    document_type: str = "runbook"
    trust_level: Literal["verified", "reviewed", "untrusted"] = "reviewed"


class KnowledgeSearchRequest(Model):
    query: str = Field(min_length=2, max_length=1000)
    service_ids: list[str] = []
    trust_levels: list[str] = ["verified", "reviewed"]
    limit: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(Model):
    chunk_id: str
    document_id: str
    document_version: str
    section: str
    content: str
    retrieval_score: float
    trust_level: str
    metadata: dict[str, Any]


class PostmortemDocument(Model):
    incident_id: str
    summary: str
    impact: str
    root_cause: str
    resolution: str
    citations: list[str]
    updated_at: datetime


class PostmortemPatch(Model):
    summary: str | None = None
    impact: str | None = None
    root_cause: str | None = None
    resolution: str | None = None


class AuditRecord(Model):
    id: UUID = Field(default_factory=uuid4)
    incident_id: str
    event_type: str
    actor: str
    detail: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvaluationReport(Model):
    dataset_version: str
    seed: int
    generated_at: datetime
    aggregate: dict[str, float]
    per_scenario: list[dict[str, Any]]


class EventMessage(Model):
    type: str
    incident_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any] = {}
