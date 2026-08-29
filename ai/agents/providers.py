from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(slots=True)
class ProviderResult:
    text: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    prompt_version: str
    provider: str


class ModelProvider(ABC):
    def __init__(self, timeout_seconds: float = 20, retries: int = 2, prompt_version: str = "incident-summary-v1") -> None:
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.prompt_version = prompt_version

    @abstractmethod
    async def summarize(self, evidence: list[dict[str, Any]]) -> ProviderResult:
        raise NotImplementedError


class OfflineProvider(ModelProvider):
    async def summarize(self, evidence: list[dict[str, Any]]) -> ProviderResult:
        ids = [str(item.get("id", "unknown")) for item in evidence]
        text = f"Offline evidence summary: {len(ids)} observations were evaluated ({', '.join(ids[:5])})."
        return ProviderResult(text=text, input_tokens=0, output_tokens=0, estimated_cost_usd=0, prompt_version=self.prompt_version, provider="offline")


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, base_url: str, model: str, api_key: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    async def summarize(self, evidence: list[dict[str, Any]]) -> ProviderResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Summarize only the supplied evidence. Cite IDs. Do not provide private reasoning."},
                {"role": "user", "content": str(evidence)},
            ],
            "temperature": 0,
        }
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            for attempt in range(self.retries + 1):
                try:
                    response = await client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
                    response.raise_for_status()
                    body = response.json()
                    usage = body.get("usage", {})
                    return ProviderResult(
                        text=body["choices"][0]["message"]["content"],
                        input_tokens=int(usage.get("prompt_tokens", 0)),
                        output_tokens=int(usage.get("completion_tokens", 0)),
                        estimated_cost_usd=0,
                        prompt_version=self.prompt_version,
                        provider="openai_compatible",
                    )
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    last_error = exc
                    if attempt < self.retries:
                        await asyncio.sleep(0.2 * 2**attempt)
        raise RuntimeError("Model provider failed within retry policy") from last_error


class OllamaProvider(OpenAICompatibleProvider):
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434/v1", **kwargs: Any) -> None:
        super().__init__(base_url=base_url, model=model, api_key="ollama", **kwargs)
