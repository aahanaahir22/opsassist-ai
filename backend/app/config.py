from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./opsassist.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8080"]
    )
    api_key: str | None = None
    seed_demo: bool = True
    incident_window_minutes: int = 15
    runbook_dir: Path = Path(__file__).parent / "data" / "runbooks"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPSASSIST_", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        return [x.strip() for x in value.split(",")] if isinstance(value, str) else value


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
