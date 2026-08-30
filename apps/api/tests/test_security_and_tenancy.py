from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import PolicyError
from app.core.security import DEMO_PERMISSIONS, Principal, current_principal
from app.main import app
from app.schemas.models import ActionRequest, ActionType
from app.services.policy import PolicyEngine


def principal(tenant: str, permissions: frozenset[str] = DEMO_PERMISSIONS) -> Principal:
    return Principal(f"user-{tenant}", tenant, None, frozenset({"incident_commander"}), permissions)


def test_tenants_cannot_observe_each_others_incidents() -> None:
    tenant_a, tenant_b = f"org-a-{uuid4().hex}", f"org-b-{uuid4().hex}"
    with TestClient(app) as client:
        app.dependency_overrides[current_principal] = lambda: principal(tenant_a)
        created = client.post("/api/v1/incidents/simulate", json={"scenario_id": "checkout_pool_exhaustion"})
        assert created.status_code == 200
        incident_id = created.json()["id"]
        app.dependency_overrides[current_principal] = lambda: principal(tenant_b)
        assert client.get(f"/api/v1/incidents/{incident_id}").status_code == 404
        assert incident_id not in {item["id"] for item in client.get("/api/v1/incidents").json()}
    app.dependency_overrides.clear()


def test_endpoint_permission_is_enforced() -> None:
    with TestClient(app) as client:
        app.dependency_overrides[current_principal] = lambda: principal("org-no-write", frozenset({"incidents:read"}))
        response = client.post("/api/v1/incidents/simulate", json={"scenario_id": "checkout_pool_exhaustion"})
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"
    app.dependency_overrides.clear()


def test_production_configuration_fails_closed() -> None:
    settings = Settings(environment="production", auto_create_schema=False, auth_required=True)
    try:
        settings.validate_production()
    except RuntimeError as exc:
        assert "Auth0" in str(exc)
    else:
        raise AssertionError("Incomplete Auth0 configuration must fail closed")


def test_approval_signature_detects_tampering() -> None:
    policy = PolicyEngine("test-signing-key")
    record = policy.approve("sim-1", "commander", "incident_commander", True)
    assert policy.verify_approval(record)
    assert not policy.verify_approval(record.model_copy(update={"actor_id": "attacker"}))
    prohibited = ActionRequest(action_type=ActionType.DELETE_DATABASE, target_service="checkout")
    try:
        policy.enforce_simulation(prohibited)
    except PolicyError:
        pass
    else:
        raise AssertionError("Prohibited action bypassed backend policy")
