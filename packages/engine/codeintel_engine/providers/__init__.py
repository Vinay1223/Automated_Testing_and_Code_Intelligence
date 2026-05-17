"""LLM provider abstraction.

The orchestrator only knows about `Provider`. Every concrete vendor lives
behind this protocol so customers can BYO-LLM (Bedrock, Azure OpenAI) for
their own privacy / billing reasons without forking the engine.
"""

from codeintel_engine.providers.anthropic import AnthropicProvider
from codeintel_engine.providers.base import Provider, ProviderError
from codeintel_engine.providers.bedrock import BedrockProvider
from codeintel_engine.providers.factory import get_provider
from codeintel_engine.providers.groq import GroqProvider
from codeintel_engine.providers.mock import MockProvider
from codeintel_engine.providers.openai import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "BedrockProvider",
    "GroqProvider",
    "MockProvider",
    "OpenAIProvider",
    "Provider",
    "ProviderError",
    "get_provider",
]
