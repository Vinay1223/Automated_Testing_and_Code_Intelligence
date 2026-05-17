"""Deterministic provider used by tests and self-hosted air-gapped demos.

It does not call any network. It inspects the user prompt and emits a
plausible test stub that exercises:

* a happy path,
* a zero / falsy input edge case,
* any explicitly mentioned exception (e.g. `ValueError`, `TypeError`).
"""

from __future__ import annotations

import re
from typing import Any

from codeintel_engine.models import (
    ProviderResponse,
    ProviderUsage,
    TestGenerationResult,
)


class MockProvider:
    name = "mock"
    default_model = "mock-1"

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> ProviderResponse:
        del system_prompt, history
        framework = _infer_framework(user_prompt)
        import_hint = _extract_import_hint(user_prompt) or ""
        func_name = _extract_function_name(user_prompt) or "target_function"
        raises = _extract_raises(user_prompt)

        if framework == "jest":
            test_code = _jest_template(import_hint, func_name, raises)
        else:
            test_code = _pytest_template(import_hint, func_name, raises)

        return ProviderResponse(
            result=TestGenerationResult(
                explanation=(
                    f"Generated a deterministic mock test suite for `{func_name}` "
                    "covering a happy path, an edge case, and explicit exceptions "
                    f"({', '.join(raises) or 'none detected'})."
                ),
                test_code=test_code,
            ),
            usage=ProviderUsage(prompt_tokens=64, completion_tokens=128, cost_usd=0.0),
            model=model or self.default_model,
            provider=self.name,
        )


def _infer_framework(prompt: str) -> str:
    return "jest" if re.search(r"\b(jest|vitest)\b", prompt, re.IGNORECASE) else "pytest"


def _extract_import_hint(prompt: str) -> str | None:
    m = re.search(r"(from\s+[\w.]+\s+import\s+\w+)", prompt)
    if m:
        return m.group(1)
    m = re.search(r"(import\s*\{\s*\w+\s*\}\s*from\s*['\"][^'\"]+['\"];?)", prompt)
    return m.group(1) if m else None


def _extract_function_name(prompt: str) -> str | None:
    m = re.search(r"\bdef\s+(\w+)\s*\(", prompt)
    if m:
        return m.group(1)
    m = re.search(r"\bfunction\s+(\w+)\s*\(", prompt)
    if m:
        return m.group(1)
    m = re.search(r"^\s*(?:export\s+)?const\s+(\w+)\s*=", prompt, re.MULTILINE)
    return m.group(1) if m else None


def _extract_raises(prompt: str) -> list[str]:
    return re.findall(r"raise\s+(\w+Error)", prompt)


def _pytest_template(import_hint: str, func: str, raises: list[str]) -> str:
    lines: list[str] = ["import pytest", ""]
    if import_hint:
        lines.append(import_hint)
    lines.extend(
        [
            "",
            "",
            f"def test_{func}_happy_path():",
            f"    result = {func}(1, 1)",
            "    assert result is not None",
            "",
        ]
    )
    for exc in raises or []:
        lines.extend(
            [
                f"def test_{func}_raises_{exc.lower()}():",
                f"    with pytest.raises({exc}):",
                f"        {func}(0, 0)",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def _jest_template(import_hint: str, func: str, raises: list[str]) -> str:
    lines: list[str] = []
    if import_hint:
        lines.append(import_hint)
    lines.extend(
        [
            "",
            f"describe('{func}', () => {{",
            "  it('handles the happy path', () => {",
            f"    const result = {func}(1, 1);",
            "    expect(result).toBeDefined();",
            "  });",
        ]
    )
    for exc in raises or []:
        lines.extend(
            [
                f"  it('throws {exc} on invalid input', () => {{",
                f"    expect(() => {func}(0, 0)).toThrow();",
                "  });",
            ]
        )
    lines.append("});")
    return "\n".join(lines) + "\n"


def __getattr__(name: str) -> Any:  # pragma: no cover
    raise AttributeError(name)
