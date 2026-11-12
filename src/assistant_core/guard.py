"""Deterministic guardrails that run BEFORE retrieval or any LLM call."""

from __future__ import annotations

import re

_FIELDS = (
    r"(?:student (?:ids?|numbers?)|id numbers?|phone (?:numbers?)|(?:email|mail)\s+(?:addresses?|address)|mssv"
    r"|grade point average|grades?|scores?|gpas?|results?|phones?|address(?:es)?|emails?|mails?|contacts?|ids?)"
)

_TARGET = r"(?:(?:another|other)\s+students?|(?:my|a)\s+(?:friend|classmate|roommate))"

PRIVATE_PATTERNS: list[str] = [
    rf"\b(my|a) (friend|classmate|roommate)(?:'s|s'|'|s)?\s+(?:\w+\s+)?{_FIELDS}\b",
    rf"\b(another|other) students?(?:'s|s'|'|s)?\s+(?:\w+\s+)?{_FIELDS}\b",
    rf"\b{_FIELDS}\b\s+(?:of|for)\s+(another|other) students?\b",
    rf"\b{_FIELDS}\b\s+(?:of|for)\s+(my|a) (friend|classmate|roommate)\b",
    (
        rf"\b{_FIELDS}\b\s+(?:did|does)\s+"
        rf"(?:(?:another|other)\s+students?|(?:my|a)\s+(?:friend|classmate|roommate))\s+"
        r"(?:get|got|receive|received|have|has|earn|earned)\b"
    ),
    r"\b\d{8}\b",  # looks like an 8-digit student id
]

_RULE_PATTERNS: list[str] = [
    r"\b(?:does|do|can|would|will)\s+" + _TARGET + r"\s+needs?\b",
    r"\b" + _TARGET + r"\s+needs?\b",
    r"\bwhat\b.*\b(?:gpa|score|grade|result)\b.*\b(?:needed|required|needs?|requires?)\b",
    r"\b(?:requirements?|minimum|min|cutoff|threshold|eligibility|prerequisites?|criteria|criterion)\b",
    r"\b(?:needed|required)\s+(?:for|to)\b",
    r"\bwith\s+(?:a\s+)?(?:gpa|score|grade|result)\s*(?:of\s*)?\d",
    r"\b(?:gpa|score|grade)\s*(?:of\s*|[>=<]+\s*)?\d(?:\.\d+)?\b",
    (
        r"\b(?:can|could|is|are)\s+"
        + _TARGET
        + r"\s+(?:register|graduate|transfer|apply|take|retake|enroll|eligible|allowed)\b"
    ),
]

PRIVATE_REPLY: str = (
    "I can't share information about other students. " "You can only see your own records after logging in."
)


def is_private_request(text: str) -> bool:
    """Detect whether a query requests private data of other students or exposes student IDs."""
    if not text:
        return False
    t = text.lower()
    if re.search(r"\b\d{8}\b", t) is not None:
        return True
    if any(re.search(p, t) is not None for p in _RULE_PATTERNS):
        return False
    return any(re.search(p, t) is not None for p in PRIVATE_PATTERNS)
