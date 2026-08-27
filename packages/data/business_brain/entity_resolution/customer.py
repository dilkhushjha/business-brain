from rapidfuzz import fuzz
def similarity(left: str, right: str) -> float:
    return fuzz.token_set_ratio(left, right) / 100.0
