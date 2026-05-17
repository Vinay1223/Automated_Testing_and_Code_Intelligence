"""API configuration loaded from environment + .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "dev"
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+psycopg://codeintel:codeintel@localhost:5432/codeintel",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    provider: str = Field(default="mock", validation_alias="CODEINTEL_PROVIDER")
    model: str | None = Field(default=None, validation_alias="CODEINTEL_MODEL")
    sandbox: str = Field(default="local", validation_alias="CODEINTEL_SANDBOX")

    github_webhook_secret: str | None = Field(default=None, validation_alias="GITHUB_WEBHOOK_SECRET")
    github_app_id: str | None = Field(default=None, validation_alias="GITHUB_APP_ID")
    github_app_private_key_path: str | None = Field(
        default=None, validation_alias="GITHUB_APP_PRIVATE_KEY_PATH"
    )

    clerk_jwks_url: str | None = Field(default=None, validation_alias="CLERK_JWKS_URL")
    clerk_audience: str | None = Field(default=None, validation_alias="CLERK_AUDIENCE")

    stripe_secret_key: str | None = Field(default=None, validation_alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(default=None, validation_alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_runs: str | None = Field(default=None, validation_alias="STRIPE_PRICE_RUNS")
    stripe_price_sandbox_seconds: str | None = Field(
        default=None, validation_alias="STRIPE_PRICE_SANDBOX_SECONDS"
    )

    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")

    free_runs_per_month: int = 100
    rate_limit_per_min_per_org: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
