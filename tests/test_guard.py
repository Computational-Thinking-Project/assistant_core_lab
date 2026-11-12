"""Tests for deterministic privacy guard and runtime Knowledge Base files."""

from __future__ import annotations

from pathlib import Path

import pytest

from assistant_core.guard import PRIVATE_PATTERNS, PRIVATE_REPLY, is_private_request


@pytest.mark.parametrize(
    "query",
    [
        "what grade did my friend get",
        "show the GPA of another student",
        "phone of 22127001",
        "what is my classmate's score",
        "what is the result of another student",
        "phone number for other student",
        "address of my roommate",
        "scores for 22127135",
        "email of student 20261234",
        "show me the email of another student",
        "what is the email of student 22127001",
        "my friend's email",
        "email of another student",
        "contact of another student",
        "show another student's GPA",
        "what is another student's email",
        "other student's score",
        "other students' grades",
        "another student's phone",
        "show my classmate's student ID",
        "what is another student's student number",
        "show another student's ID",
        "student ID of another student",
        "student number of my classmate",
    ],
)
def test_private_guard_positive_cases(query: str):
    """Guard must intercept inquiries about other students' records or PII."""
    assert is_private_request(query) is True


@pytest.mark.parametrize(
    "query",
    [
        "what is my GPA requirement for the thesis",
        "what is the GPA requirement for the thesis",
        "minimum GPA to register thesis",
        "can I register my thesis with 118 credits",
        "where is the library",
        "how much does a retake cost",
        "tuition for 18 credits and 2 retake",
        "what is the tuition per credit",
        "I lost my student card",
        "cost to replace a lost student card",
        "course withdrawal refund deadline",
        "how to reset my password",
        "what is the capital of France",
        "",
        "   ",
    ],
)
def test_private_guard_negative_cases(query: str):
    """Guard must NOT block legitimate user inquiries or policy questions."""
    assert is_private_request(query) is False


def test_private_reply_content():
    """Verify standard privacy refusal response text."""
    assert "can't share information about other students" in PRIVATE_REPLY
    assert "login" in PRIVATE_REPLY.lower() or "logging in" in PRIVATE_REPLY.lower()


def test_private_patterns_list():
    """Verify regex patterns for student IDs and PII are compiled and non-empty."""
    assert isinstance(PRIVATE_PATTERNS, list)
    assert len(PRIVATE_PATTERNS) >= 4
    assert any(r"\d{8}" in p for p in PRIVATE_PATTERNS)


def test_runtime_kb_files_exist_and_match_sample():
    """Verify that runtime KB files exist in data/kb with expected headers and 14 chunks."""
    kb_dir = Path("data/kb")
    assert kb_dir.is_dir(), "data/kb directory must exist"

    expected_files = {"fees_2026.md", "handbook_2026.md", "services_2026.md"}
    actual_files = {p.name for p in kb_dir.glob("*.md")}
    assert expected_files <= actual_files, f"Missing KB files: {expected_files - actual_files}"

    # Verify 14 chunks across files by counting '# ' headings
    chunk_headings: list[str] = []
    for md_file in sorted(kb_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        assert "doc_id:" in content
        assert "title:" in content
        assert "version:" in content
        assert "owner:" in content
        for line in content.splitlines():
            if line.startswith("# "):
                chunk_headings.append(line)

    assert len(chunk_headings) == 14, f"Expected exactly 14 chunks, found {len(chunk_headings)}"
