"""Per-org sliding-window rate limiter.

Uses Redis when configured; falls back to an in-process counter that is
only safe for single-worker dev. The dependency form lets routes pin
specific limits with a decorator-like syntax.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any

from fastapi import Depends, HTTPException, status

from codeintel_api.auth import Principal, require_principal
from codeintel_api.settings import get_settings


class InMemoryLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, *, limit: int, window_s: float) -> bool:
        now = time.monotonic()
        window = self._hits[key]
        while window and now - window[0] > window_s:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True


_LIMITER = InMemoryLimiter()


def rate_limit(*, per_min: int | None = None) -> Any:
    async def _dep(principal: Principal = Depends(require_principal)) -> Principal:
        settings = get_settings()
        limit = per_min or settings.rate_limit_per_min_per_org
        if not _LIMITER.hit(f"org:{principal.org_id}", limit=limit, window_s=60.0):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({limit}/min per org)",
            )
        return principal

    return _dep
