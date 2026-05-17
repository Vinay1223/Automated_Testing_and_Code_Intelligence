# `codeintel-engine`

The core engine that powers every CodeIntel surface (API, GitHub App, IDE
extension). Pure-Python, framework-agnostic, fully unit-tested.

## Subpackages

| Module | Responsibility |
|---|---|
| `models` | Pydantic schemas (`FunctionTarget`, `TestRun`, `Verdict`, `RunState`) |
| `adapters` | Per-language adapter (Python, TypeScript) — discovery + import hints |
| `profilers` | Pure-AST extraction of functions worth testing |
| `generators` | LLM-backed test generators per framework (pytest, Jest) |
| `providers` | LLM provider abstraction (Groq, OpenAI, Anthropic, Bedrock, mock) |
| `sandbox` | Test execution: Docker (prod) and local subprocess (dev) |
| `orchestrator` | Generate → execute → self-heal loop with state machine |
| `coverage` | Coverage diff against the user's existing suite |
| `github` | GitHub PR creation + webhook signature verification |
| `cache` | Redis-backed cache for `(function_hash, model)` → result |

## Quickstart

```bash
uv sync
uv run pytest
```

Smoke-test the orchestrator end-to-end against the legacy sample repo with
the mock provider:

```bash
uv run python -m codeintel_engine.cli scan \
  --repo packages/engine/legacy/sample_repo \
  --provider mock
```
