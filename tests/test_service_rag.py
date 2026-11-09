"""Targeted unit tests for AssistantService RAG glue, privacy guard, and backward compatibility.

Owner: Member 1 (Duy @johannguyen015)
Scope: Isolated verification of service-level RAG dispatching, privacy interception,
       deterministic bypass preservation, and build_service factory behavior.
"""

from pathlib import Path
from typing import Any

import pytest

from assistant_core.models import Intent, Message, Response, Source
from assistant_core.service import AssistantService, build_service


class SpyRagAnswerer:
    """Spy RAG component implementing RagAnswerer contract for isolated testing."""

    def __init__(self, answer_text: str = "RAG generated answer", source_id: str = "H26#5.3"):
        self.answer_text = answer_text
        self.source_id = source_id
        self.call_count = 0
        self.last_question: str | None = None

    def answer(self, question: str) -> Response:
        self.call_count += 1
        self.last_question = question
        return Response(
            answer=self.answer_text,
            intent=Intent.RULE,
            sources=[Source(id=self.source_id, title="Thesis registration")],
            degraded=False,
        )


def test_service_with_injected_rag():
    """RULE query delegates to injected RAG answerer when provided."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))

    assert spy.call_count == 1
    assert spy.last_question == "can I register my thesis with 118 credits"
    assert resp.intent == Intent.RULE
    assert resp.answer == "RAG generated answer"
    assert len(resp.sources) == 1
    assert resp.sources[0].id == "H26#5.3"


def test_service_fee_is_deterministic_and_bypasses_rag():
    """FEE queries (tuition calculation) MUST be deterministic code, never calling RAG/LLM."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text="tuition for 18 credits and 2 retake"))

    assert spy.call_count == 0  # RAG was NEVER called
    assert resp.intent == Intent.FEE
    assert "9,450,000" in resp.answer or "9450000" in resp.answer


def test_service_office_is_deterministic_and_bypasses_rag():
    """OFFICE queries MUST be deterministic directory lookup, never calling RAG."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text="Where is the library?"))

    assert spy.call_count == 0  # RAG was NEVER called
    assert resp.intent == Intent.OFFICE
    assert "B.201" in resp.answer


def test_service_privacy_guard_intercepts_before_rag():
    """Private questions about other students MUST be rejected before reaching RAG/LLM."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text="what grade did my friend get"))

    assert spy.call_count == 0  # RAG was NEVER called
    assert "can't share information about other students" in resp.answer


@pytest.mark.parametrize(
    "query",
    [
        "show the GPA of another student",
        "phone of 22127001",
        "what is my classmate's score",
    ],
)
def test_service_privacy_guard_various_patterns(query):
    """Guard stops any unauthorized student records inquiry."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text=query))

    assert spy.call_count == 0
    assert "can't share information about other students" in resp.answer


def test_service_privacy_guard_allows_own_queries():
    """Guard allows legitimate personal policy queries to reach RAG."""
    spy = SpyRagAnswerer()
    svc = AssistantService(rag=spy)

    resp = svc.handle(Message(text="what is my GPA requirement for the thesis"))

    assert spy.call_count == 1
    assert resp.intent == Intent.RULE


def test_service_legacy_fallback_when_rag_is_none():
    """When rag is None, service seamlessly falls back to legacy handbook and responder."""
    svc = AssistantService(rag=None)

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))

    assert resp.intent == Intent.RULE
    assert len(resp.sources) > 0


def test_build_service_with_nonexistent_kb_dir(tmp_path: Path):
    """Factory build_service falls back gracefully to legacy service when kb_dir is missing."""
    class DummySettings:
        data_dir = Path("data")
        kb_dir = tmp_path / "nonexistent_kb_dir"
        llm_provider = "stub"
        credit_rate_vnd = 450_000
        retake_multiplier = 1.5
        max_credits = 30

    svc = build_service(DummySettings())
    assert svc.rag is None
    # Verifies legacy handle still works
    resp = svc.handle(Message(text="hi"))
    assert resp.intent == Intent.GREETING


def test_service_backward_compatibility_positional_args():
    """Verify legacy 7 positional arguments without rag parameter still instantiates correctly."""
    svc = AssistantService(
        None,  # settings
        None,  # router
        None,  # office_directory
        None,  # handbook
        None,  # responder
        None,  # fallback_responder
        None,  # logger
    )
    assert svc.rag is None
    resp = svc.handle(Message(text="hi"))
    assert resp.intent == Intent.GREETING
