"""Parse the small subset of GitHub webhook payloads we care about."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PullRequestEvent:
    action: str
    number: int
    repo_full_name: str
    head_sha: str
    base_sha: str
    base_branch: str
    head_branch: str
    installation_id: int | None
    skip: bool


def parse_pr_event(payload: dict[str, Any]) -> PullRequestEvent | None:
    """Return a normalized PR event, or None if this payload isn't one."""
    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        return None
    repo = payload.get("repository") or {}
    head = pr.get("head") or {}
    base = pr.get("base") or {}
    installation = payload.get("installation") or {}
    title = pr.get("title", "") or ""
    body = pr.get("body") or ""

    return PullRequestEvent(
        action=payload.get("action", ""),
        number=int(pr.get("number", 0)),
        repo_full_name=str(repo.get("full_name", "")),
        head_sha=str(head.get("sha", "")),
        base_sha=str(base.get("sha", "")),
        base_branch=str(base.get("ref", "")),
        head_branch=str(head.get("ref", "")),
        installation_id=installation.get("id"),
        skip="[skip codeintel]" in title.lower() or "[skip codeintel]" in body.lower(),
    )
