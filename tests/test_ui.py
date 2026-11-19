"""Tests for UI logic, the HTTP client, and Streamlit feedback flows.

Covers:
  - AssistantClient: ask() and send_feedback() — via httpx.MockTransport
  - validate_input()
  - format_sources()           ← L1 (Trung Anh)
  - status_note()              ← L2 (Trung Anh)
  - stream_generator()         ← Bonus D.5
  - format_source_badges()     ← Bonus D.5

No third-party mock library required: httpx.MockTransport is part of httpx.
"""

from __future__ import annotations

import json

import httpx

from ui.api_client import AssistantClient, ChatResult
from ui.logic import (
    format_source_badges,
    format_sources,
    status_note,
    stream_generator,
    validate_input,
)

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


def test_ask_500() -> None:
    client = _client_with([_mock_response(500, "temporary failure")])
    result = client.ask("Hello?")
    assert not result.ok
    assert result.error == "Server error 500: temporary failure"


# ---------------------------------------------------------------------------
# AssistantClient.send_feedback() — POST /v1/feedback (expects 201)
# ---------------------------------------------------------------------------


def test_feedback_ok() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/feedback"
        assert json.loads(request.read()) == {"request_id": "req001abc123", "rating": 1}
        return httpx.Response(201, json={"id": 1, "created_at": "2026-01-01T00:00:00Z"})

    client = AssistantClient(base_url=BASE, timeout=5.0, transport=httpx.MockTransport(handler))
    assert client.send_feedback("req001abc123", 1) is True


def test_feedback_negative() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/feedback"
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
    assert validate_input("") == "Please type a question."
    assert validate_input("   ") == "Please type a question."
    assert validate_input("x" * 2000) is None
    assert validate_input("x" * 2001) == "Your question is too long (max 2000 characters)."
    assert validate_input("How much is tuition?") is None


# ---------------------------------------------------------------------------
# L1 & L2 — format_sources and status_note (Trung Anh)
# ---------------------------------------------------------------------------


def test_format_sources() -> None:
    assert format_sources([]) == ""
    assert format_sources([{"id": "S26#1", "title": "1 Library borrowing"}]) == "Sources: S26#1 — 1 Library borrowing"
    assert (
        format_sources(
            [
                {"id": "H26#5.3", "title": "5.3 Thesis registration"},
                {"id": "F26#1.1", "title": "Tuition per credit"},
            ]
        )
        == "Sources: H26#5.3 — 5.3 Thesis registration; F26#1.1 — Tuition per credit"
    )


def test_status_note() -> None:
    assert (
        status_note(ChatResult(ok=True, escalate=True))
        == "I could not find this in the official documents. A staff member can help: Training Office, room I.101."
    )
    assert (
        status_note(ChatResult(ok=True, degraded=True))
        == "Shown directly from the source document (the AI helper was unavailable)."
    )
    assert (
        status_note(ChatResult(ok=True, escalate=True, degraded=True))
        == "I could not find this in the official documents. A staff member can help: Training Office, room I.101."
    )
    assert status_note(ChatResult(ok=True)) is None


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


def test_f1_dislike_succeeds_after_failed_feedback_retry(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    calls: list[tuple[str, int]] = []

    def mock_send_feedback(self, rid: str, rating: int) -> bool:
        calls.append((rid, rating))
        return len(calls) == 2

    monkeypatch.setattr(AssistantClient, "healthy", lambda self: True)
    monkeypatch.setattr(AssistantClient, "send_feedback", mock_send_feedback)
    at = AppTest.from_file("ui/app.py").run()
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-retry"})
    at.run()

    [b for b in at.button if b.label == "👎"][0].click().run()
    assert calls == [("req-retry", -1)]
    assert "req-retry" not in at.session_state.rated
    assert any(b.label == "👎" for b in at.button)
    assert any(b.label == "👍" for b in at.button)

    [b for b in at.button if b.label == "👎"][0].click().run()
    assert calls == [("req-retry", -1), ("req-retry", -1)]
    assert "req-retry" in at.session_state.rated
    assert not any(b.label == "👎" for b in at.button)
    assert not any(b.label == "👍" for b in at.button)


def test_h1_first_screen_shows_ai_notice_and_examples_in_main_pane(monkeypatch) -> None:
    from streamlit.testing.v1 import AppTest

    from ui.api_client import ChatResult

    asked: list[str] = []

    def mock_ask(self, question: str, session_id: str = "") -> ChatResult:
        asked.append(question)
        return ChatResult(
            ok=True,
            answer="You need at least 120 accumulated credits.",
            sources=[{"id": "H26#5.3", "title": "5.3 Thesis registration"}],
            request_id="req-h1-test",
        )

    monkeypatch.setattr(AssistantClient, "healthy", lambda self: True)
    monkeypatch.setattr(AssistantClient, "ask", mock_ask)

    at = AppTest.from_file("ui/app.py").run(timeout=10)

    main_captions = [c.value for c in at.main.caption]
    assert any("AI assistant" in cap for cap in main_captions)
    assert at.title[0].value == "FIT Study Assistant"
    assert not any("\U0001f4a1" in s.value for s in at.sidebar.subheader)

    starter_btns = [b for b in at.main.button if (b.key or "").startswith("starter_ex_")]
    assert len(starter_btns) == 4

    starter_btns[0].click().run(timeout=10)
    assert asked == ["Can I register my thesis with 118 credits?"]
    assert not any((b.key or "").startswith("starter_ex_") for b in at.main.button)


def test_h1_slow_health_check_does_not_show_offline_banner(monkeypatch) -> None:
    import socket
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from streamlit.testing.v1 import AppTest

    seen_paths: list[str] = []

    class SlowHealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            seen_paths.append(self.path)
            time.sleep(0.8)
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHealthHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("ASSISTANT_API_URL", f"http://127.0.0.1:{port}")
        at = AppTest.from_file("ui/app.py").run(timeout=10)
        assert seen_paths == ["/health"]
        assert len(at.error) == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        unused_port = sock.getsockname()[1]

    monkeypatch.setenv("ASSISTANT_API_URL", f"http://127.0.0.1:{unused_port}")
    started = time.monotonic()
    down_at = AppTest.from_file("ui/app.py").run(timeout=10)
    elapsed = time.monotonic() - started
    assert elapsed < 3.0
    assert len(down_at.error) == 1
    assert "The assistant backend is not reachable" in down_at.error[0].value
    assert "Training Office (room I.101)" in down_at.error[0].value
