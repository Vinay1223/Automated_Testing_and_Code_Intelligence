"""Profiler protocol shared by all language-specific profilers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from codeintel_engine.models import FunctionTarget


class Profiler(Protocol):
    """Walks a repository and extracts testable functions."""

    def profile(self, repo_root: Path) -> list[FunctionTarget]: ...


SKIP_DIRECTORIES: frozenset[str] = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".next",
        "out",
        "coverage",
        "legacy",
    }
)


def iter_source_files(
    repo_root: Path,
    extensions: tuple[str, ...],
    skip_test_files: bool = True,
) -> list[Path]:
    """Recursively yield files matching `extensions`, skipping noise."""
    results: list[Path] = []
    root = repo_root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel_parts = path.resolve().relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        if any(part in SKIP_DIRECTORIES for part in rel_parts[:-1]):
            continue
        if path.suffix.lower() not in extensions:
            continue
        name = path.name.lower()
        if skip_test_files and (
            name.startswith("test_")
            or name.endswith(("_test.py", ".test.ts", ".test.tsx", ".test.js", ".spec.ts", ".spec.js"))
        ):
            continue
        results.append(path)
    return results
