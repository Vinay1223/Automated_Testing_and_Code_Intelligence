"""GitHub App webhook receiver.

Verifies the HMAC, parses the PR payload, and enqueues an orchestrator
run for every changed function. The actual queue is abstracted as
`request.app.state.runs` plus a background task; in production this is
Celery or RQ on top of Redis.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from codeintel_engine.github.signature import verify_webhook_signature
from codeintel_engine.github.webhooks import parse_pr_event
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from codeintel_api.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    body = await request.body()

    if settings.github_webhook_secret:
        if not verify_webhook_signature(body, x_hub_signature_256, settings.github_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        logger.warning("GITHUB_WEBHOOK_SECRET not set; accepting %s unsigned (dev only)", x_github_delivery)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Bad JSON") from e

    if x_github_event != "pull_request":
        return {"ignored": True, "event": x_github_event, "delivery": x_github_delivery}

    event = parse_pr_event(payload)
    if event is None or event.skip:
        return {"ignored": True, "reason": "skip-marker or non-pr"}

    background.add_task(_enqueue_pr_run, event=event)
    return {
        "accepted": True,
        "delivery": x_github_delivery,
        "repo": event.repo_full_name,
        "pr": event.number,
    }


async def _enqueue_pr_run(*, event) -> None:  # type: ignore[no-untyped-def]
    """Placeholder for the real Celery / RQ enqueue.

    In production this resolves an installation token, clones the head SHA
    into a tmpfs, runs the diff-aware profiler, and creates one run per
    changed function. Kept as a no-op here so the webhook is exercised
    end-to-end in tests without depending on Redis.
    """
    logger.info(
        "Would enqueue PR run repo=%s pr=%s head=%s",
        event.repo_full_name,
        event.number,
        event.head_sha,
    )
