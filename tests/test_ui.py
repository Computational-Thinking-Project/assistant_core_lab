"""Tests for ui/logic.py and ui/api_client.py — Bonus D.5 scope (Duy).

Covers:
  - AssistantClient: ask(), healthy(), send_feedback() — via httpx.MockTransport
  - validate_input()
  - stream_generator()         ← Bonus D.5
  - format_source_badges()     ← Bonus D.5

L1 (format_sources) and L2 (status_note) are intentionally NOT tested here;
those belong to Trung Anh's PR.

No third-party mock library required: httpx.MockTransport is part of httpx.
"""

from __future__ import annotations

import httpx

from ui.api_client import AssistantClient
from ui.logic import format_source_badges, stream_generator, validate_input

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

BASE = "http://127.0.0.1:8000"


def _mock_response(status_code: int, body: dict | str) -> httpx.Response:
    if isinstance(body, str):
        return httpx.Response(status_code, text=body)
    return httpx.Response(status_code, json=body)


def _client_with(responses: list[httpx.Response]) -> AssistantClient:
    """Return an AssistantClient whose HTTP calls are served from *responses* in order."""
    idx = 0

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal idx
        resp = responses[idx]
        idx += 1
        return resp

    transport = httpx.MockTransport(_handler)
    return AssistantClient(base_url=BASE, timeout=5.0, transport=transport)


# ---------------------------------------------------------------------------
# AssistantClient.ask() — POST /v1/chat
# ---------------------------------------------------------------------------


def test_ask_ok() -> None:
    payload = {
        "answer": "You need 120 credits.",
        "sources": [{"id": "H26", "title": "Thesis rules"}],
        "request_id": "req001abc123",
        "escalate": False,
        "degraded": False,
        "intent": "rule",
        "path": "retrieval",
        "confidence": 0.9,
    }
    client = _client_with([_mock_response(200, payload)])
    result = client.ask("How many credits to register thesis?", session_id="sess1")
    assert result.ok
    assert result.answer == "You need 120 credits."
    assert result.sources == [{"id": "H26", "title": "Thesis rules"}]
    assert result.request_id == "req001abc123"
    assert not result.escalate
    assert not result.degraded


def test_ask_backend_down() -> None:
    def _raise(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    transport = httpx.MockTransport(_raise)
    client = AssistantClient(base_url=BASE, timeout=5.0, transport=transport)
    result = client.ask("Hello?")
    assert not result.ok
    assert "connect" in result.error.lower()


def test_ask_timeout() -> None:
    def _raise(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    transport = httpx.MockTransport(_raise)
    client = AssistantClient(base_url=BASE, timeout=5.0, transport=transport)
    result = client.ask("Hello?")
    assert not result.ok
    assert "timed out" in result.error.lower()


def test_ask_422() -> None:
    body = {"error": {"code": "invalid_request", "message": "message field required"}}
    client = _client_with([_mock_response(422, body)])
    result = client.ask("")
    assert not result.ok
    assert "invalid" in result.error.lower()


def test_ask_429() -> None:
    client = _client_with([_mock_response(429, {"error": {"code": "too_many_requests"}})])
    result = client.ask("spam")
    assert not result.ok
    assert "too many" in result.error.lower()


# ---------------------------------------------------------------------------
# AssistantClient.send_feedback() — POST /v1/feedback (expects 201)
# ---------------------------------------------------------------------------


def test_feedback_ok() -> None:
    body = {"id": 1, "request_id": "req001abc123", "rating": 1, "created_at": "2026-01-01T00:00:00Z"}
    client = _client_with([_mock_response(201, body)])
    assert client.send_feedback("req001abc123", 1) is True


def test_feedback_fail() -> None:
    client = _client_with([_mock_response(422, {"error": {"code": "invalid_request"}})])
    assert client.send_feedback("bad", 99) is False


# ---------------------------------------------------------------------------
# validate_input
# ---------------------------------------------------------------------------


def test_validate_input() -> None:
    assert validate_input("") is not None
    assert validate_input("   ") is not None
    assert validate_input("x" * 2001) is not None
    assert validate_input("How much is tuition?") is None


# ---------------------------------------------------------------------------
# Bonus D.5 — stream_generator
# ---------------------------------------------------------------------------


def test_stream_generator() -> None:
    text = "Hello world foo"
    chunks = list(stream_generator(text, delay=0))
    # Reconstruct should equal original text
    assert "".join(chunks) == text
    # Must yield one chunk per word for a multi-word string
    assert len(chunks) == 3
    # All but the last chunk should end with a space
    for chunk in chunks[:-1]:
        assert chunk.endswith(" "), f"chunk {chunk!r} should end with space"


def test_stream_generator_single_word() -> None:
    chunks = list(stream_generator("hello", delay=0))
    assert chunks == ["hello"]


# ---------------------------------------------------------------------------
# Bonus D.5 — format_source_badges
# ---------------------------------------------------------------------------


def test_format_source_badges() -> None:
    sources = [
        {"id": "H26", "title": "Thesis registration"},
        {"id": "F5", "title": "Fee schedule"},
        {"id": "", "title": ""},  # empty — should be excluded
    ]
    badges = format_source_badges(sources)
    # Empty-id-and-title entry must be dropped
    assert len(badges) == 2
    assert badges[0] == ("H26", "Thesis registration")
    assert badges[1] == ("F5", "Fee schedule")

    # Edge: empty list → empty list
    assert format_source_badges([]) == []

    # Edge: source missing title key → safe, title defaults to ""
    partial = format_source_badges([{"id": "X1"}])
    assert partial == [("X1", "")]
