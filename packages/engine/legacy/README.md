# Legacy prototypes

These scripts are the original `revision_*` prototypes that proved the
"generate → execute → self-heal" agent loop. They are kept here as
**reference implementations only** and are not used by the production
CodeIntel engine.

The production code lives in [`packages/engine/codeintel_engine`](../codeintel_engine).

| File | Mapped to in the engine |
|------|--------------------------|
| `revision_1_agent.py` | `orchestrator.py` (early retry loop) |
| `revision_2_agent.py` | `orchestrator.py` (history-aware retry loop) |
| `revision_3_profiler.py` | `profilers/python_ast.py` |
| `revision_3_pipeline.py` | `orchestrator.py` (multi-target loop) |
| `revision_4_pr_engine.py` | `github/pr_engine.py` |
| `target_code.py`, `sample_repo/` | Fixtures used by engine integration tests |
| `test_github.py` | Replaced by `github/client.py` |

To run the original prototypes (requires `GROQ_API_KEY`):

```bash
cd packages/engine/legacy
uv run python revision_4_pr_engine.py
```

These files will be removed in a future major release.
