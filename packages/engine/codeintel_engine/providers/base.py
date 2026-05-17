"""Provider protocol + shared error type."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from codeintel_engine.models import ProviderResponse


class ProviderError(RuntimeError):
    """Raised when an LLM provider call fails after retries."""


@runtime_checkable
class Provider(Protocol):
    name: str
    default_model: str

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> ProviderResponse: ...
