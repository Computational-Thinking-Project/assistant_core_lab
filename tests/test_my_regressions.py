"""Lab 8 Part E: turn YOUR Week-7 failures into regression tests.

Write at least three tests. Each one must:
  - have a name that says what went wrong, e.g. test_empty_sources_does_not_crash_ui
  - FAIL on the old code (check by temporarily undoing your fix), and PASS after the fix.
Use the fixtures `service`, `settings` from conftest.py, or build a TestClient like tests/test_security.py.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from assistant_api.db import Repository, init_db, make_engine
from assistant_api.main import create_app
from assistant_core.models import Message


@pytest.fixture
def regression_api(settings, service):
    engine = make_engine("sqlite://")
    init_db(engine)
    s = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 50})
    return TestClient(create_app(s, service, repo=Repository(engine, "test-salt")))


def test_example_greeting_still_works(service):
    """Example: a control case that must never break."""
    assert "Hello" in service.handle(Message(text="hi")).answer


def test_retake_number_as_word(service):
    """BUG-7: 'two retakes' was ignored when retake count was written as a word, giving wrong total."""
    r = service.handle(Message(text="tuition for 18 credits and two retakes"))
    assert "8,100,000" not in r.answer  # never the wrong total (8,100,000 VND ignores the retakes)
    assert "9,450,000" in r.answer  # 18*450_000 + 2*450_000*1.5 = 9,450,000 VND


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": "   \t\n  "},
        {"message": "hello\x00world"},
        {"message": "x" * 2001},
        {"message": "tuition for 18 credits", "session_id": "   "},
        {"message": "tuition for 18 credits", "session_id": "bad\x00sid"},
    ],
)
def test_oversized_or_malformed_input(regression_api: TestClient, payload: dict) -> None:
    """BUG-2: blank/whitespace-only, null-byte, and oversized chat inputs must return 422 and store nothing."""
    resp = regression_api.post("/v1/chat", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_request"

    # Control query still works cleanly and stats reflect only valid interactions.
    stats_before = regression_api.get("/v1/stats/intents", headers={"X-API-Key": "secret-admin"})
    assert stats_before.status_code == 200 and stats_before.json() == []

    ok = regression_api.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
    assert ok.status_code == 200
    assert "9,450,000" in ok.json()["answer"]


def test_feedback_validation_rejects_blank_ids_and_unbounded_limits(regression_api: TestClient) -> None:
    """BUG-2: blank/null-byte feedback fields and out-of-range GET /v1/feedback?limit must return 422."""
    bad_json = regression_api.post("/v1/chat", content=b"{not json", headers={"Content-Type": "application/json"})
    assert bad_json.status_code == 422

    assert regression_api.post("/v1/feedback", json={"request_id": "   ", "rating": 1}).status_code == 422
    assert regression_api.post("/v1/feedback", json={"request_id": "abc\x00", "rating": 1}).status_code == 422
    assert regression_api.get("/v1/feedback?limit=-1", headers={"X-API-Key": "secret-admin"}).status_code == 422
    assert regression_api.get("/v1/feedback?limit=0", headers={"X-API-Key": "secret-admin"}).status_code == 422
    assert regression_api.get("/v1/feedback?limit=501", headers={"X-API-Key": "secret-admin"}).status_code == 422
