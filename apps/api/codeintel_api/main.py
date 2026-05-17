"""CodeIntel HTTP API entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codeintel_api.routes import health, runs, scans, webhooks_github, webhooks_stripe
from codeintel_api.settings import get_settings
from codeintel_api.store import RunStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting CodeIntel API in %s mode", settings.environment)
    app.state.settings = settings
    app.state.runs = RunStore()
    if settings.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)
        except Exception:
            logger.exception("Failed to init Sentry")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="CodeIntel API",
        version="0.1.0",
        description="AI test engineer for your repo.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(runs.router)
    app.include_router(scans.router)
    app.include_router(webhooks_github.router)
    app.include_router(webhooks_stripe.router)
    return app


app = create_app()
