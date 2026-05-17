# sample_repo/math_utils.py

def add_numbers(a: int, b: int) -> int:
    return a + b

def divide_numbers(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b