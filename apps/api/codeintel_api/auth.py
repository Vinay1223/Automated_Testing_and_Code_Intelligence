"""JWT auth dependency.

In production we verify Clerk-signed JWTs via JWKS. For local dev and
tests we accept any `Authorization: Bearer dev-<org>` token and parse the
org id out of it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from codeintel_api.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Principal:
    user_id: str
    org_id: str
    is_dev: bool = False


async def require_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer")

    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()

    if settings.environment == "dev" and token.startswith("dev-"):
        return Principal(user_id="dev-user", org_id=token[len("dev-"):] or "dev", is_dev=True)

    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Auth not configured (set CLERK_JWKS_URL)",
        )

    try:
        import jwt  # type: ignore[import-not-found]
        from jwt import PyJWKClient  # type: ignore[import-not-found]
    except ImportError as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail="PyJWT not installed") from e

    try:
        client = PyJWKClient(settings.clerk_jwks_url)
        signing_key = client.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.clerk_audience,
            options={"verify_exp": True},
        )
    except Exception as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    org_id = claims.get("org_id") or claims.get("o", {}).get("id") or "default"
    user_id = claims.get("sub", "unknown")
    return Principal(user_id=user_id, org_id=org_id)
