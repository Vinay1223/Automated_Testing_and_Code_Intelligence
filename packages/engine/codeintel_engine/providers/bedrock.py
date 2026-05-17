"""AWS Bedrock provider — enterprise / BYO-cloud path.

Customers in regulated industries (banking, defense, healthcare) frequently
require all LLM traffic to stay inside their AWS org. Selecting the Bedrock
provider routes generation calls through `boto3` to a model they own.
"""

from __future__ import annotations

import json
import os
from typing import Any

from codeintel_engine.models import (
    ProviderResponse,
    ProviderUsage,
    TestGenerationResult,
)
from codeintel_engine.providers.base import ProviderError


class BedrockProvider:
    name = "bedrock"
    default_model = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    def __init__(self, region: str | None = None) -> None:
        self._region = region or os.getenv("AWS_BEDROCK_REGION", "us-east-1")

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> ProviderResponse:
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as e:
            raise ProviderError("boto3 is required for the Bedrock provider") from e

        client = boto3.client("bedrock-runtime", region_name=self._region)
        messages: list[dict[str, Any]] = list(history or [])
        messages.append({"role": "user", "content": user_prompt})
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "system": system_prompt,
                "messages": messages,
            }
        )
        response = client.invoke_model(
            modelId=model or self.default_model,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        content_blocks = payload.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        explanation, test_code = _split_explanation_and_code(text)
        return ProviderResponse(
            result=TestGenerationResult(explanation=explanation, test_code=test_code),
            usage=ProviderUsage(
                prompt_tokens=payload.get("usage", {}).get("input_tokens", 0),
                completion_tokens=payload.get("usage", {}).get("output_tokens", 0),
            ),
            model=model or self.default_model,
            provider=self.name,
        )


def _split_explanation_and_code(text: str) -> tuple[str, str]:
    if "```" in text:
        head, _, rest = text.partition("```")
        code, _, _tail = rest.partition("```")
        for prefix in ("python\n", "typescript\n", "ts\n", "javascript\n", "js\n"):
            if code.startswith(prefix):
                code = code[len(prefix):]
                break
        return head.strip() or "Generated test suite.", code.strip()
    return "Generated test suite.", text.strip()
