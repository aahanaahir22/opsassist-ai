from app.schemas.models import ActionRequest, ActionType
from app.services.simulator import DigitalTwin


def test_simulation_is_reproducible_and_estimated() -> None:
    action = ActionRequest(action_type=ActionType.ROLLBACK, target_service="checkout")
    twin = DigitalTwin()
    first = twin.simulate("inc_1", action, [("checkout", "payment"), ("checkout", "postgres")], .8, 42)
    second = twin.simulate("inc_1", action, [("checkout", "payment"), ("checkout", "postgres")], .8, 42)
    assert first.estimated_recovery_probability == second.estimated_recovery_probability
    assert "estimate" in first.estimate_label.lower()
    assert first.blast_radius == ["checkout", "payment", "postgres"]
