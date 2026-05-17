"""`python -m codeintel_engine.cli` — local developer entry point.

This is a thin wrapper that wires the engine up exactly like the API
does, but for ad-hoc terminal use. It's used in the docs and the
"30-second demo" GIF.

Usage:
    python -m codeintel_engine.cli scan --repo packages/engine/legacy/sample_repo
    python -m codeintel_engine.cli run --repo packages/engine/legacy/sample_repo \
        --function add_numbers --provider mock
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from codeintel_engine.adapters import (
    registry as adapter_registry,  # noqa: F401 (registration side-effect)
)
from codeintel_engine.adapters.base import registry
from codeintel_engine.coverage import static_coverage
from codeintel_engine.models import FunctionTarget, Language, TestFramework
from codeintel_engine.orchestrator import Orchestrator, OrchestratorConfig
from codeintel_engine.providers import get_provider
from codeintel_engine.sandbox.local_runner import LocalSandbox


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="codeintel", description="CodeIntel CLI")
    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Discover testable functions in a repo")
    scan.add_argument("--repo", type=Path, required=True)
    scan.add_argument(
        "--language",
        choices=[lang.value for lang in Language],
        action="append",
        default=None,
    )
    scan.add_argument("--coverage", action="store_true", help="Include static coverage diff")

    run = sub.add_parser("run", help="Generate + validate a test for one function")
    run.add_argument("--repo", type=Path, required=True)
    run.add_argument("--function", required=True, help="Function name to target")
    run.add_argument("--provider", default="mock")
    run.add_argument("--model", default=None)
    run.add_argument("--framework", choices=[f.value for f in TestFramework], default="pytest")
    run.add_argument("--max-retries", type=int, default=3)
    return p


async def _scan(args: argparse.Namespace) -> int:
    languages = (
        [Language(v) for v in args.language] if args.language else list(Language)
    )
    targets = []
    for lang in languages:
        try:
            adapter = registry.get(lang)
        except LookupError:
            continue
        targets.extend(adapter.discover(args.repo))
    payload: dict[str, object] = {
        "repo": str(args.repo),
        "total": len(targets),
        "functions": [
            {
                "language": t.language.value,
                "file": str(t.file),
                "name": t.name,
                "qualified_name": t.qualified_name,
                "lines": [t.start_line, t.end_line],
                "raises": t.raises,
            }
            for t in targets
        ],
    }
    if args.coverage:
        report = static_coverage(targets, [args.repo / "tests", args.repo])
        payload["coverage"] = {
            "covered": report.covered_functions,
            "total": report.total_functions,
            "pct": report.coverage_pct,
            "uncovered": [t.qualified_name for t in report.uncovered],
        }
    print(json.dumps(payload, indent=2))
    return 0


async def _run(args: argparse.Namespace) -> int:
    targets: list[FunctionTarget] = []
    for lang in Language:
        try:
            adapter = registry.get(lang)
        except LookupError:
            continue
        targets.extend(adapter.discover(args.repo))
    chosen = next((t for t in targets if t.name == args.function), None)
    if chosen is None:
        print(f"function {args.function!r} not found in {args.repo}", file=sys.stderr)
        return 2

    provider = get_provider(args.provider)
    config = OrchestratorConfig(
        repo_root=args.repo.resolve(),
        framework=TestFramework(args.framework),
        max_retries=args.max_retries,
        model=args.model,
    )
    orchestrator = Orchestrator(provider=provider, sandbox=LocalSandbox(), config=config)
    run = await orchestrator.run(chosen)
    print(json.dumps(run.model_dump(mode="json"), indent=2, default=str))
    return 0 if run.state.value == "passed" else 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = _parser().parse_args(argv)
    if args.command == "scan":
        return asyncio.run(_scan(args))
    if args.command == "run":
        return asyncio.run(_run(args))
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
