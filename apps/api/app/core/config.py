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
    scenario_seed: int = 20260829
    approval_signing_key: str = "local-demo-change-me"
    verification_windows: int = 3
    data_dir: Path = Path("data")
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPSASSIST_", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
