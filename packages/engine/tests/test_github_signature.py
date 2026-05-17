from __future__ import annotations

import hashlib
import hmac

from codeintel_engine.github.signature import verify_webhook_signature
from codeintel_engine.github.webhooks import parse_pr_event


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signature_accepts_valid_payload():
    secret, body = "topsecret", b'{"hello":"world"}'
    assert verify_webhook_signature(body, _sign(secret, body), secret) is True


def test_signature_rejects_invalid_payload():
    secret, body = "topsecret", b'{"hello":"world"}'
    assert verify_webhook_signature(body, _sign("wrong", body), secret) is False


def test_signature_rejects_missing_header():
    assert verify_webhook_signature(b"x", None, "s") is False
    assert verify_webhook_signature(b"x", "garbage", "s") is False


def test_parse_pr_event_extracts_basics():
    event = parse_pr_event(
        {
            "action": "opened",
            "pull_request": {
                "number": 7,
                "title": "Hello",
                "body": "",
                "head": {"sha": "abc", "ref": "feat/x"},
                "base": {"sha": "def", "ref": "main"},
            },
            "repository": {"full_name": "octo/repo"},
            "installation": {"id": 42},
        }
    )
    assert event is not None
    assert event.number == 7
    assert event.repo_full_name == "octo/repo"
    assert event.installation_id == 42
    assert event.skip is False


def test_parse_pr_event_honors_skip_marker():
    event = parse_pr_event(
        {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "[skip codeintel] WIP",
                "body": "",
                "head": {"sha": "a"},
                "base": {"sha": "b"},
            },
            "repository": {"full_name": "x/y"},
        }
    )
    assert event is not None and event.skip is True


def test_parse_pr_event_ignores_non_pr_payloads():
    assert parse_pr_event({"action": "push"}) is None
