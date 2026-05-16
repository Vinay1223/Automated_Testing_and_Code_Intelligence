from sample_repo.math_utils import add_numbers
import pytest

def test_add_positive_numbers():
    assert add_numbers(5, 7) == 12

def test_add_negative_numbers():
    assert add_numbers(-5, -7) == -12

def test_add_mixed_numbers():
    assert add_numbers(-5, 7) == 2

def test_add_zero():
    assert add_numbers(0, 0) == 0

def test_add_non_integer_inputs():
    assert add_numbers(5.5, 7) == 12.5

def test_add_non_numeric_inputs():
    with pytest.raises(TypeError):
        add_numbers("five", 7)