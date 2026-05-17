"""Cache for `(function_hash, model) -> ProviderResponse`.

Two backends are supported:

* `InMemoryCache` — process-local dict, used in tests and the dev API.
* `RedisCache` — used in production. The class never imports `redis` at
  module load time; the caller passes in a client.

A cache hit is roughly 0ms and saves ~1-3 cents per call, which is the
single biggest unit-economics lever.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from codeintel_engine.models import FunctionTarget, ProviderResponse


class Cache(Protocol):
    async def get(self, key: str) -> ProviderResponse | None: ...
    async def set(self, key: str, value: ProviderResponse, ttl_s: int | None = None) -> None: ...


def cache_key(target: FunctionTarget, *, provider: str, model: str) -> str:
    return f"codeintel:gen:{provider}:{model}:{target.hash}"


class InMemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key: str) -> ProviderResponse | None:
        raw = self._data.get(key)
        if raw is None:
            return None
        return ProviderResponse.model_validate_json(raw)

    async def set(self, key: str, value: ProviderResponse, ttl_s: int | None = None) -> None:
        del ttl_s
        self._data[key] = value.model_dump_json()


class RedisCache:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> ProviderResponse | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return ProviderResponse.model_validate(json.loads(raw))

    async def set(self, key: str, value: ProviderResponse, ttl_s: int | None = None) -> None:
        payload = value.model_dump_json()
        if ttl_s:
            await self._client.setex(key, ttl_s, payload)
        else:
            await self._client.set(key, payload)
