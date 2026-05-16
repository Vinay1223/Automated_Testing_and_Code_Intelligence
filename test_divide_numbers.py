from sample_repo.math_utils import divide_numbers
import pytest

def test_divide_numbers_success():
    assert divide_numbers(10.0, 2.0) == 5.0

def test_divide_numbers_by_zero():
    with pytest.raises(ValueError) as exc_info:
        divide_numbers(10.0, 0.0)
    assert str(exc_info.value) == 'Cannot divide by zero'