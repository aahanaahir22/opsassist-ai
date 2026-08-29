import pytest

from app.core.errors import PolicyError
from app.schemas.models import ActionRequest, ActionType
from app.services.policy import PolicyEngine


def test_prohibited_action_fails_in_backend() -> None:
    engine = PolicyEngine("test-key")
    with pytest.raises(PolicyError) as error:
        engine.enforce_simulation(ActionRequest(action_type=ActionType.DELETE_DATABASE, target_service="checkout"))
    assert error.value.code == "POLICY_ACTION_PROHIBITED"


def test_approval_is_signed_and_role_checked() -> None:
    engine = PolicyEngine("test-key")
    with pytest.raises(PolicyError):
        engine.approve("sim_1", "u1", "operator", True)
    approved = engine.approve("sim_1", "u1", "incident_commander", True)
    assert len(approved.signature) == 64
