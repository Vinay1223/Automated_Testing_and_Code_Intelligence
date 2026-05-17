# CodeIntel — consolidated documentation report

This document merges the project’s **canonical documentation** into one place for onboarding, security review, and operations. **Authoritative sources** remain the files linked in [Source index](#source-index); this report may lag those files if they diverge.

**Last assembled from:** root `README.md`, `docs/*.md`, `apps/api/README.md`, `packages/engine/README.md`, `apps/vscode-extension/README.md`, `packages/engine/legacy/README.md`, `.github/workflows/ci.yml`, and root `pyproject.toml`.

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [Repository layout](#2-repository-layout)
3. [Architecture](#3-architecture)
4. [Security & SOC 2 readiness](#4-security--soc-2-readiness)
5. [Self-hosting](#5-self-hosting)
6. [Pricing & metering](#6-pricing--metering)
7. [API gateway (`codeintel-api`)](#7-api-gateway-codeintel-api)
8. [Engine (`codeintel-engine`)](#8-engine-codeintel-engine)
9. [VS Code / Cursor extension](#9-vs-code--cursor-extension)
10. [Legacy prototypes](#10-legacy-prototypes)
11. [Development, testing & CI](#11-development-testing--ci)
12. [Source index](#12-source-index)

---

## 1. Project overview

**CodeIntel** is an AI-assisted test-generation platform that lives in your repo. It scans code, generates **pytest** and **Jest** suites, runs them in a **sandboxed** environment, and can open **PRs** with passing tests.

### Surfaces (one engine, three clients)

| Surface | Role |
|--------|------|
| **GitHub App** | Auto-opens PRs with tests for changed functions. |
| **VS Code / Cursor extension** | Right-click a function → generated tests. |
| **SaaS dashboard** | Coverage trends, run history, billing, teams. |

### Product pillars

- **Sandboxed validation** — Generated tests run in ephemeral containers: `--network=none`, read-only mount, CPU/memory caps.
- **Self-healing** — Sandbox failures feed back into the model (bounded retries).
- **BYO-LLM** — Groq default path; optional OpenAI / Anthropic / AWS Bedrock for customer-controlled inference.
- **Polyglot** — Python + TypeScript/JavaScript via adapters (more languages planned).
- **Mutation & flaky awareness** — Optional mutation testing; flaky-test guards before merge (see root README).

### High-level system diagram

```mermaid
flowchart LR
    subgraph clients [Client Surfaces]
        IDE[VS Code / Cursor]
        GHApp[GitHub App]
        Dash[Next.js Dashboard]
    end
    subgraph api [API Layer]
        FastAPI[FastAPI Gateway]
        Auth[Clerk JWT]
        Stripe[Stripe Metered Billing]
    end
    subgraph engine [CodeIntel Engine]
        Orch[Orchestrator]
        Prof[Multi-Lang Profiler]
        Gen[Generators]
        Sandbox["Docker Sandbox"]
        Providers["Groq / OpenAI / Anthropic / Bedrock"]
    end
    subgraph data [Data + Infra]
        PG[(Postgres)]
        Redis[(Redis)]
        S3[(S3 artifacts)]
    end
    IDE -->|JWT| FastAPI
    GHApp -->|HMAC| FastAPI
    Dash -->|JWT| FastAPI
    FastAPI --> Auth
    FastAPI --> Stripe
    FastAPI -->|enqueue| Redis
    Redis --> Orch
    Orch --> Prof
    Orch --> Gen
    Gen --> Providers
    Orch --> Sandbox
    Orch --> PG
    Orch --> S3
```

### Quickstart (from root README)

**One-line demo (mock provider, offline):**

```bash
uv sync --all-packages
uv run python -m codeintel_engine.cli scan --repo packages/engine/legacy/sample_repo --coverage
uv run python -m codeintel_engine.cli run  --repo packages/engine/legacy/sample_repo --function divide_numbers --provider mock
```

**Full stack (local):**

```bash
cp .env.example .env
uv sync --all-packages
pnpm install
uv run uvicorn codeintel_api.main:app --reload    # http://localhost:8000
pnpm --filter @codeintel/dashboard dev            # http://localhost:3000
```

Or: `docker compose -f infra/docker-compose.yml up --build`.

### Proposed commercial tiers (summary)

| Tier | Price | Limits |
|------|--------|--------|
| Free | $0 | 100 runs/mo, mock provider |
| Team | $29/seat/mo + usage | Unlimited runs, multiple providers, GitHub App, IDE, dashboard |
| Enterprise | Contact | Self-hosted Helm, BYO-LLM, SSO, SOC 2, audit export |

### License

**Apache-2.0** — see repository `LICENSE`.

---

## 2. Repository layout

```
apps/
  api/              FastAPI gateway, GitHub + Stripe webhooks
  dashboard/        Next.js 14 (App Router) + Tailwind + Clerk + Stripe
  vscode-extension/ VS Code / Cursor extension (TypeScript)
packages/
  engine/           Python engine (profilers, generators, sandbox, orchestrator)
    legacy/         Original revision_*.py prototypes (reference only)
  sdk-ts/           Typed TS SDK (dashboard + extension)
  ui/               Shared React primitives
infra/
  docker/           Sandbox images (codeintel-py, codeintel-node)
  helm/             Helm chart (enterprise self-host)
  terraform/        AWS reference (VPC, ECS, RDS, ElastiCache)
  docker-compose.yml  Local dev stack
docs/
  architecture.md   System design
  security.md       Threat model, SOC 2 mapping
  self-hosting.md   Enterprise install
  pricing.md        Plans + metering
  DOCUMENTATION_REPORT.md  This merged report
```

**Package manager (Node):** root `package.json` declares `"packageManager": "pnpm@9.10.0"`; CI uses `pnpm/action-setup@v4` without a conflicting `version` pin so setup reads this field.

---

## 3. Architecture

CodeIntel is a **monorepo** with one **engine** and **three client surfaces**. Boundaries, data flow, and trade-offs are documented below.

### 3.1 Components

| Layer | Tech | Location |
|-------|------|----------|
| Engine | Python 3.12, Pydantic v2, asyncio | `packages/engine` |
| API gateway | FastAPI, SQLAlchemy 2, Alembic | `apps/api` |
| Dashboard | Next.js 14 (App Router), Tailwind, Clerk, Stripe | `apps/dashboard` |
| IDE extension | TypeScript, vscode-api | `apps/vscode-extension` |
| Sandbox | Docker (prod) or local subprocess (dev) | `infra/docker` |
| Self-hosted | Helm chart | `infra/helm` |

### 3.2 End-to-end flow (GitHub App, PR time)

```mermaid
sequenceDiagram
  autonumber
  participant GH as GitHub
  participant API as FastAPI
  participant Q as Redis queue
  participant W as Worker
  participant SB as Sandbox (Docker)
  participant DB as Postgres
  GH->>API: POST /webhooks/github (HMAC)
  API->>API: verify_webhook_signature
  API->>Q: enqueue(pr_event)
  API-->>GH: 202 Accepted
  Q->>W: dequeue
  W->>W: clone head SHA into tmpfs
  W->>W: profile diff -> FunctionTarget[]
  loop per function
    W->>W: generator.initial_prompt
    W->>W: provider.generate
    W->>SB: docker run codeintel-py
    SB-->>W: Verdict (passed/failed, junit)
    alt failed and retries left
      W->>W: generator.heal_prompt
    end
  end
  W->>DB: persist TestRun
  W->>GH: open PR with passing tests
```

### 3.3 Engine decomposition

```mermaid
classDiagram
  class Orchestrator {
    +run(target) TestRun
    +stream(target) AsyncIterator
  }
  class Provider { <<protocol>> }
  class Sandbox { <<protocol>> }
  class Generator { <<protocol>> }
  class LanguageAdapter { <<protocol>> }
  class Profiler { <<protocol>> }
  Orchestrator --> Provider
  Orchestrator --> Sandbox
  Orchestrator --> Generator
  Orchestrator --> LanguageAdapter
  LanguageAdapter --> Profiler
  Provider <|.. GroqProvider
  Provider <|.. OpenAIProvider
  Provider <|.. AnthropicProvider
  Provider <|.. BedrockProvider
  Provider <|.. MockProvider
  Sandbox <|.. DockerSandbox
  Sandbox <|.. LocalSandbox
  Generator <|.. PytestGenerator
  Generator <|.. JestGenerator
  Profiler <|.. PythonAstProfiler
  Profiler <|.. TypeScriptProfiler
```

Dependencies target **protocols**, not concrete classes — the extension point for custom LLM, sandbox, or profiler implementations.

### 3.4 State machine

`TestRun.state` moves only forward; transitions are persisted for restart safety.

```mermaid
stateDiagram-v2
  [*] --> pending
  pending --> generating
  generating --> validating
  validating --> passed
  validating --> healing
  healing --> generating
  generating --> failed
  validating --> failed
  passed --> [*]
  failed --> [*]
  pending --> cancelled
  generating --> cancelled
  validating --> cancelled
  healing --> cancelled
```

### 3.5 Design rationale (summary)

| Choice | Reason |
|--------|--------|
| FastAPI over Django | Async-first, smaller surface, OpenAPI |
| Pydantic v2 | Strict API models; shared with engine |
| Docker sandbox | Untrusted generated code isolated from API process |
| uv + pnpm workspaces | Fast resolution; clear SSOT per language |
| Clerk + Stripe | Multi-tenant auth + metered billing |
| Tree-sitter (TS/JS), `ast` (Python) | Full AST in production paths |

---

## 4. Security & SOC 2 readiness

CodeIntel processes **customer source code**. This section supports procurement, reviewers, and audit.

### 4.1 Threat model

| Risk | Mitigation |
|------|------------|
| Untrusted code escapes sandbox | Docker `--network=none --read-only --pids-limit --memory --cpus --security-opt=no-new-privileges`; read-only repo mount; optional gVisor (future). |
| Source persists in vendor cloud | Source in sandbox tmpfs for run duration only; persist hashes, tests, verdicts — not full source (per product policy). |
| Generated test exfiltrates secrets | No network in sandbox; API scrubs env of secrets at edge. |
| LLM sees source | BYO-LLM (Bedrock/Azure) in self-hosted mode. |
| Webhook spoofing | HMAC-SHA256 (GitHub); Stripe signature verification. |
| IDE token theft | VS Code `SecretStorage` (OS-backed); never logged or in URLs. |
| Replay / idempotency | Stripe idempotency keys; GitHub dedupe via `X-GitHub-Delivery`. |
| Cross-org escalation | Routes scoped by `Principal.org_id` from JWT (see API tests). |
| Rate-limit abuse | Per-org limiter (Redis prod, in-memory dev). |

### 4.2 Identity & access

- **End users:** Clerk JWT (RS256 / JWKS). Dev tokens (`dev-<org>`) only when `environment=dev`.
- **GitHub App:** Installation tokens from private key in secret store (not on disk).
- **Internal services:** Short-lived IAM (Terraform in AWS reference).

### 4.3 Data classification & retention

| Datum | Retention | Class |
|-------|-----------|--------|
| Generated test code | Indefinite (deletable via API) | Customer-confidential |
| Source code | Per-run only (tmpfs, time-bounded) | Customer-confidential |
| Function hashes | 90 days | Internal |
| LLM token usage | 24 months (billing) | Internal |
| Webhook deliveries | 30 days | Internal |
| Audit log | 12 months | Internal |

### 4.4 SOC 2 controls map (excerpt)

| Trust criteria | Control | Evidence location |
|----------------|---------|-------------------|
| CC6.1 Logical access | Clerk SSO + per-org JWT | `apps/api/codeintel_api/auth.py` |
| CC6.6 Encryption in transit | TLS / ingress | `infra/helm/templates/ingress.yaml` |
| CC6.7 Encryption at rest | RDS / S3 / Redis | `infra/terraform/main.tf` |
| CC7.2 Monitoring | Sentry + OTel | `apps/api/codeintel_api/main.py` |
| CC8.1 Change management | PR + CI | `.github/workflows/ci.yml` |

Audit export sinks configured via Helm `values.yaml` (`audit.sink`).

### 4.5 Responsible disclosure

Report to `security@codeintel.dev` (PGP on website). Triage within 1 business day; critical remediation target within 30 days.

---

## 5. Self-hosting

Enterprises run the stack **inside their VPC**; LLM traffic can stay on **Bedrock** or **Azure OpenAI**.

### 5.1 Prerequisites

- Kubernetes **1.27+**
- **Postgres 15+** (Aurora suggested for HA)
- **Redis 7+**
- **Clerk** or SAML 2.0 IdP (enterprise SSO)
- LLM: **AWS Bedrock** or **Azure OpenAI**

### 5.2 Helm install (example)

```bash
helm repo add codeintel https://charts.codeintel.dev
helm install codeintel codeintel/codeintel \
  --namespace codeintel --create-namespace \
  --values my-values.yaml
```

**Minimal `my-values.yaml`:**

```yaml
image:
  tag: "0.1.0"
ingress:
  host: codeintel.acme.internal
provider:
  default: bedrock
  bedrock:
    region: us-east-1
auth:
  provider: sso-saml
  sso:
    metadataUrl: https://idp.acme.internal/metadata
postgres:
  url: postgresql+psycopg://codeintel:****@rds.acme.internal:5432/codeintel
redis:
  url: redis://redis.acme.internal:6379/0
audit:
  enabled: true
  sink: s3
  s3:
    bucket: acme-codeintel-audit
    region: us-east-1
```

### 5.3 Air-gapped install

1. Mirror images (`api`, `dashboard`, `sandbox-py`, `sandbox-node`) to private registry.
2. Override `image.*` in `values.yaml`.
3. Set `provider.default` to in-VPC endpoint (`bedrock` or `azure`).

### 5.4 Upgrades & operations

- **Semver**; minors via `helm upgrade …`; majors ship `MIGRATING.md`.
- **Backups:** RDS snapshots (e.g. 14-day retention in Terraform reference).
- **DR:** Cross-region Postgres replica; RTO target in runbook.
- **Observability:** `/metrics` scrape; Grafana dashboards (see Helm `dashboards/` roadmap).
- **Audit:** S3 object lock for tamper evidence.

---

## 6. Pricing & metering

### 6.1 Plans

| Plan | Price | Best for |
|------|-------|----------|
| **Free** | $0 | Solo / OSS |
| **Team** | $29/seat/mo + usage | 5–500 dev orgs |
| **Enterprise** | Contact sales | Regulated / self-hosted |

### 6.2 Free tier

- 100 generation runs / org / month
- `mock` provider only
- 1 GitHub repo
- Community support

### 6.3 Team tier

- $29 / seat / month (active devs who ran a test in last 30 days)
- Metered: e.g. `generation_runs` (tiered by provider), `sandbox_seconds`
- All SaaS providers (Groq, OpenAI, Anthropic); unlimited repos; GitHub App + IDE + dashboard

### 6.4 Enterprise tier

- Self-hosted Helm; BYO-LLM; SAML/SCIM; audit export; SOC 2 Type II; SLA options; annual contracts

### 6.5 Metered events (Stripe)

Implementation: `apps/api/codeintel_api/billing.py`.

| Meter | Unit | When |
|-------|------|------|
| `runs` | 1 per terminal `TestRun` | Run completion |
| `sandbox_seconds` | Wall seconds | Run completion |
| `seats` | Active devs / month | Daily roll-up |

Idempotency on `(org_id, meter, run_id)` for safe retries.

---

## 7. API gateway (`codeintel-api`)

FastAPI service for dashboard, IDE, and GitHub App. See `apps/api` and `docs/architecture.md`.

### 7.1 Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/healthz` | none | Liveness |
| GET | `/readyz` | none | Readiness (DB + Redis) |
| POST | `/v1/scans` | JWT | Scan repo; uncovered functions |
| POST | `/v1/runs` | JWT | Start test-generation run |
| GET | `/v1/runs/{id}` | JWT | Run status |
| GET | `/v1/runs/{id}/stream` | JWT | SSE `EngineEvent` stream |
| POST | `/webhooks/github` | HMAC | GitHub App |
| POST | `/webhooks/stripe` | Stripe sig | Billing webhooks |

### 7.2 Local run

```bash
uv run uvicorn codeintel_api.main:app --reload
# curl http://localhost:8000/healthz -> {"status":"ok"}
```

---

## 8. Engine (`codeintel-engine`)

Pure Python; shared by API, GitHub worker, and tooling.

### 8.1 Subpackages

| Module | Responsibility |
|--------|----------------|
| `models` | Pydantic schemas (`FunctionTarget`, `TestRun`, `Verdict`, `RunState`, …) |
| `adapters` | Per-language: discovery, import hints, test paths |
| `profilers` | AST extraction (Python + TS/JS) |
| `generators` | pytest / Jest prompt + output handling |
| `providers` | Groq, OpenAI, Anthropic, Bedrock, mock |
| `sandbox` | Docker (prod) / local subprocess (dev) |
| `orchestrator` | Generate → validate → heal loop |
| `coverage` | Diff vs existing suite |
| `github` | PR helpers, webhook HMAC |
| `cache` | Redis cache for `(function_hash, model)` → result |

### 8.2 Commands

```bash
cd packages/engine   # or from root with workspace
uv sync
uv run pytest
```

**Mock smoke test:**

```bash
uv run python -m codeintel_engine.cli scan \
  --repo packages/engine/legacy/sample_repo \
  --provider mock
```

---

## 9. VS Code / Cursor extension

**Command:** *CodeIntel: Generate Tests for Function* — calls API, streams generation, validates in sandbox, shows diff; optional PR flow.

### 9.1 Install

- VS Code Marketplace / Open VSX: search “CodeIntel”
- From source: `pnpm install && pnpm package` → install `.vsix`

### 9.2 Sign-in

1. `CodeIntel: Sign In`
2. Browser **device OAuth** (no manual token paste)
3. Tokens in **SecretStorage** (Keychain / DPAPI / libsecret)

### 9.3 Settings

| Setting | Default | Notes |
|---------|---------|--------|
| `codeintel.apiUrl` | `https://api.codeintel.dev` | Self-hosted URL if needed |
| `codeintel.provider` | `groq` | `mock` / `groq` / `openai` / `anthropic` / `bedrock` |
| `codeintel.maxRetries` | `3` | Self-heal attempts |
| `codeintel.openDiffOnSuccess` | `true` | Open diff on success |

---

## 10. Legacy prototypes

Under `packages/engine/legacy`: original `revision_*` scripts — **reference only**, **not** production.

| File | Maps to (conceptually) |
|------|-------------------------|
| `revision_1_agent.py` | Early orchestrator retry loop |
| `revision_2_agent.py` | History-aware retry |
| `revision_3_profiler.py` | `profilers/python_ast.py` |
| `revision_3_pipeline.py` | Multi-target orchestration |
| `revision_4_pr_engine.py` | `github/pr_engine.py` |
| `target_code.py`, `sample_repo/` | Fixtures / samples |
| `test_github.py` | Superseded by `github/client.py` |

Run legacy demo (needs `GROQ_API_KEY`):

```bash
cd packages/engine/legacy
uv run python revision_4_pr_engine.py
```

Planned removal in a future major release.

---

## 11. Development, testing & CI

### 11.1 Python tooling (root `pyproject.toml`)

- **Workspace:** `packages/engine`, `apps/api`
- **Dev dependency group:** `ruff`, `mypy`, `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`
- **Ruff:** line length 100, Python 3.12; excludes `packages/engine/legacy`
- **Mypy:** strict, Python 3.12; excludes `packages/engine/legacy`
- **Pytest:** `packages/engine/tests`, `apps/api/tests`; `asyncio_mode = auto`
- **Coverage:** CI enforces **≥80%** on `codeintel_engine` + `codeintel_api` with `[tool.coverage.run] omit` excluding integration-only modules (CLI, cache, DB layer, cloud provider SDK paths, Docker runner, GitHub API client/PR engine). Treat omissions as “not in this unit gate — cover in integration/E2E tests.”

### 11.2 GitHub Actions (`.github/workflows/ci.yml`)

| Job | What runs |
|-----|-----------|
| **Python (engine + api)** | `uv sync --all-packages --group dev` → `ruff check .` → `mypy packages/engine/codeintel_engine` → `pytest` with coverage fail-under 80% |
| **Node (dashboard + extension)** | `pnpm/action-setup@v4` (reads `packageManager`) → Node 20 + pnpm cache → `pnpm install --frozen-lockfile` → `pnpm -r --if-present lint|build|test` |
| **Sandbox images** | `docker build` for `codeintel-py.Dockerfile` and `codeintel-node.Dockerfile` under `infra/docker` |

Triggers: `push` to `main`/`master`, all `pull_request`s.

### 11.3 Local checks (quick reference)

```bash
uv sync --all-packages --group dev
uv run ruff check .
uv run mypy packages/engine/codeintel_engine
uv run pytest --cov=codeintel_engine --cov=codeintel_api --cov-fail-under=80

pnpm install --frozen-lockfile
pnpm -r --if-present lint
pnpm -r --if-present build
```

---

## 12. Source index

| Document | Path |
|----------|------|
| Main README | `README.md` |
| Architecture | `docs/architecture.md` |
| Security | `docs/security.md` |
| Self-hosting | `docs/self-hosting.md` |
| Pricing | `docs/pricing.md` |
| API README | `apps/api/README.md` |
| Engine README | `packages/engine/README.md` |
| Extension README | `apps/vscode-extension/README.md` |
| Legacy README | `packages/engine/legacy/README.md` |
| CI workflow | `.github/workflows/ci.yml` |
| Python workspace & tooling | `pyproject.toml` |
| **This report** | `docs/DOCUMENTATION_REPORT.md` |

---

*End of consolidated report.*
