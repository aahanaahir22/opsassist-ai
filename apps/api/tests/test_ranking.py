from app.schemas.models import RankingComponents
from app.services.ranking import RootCauseRanker


def components(penalty: float) -> RankingComponents:
    return RankingComponents(
        temporal_precedence=.9, anomaly_severity=.9, dependency_centrality=.8,
        trace_relationship=.9, deployment_proximity=.9, historical_similarity=.7,
        runbook_relevance=.8, agent_agreement=.9, contradiction_penalty=penalty,
    )


def test_contradiction_penalty_reduces_score() -> None:
    ranker = RootCauseRanker()
    supported = ranker.score("a", "A", components(.05), ["EV-1"], [])
    contradicted = ranker.score("b", "B", components(.60), ["EV-1"], ["EV-2"])
    assert supported.score > contradicted.score
    assert ranker.rank([contradicted, supported])[0].hypothesis_id == "a"
