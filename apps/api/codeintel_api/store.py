"""In-memory `TestRun` store.

This is the seam where the Postgres-backed repository plugs in. The API
imports `RunStore` and never sees the SQLAlchemy session, so swapping
backends is a one-line change in `main.py`.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from uuid import UUID

from codeintel_engine.models import TestRun


class RunStore:
    def __init__(self, max_history: int = 500) -> None:
        self._by_id: dict[UUID, TestRun] = {}
        self._history: deque[UUID] = deque(maxlen=max_history)

    def save(self, run: TestRun) -> None:
        if run.id not in self._by_id:
            self._history.append(run.id)
        self._by_id[run.id] = run

    def get(self, run_id: UUID) -> TestRun | None:
        return self._by_id.get(run_id)

    def list_recent(self, *, limit: int = 50, org_id: str | None = None) -> list[TestRun]:
        out: list[TestRun] = []
        for rid in reversed(self._history):
            run = self._by_id.get(rid)
            if run is None:
                continue
            if org_id is not None and run.org_id != org_id:
                continue
            out.append(run)
            if len(out) >= limit:
                break
        return out

    def all(self) -> Iterable[TestRun]:
        return self._by_id.values()
