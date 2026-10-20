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


def test_parse_without_credits():
    with pytest.raises(InvalidRequest):
        parse_credits("tuition fee")


def test_tuition_value():
    assert tuition(18, 2, 450000, 1.5, 30) == 9450000


def test_tuition_without_retake():
    assert tuition(15, 0, 450000, 1.5, 30) == 6750000


@pytest.mark.parametrize("credits", [0, 31])
def test_tuition_out_of_range(credits):
    with pytest.raises(InvalidRequest):
        tuition(credits, 0, 450000, 1.5, 30)
