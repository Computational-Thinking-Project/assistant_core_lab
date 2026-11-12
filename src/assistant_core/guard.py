"""Deterministic guardrails that run BEFORE retrieval or any LLM call."""

from __future__ import annotations

import re

_CONTACT_FIELDS = (
    r"(?:student (?:ids?|numbers?)|id numbers?|phone (?:numbers?)|(?:email|mail)\s+(?:addresses?|address)|mssv"
    r"|phones?|address(?:es)?|emails?|mails?|contacts?|ids?)"
)
_ACADEMIC_FIELDS = r"(?:grade point average|grades?|scores?|gpas?|results?)"
_FIELDS = rf"(?:{_CONTACT_FIELDS}|{_ACADEMIC_FIELDS})"
_TARGET = r"(?:(?:another|other)\s+students?|(?:my|a)\s+(?:friend|classmate|roommate))"

_POLICY_SUFFIX = r"(?!\s+(?:requirements?|cutoffs?|thresholds?)\b)"
_MODIFIER = r"(?:(?!(?:with|minimum|min|passing)\b)\w+\s+)?"

PRIVATE_PATTERNS: list[str] = [
    # 1. Possessive third-party requests: "another student's GPA", "my friend's email", "other students' grades"
    rf"\b{_TARGET}(?:'s|s'|'|s)?\s+{_MODIFIER}{_FIELDS}{_POLICY_SUFFIX}\b",
    # 2. Field OF target: "GPA of another student", "address of my roommate", "email of another student"
    rf"\b{_FIELDS}{_POLICY_SUFFIX}\b\s+of\s+{_TARGET}\b",
    # 3. Contact field FOR target: "phone number for other student", "contact for another student"
    rf"\b{_CONTACT_FIELDS}\b\s+for\s+{_TARGET}\b",
    # 4. Attainment verbs: "what grade did my friend get", "what GPA does another student have"
    (rf"\b{_FIELDS}\b\s+(?:did|does)\s+" rf"{_TARGET}\s+" r"(?:get|got|receive|received|have|has|earn|earned)\b"),
    # 5. 8-digit student ID
    r"\b\d{8}\b",
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
