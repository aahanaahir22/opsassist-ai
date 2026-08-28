def seed(client):
    response = client.post("/api/v1/demo/reset")
    assert response.status_code == 200
    return response.json()


def test_health(client):
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert data["execution_mode"] == "simulated"
    assert "faiss" in data["retrieval_engine"] or "fallback" in data["retrieval_engine"]


def test_grouping_rag_and_policy(client):
    incident = seed(client)
    assert incident["event_count"] == 3
    assert incident["severity"] == "critical"
    assert incident["confidence"] == 0.88
    assert incident["status"] == "approval_pending"
    assert incident["evidence"]
    assert all(x["evidence_id"].startswith("RB-") for x in incident["evidence"])
    assert incident["policy_decision"]["decision"] == "approval_required"


def test_execution_blocked_without_approval(client):
    incident = seed(client)
    response = client.post(f"/api/v1/incidents/{incident['id']}/execute")
    assert response.status_code == 409
    assert response.json()["detail"] == "Human approval is required"


def test_complete_approval_execution_audit_flow(client):
    incident = seed(client)
    approval = client.get("/api/v1/approvals").json()[0]
    decision = client.post(
        f"/api/v1/approvals/{approval['id']}/decision",
        json={
            "decision": "approved",
            "decided_by": "on-call.engineer@example.com",
            "reason": "Evidence and rolling safeguards verified.",
        },
    )
    assert decision.status_code == 200
    result = client.post(f"/api/v1/incidents/{incident['id']}/execute")
    assert result.status_code == 200
    assert result.json()["after_state"]["health"] == "healthy"
    assert client.get(f"/api/v1/incidents/{incident['id']}").json()["status"] == "resolved"
    actions = {
        x["action"] for x in client.get(f"/api/v1/audit?incident_id={incident['id']}").json()
    }
    assert {
        "incident.created",
        "incident.analyzed",
        "approval.decided",
        "remediation.executed",
    } <= actions


def test_matching_event_groups(client):
    incident = seed(client)
    event = client.post(
        "/api/v1/events",
        json={
            "service": "payment-api",
            "environment": "production",
            "severity": "high",
            "message": "Another pool acquisition timeout",
            "error_code": "DB_TIMEOUT",
            "trace_id": "tr_group",
            "attributes": {"pool_waiters": 140},
        },
    )
    assert event.status_code == 201
    assert event.json()["incident_id"] == incident["id"]
    assert client.get(f"/api/v1/incidents/{incident['id']}").json()["event_count"] == 4


def test_dashboard_metrics(client):
    seed(client)
    data = client.get("/api/v1/dashboard").json()
    assert data["open_incidents"] == 1
    assert data["critical_incidents"] == 1
    assert data["pending_approvals"] == 1
    assert data["evidence_coverage"] == 1.0


def test_analysis_filters_and_missing_incidents(client):
    incident = seed(client)
    filtered = client.get("/api/v1/incidents?status=approval_pending")
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == [incident["id"]]

    analyzed = client.post(f"/api/v1/incidents/{incident['id']}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["evidence"]

    assert client.get("/api/v1/incidents/missing").status_code == 404
    assert client.post("/api/v1/incidents/missing/analyze").status_code == 404


def test_invalid_approval_and_unanalyzed_execution(client):
    seed(client)
    approval = client.get("/api/v1/approvals").json()[0]
    body = {
        "decision": "rejected",
        "decided_by": "on-call.engineer@example.com",
        "reason": "Additional database evidence is required.",
    }
    assert client.post(f"/api/v1/approvals/{approval['id']}/decision", json=body).status_code == 200
    assert client.post(f"/api/v1/approvals/{approval['id']}/decision", json=body).status_code == 409
    assert client.post("/api/v1/approvals/missing/decision", json=body).status_code == 404
    assert client.post("/api/v1/incidents/missing/execute").status_code == 404

    event = client.post(
        "/api/v1/events",
        json={
            "service": "search-api",
            "environment": "staging",
            "severity": "medium",
            "message": "Search response latency exceeded the staging threshold",
            "error_code": "SEARCH_LATENCY",
        },
    ).json()
    response = client.post(f"/api/v1/incidents/{event['incident_id']}/execute")
    assert response.status_code == 409
    assert response.json()["detail"] == "Analyze the incident before execution"
