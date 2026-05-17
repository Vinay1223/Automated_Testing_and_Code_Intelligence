"""`POST /v1/scans` — discover testable functions and report static coverage."""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.adapters.base import registry
from codeintel_engine.coverage import static_coverage
from codeintel_engine.models import FunctionTarget, Language
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from codeintel_api.auth import Principal
from codeintel_api.rate_limit import rate_limit

router = APIRouter(prefix="/v1/scans", tags=["scans"])


class ScanRequest(BaseModel):
    repo_path: Path
    languages: list[Language] | None = None


class ScanResponse(BaseModel):
    repo_path: Path
    total: int
    coverage_pct: float
    uncovered: list[str]
    targets: list[FunctionTarget]


@router.post("", response_model=ScanResponse)
async def create_scan(
    payload: ScanRequest,
    principal: Principal = Depends(rate_limit(per_min=30)),
) -> ScanResponse:
    if not payload.repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {payload.repo_path}")

    languages = payload.languages or list(Language)
    targets: list[FunctionTarget] = []
    for lang in languages:
        try:
            adapter = registry.get(lang)
        except LookupError:
            continue
        targets.extend(adapter.discover(payload.repo_path))

    coverage = static_coverage(targets, [payload.repo_path / "tests", payload.repo_path])
    return ScanResponse(
        repo_path=payload.repo_path,
        total=len(targets),
        coverage_pct=coverage.coverage_pct,
        uncovered=[t.qualified_name for t in coverage.uncovered],
        targets=targets,
    )
