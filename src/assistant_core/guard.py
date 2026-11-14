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

_POLICY_SUFFIX = (
    r"(?!\s+(?:requirements?|cutoffs?|thresholds?|needed|required"
    r"|advice|help|calculator|calculation|guidance|formula)\b)"
)
_POLICY_PREFIX = r"(?<!\bminimum\s)(?<!\bmin\s)(?<!\bpassing\s)(?<!\bcutoff\s)(?<!\bthreshold\s)"
_POLICY_ACTION = r"(?!\s+to\s+(?:register|graduate|transfer|apply|take|retake|enroll|pass|qualify)\b)"
_NON_VERB_MODIFIERS = r"(?:current|cumulative|official|final|overall|semester|recent|personal)"
_ACTUAL_QUALIFIER = r"(?:actual|real|current)\s+"
_EXPLICIT_CMD = r"(?:show(?:\s+me)?|give(?:\s+me)?|tell(?:\s+me)?|provide|display|view)\b"
_ATTAIN_VERBS = (
    r"(?:get|got|gotten|receive|received|have|has|had" r"|earn|earned|achieve|achieved|score|scored|obtain|obtained)"
)
_AUX = r"(?:did|does|has|had|is|was)"

PRIVATE_PATTERNS: list[str] = [
    # 1. Possessive with apostrophe (allows multiple adjective modifiers, e.g. "current cumulative GPA"):
    rf"\b{_TARGET}(?:'s|s')\s+(?:(?!(?:with|minimum|min|passing)\b)\w+\s+){{0,3}}{_FIELDS}{_POLICY_SUFFIX}\b",
    # 2. Compound noun without apostrophe (allows 0 words or non-verb modifier, e.g. "another student phone number"):
    rf"\b{_TARGET}\s+(?:{_NON_VERB_MODIFIERS}\s+)?{_FIELDS}{_POLICY_SUFFIX}\b",
    # 3. Field OF target: "GPA of another student", "address of my roommate", "email of another student"
    rf"\b{_FIELDS}{_POLICY_SUFFIX}\b\s+of\s+{_TARGET}\b",
    # 4. Explicit actual record or retrieval command for target (takes precedence over policy action):
    # e.g. "actual GPA for another student to register...", "Show me the GPA for another student to register...",
    # "Give me the actual score for my friend to pass the course"
    rf"\b{_POLICY_PREFIX}{_ACTUAL_QUALIFIER}{_FIELDS}{_POLICY_SUFFIX}\b\s+for\s+{_TARGET}\b",
    rf"\b{_EXPLICIT_CMD}.*\b{_POLICY_PREFIX}{_FIELDS}{_POLICY_SUFFIX}\b\s+for\s+{_TARGET}\b",
    # 5. Field FOR target (academic or contact, not preceded by policy words, not followed by policy action):
    rf"\b{_POLICY_PREFIX}{_FIELDS}{_POLICY_SUFFIX}\b\s+for\s+{_TARGET}{_POLICY_ACTION}\b",
    # 6. Attainment verbs in inverted questions, relative clauses, or direct queries:
    # e.g. "what grade did my friend get", "what grade has my friend received", "what is the grade my friend got"
    rf"\b{_FIELDS}\b\s+(?:{_AUX}\s+|(?:that\s+)?)?{_TARGET}\s+{_ATTAIN_VERBS}\b",
    # 7. 8-digit student ID
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
