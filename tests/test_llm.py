"""Grounding and offline-provider checks against the production LLM module."""

from __future__ import annotations

import json

import pytest

from assistant_core.errors import ProviderError
from assistant_core.llm import StubLLM, build_prompt, make_llm, parse_draft
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import Chunk
from assistant_core.rag.index import Hit


def raw_draft(**changes: object) -> str:
    data = {"answer": "Use the Training Office.", "source_ids": ["S26#3"], "confidence": 0.7, "abstain": False}
    data.update(changes)
    return json.dumps(data)


@pytest.fixture
def hit() -> Hit:
    return Hit(
        Chunk(
            "S26#3",
            "S26",
            "Student card replacement",
            "Replace a lost card in room I.102.",
            "2026.1",
            "Student Affairs",
        ),
        4.5,
    )


def test_parse_draft_accepts_grounded_answer_and_abstention() -> None:
    grounded = parse_draft(raw_draft(), {"S26#3"})
    assert grounded.source_ids == ["S26#3"]
    assert grounded.confidence == 0.7
    abstention = parse_draft(raw_draft(answer="", source_ids=[], confidence=0.0, abstain=True), set())
    assert abstention.abstain is True


@pytest.mark.parametrize(
    "raw",
    [
        raw_draft(source_ids=[]),
        raw_draft(source_ids=["S26#3", "H26#9.9"]),
        raw_draft(source_ids="S26#3"),
        raw_draft(source_ids=[7]),
        raw_draft(confidence=7),
        raw_draft(confidence="0.7"),
        raw_draft(confidence=True),
        raw_draft(abstain="false"),
        raw_draft(answer=5),
        raw_draft(unexpected="extra"),
        json.dumps({"answer": "missing fields"}),
        "not JSON",
        "prefix " + raw_draft(),
        raw_draft() + " suffix",
        "[" + raw_draft() + "]",
        raw_draft(confidence=float("nan")),
    ],
)
def test_parse_draft_rejects_invalid_or_ungrounded_output(raw: str) -> None:
    with pytest.raises(ProviderError):
        parse_draft(raw, {"S26#3"})


def test_prompt_inserts_sources_and_question_without_recursing(hit: Hit) -> None:
    question = "Where do I replace {sources}?"
    prompt = build_prompt(question, [hit])
    assert "[S26#3] Student card replacement: Replace a lost card in room I.102." in prompt
    assert f"QUESTION: {question}" in prompt
    assert "Return ONLY a valid JSON object" in prompt
    with pytest.raises(ProviderError, match="unsupported prompt version"):
        build_prompt(question, [hit], version="other")


def test_stub_is_offline_and_produces_parseable_output(hit: Hit) -> None:
    stub = make_llm("stub", "unused", None, None, 5.0)
    assert isinstance(stub, StubLLM)
    draft = parse_draft(stub.complete(build_prompt("I lost my student card", [hit])), {hit.chunk.id})
    assert draft.source_ids == ["S26#3"]
    assert draft.abstain is False
    assert parse_draft(stub.complete(build_prompt("unknown", [])), set()).abstain is True


@pytest.mark.parametrize("provider", ["ollama", "openai", "unknown"])
def test_other_providers_fail_without_network(provider: str) -> None:
    with pytest.raises(ProviderError, match="not supported"):
        make_llm(provider, "unused", None, None, 5.0)


def test_stub_failure_modes() -> None:
    with pytest.raises(ProviderError, match="stub provider unavailable"):
        StubLLM(fail=True).complete("prompt")
    with pytest.raises(ProviderError, match="invalid structured output"):
        parse_draft(StubLLM(garbage=True).complete("prompt"), set())


class FakeIndex:
    def __init__(self, hit: Hit) -> None:
        self.hit = hit

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return [self.hit]


class WrongCitationLLM:
    name = "wrong-citation"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return raw_draft(source_ids=["H26#9.9"])


def test_answerer_uses_production_parser_and_grounded_stub(hit: Hit) -> None:
    from assistant_core import llm
    from assistant_core.rag import answerer

    assert answerer.parse_draft is llm.parse_draft
    result = RagAnswerer(FakeIndex(hit), StubLLM()).answer("I lost my student card")
    assert result.path == "llm"
    assert result.degraded is False
    assert [source.id for source in result.sources] == ["S26#3"]


def test_invalid_citation_retries_then_degrades_to_retrieval(hit: Hit) -> None:
    wrong_llm = WrongCitationLLM()
    result = RagAnswerer(FakeIndex(hit), wrong_llm, retries=1).answer("I lost my student card")
    assert wrong_llm.calls == 2
    assert result.path == "retrieval"
    assert result.degraded is True
    assert [source.id for source in result.sources] == ["S26#3"]
