"""Engine configuration loaded from environment variables.

This is intentionally lightweight — the API/dashboard own their own config
and only pass what the engine needs into `OrchestratorConfig`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class EngineSettings:
    provider: str = os.getenv("CODEINTEL_PROVIDER", "mock")
    model: str | None = os.getenv("CODEINTEL_MODEL") or None
    sandbox: str = os.getenv("CODEINTEL_SANDBOX", "local")
    sandbox_py_image: str = os.getenv(
        "CODEINTEL_SANDBOX_PY_IMAGE", "ghcr.io/codeintel/sandbox-py:3.12"
    )
    sandbox_node_image: str = os.getenv(
        "CODEINTEL_SANDBOX_NODE_IMAGE", "ghcr.io/codeintel/sandbox-node:20"
    )
    sandbox_timeout_s: int = int(os.getenv("CODEINTEL_SANDBOX_TIMEOUT_S", "60"))
    sandbox_memory_mb: int = int(os.getenv("CODEINTEL_SANDBOX_MEMORY_MB", "512"))
    sandbox_cpus: float = float(os.getenv("CODEINTEL_SANDBOX_CPUS", "1.0"))
    debug: bool = _bool("CODEINTEL_DEBUG", False)


SETTINGS = EngineSettings()
