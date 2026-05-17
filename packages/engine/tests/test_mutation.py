from codeintel_engine.mutation import parse_mutmut_json, parse_stryker_json


def test_parse_mutmut_basic():
    r = parse_mutmut_json('{"killed": 8, "survived": 2, "timeout": 0}')
    assert r.total == 10
    assert r.killed == 8
    assert r.score == 80.0
    assert r.grade == "B"


def test_parse_mutmut_handles_garbage():
    r = parse_mutmut_json("not json")
    assert r.total == 0
    assert r.grade == "F"


def test_parse_stryker_basic():
    r = parse_stryker_json(
        '{"files": {"a.ts": {"mutants": ['
        '{"status": "Killed"}, {"status": "Killed"}, {"status": "Survived"}'
        ']}}}'
    )
    assert r.killed == 2
    assert r.survived == 1
    assert r.total == 3
