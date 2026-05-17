from __future__ import annotations

import pytest
from codeintel_engine.providers import MockProvider, ProviderError, get_provider


@pytest.mark.asyncio
async def test_mock_provider_emits_happy_path_and_exception_cases():
    provider = MockProvider()
    resp = await provider.generate(
        system_prompt="you are a tester",
        user_prompt=(
            "Please generate a pytest suite for the function.\n"
            "from sample_repo.math_utils import divide_numbers\n\n"
            "def divide_numbers(a, b):\n"
            "    if b == 0:\n"
            "        raise ValueError('Cannot divide by zero')\n"
            "    return a / b\n"
        ),
    )
    assert "import pytest" in resp.result.test_code
    assert "divide_numbers" in resp.result.test_code
    assert "ValueError" in resp.result.test_code
    assert "```" not in resp.result.test_code


@pytest.mark.asyncio
async def test_mock_provider_handles_jest_prompts():
    provider = MockProvider()
    resp = await provider.generate(
        system_prompt="jest",
        user_prompt=(
            "Generate a Jest suite.\n"
            "import { capitalize } from './string_utils';\n"
            "export function capitalize(s) { if (!s) throw new Error('e'); return s; }\n"
        ),
    )
    assert "describe" in resp.result.test_code
    assert "capitalize" in resp.result.test_code


def test_factory_unknown_provider_raises():
    with pytest.raises(ProviderError):
        get_provider("nope")


def test_factory_returns_mock():
    assert isinstance(get_provider("mock"), MockProvider)
