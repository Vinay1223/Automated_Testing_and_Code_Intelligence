"""OpenAI provider (accurate tier)."""

from __future__ import annotations

import os
from typing import Any

from codeintel_engine.models import (
    ProviderResponse,
    ProviderUsage,
    TestGenerationResult,
)
from codeintel_engine.providers.base import ProviderError


class OpenAIProvider:
    name = "openai"
    default_model = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> ProviderResponse:
        if not self._api_key:
            raise ProviderError("OPENAI_API_KEY is not set")
        try:
            from pydantic_ai import Agent
            from pydantic_ai.models.openai import OpenAIModel
        except ImportError as e:  # pragma: no cover
            raise ProviderError("pydantic-ai is not installed") from e

        agent = Agent(
            model=OpenAIModel(model_name=model or self.default_model),
            output_type=TestGenerationResult,
            system_prompt=system_prompt,
        )
        kwargs: dict[str, Any] = {}
        if history:
            kwargs["message_history"] = history
        result = await agent.run(user_prompt, **kwargs)
        return ProviderResponse(
            result=result.output,
            usage=ProviderUsage(),
            model=model or self.default_model,
            provider=self.name,
        )
