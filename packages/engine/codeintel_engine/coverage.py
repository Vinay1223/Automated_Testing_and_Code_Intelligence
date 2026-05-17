"""Coverage diff: which discovered functions lack a test today?

This is *static* coverage — we ask the question "does any test file
mention this function name?" not "does pytest cover this line?" Real
line coverage is delegated to the user's existing tooling.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from codeintel_engine.models import CoverageReport, FunctionTarget


def static_coverage(
    targets: Iterable[FunctionTarget], test_dirs: Iterable[Path]
) -> CoverageReport:
    targets_list = list(targets)
    if not targets_list:
        return CoverageReport(total_functions=0, covered_functions=0, uncovered=[])

    test_text = _read_all_tests(test_dirs)
    uncovered = [t for t in targets_list if not _mentions(test_text, t)]
    covered = len(targets_list) - len(uncovered)
    return CoverageReport(
        total_functions=len(targets_list),
        covered_functions=covered,
        uncovered=uncovered,
    )


def _mentions(corpus: str, target: FunctionTarget) -> bool:
    if not target.name:
        return False
    return re.search(rf"\b{re.escape(target.name)}\b", corpus) is not None


def _read_all_tests(test_dirs: Iterable[Path]) -> str:
    chunks: list[str] = []
    for root in test_dirs:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return "\n".join(chunks)
