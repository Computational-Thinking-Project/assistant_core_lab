"""Tests for tools.py (credit parsing and tuition calculation).

Phụ trách: Thành viên 5 (Quỳnh nhatquynh1107)
"""

import pytest

from assistant_core.errors import InvalidRequest
from assistant_core.tools import parse_credits, tuition


def test_parse_with_retake():
    assert parse_credits("tuition for 18 credits and 2 retake") == (18, 2)


def test_parse_without_retake():
    assert parse_credits("tuition for 15 credits") == (15, 0)


def test_parse_retake_first():
    assert parse_credits("tuition for 2 retake and 18 credits") == (18, 2)


def test_parse_retake_as_word():
    assert parse_credits("tuition for 18 credits and two retakes") == (18, 2)


def test_parse_without_credits():
    with pytest.raises(InvalidRequest):
        parse_credits("tuition fee")


@pytest.mark.parametrize(
    "text",
    [
        "tuition for -10 credits",
        "tuition for - 10 credits",
        "tuition for -two credits",
        "tuition for 18 credits and -2 retakes",
        "tuition for 18 credits and - two retakes",
        "tuition for \u221210 credits",
        "tuition for \u2212 10 credits",
        "tuition for \u2212two credits",
        "tuition for 18 credits and \u22122 retakes",
        "tuition for \u2212two retakes and 18 credits",
    ],
)
def test_parse_rejects_negative_credit_or_retake_counts(text):
    with pytest.raises(InvalidRequest, match="negative"):
        parse_credits(text)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("tuition for 18 credits and 2 retakes - 2026 intake", (18, 2)),
        ("tuition for 2 retakes and 18 credits - 2026 intake", (18, 2)),
        ("tuition for 18 credits and two retakes \u2212 2026 intake", (18, 2)),
        ("tuition for 2 credits and 2 retakes - 2026 intake", (2, 2)),
    ],
)
def test_parse_keeps_credit_counts_with_intake_suffix(text, expected):
    assert parse_credits(text) == expected


def test_tuition_value():
    assert tuition(18, 2, 450000, 1.5, 30) == 9450000


def test_tuition_without_retake():
    assert tuition(15, 0, 450000, 1.5, 30) == 6750000


@pytest.mark.parametrize("credits", [0, 31])
def test_tuition_out_of_range(credits):
    with pytest.raises(InvalidRequest):
        tuition(credits, 0, 450000, 1.5, 30)


def test_tuition_rejects_negative_retake_count():
    with pytest.raises(InvalidRequest, match="negative"):
        tuition(18, -2, 450000, 1.5, 30)
