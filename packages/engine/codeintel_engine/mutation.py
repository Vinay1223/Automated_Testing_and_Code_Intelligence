"""Mutation testing integration.

Mutation testing answers the actually-important question: "do my tests
catch real bugs?" A mutation runner makes a small change to the source
(e.g. flip `==` to `!=`) and re-runs the suite. A *survived* mutation
means the tests didn't detect the bug.

This module is a thin orchestration layer over the language-native
mutators — `mutmut` for Python, `stryker` for JavaScript / TypeScript.
The orchestration is identical: spawn the mutator inside the same
sandbox we use for normal runs, parse its JSON report, and emit a
`MutationReport`.

In v1 this is an optional check exposed via:

* `codeintel mutate --repo <path> --function <name>`
* a "Run mutation testing" button on the dashboard run-detail page,
* a GitHub PR comment when a Team-tier customer opts in.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from codeintel_engine.models import Language

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MutationReport:
    total: int
    killed: int
    survived: int
    timeout: int
    score: float  # 0..100, higher is better

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 60:
            return "C"
        if self.score >= 40:
            return "D"
        return "F"


def parse_mutmut_json(blob: str) -> MutationReport:
    """Parse mutmut's `--json` output. Tolerant of partial reports."""
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        logger.warning("mutmut JSON parse failed")
        return MutationReport(0, 0, 0, 0, 0.0)
    killed = int(data.get("killed", 0))
    survived = int(data.get("survived", 0))
    timeout = int(data.get("timeout", 0))
    total = killed + survived + timeout
    score = 100.0 * killed / total if total else 0.0
    return MutationReport(total, killed, survived, timeout, round(score, 2))


def parse_stryker_json(blob: str) -> MutationReport:
    """Parse stryker's `mutation-report.json` (incremental schema)."""
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return MutationReport(0, 0, 0, 0, 0.0)
    killed = survived = timeout = 0
    for file_report in data.get("files", {}).values():
        for m in file_report.get("mutants", []):
            status = m.get("status")
            if status == "Killed":
                killed += 1
            elif status == "Survived":
                survived += 1
            elif status == "Timeout":
                timeout += 1
    total = killed + survived + timeout
    score = 100.0 * killed / total if total else 0.0
    return MutationReport(total, killed, survived, timeout, round(score, 2))


def mutation_command(language: Language, target_file: Path) -> list[str]:
    """argv to run mutation testing inside the appropriate sandbox image."""
    if language is Language.PYTHON:
        return ["mutmut", "run", "--paths-to-mutate", str(target_file), "--simple-output"]
    return [
        "npx",
        "stryker",
        "run",
        "--mutate",
        str(target_file),
        "--reporters",
        "json",
    ]
