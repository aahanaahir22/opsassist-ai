from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Awaitable, Callable

from app.schemas.models import AgentFinding, Evidence


Publisher = Callable[[str, dict], Awaitable[None]]


AGENT_TASKS = [
    ("Signal Analyst", "Quantify metric anomalies"),
    ("Log Investigator", "Extract normalized failure signatures"),
    ("Metrics Analyst", "Compare rolling baselines"),
    ("Trace Investigator", "Localize critical-path latency"),
    ("Dependency Analyst", "Measure topology propagation"),
    ("Runbook Researcher", "Retrieve exact operational citations"),
    ("Root-Cause Investigator", "Rank competing hypotheses"),
    ("Risk Guardian", "Classify candidate actions"),
    ("Remediation Planner", "Propose reversible simulator actions"),
    ("Verification Agent", "Define recovery windows"),
    ("Postmortem Writer", "Draft a cited incident record"),
]


class AgentOrchestrator:
    """Typed, deterministic state machine for offline mode."""

    async def run(self, incident_id: str, evidence: list[Evidence], publish: Publisher) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        evidence_ids = [item.id for item in evidence]
        for index, (name, task) in enumerate(AGENT_TASKS):
            await publish("agent.started", {"agent": name, "task": task})
            started = perf_counter()
            await asyncio.sleep(0)
            confidence = min(0.96, 0.72 + len(evidence) * 0.025 - index * 0.004)
            finding = AgentFinding(
                agent_name=name,
                task=task,
                input_references=[incident_id, *evidence_ids[:3]],
                evidence_ids=evidence_ids[:4],
                finding=f"{task} completed from {len(evidence_ids)} persisted evidence objects in offline mode.",
                proposed_hypothesis="database_pool_exhaustion" if name == "Root-Cause Investigator" else None,
                confidence=round(confidence, 4),
                uncertainty=round(1 - confidence, 4),
                contradictions=[item.id for item in evidence if item.stance == "contradicts"],
                duration_ms=max(1, int((perf_counter() - started) * 1000)),
                status="completed",
            )
            findings.append(finding)
            await publish("agent.completed", finding.model_dump(mode="json"))
        return findings
