"""Language adapter protocol + registry.

Every language CodeIntel supports implements this protocol. The orchestrator
never branches on language — it asks the adapter what to do.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from codeintel_engine.models import FunctionTarget, Language, TestFramework


@runtime_checkable
class LanguageAdapter(Protocol):
    language: Language
    default_framework: TestFramework
    file_extensions: tuple[str, ...]

    def discover(self, repo_root: Path) -> list[FunctionTarget]:
        """Walk `repo_root` and return every testable function."""
        ...

    def import_hint(self, target: FunctionTarget, repo_root: Path) -> str:
        """Return a one-line hint the LLM can paste at the top of the test file."""
        ...

    def test_filename(self, target: FunctionTarget) -> str:
        """Conventional test filename for this target (e.g. `test_foo.py`)."""
        ...

    def sandbox_image_env_key(self) -> str:
        """Key on `EngineSettings` whose value names the sandbox image."""
        ...

    def run_command(self, test_file: Path) -> list[str]:
        """Argv to execute inside the sandbox."""
        ...

    def junit_arg(self, output_path: Path) -> list[str]:
        """Extra argv to emit JUnit XML to `output_path`."""
        ...


class AdapterRegistry:
    def __init__(self) -> None:
        self._by_language: dict[Language, LanguageAdapter] = {}

    def register(self, adapter: LanguageAdapter) -> None:
        self._by_language[adapter.language] = adapter

    def get(self, language: Language) -> LanguageAdapter:
        try:
            return self._by_language[language]
        except KeyError as e:
            raise LookupError(f"No adapter registered for {language!r}") from e

    def for_path(self, path: Path) -> LanguageAdapter | None:
        suffix = path.suffix.lower()
        for adapter in self._by_language.values():
            if suffix in adapter.file_extensions:
                return adapter
        return None

    def all(self) -> list[LanguageAdapter]:
        return list(self._by_language.values())


registry = AdapterRegistry()
