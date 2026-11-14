"""Compare deterministic, retrieval-only, and LLM assistant paths on eval/cases.jsonl.

Owner: Member 7 (Tam @AI-WFox)
Evaluates integrated production modules (load_folder, make_index, RagAnswerer,
StubLLM/make_llm, AssistantService, build_service, and guard) without fallback
or duplicate RAG implementations.

Usage:
    python eval/compare_paths.py
    python eval/compare_paths.py --baseline-only
    python eval/compare_paths.py --strict
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from assistant_core.config import Settings, load_settings
from assistant_core.models import Message
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import Chunk, load_folder
from assistant_core.rag.index import Hit, make_index
from assistant_core.service import AssistantService, build_service

BASELINE_CASE_COUNT = 20
KNOWN_FAILURES = frozenset({"E13", "E14", "E15", "E19"})


class NoAnswer:
    """Empty retrieval index that isolates the deterministic (no-RAG) baseline."""

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return []


@dataclass(frozen=True)
class PathResult:
    """Measured evaluation summary for one execution path."""

    name: str
    correct: int
    total: int
    abstain_ok: int
    abstain_total: int
    p50_ms: float
    max_ms: float
    fails: tuple[str, ...]


def load_production_kb(kb_dir: Path) -> list[Chunk]:
    """Load markdown knowledge chunks from the production KB directory."""
    if not kb_dir.exists() or not kb_dir.is_dir():
        raise FileNotFoundError(f"KB directory not found: {kb_dir}")
    chunks = load_folder(kb_dir)
    if not chunks:
        raise ValueError(f"KB directory contains no markdown chunks: {kb_dir}")
    return chunks


def load_cases(cases_file: Path) -> list[dict[str, Any]]:
    """Load evaluation cases from JSONL and fail loudly if missing or empty."""
    if not cases_file.exists():
        raise FileNotFoundError(f"Evaluation file not found: {cases_file}")
    cases = [
        json.loads(line)
        for line in cases_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not cases:
        raise ValueError(f"Evaluation file is empty: {cases_file}")
    return cases


def correct(case: dict[str, Any], resp: Any) -> bool:
    """Return True when a service response satisfies the evaluation case expectation."""
    if case.get("expect_abstain"):
        path = getattr(resp, "path", "")
        intent = getattr(resp, "intent", None)
        intent_val = intent.value if hasattr(intent, "value") else str(intent)
        escalate = getattr(resp, "escalate", False)
        answer = getattr(resp, "answer", "").lower()
        if path == "abstain" or intent_val == "unknown" or escalate:
            return True
        if "sorry" in answer or "don't know" in answer or "dont know" in answer or "contact" in answer:
            return True
        if "can't share" in answer or "cannot share" in answer:
            return True
        return False

    if "expect_contains" in case:
        return case["expect_contains"] in getattr(resp, "answer", "")

    if "expect_source" in case:
        expected = case["expect_source"]
        sources = getattr(resp, "sources", [])
        return any(getattr(s, "id", "") == expected for s in sources)

    return False


def build_eval_paths(settings: Settings, chunks: list[Chunk]) -> dict[str, AssistantService]:
    """Construct all three isolated evaluation paths over production components."""
    data_dir = Path(settings.data_dir)
    offices_file = data_dir / "offices.csv"
    handbook_file = data_dir / "handbook.json"
    if not offices_file.exists() or not handbook_file.exists():
        raise FileNotFoundError(f"Required data assets missing in: {data_dir}")

    llm_svc = build_service(settings)
    if not isinstance(llm_svc.rag, RagAnswerer):
        raise RuntimeError("build_service() did not wire production RagAnswerer")
    if llm_svc.rag.llm is None:
        raise RuntimeError("build_service() did not configure a production LLM adapter")

    index = make_index(settings.retrieval_kind, chunks)
    min_score = float(settings.retrieval_min_score)
    prompt_version = settings.prompt_version
    llm_label = f"llm ({llm_svc.rag.llm.name})"

    det_svc = AssistantService(
        settings=settings,
        office_directory=llm_svc.office_directory,
        handbook=llm_svc.handbook,
        responder=llm_svc.responder,
        rag=RagAnswerer(NoAnswer(), None, min_score=min_score, prompt_version=prompt_version),
    )
    ret_svc = AssistantService(
        settings=settings,
        office_directory=llm_svc.office_directory,
        handbook=llm_svc.handbook,
        responder=llm_svc.responder,
        rag=RagAnswerer(index, None, min_score=min_score, prompt_version=prompt_version),
    )
    return {
        "deterministic": det_svc,
        "retrieval": ret_svc,
        llm_label: llm_svc,
    }


def evaluate_path(name: str, svc: AssistantService, cases: list[dict[str, Any]]) -> PathResult:
    """Run an ordered set of evaluation cases against one service configuration."""
    ok = 0
    abst_ok = 0
    abst_total = 0
    latencies: list[float] = []
    fails: list[str] = []

    for case in cases:
        t0 = time.perf_counter()
        resp = svc.handle(Message(text=case["question"]))
        latencies.append((time.perf_counter() - t0) * 1000)
        passed = correct(case, resp)
        ok += int(passed)
        if case.get("expect_abstain"):
            abst_total += 1
            abst_ok += int(passed)
        if not passed:
            fails.append(case["id"])

    p50_ms = statistics.median(latencies) if latencies else 0.0
    max_ms = max(latencies) if latencies else 0.0
    return PathResult(
        name=name,
        correct=ok,
        total=len(cases),
        abstain_ok=abst_ok,
        abstain_total=abst_total,
        p50_ms=p50_ms,
        max_ms=max_ms,
        fails=tuple(fails),
    )


def evaluate_suite(
    label: str,
    paths: dict[str, AssistantService],
    cases: list[dict[str, Any]],
) -> list[PathResult]:
    """Evaluate all three paths on a case subset and print the summary table."""
    print(f"\n=== {label} ({len(cases)} cases) ===")
    print(f"{'path':18} {'correct':>8} {'abstain ok':>11} {'p50 ms':>7} {'max ms':>7}")
    results: list[PathResult] = []
    for name, svc in paths.items():
        res = evaluate_path(name, svc, cases)
        results.append(res)
        fail_str = " ".join(res.fails)
        print(
            f"{res.name:18} {res.correct:>5}/{res.total:<2} "
            f"{res.abstain_ok:>7}/{res.abstain_total:<2} "
            f"{res.p50_ms:7.1f} {res.max_ms:7.1f}   fails: {fail_str}"
        )
    return results


def check_release_gate(
    results: list[PathResult],
    *,
    strict: bool = False,
    known_failures: frozenset[str] = KNOWN_FAILURES,
) -> list[str]:
    """Validate retrieval and LLM path quality against release-gate expectations."""
    errors: list[str] = []
    by_name = {r.name: r for r in results}
    ret_res = by_name.get("retrieval")
    llm_res = next((r for name, r in by_name.items() if name.startswith("llm ")), None)

    if ret_res is None or llm_res is None:
        return ["missing retrieval or llm evaluation results"]

    for res in (ret_res, llm_res):
        if res.correct == 0:
            errors.append(f"{res.name} scored 0/{res.total}")
        unexpected = list(res.fails) if strict else [cid for cid in res.fails if cid not in known_failures]
        if unexpected:
            mode = "strict" if strict else "release"
            errors.append(f"{res.name} failed {mode} gate on cases: {', '.join(unexpected)}")

    if llm_res.correct < ret_res.correct:
        errors.append(
            f"{llm_res.name} regressed below retrieval on total score ({llm_res.correct} < {ret_res.correct})"
        )
    if llm_res.abstain_ok < ret_res.abstain_ok:
        errors.append(
            f"{llm_res.name} regressed below retrieval on abstention ({llm_res.abstain_ok} < {ret_res.abstain_ok})"
        )
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare deterministic, retrieval, and LLM paths.")
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Evaluate only the first 20 baseline cases (E01-E20).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require zero failed cases (fail even on documented known failures).",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("eval/cases.jsonl"),
        help="Path to evaluation JSONL file (default: eval/cases.jsonl).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        settings = load_settings(env_file=None)
        cases = load_cases(args.cases)
        chunks = load_production_kb(Path(settings.kb_dir))
        paths = build_eval_paths(settings, chunks)
    except (FileNotFoundError, ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"GATE FAILED (setup): {exc}", file=sys.stderr)
        return 1

    print(
        "Config:"
        f" kb_dir={settings.kb_dir}"
        f" chunks={len(chunks)}"
        f" retrieval={settings.retrieval_kind}"
        f" min_score={settings.retrieval_min_score}"
        f" llm={settings.llm_provider}"
        f" prompt={settings.prompt_version}"
    )

    baseline_cases = cases[:BASELINE_CASE_COUNT]
    baseline_results = evaluate_suite("Baseline (Part F: E01-E20)", paths, baseline_cases)
    gate_results = baseline_results

    if not args.baseline_only and len(cases) > BASELINE_CASE_COUNT:
        full_results = evaluate_suite("Full Suite (Part H1: E01-E55)", paths, cases)
        gate_results = full_results

    gate_errors = check_release_gate(gate_results, strict=args.strict)
    if gate_errors:
        for err in gate_errors:
            print(f"GATE FAILED: {err}", file=sys.stderr)
        return 1

    print(
        f"\nGATE PASSED: verified {len(chunks)} KB chunks across {len(gate_results)} paths"
        + ("" if args.strict else f" (known failures: {', '.join(sorted(KNOWN_FAILURES))})")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
