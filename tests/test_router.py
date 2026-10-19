"""Tests for router.py (intent detection) and models.py validation.

Phụ trách: Thành viên 3 (Đạt)
"""

import pytest
from pydantic import ValidationError

from assistant_core.models import Intent, Message, Response, Source
from assistant_core.router import route

SAMPLE_OFFICES = {"library", "student affairs", "admissions"}


@pytest.mark.parametrize(
    "text",
    [
        "hi",
        "hello",
        "hey",
        "xin chao",
        "Hello!",
        "HEY?",
        "  xin chao.  ",
        "HI?!",
    ],
)
def test_route_greeting(text: str) -> None:
    assert route(text, SAMPLE_OFFICES) is Intent.GREETING


@pytest.mark.parametrize(
    "text",
    [
        "tuition for 18 credits and 2 retake",
        "What is the fee?",
        "how much is the tuition fee",
        "FEE calculation",
    ],
)
def test_route_fee(text: str) -> None:
    assert route(text, SAMPLE_OFFICES) is Intent.FEE


@pytest.mark.parametrize(
    "text",
    [
        "Where is the library?",
        "what time does student affairs open?",
        "Admissions office location",
    ],
)
def test_route_office(text: str) -> None:
    assert route(text, SAMPLE_OFFICES) is Intent.OFFICE


@pytest.mark.parametrize(
    "text",
    [
        "can I defer my exam?",
        "thesis registration credits",
        "what are the graduation requirements?",
    ],
)
def test_route_rule(text: str) -> None:
    assert route(text, SAMPLE_OFFICES) is Intent.RULE


def test_route_office_not_in_names() -> None:
    assert route("Where is the clinic?", SAMPLE_OFFICES) is Intent.RULE


def test_message_valid() -> None:
    msg = Message(text="hello assistant")
    assert msg.text == "hello assistant"
    assert msg.session_id == "local"


def test_message_custom_session() -> None:
    msg = Message(text="hello", session_id="user_123")
    assert msg.session_id == "user_123"


def test_message_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(text="")


def test_message_too_long_rejected() -> None:
    with pytest.raises(ValidationError):
        Message(text="a" * 2001)


def test_response_defaults() -> None:
    resp = Response(answer="Hello!", intent=Intent.GREETING)
    assert resp.answer == "Hello!"
    assert resp.intent is Intent.GREETING
    assert resp.sources == []
    assert resp.degraded is False


def test_response_with_sources_and_degraded() -> None:
    src = Source(id="H26-5.3", title="Thesis Policy")
    resp = Response(
        answer="Fallback answer",
        intent=Intent.RULE,
        sources=[src],
        degraded=True,
    )
    assert resp.degraded is True
    assert len(resp.sources) == 1
    assert resp.sources[0].id == "H26-5.3"
