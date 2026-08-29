from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsAssist AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./opsassist.db"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    ai_mode: str = "offline"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_agent_timeout_seconds: float = 25.0
    openai_agent_concurrency: int = 4
    auth_required: bool = False
    auth0_domain: str | None = None
    auth0_audience: str | None = None
    auth0_roles_claim: str = "https://opsassist.ai/roles"
    auth0_permissions_claim: str = "permissions"
    auth0_tenant_claim: str = "org_id"
    demo_tenant_id: str = "demo"
    auto_create_schema: bool = True
    redis_url: str | None = None
    rate_limit_per_minute: int = 120
    sentry_dsn: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "opsassist-api"
    index_dir: Path = Path("data/indexes")
    retrieval_service_url: str | None = None
    indexer_shared_key: str | None = None
    scenario_seed: int = 20260829
    approval_signing_key: str = "local-demo-change-me"
    verification_windows: int = 3
    data_dir: Path = Path("data")
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPSASSIST_", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def auth0_issuer(self) -> str | None:
        if not self.auth0_domain:
            return None
        return f"https://{self.auth0_domain.rstrip('/')}/"

    def validate_production(self) -> None:
        if self.ai_mode not in {"offline", "openai"}:
            raise RuntimeError(f"Unsupported AI mode: {self.ai_mode}")
        if self.ai_mode == "openai" and not self.openai_api_key:
            raise RuntimeError("OPSASSIST_OPENAI_API_KEY is required when AI mode is openai")
        if self.auth_required and (not self.auth0_domain or not self.auth0_audience):
            raise RuntimeError("Auth0 domain and audience are required when authentication is enabled")
        if self.environment == "production" and self.auto_create_schema:
            raise RuntimeError("Production must use Alembic; set OPSASSIST_AUTO_CREATE_SCHEMA=false")


@lru_cache
def get_settings() -> Settings:
    return Settings()
