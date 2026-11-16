"""HTTP client for the assistant backend.

Talks to the FastAPI service; never imports assistant_core directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass
class ChatResult:
    """Parsed response from POST /ask."""

    ok: bool
    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    request_id: str = ""
    escalate: bool = False
    degraded: bool = False
    error: str = ""


class AssistantClient:
    """Thin wrapper around the assistant HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    def healthy(self) -> bool:
        """Return True if the backend is reachable."""
        try:
            r = httpx.get(f"{self._base}/health", timeout=3.0)
            return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    def ask(self, question: str, session_id: str = "") -> ChatResult:
        """Send a question to the backend and return a ChatResult."""
        try:
            r = httpx.post(
                f"{self._base}/ask",
                json={"question": question, "session_id": session_id},
                timeout=self._timeout,
            )
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
        except httpx.ConnectError:
            return ChatResult(ok=False, error="Cannot connect to the assistant backend.")
        except (httpx.HTTPError, OSError, ValueError) as exc:
            return ChatResult(ok=False, error=str(exc))

    def send_feedback(self, request_id: str, rating: int) -> bool:
        """Send thumbs-up/down feedback. Returns True on success."""
        try:
            r = httpx.post(
                f"{self._base}/feedback",
                json={"request_id": request_id, "rating": rating},
                timeout=5.0,
            )
            return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False
