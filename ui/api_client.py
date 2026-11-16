"""HTTP client for the assistant backend.

Talks to the FastAPI service at /v1/chat and /v1/feedback;
never imports assistant_core directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class ChatResult:
    """Parsed response from POST /v1/chat."""

    ok: bool
    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    request_id: str = ""
    escalate: bool = False
    degraded: bool = False
    error: str = ""


class AssistantClient:
    """Thin wrapper around the assistant HTTP API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self._base, timeout=self._timeout, transport=self._transport)

    def healthy(self) -> bool:
        """Return True if the backend is reachable."""
        try:
            with self._client() as c:
                r = c.get("/health")
            return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    def ask(self, question: str, session_id: str = "") -> ChatResult:
        """Send a question to POST /v1/chat and return a ChatResult."""
        try:
            with self._client() as c:
                r = c.post(
                    "/v1/chat",
                    json={"message": question, "session_id": session_id or "anonymous"},
                )
            if r.status_code == 422:
                detail = r.json().get("error", {}).get("message", "Invalid request.")
                return ChatResult(ok=False, error=f"Invalid request: {detail}")
            if r.status_code == 429:
                return ChatResult(ok=False, error="Too many requests — please wait a moment before retrying.")
            if r.status_code != 200:
                return ChatResult(ok=False, error=f"Server error {r.status_code}: {r.text[:200]}")
            data = r.json()
            return ChatResult(
                ok=True,
                answer=data.get("answer", ""),
                sources=data.get("sources", []),
                request_id=data.get("request_id", ""),
                escalate=data.get("escalate", False),
                degraded=data.get("degraded", False),
            )
        except httpx.TimeoutException:
            return ChatResult(ok=False, error="The request timed out — the server may be busy.")
        except httpx.ConnectError:
            return ChatResult(ok=False, error="Cannot connect to the assistant backend.")
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return ChatResult(ok=False, error=str(exc))

    def send_feedback(self, request_id: str, rating: int) -> bool:
        """Send thumbs-up/down feedback to POST /v1/feedback. Returns True on 201."""
        try:
            with self._client() as c:
                r = c.post(
                    "/v1/feedback",
                    json={"request_id": request_id, "rating": rating},
                )
            return r.status_code == 201
        except (httpx.HTTPError, OSError):
            return False
