"""Deterministic guardrails that run BEFORE retrieval or any LLM call."""

from __future__ import annotations

import re

_FIELDS = r"(grade|score|gpa|result|phone|address|email|mail|contact" r"|student id|student number|id number|mssv|id)"

PRIVATE_PATTERNS: list[str] = [
    rf"\b(my|a) (friend|classmate|roommate)'?s?\b.*\b{_FIELDS}",
    rf"\b(another|other) student'?s?\b.*\b{_FIELDS}",
    rf"\b{_FIELDS}s?\b.*\b(of|for) (another|other) student",
    rf"\b{_FIELDS}s?\b.*\b(my|a) (friend|classmate|roommate)",
    r"\b\d{8}\b",  # looks like an 8-digit student id
]

PRIVATE_REPLY: str = (
    "I can't share information about other students. " "You can only see your own records after logging in."
)


def is_private_request(text: str) -> bool:
    """Detect whether a query requests private data of other students or exposes student IDs."""
    if not text:
        return False
    t = text.lower()
    return any(re.search(p, t) is not None for p in PRIVATE_PATTERNS)
