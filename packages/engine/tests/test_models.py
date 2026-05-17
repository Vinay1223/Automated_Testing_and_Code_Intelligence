from __future__ import annotations

from pathlib import Path

from codeintel_engine.models import (
    TERMINAL_STATES,
    FunctionTarget,
    Language,
    RunState,
    RunSummary,
    TestFramework,
    TestRun,
)


def _target() -> FunctionTarget:
    return FunctionTarget(
        language=Language.PYTHON,
        file=Path("a/b.py"),
        name="foo",
        qualified_name="a.b.foo",
        source_code="def foo():\n    return 1\n",
        start_line=1,
        end_line=2,
    )


def test_function_target_hash_is_stable():
    t1 = _target()
    t2 = _target()
    assert t1.hash == t2.hash


def test_function_target_hash_changes_with_source():
    t1 = _target()
    t2 = t1.model_copy(update={"source_code": "def foo():\n    return 2\n"})
    assert t1.hash != t2.hash


def test_test_run_touch_updates_state_and_timestamp():
    run = TestRun(target=_target(), framework=TestFramework.PYTEST)
    before = run.updated_at
    run.touch(RunState.GENERATING)
    assert run.state is RunState.GENERATING
    assert run.updated_at >= before


def test_run_summary_round_trip():
    run = TestRun(target=_target(), framework=TestFramework.PYTEST, state=RunState.PASSED)
    summary = RunSummary.from_run(run)
    assert summary.passed is True
    assert summary.function == "a.b.foo"
    assert summary.framework is TestFramework.PYTEST


def test_terminal_states_constant():
    assert RunState.PASSED in TERMINAL_STATES
    assert RunState.FAILED in TERMINAL_STATES
    assert RunState.CANCELLED in TERMINAL_STATES
    assert RunState.GENERATING not in TERMINAL_STATES
