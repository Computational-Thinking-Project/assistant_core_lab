import httpx

from ui.api_client import AssistantClient, ChatResult
from ui.logic import format_sources, status_note, validate_input

OK = {
    "answer": "Room B.201",
    "intent": "office",
    "sources": [{"id": "S26#1", "title": "1 Library borrowing"}],
    "degraded": False,
    "escalate": False,
    "path": "deterministic",
    "request_id": "abc123",
}


def client_with(handler) -> AssistantClient:
    return AssistantClient("http://api.test", transport=httpx.MockTransport(handler))


def test_ask_ok():
    r = client_with(lambda req: httpx.Response(200, json=OK)).ask("where is the library", "s1")
    assert r.ok and r.answer == "Room B.201" and r.request_id == "abc123"


def test_ask_backend_down():
    def boom(req):
        raise httpx.ConnectError("refused", request=req)

    r = client_with(boom).ask("hi", "s1")
    assert not r.ok and "backend" in r.error


def test_ask_validation_and_server_errors():
    assert "type a question" in client_with(lambda req: httpx.Response(422)).ask("", "s").error
    assert "error 500" in client_with(lambda req: httpx.Response(500)).ask("x", "s").error


def test_feedback():
    assert client_with(lambda req: httpx.Response(201, json={})).send_feedback("abc123", 1)


def test_feedback_negative():
    def handler(req):
        import json

        data = json.loads(req.content)
        assert data["request_id"] == "abc123"
        assert data["rating"] == -1
        return httpx.Response(
            201,
            json={
                "id": 1,
                "request_id": "abc123",
                "rating": -1,
                "comment": None,
                "created_at": "2026-11-16T16:00:00",
            },
        )

    assert client_with(handler).send_feedback("abc123", -1) is True


def test_f1_dislike_button_in_ui():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("ui/app.py")
    at.run()
    # Inject an assistant message with request_id to trigger thumbs-up & thumbs-down rendering
    at.session_state.messages.append({"role": "assistant", "content": "Sample answer", "request_id": "req-f1-test"})
    at.run()

    # Find the down button with label 👎 and verify unique key
    down_btn = [b for b in at.button if b.label == "👎"][0]
    assert down_btn.key == "down1"

    # Click the 👎 button
    down_btn.click().run()

    # Verify request_id is recorded in rated session_state
    assert "req-f1-test" in at.session_state.rated

    # Verify on rerun that both buttons disappear
    at.run()
    assert not any(b.label == "👎" for b in at.button)
    assert not any(b.label == "👍" for b in at.button)


def test_validate_input():
    assert validate_input("   ") == "Please type a question."
    assert validate_input("x" * 2001).startswith("Your question is too long")
    assert validate_input("hello") is None


def test_format_sources():
    assert format_sources([]) == ""
    assert format_sources(OK["sources"]) == "Sources: S26#1 — 1 Library borrowing"


def test_status_note():
    assert "Training Office" in status_note(ChatResult(ok=True, escalate=True))
    assert status_note(ChatResult(ok=True)) is None
