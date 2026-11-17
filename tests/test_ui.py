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


def test_feedback_negative() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        import json

        data = json.loads(request.read())
        assert data["rating"] == -1
        assert data["request_id"] == "abc123"
        return httpx.Response(201, json={"id": 1, "created_at": "2026-01-01T00:00:00Z"})

    transport = httpx.MockTransport(handler)
    client = AssistantClient(base_url=BASE, timeout=5.0, transport=transport)
    assert client.send_feedback("abc123", -1) is True


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


# ---------------------------------------------------------------------------
# F1 — Feedback UI Buttons & Flow (Bội Anh)
# ---------------------------------------------------------------------------


def test_f1_dislike_button_in_ui(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    calls: list[tuple[str, int]] = []

    def mock_send_feedback(self, rid: str, rating: int, comment: str | None = None) -> bool:
        calls.append((rid, rating))
        return True

    monkeypatch.setattr(AssistantClient, "send_feedback", mock_send_feedback)
    at = AppTest.from_file("ui/app.py").run()
    # Inject an assistant message with request_id to trigger thumbs-up & thumbs-down rendering
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-f1-test"})
    at.run()

    # Find the 👎 button
    down_btn = [b for b in at.button if b.label == "👎"][0]
    assert down_btn.key == "down1"

    # Click the 👎 button once - both buttons must disappear immediately on this single run
    down_btn.click().run()

    # Assert request ID and -1 rating transmitted by 👎
    assert calls == [("req-f1-test", -1)]

    # Verify request_id is recorded in rated session_state and controls are gone without an extra run
    assert "req-f1-test" in at.session_state.rated
    assert not any(b.label == "👎" for b in at.button)
    assert not any(b.label == "👍" for b in at.button)


def test_f1_like_button_in_ui(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    calls: list[tuple[str, int]] = []

    def mock_send_feedback(self, rid: str, rating: int, comment: str | None = None) -> bool:
        calls.append((rid, rating))
        return True

    monkeypatch.setattr(AssistantClient, "send_feedback", mock_send_feedback)
    at = AppTest.from_file("ui/app.py").run()
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-like-test"})
    at.run()

    up_btn = [b for b in at.button if b.label == "👍"][0]
    assert up_btn.key == "up1"

    # Click the 👍 button once - both buttons must disappear immediately on this single run
    up_btn.click().run()

    # Assert request ID and +1 rating transmitted by 👍
    assert calls == [("req-like-test", 1)]

    # Verify request_id is recorded in rated session_state and controls are gone without an extra run
    assert "req-like-test" in at.session_state.rated
    assert not any(b.label == "👍" for b in at.button)
    assert not any(b.label == "👎" for b in at.button)


def test_f1_dislike_button_failed_feedback_allows_retry(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(AssistantClient, "send_feedback", lambda self, rid, rating, comment=None: False)
    at = AppTest.from_file("ui/app.py").run()
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-fail-test"})
    at.run()

    down_btn = [b for b in at.button if b.label == "👎"][0]
    # Click 👎 when backend fails
    down_btn.click().run()

    # When feedback submission fails, request must NOT be marked as rated and buttons remain for retry
    assert "req-fail-test" not in at.session_state.rated
    assert len([b for b in at.button if b.label == "👎"]) == 1
    assert len([b for b in at.button if b.label == "👍"]) == 1


def test_f1_like_button_failed_feedback_allows_retry(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(AssistantClient, "send_feedback", lambda self, rid, rating, comment=None: False)
    at = AppTest.from_file("ui/app.py").run()
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-fail-like"})
    at.run()

    up_btn = [b for b in at.button if b.label == "👍"][0]
    # Click 👍 when backend fails
    up_btn.click().run()

    # When feedback submission fails, request must NOT be marked as rated and buttons remain for retry
    assert "req-fail-like" not in at.session_state.rated
    assert len([b for b in at.button if b.label == "👍"]) == 1
    assert len([b for b in at.button if b.label == "👎"]) == 1
