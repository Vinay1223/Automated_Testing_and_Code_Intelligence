"""`/v1/runs` — submit and inspect orchestrator runs."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from codeintel_engine.adapters.base import registry
from codeintel_engine.models import (
    FunctionTarget,
    Language,
    RunSummary,
    TestFramework,
    TestRun,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from codeintel_api.auth import Principal
from codeintel_api.engine_factory import build_orchestrator
from codeintel_api.rate_limit import rate_limit
from codeintel_api.settings import get_settings

router = APIRouter(prefix="/v1/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    repo_path: Path
    function_name: str
    language: Language = Language.PYTHON
    framework: TestFramework = TestFramework.PYTEST
    max_retries: int = 3
    model: str | None = None


@router.post("", response_model=TestRun)
async def create_run(
    payload: CreateRunRequest,
    request: Request,
    principal: Principal = Depends(rate_limit(per_min=20)),
) -> TestRun:
    if not payload.repo_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {payload.repo_path}")

    target = _find_target(payload.repo_path, payload.language, payload.function_name)
    settings = get_settings()
    orchestrator = build_orchestrator(
        settings, repo_root=payload.repo_path, org_id=principal.org_id
    )
    orchestrator._config.max_retries = payload.max_retries
    orchestrator._config.framework = payload.framework
    if payload.model:
        orchestrator._config.model = payload.model

    run = await orchestrator.run(target)
    request.app.state.runs.save(run)
    return run


@router.get("", response_model=list[RunSummary])
async def list_runs(
    principal: Principal = Depends(rate_limit(per_min=120)),
    request: Request = None,  # type: ignore[assignment]
) -> list[RunSummary]:
    assert request is not None
    runs = request.app.state.runs.list_recent(limit=100, org_id=principal.org_id)
    return [RunSummary.from_run(r) for r in runs]


@router.get("/{run_id}", response_model=TestRun)
async def get_run(
    run_id: UUID,
    request: Request,
    principal: Principal = Depends(rate_limit(per_min=240)),
) -> TestRun:
    run = request.app.state.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.org_id and run.org_id != principal.org_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: UUID,
    request: Request,
    principal: Principal = Depends(rate_limit(per_min=60)),
) -> StreamingResponse:
    """SSE stream of `EngineEvent`s. Used by the dashboard run-detail page."""
    run = request.app.state.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.org_id and run.org_id != principal.org_id:
        raise HTTPException(status_code=404, detail="Run not found")

    async def _gen():
        yield f"event: snapshot\ndata: {run.model_dump_json()}\n\n"
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


def _find_target(repo: Path, language: Language, name: str) -> FunctionTarget:
    try:
        adapter = registry.get(language)
    except LookupError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    for t in adapter.discover(repo):
        if t.name == name:
            return t
    raise HTTPException(status_code=404, detail=f"Function {name!r} not found in {repo}")
