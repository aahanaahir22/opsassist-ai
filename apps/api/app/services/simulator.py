from __future__ import annotations

import random
from collections import deque

from app.schemas.models import ActionRequest, ActionType, SimulationResult


ACTION_EFFECT = {
    ActionType.ROLLBACK: (0.82, 0.78, 0.76, 140),
    ActionType.RESTART: (0.64, 0.52, 0.57, 85),
    ActionType.SCALE: (0.58, 0.46, 0.35, 55),
    ActionType.INCREASE_POOL: (0.69, 0.63, 0.60, 40),
    ActionType.DISABLE_INTEGRATION: (0.56, 0.42, 0.48, 25),
}


class DigitalTwin:
    def affected_services(
        self, target: str, edges: list[tuple[str, str]], max_depth: int = 1
    ) -> list[str]:
        graph: dict[str, set[str]] = {}
        for source, destination in edges:
            graph.setdefault(source, set()).add(destination)
            graph.setdefault(destination, set()).add(source)
        seen = {target}
        queue = deque([(target, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in graph.get(node, set()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return sorted(seen)

    def simulate(
        self,
        incident_id: str,
        action: ActionRequest,
        edges: list[tuple[str, str]],
        severity: float,
        seed: int,
    ) -> SimulationResult:
        if action.action_type not in ACTION_EFFECT:
            raise ValueError(f"Action {action.action_type} is not simulatable")
        base_probability, latency_gain, error_gain, downtime = ACTION_EFFECT[action.action_type]
        rng = random.Random(seed)
        topology_penalty = min(0.18, max(0, len(self.affected_services(action.target_service, edges)) - 1) * 0.025)
        jitter = rng.uniform(-0.025, 0.025)
        probability = max(0.05, min(0.98, base_probability + severity * 0.1 - topology_penalty + jitter))
        uncertainty = round(0.07 + topology_penalty / 2, 4)
        return SimulationResult(
            incident_id=incident_id,
            action=action,
            estimated_recovery_probability=round(probability, 4),
            uncertainty=uncertainty,
            confidence_interval=(round(max(0, probability - uncertainty), 4), round(min(1, probability + uncertainty), 4)),
            expected_latency_improvement_pct=round(latency_gain * 100, 1),
            expected_error_rate_improvement_pct=round(error_gain * 100, 1),
            blast_radius=self.affected_services(action.target_service, edges),
            expected_downtime_seconds=downtime,
            rollback_feasibility="high" if action.action_type == ActionType.ROLLBACK else "medium",
            preconditions=["Simulation dataset loaded", "At least two healthy synthetic replicas", "Rollback artifact checksum present"],
            assumptions=["Synthetic topology is current", "No second incident begins during execution"],
            failure_outcome="Action is rolled back in the simulator and the incident remains open.",
            simulation_seed=seed,
        )
