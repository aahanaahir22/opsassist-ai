from __future__ import annotations

from app.schemas.models import RankedHypothesis, RankingComponents

DEFAULT_WEIGHTS = {
    "temporal_precedence": 0.15,
    "anomaly_severity": 0.15,
    "dependency_centrality": 0.10,
    "trace_relationship": 0.15,
    "deployment_proximity": 0.10,
    "historical_similarity": 0.08,
    "runbook_relevance": 0.10,
    "agent_agreement": 0.17,
}


class RootCauseRanker:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS

    def score(
        self,
        hypothesis_id: str,
        label: str,
        components: RankingComponents,
        supporting: list[str],
        contradicting: list[str],
    ) -> RankedHypothesis:
        positive = sum(getattr(components, key) * weight for key, weight in self.weights.items())
        score = max(0.0, min(1.0, positive * (1 - components.contradiction_penalty)))
        return RankedHypothesis(
            hypothesis_id=hypothesis_id,
            label=label,
            score=round(score, 4),
            components=components,
            supporting_evidence_ids=supporting,
            contradicting_evidence_ids=contradicting,
            uncertainty=round(1 - score, 4),
        )

    def rank(self, candidates: list[RankedHypothesis]) -> list[RankedHypothesis]:
        ordered = sorted(candidates, key=lambda item: item.score, reverse=True)
        return [item.model_copy(update={"rank": index + 1}) for index, item in enumerate(ordered)]
