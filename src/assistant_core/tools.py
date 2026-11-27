"""Deterministic tools for credit parsing and tuition calculation.

Phụ trách: Thành viên 5 (Quỳnh nhatquynh1107)
Phạm vi: parse_credits(), tuition()
"""

import re

from .errors import InvalidRequest

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _replace_number_words(text: str) -> str:
    """Normalize English number words (zero..ten) to digits."""
    lowered = text.lower()
    for word, digit in NUMBER_WORDS.items():
        lowered = re.sub(rf"\b{word}\b", str(digit), lowered)
    return lowered


def parse_credits(text: str) -> tuple[int, int]:
    normalized = _replace_number_words(text)
    if re.search(r"-\s*\d+", normalized):
        raise InvalidRequest("Credit and retake counts must not be negative.")
    retake = re.search(r"(\d+)\s*retake", normalized)
    numbers = [int(n) for n in re.findall(r"\d+", normalized)]
    retake_n = int(retake.group(1)) if retake else 0
    others = numbers.copy()

    if retake:
        others.remove(retake_n)
    if not others:
        raise InvalidRequest("How many credits?")
    return others[0], retake_n


def tuition(credits: int, retake: int, rate: int, retake_multiplier: float, max_credits: int) -> int:
    if not 1 <= credits <= max_credits:
        raise InvalidRequest(f"Credits must be between 1 and {max_credits}.")
    if retake < 0:
        raise InvalidRequest("Retake credits must not be negative.")
    return int(credits * rate + retake * rate * retake_multiplier)
