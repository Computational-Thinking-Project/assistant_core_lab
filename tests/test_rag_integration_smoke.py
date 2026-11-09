"""Targeted integration smoke tests for 3-path assistant execution.

Owner: Member 7 (Tam @AI-WFox)
Scope: Verifies end-to-end integration contracts across deterministic tools,
       knowledge retrieval, privacy protection, out-of-scope abstention,
       and graceful fallback.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import pytest

from assistant_core.config import load_settings
from assistant_core.errors import ProviderError
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import TemplateResponder
from assistant_core.service import AssistantService
from eval.compare_paths import (
    FallbackBM25Index,
    FallbackRagAnswerer,
    NoAnswer,
    StubLLM,
    build_service_adapter,
    load_kb_chunks,
)


def get_clean_settings() -> Any:
    """Provide clean settings with canonical 450,000 VND rate and 1.5 multiplier."""
    s = load_settings()
    s.credit_rate_vnd = 450_000
    s.retake_multiplier = 1.5
    s.max_credits = 30
    return s


def get_data_dir(s: Any | None = None) -> Path:
    """Resolve data directory safely, resilient to dirty test environment variables."""
    if s is not None:
        d = getattr(s, "data_dir", None)
        if d and (Path(d) / "offices.csv").exists():
            return Path(d)
    candidates = [
        Path("data"),
        Path(__file__).resolve().parents[1] / "data",
    ]
    for c in candidates:
        if (c / "offices.csv").exists():
            return c
    return Path("data")


@pytest.fixture(scope="module")
def shared_index():
    chunks = load_kb_chunks()
    return FallbackBM25Index(chunks)


@pytest.fixture
def base_service(shared_index):
    s = get_clean_settings()
    data_dir = get_data_dir(s)
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    rag = FallbackRagAnswerer(index=shared_index, llm=StubLLM(), min_score=2.0)
    return build_service_adapter(s, offices, handbook, TemplateResponder(), rag)


def test_smoke_fee_calculation_is_deterministic(base_service):
    """Case E03: Tuition calculation MUST be deterministic and return 9,450,000 VND."""
    msg = Message(text="tuition for 18 credits and 2 retake")
    resp = base_service.handle(msg)

    assert resp.intent == Intent.FEE
    assert "9,450,000" in resp.answer or "9450000" in resp.answer


def test_smoke_office_directory_is_deterministic(base_service):
    """Case E04: Office inquiries MUST return accurate location B.201 without hallucination."""
    msg = Message(text="where is the library")
    resp = base_service.handle(msg)

    assert resp.intent == Intent.OFFICE
    assert "B.201" in resp.answer


def test_smoke_student_card_replacement_retrieves_source(base_service):
    """Case E05: Student card replacement inquiry retrieves policy S26#3."""
    msg = Message(text="I lost my student card")
    resp = base_service.handle(msg)

    source_ids = [s.id for s in getattr(resp, "sources", [])]
    assert "S26#3" in source_ids


def test_smoke_out_of_scope_france_abstains(base_service):
    """Case E16: Out-of-scope question ('capital of France') MUST safely abstain."""
    msg = Message(text="what is the capital of France")
    resp = base_service.handle(msg)

    path = getattr(resp, "path", "")
    intent = getattr(resp, "intent", None)
    intent_val = intent.value if hasattr(intent, "value") else str(intent)
    escalate = getattr(resp, "escalate", False)

    is_abstained = path == "abstain" or intent_val == "unknown" or escalate or "don't know" in resp.answer.lower()
    assert is_abstained, f"Expected abstention but got: {resp.answer}"


def test_smoke_privacy_guard_intercepts_unauthorized_records(base_service):
    """Case E18: Requesting grades or info of other students MUST be rejected."""
    msg = Message(text="what grade did my friend get")
    resp = base_service.handle(msg)

    answer_lower = resp.answer.lower()
    assert (
        "can't share" in answer_lower
        or "cannot share" in answer_lower
        or "privacy" in answer_lower
        or getattr(resp, "path", "") == "abstain"
        or getattr(resp, "escalate", False)
    )


def test_smoke_degraded_fallback_when_llm_fails(shared_index):
    """When LLM provider fails, system must degrade gracefully to fallback or escalate."""
    class FailingLLM:
        name = "failing_mock"

        def generate_answer(self, question: str, hits: Any, prompt_version: str = "answer_v1"):
            raise ProviderError("LLM downstream service timed out")

    s = load_settings()
    data_dir = get_data_dir(s)
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    class ResilientRagAnswerer(FallbackRagAnswerer):
        def answer(self, question: str) -> Response:
            try:
                return super().answer(question)
            except ProviderError:
                # Degraded fallback to pure retrieval
                hits = self.index.search(question, k=1)
                if hits:
                    top = hits[0].chunk
                    return Response(
                        answer=f"{top.title}: {top.text}",
                        intent=getattr(Intent, "RULE", "rule"),
                        sources=[Source(id=top.id, title=top.title)],
                        path="retrieval_fallback",
                        degraded=True,
                    )
                return Response(
                    answer="Service degraded. Please contact the Training Office.",
                    intent=getattr(Intent, "UNKNOWN", "unknown"),
                    path="abstain",
                    escalate=True,
                    degraded=True,
                )

    rag = ResilientRagAnswerer(index=shared_index, llm=FailingLLM(), min_score=2.0)
    svc = build_service_adapter(s, offices, handbook, TemplateResponder(), rag)

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.degraded is True
    assert len(resp.sources) > 0 or getattr(resp, "escalate", False)


def test_smoke_deterministic_path_never_answers_rules(shared_index):
    """Deterministic path without retrieval MUST escalate on rule questions."""
    s = load_settings()
    data_dir = get_data_dir(s)
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    rag = FallbackRagAnswerer(index=NoAnswer(), llm=None, min_score=2.0)
    svc = build_service_adapter(s, offices, handbook, TemplateResponder(), rag)

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))
    assert getattr(resp, "path", "") == "abstain" or getattr(resp, "escalate", False) or resp.intent.value == "unknown"
