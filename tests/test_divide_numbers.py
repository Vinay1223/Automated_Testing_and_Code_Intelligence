from sample_repo.math_utils import divide_numbers
import pytest

def test_divide_by_non_zero():
    assert divide_numbers(10, 2) == 5

def test_divide_by_zero():
    with pytest.raises(ValueError) as exc_info:
        divide_numbers(10, 0)
    assert str(exc_info.value) == 'Cannot divide by zero'

def test_divide_by_negative():
    assert divide_numbers(10, -2) == -5
    assert divide_numbers(-10, 2) == -5
    assert divide_numbers(-10, -2) == 5