"""Pydantic schemas shared across the engine, API, and clients.

These types are the public contract of the CodeIntel engine. Keep them
backwards-compatible across minor versions.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"


class TestFramework(str, Enum):
    __test__ = False  # not a pytest test class
    PYTEST = "pytest"
    JEST = "jest"
    VITEST = "vitest"


class RunState(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    HEALING = "healing"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES: frozenset[RunState] = frozenset(
    {RunState.PASSED, RunState.FAILED, RunState.CANCELLED}
)


class FunctionTarget(BaseModel):
    """A single function discovered by a profiler and worth testing."""

    model_config = ConfigDict(frozen=True)

    language: Language
    file: Path
    name: str
    qualified_name: str = Field(
        description="Dotted path: e.g. 'sample_repo.math_utils.add_numbers' or 'src/utils/math.add'.",
    )
    source_code: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    docstring: str | None = None
    raises: list[str] = Field(default_factory=list, description="Exception names statically detected.")

    @property
    def hash(self) -> str:
        """Stable hash used as a cache key for `(function_hash, model)`."""
        h = hashlib.sha256()
        h.update(self.source_code.encode("utf-8"))
        h.update(self.qualified_name.encode("utf-8"))
        return h.hexdigest()


class GenerationAttempt(BaseModel):
    """A single LLM round-trip plus its sandbox verdict."""

    attempt: int = Field(ge=1)
    started_at: datetime
    finished_at: datetime | None = None
    provider: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    test_code: str
    explanation: str
    sandbox_passed: bool | None = None
    sandbox_log: str = ""
    elapsed_ms: int | None = None


class Verdict(BaseModel):
    """Outcome of a single test run inside the sandbox."""

    passed: bool
    log: str
    exit_code: int
    duration_ms: int
    tests_collected: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    junit_xml: str | None = None


class TestRun(BaseModel):
    """A full orchestrator run for one `FunctionTarget`."""

    __test__ = False  # not a pytest test class

    id: UUID = Field(default_factory=uuid4)
    org_id: str | None = None
    repo: str | None = None
    target: FunctionTarget
    framework: TestFramework
    state: RunState = RunState.PENDING
    attempts: list[GenerationAttempt] = Field(default_factory=list)
    final_test_code: str | None = None
    final_explanation: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: str | None = None

    def touch(self, state: RunState) -> None:
        self.state = state
        self.updated_at = datetime.now(UTC)


class TestGenerationResult(BaseModel):
    """Structured output expected from every LLM provider."""

    __test__ = False  # not a pytest test class

    explanation: str = Field(description="Human-readable summary of the cases covered.")
    test_code: str = Field(
        description="Pure, executable test code. No markdown fences."
    )


class ProviderUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


class ProviderResponse(BaseModel):
    result: TestGenerationResult
    usage: ProviderUsage = ProviderUsage()
    model: str
    provider: str


class CoverageReport(BaseModel):
    """Diff between discovered functions and the user's existing test suite."""

    total_functions: int
    covered_functions: int
    uncovered: list[FunctionTarget]

    @property
    def coverage_pct(self) -> float:
        if self.total_functions == 0:
            return 100.0
        return round(100.0 * self.covered_functions / self.total_functions, 2)


class ScanRequest(BaseModel):
    repo_path: Path
    languages: list[Language] = Field(default_factory=lambda: [Language.PYTHON, Language.TYPESCRIPT])
    max_targets: int | None = Field(default=None, ge=1)


class RunRequest(BaseModel):
    target: FunctionTarget
    framework: TestFramework
    max_retries: int = Field(default=3, ge=1, le=10)
    provider: str | None = None
    model: str | None = None


class RunSummary(BaseModel):
    """Lightweight view used by the dashboard and API list endpoints."""

    id: UUID
    state: RunState
    function: str
    file: Path
    framework: TestFramework
    attempts: int
    passed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_run(cls, run: TestRun) -> RunSummary:
        return cls(
            id=run.id,
            state=run.state,
            function=run.target.qualified_name,
            file=run.target.file,
            framework=run.framework,
            attempts=len(run.attempts),
            passed=run.state == RunState.PASSED,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )


SeverityLevel = Literal["info", "warn", "error"]


class EngineEvent(BaseModel):
    """Structured event emitted by the orchestrator for streaming / observability."""

    run_id: UUID
    state: RunState
    attempt: int | None = None
    severity: SeverityLevel = "info"
    message: str
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))
