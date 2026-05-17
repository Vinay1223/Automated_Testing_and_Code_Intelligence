"""Factory that resolves the configured provider name to an instance."""

from __future__ import annotations

from codeintel_engine.providers.anthropic import AnthropicProvider
from codeintel_engine.providers.base import Provider, ProviderError
from codeintel_engine.providers.bedrock import BedrockProvider
from codeintel_engine.providers.groq import GroqProvider
from codeintel_engine.providers.mock import MockProvider
from codeintel_engine.providers.openai import OpenAIProvider

_BUILDERS: dict[str, type[Provider]] = {
    "mock": MockProvider,
    "groq": GroqProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "bedrock": BedrockProvider,
}


def get_provider(name: str) -> Provider:
    key = name.lower().strip()
    builder = _BUILDERS.get(key)
    if builder is None:
        raise ProviderError(
            f"Unknown provider {name!r}. Available: {sorted(_BUILDERS)}"
        )
    return builder()
