"""Groq provider (default for the fast tier).

Uses `pydantic-ai` to enforce a structured `TestGenerationResult` payload.
"""

from __future__ import annotations

import os
from typing import Any

from codeintel_engine.models import (
    ProviderResponse,
    ProviderUsage,
    TestGenerationResult,
)
from codeintel_engine.providers.base import ProviderError


class GroqProvider:
    name = "groq"
    default_model = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("GROQ_API_KEY")

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> ProviderResponse:
        if not self._api_key:
            raise ProviderError("GROQ_API_KEY is not set")
        try:
            from pydantic_ai import Agent
            from pydantic_ai.models.groq import GroqModel
        except ImportError as e:  # pragma: no cover
            raise ProviderError("pydantic-ai is not installed") from e

        agent = Agent(
            model=GroqModel(model_name=model or self.default_model),
            output_type=TestGenerationResult,
            system_prompt=system_prompt,
        )
        kwargs: dict[str, Any] = {}
        if history:
            kwargs["message_history"] = history

        result = await agent.run(user_prompt, **kwargs)
        data: TestGenerationResult = result.output
        usage = ProviderUsage()
        try:
            u = result.usage()
            usage = ProviderUsage(
                prompt_tokens=getattr(u, "request_tokens", 0) or 0,
                completion_tokens=getattr(u, "response_tokens", 0) or 0,
            )
        except Exception:
            pass
        return ProviderResponse(
            result=data,
            usage=usage,
            model=model or self.default_model,
            provider=self.name,
        )
