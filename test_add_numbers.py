from sample_repo.math_utils import add_numbers


def test_add_positive_numbers():
    assert add_numbers(5, 7) == 12


def test_add_negative_numbers():
    assert add_numbers(-5, -7) == -12


def test_add_mixed_numbers():
    assert add_numbers(-5, 7) == 2


def test_add_zero():
    assert add_numbers(0, 0) == 0


def test_add_one_positive_and_zero():
    assert add_numbers(5, 0) == 5


def test_add_one_negative_and_zero():
    assert add_numbers(-5, 0) == -5


def test_add_non_integer_input():
    try:
        add_numbers(5, '7')
        assert False, "Expected TypeError to be raised"
    except TypeError:
        pass