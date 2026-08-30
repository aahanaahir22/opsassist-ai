from __future__ import annotations

from datetime import UTC, datetime
from math import sqrt
from statistics import fmean, pstdev

import numpy as np
from sklearn.ensemble import IsolationForest

from app.schemas.models import AnomalyResult


def _result(
    detector: str,
    values: list[float],
    service_id: str,
    metric: str,
    score: float,
    threshold: float,
    is_anomaly: bool,
    explanation: str,
) -> AnomalyResult:
    baseline = fmean(values[:-1]) if len(values) > 1 else values[-1]
    return AnomalyResult(
        detector=detector,
        metric=metric,
        service_id=service_id,
        timestamp=datetime.now(UTC),
        observed_value=values[-1],
        baseline_value=baseline,
        score=round(float(score), 4),
        threshold=threshold,
        is_anomaly=is_anomaly,
        explanation=explanation,
    )


class AnomalyService:
    """Numerical detectors. No LLM participates in these calculations."""

    def detect(
        self, values: list[float], service_id: str, metric: str, threshold: float = 3.0
    ) -> list[AnomalyResult]:
        clean = [float(value) for value in values if value is not None]
        if len(clean) < 4:
            raise ValueError("At least four numeric observations are required")
        return [
            self.z_score(clean, service_id, metric, threshold),
            self.isolation_forest(clean, service_id, metric),
            self.change_point(clean, service_id, metric),
            self.rate_of_change(clean, service_id, metric),
        ]

    def z_score(self, values: list[float], service_id: str, metric: str, threshold: float) -> AnomalyResult:
        baseline = values[:-1]
        deviation = pstdev(baseline)
        score = 0.0 if deviation == 0 else abs(values[-1] - fmean(baseline)) / deviation
        return _result(
            "z_score", values, service_id, metric, score, threshold, score >= threshold,
            f"Observed value is {score:.2f} standard deviations from the rolling baseline.",
        )

    def isolation_forest(self, values: list[float], service_id: str, metric: str) -> AnomalyResult:
        array = np.asarray(values, dtype=float).reshape(-1, 1)
        model = IsolationForest(contamination="auto", random_state=42, n_estimators=100)
        model.fit(array[:-1])
        raw = -float(model.score_samples(array[-1:])[0])
        is_anomaly = bool(model.predict(array[-1:])[0] == -1)
        return _result(
            "isolation_forest", values, service_id, metric, raw, 0.5, is_anomaly,
            "Isolation Forest compared the latest point with seeded trees fitted to its history.",
        )

    def change_point(self, values: list[float], service_id: str, metric: str) -> AnomalyResult:
        split = max(2, len(values) // 2)
        before, after = values[:split], values[split:]
        pooled = sqrt((pstdev(before) ** 2 + pstdev(after) ** 2) / 2) or 1.0
        score = abs(fmean(after) - fmean(before)) / pooled
        return _result(
            "change_point", values, service_id, metric, score, 2.5, score >= 2.5,
            f"Window means shifted by {score:.2f} pooled standard deviations.",
        )

    def rate_of_change(self, values: list[float], service_id: str, metric: str) -> AnomalyResult:
        denominator = abs(values[-2]) or 1.0
        score = abs(values[-1] - values[-2]) / denominator
        return _result(
            "rate_of_change", values, service_id, metric, score, 0.5, score >= 0.5,
            f"The last observation changed by {score * 100:.1f}% from the previous point.",
        )
