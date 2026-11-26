"""Lab 8 Part E: turn YOUR Week-7 failures into regression tests.

Write at least three tests. Each one must:
  - have a name that says what went wrong, e.g. test_empty_sources_does_not_crash_ui
  - FAIL on the old code (check by temporarily undoing your fix), and PASS after the fix.
Use the fixtures `service`, `settings` from conftest.py, or build a TestClient like tests/test_security.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from assistant_core.models import Intent, Message
from assistant_core.rag.chunker import Chunk
from assistant_core.rag.index import Hit
from assistant_core.service import build_service


def test_example_greeting_still_works(service):
    """Example: a control case that must never break."""
    assert "Hello" in service.handle(Message(text="hi")).answer


def test_retake_number_as_word(service):
    """BUG-7: 'two retakes' was ignored when retake count was written as a word, giving wrong total."""
    r = service.handle(Message(text="tuition for 18 credits and two retakes"))
    assert "8,100,000" not in r.answer  # never the wrong total (8,100,000 VND ignores the retakes)
    assert "9,450,000" in r.answer  # 18*450_000 + 2*450_000*1.5 = 9,450,000 VND


class _SingleHitIndex:
    def __init__(self, chunk: Chunk, score: float = 4.5) -> None:
        self._hit = Hit(chunk=chunk, score=score)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return [self._hit][:k]


class _FakeCitationLLM:
    """Stub LLM that returns valid source_ids JSON but injects an unretrieved inline citation."""

    name = "fake-hallucinating-citation"

    def __init__(self, payloads: list[str]) -> None:
        self._payloads = list(payloads)
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self._payloads.pop(0)


def test_citation_of_unretrieved_source_is_rejected(settings):
    """BUG-3: fabricated inline [doc#section] citations & duplicate source_ids must be rejected/normalized."""
    kb_dir = Path(__file__).resolve().parents[1] / "data" / "kb"
    cfg = settings.model_copy(update={"kb_dir": kb_dir, "llm_provider": "stub"})
    rag_service = build_service(cfg)
    assert rag_service.rag is not None

    # Inject a chunk whose only retrieved ID is H26#5.3, while LLM claims [H26#9.9] in prose.
    retrieved_chunk = Chunk(
        id="H26#5.3",
        doc_id="H26",
        title="5.3 Thesis registration",
        text="Students may register a thesis when they have at least 120 accumulated credits.",
        version="2026.1",
        owner="Training Office",
    )
    rag_service.rag.index = _SingleHitIndex(retrieved_chunk)
    hallucinated = json.dumps(
        {
            "answer": "According to [H26#9.9], students only need 90 credits to register a thesis.",
            "source_ids": ["H26#5.3", "H26#5.3"],
            "confidence": 0.9,
            "abstain": False,
        }
    )
    rag_service.rag.llm = _FakeCitationLLM([hallucinated, hallucinated])

    r = rag_service.handle(Message(text="Can I register my thesis with 118 credits?"))
    assert "[H26#9.9]" not in r.answer
    assert r.intent == Intent.RULE
    assert r.path == "retrieval"
    assert r.degraded is True
    assert [s.id for s in r.sources] == ["H26#5.3"]

    # Control: grounded StubLLM reply still succeeds normally without degrading.
    clean_service = build_service(cfg)
    ctrl = clean_service.handle(Message(text="Can I register my thesis with 118 credits?"))
    assert ctrl.path == "llm"
    assert ctrl.degraded is False
    assert [s.id for s in ctrl.sources] == ["H26#5.3"]


def test_duplicate_source_ids_are_deduplicated_in_rag_response(settings):
    """BUG-3: repeated source_ids in grounded LLM JSON must not produce duplicate Source objects."""
    kb_dir = Path(__file__).resolve().parents[1] / "data" / "kb"
    cfg = settings.model_copy(update={"kb_dir": kb_dir, "llm_provider": "stub"})
    rag_service = build_service(cfg)
    assert rag_service.rag is not None

    dup_payload = json.dumps(
        {
            "answer": "You need at least 120 accumulated credits.",
            "source_ids": ["H26#5.3", "H26#5.3"],
            "confidence": 0.8,
            "abstain": False,
        }
    )
    rag_service.rag.llm = _FakeCitationLLM([dup_payload])
    r = rag_service.handle(Message(text="Can I register my thesis with 118 credits?"))
    assert r.path == "llm"
    assert r.degraded is False
    assert [s.id for s in r.sources] == ["H26#5.3"]
