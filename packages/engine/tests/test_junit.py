from codeintel_engine.sandbox.junit import parse_junit


def test_parse_junit_basic_stats():
    xml = (
        '<testsuites>'
        '<testsuite tests="5" failures="1" errors="0" skipped="1"></testsuite>'
        '</testsuites>'
    )
    assert parse_junit(xml) == (5, 3, 1)


def test_parse_junit_malformed_returns_zeros():
    assert parse_junit("<not xml") == (0, 0, 0)
