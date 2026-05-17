"""Jest / Vitest generator — TypeScript + JavaScript."""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.adapters.typescript import TypeScriptAdapter
from codeintel_engine.generators.base import strip_code_fences
from codeintel_engine.models import FunctionTarget, TestFramework

_SYSTEM_PROMPT_TPL = """You are a senior TypeScript QA engineer. You write {framework_name} suites.

Hard rules:
- The `test_code` field MUST contain ONLY pure TypeScript source code. NEVER include
  triple backticks, language tags, or any markdown.
- Always import the target function from its source module using the import path
  the user provides. Never redefine the function inside the test file.
- For every documented thrown error, write `expect(() => ...).toThrow(...)`.
- Use `describe` / `it` blocks and group related cases. Use `it.each` when there
  are 3+ similar cases.
- Cover: a happy path, at least one edge case (zero / empty / negative), every
  thrown error from the source, and one boundary case.
- Tests must be deterministic — no network, no filesystem, no real timers.
"""


class JestGenerator:
    def __init__(self, framework: TestFramework = TestFramework.JEST) -> None:
        if framework not in {TestFramework.JEST, TestFramework.VITEST}:
            raise ValueError(f"JestGenerator does not support {framework!r}")
        self.framework = framework
        self._adapter = TypeScriptAdapter()

    @property
    def framework_name(self) -> str:
        return "Jest" if self.framework == TestFramework.JEST else "Vitest"

    def system_prompt(self) -> str:
        return _SYSTEM_PROMPT_TPL.format(framework_name=self.framework_name)

    def initial_prompt(self, target: FunctionTarget, repo_root: Path) -> str:
        import_hint = self._adapter.import_hint(target, repo_root)
        return (
            f"Generate a complete {self.framework_name} suite for `{target.name}`.\n"
            f"Use this import: `{import_hint}`\n\n"
            f"--- FUNCTION SOURCE ---\n{target.source_code}\n-----------------------\n"
        )

    def heal_prompt(self, target: FunctionTarget, bad_code: str, sandbox_log: str) -> str:
        return (
            f"CRITICAL FIX REQUIRED. The {self.framework_name} suite failed to run.\n\n"
            "--- YOUR PREVIOUS OUTPUT ---\n"
            f"{bad_code}\n"
            "----------------------------\n\n"
            "--- SANDBOX LOG ---\n"
            f"{sandbox_log[:4000]}\n"
            "-------------------\n\n"
            f"Return ONLY clean TypeScript code (no markdown). Ensure the import "
            f"path resolves to `{target.name}` and that thrown errors are matched "
            "with `.toThrow()`."
        )

    def postprocess(self, raw_code: str) -> str:
        return strip_code_fences(raw_code)
