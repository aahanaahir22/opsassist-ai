import os
from pathlib import Path

os.environ["OPSASSIST_DATABASE_URL"] = "sqlite:///./test_opsassist.db"
os.environ["OPSASSIST_DATA_DIR"] = str(Path(__file__).resolve().parents[3] / "data")

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_complete_checkout_workflow() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/ready").status_code == 200
        incident = client.post("/api/v1/incidents/simulate", json={"scenario_id": "checkout_pool_exhaustion", "seed": 847}).json()
        incident_id = incident["id"]
        investigated = client.post(f"/api/v1/incidents/{incident_id}/investigate")
        assert investigated.status_code == 200
        assert investigated.json()["incident"]["hypotheses"][0]["score"] > 0
        simulation = client.post(f"/api/v1/incidents/{incident_id}/simulate-action", json={"action_type":"rollback_deployment","target_service":"checkout","parameters":{"target_version":"v2.18.0"},"seed":847}).json()
        approval = client.post(f"/api/v1/incidents/{incident_id}/approve", json={"simulation_id":simulation["id"],"actor_id":"test-commander","actor_role":"incident_commander","acknowledgement":True}).json()
        execution = client.post(f"/api/v1/incidents/{incident_id}/execute", json={"simulation_id":simulation["id"],"approval_id":approval["id"],"idempotency_key":f"checkout-e2e-{incident_id}"}).json()
        verified = client.post(f"/api/v1/incidents/{incident_id}/verify", params={"execution_id": execution["id"]}).json()
        assert verified["state"] == "VERIFIED"
        postmortem = client.get(f"/api/v1/incidents/{incident_id}/postmortem").json()
        assert postmortem["citations"]


def test_prohibited_action_is_blocked_even_without_frontend() -> None:
    with TestClient(app) as client:
        incident = client.post("/api/v1/incidents/simulate", json={"scenario_id": "checkout_pool_exhaustion"}).json()
        client.post(f"/api/v1/incidents/{incident['id']}/investigate")
        response = client.post(f"/api/v1/incidents/{incident['id']}/simulate-action", json={"action_type":"delete_database","target_service":"checkout"})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "POLICY_ACTION_PROHIBITED"
