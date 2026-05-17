"""Sandbox protocol + request DTO.

A sandbox runs a generated test file against the target repository and returns
a `Verdict`. Production deployments MUST use `DockerSandbox`. The
`LocalSandbox` is for developer machines only and is gated behind an
explicit setting (`CODEINTEL_SANDBOX=local`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from codeintel_engine.adapters.base import LanguageAdapter
from codeintel_engine.models import Verdict


@dataclass
class SandboxRequest:
    repo_root: Path
    test_file: Path
    test_code: str
    adapter: LanguageAdapter
    timeout_s: int = 60
    memory_mb: int = 512
    cpus: float = 1.0
    env: dict[str, str] = field(default_factory=dict)


class Sandbox(Protocol):
    name: str

    async def run(self, request: SandboxRequest) -> Verdict: ...
