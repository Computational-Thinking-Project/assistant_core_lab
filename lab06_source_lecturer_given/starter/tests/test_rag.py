import json
from pathlib import Path

import pytest

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.guard import is_private_request
from assistant_core.llm import StubLLM, parse_draft
from assistant_core.models import Intent
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import Hit, make_index
from assistant_core.tools import run_tool_call

KB = Path(__file__).resolve().parents[1] / "data" / "kb"


@pytest.fixture(scope="module")
def chunks():
    return load_folder(KB)


def test_chunks_have_ids_and_metadata(chunks):
    ids = {c.id for c in chunks}
    assert {"H26#5.3", "F26#2", "S26#3"} <= ids
    assert all(c.version == "2026.1" for c in chunks)


@pytest.mark.parametrize("kind", ["bm25", "tfidf", "hybrid"])
def test_retrieval_finds_thesis_rule(chunks, kind):
    assert make_index(kind, chunks).search("can I register my thesis with 118 credits")[0].chunk.id == "H26#5.3"


def test_abstain_when_nothing_relevant(chunks):
    r = RagAnswerer(make_index("bm25", chunks), StubLLM()).answer("what is the capital of France")
    assert r.path == "abstain" and r.escalate


def test_llm_answer_is_grounded(chunks):
    r = RagAnswerer(make_index("bm25", chunks), StubLLM()).answer("I lost my student card")
    assert r.path == "llm" and r.sources[0].id == "S26#3"


def test_invalid_output_falls_back_to_retrieval(chunks):
    r = RagAnswerer(make_index("bm25", chunks), StubLLM(garbage=True)).answer("I lost my student card")
    assert r.path == "retrieval" and r.degraded and r.sources[0].id == "S26#3"


def test_provider_failure_falls_back(chunks):
    r = RagAnswerer(make_index("bm25", chunks), StubLLM(fail=True)).answer("reset my password")
    assert r.degraded and r.sources


def test_citation_of_unretrieved_source_is_rejected():
    raw = json.dumps({"answer": "x", "source_ids": ["H26#9.9"], "confidence": 0.9, "abstain": False})
    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})


def test_tool_call_validated():
    assert "9,450,000" in run_tool_call('{"tool": "calc_fee", "args": {"credits": 18, "retake": 2}}', 450_000, 1.5, 30)
    assert run_tool_call('{"answer": "not a tool"}', 450_000, 1.5, 30) is None
    with pytest.raises(InvalidRequest):
        run_tool_call('{"tool": "calc_fee", "args": {"credits": 99}}', 450_000, 1.5, 30)


class ToolCallingLLM:
    name = "scripted"

    def complete(self, prompt):
        return '{"tool": "calc_fee", "args": {"credits": 10}}'


def test_answerer_executes_tool_call(chunks):
    def runner(raw):
        return run_tool_call(raw, 450_000, 1.5, 30)

    r = RagAnswerer(make_index("bm25", chunks), ToolCallingLLM(), tool_runner=runner).answer(
        "how much does a retake cost"
    )
    assert r.path == "tool" and "4,500,000" in r.answer


@pytest.mark.parametrize("q", ["what grade did my friend get", "show the GPA of another student", "phone of 22127001"])
def test_privacy_guard(q):
    assert is_private_request(q)


def test_privacy_guard_allows_own_questions():
    assert not is_private_request("what is my GPA requirement for the thesis")


@pytest.mark.parametrize("score", [None, 1.999])
def test_abstain_before_calling_llm(chunks, score):
    class FixedIndex:
        def search(self, query, k=3):
            return [] if score is None else [Hit(chunks[0], score)]

    class ForbiddenLLM:
        name = "forbidden"

        def complete(self, prompt):
            pytest.fail("A1 must abstain before calling the LLM")

    response = RagAnswerer(FixedIndex(), ForbiddenLLM()).answer("a question")
    assert response.path == "abstain"
    assert response.intent is Intent.UNKNOWN
    assert response.escalate and response.confidence == 0.0
    assert response.sources == []


def test_score_equal_to_threshold_calls_llm(chunks):
    class FixedIndex:
        def search(self, query, k=3):
            return [Hit(chunks[0], 2.0)]

    class CountingLLM(StubLLM):
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return super().complete(prompt)

    llm = CountingLLM()
    response = RagAnswerer(FixedIndex(), llm).answer("a question")
    assert llm.calls == 1
    assert response.path == "llm"
    assert [source.id for source in response.sources] == [chunks[0].id]


@pytest.mark.parametrize("source_ids", [[], ["H26#5.3", "invented#1"]])
def test_non_abstain_requires_only_retrieved_sources(source_ids):
    raw = json.dumps({"answer": "x", "source_ids": source_ids, "confidence": 0.7, "abstain": False})
    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})


@pytest.mark.parametrize("abstain, source_ids", [(False, ["H26#5.3"]), (True, [])])
def test_valid_citation_or_explicit_abstain_is_accepted(abstain, source_ids):
    raw = json.dumps({"answer": "x", "source_ids": source_ids, "confidence": 0.7, "abstain": abstain})
    draft = parse_draft(raw, {"H26#5.3"})
    assert draft.abstain is abstain and draft.source_ids == source_ids


@pytest.mark.parametrize("raw", ['{"answer":', '{"answer":"x","source_ids":[],"confidence":7}'])
def test_invalid_json_or_schema_raises_provider_error(raw):
    with pytest.raises(ProviderError):
        parse_draft(raw, {"H26#5.3"})


@pytest.mark.parametrize("source_ids", [[], ["invented#1"]])
def test_bad_citations_retry_once_then_fall_back(chunks, source_ids):
    class InvalidCitationLLM:
        name = "invalid-citation"
        calls = 0

        def complete(self, prompt):
            self.calls += 1
            return json.dumps({"answer": "x", "source_ids": source_ids, "confidence": 0.7, "abstain": False})

    llm = InvalidCitationLLM()
    response = RagAnswerer(make_index("bm25", chunks), llm).answer("I lost my student card")
    assert llm.calls == 2
    assert response.path == "retrieval" and response.degraded
    assert [source.id for source in response.sources] == ["S26#3"]
