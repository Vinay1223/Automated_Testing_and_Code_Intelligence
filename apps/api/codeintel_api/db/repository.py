"""SQLAlchemy-backed `TestRun` repository.

Swap this in for `codeintel_api.store.RunStore` to persist runs across
restarts. The signature is intentionally identical to the in-memory
store so the API code doesn't need to change.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from codeintel_engine.models import TestRun
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from codeintel_api.db.models import RunRow


class SqlRunStore:
    def __init__(self, sm: sessionmaker) -> None:
        self._sm = sm

    def save(self, run: TestRun) -> None:
        with self._sm() as session:
            row = session.get(RunRow, str(run.id))
            if row is None:
                row = RunRow(id=str(run.id))
                session.add(row)
            row.org_id = run.org_id
            row.repo = run.repo
            row.function_name = run.target.qualified_name
            row.framework = run.framework.value
            row.language = run.target.language.value
            row.state = run.state.value
            row.attempts = len(run.attempts)
            row.final_test_code = run.final_test_code
            row.final_explanation = run.final_explanation
            row.error = run.error
            row.payload = run.model_dump(mode="json")
            session.commit()

    def get(self, run_id: UUID) -> TestRun | None:
        with self._sm() as session:
            row = session.get(RunRow, str(run_id))
            if row is None:
                return None
            return TestRun.model_validate(row.payload)

    def list_recent(self, *, limit: int = 50, org_id: str | None = None) -> list[TestRun]:
        with self._sm() as session:
            stmt = select(RunRow).order_by(RunRow.updated_at.desc()).limit(limit)
            if org_id is not None:
                stmt = stmt.where(RunRow.org_id == org_id)
            rows = session.execute(stmt).scalars().all()
            return [TestRun.model_validate(r.payload) for r in rows]

    def all(self) -> Iterable[TestRun]:
        with self._sm() as session:
            for row in session.execute(select(RunRow)).scalars():
                yield TestRun.model_validate(row.payload)
