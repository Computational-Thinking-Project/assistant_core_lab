"""Tests for is_private_request hardening — Lab 08 Homework H1 (Bội Anh).

Covers edge cases required by Lab 08 H1:
  1. Empty input & whitespace
  2. Zero & numeric values
  3. Very large inputs (performance and ReDoS resistance)
  4. Vietnamese PII requests and false-positive controls
  5. Wrong types (None, int, list, dict, bytes)
"""

from __future__ import annotations

import time

import pytest

from assistant_core.guard import is_private_request


# 1. Empty input & whitespace
@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
        "\r\n",
        "  \t \n  ",
    ],
)
def test_empty_and_whitespace_inputs(text: str) -> None:
    assert is_private_request(text) is False


# 2. Zero & numeric values
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", False),
        ("0000", False),
        ("123", False),
        # 8-digit strings match the student ID pattern
        ("00000000", True),
        ("22127001", True),
        ("student 22127005", True),
    ],
)
def test_numeric_and_zero_inputs(text: str, expected: bool) -> None:
    assert is_private_request(text) is expected


# 3. Very large inputs (performance and ReDoS resistance)
def test_very_large_inputs() -> None:
    # 50,000 chars of benign text: must be fast (< 0.1s) and return False
    large_safe = "How much is tuition for 18 credits? " * 1500
    start = time.perf_counter()
    assert is_private_request(large_safe) is False
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2, f"Large input check took too long: {elapsed:.2f}s"

    # Large input containing a private request: must detect accurately
    large_private = "x" * 20000 + " What is the GPA of another student? " + "y" * 20000
    start = time.perf_counter()
    assert is_private_request(large_private) is True
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2, f"Large private input check took too long: {elapsed:.2f}s"


# 4. Vietnamese text: PII queries and non-private control queries
@pytest.mark.parametrize(
    "text",
    [
        "Cho tôi xem điểm thi của bạn tôi",
        "Xem số điện thoại của sinh viên khác",
        "Địa chỉ nhà của bạn cùng lớp là gì?",
        "GPA của bạn tôi là bao nhiêu?",
        "Cho xin email của bạn cùng phòng",
        "Tôi muốn hỏi số điện thoại sinh viên khác",
        "Xem thông tin cá nhân của bạn học",
    ],
)
def test_vietnamese_pii_requests_flagged(text: str) -> None:
    assert is_private_request(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "Học phí cho 18 tín chỉ là bao nhiêu?",
        "Điều kiện GPA tối thiểu để làm khóa luận tốt nghiệp?",
        "Điểm chuẩn xét học bổng học kỳ này?",
        "Phòng đào tạo ở đâu?",
        "Thủ tục cấp lại thẻ sinh viên bị mất",
        "Tôi có thể rút môn học trước thời hạn nào?",
    ],
)
def test_vietnamese_normal_questions_not_flagged(text: str) -> None:
    assert is_private_request(text) is False


# 5. Wrong types (None, int, list, dict, bytes)
@pytest.mark.parametrize(
    "wrong_val",
    [
        None,
        0,
        42,
        3.14,
        [],
        ["What is the GPA of another student?"],
        {"message": "What is the GPA of another student?"},
        b"What is the GPA of another student?",
    ],
)
def test_wrong_types_safe_handling(wrong_val: object) -> None:
    # Function must handle non-string gracefully without raising AttributeError or crashing
    assert is_private_request(wrong_val) is False  # type: ignore[arg-type]
