from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.schemas.models import Evidence
from app.services.orchestration import AgentOrchestrator


class BrokenResponses:
    async def create(self, **_kwargs):
        raise TimeoutError("provider unavailable")


class BrokenClient:
    responses = BrokenResponses()


@pytest.mark.asyncio
async def test_openai_outage_returns_typed_partial_findings() -> None:
    orchestrator = AgentOrchestrator(Settings(ai_mode="offline", openai_agent_concurrency=11))
    orchestrator._client = BrokenClient()
    evidence = [Evidence(id="EV-1", kind="metric", label="Pool saturation", source_id="metric-1", timestamp=datetime.now(UTC), stance="supports", reliability=0.9, excerpt="value=98", explanation="Pool is saturated")]
    published: list[str] = []

    async def publish(event_type: str, _data: dict) -> None:
        published.append(event_type)

    findings = await orchestrator.run("inc-test", evidence, publish)
    assert len(findings) == 11
    assert all(item.status == "partial" and item.error for item in findings)
    assert published.count("agent.completed") == 11
