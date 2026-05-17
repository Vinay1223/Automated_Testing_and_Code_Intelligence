"""TypeScript / JavaScript adapter — Jest, ESM-compatible imports."""

from __future__ import annotations

from pathlib import Path

from codeintel_engine.models import FunctionTarget, Language, TestFramework
from codeintel_engine.profilers.ts_tree_sitter import TypeScriptProfiler


class TypeScriptAdapter:
    language = Language.TYPESCRIPT
    default_framework = TestFramework.JEST
    file_extensions = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

    def __init__(self) -> None:
        self._profiler = TypeScriptProfiler()

    def discover(self, repo_root: Path) -> list[FunctionTarget]:
        return self._profiler.profile(repo_root)

    def import_hint(self, target: FunctionTarget, repo_root: Path) -> str:
        rel = target.file.relative_to(repo_root) if target.file.is_absolute() else target.file
        # Drop extension; Jest + ts-jest handle resolution.
        module_path = "./" + str(rel.with_suffix("")).replace("\\", "/")
        return f"import {{ {target.name} }} from '{module_path}';"

    def test_filename(self, target: FunctionTarget) -> str:
        return f"{target.name}.test.ts"

    def sandbox_image_env_key(self) -> str:
        return "sandbox_node_image"

    def run_command(self, test_file: Path) -> list[str]:
        return ["npx", "--yes", "jest", "--ci", "--colors=false", str(test_file)]

    def junit_arg(self, output_path: Path) -> list[str]:
        return [
            "--reporters=default",
            "--reporters=jest-junit",
            "--testResultsProcessor=jest-junit",
        ]
