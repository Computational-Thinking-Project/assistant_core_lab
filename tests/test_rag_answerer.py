"""Targeted unit tests for Response contract, router characterization, and RagAnswerer (TV3 - Đạt).

Tests verify:
1. Response model backward compatibility with defaults (`escalate=False`, `path="deterministic"`, `confidence=None`).
2. A1: Pre-retrieval abstain (zero LLM calls when score < min_score or no hits).
3. Retrieval-only baseline (`llm=None`).
4. LLM grounded success (`path="llm"`, source mapping) and model-initiated abstain (`abstain=True`).
5. ProviderError / invalid JSON retry policy (`retries=1` -> 2 attempts) and degraded retrieval fallback.
6. FakeToolRunner execution and `InvalidRequest` degraded handling.
7. Router characterization for tuition calculation (`Intent.FEE`) and known failures E13/E15.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from assistant_core import llm as prod_llm
from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Response
from assistant_core.rag import answerer as answerer_module
from assistant_core.rag.answerer import ESCALATE_MSG, RagAnswerer
from assistant_core.rag.chunker import Chunk
from assistant_core.rag.index import Hit, Index
from assistant_core.router import route


@dataclass(frozen=True)
class DummyChunk:
    id: str
    title: str
    text: str


@dataclass(frozen=True)
class DummyHit:
    chunk: DummyChunk
    score: float


class FakeIndex:
    def __init__(self, hits: list[DummyHit] | None = None):
        self.hits = hits if hits is not None else []
        self.search_queries: list[str] = []

    def search(self, query: str, k: int = 3) -> list[DummyHit]:
        self.search_queries.append(query)
        return self.hits[:k]


class SpyLLM:
    name = "spy"

    def __init__(self, return_values: list[str] | None = None, raise_error: bool = False):
        self.return_values = list(return_values) if return_values else []
        self.raise_error = raise_error
        self.call_count = 0
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.call_count += 1
        self.prompts.append(prompt)
        if self.raise_error:
            raise ProviderError("simulated provider failure")
        if self.return_values:
            return self.return_values.pop(0)
        return json.dumps({
            "answer": "Students need at least 120 credits and GPA >= 2.0 to register the thesis.",
            "source_ids": ["H26#5.3"],
            "confidence": 0.85,
            "abstain": False,
        })


class FakeToolRunner:
    def __init__(self, result: str | None = None, error_msg: str | None = None):
        self.result = result
        self.error_msg = error_msg
        self.calls: list[str] = []

    def __call__(self, raw: str) -> str | None:
        self.calls.append(raw)
        if self.error_msg is not None:
            raise InvalidRequest(self.error_msg)
        if "calc_fee" in raw:
            return self.result
        return None


def test_response_model_backward_compatibility():
    """Existing code creating Response without new fields must work seamlessly with defaults."""
    resp = Response(answer="Tuition is 9,450,000 VND", intent=Intent.FEE)
    assert resp.answer == "Tuition is 9,450,000 VND"
    assert resp.intent == Intent.FEE
    assert resp.sources == []
    assert resp.degraded is False
    assert resp.escalate is False
    assert resp.path == "deterministic"
    assert resp.confidence is None


def test_rag_answerer_a1_abstain_no_hits():
    """When retrieval finds zero hits, abstain before calling the LLM (zero LLM calls)."""
    fake_index = FakeIndex(hits=[])
    spy_llm = SpyLLM()
    answerer = RagAnswerer(fake_index, spy_llm, min_score=2.0)

    res = answerer.answer("what is the capital of France")

    assert res.path == "abstain"
    assert res.escalate is True
    assert res.confidence == 0.0
    assert res.intent == Intent.UNKNOWN
    assert res.answer == ESCALATE_MSG
    assert spy_llm.call_count == 0  # CRITICAL: LLM was never called!


def test_rag_answerer_a1_abstain_low_score():
    """When best retrieval score is below min_score (e.g. 1.2 < 2.0), abstain before calling LLM."""
    low_hit = DummyHit(chunk=DummyChunk(id="H26#1.1", title="General", text="Info"), score=1.2)
    fake_index = FakeIndex(hits=[low_hit])
    spy_llm = SpyLLM()
    answerer = RagAnswerer(fake_index, spy_llm, min_score=2.0)

    res = answerer.answer("unrelated query with weak overlap")

    assert res.path == "abstain"
    assert res.escalate is True
    assert res.confidence == 0.0
    assert spy_llm.call_count == 0  # CRITICAL: LLM was never called!


def test_rag_answerer_retrieval_baseline():
    """When llm is None, answerer acts as retrieval baseline quoting the top source."""
    hit = DummyHit(chunk=DummyChunk(id="S26#3", title="Card replacement", text="Replace in I.102."), score=4.5)
    fake_index = FakeIndex(hits=[hit])
    answerer = RagAnswerer(fake_index, llm=None, min_score=2.0)

    res = answerer.answer("I lost my student card")

    assert res.path == "retrieval"
    assert res.intent == Intent.RULE
    assert "Card replacement: Replace in I.102." in res.answer
    assert len(res.sources) == 1
    assert res.sources[0].id == "S26#3"
    assert res.degraded is False


def test_rag_answerer_llm_grounded_success():
    """When LLM returns valid grounded JSON, return path='llm' with mapped Source objects."""
    hit = DummyHit(chunk=DummyChunk(id="H26#5.3", title="Thesis registration", text="Min 120 credits."), score=5.0)
    fake_index = FakeIndex(hits=[hit])
    spy_llm = SpyLLM()
    answerer = RagAnswerer(fake_index, spy_llm, min_score=2.0)

    res = answerer.answer("can I register my thesis with 118 credits")

    assert spy_llm.call_count == 1
    assert res.path == "llm"
    assert res.intent == Intent.RULE
    assert res.degraded is False
    assert res.escalate is False
    assert res.confidence == 0.85
    assert [s.id for s in res.sources] == ["H26#5.3"]


def test_rag_answerer_llm_provider_failure_fallback():
    """When LLM provider fails on all retries, fall back to degraded retrieval."""
    hit = DummyHit(chunk=DummyChunk(id="H26#5.3", title="Thesis registration", text="Min 120 credits."), score=5.0)
    fake_index = FakeIndex(hits=[hit])
    failing_llm = SpyLLM(raise_error=True)
    answerer = RagAnswerer(fake_index, failing_llm, min_score=2.0, retries=1)

    res = answerer.answer("can I register my thesis with 118 credits")

    # Called initial attempt + 1 retry = 2 attempts
    assert failing_llm.call_count == 2
    assert res.path == "retrieval"
    assert res.degraded is True
    assert "Thesis registration: Min 120 credits." in res.answer
    assert res.sources[0].id == "H26#5.3"


def test_rag_answerer_tool_runner():
    """When FakeToolRunner is configured and model requests fee calculation."""
    hit = DummyHit(chunk=DummyChunk(id="F26#2", title="Retake fee", text="1.5x regular rate"), score=3.0)
    fake_index = FakeIndex(hits=[hit])
    llm = SpyLLM(return_values=['{"tool": "calc_fee", "args": {"credits": 10}}'])
    tool_runner = FakeToolRunner(result="Total fee is 4,500,000 VND")

    answerer = RagAnswerer(fake_index, llm, min_score=2.0, tool_runner=tool_runner)
    res = answerer.answer("how much does a retake cost")

    assert len(tool_runner.calls) == 1
    assert res.path == "tool"
    assert res.intent == Intent.FEE
    assert "4,500,000" in res.answer


def test_rag_answerer_tool_runner_invalid_request():
    """When FakeToolRunner raises InvalidRequest, return degraded tool response."""
    hit = DummyHit(chunk=DummyChunk(id="F26#2", title="Retake fee", text="1.5x regular rate"), score=3.0)
    fake_index = FakeIndex(hits=[hit])
    llm = SpyLLM(return_values=['{"tool": "calc_fee", "args": {"credits": 999}}'])
    tool_runner = FakeToolRunner(error_msg="credits exceed maximum limit of 30")

    answerer = RagAnswerer(fake_index, llm, min_score=2.0, tool_runner=tool_runner)
    res = answerer.answer("can I take 999 credits")

    assert len(tool_runner.calls) == 1
    assert res.path == "tool"
    assert res.intent == Intent.FEE
    assert res.degraded is True
    assert "credits exceed maximum limit" in res.answer


def test_router_fee_calculation_query():
    """Deterministic tuition calculation query ('tuition for 18 credits ...') routes to Intent.FEE."""
    offices = {"Training Office", "Library", "Finance Office"}
    assert route("tuition for 18 credits and 2 retake", offices) == Intent.FEE


def test_router_known_failure_e13_and_e15_characterization():
    """Characterize known keyword-routing behaviour for E13 ('tuition due') and E15 ('library book')."""
    offices = {"Training Office", "Library", "Finance Office"}
    # E13 contains 'tuition', so simple keyword router classifies it as Intent.FEE (known failure E13)
    assert route("when is tuition due", offices) == Intent.FEE
    # E15 contains office name 'library', so simple keyword router classifies it as Intent.OFFICE (known failure E15)
    assert route("how long can I keep a library book", offices) == Intent.OFFICE


def test_rag_answerer_a1_threshold_boundary():
    """Score just below min_score abstains with 0 LLM calls; score equal to min_score calls LLM."""
    below_hit = DummyHit(chunk=DummyChunk(id="S26#3", title="Student card", text="Room I.102."), score=1.99)
    spy_abstain = SpyLLM()
    res_below = RagAnswerer(FakeIndex(hits=[below_hit]), spy_abstain, min_score=2.0).answer("card")
    assert res_below.path == "abstain"
    assert res_below.escalate is True
    assert spy_abstain.call_count == 0

    exact_hit = DummyHit(chunk=DummyChunk(id="H26#5.3", title="Thesis", text="120 credits."), score=2.0)
    spy_pass = SpyLLM()
    res_exact = RagAnswerer(FakeIndex(hits=[exact_hit]), spy_pass, min_score=2.0).answer("thesis")
    assert spy_pass.call_count == 1
    assert res_exact.path == "llm"
    assert [s.id for s in res_exact.sources] == ["H26#5.3"]


def test_rag_answerer_llm_model_abstain():
    """Valid abstain=True draft from production parse_draft returns abstain without retrying."""
    hit = DummyHit(chunk=DummyChunk(id="H26#5.3", title="Thesis", text="120 credits."), score=4.0)
    llm = SpyLLM(return_values=[json.dumps({"answer": "", "source_ids": [], "confidence": 0.25, "abstain": True})])
    res = RagAnswerer(FakeIndex(hits=[hit]), llm, min_score=2.0, retries=1).answer("unrelated question")
    assert llm.call_count == 1
    assert res.path == "abstain"
    assert res.escalate is True
    assert res.intent == Intent.UNKNOWN
    assert res.confidence == 0.25
    assert res.answer == ESCALATE_MSG


@pytest.mark.parametrize(
    "bad_output",
    [
        "not valid json",
        json.dumps({"answer": "Fake claim.", "source_ids": ["H26#9.9"], "confidence": 0.9, "abstain": False}),
    ],
)
def test_rag_answerer_invalid_json_or_fake_citation_retries_then_degrades(bad_output: str):
    """Invalid JSON or ungrounded citation retries once via production parse_draft then falls back degraded."""
    hit = DummyHit(chunk=DummyChunk(id="H26#5.3", title="Thesis", text="Min 120 credits."), score=4.0)
    llm = SpyLLM(return_values=[bad_output, bad_output])
    res = RagAnswerer(FakeIndex(hits=[hit]), llm, min_score=2.0, retries=1).answer("thesis credits")
    assert llm.call_count == 2
    assert res.path == "retrieval"
    assert res.degraded is True
    assert [s.id for s in res.sources] == ["H26#5.3"]


def test_rag_answerer_uses_production_imports_and_distinguishes_none_vs_stub():
    """Confirm no fallback parser/index shims remain and llm=None vs StubLLM return distinct paths."""
    assert answerer_module.parse_draft is prod_llm.parse_draft
    assert answerer_module.build_prompt is prod_llm.build_prompt
    assert answerer_module.Index is Index

    prod_hit = Hit(
        chunk=Chunk(
            id="S26#3",
            doc_id="S26",
            title="Student card replacement",
            text="Replace a lost card in room I.102.",
            version="2026.1",
            owner="Student Affairs",
        ),
        score=4.5,
    )
    index = FakeIndex(hits=[prod_hit])

    retrieval_res = RagAnswerer(index, llm=None, min_score=2.0).answer("I lost my student card")
    assert retrieval_res.path == "retrieval"
    assert retrieval_res.confidence is None
    assert [s.id for s in retrieval_res.sources] == ["S26#3"]

    llm_res = RagAnswerer(index, llm=prod_llm.StubLLM(), min_score=2.0).answer("I lost my student card")
    assert llm_res.path == "llm"
    assert llm_res.degraded is False
    assert [s.id for s in llm_res.sources] == ["S26#3"]
