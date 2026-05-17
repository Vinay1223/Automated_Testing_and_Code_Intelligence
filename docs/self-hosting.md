# Self-hosting CodeIntel

Enterprise customers can run the entire stack inside their own VPC.
Nothing CodeIntel-owned needs to be reachable from the customer's
network — including the LLM calls when you point `provider.default` at
Bedrock or Azure OpenAI.

## Prerequisites

- Kubernetes 1.27+ cluster (EKS / GKE / AKS / OpenShift all tested).
- Postgres 15+ (RDS Aurora recommended for HA).
- Redis 7+ (ElastiCache or in-cluster).
- An identity provider supported by Clerk **or** any SAML 2.0 IdP for
  the Enterprise SSO add-on.
- An LLM endpoint: AWS Bedrock (`anthropic.claude-3-5-sonnet-*`) or
  Azure OpenAI (`gpt-4o-*`).

## Install

```bash
helm repo add codeintel https://charts.codeintel.dev
helm install codeintel codeintel/codeintel \
  --namespace codeintel --create-namespace \
  --values my-values.yaml
```

Minimal `my-values.yaml`:

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

## Air-gapped install

CodeIntel does not phone home. To install offline:

1. Mirror the three images (`ghcr.io/codeintel/api`, `…/dashboard`,
   `…/sandbox-py`, `…/sandbox-node`) into your private registry.
2. Override `image.api` / `image.dashboard` / `image.sandboxPy` /
   `image.sandboxNode` in your `values.yaml`.
3. Set `provider.default: bedrock` (or `azure`) and configure the
   endpoint inside your VPC.

## Upgrades

CodeIntel follows semver. Minor upgrades are automatic
(`helm upgrade codeintel codeintel/codeintel --version ^0.1.0`).
Major upgrades ship a `MIGRATING.md` with explicit steps.

## Operational runbook

- **Daily backups**: RDS snapshots, 14-day retention (set in
  `infra/terraform/main.tf`).
- **DR**: cross-region read replica for Postgres; restore time < 30 min.
- **Observability**: Prometheus scrape at `/metrics`; pre-built Grafana
  dashboards under `infra/helm/dashboards/` (Phase 5.1).
- **Audit log export**: S3 bucket with object-lock for tamper evidence.
