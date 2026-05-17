"""Dockerized sandbox — the production runner.

Launches an ephemeral container with:

* `--network=none` (no exfiltration),
* `--read-only` root filesystem,
* `--tmpfs /tmp:rw,noexec`,
* CPU + memory caps from `EngineSettings`,
* read-only bind mount of the repo,
* a writable bind mount of a per-run temp dir (for the generated test file
  and JUnit output),
* a hard wall-clock timeout enforced from the host.

The runner shells out to the `docker` CLI rather than using a Python
client to avoid pulling a large dep into the engine. In Kubernetes
deployments this class is swapped for a Job-based sandbox in the worker.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import time
import uuid
from pathlib import Path

from codeintel_engine.config import SETTINGS
from codeintel_engine.models import Verdict
from codeintel_engine.sandbox.base import SandboxRequest
from codeintel_engine.sandbox.junit import parse_junit

logger = logging.getLogger(__name__)


class DockerSandboxError(RuntimeError):
    """Raised when the docker CLI is unavailable or fails to launch."""


class DockerSandbox:
    name = "docker"

    def __init__(self, docker_bin: str | None = None) -> None:
        self._docker = docker_bin or shutil.which("docker") or "docker"

    async def run(self, request: SandboxRequest) -> Verdict:
        image = getattr(SETTINGS, request.adapter.sandbox_image_env_key())
        container_name = f"codeintel-{uuid.uuid4().hex[:12]}"

        with tempfile.TemporaryDirectory(prefix="codeintel-docker-") as host_workdir:
            host = Path(host_workdir)
            test_path = host / request.test_file.name
            test_path.write_text(request.test_code, encoding="utf-8")
            junit_path = host / "junit.xml"

            cmd = self._build_docker_command(
                image=image,
                container_name=container_name,
                request=request,
                host_workdir=host,
                test_path=test_path,
                junit_path=junit_path,
            )
            logger.info("DockerSandbox running container %s", container_name)

            start = time.monotonic()
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=request.timeout_s + 5
                )
                duration_ms = int((time.monotonic() - start) * 1000)
                exit_code = proc.returncode if proc.returncode is not None else -1
                log = (stdout + b"\n----STDERR----\n" + stderr).decode(
                    "utf-8", errors="replace"
                )
            except TimeoutError:
                duration_ms = int((time.monotonic() - start) * 1000)
                await self._kill(container_name)
                return Verdict(
                    passed=False,
                    log=f"Container timeout after {request.timeout_s}s",
                    exit_code=124,
                    duration_ms=duration_ms,
                )
            except FileNotFoundError as e:
                raise DockerSandboxError(
                    f"Docker CLI not found at {self._docker!r}. "
                    "Install Docker or set CODEINTEL_SANDBOX=local for dev."
                ) from e

            junit_xml = junit_path.read_text(encoding="utf-8") if junit_path.exists() else None
            stats = parse_junit(junit_xml) if junit_xml else (0, 0, 0)
            return Verdict(
                passed=exit_code == 0,
                log=log,
                exit_code=exit_code,
                duration_ms=duration_ms,
                tests_collected=stats[0],
                tests_passed=stats[1],
                tests_failed=stats[2],
                junit_xml=junit_xml,
            )

    def _build_docker_command(
        self,
        *,
        image: str,
        container_name: str,
        request: SandboxRequest,
        host_workdir: Path,
        test_path: Path,
        junit_path: Path,
    ) -> list[str]:
        run_cmd = list(request.adapter.run_command(Path("/work") / test_path.name))
        run_cmd.extend(request.adapter.junit_arg(Path("/work/junit.xml")))

        return [
            self._docker,
            "run",
            "--rm",
            "--name",
            container_name,
            "--network=none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            f"--memory={request.memory_mb}m",
            f"--cpus={request.cpus}",
            "--pids-limit=128",
            "--security-opt=no-new-privileges",
            "-v",
            f"{request.repo_root}:/repo:ro",
            "-v",
            f"{host_workdir}:/work:rw",
            "-w",
            "/repo",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            image,
            *run_cmd,
        ]

    async def _kill(self, container_name: str) -> None:
        try:
            proc = await asyncio.create_subprocess_exec(
                self._docker,
                "kill",
                container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        except Exception:
            logger.exception("Failed to kill container %s", container_name)
