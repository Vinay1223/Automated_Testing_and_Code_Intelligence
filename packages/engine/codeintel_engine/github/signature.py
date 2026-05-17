"""GitHub webhook HMAC signature verification.

GitHub signs every webhook with HMAC-SHA256 using the secret you configured
on the GitHub App. This module is a pure function — it does not log the
payload (sensitive) and runs in constant time to defeat timing attacks.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_webhook_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    """Return True iff `signature_header` is a valid GitHub HMAC for `payload`.

    `signature_header` is the value of `X-Hub-Signature-256` (e.g.
    `sha256=abc123...`). Missing or malformed headers return False.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    sent = signature_header.split("=", 1)[1].strip()
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sent, digest)
