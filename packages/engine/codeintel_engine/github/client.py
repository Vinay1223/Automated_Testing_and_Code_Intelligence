"""Thin wrapper around PyGithub used by the PR engine.

The class is intentionally minimal — we only expose what the orchestrator
needs. Authentication is handled by the caller (Personal Access Token for
the CLI, GitHub App installation token for the SaaS backend).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CommitFile:
    path: str
    content: str
    message: str


class GitHubClient:
    def __init__(self, token: str, *, default_repo: str | None = None) -> None:
        try:
            from github import Github  # type: ignore[import-not-found]
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("PyGithub is required for GitHubClient") from e
        self._gh = Github(token)
        self._default_repo = default_repo

    def repo(self, full_name: str | None = None) -> Any:
        target = full_name or self._default_repo
        if not target:
            raise ValueError("repo full name not provided and no default configured")
        return self._gh.get_repo(target)

    def open_pr(
        self,
        *,
        repo_full_name: str,
        branch_name: str,
        files: list[CommitFile],
        title: str,
        body: str,
        base_branch: str | None = None,
    ) -> str:
        repo = self.repo(repo_full_name)
        default_branch = base_branch or repo.default_branch
        source = repo.get_branch(default_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
        for f in files:
            repo.create_file(
                path=f.path, message=f.message, content=f.content, branch=branch_name
            )
        pr = repo.create_pull(title=title, body=body, head=branch_name, base=default_branch)
        logger.info("Opened PR %s", pr.html_url)
        return pr.html_url

    def post_review_comment(
        self, *, repo_full_name: str, pr_number: int, body: str
    ) -> None:
        repo = self.repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(body)
