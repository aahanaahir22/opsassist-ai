from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer


SECRET_PATTERN = re.compile(
    r"(?i)(authorization|api[_-]?key|password|token)\s*[=:]\s*[^\s,;]+"
)
VARIABLE_PATTERN = re.compile(r"\b(?:[0-9a-f]{8,}|\d+|[0-9a-f-]{36})\b", re.I)


@dataclass(slots=True)
class CorrelatedEvent:
    id: str
    service_id: str
    timestamp: datetime
    message: str
    trace_id: str | None = None


class CorrelationService:
    def normalize(self, message: str) -> str:
        redacted = SECRET_PATTERN.sub(lambda m: f"{m.group(1).lower()}=[REDACTED]", message.lower())
        return VARIABLE_PATTERN.sub("<var>", redacted)

    def correlate(
        self,
        raw_events: list[dict[str, Any]],
        dependency_edges: list[tuple[str, str]],
        eps: float = 0.72,
    ) -> list[dict[str, Any]]:
        events = [
            CorrelatedEvent(
                id=str(item["id"]),
                service_id=str(item["service_id"]),
                timestamp=datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00")),
                message=self.normalize(str(item.get("message", ""))),
                trace_id=item.get("trace_id"),
            )
            for item in raw_events
        ]
        if not events:
            return []
        text = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform([e.message for e in events])
        similarity_distance = 1 - (text @ text.T).toarray()
        adjacency = {frozenset(edge) for edge in dependency_edges}
        feature_distance = similarity_distance.copy()
        reasons: dict[tuple[int, int], list[str]] = {}
        for i, left in enumerate(events):
            for j, right in enumerate(events):
                if i >= j:
                    continue
                pair_reasons: list[str] = []
                seconds = abs((left.timestamp - right.timestamp).total_seconds())
                if seconds <= 120:
                    feature_distance[i, j] = feature_distance[j, i] = max(0, feature_distance[i, j] - 0.22)
                    pair_reasons.append(f"within {seconds:.0f}s")
                if left.trace_id and left.trace_id == right.trace_id:
                    feature_distance[i, j] = feature_distance[j, i] = 0
                    pair_reasons.append("shared trace ID")
                if left.service_id == right.service_id:
                    feature_distance[i, j] = feature_distance[j, i] = max(0, feature_distance[i, j] - 0.2)
                    pair_reasons.append("shared service")
                if frozenset((left.service_id, right.service_id)) in adjacency:
                    feature_distance[i, j] = feature_distance[j, i] = max(0, feature_distance[i, j] - 0.15)
                    pair_reasons.append("direct dependency")
                reasons[(i, j)] = pair_reasons
        np.fill_diagonal(feature_distance, 0)
        labels = DBSCAN(eps=eps, min_samples=1, metric="precomputed").fit_predict(feature_distance)
        clusters: list[dict[str, Any]] = []
        for label in sorted(set(int(value) for value in labels)):
            indices = [i for i, value in enumerate(labels) if int(value) == label]
            explanation = sorted({reason for (i, j), pair in reasons.items() if i in indices and j in indices for reason in pair})
            clusters.append({
                "cluster_id": f"cluster_{label + 1}",
                "event_ids": [events[i].id for i in indices],
                "service_ids": sorted({events[i].service_id for i in indices}),
                "explanation": explanation or ["log-template similarity"],
            })
        return clusters
