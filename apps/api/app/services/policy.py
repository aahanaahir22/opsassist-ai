from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import uuid4

from app.core.errors import PolicyError
from app.schemas.models import ActionRequest, ActionType, ApprovalRecord


CLASSIFICATION = {
    ActionType.RESTART: "sensitive",
    ActionType.SCALE: "safe",
    ActionType.INCREASE_POOL: "sensitive",
    ActionType.ROLLBACK: "sensitive",
    ActionType.DISABLE_INTEGRATION: "high_risk",
    ActionType.DELETE_DATABASE: "prohibited",
}

ROLE_PERMISSIONS = {
    "operator": {"safe"},
    "incident_commander": {"safe", "sensitive", "high_risk"},
    "admin": {"safe", "sensitive", "high_risk"},
}


class PolicyEngine:
    def __init__(self, signing_key: str) -> None:
        self.signing_key = signing_key.encode()

    def classify(self, action: ActionRequest) -> str:
        return CLASSIFICATION.get(action.action_type, "prohibited")

    def enforce_simulation(self, action: ActionRequest) -> str:
        classification = self.classify(action)
        if classification == "prohibited":
            raise PolicyError("POLICY_ACTION_PROHIBITED", "This action is prohibited by backend policy.", 403)
        if action.target_service not in {"checkout", "payment", "inventory", "auth", "redis", "provider"}:
            raise PolicyError("POLICY_RESOURCE_DENIED", "The target is outside the simulator allow-list.", 403)
        return classification

    def approve(self, simulation_id: str, actor_id: str, actor_role: str, acknowledgement: bool) -> ApprovalRecord:
        if not acknowledgement:
            raise PolicyError("POLICY_ACKNOWLEDGEMENT_REQUIRED", "Explicit acknowledgement is required.", 400)
        if "sensitive" not in ROLE_PERMISSIONS.get(actor_role, set()):
            raise PolicyError("POLICY_APPROVAL_REQUIRED", "Incident Commander approval is required.", 403)
        approved_at = datetime.now(UTC)
        payload = f"{simulation_id}:{actor_id}:{actor_role}:{approved_at.isoformat()}"
        signature = hmac.new(self.signing_key, payload.encode(), hashlib.sha256).hexdigest()
        return ApprovalRecord(
            id=f"apr_{uuid4().hex[:12]}",
            simulation_id=simulation_id,
            actor_id=actor_id,
            actor_role=actor_role,
            approved_at=approved_at,
            signature=signature,
        )
