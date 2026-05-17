import hashlib
import hmac
import json


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "topsecret")
    from codeintel_api.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    body = json.dumps({"action": "opened", "pull_request": {}, "repository": {}}).encode()
    r = client.post(
        "/webhooks/github",
        data=body,
        headers={
            "X-Hub-Signature-256": _sign("wrong", body),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "deadbeef",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401


def test_webhook_accepts_valid_signed_payload(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "topsecret")
    from codeintel_api.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "title": "Feature",
            "body": "",
            "head": {"sha": "a", "ref": "feat"},
            "base": {"sha": "b", "ref": "main"},
        },
        "repository": {"full_name": "octo/repo"},
        "installation": {"id": 1},
    }
    body = json.dumps(payload).encode()
    r = client.post(
        "/webhooks/github",
        data=body,
        headers={
            "X-Hub-Signature-256": _sign("topsecret", body),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "abc",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 202


def test_webhook_skips_marker(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "topsecret")
    from codeintel_api.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "title": "[skip codeintel] wip",
            "body": "",
            "head": {"sha": "a"},
            "base": {"sha": "b"},
        },
        "repository": {"full_name": "octo/repo"},
    }
    body = json.dumps(payload).encode()
    r = client.post(
        "/webhooks/github",
        data=body,
        headers={
            "X-Hub-Signature-256": _sign("topsecret", body),
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "xyz",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 202
    assert r.json()["ignored"] is True
