"""Flaky test detection.

A test is "flaky" if it doesn't deterministically pass or fail given the
same code under test. We detect this by:

1. Re-running each generated test N times back-to-back.
2. Recording the exit code and a stable hash of the failure log.
3. If results disagree -> flag.

We surface the result in the run detail page and bias the orchestrator to
*not* commit flaky tests to a PR.
"""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from codeintel_engine.models import Verdict


@dataclass(frozen=True)
class FlakeReport:
    runs: int
    passes: int
    failures: int
    is_flaky: bool
    distinct_failure_hashes: int


async def detect_flake(
    runner: Callable[[], Awaitable[Verdict]],
    *,
    runs: int = 5,
) -> FlakeReport:
    """Run `runner` `runs` times and report flakiness.

    `runner` should be a closure that executes the same test in the same
    sandbox and returns a fresh `Verdict` each time.
    """
    passes = failures = 0
    hashes: set[str] = set()
    for _ in range(runs):
        verdict = await runner()
        if verdict.passed:
            passes += 1
        else:
            failures += 1
            hashes.add(_log_hash(verdict.log))
    is_flaky = passes > 0 and failures > 0
    return FlakeReport(
        runs=runs,
        passes=passes,
        failures=failures,
        is_flaky=is_flaky,
        distinct_failure_hashes=len(hashes),
    )


def _log_hash(log: str) -> str:
    # Strip wall-clock timings before hashing so non-flaky failures
    # collapse to a single hash.
    import re

    normalized = re.sub(r"\d+\.\d+s", "Xs", log)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
