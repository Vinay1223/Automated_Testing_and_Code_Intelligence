import pytest
def calculate_percentage(part: float, total: float) -> float:
    if total == 0:
        raise ValueError("Total cannot be zero.")
    return round((part / total) * 100, 2)

def test_calculate_percentage_zero_total():
    with pytest.raises(ValueError):
        calculate_percentage(10, 0)

def test_calculate_percentage_zero_part():
    assert calculate_percentage(0, 100) == 0

def test_calculate_percentage_equal_part_total():
    assert calculate_percentage(10, 10) == 100.0

def test_calculate_percentage_part_larger_than_total():
    assert calculate_percentage(10, 5) == 200.0

def test_calculate_percentage_part_smaller_than_total():
    assert calculate_percentage(5, 10) == 50.0

def test_calculate_percentage_negative_part():
    assert calculate_percentage(-5, 10) == -50.0

def test_calculate_percentage_negative_total():
    with pytest.raises(ValueError):
        calculate_percentage(10, 0)
    assert calculate_percentage(10, -10) == -100.0