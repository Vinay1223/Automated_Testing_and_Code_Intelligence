"""Python AST profiler — extracts every function and async function.

This is the production replacement for `legacy/revision_3_profiler.py`.
The key improvements:

* Recursive in a safe way (skips virtualenvs, build artifacts, legacy dirs).
* Captures `start_line`, `end_line`, docstring, and statically-detected
  `raise X` exceptions so the generator prompt can be much more precise.
* Builds a qualified name from the file's path so the orchestrator can
  generate a correct import without re-running heuristics.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from codeintel_engine.models import FunctionTarget, Language
from codeintel_engine.profilers.base import iter_source_files

logger = logging.getLogger(__name__)

_PRIVATE_PREFIX = "_"


class PythonAstProfiler:
    file_extensions = (".py",)

    def profile(self, repo_root: Path) -> list[FunctionTarget]:
        root = repo_root.resolve()
        targets: list[FunctionTarget] = []
        for file in iter_source_files(root, self.file_extensions):
            targets.extend(self._extract(file, root))
        return targets

    def _extract(self, file: Path, repo_root: Path) -> list[FunctionTarget]:
        try:
            source = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", file, e)
            return []
        try:
            tree = ast.parse(source, filename=str(file))
        except SyntaxError as e:
            logger.warning("Skipping %s due to syntax error: %s", file, e)
            return []

        try:
            rel = file.resolve().relative_to(repo_root)
        except ValueError:
            rel = file
        module_parts = list(rel.with_suffix("").parts)

        targets: list[FunctionTarget] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith(_PRIVATE_PREFIX) and not node.name.startswith("__"):
                continue
            source_segment = ast.get_source_segment(source, node)
            if source_segment is None:
                continue
            targets.append(
                FunctionTarget(
                    language=Language.PYTHON,
                    file=file,
                    name=node.name,
                    qualified_name=".".join([*module_parts, node.name]),
                    source_code=source_segment,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=ast.get_docstring(node),
                    raises=self._collect_raises(node),
                )
            )
        return targets

    @staticmethod
    def _collect_raises(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        names: list[str] = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise) and sub.exc is not None:
                exc = sub.exc
                if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
                    names.append(exc.func.id)
                elif isinstance(exc, ast.Name):
                    names.append(exc.id)
        seen: dict[str, None] = {}
        for n in names:
            seen.setdefault(n)
        return list(seen.keys())
