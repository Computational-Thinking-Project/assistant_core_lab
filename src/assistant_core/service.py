"""AssistantService entry point and dependency coordinator.

Phụ trách: Thành viên 1 (Duy @johannguyen015)
Phạm vi: AssistantService, handle(msg: Message) -> Response
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Imports with fallback to agreed contracts (for isolated/independent testing)
# ---------------------------------------------------------------------------

try:
    from assistant_core.models import Intent, Message, Response, Source
except (ImportError, AttributeError):

    class Intent(str, Enum):
        GREETING = "greeting"
        FEE = "fee"
        OFFICE = "office"
        RULE = "rule"
        UNKNOWN = "unknown"

    class Source(BaseModel):
        id: str
        title: str

    class Message(BaseModel):
        text: str = Field(min_length=1, max_length=2000)
        session_id: str = "local"

    class Response(BaseModel):
        answer: str
        intent: Intent
        sources: list[Source] = Field(default_factory=list)
        degraded: bool = False


try:
    from assistant_core.errors import AssistantError, ProviderError
except (ImportError, AttributeError):

    class AssistantError(Exception):
        """Base exception for assistant_core."""

    class ProviderError(AssistantError):
        """External provider error."""


# Responder protocol
class Responder(Protocol):
    def explain(self, question: str, rule: Any) -> str:
        """Generate explanation using rule context."""
        ...


class _DefaultTemplateResponder:
    """Fallback responder producing deterministic rule answers without LLM."""

    def explain(self, question: str, rule: Any) -> str:
        rule_text = rule.text if hasattr(rule, "text") else rule.get("text", "")
        rule_id = rule.id if hasattr(rule, "id") else rule.get("id", "")
        return f"{rule_text} (source: {rule_id})"


class _DefaultStubLLMResponder:
    """Stub LLM responder for deterministic simulation."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def explain(self, question: str, rule: Any) -> str:
        if self.should_fail:
            raise ProviderError("LLM provider unavailable")
        rule_text = rule.text if hasattr(rule, "text") else rule.get("text", "")
        rule_id = rule.id if hasattr(rule, "id") else rule.get("id", "")
        return f"Here is what I found: {rule_text} Question: {question} (source: {rule_id})"


# Default deterministic tools fallback
def _default_parse_credits(text: str) -> tuple[int, int]:
    words = text.lower().replace("?", " ").split()
    credits_val = 0
    retake_val = 0
    for i, word in enumerate(words):
        if word.isdigit():
            if i + 1 < len(words) and words[i + 1].startswith("retake"):
                retake_val = int(word)
            elif credits_val == 0:
                credits_val = int(word)
    return credits_val, retake_val


def _default_tuition(
    credits_val: int,
    retake_val: int = 0,
    rate: int = 450_000,
    retake_multiplier: float = 1.5,
    max_credits: int = 30,
) -> int:
    if credits_val > max_credits:
        raise ValueError("too many credits")
    total = credits_val * rate + retake_val * rate * retake_multiplier
    return int(total)


# Default router fallback
def _default_route(text: str, office_names: set[str]) -> Intent:
    m = text.lower().strip()
    if m in ["hi", "hello", "hey", "xin chao"]:
        return Intent.GREETING
    if "fee" in m or "tuition" in m:
        return Intent.FEE
    if any(k.lower() in m for k in office_names):
        return Intent.OFFICE
    if any(w in m for w in ["thesis", "retake", "exam", "credit", "course", "load"]):
        return Intent.RULE
    return Intent.UNKNOWN


# ---------------------------------------------------------------------------
# AssistantService implementation
# ---------------------------------------------------------------------------


class AssistantService:
    """Core domain service orchestrating routing, tools, knowledge, and responders."""

    def __init__(
        self,
        settings: Any | None = None,
        router: Callable[[str, set[str]], Intent] | None = None,
        office_directory: Any | None = None,
        handbook: Any | None = None,
        responder: Responder | None = None,
        fallback_responder: Responder | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.settings = settings
        self.router = router or self._resolve_router()
        self.office_directory = office_directory or self._resolve_office_directory()
        self.handbook = handbook or self._resolve_handbook()
        self.responder = responder or self._resolve_responder()
        self.fallback_responder = fallback_responder or _DefaultTemplateResponder()
        self.logger = logger or logging.getLogger("assistant_core.service")

        # Configurable tuition parameters
        self.rate = getattr(settings, "credit_rate_vnd", 450_000) if settings else 450_000
        self.retake_multiplier = getattr(settings, "retake_multiplier", 1.5) if settings else 1.5
        self.max_credits = getattr(settings, "max_credits", 30) if settings else 30

    def _resolve_router(self) -> Callable[[str, set[str]], Intent]:
        try:
            from assistant_core.router import route

            if callable(route):
                return route
        except (ImportError, AttributeError):
            pass
        return _default_route

    def _resolve_office_directory(self) -> Any:
        try:
            from assistant_core.knowledge import OfficeDirectory

            data_dir = getattr(self.settings, "data_dir", Path("data")) if self.settings else Path("data")
            csv_path = Path(data_dir) / "offices.csv"
            if csv_path.exists():
                return OfficeDirectory.load(csv_path)
        except (ImportError, AttributeError, OSError, ValueError):
            pass
        return None

    def _resolve_handbook(self) -> Any:
        try:
            from assistant_core.knowledge import Handbook

            data_dir = getattr(self.settings, "data_dir", Path("data")) if self.settings else Path("data")
            json_path = Path(data_dir) / "handbook.json"
            if json_path.exists():
                return Handbook.load(json_path)
        except (ImportError, AttributeError, OSError, ValueError):
            pass
        return None

    def _resolve_responder(self) -> Responder:
        try:
            from assistant_core.responder import StubLLMResponder

            return StubLLMResponder()
        except (ImportError, AttributeError):
            return _DefaultStubLLMResponder()

    def get_office_names(self) -> set[str]:
        """Return office names registered in directory."""
        if self.office_directory and hasattr(self.office_directory, "get_names"):
            return self.office_directory.get_names()
        if self.office_directory and hasattr(self.office_directory, "offices"):
            return set(self.office_directory.offices.keys())
        # Default offices from data/offices.csv
        return {"training office", "student affairs", "library", "it helpdesk"}

    def handle(self, msg: Message | str) -> Response:
        """Primary public service entry point."""
        start_time = time.perf_counter()

        # Boundary validation / conversion
        if isinstance(msg, str):
            clean_text = msg.strip()
            if not clean_text:
                return Response(answer="empty", intent=Intent.UNKNOWN)
            msg = Message(text=clean_text)

        text = msg.text.strip()
        if not text:
            return Response(answer="empty", intent=Intent.UNKNOWN)

        intent = self.router(text, self.get_office_names())
        response = self._dispatch(intent, text, msg)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.logger.info(
            "Request handled",
            extra={
                "intent": response.intent.value,
                "latency_ms": latency_ms,
                "session": msg.session_id,
                "degraded": response.degraded,
            },
        )
        return response

    def _dispatch(self, intent: Intent, text: str, msg: Message) -> Response:
        if intent == Intent.GREETING:
            return Response(
                answer="Hello! I can help with offices, fees and rules.",
                intent=Intent.GREETING,
            )

        if intent == Intent.FEE:
            return self._handle_fee(text)

        if intent == Intent.OFFICE:
            return self._handle_office(text)

        if intent == Intent.RULE:
            return self._handle_rule(text)

        return Response(answer="Sorry I dont know", intent=Intent.UNKNOWN)

    def _handle_fee(self, text: str) -> Response:
        try:
            from assistant_core.tools import parse_credits, tuition
        except (ImportError, AttributeError):
            parse_credits = _default_parse_credits
            tuition = _default_tuition

        credits_val, retake_val = parse_credits(text)
        if credits_val == 0:
            return Response(answer="How many credits?", intent=Intent.FEE)

        if credits_val > self.max_credits:
            return Response(answer="too many credits", intent=Intent.FEE)

        try:
            total = tuition(
                credits_val,
                retake_val,
                rate=self.rate,
                retake_multiplier=self.retake_multiplier,
                max_credits=self.max_credits,
            )
            return Response(answer=f"Your tuition is {total} VND", intent=Intent.FEE)
        except ValueError:
            return Response(answer="too many credits", intent=Intent.FEE)

    def _handle_office(self, text: str) -> Response:
        lower_text = text.lower()
        if self.office_directory and hasattr(self.office_directory, "find"):
            office = self.office_directory.find(text)
            if office:
                name = getattr(office, "name", "")
                room = getattr(office, "room", "")
                hours = getattr(office, "hours", "")
                return Response(
                    answer=f"{name}: room {room}, open {hours}",
                    intent=Intent.OFFICE,
                    sources=[Source(id=f"office-{name.lower()}", title=name)],
                )

        # Fallback dictionary matching data/offices.csv
        offices = {
            "training office": ("Training Office", "I.101", "Mon-Fri 07:30-16:30"),
            "student affairs": ("Student Affairs", "I.102", "Mon-Fri 08:00-16:00"),
            "library": ("Library", "B.201", "Mon-Sat 07:00-20:00"),
            "it helpdesk": ("IT Helpdesk", "E.005", "Mon-Fri 08:00-17:00"),
        }
        for key, (name, room, hours) in offices.items():
            if key in lower_text:
                return Response(
                    answer=f"{name}: room {room}, open {hours}",
                    intent=Intent.OFFICE,
                    sources=[Source(id=f"office-{key}", title=name)],
                )

        return Response(answer="Sorry I dont know", intent=Intent.UNKNOWN)

    def _handle_rule(self, text: str) -> Response:
        rule = None
        if self.handbook and hasattr(self.handbook, "search"):
            rule = self.handbook.search(text)
        elif self.handbook and hasattr(self.handbook, "find_rule"):
            rule = self.handbook.find_rule(text)
        else:
            rule = self._fallback_handbook_search(text)

        if not rule:
            return Response(answer="Sorry I dont know", intent=Intent.UNKNOWN)

        rule_id = rule.id if hasattr(rule, "id") else rule.get("id", "rule")
        rule_title = rule.title if hasattr(rule, "title") else rule.get("title", rule_id)
        source = Source(id=rule_id, title=rule_title)

        try:
            answer = self.responder.explain(text, rule)
            return Response(
                answer=answer,
                intent=Intent.RULE,
                sources=[source],
                degraded=False,
            )
        except ProviderError as exc:
            self.logger.warning("Provider error caught (%s), using fallback responder", exc)
            fallback_answer = self.fallback_responder.explain(text, rule)
            return Response(
                answer=fallback_answer,
                intent=Intent.RULE,
                sources=[source],
                degraded=True,
            )

    def _fallback_handbook_search(self, text: str) -> dict[str, str] | None:
        rules = [
            {
                "id": "H26-4.2",
                "title": "Retaking a course",
                "text": (
                    "Students may retake a course they failed. Retake credits are charged at 1.5 times the "
                    "normal rate. Final-year students must register retakes before week 2."
                ),
            },
            {
                "id": "H26-5.3",
                "title": "Thesis registration",
                "text": (
                    "Students may register a thesis when they have at least 120 accumulated credits and a "
                    "GPA of at least 2.0."
                ),
            },
            {
                "id": "H26-5.4",
                "title": "Late thesis registration",
                "text": "Late thesis registration requires approval from the Faculty and the supervisor.",
            },
            {
                "id": "H26-6.1",
                "title": "Credit load",
                "text": (
                    "A regular semester load is between 14 and 30 credits. More than 30 credits requires approval."
                ),
            },
            {
                "id": "H26-7.2",
                "title": "Exam absence",
                "text": (
                    "Students absent from a final exam for medical reasons must submit evidence to the "
                    "Training Office within 3 working days."
                ),
            },
        ]
        best = None
        best_score = 0
        words = text.lower().split()
        for r in rules:
            score = sum(1 for w in words if len(w) > 3 and w in r["text"].lower())
            if score > best_score:
                best_score = score
                best = r
        if best and best_score >= 1:
            return best
        return None
