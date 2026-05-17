"""Pytest generator — Python + pytest, edge-case aware."""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.adapters.python import PythonAdapter
from codeintel_engine.generators.base import strip_code_fences
from codeintel_engine.models import FunctionTarget, TestFramework

_SYSTEM_PROMPT = """You are a senior Python QA engineer. You write pytest suites.

Hard rules:
- The `test_code` field MUST contain ONLY pure Python source code. NEVER include
  triple backticks, comments like "```python", or any markdown.
- Always import the target function from its module. Never redefine the function
  inside the test file.
- For every explicit `raise X(...)` in the target, write a test that asserts
  `pytest.raises(X)`. Use the exact exception class.
- Use parametrize when it makes 3+ similar cases compact.
- Cover: a happy path, at least one edge case (zero / empty / negative),
  the documented exceptions, and one boundary case.
- Keep tests deterministic. No network, no filesystem, no real time.
"""


class PytestGenerator:
    framework = TestFramework.PYTEST

    def __init__(self) -> None:
        self._adapter = PythonAdapter()

    def system_prompt(self) -> str:
        return _SYSTEM_PROMPT

    def initial_prompt(self, target: FunctionTarget, repo_root: Path) -> str:
        import_hint = self._adapter.import_hint(target, repo_root)
        raises = ", ".join(target.raises) or "none statically detected"
        return (
            f"Generate a complete pytest suite for the function `{target.name}`.\n"
            f"Import it with: `{import_hint}`\n"
            f"Explicit exceptions raised: {raises}\n\n"
            f"--- FUNCTION SOURCE ---\n{target.source_code}\n-----------------------\n"
        )

    def heal_prompt(self, target: FunctionTarget, bad_code: str, sandbox_log: str) -> str:
        return (
            "CRITICAL FIX REQUIRED. The test file you produced failed to run.\n\n"
            "--- YOUR PREVIOUS OUTPUT ---\n"
            f"{bad_code}\n"
            "----------------------------\n\n"
            "--- SANDBOX LOG ---\n"
            f"{sandbox_log[:4000]}\n"
            "-------------------\n\n"
            "Return ONLY clean Python code (no backticks, no markdown). "
            "Ensure the import path is correct and that exception types match the "
            f"raises in the original source for `{target.name}`."
        )

    def postprocess(self, raw_code: str) -> str:
        return strip_code_fences(raw_code)
