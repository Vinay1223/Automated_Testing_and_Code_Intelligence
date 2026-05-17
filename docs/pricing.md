# Pricing & metering

## Plans

| Plan | Price | Best for |
|---|---|---|
| **Free** | $0 | Solo devs, open source |
| **Team** | $29 / seat / mo + usage | 5–500-dev orgs |
| **Enterprise** | Contact sales | Regulated industries, self-hosted |

## Free tier

- 100 generation runs per month per org.
- `mock` provider only.
- 1 GitHub repo.
- Community support.

## Team tier

- $29 / seat / month (active devs who triggered a run in the last 30 days).
- Plus metered usage:
  - `generation_runs`: $0.05 / run (Groq), $0.20 / run (OpenAI / Anthropic).
  - `sandbox_seconds`: $0.0002 / sec (Docker), free under 60s/run.
- All providers: Groq, OpenAI, Anthropic.
- Unlimited repos.
- GitHub App + IDE extension + SaaS dashboard.

## Enterprise tier

- Self-hosted Helm chart inside your VPC.
- BYO-LLM (Bedrock, Azure OpenAI, on-prem inference).
- SSO (SAML), SCIM, audit log export.
- SOC 2 Type II report.
- 99.9% SLA for managed SaaS, 24×5 support.
- Custom contract; annual.

## Metered events

Reported to Stripe via [`apps/api/codeintel_api/billing.py`](../apps/api/codeintel_api/billing.py):

| Meter | Unit | When |
|---|---|---|
| `runs` | 1 per terminal `TestRun` | On run completion |
| `sandbox_seconds` | wall-clock seconds | On run completion |
| `seats` | active devs / month | Daily aggregator |

All meters are idempotent on `(org_id, meter, run_id)` so retries are
safe.
