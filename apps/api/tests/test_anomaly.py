from app.services.anomaly import AnomalyService


def test_z_score_detects_spike() -> None:
    result = AnomalyService().z_score([100, 101, 99, 100, 102, 900], "checkout", "latency", 3.0)
    assert result.is_anomaly
    assert result.score > result.threshold


def test_noisy_normal_series_is_not_a_rate_spike() -> None:
    result = AnomalyService().rate_of_change([96, 105, 99, 103, 101], "checkout", "latency")
    assert not result.is_anomaly


def test_missing_values_are_ignored() -> None:
    results = AnomalyService().detect([100, None, 99, 101, 800], "checkout", "latency")  # type: ignore[list-item]
    assert len(results) == 4


def test_too_few_points_fail_validation() -> None:
    try:
        AnomalyService().detect([1, 2, 3], "service", "metric")
    except ValueError as exc:
        assert "four" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
