import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from assistant_api.db import ChatSession, Interaction, Repository, init_db, make_engine
from assistant_api.main import create_app
from assistant_api.schemas import ChatResponse
from assistant_api.weather import WeatherClient
from assistant_core.models import Intent, Response, Source

OK_JSON = {"current": {"time": "2026-10-05T09:00", "temperature_2m": 31.2, "weather_code": 3, "wind_speed_10m": 8.5}}


def weather_with(handler) -> WeatherClient:
    transport = httpx.MockTransport(handler)
    return WeatherClient("https://example.test/forecast", 10.76, 106.68, retries=1, transport=transport)


@pytest.fixture
def repo():
    engine = make_engine("sqlite://")
    init_db(engine)
    return Repository(engine, "test-salt")


@pytest.fixture
def client(settings, service, repo):
    settings = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 5})
    app = create_app(settings, service, weather_with(lambda req: httpx.Response(200, json=OK_JSON)), repo=repo)
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_list_offices_success(client: TestClient) -> None:
    """Return HTTP 200 and a JSON list with the public office fields."""
    response = client.get("/v1/offices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(set(office) == {"name", "room", "hours"} for office in data)


def test_list_offices_contains_library(client: TestClient) -> None:
    """Include Library and keep the office names in sorted order."""
    response = client.get("/v1/offices")
    names = [office["name"] for office in response.json()]
    assert "Library" in names
    assert names == sorted(names)


def test_chat_fee(client):
    r = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "fee" and "9,450,000" in body["answer"] and body["request_id"]


def test_chat_validation_error(client):
    r = client.post("/v1/chat", json={"message": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_rate_limit(client):
    codes = [client.post("/v1/chat", json={"message": "hi"}).status_code for _ in range(6)]
    assert codes[-1] == 429


def test_feedback_roundtrip(client):
    rid = client.post("/v1/chat", json={"message": "hi"}).json()["request_id"]
    r = client.post("/v1/feedback", json={"request_id": rid, "rating": 1})
    assert r.status_code == 201 and r.json()["id"] == 1
    assert client.get("/v1/feedback").status_code == 401
    listed = client.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert listed.status_code == 200 and len(listed.json()) == 1


def test_feedback_unknown_request_id(client):
    r = client.post("/v1/feedback", json={"request_id": "nonexistent-id", "rating": 1})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_request_id"


def test_feedback_rating_out_of_range(client):
    assert client.post("/v1/feedback", json={"request_id": "x", "rating": 5}).status_code == 422


def test_intent_stats(client):
    client.post("/v1/chat", json={"message": "tuition for 18 credits"})
    assert client.get("/v1/stats/intents").status_code == 401
    r = client.get("/v1/stats/intents", headers={"X-API-Key": "secret-admin"})
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_weather_ok(client):
    r = client.get("/v1/weather")
    assert r.status_code == 200 and r.json()["description"] == "overcast"


def test_weather_down_returns_503(settings, service, repo):
    def boom(req):
        raise httpx.ConnectTimeout("timeout", request=req)

    app = create_app(settings, service, weather_with(boom), repo=repo)
    r = TestClient(app).get("/v1/weather")
    assert r.status_code == 503 and r.json()["error"]["code"] == "weather_service_unavailable"


def test_weather_stale_cache_when_upstream_fails():
    calls = {"n": 0}

    def flaky(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(200, json=OK_JSON)
        return httpx.Response(500)

    w = weather_with(flaky)
    w.cache_ttl_s = 0  # force a refresh on the second call
    assert not w.current().stale
    assert w.current().stale


class _EmptyOffices:
    def all(self) -> list:
        return []


class _FakeChatService:
    def __init__(self, response: Response) -> None:
        self.offices = _EmptyOffices()
        self._response = response

    def handle(self, msg: object) -> Response:
        return self._response


def _fake_chat_client(settings, repo: Repository, response: Response) -> TestClient:
    cfg = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 5})
    app = create_app(
        cfg,
        _FakeChatService(response),
        weather_with(lambda req: httpx.Response(200, json=OK_JSON)),
        repo=repo,
    )
    return TestClient(app)


def test_chat_response_defaults_for_legacy_and_fee(client: TestClient) -> None:
    legacy_payload = {"answer": "Hello!", "intent": Intent.GREETING, "sources": [], "degraded": False}
    schema_obj = ChatResponse(**legacy_payload, request_id="abc123def456")
    assert schema_obj.escalate is False
    assert schema_obj.path == "deterministic"
    assert schema_obj.confidence is None

    r = client.post("/v1/chat", json={"message": "tuition for 18 credits and 2 retake"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "fee" and "9,450,000" in body["answer"] and body["request_id"]
    assert body["path"] == "deterministic"
    assert body["escalate"] is False
    assert body["confidence"] is None


def test_chat_abstain_response_and_db_metadata(settings, repo: Repository) -> None:
    abstain_resp = Response(
        answer="Please contact the Training Office (room I.101) or ask your academic advisor.",
        intent=Intent.UNKNOWN,
        sources=[],
        degraded=False,
        escalate=True,
        path="abstain",
        confidence=0.0,
    )
    client = _fake_chat_client(settings, repo, abstain_resp)
    r = client.post("/v1/chat", json={"message": "what is the capital of France", "session_id": "raw-student-99"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "unknown"
    assert body["path"] == "abstain"
    assert body["escalate"] is True
    assert body["confidence"] == 0.0
    assert len(body["request_id"]) == 12

    with Session(repo.engine) as db:
        sessions = db.exec(select(ChatSession)).all()
        interactions = db.exec(select(Interaction)).all()
    assert len(sessions) == 1 and "raw-student-99" not in sessions[0].id
    assert len(interactions) == 1
    assert interactions[0].request_id == body["request_id"]
    assert interactions[0].resolved is False
    assert interactions[0].degraded is False


def test_chat_grounded_llm_response_and_feedback_roundtrip(settings, repo: Repository) -> None:
    llm_resp = Response(
        answer="You need at least 120 credits and GPA 2.0 to register a thesis.",
        intent=Intent.RULE,
        sources=[Source(id="H26#5.3", title="5.3 Thesis registration")],
        degraded=False,
        escalate=False,
        path="llm",
        confidence=0.85,
    )
    client = _fake_chat_client(settings, repo, llm_resp)
    r = client.post("/v1/chat", json={"message": "can I register my thesis with 118 credits"})
    assert r.status_code == 200
    body = r.json()
    assert body["path"] == "llm"
    assert body["escalate"] is False
    assert body["confidence"] == 0.85
    assert body["sources"] == [{"id": "H26#5.3", "title": "5.3 Thesis registration"}]

    fb = client.post("/v1/feedback", json={"request_id": body["request_id"], "rating": 1})
    assert fb.status_code == 201 and fb.json()["request_id"] == body["request_id"]


def test_chat_degraded_retrieval_fallback_and_stats(settings, repo: Repository) -> None:
    degraded_resp = Response(
        answer="3 Student card replacement: A lost student card can be replaced at Student Affairs (room I.102).",
        intent=Intent.RULE,
        sources=[Source(id="S26#3", title="3 Student card replacement")],
        degraded=True,
        escalate=False,
        path="retrieval",
        confidence=None,
    )
    client = _fake_chat_client(settings, repo, degraded_resp)
    r = client.post("/v1/chat", json={"message": "I lost my student card"})
    assert r.status_code == 200
    body = r.json()
    assert body["degraded"] is True
    assert body["path"] == "retrieval"
    assert body["escalate"] is False
    assert body["confidence"] is None
    assert body["sources"] == [{"id": "S26#3", "title": "3 Student card replacement"}]

    stats = client.get("/v1/stats/intents", headers={"X-API-Key": "secret-admin"})
    assert stats.status_code == 200
    rows = stats.json()
    assert len(rows) == 1
    assert rows[0]["intent"] == "rule" and rows[0]["requests"] == 1 and rows[0]["unresolved"] == 0
