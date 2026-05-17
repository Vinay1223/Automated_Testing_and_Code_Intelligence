"""Generator protocol — builds the prompt and post-processes LLM output.

A generator is a thin, deterministic shell around an LLM call. It owns:

* the **system prompt** (framework + assertion style + tone),
* the **user prompt** (function source + import hint + raises hint),
* the **healing prompt** (broken code + sandbox log + corrective hints),
* **post-processing** (strip markdown fences, normalize line endings).

The orchestrator owns retries and state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from codeintel_engine.models import FunctionTarget, TestFramework


class Generator(Protocol):
    framework: TestFramework

    def system_prompt(self) -> str: ...
    def initial_prompt(self, target: FunctionTarget, repo_root: Path) -> str: ...
    def heal_prompt(self, target: FunctionTarget, bad_code: str, sandbox_log: str) -> str: ...
    def postprocess(self, raw_code: str) -> str: ...


def get_generator(framework: TestFramework) -> Generator:
    from codeintel_engine.generators.jest_generator import JestGenerator
    from codeintel_engine.generators.pytest_generator import PytestGenerator

    if framework == TestFramework.PYTEST:
        return PytestGenerator()
    if framework in {TestFramework.JEST, TestFramework.VITEST}:
        return JestGenerator(framework=framework)
    raise ValueError(f"No generator registered for framework {framework!r}")


def strip_code_fences(raw: str) -> str:
    cleaned = raw.strip()
    for fence in ("```python", "```typescript", "```ts", "```javascript", "```js", "```"):
        cleaned = cleaned.replace(fence, "")
    return cleaned.strip() + "\n"
