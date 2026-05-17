"""API test fixtures.

We use FastAPI's `TestClient` with a fresh app instance per test so the
in-memory `RunStore` doesn't leak between tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _dev_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINTEL_PROVIDER", "mock")
    monkeypatch.setenv("CODEINTEL_SANDBOX", "local")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./_test.db")
    monkeypatch.setenv("environment", "dev")


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Re-import so settings cache is fresh.
    from codeintel_api.main import create_app
    from codeintel_api.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer dev-acme"}


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "math_utils.py").write_text(
        "def add_numbers(a, b):\n    return a + b\n\n"
        "def divide_numbers(a, b):\n"
        "    if b == 0:\n        raise ValueError('Cannot divide by zero')\n"
        "    return a / b\n",
        encoding="utf-8",
    )
    return tmp_path
