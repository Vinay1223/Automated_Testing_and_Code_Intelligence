"""Stripe metered-billing webhook receiver.

We listen for `invoice.created`, `customer.subscription.updated`, and
`checkout.session.completed`. Verification uses Stripe's signing secret.
The receiver is idempotent — Stripe retries deliveries up to 3 days.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from codeintel_api.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=status.HTTP_202_ACCEPTED)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
) -> dict[str, str]:
    settings = get_settings()
    body = await request.body()
    if not settings.stripe_webhook_secret or not settings.stripe_secret_key:
        logger.warning("Stripe not configured; accepting webhook in dev")
        return {"accepted": "dev"}

    try:
        import stripe  # type: ignore[import-not-found]
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail="stripe SDK missing") from e

    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(  # type: ignore[attr-defined]
            payload=body,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except Exception as e:
        logger.warning("Stripe signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    handler = _HANDLERS.get(event["type"], _ignored)
    await handler(event)
    return {"accepted": "ok"}


async def _ignored(event) -> None:  # type: ignore[no-untyped-def]
    logger.info("Ignored stripe event type=%s", event.get("type"))


async def _on_subscription_updated(event) -> None:  # type: ignore[no-untyped-def]
    logger.info("subscription updated: %s", event["data"]["object"]["id"])


async def _on_invoice_created(event) -> None:  # type: ignore[no-untyped-def]
    logger.info("invoice created: %s", event["data"]["object"]["id"])


async def _on_checkout_completed(event) -> None:  # type: ignore[no-untyped-def]
    logger.info("checkout completed: %s", event["data"]["object"]["id"])


_HANDLERS = {
    "customer.subscription.updated": _on_subscription_updated,
    "invoice.created": _on_invoice_created,
    "checkout.session.completed": _on_checkout_completed,
}
