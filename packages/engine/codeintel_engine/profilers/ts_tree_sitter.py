"""TypeScript / JavaScript profiler.

Uses `tree-sitter-language-pack` when available for accurate AST parsing.
Falls back to a regex-based extractor when the native parser is not
installed (CI smoke tests, lightweight dev setups). The fallback is
clearly marked and never used in production sandboxes — production builds
always install the wheel.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from codeintel_engine.models import FunctionTarget, Language
from codeintel_engine.profilers.base import iter_source_files

logger = logging.getLogger(__name__)

_FUNCTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"^export\s+(?:default\s+)?(?:async\s+)?function\s+(?P<name>[A-Za-z_$][\w$]*)\s*\(",
        re.MULTILINE,
    ),
    re.compile(
        r"^(?:export\s+)?(?:async\s+)?function\s+(?P<name>[A-Za-z_$][\w$]*)\s*\(",
        re.MULTILINE,
    ),
    re.compile(
        r"^(?:export\s+)?const\s+(?P<name>[A-Za-z_$][\w$]*)\s*[:=].*?=>",
        re.MULTILINE,
    ),
]


class TypeScriptProfiler:
    file_extensions = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

    def __init__(self) -> None:
        self._parser = self._load_parser()

    @staticmethod
    def _load_parser() -> object | None:
        try:
            from tree_sitter_language_pack import get_parser  # type: ignore[import-not-found]

            return get_parser("typescript")
        except Exception as e:  # pragma: no cover - exercised only when wheel missing
            logger.warning(
                "tree-sitter-language-pack unavailable (%s); falling back to regex profiler.",
                e,
            )
            return None

    def profile(self, repo_root: Path) -> list[FunctionTarget]:
        root = repo_root.resolve()
        targets: list[FunctionTarget] = []
        for file in iter_source_files(root, self.file_extensions):
            targets.extend(self._extract(file, root))
        return targets

    def _extract(self, file: Path, repo_root: Path) -> list[FunctionTarget]:
        try:
            source = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", file, e)
            return []
        if self._parser is not None:
            try:
                return self._extract_with_tree_sitter(file, repo_root, source)
            except Exception as e:
                logger.debug("tree-sitter failed for %s (%s); falling back to regex", file, e)
        return self._extract_with_regex(file, repo_root, source)

    def _extract_with_tree_sitter(
        self, file: Path, repo_root: Path, source: str
    ) -> list[FunctionTarget]:
        assert self._parser is not None
        try:
            tree = self._parser.parse(source.encode("utf-8"))  # type: ignore[attr-defined]
        except TypeError:
            tree = self._parser.parse(source)  # type: ignore[attr-defined]
        root = tree.root_node
        if callable(root):
            root = root()
        targets: list[FunctionTarget] = []
        try:
            rel = file.resolve().relative_to(repo_root)
        except ValueError:
            rel = file
        module_parts = list(rel.with_suffix("").parts)
        for node in _walk(root):
            name = _function_name(node, source)
            if name is None:
                continue
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            targets.append(
                FunctionTarget(
                    language=Language.TYPESCRIPT,
                    file=file,
                    name=name,
                    qualified_name=".".join([*module_parts, name]),
                    source_code=source[node.start_byte : node.end_byte],
                    start_line=start_line,
                    end_line=end_line,
                )
            )
        return targets

    def _extract_with_regex(
        self, file: Path, repo_root: Path, source: str
    ) -> list[FunctionTarget]:
        targets: list[FunctionTarget] = []
        try:
            rel = file.resolve().relative_to(repo_root)
        except ValueError:
            rel = file
        module_parts = list(rel.with_suffix("").parts)
        seen: set[str] = set()
        for pattern in _FUNCTION_PATTERNS:
            for match in pattern.finditer(source):
                name = match.group("name")
                if name in seen:
                    continue
                seen.add(name)
                line = source[: match.start()].count("\n") + 1
                snippet = self._snippet_for(source, match.start())
                targets.append(
                    FunctionTarget(
                        language=Language.TYPESCRIPT,
                        file=file,
                        name=name,
                        qualified_name=".".join([*module_parts, name]),
                        source_code=snippet,
                        start_line=line,
                        end_line=line + snippet.count("\n"),
                    )
                )
        return targets

    @staticmethod
    def _snippet_for(source: str, start: int) -> str:
        # Best-effort: take up to 40 lines from the match.
        end = source.find("\n", start)
        for _ in range(40):
            next_break = source.find("\n", end + 1)
            if next_break == -1:
                break
            end = next_break
        return source[start:end]


_FUNCTION_NODE_TYPES: frozenset[str] = frozenset(
    {
        "function_declaration",
        "function_expression",
        "arrow_function",
        "method_definition",
        "generator_function_declaration",
    }
)


def _walk(node):  # type: ignore[no-untyped-def]
    yield node
    for child in node.children:
        yield from _walk(child)


def _function_name(node, source: str) -> str | None:  # type: ignore[no-untyped-def]
    if node.type not in _FUNCTION_NODE_TYPES:
        return None
    for child in node.children:
        if child.type in {"identifier", "property_identifier"}:
            return source[child.start_byte : child.end_byte]
    # Arrow functions assigned to const: name lives on the parent's left-hand side.
    parent = node.parent
    if parent is not None and parent.type in {"variable_declarator", "lexical_declaration"}:
        for child in parent.children:
            if child.type == "identifier":
                return source[child.start_byte : child.end_byte]
    return None
