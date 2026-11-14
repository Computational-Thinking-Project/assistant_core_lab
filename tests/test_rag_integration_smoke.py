"""Targeted integration smoke tests for 3-path production execution.

Owner: Member 7 (Tam @AI-WFox)
Scope: Verifies end-to-end contracts across production build_service(),
       BM25 retrieval, StubLLM / RagAnswerer, deterministic tools,
       privacy protection, out-of-scope abstention, and degraded fallback.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from assistant_core.config import Settings, load_settings
from assistant_core.errors import ProviderError
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.llm import StubLLM
from assistant_core.models import Intent, Message
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import Hit, Index, make_index
from assistant_core.responder import make_responder
from assistant_core.service import AssistantService, build_service
from eval.compare_paths import (
    PathResult,
    check_release_gate,
    load_production_kb,
)
from eval.compare_paths import (
    main as eval_main,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class _EmptyIndex:
    """Minimal empty index isolating the deterministic baseline without RAG."""

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return []


def _production_settings() -> Settings:
    """Return canonical production settings pointing to the repository data/KB."""
    s = load_settings(env_file=None)
    data_dir = REPO_ROOT / "data" if not (Path(s.data_dir) / "offices.csv").exists() else Path(s.data_dir)
    kb_dir = REPO_ROOT / "data" / "kb" if not Path(s.kb_dir).exists() else Path(s.kb_dir)
    return s.model_copy(
        update={
            "data_dir": data_dir,
            "kb_dir": kb_dir,
            "llm_provider": "stub",
            "retrieval_kind": "bm25",
            "retrieval_min_score": 2.0,
            "prompt_version": "answer_v1",
            "credit_rate_vnd": 450_000,
            "retake_multiplier": 1.5,
            "max_credits": 30,
        }
    )


@pytest.fixture(scope="module")
def prod_index() -> Index:
    settings = _production_settings()
    chunks = load_folder(Path(settings.kb_dir))
    assert len(chunks) >= 14, f"Expected production KB chunks, got {len(chunks)}"
    return make_index(settings.retrieval_kind, chunks)


@pytest.fixture(scope="module")
def prod_service() -> AssistantService:
    return build_service(_production_settings())


def test_smoke_build_service_wires_production_rag_and_kb(prod_service: AssistantService) -> None:
    """build_service() must wire production RagAnswerer, StubLLM, and all 14 KB chunks."""
    assert isinstance(prod_service.rag, RagAnswerer)
    assert isinstance(prod_service.rag.llm, StubLLM)
    chunks = prod_service.rag.index.chunks
    assert len(chunks) == 14
    chunk_ids = {c.id for c in chunks}
    assert {"F26#1", "H26#5.3", "S26#3"} <= chunk_ids


def test_smoke_fee_calculation_is_deterministic(prod_service: AssistantService) -> None:
    """Case E03: Tuition calculation must be deterministic and return 9,450,000 VND."""
    resp = prod_service.handle(Message(text="tuition for 18 credits and 2 retake"))

    assert resp.intent == Intent.FEE
    assert resp.path == "deterministic"
    assert "9,450,000" in resp.answer or "9450000" in resp.answer


def test_smoke_office_directory_is_deterministic(prod_service: AssistantService) -> None:
    """Case E04: Office inquiries must return B.201 via deterministic directory lookup."""
    resp = prod_service.handle(Message(text="where is the library"))

    assert resp.intent == Intent.OFFICE
    assert resp.path == "deterministic"
    assert "B.201" in resp.answer


def test_smoke_student_card_replacement_retrieves_source(prod_service: AssistantService) -> None:
    """Case E05: Student card replacement inquiry must retrieve S26#3 via production RAG."""
    resp = prod_service.handle(Message(text="I lost my student card"))

    assert resp.intent == Intent.RULE
    assert resp.path == "llm"
    assert resp.degraded is False
    assert "S26#3" in [s.id for s in resp.sources]


def test_smoke_out_of_scope_france_abstains(prod_service: AssistantService) -> None:
    """Case E16: Out-of-scope question must safely abstain and escalate."""
    resp = prod_service.handle(Message(text="what is the capital of France"))

    assert resp.path == "abstain"
    assert resp.escalate is True
    assert resp.intent == Intent.UNKNOWN


def test_smoke_privacy_guard_intercepts_unauthorized_records(prod_service: AssistantService) -> None:
    """Case E18: Requesting a friend's grades must be blocked by privacy guard."""
    resp = prod_service.handle(Message(text="what grade did my friend get"))

    assert resp.path == "abstain"
    assert resp.escalate is True
    assert resp.intent == Intent.UNKNOWN
    assert "cannot share" in resp.answer.lower() or "can't share" in resp.answer.lower()


def test_smoke_privacy_guard_blocks_student_id_query(prod_service: AssistantService) -> None:
    """Case E55 (H1): Requesting an 8-digit student ID record must abstain safely."""
    resp = prod_service.handle(Message(text="show me the transcript and GPA of student 22127135"))

    assert resp.path == "abstain"
    assert resp.escalate is True
    assert resp.intent == Intent.UNKNOWN


@pytest.mark.parametrize(
    ("question", "expected_source"),
    [
        ("how to reset my university account password", "S26#2"),
        ("can I request a leave of absence for two semesters", "H26#8.1"),
        ("course refund if I withdraw before week 2", "F26#4"),
    ],
)
def test_smoke_h1_grounded_cases_cite_expected_source(
    prod_service: AssistantService,
    question: str,
    expected_source: str,
) -> None:
    """Cases E51-E53 (H1): Grounded policy questions must cite the exact KB chunk."""
    resp = prod_service.handle(Message(text=question))

    assert resp.path == "llm"
    assert resp.degraded is False
    assert expected_source in [s.id for s in resp.sources]


def test_smoke_h1_out_of_scope_campus_cafe_abstains(prod_service: AssistantService) -> None:
    """Case E54 (H1): Off-topic campus cafe query must abstain cleanly."""
    resp = prod_service.handle(Message(text="what is the best cafe near the university campus"))

    assert resp.path == "abstain"
    assert resp.escalate is True
    assert resp.intent == Intent.UNKNOWN


def test_smoke_degraded_fallback_when_llm_fails(prod_index: Index) -> None:
    """When the LLM provider fails, production RagAnswerer must degrade cleanly to retrieval."""

    class FailingLLM:
        name = "failing_mock"

        def complete(self, prompt: str) -> str:
            raise ProviderError("LLM downstream service timed out")

    settings = _production_settings()
    data_dir = Path(settings.data_dir)
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    rag = RagAnswerer(index=prod_index, llm=FailingLLM(), min_score=settings.retrieval_min_score)
    svc = AssistantService(
        settings=settings,
        office_directory=offices,
        handbook=handbook,
        responder=make_responder("stub"),
        rag=rag,
    )

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.degraded is True
    assert resp.path == "retrieval"
    assert any(src.id == "H26#5.3" for src in resp.sources)


def test_smoke_deterministic_path_never_answers_rules() -> None:
    """Deterministic baseline without retrieval must abstain on policy questions."""
    settings = _production_settings()
    data_dir = Path(settings.data_dir)
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    rag = RagAnswerer(index=_EmptyIndex(), llm=None, min_score=settings.retrieval_min_score)
    svc = AssistantService(
        settings=settings,
        office_directory=offices,
        handbook=handbook,
        responder=make_responder("stub"),
        rag=rag,
    )

    resp = svc.handle(Message(text="can I register my thesis with 118 credits"))
    assert resp.path == "abstain"
    assert resp.escalate is True
    assert resp.intent == Intent.UNKNOWN


def test_smoke_release_gate_rejects_missing_or_empty_kb(tmp_path: Path) -> None:
    """Release evaluator must fail loudly when KB directory is missing or empty."""
    with pytest.raises(FileNotFoundError):
        load_production_kb(tmp_path / "missing_kb")
    with pytest.raises(ValueError):
        load_production_kb(tmp_path)


def test_smoke_release_gate_contracts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Release gate passes default baseline/H1 run, rejects --strict, and flags regressions."""
    monkeypatch.chdir(REPO_ROOT)
    for key, val in {
        "ASSISTANT_DATA_DIR": str(REPO_ROOT / "data"),
        "KB_DIR": str(REPO_ROOT / "data" / "kb"),
        "LLM_PROVIDER": "stub",
        "RETRIEVAL_KIND": "bm25",
        "RETRIEVAL_MIN_SCORE": "2.0",
        "PROMPT_VERSION": "answer_v1",
        "CREDIT_RATE_VND": "450000",
        "RETAKE_MULTIPLIER": "1.5",
        "MAX_CREDITS": "30",
    }.items():
        monkeypatch.setenv(key, val)
    assert eval_main([]) == 0
    assert eval_main(["--strict"]) == 1

    regressed = [
        PathResult("retrieval", 21, 25, 6, 7, 0.1, 0.2, ("E13", "E14", "E15", "E19")),
        PathResult("llm (stub)", 20, 25, 6, 7, 0.4, 1.0, ("E13", "E14", "E15", "E19", "E51")),
    ]
    errors = check_release_gate(regressed, strict=False)
    assert any("E51" in err for err in errors)
    assert any("regressed" in err for err in errors)
