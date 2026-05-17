"""The CodeIntel orchestrator.

Generate -> Validate (in sandbox) -> Heal -> Repeat. Drives one
`FunctionTarget` through a state machine and emits `EngineEvent`s along
the way so the API can stream progress over SSE / WebSocket.

The class is provider-, profiler-, sandbox-, and language-agnostic. All of
those are injected so this code never imports a vendor SDK directly.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from codeintel_engine.adapters.base import LanguageAdapter
from codeintel_engine.adapters.base import registry as adapter_registry
from codeintel_engine.generators.base import Generator, get_generator
from codeintel_engine.models import (
    EngineEvent,
    FunctionTarget,
    GenerationAttempt,
    RunState,
    TestFramework,
    TestRun,
)
from codeintel_engine.providers.base import Provider
from codeintel_engine.sandbox.base import Sandbox, SandboxRequest

logger = logging.getLogger(__name__)


EventCallback = Callable[[EngineEvent], Awaitable[None] | None]


@dataclass
class OrchestratorConfig:
    repo_root: Path
    framework: TestFramework = TestFramework.PYTEST
    max_retries: int = 3
    sandbox_timeout_s: int = 60
    sandbox_memory_mb: int = 512
    sandbox_cpus: float = 1.0
    on_event: EventCallback | None = None
    org_id: str | None = None
    repo: str | None = None
    model: str | None = None
    extra_env: dict[str, str] = field(default_factory=dict)


class Orchestrator:
    """Runs the generate/validate/heal loop for one target."""

    def __init__(
        self,
        *,
        provider: Provider,
        sandbox: Sandbox,
        config: OrchestratorConfig,
        adapter: LanguageAdapter | None = None,
        generator: Generator | None = None,
    ) -> None:
        self._provider = provider
        self._sandbox = sandbox
        self._config = config
        self._generator = generator or get_generator(config.framework)
        self._adapter = adapter

    async def run(self, target: FunctionTarget) -> TestRun:
        adapter = self._adapter or adapter_registry.get(target.language)
        run = TestRun(
            target=target,
            framework=self._generator.framework,
            org_id=self._config.org_id,
            repo=self._config.repo,
        )
        await self._emit(run, RunState.PENDING, "Run created")

        history: list[dict[str, str]] = []
        user_prompt = self._generator.initial_prompt(target, self._config.repo_root)
        system_prompt = self._generator.system_prompt()

        for attempt_idx in range(1, self._config.max_retries + 1):
            run.touch(RunState.GENERATING)
            await self._emit(run, RunState.GENERATING, f"Attempt {attempt_idx}: generating", attempt_idx)

            started = datetime.now(UTC)
            t0 = time.monotonic()
            try:
                resp = await self._provider.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=history or None,
                    model=self._config.model,
                )
            except Exception as e:
                run.touch(RunState.FAILED)
                run.error = f"Provider failure: {e}"
                await self._emit(run, RunState.FAILED, run.error, attempt_idx, severity="error")
                return run

            clean_code = self._generator.postprocess(resp.result.test_code)
            attempt = GenerationAttempt(
                attempt=attempt_idx,
                started_at=started,
                finished_at=datetime.now(UTC),
                provider=resp.provider,
                model=resp.model,
                prompt_tokens=resp.usage.prompt_tokens,
                completion_tokens=resp.usage.completion_tokens,
                test_code=clean_code,
                explanation=resp.result.explanation,
                elapsed_ms=int((time.monotonic() - t0) * 1000),
            )
            run.attempts.append(attempt)
            run.touch(RunState.VALIDATING)
            await self._emit(run, RunState.VALIDATING, "Running sandbox", attempt_idx)

            verdict = await self._sandbox.run(
                SandboxRequest(
                    repo_root=self._config.repo_root,
                    test_file=Path(adapter.test_filename(target)),
                    test_code=clean_code,
                    adapter=adapter,
                    timeout_s=self._config.sandbox_timeout_s,
                    memory_mb=self._config.sandbox_memory_mb,
                    cpus=self._config.sandbox_cpus,
                    env=self._config.extra_env,
                )
            )
            attempt.sandbox_passed = verdict.passed
            attempt.sandbox_log = verdict.log[-4000:]

            if verdict.passed:
                run.final_test_code = clean_code
                run.final_explanation = resp.result.explanation
                run.touch(RunState.PASSED)
                await self._emit(
                    run,
                    RunState.PASSED,
                    f"Sandbox passed ({verdict.tests_passed}/{verdict.tests_collected})",
                    attempt_idx,
                )
                return run

            run.touch(RunState.HEALING)
            await self._emit(
                run,
                RunState.HEALING,
                f"Sandbox failed (exit {verdict.exit_code}); healing",
                attempt_idx,
                severity="warn",
            )
            history = [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": clean_code},
            ]
            user_prompt = self._generator.heal_prompt(target, clean_code, verdict.log)

        run.touch(RunState.FAILED)
        run.error = f"Exhausted {self._config.max_retries} retries"
        await self._emit(run, RunState.FAILED, run.error, severity="error")
        return run

    async def stream(self, target: FunctionTarget) -> AsyncIterator[EngineEvent]:
        """Yield events for streaming endpoints. The full run is the final value."""
        queue: asyncio.Queue[EngineEvent | None] = asyncio.Queue()

        async def on_event(event: EngineEvent) -> None:
            await queue.put(event)

        original = self._config.on_event
        self._config.on_event = on_event
        try:
            task = asyncio.create_task(self.run(target))
            while True:
                getter = asyncio.create_task(queue.get())
                done, _ = await asyncio.wait(
                    {task, getter},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if getter in done:
                    item = getter.result()
                    if item is None:
                        await task
                        return
                    yield item
                else:
                    getter.cancel()
                    try:
                        await getter
                    except asyncio.CancelledError:
                        pass
                    await queue.put(None)
        finally:
            self._config.on_event = original

    async def _emit(
        self,
        run: TestRun,
        state: RunState,
        message: str,
        attempt: int | None = None,
        severity: str = "info",
    ) -> None:
        cb = self._config.on_event
        if cb is None:
            return
        event = EngineEvent(
            run_id=run.id,
            state=state,
            attempt=attempt,
            severity=severity,  # type: ignore[arg-type]
            message=message,
        )
        result = cb(event)
        if asyncio.iscoroutine(result):
            await result
