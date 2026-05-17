"""Shared fixtures for the engine test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SAMPLE_REPO = ENGINE_ROOT / "legacy" / "sample_repo"


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """A small repo with one Python module and one TS module, ready to scan."""
    py = tmp_path / "math_utils.py"
    py.write_text(
        '''
def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def _private_helper(x):
    return x
'''.lstrip(),
        encoding="utf-8",
    )
    ts = tmp_path / "string_utils.ts"
    ts.write_text(
        '''
export function capitalize(input: string): string {
  if (input.length === 0) {
    throw new Error("empty");
  }
  return input[0].toUpperCase() + input.slice(1);
}

export const shout = (s: string): string => s.toUpperCase();
'''.lstrip(),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def legacy_sample_repo() -> Path:
    return LEGACY_SAMPLE_REPO
