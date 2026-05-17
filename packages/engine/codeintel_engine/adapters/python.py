"""Python language adapter — pytest, importable via dotted paths."""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.models import FunctionTarget, Language, TestFramework
from codeintel_engine.profilers.python_ast import PythonAstProfiler


class PythonAdapter:
    language = Language.PYTHON
    default_framework = TestFramework.PYTEST
    file_extensions: tuple[str, ...] = (".py",)

    def __init__(self) -> None:
        self._profiler = PythonAstProfiler()

    def discover(self, repo_root: Path) -> list[FunctionTarget]:
        return self._profiler.profile(repo_root)

    def import_hint(self, target: FunctionTarget, repo_root: Path) -> str:
        rel = target.file.relative_to(repo_root) if target.file.is_absolute() else target.file
        module = ".".join(rel.with_suffix("").parts)
        return f"from {module} import {target.name}"

    def test_filename(self, target: FunctionTarget) -> str:
        return f"test_{target.name}.py"

    def sandbox_image_env_key(self) -> str:
        return "sandbox_py_image"

    def run_command(self, test_file: Path) -> list[str]:
        return ["pytest", "-q", str(test_file)]

    def junit_arg(self, output_path: Path) -> list[str]:
        return [f"--junitxml={output_path}"]
