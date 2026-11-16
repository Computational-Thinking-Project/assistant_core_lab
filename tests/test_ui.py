"""Tests for ui/logic.py and ui/api_client.py — Bonus D.5 scope (Duy).

Covers:
  - AssistantClient: ask(), healthy(), send_feedback() — via httpx mock
  - validate_input()
  - stream_generator()         ← Bonus D.5
  - format_source_badges()     ← Bonus D.5

L1 (format_sources) and L2 (status_note) are intentionally NOT tested here;
those belong to Trung Anh's PR.
"""

from __future__ import annotations

import httpx
import respx

from ui.api_client import AssistantClient
from ui.logic import format_source_badges, stream_generator, validate_input

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

BASE = "http://127.0.0.1:8000"


def _make_client() -> AssistantClient:
    return AssistantClient(base_url=BASE, timeout=5.0)


# ---------------------------------------------------------------------------
# AssistantClient tests
# ---------------------------------------------------------------------------


@respx.mock
def test_ask_ok() -> None:
    respx.post(f"{BASE}/ask").mock(
        return_value=httpx.Response(
            200,
            json={
                "answer": "You need 120 credits.",
                "sources": [{"id": "H26", "title": "Thesis rules"}],
                "request_id": "req-001",
                "escalate": False,
                "degraded": False,
            },
        )
    )
    result = _make_client().ask("How many credits to register thesis?")
    assert result.ok
    assert result.answer == "You need 120 credits."
    assert result.sources == [{"id": "H26", "title": "Thesis rules"}]
    assert result.request_id == "req-001"
    assert not result.escalate
    assert not result.degraded


@respx.mock
def test_ask_backend_down() -> None:
    respx.post(f"{BASE}/ask").mock(side_effect=httpx.ConnectError("refused"))
    result = _make_client().ask("Hello?")
    assert not result.ok
    assert "connect" in result.error.lower()


@respx.mock
def test_ask_validation_and_server_errors() -> None:
    # 422 from the backend
    respx.post(f"{BASE}/ask").mock(return_value=httpx.Response(422, text="Unprocessable"))
    result = _make_client().ask("bad payload")
    assert not result.ok
    assert "422" in result.error


@respx.mock
def test_feedback() -> None:
    respx.post(f"{BASE}/feedback").mock(return_value=httpx.Response(200))
    ok = _make_client().send_feedback("req-001", 1)
    assert ok


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
    # Must yield more than one chunk for a multi-word string
    assert len(chunks) == 3
    # All but the last chunk should end with a space
    for chunk in chunks[:-1]:
        assert chunk.endswith(" "), f"chunk {chunk!r} should end with space"


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

    # Edge: source missing keys → still safe
    partial = format_source_badges([{"id": "X1"}])
    assert partial == [("X1", "")]
