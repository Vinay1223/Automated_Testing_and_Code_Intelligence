from __future__ import annotations

from pathlib import Path

import pytest
from codeintel_engine.adapters import registry  # noqa: F401 (registers adapters)
from codeintel_engine.models import (
    EngineEvent,
    FunctionTarget,
    Language,
    ProviderResponse,
    ProviderUsage,
    RunState,
    TestGenerationResult,
    Verdict,
)
from codeintel_engine.orchestrator import Orchestrator, OrchestratorConfig
from codeintel_engine.sandbox.base import Sandbox, SandboxRequest


class _ScriptedProvider:
    name = "scripted"
    default_model = "scripted-1"

    def __init__(self, codes: list[str]):
        self._codes = list(codes)
        self.calls = 0

    async def generate(self, *, system_prompt, user_prompt, history=None, model=None):
        self.calls += 1
        if not self._codes:
            raise RuntimeError("no more scripted responses")
        return ProviderResponse(
            result=TestGenerationResult(
                explanation=f"call {self.calls}",
                test_code=self._codes.pop(0),
            ),
            usage=ProviderUsage(),
            model=model or self.default_model,
            provider=self.name,
        )


class _ScriptedSandbox(Sandbox):
    name = "scripted"

    def __init__(self, verdicts: list[bool]):
        self._verdicts = list(verdicts)
        self.calls = 0

    async def run(self, request: SandboxRequest) -> Verdict:
        self.calls += 1
        passed = self._verdicts.pop(0)
        return Verdict(
            passed=passed,
            log="ok" if passed else "boom",
            exit_code=0 if passed else 1,
            duration_ms=10,
            tests_collected=3,
            tests_passed=3 if passed else 0,
            tests_failed=0 if passed else 3,
        )


def _target(name: str = "add_numbers") -> FunctionTarget:
    return FunctionTarget(
        language=Language.PYTHON,
        file=Path("math_utils.py"),
        name=name,
        qualified_name=f"math_utils.{name}",
        source_code=f"def {name}(a, b):\n    return a + b\n",
        start_line=1,
        end_line=2,
    )


@pytest.mark.asyncio
async def test_orchestrator_passes_on_first_attempt(tmp_path: Path):
    provider = _ScriptedProvider(["def test_ok():\n    assert True\n"])
    sandbox = _ScriptedSandbox([True])
    events: list[EngineEvent] = []

    async def on_event(ev):
        events.append(ev)

    cfg = OrchestratorConfig(repo_root=tmp_path, on_event=on_event, max_retries=3)
    orch = Orchestrator(provider=provider, sandbox=sandbox, config=cfg)
    run = await orch.run(_target())

    assert run.state is RunState.PASSED
    assert len(run.attempts) == 1
    assert provider.calls == 1
    assert sandbox.calls == 1
    assert run.final_test_code is not None
    states = [e.state for e in events]
    assert RunState.PASSED in states


@pytest.mark.asyncio
async def test_orchestrator_self_heals(tmp_path: Path):
    provider = _ScriptedProvider(
        [
            "def test_bad():\n    assert False\n",
            "def test_good():\n    assert True\n",
        ]
    )
    sandbox = _ScriptedSandbox([False, True])
    cfg = OrchestratorConfig(repo_root=tmp_path, max_retries=3)
    orch = Orchestrator(provider=provider, sandbox=sandbox, config=cfg)
    run = await orch.run(_target())

    assert run.state is RunState.PASSED
    assert len(run.attempts) == 2
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_orchestrator_gives_up_after_max_retries(tmp_path: Path):
    provider = _ScriptedProvider(["x" for _ in range(5)])
    sandbox = _ScriptedSandbox([False, False, False])
    cfg = OrchestratorConfig(repo_root=tmp_path, max_retries=3)
    orch = Orchestrator(provider=provider, sandbox=sandbox, config=cfg)
    run = await orch.run(_target())

    assert run.state is RunState.FAILED
    assert len(run.attempts) == 3
    assert run.error is not None


@pytest.mark.asyncio
async def test_orchestrator_marks_failed_on_provider_error(tmp_path: Path):
    class _Broken:
        name = "broken"
        default_model = "x"

        async def generate(self, **_):
            raise RuntimeError("upstream 500")

    cfg = OrchestratorConfig(repo_root=tmp_path, max_retries=3)
    orch = Orchestrator(
        provider=_Broken(),  # type: ignore[arg-type]
        sandbox=_ScriptedSandbox([]),
        config=cfg,
    )
    run = await orch.run(_target())
    assert run.state is RunState.FAILED
    assert "upstream 500" in (run.error or "")
