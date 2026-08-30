from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import OpsAssistError

DEMO_PERMISSIONS = frozenset({
    "incidents:read", "incidents:write", "actions:simulate", "actions:approve",
    "actions:execute", "actions:verify", "knowledge:read", "knowledge:write",
    "telemetry:write", "evaluations:read", "audit:read", "postmortems:write",
})


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    tenant_id: str
    email: str | None
    roles: frozenset[str]
    permissions: frozenset[str]
    token: str | None = None


bearer = HTTPBearer(auto_error=False)


class Auth0Verifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.jwks = jwt.PyJWKClient(f"{settings.auth0_issuer}.well-known/jwks.json") if settings.auth0_issuer else None

    def verify(self, token: str) -> Principal:
        if not self.jwks or not self.settings.auth0_issuer or not self.settings.auth0_audience:
            raise OpsAssistError("AUTH_NOT_CONFIGURED", "Authentication is not configured.", 503)
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.auth0_audience,
                issuer=self.settings.auth0_issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise OpsAssistError("INVALID_TOKEN", "The access token is invalid or expired.", 401) from exc
        tenant = claims.get(self.settings.auth0_tenant_claim)
        if not isinstance(tenant, str) or not tenant:
            raise OpsAssistError("TENANT_REQUIRED", "An Auth0 Organization is required.", 403)
        return Principal(
            subject=str(claims["sub"]),
            tenant_id=tenant,
            email=claims.get("email"),
            roles=frozenset(_string_list(claims.get(self.settings.auth0_roles_claim))),
            permissions=frozenset(_string_list(claims.get(self.settings.auth0_permissions_claim))),
            token=token,
        )


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return value.split()
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


@lru_cache
def verifier() -> Auth0Verifier:
    return Auth0Verifier(get_settings())


def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    if not settings.auth_required:
        return Principal("demo-user", settings.demo_tenant_id, None, frozenset({"incident_commander"}), DEMO_PERMISSIONS)
    if not credentials or credentials.scheme.lower() != "bearer":
        raise OpsAssistError("AUTHENTICATION_REQUIRED", "A bearer access token is required.", 401)
    return verifier().verify(credentials.credentials)


def require_permissions(*required: str) -> Callable[..., Principal]:
    def dependency(principal: Annotated[Principal, Depends(current_principal)]) -> Principal:
        missing = set(required) - principal.permissions
        if missing:
            raise OpsAssistError("FORBIDDEN", "Missing required permissions.", 403, {"required": sorted(missing)})
        return principal
    return dependency


def verify_websocket_token(token: str | None, settings: Settings) -> Principal:
    if not settings.auth_required:
        return Principal("demo-user", settings.demo_tenant_id, None, frozenset({"incident_commander"}), DEMO_PERMISSIONS)
    if not token:
        raise OpsAssistError("AUTHENTICATION_REQUIRED", "A WebSocket bearer token is required.", 401)
    return verifier().verify(token)
