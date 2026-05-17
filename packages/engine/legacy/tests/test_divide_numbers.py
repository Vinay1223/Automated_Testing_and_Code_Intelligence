import pytest

from sample_repo.math_utils import divide_numbers


def test_divide_by_non_zero():
    assert divide_numbers(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide_numbers(10, 0)


def test_divide_by_negative():
    assert divide_numbers(10, -2) == -5
    assert divide_numbers(-10, 2) == -5
    assert divide_numbers(-10, -2) == 5
