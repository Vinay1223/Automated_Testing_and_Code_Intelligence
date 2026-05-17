def calculate_percentage(part: float, total: float) -> float:
    if total == 0:
        raise ValueError("Total cannot be zero.")
    return round((part / total) * 100, 2)
