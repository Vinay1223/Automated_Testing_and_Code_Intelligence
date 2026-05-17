import pytest
from codeintel_engine.flaky import detect_flake
from codeintel_engine.models import Verdict


@pytest.mark.asyncio
async def test_detect_flake_flags_inconsistent_results():
    sequence = [True, False, True, True, False]

    async def runner():
        passed = sequence.pop(0)
        return Verdict(
            passed=passed,
            log="ok" if passed else "boom 1.23s",
            exit_code=0 if passed else 1,
            duration_ms=10,
        )

    report = await detect_flake(runner, runs=5)
    assert report.is_flaky is True
    assert report.passes == 3
    assert report.failures == 2


@pytest.mark.asyncio
async def test_detect_flake_no_false_positive_when_all_pass():
    async def runner():
        return Verdict(passed=True, log="", exit_code=0, duration_ms=1)

    report = await detect_flake(runner, runs=3)
    assert report.is_flaky is False
