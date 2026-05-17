# Security & SOC 2 readiness

CodeIntel processes customer source code. This document is what we hand
to procurement, security reviewers, and the SOC 2 auditor.

## Threat model

| Risk | Mitigation |
|---|---|
| Untrusted code escapes the sandbox | Docker `--network=none --read-only --pids-limit --memory --cpus --security-opt=no-new-privileges`, repo mounted read-only. Optional gVisor in Phase 5+. |
| Source code persists in our cloud | Source lives in the sandbox tmpfs for the duration of the run only. We persist function hashes + generated tests + verdicts, never the source. |
| Generated test exfiltrates secrets | `--network=none` on the sandbox; envvars passed in are scrubbed of secrets at the API edge. |
| LLM provider sees source | BYO-LLM via Bedrock or Azure OpenAI keeps generation inside the customer's cloud (`docs/self-hosting.md`). |
| Webhook spoofing | HMAC-SHA256 on every GitHub webhook (`codeintel_engine/github/signature.py`); Stripe signature verification on every billing event. |
| Auth token theft (IDE) | Tokens stored in VS Code SecretStorage (Keychain / DPAPI / libsecret). Never logged, never sent in URLs. |
| Replay / idempotency | Stripe deliveries use Stripe's idempotency keys; GitHub deliveries deduped by `X-GitHub-Delivery`. |
| Privilege escalation across orgs | Every API route filters by `Principal.org_id` from the JWT. Tests in [`apps/api/tests/test_auth.py`](../apps/api/tests/test_auth.py). |
| Rate-limit abuse | Per-org sliding-window limiter (Redis in prod, in-memory in dev). |

## Identity & access

- **End users**: Clerk JWTs (RS256, verified against JWKS). Dev tokens
  (`dev-<org>`) are accepted **only** when `environment=dev`.
- **GitHub App**: per-installation tokens minted from a private key
  loaded from a secret store. Never on disk.
- **Internal services**: short-lived IAM roles (Terraform-managed) in
  production AWS.

## Data classification & retention

| Datum | Retention | Class |
|---|---|---|
| Generated test code | Indefinite (you can `DELETE /v1/runs/{id}`) | Customer-confidential |
| Source code | Per-run only (tmpfs, max 60s) | Customer-confidential |
| Function hashes | 90 days | Internal |
| LLM token usage | 24 months (billing) | Internal |
| Webhook deliveries | 30 days | Internal |
| Audit log | 12 months | Internal |

## SOC 2 controls map

| Trust criteria | Control | Evidence |
|---|---|---|
| CC6.1 Logical access | Clerk SSO + per-org JWT | `apps/api/codeintel_api/auth.py` |
| CC6.6 Encryption in transit | TLS via ingress; CA-signed certs | `infra/helm/templates/ingress.yaml` |
| CC6.7 Encryption at rest | RDS / S3 / Redis at-rest encryption | `infra/terraform/main.tf` |
| CC7.2 System monitoring | Sentry + OTel pipeline | `apps/api/codeintel_api/main.py` |
| CC8.1 Change management | All changes via PR + required reviewers + green CI | `.github/workflows/ci.yml` |

Audit log export sinks (S3 / Splunk / Datadog) are configured via
`infra/helm/values.yaml` (`audit.sink`).

## Responsible disclosure

Report vulnerabilities to `security@codeintel.dev` (PGP key on the
website). We commit to triage within 1 business day and a fix or
mitigation within 30 days for critical issues.
