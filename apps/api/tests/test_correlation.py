from app.services.correlation import CorrelationService


def test_related_events_cluster_and_unrelated_event_stays_separate() -> None:
    events = [
        {"id": "a", "service_id": "checkout", "timestamp": "2026-08-29T09:43:00Z", "trace_id": "t1", "message": "pool timeout active=98"},
        {"id": "b", "service_id": "postgres", "timestamp": "2026-08-29T09:43:02Z", "trace_id": "t1", "message": "connection pool timeout active=100"},
        {"id": "c", "service_id": "auth", "timestamp": "2026-08-29T12:43:00Z", "trace_id": "t9", "message": "certificate expired"},
    ]
    clusters = CorrelationService().correlate(events, [("checkout", "postgres")])
    event_sets = [set(cluster["event_ids"]) for cluster in clusters]
    assert {"a", "b"} in event_sets
    assert {"c"} in event_sets


def test_secret_redaction_and_template_normalization() -> None:
    normalized = CorrelationService().normalize("api_key=secret-123 request 98123 failed")
    assert "secret-123" not in normalized
    assert "[REDACTED]" in normalized
    assert "<var>" in normalized
