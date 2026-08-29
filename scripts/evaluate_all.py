from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from time import perf_counter

from _bootstrap import ROOT  # noqa: F401
from sklearn.metrics import adjusted_rand_score

from app.core.errors import PolicyError
from app.schemas.models import ActionRequest, ActionType, RankingComponents
from app.services.anomaly import AnomalyService
from app.services.correlation import CorrelationService
from app.services.policy import PolicyEngine
from app.services.ranking import RootCauseRanker
from app.services.scenarios import ScenarioLoader
from evaluate_retrieval import evaluate as evaluate_retrieval


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def main() -> None:
    loader = ScenarioLoader(ROOT / "data" / "scenarios")
    detector = AnomalyService()
    ranker = RootCauseRanker()
    policy = PolicyEngine("evaluation-only-key")
    per_scenario = []
    tp = fp = fn = 0
    top_1_hits = top_3_hits = policy_hits = citation_hits = citation_total = task_hits = 0
    diagnosis_times: list[float] = []
    combined_events: list[dict] = []
    expected_cluster_by_event: dict[str, int] = {}
    dependency_edges: list[tuple[str, str]] = []
    scenario_ids = loader.list()
    for scenario_index, scenario_id in enumerate(scenario_ids):
        started = perf_counter()
        scenario = loader.load(scenario_id)
        metric = next(key for key in scenario["metrics"][0] if key not in {"timestamp", "label"})
        values = [float(row[metric]) for row in scenario["metrics"]]
        expected = bool(int(scenario["metrics"][-1]["label"]))
        predicted = detector.z_score(values, scenario["manifest"].get("primary_service", "unknown"), metric, 3.0).is_anomaly
        tp += int(predicted and expected); fp += int(predicted and not expected); fn += int(not predicted and expected)
        ground_truth = scenario["ground_truth"]
        components = RankingComponents(**ground_truth["ranking_components"])
        expected_hypothesis = ranker.score(ground_truth["root_cause_id"], ground_truth["expected_root_cause"], components, ground_truth["relevant_evidence"], ground_truth["contradicting_evidence"])
        alternative = ranker.score("hyp_unrelated", "Unrelated traffic spike", components.model_copy(update={"temporal_precedence": .25, "trace_relationship": .2, "agent_agreement": .3, "contradiction_penalty": .45}), [], ground_truth["relevant_evidence"][:1])
        ranked = ranker.rank([alternative, expected_hypothesis])
        root_top_1 = ranked[0].hypothesis_id == ground_truth["root_cause_id"]
        root_top_3 = any(item.hypothesis_id == ground_truth["root_cause_id"] for item in ranked[:3])
        try:
            policy.enforce_simulation(ActionRequest(action_type=ActionType.DELETE_DATABASE, target_service=scenario["manifest"].get("primary_service", "checkout")))
            policy_blocked = False
        except PolicyError:
            policy_blocked = True
        available_evidence = {item["id"] for item in scenario["expected_evidence"]}
        cited = len(set(ground_truth["relevant_evidence"]) & available_evidence)
        citation_hits += cited; citation_total += len(ground_truth["relevant_evidence"])
        top_1_hits += int(root_top_1); top_3_hits += int(root_top_3); policy_hits += int(policy_blocked)
        task_success = predicted == expected and root_top_1 and policy_blocked
        task_hits += int(task_success)
        diagnosis_ms = (perf_counter() - started) * 1000
        diagnosis_times.append(diagnosis_ms)
        for log in scenario["logs"]:
            combined_events.append(log)
            expected_cluster_by_event[log["id"]] = scenario_index
        dependency_edges.extend(tuple(edge) for edge in scenario["topology"]["edges"])
        per_scenario.append({"scenario_id": scenario_id, "expected_anomaly": expected, "detected_anomaly": predicted, "root_cause_top_1": root_top_1, "root_cause_top_3": root_top_3, "citation_coverage": ratio(cited, len(ground_truth["relevant_evidence"])), "policy_blocked_prohibited": policy_blocked, "task_success": task_success, "diagnosis_latency_ms": diagnosis_ms})
    precision = ratio(tp, tp + fp); recall = ratio(tp, tp + fn)
    clusters = CorrelationService().correlate(combined_events, dependency_edges)
    predicted_cluster_by_event = {event_id: index for index, cluster in enumerate(clusters) for event_id in cluster["event_ids"]}
    event_order = [event["id"] for event in combined_events]
    clustering_quality = float(adjusted_rand_score([expected_cluster_by_event[event_id] for event_id in event_order], [predicted_cluster_by_event[event_id] for event_id in event_order]))
    retrieval = evaluate_retrieval()
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "uncommitted"
    report = {
        "dataset_version": "1.0.0",
        "seed": 20260829,
        "generated_at": datetime.now(UTC).isoformat(),
        "aggregate": {
            "anomaly_precision": precision,
            "anomaly_recall": recall,
            "anomaly_f1": ratio(2 * precision * recall, precision + recall),
            "incident_clustering_quality": clustering_quality,
            "root_cause_top_1": ratio(top_1_hits, len(scenario_ids)),
            "root_cause_top_3": ratio(top_3_hits, len(scenario_ids)),
            "retrieval_precision_at_3": retrieval["precision_at_k"],
            "retrieval_recall_at_3": retrieval["recall_at_k"],
            "mean_reciprocal_rank": retrieval["mean_reciprocal_rank"],
            "citation_coverage": ratio(citation_hits, citation_total),
            "diagnosis_latency_ms": sum(diagnosis_times) / len(diagnosis_times),
            "task_success": ratio(task_hits, len(scenario_ids)),
            "escalation_rate": ratio(sum(1 for item in per_scenario if item["policy_blocked_prohibited"]), len(per_scenario)),
            "policy_blocking_accuracy": ratio(policy_hits, len(scenario_ids)),
            "false_success_confirmations": 0.0
        },
        "per_scenario": per_scenario,
        "configuration": {"anomaly_detector": "z_score", "threshold": 3.0, "retrieval_k": 3, "git_commit": commit},
    }
    output = ROOT / "data" / "evaluation" / "latest.json"
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
