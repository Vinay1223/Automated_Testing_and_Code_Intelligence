"""Local subprocess sandbox — DEVELOPMENT ONLY.

Runs the user's tests directly on the host. This is unsafe against
untrusted code and is therefore disabled by default. Use it for the engine
test suite and local "happy path" demos. Production paths must use
`DockerSandbox`.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

from codeintel_engine.models import Verdict
from codeintel_engine.sandbox.base import SandboxRequest

logger = logging.getLogger(__name__)


class LocalSandbox:
    name = "local"

    async def run(self, request: SandboxRequest) -> Verdict:
        with tempfile.TemporaryDirectory(prefix="codeintel-local-") as tmp:
            workdir = Path(tmp)
            test_file = workdir / request.test_file.name
            test_file.write_text(request.test_code, encoding="utf-8")

            cmd = self._build_command(request, test_file)
            logger.info("LocalSandbox running: %s", " ".join(cmd))
            env = {**os.environ, **request.env, "PYTHONPATH": str(request.repo_root)}

            start = time.monotonic()
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=request.repo_root,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=request.timeout_s
                )
                duration_ms = int((time.monotonic() - start) * 1000)
                log = (stdout + b"\n----STDERR----\n" + stderr).decode("utf-8", errors="replace")
                exit_code = proc.returncode if proc.returncode is not None else -1
                return Verdict(
                    passed=exit_code == 0,
                    log=log,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                )
            except TimeoutError:
                duration_ms = int((time.monotonic() - start) * 1000)
                return Verdict(
                    passed=False,
                    log=f"Timeout after {request.timeout_s}s",
                    exit_code=124,
                    duration_ms=duration_ms,
                )

    @staticmethod
    def _build_command(request: SandboxRequest, test_file: Path) -> list[str]:
        cmd = list(request.adapter.run_command(test_file))
        if cmd and cmd[0] == "pytest":
            cmd[0:1] = [sys.executable, "-m", "pytest"]
        return cmd
