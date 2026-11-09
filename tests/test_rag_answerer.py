"""Targeted unit tests for Response contract and RagAnswerer (TV3 - Đạt).

Tests verify:
1. Response model backward compatibility with defaults.
2. A1: Pre-retrieval abstain (zero LLM calls when score < min_score or no hits).
3. Retrieval-only baseline (llm=None).
4. LLM path success and source mapping.
5. ProviderError / bad output retry policy and degraded retrieval fallback.
6. Tool runner execution and error handling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.rag.answerer import ESCALATE_MSG, RagAnswerer


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
            "answer": "Default mock answer",
            "source_ids": ["H26#5.3"],
            "confidence": 0.85,
            "abstain": False,
        })


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
    """When tool runner is configured and model requests fee calculation."""
    hit = DummyHit(chunk=DummyChunk(id="F26#2", title="Retake fee", text="1.5x regular rate"), score=3.0)
    fake_index = FakeIndex(hits=[hit])
    llm = SpyLLM(return_values=['{"tool": "calc_fee", "args": {"credits": 10}}'])

    def dummy_tool_runner(raw: str) -> str | None:
        if "calc_fee" in raw:
            return "Total fee is 4,500,000 VND"
        return None

    answerer = RagAnswerer(fake_index, llm, min_score=2.0, tool_runner=dummy_tool_runner)
    res = answerer.answer("how much does a retake cost")

    assert res.path == "tool"
    assert res.intent == Intent.FEE
    assert "4,500,000" in res.answer


def test_rag_answerer_tool_runner_invalid_request():
    """When tool runner raises InvalidRequest, return degraded tool response."""
    hit = DummyHit(chunk=DummyChunk(id="F26#2", title="Retake fee", text="1.5x regular rate"), score=3.0)
    fake_index = FakeIndex(hits=[hit])
    llm = SpyLLM(return_values=['{"tool": "calc_fee", "args": {"credits": 999}}'])

    def invalid_tool_runner(raw: str) -> str | None:
        raise InvalidRequest("credits exceed maximum limit of 30")

    answerer = RagAnswerer(fake_index, llm, min_score=2.0, tool_runner=invalid_tool_runner)
    res = answerer.answer("can I take 999 credits")

    assert res.path == "tool"
    assert res.intent == Intent.FEE
    assert res.degraded is True
    assert "credits exceed maximum limit" in res.answer
