# `codeintel-api`

FastAPI gateway that powers the dashboard, the IDE extensions, and the
GitHub App. See [`docs/architecture.md`](../../docs/architecture.md).

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET  | `/healthz` | none | Liveness probe |
| GET  | `/readyz` | none | Readiness probe (DB + Redis ping) |
| POST | `/v1/scans` | JWT | Scan a local/uploaded repo and return uncovered functions |
| POST | `/v1/runs` | JWT | Kick off a test-generation run for a single function |
| GET  | `/v1/runs/{id}` | JWT | Fetch a run |
| GET  | `/v1/runs/{id}/stream` | JWT | SSE stream of `EngineEvent`s |
| POST | `/webhooks/github` | HMAC | GitHub App webhook receiver |
| POST | `/webhooks/stripe` | Stripe sig | Stripe metered billing webhook |

## Run locally

```bash
uv run uvicorn codeintel_api.main:app --reload
```

Then `curl http://localhost:8000/healthz` -> `{"status":"ok"}`.
