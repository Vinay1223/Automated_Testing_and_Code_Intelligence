from __future__ import annotations

from pathlib import Path

from codeintel_engine.profilers.python_ast import PythonAstProfiler
from codeintel_engine.profilers.ts_tree_sitter import TypeScriptProfiler


def test_python_profiler_finds_public_functions(sample_repo: Path):
    targets = PythonAstProfiler().profile(sample_repo)
    names = {t.name for t in targets}
    assert "add_numbers" in names
    assert "divide_numbers" in names
    assert "_private_helper" not in names


def test_python_profiler_detects_raises(sample_repo: Path):
    targets = {t.name: t for t in PythonAstProfiler().profile(sample_repo)}
    assert "ValueError" in targets["divide_numbers"].raises
    assert targets["add_numbers"].raises == []


def test_python_profiler_skips_test_files(tmp_path: Path):
    (tmp_path / "test_module.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (tmp_path / "module.py").write_text("def real(): return 1\n", encoding="utf-8")
    targets = PythonAstProfiler().profile(tmp_path)
    assert [t.name for t in targets] == ["real"]


def test_typescript_profiler_finds_functions(sample_repo: Path):
    targets = TypeScriptProfiler().profile(sample_repo)
    names = {t.name for t in targets}
    assert "capitalize" in names
    assert "shout" in names


def test_python_profiler_qualified_name_uses_relative_path(sample_repo: Path):
    targets = PythonAstProfiler().profile(sample_repo)
    add = next(t for t in targets if t.name == "add_numbers")
    assert add.qualified_name == "math_utils.add_numbers"
