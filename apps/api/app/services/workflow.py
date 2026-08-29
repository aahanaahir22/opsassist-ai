from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import NotFoundError, PolicyError
from app.core.security import Principal
from app.db.models import (
    Approval,
    AuditEvent,
    Execution,
    Incident,
    Postmortem,
    ProposedAction,
    SimulationRun,
    Verification,
)
from app.schemas.models import (
    ActionRequest,
    ApprovalRecord,
    Evidence,
    ExecutionResult,
    ExecutionState,
    IncidentDetail,
    IncidentSummary,
    PostmortemDocument,
    RankedHypothesis,
    RankingComponents,
    SimulationResult,
    VerificationResult,
)
from app.services.anomaly import AnomalyService
from app.services.orchestration import AgentOrchestrator
from app.services.policy import PolicyEngine
from app.services.ranking import RootCauseRanker
from app.services.scenarios import ScenarioLoader
from app.services.simulator import DigitalTwin


class WorkflowService:
    def __init__(self, session: Session, settings: Settings, principal: Principal) -> None:
        self.session = session
        self.settings = settings
        self.principal = principal
        self.tenant_id = principal.tenant_id
        self.scenarios = ScenarioLoader(Path(settings.data_dir) / "scenarios")
        self.anomaly = AnomalyService()
        self.ranker = RootCauseRanker()
        self.twin = DigitalTwin()
        self.policy = PolicyEngine(settings.approval_signing_key)
        self.orchestrator = AgentOrchestrator(settings)

    def _incident(self, incident_id: str) -> Incident:
        incident = self.session.scalar(select(Incident).where(Incident.id == incident_id, Incident.tenant_id == self.tenant_id))
        if not incident:
            raise NotFoundError("Incident", incident_id)
        return incident

    def _audit(self, incident_id: str, event_type: str, actor: str, detail: dict) -> None:
        self.session.add(AuditEvent(tenant_id=self.tenant_id, incident_id=incident_id, event_type=event_type, actor=actor, detail=detail))

    def create_incident(self, scenario_id: str, seed: int) -> IncidentDetail:
        scenario = self.scenarios.load(scenario_id)
        incident = Incident(
            id=f"inc_{uuid4().hex[:12]}",
            tenant_id=self.tenant_id,
            scenario_id=scenario_id,
            title=scenario["manifest"].get("title", scenario_id.replace("_", " ").title()),
            status="OPEN",
            synthetic=True,
            seed=seed,
            state={"scenario": scenario, "anomalies": [], "evidence": [], "hypotheses": [], "agents": [], "timeline": []},
        )
        self.session.add(incident)
        self.session.flush()
        self._audit(incident.id, "incident.created", self.principal.subject, {"scenario_id": scenario_id, "seed": seed})
        self.session.commit()
        return self.detail(incident.id)

    def list_incidents(self) -> list[IncidentSummary]:
        incidents = self.session.scalars(select(Incident).where(Incident.tenant_id == self.tenant_id).order_by(Incident.created_at.desc())).all()
        return [IncidentSummary.model_validate(item) for item in incidents]

    def _record(self, incident: Incident) -> dict:
        return dict(incident.state or {})

    def detail(self, incident_id: str) -> IncidentDetail:
        incident = self._incident(incident_id)
        state = self._record(incident)
        return IncidentDetail(
            **IncidentSummary.model_validate(incident).model_dump(),
            anomalies=state.get("anomalies", []),
            evidence=state.get("evidence", []),
            hypotheses=state.get("hypotheses", []),
            agent_findings=state.get("agents", []),
            timeline=state.get("timeline", []),
        )

    async def investigate(self, incident_id: str, publish) -> IncidentDetail:
        incident = self._incident(incident_id)
        state = self._record(incident)
        scenario = state["scenario"]
        metrics = scenario["metrics"]
        metric_name = next((key for key in metrics[0] if key not in {"timestamp", "label"}), "value")
        values = [float(row[metric_name]) for row in metrics]
        anomalies = self.anomaly.detect(values, scenario["manifest"].get("primary_service", "checkout"), metric_name)
        evidence = [Evidence.model_validate(item) for item in scenario["expected_evidence"]]
        await publish("anomaly.detected", {"results": [item.model_dump(mode="json") for item in anomalies]})
        components = RankingComponents(**scenario["ground_truth"]["ranking_components"])
        leading = self.ranker.score(
            scenario["ground_truth"]["root_cause_id"],
            scenario["ground_truth"]["expected_root_cause"],
            components,
            scenario["ground_truth"]["relevant_evidence"],
            scenario["ground_truth"]["contradicting_evidence"],
        )
        alternative = self.ranker.score(
            "hyp_external_dependency",
            "External dependency degradation",
            components.model_copy(update={"deployment_proximity": 0.12, "agent_agreement": 0.28, "contradiction_penalty": 0.52}),
            [evidence[-1].id] if evidence else [],
            scenario["ground_truth"]["relevant_evidence"][:2],
        )
        ranked: list[RankedHypothesis] = self.ranker.rank([leading, alternative])
        agents = await self.orchestrator.run(incident_id, evidence, publish)
        state.update({
            "anomalies": [item.model_dump(mode="json") for item in anomalies],
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "hypotheses": [item.model_dump(mode="json") for item in ranked],
            "agents": [item.model_dump(mode="json") for item in agents],
            "timeline": [
                {"type": "incident.created", "at": incident.created_at.isoformat()},
                {"type": "anomaly.detected", "at": datetime.now(UTC).isoformat()},
                {"type": "hypothesis.updated", "at": datetime.now(UTC).isoformat()},
            ],
        })
        incident.state = state
        incident.status = "INVESTIGATED"
        self._audit(incident_id, "investigation.completed", "agent_council", {"leading_score": ranked[0].score})
        self.session.commit()
        await publish("hypothesis.updated", ranked[0].model_dump(mode="json"))
        return self.detail(incident_id)

    def simulate_action(self, incident_id: str, action: ActionRequest) -> SimulationResult:
        incident = self._incident(incident_id)
        self.policy.enforce_simulation(action)
        state = self._record(incident)
        if not state.get("hypotheses"):
            raise PolicyError("INVESTIGATION_REQUIRED", "Investigate the incident before simulation.", 409)
        edges = [tuple(edge) for edge in state["scenario"]["topology"]["edges"]]
        severity = max((item["score"] for item in state.get("anomalies", [])), default=0.0)
        normalized_severity = min(1.0, severity / 5)
        result = self.twin.simulate(incident_id, action, edges, normalized_severity, action.seed or incident.seed)
        proposed = ProposedAction(
            id=f"act_{uuid4().hex[:12]}", incident_id=incident_id, action_type=action.action_type,
            target_service=action.target_service, state=ExecutionState.SIMULATED, parameters=action.parameters,
        )
        self.session.add(proposed)
        self.session.flush()
        self.session.add(SimulationRun(
            id=result.id, incident_id=incident_id, action_id=proposed.id, seed=result.simulation_seed,
            result=result.model_dump(mode="json"),
        ))
        self._audit(incident_id, "simulation.completed", "operator", result.model_dump(mode="json"))
        self.session.commit()
        return result

    def approve(self, incident_id: str, record: ApprovalRecord) -> ApprovalRecord:
        simulation = self.session.get(SimulationRun, record.simulation_id)
        if not simulation or simulation.incident_id != incident_id:
            raise NotFoundError("Simulation", record.simulation_id)
        self.session.add(Approval(**record.model_dump()))
        self._audit(incident_id, "approval.recorded", record.actor_id, {"approval_id": record.id, "signature": record.signature})
        self.session.commit()
        return record

    def execute(self, incident_id: str, simulation_id: str, approval_id: str | None, idempotency_key: str) -> ExecutionResult:
        self._incident(incident_id)
        scoped_key = hashlib.sha256(f"{self.tenant_id}:{idempotency_key}".encode()).hexdigest()
        existing = self.session.scalar(select(Execution).where(Execution.idempotency_key == scoped_key, Execution.incident_id == incident_id))
        if existing:
            return ExecutionResult(**existing.result)
        simulation = self.session.get(SimulationRun, simulation_id)
        if not simulation or simulation.incident_id != incident_id:
            raise NotFoundError("Simulation", simulation_id)
        action_type = simulation.result["action"]["action_type"]
        if action_type != "scale_replicas":
            approval = self.session.get(Approval, approval_id) if approval_id else None
            if not approval or approval.simulation_id != simulation_id:
                raise PolicyError("POLICY_APPROVAL_REQUIRED", "This action requires Incident Commander approval.", 403)
            approval_record = ApprovalRecord.model_validate(approval)
            if not self.policy.verify_approval(approval_record):
                raise PolicyError("POLICY_INVALID_SIGNATURE", "The approval signature is invalid.", 403)
        now = datetime.now(UTC)
        probability = float(simulation.result["estimated_recovery_probability"])
        recovered_estimate = probability >= 0.7
        telemetry = [
            {
                "latency_p95_ms": value if recovered_estimate else value * 4,
                "error_rate_pct": error if recovered_estimate else error * 8,
                "pool_occupancy_pct": pool if recovered_estimate else min(100, pool + 30),
                "auth_failure_rate_pct": error if recovered_estimate else 22.0,
                "heap_used_mb": 520 + index * 9 if recovered_estimate else 930 + index * 20,
                "cache_miss_rate_pct": 10 + index if recovered_estimate else 75 + index * 4,
                "provider_429_rate_pct": error if recovered_estimate else 41.0,
            }
            for index, (value, error, pool) in enumerate([(242.0, 0.9, 68.0), (221.0, 0.7, 64.0), (204.0, 0.6, 61.0)])
        ]
        result = ExecutionResult(
            id=f"exe_{uuid4().hex[:12]}", incident_id=incident_id, state=ExecutionState.EXECUTED,
            action_type=action_type, started_at=now, completed_at=now,
            detail="Action executed only against the deterministic synthetic simulator.",
            post_action_telemetry=telemetry,
        )
        self.session.add(Execution(
            id=result.id, incident_id=incident_id, simulation_id=simulation_id,
            idempotency_key=scoped_key, state=result.state, result=result.model_dump(mode="json"),
        ))
        self._audit(incident_id, "execution.completed", "simulator", result.model_dump(mode="json"))
        self.session.commit()
        return result

    def verify(self, incident_id: str, execution_id: str) -> VerificationResult:
        self._incident(incident_id)
        execution = self.session.get(Execution, execution_id)
        if not execution or execution.incident_id != incident_id:
            raise NotFoundError("Execution", execution_id)
        state = self._record(self._incident(incident_id))
        criteria = state["scenario"]["ground_truth"]["verification_criteria"]
        windows = execution.result.get("post_action_telemetry", [])
        checks = {
            "latency_p95_below_250_ms": lambda row: row["latency_p95_ms"] < 250,
            "error_rate_below_1_percent": lambda row: row["error_rate_pct"] < 1,
            "pool_occupancy_below_70_percent": lambda row: row["pool_occupancy_pct"] < 70,
            "auth_failure_rate_below_1_percent": lambda row: row["auth_failure_rate_pct"] < 1,
            "heap_below_600_mb": lambda row: row["heap_used_mb"] < 600,
            "no_oom_for_three_windows": lambda row: row["heap_used_mb"] < 900,
            "miss_rate_below_15_percent": lambda row: row["cache_miss_rate_pct"] < 15,
            "provider_429_rate_below_1_percent": lambda row: row["provider_429_rate_pct"] < 1,
        }
        conditions = {key: len(windows) >= self.settings.verification_windows and all(checks[key](row) for row in windows[-self.settings.verification_windows:]) for key in criteria if key in checks}
        verified = len(conditions) == len(criteria) and all(conditions.values())
        result = VerificationResult(
            incident_id=incident_id, execution_id=execution_id, state=ExecutionState.VERIFIED if verified else ExecutionState.FAILED,
            windows_observed=len(windows), windows_required=self.settings.verification_windows,
            conditions=conditions, observed_windows=windows, verified_at=datetime.now(UTC) if verified else None,
        )
        self.session.add(Verification(
            incident_id=incident_id, execution_id=execution_id,
            windows_observed=result.windows_observed, criteria=conditions, verified=verified,
        ))
        incident = self._incident(incident_id)
        incident.status = "VERIFIED" if verified else "FAILED"
        self._audit(incident_id, "incident.recovered" if verified else "verification.failed", "verification_agent", result.model_dump(mode="json"))
        self.session.commit()
        return result

    def postmortem(self, incident_id: str) -> PostmortemDocument:
        incident = self._incident(incident_id)
        if incident.status != "VERIFIED":
            raise PolicyError("VERIFICATION_REQUIRED", "Recovery must be verified before postmortem generation.", 409)
        state = self._record(incident)
        hypothesis = state["hypotheses"][0]
        existing = self.session.scalar(select(Postmortem).where(Postmortem.incident_id == incident_id))
        if existing:
            return PostmortemDocument(**existing.content)
        document = PostmortemDocument(
            incident_id=incident_id,
            summary=f"Synthetic incident {incident.title} reached verified recovery.",
            impact=state["scenario"]["ground_truth"]["impact"],
            root_cause=f"{hypothesis['label']} (computed score {hypothesis['score']:.3f}).",
            resolution=state["scenario"]["ground_truth"]["correct_remediation"],
            citations=hypothesis["supporting_evidence_ids"],
            updated_at=datetime.now(UTC),
        )
        self.session.add(Postmortem(incident_id=incident_id, content=document.model_dump(mode="json")))
        self._audit(incident_id, "postmortem.generated", "postmortem_writer", {"citations": document.citations})
        self.session.commit()
        return document
