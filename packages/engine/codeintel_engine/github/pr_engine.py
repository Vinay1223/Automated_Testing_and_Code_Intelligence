"""Pull-request engine.

Takes one or more passing `TestRun`s and proposes a single PR with all of
their generated test files. Replaces the imperative `revision_4_pr_engine`
flow with a class that's easy to mock in tests.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from codeintel_engine.github.client import CommitFile, GitHubClient
from codeintel_engine.models import TestRun

logger = logging.getLogger(__name__)


@dataclass
class PRProposal:
    branch_name: str
    title: str
    body: str
    files: list[CommitFile]


class PullRequestEngine:
    def __init__(self, client: GitHubClient, *, tests_dir: str = "tests") -> None:
        self._client = client
        self._tests_dir = tests_dir.rstrip("/")

    def propose(self, runs: list[TestRun], *, repo_full_name: str) -> PRProposal:
        passing = [r for r in runs if r.state.value == "passed" and r.final_test_code]
        if not passing:
            raise ValueError("No passing runs to propose")

        suffix = passing[0].target.name if len(passing) == 1 else f"{len(passing)}-functions"
        branch_name = f"codeintel/add-tests-{suffix}-{int(time.time())}"
        files = [
            CommitFile(
                path=f"{self._tests_dir}/test_{run.target.name}.py"
                if run.framework.value == "pytest"
                else f"{self._tests_dir}/{run.target.name}.test.ts",
                content=run.final_test_code or "",
                message=f"test: add automated suite for {run.target.qualified_name}",
            )
            for run in passing
        ]
        title = (
            f"Add automated tests for `{passing[0].target.name}`"
            if len(passing) == 1
            else f"Add automated tests for {len(passing)} functions"
        )
        body = _render_body(passing)
        return PRProposal(branch_name=branch_name, title=title, body=body, files=files)

    def submit(self, proposal: PRProposal, *, repo_full_name: str, base_branch: str | None = None) -> str:
        return self._client.open_pr(
            repo_full_name=repo_full_name,
            branch_name=proposal.branch_name,
            files=proposal.files,
            title=proposal.title,
            body=proposal.body,
            base_branch=base_branch,
        )


def _render_body(runs: list[TestRun]) -> str:
    lines = [
        "## Automated test contribution",
        "",
        "This PR was opened by **CodeIntel** after the generated tests passed",
        "the sandbox. Each function below has been validated end-to-end.",
        "",
        "| Function | Attempts | Tests | Provider |",
        "|----------|---------:|------:|----------|",
    ]
    for run in runs:
        last = run.attempts[-1] if run.attempts else None
        lines.append(
            f"| `{run.target.qualified_name}` | {len(run.attempts)} | "
            f"{(run.target.raises and len(run.target.raises) + 1) or 1}+ | "
            f"{last.provider if last else '?'}/{last.model if last else '?'} |"
        )
    lines.extend(
        [
            "",
            "<details><summary>Why CodeIntel proposed these</summary>",
            "",
            *(f"- **{r.target.qualified_name}** — {r.final_explanation or ''}" for r in runs),
            "",
            "</details>",
            "",
            "_Generated and validated autonomously. Reply with `[skip codeintel]` "
            "in any future commit to opt out of this repo._",
        ]
    )
    return "\n".join(lines)
