"""Stripe metered billing helpers.

Three meters are reported:

* `runs` — every orchestrator run that reaches a terminal state.
* `sandbox_seconds` — wall-clock seconds inside the sandbox per run.
* `seats` — paid IDE seats (reported separately by the dashboard).

`record_usage` is idempotent — calling it twice with the same
`idempotency_key` is a no-op. Stripe's API natively de-duplicates on
this header.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from codeintel_api.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class UsageEvent:
    org_stripe_customer_id: str
    quantity: int
    meter: str  # "runs" | "sandbox_seconds" | "seats"
    idempotency_key: str


def record_usage(event: UsageEvent, settings: Settings) -> bool:
    """Report a metered usage event to Stripe.

    Returns True on success, False if Stripe is unconfigured (dev mode).
    Raises on network / 4xx errors so the caller can decide on retries.
    """
    if not settings.stripe_secret_key:
        logger.info(
            "stripe not configured; dropping meter=%s qty=%s",
            event.meter,
            event.quantity,
        )
        return False
    try:
        import stripe  # type: ignore[import-not-found]
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("stripe SDK missing") from e

    stripe.api_key = settings.stripe_secret_key
    price = _resolve_price(event.meter, settings)
    if price is None:
        logger.warning("No Stripe price configured for meter=%s", event.meter)
        return False

    stripe.SubscriptionItem.create_usage_record(  # type: ignore[attr-defined]
        price,
        quantity=event.quantity,
        action="increment",
        idempotency_key=event.idempotency_key,
    )
    return True


def _resolve_price(meter: str, settings: Settings) -> str | None:
    if meter == "runs":
        return settings.stripe_price_runs
    if meter == "sandbox_seconds":
        return settings.stripe_price_sandbox_seconds
    return None
