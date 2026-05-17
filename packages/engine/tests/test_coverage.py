from __future__ import annotations

from pathlib import Path

from codeintel_engine.coverage import static_coverage
from codeintel_engine.profilers.python_ast import PythonAstProfiler


def test_static_coverage_flags_uncovered(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "module.py").write_text(
        "def covered():\n    return 1\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_module.py").write_text(
        "from src.module import covered\ndef test_c(): assert covered() == 1\n",
        encoding="utf-8",
    )
    targets = PythonAstProfiler().profile(src)
    report = static_coverage(targets, [tests])
    assert report.total_functions == 2
    assert report.covered_functions == 1
    assert {t.name for t in report.uncovered} == {"uncovered"}
    assert 0.0 < report.coverage_pct < 100.0
