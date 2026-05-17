"""Constructs an `Orchestrator` from API settings.

Kept tiny so route handlers stay readable.
"""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.adapters import registry  # noqa: F401 (registration side-effect)
from codeintel_engine.orchestrator import Orchestrator, OrchestratorConfig
from codeintel_engine.providers import get_provider
from codeintel_engine.sandbox.docker_runner import DockerSandbox
from codeintel_engine.sandbox.local_runner import LocalSandbox

from codeintel_api.settings import Settings


def build_orchestrator(settings: Settings, *, repo_root: Path, org_id: str | None) -> Orchestrator:
    provider = get_provider(settings.provider)
    sandbox = LocalSandbox() if settings.sandbox == "local" else DockerSandbox()
    config = OrchestratorConfig(
        repo_root=repo_root.resolve(),
        org_id=org_id,
        model=settings.model,
    )
    return Orchestrator(provider=provider, sandbox=sandbox, config=config)
