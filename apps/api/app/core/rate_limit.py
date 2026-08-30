from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.errors import OpsAssistError
from app.core.security import Principal, current_principal

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover - development-only fallback
    Redis = None  # type: ignore[assignment,misc]


_local: dict[str, deque[datetime]] = defaultdict(deque)
_lock = asyncio.Lock()
_redis: Redis | None = None


async def enforce_rate_limit(request: Request, principal: Annotated[Principal, Depends(current_principal)]) -> None:
    global _redis
    settings = get_settings()
    identity = principal.subject or (request.client.host if request.client else "unknown")
    tenant = principal.tenant_id
    minute = int(datetime.now(UTC).timestamp() // 60)
    key = f"opsassist:ratelimit:{tenant}:{identity}:{minute}"
    if settings.redis_url and Redis is not None:
        if _redis is None:
            _redis = Redis.from_url(settings.redis_url, decode_responses=True)
        count = await _redis.incr(key)
        if count == 1:
            await _redis.expire(key, 70)
        if count > settings.rate_limit_per_minute:
            raise OpsAssistError("RATE_LIMITED", "Request rate limit exceeded.", 429)
        return
    async with _lock:
        now = datetime.now(UTC)
        window = _local[key]
        while window and window[0] < now - timedelta(minutes=1):
            window.popleft()
        if len(window) >= settings.rate_limit_per_minute:
            raise OpsAssistError("RATE_LIMITED", "Request rate limit exceeded.", 429)
        window.append(now)
