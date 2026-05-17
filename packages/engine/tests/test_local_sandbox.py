from __future__ import annotations

from pathlib import Path

import pytest
from codeintel_engine.adapters.python import PythonAdapter
from codeintel_engine.sandbox.base import SandboxRequest
from codeintel_engine.sandbox.local_runner import LocalSandbox


@pytest.mark.asyncio
async def test_local_sandbox_runs_passing_test(tmp_path: Path):
    (tmp_path / "math_utils.py").write_text(
        "def add_numbers(a, b):\n    return a + b\n", encoding="utf-8"
    )
    test_code = (
        "from math_utils import add_numbers\n\n"
        "def test_add():\n"
        "    assert add_numbers(2, 3) == 5\n"
    )
    verdict = await LocalSandbox().run(
        SandboxRequest(
            repo_root=tmp_path,
            test_file=Path("test_add_numbers.py"),
            test_code=test_code,
            adapter=PythonAdapter(),
            timeout_s=30,
        )
    )
    assert verdict.passed, verdict.log
    assert verdict.exit_code == 0


@pytest.mark.asyncio
async def test_local_sandbox_reports_failure(tmp_path: Path):
    (tmp_path / "math_utils.py").write_text(
        "def add_numbers(a, b):\n    return a + b\n", encoding="utf-8"
    )
    verdict = await LocalSandbox().run(
        SandboxRequest(
            repo_root=tmp_path,
            test_file=Path("test_bad.py"),
            test_code="def test_bad():\n    assert 1 == 2\n",
            adapter=PythonAdapter(),
            timeout_s=30,
        )
    )
    assert not verdict.passed
    assert verdict.exit_code != 0
