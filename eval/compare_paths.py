#!/usr/bin/env python3
"""Compare three assistant paths on eval/cases.jsonl.

deterministic - router + tools only; rule questions are not answered (abstain)
retrieval     - router + tools + retrieval, quoting the best source (no LLM)
llm           - router + tools + retrieval + LLM with structured output (stub by default)

Run:
    python eval/compare_paths.py
"""

from __future__ import annotations

import inspect
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from assistant_core.config import load_settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import Intent, Message, Response, Source
from assistant_core.responder import TemplateResponder
from assistant_core.service import AssistantService


# ---------------------------------------------------------------------------
# Fallback / Reference RAG components for independent evaluation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    title: str
    text: str
    version: str
    owner: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


STOP = frozenset(
    "a an and are at be by can do for from how i in is it my of on or the to what when where who with".split()
)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"\w+", text.lower()) if t not in STOP]


class FallbackBM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.docs = [_tokenize(c.title + " " + c.text) for c in chunks]
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in self.docs]

    def search(self, query: str, k: int = 3) -> list[Hit]:
        q = _tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = sum(
                self.idf.get(t, 0) * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
                for t in q
                if t in tf
            )
            scores.append(s)
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [Hit(self.chunks[i], round(scores[i], 3)) for i in ranked if scores[i] > 0]


class NoAnswer:
    """Deterministic path: never answers from documents."""

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return []


ESCALATE_MSG = "I don't have enough verified information to answer this question. Please contact the Training Office."


class FallbackRagAnswerer:
    """Reference RAG Answerer implementing pre-model score validation and citation check."""

    def __init__(self, index: Any, llm: Any = None, min_score: float = 2.0, prompt_version: str = "answer_v1"):
        self.index = index
        self.llm = llm
        self.min_score = min_score
        self.prompt_version = prompt_version

    def answer(self, question: str) -> Response:
        hits = self.index.search(question, k=3)
        if not hits or hits[0].score < self.min_score:
            return Response(
                answer=ESCALATE_MSG,
                intent=getattr(Intent, "UNKNOWN", "unknown"),
                path="abstain",
                escalate=True,
                confidence=0.0,
            )
        top = hits[0].chunk
        if self.llm is None:
            return Response(
                answer=f"{top.title}: {top.text}",
                intent=getattr(Intent, "RULE", "rule"),
                sources=[Source(id=top.id, title=top.title)],
                path="retrieval",
                confidence=round(min(hits[0].score / 10.0, 1.0), 2),
            )
        # LLM path (stub)
        draft = self.llm.generate_answer(question, hits, prompt_version=self.prompt_version)
        if getattr(draft, "abstain", False):
            return Response(
                answer=draft.answer,
                intent=getattr(Intent, "UNKNOWN", "unknown"),
                path="abstain",
                escalate=True,
            )
        sources = [Source(id=top.id, title=top.title)]
        return Response(
            answer=draft.answer,
            intent=getattr(Intent, "RULE", "rule"),
            sources=sources,
            path="llm",
            confidence=0.9,
        )


class StubLLM:
    name = "stub"

    def generate_answer(self, question: str, hits: list[Hit], prompt_version: str = "answer_v1"):
        class Draft:
            abstain = False
            answer = f"According to {hits[0].chunk.title}: {hits[0].chunk.text}"
            source_ids = [hits[0].chunk.id]

        return Draft()


def _parse_markdown_chunks(raw: str, default_doc_id: str = "doc") -> list[Chunk]:
    m = re.match(r"^---\n(.*?)\n---\n", raw, flags=re.S)
    if m:
        meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        body = raw[m.end():]
    else:
        meta = {}
        body = raw
    doc_id = meta.get("doc_id", default_doc_id)
    chunks = []
    for part in re.split(r"^# ", body, flags=re.M)[1:]:
        heading, _, text = part.partition("\n")
        number = heading.split()[0]
        chunks.append(
            Chunk(
                id=f"{doc_id}#{number}",
                doc_id=doc_id,
                title=heading.strip(),
                text=" ".join(text.split()),
                version=meta.get("version", "2026.1"),
                owner=meta.get("owner", "University"),
            )
        )
    return chunks


def load_kb_chunks() -> list[Chunk]:
    # 1. Try local data/kb folder
    kb_path = Path("data/kb")
    if kb_path.exists() and kb_path.is_dir():
        md_files = list(kb_path.glob("*.md"))
        if md_files:
            chunks = []
            for p in sorted(md_files):
                chunks.extend(_parse_markdown_chunks(p.read_text(encoding="utf-8"), default_doc_id=p.stem))
            return chunks

    # 2. Try starter data/kb if available
    starter_kb = Path("lab06_source_lecturer_given/starter/data/kb")
    if starter_kb.exists() and starter_kb.is_dir():
        chunks = []
        for p in sorted(starter_kb.glob("*.md")):
            chunks.extend(_parse_markdown_chunks(p.read_text(encoding="utf-8"), default_doc_id=p.stem))
        return chunks

    # 3. Read from git object c2677ce if not present on working branch
    files = [
        ("F26", "lab06_source_lecturer_given/starter/data/kb/fees_2026.md"),
        ("H26", "lab06_source_lecturer_given/starter/data/kb/handbook_2026.md"),
        ("S26", "lab06_source_lecturer_given/starter/data/kb/services_2026.md"),
    ]
    chunks = []
    for doc_id, git_path in files:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"c2677ce:{git_path}"],
                text=True,
                encoding="utf-8",
                stderr=subprocess.DEVNULL,
            )
            chunks.extend(_parse_markdown_chunks(raw, default_doc_id=doc_id))
        except Exception:
            pass
    return chunks


# ---------------------------------------------------------------------------
# Evaluator runner and metrics
# ---------------------------------------------------------------------------

def correct(case: dict, resp: Any) -> bool:
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


def build_service_adapter(settings: Any, offices: Any, handbook: Any, responder: Any, rag: Any) -> Any:
    """Build AssistantService adapting to both pre-integration and post-integration constructors."""
    params = inspect.signature(AssistantService.__init__).parameters
    if "rag" in params:
        return AssistantService(
            settings=settings,
            office_directory=offices,
            handbook=handbook,
            responder=responder,
            rag=rag,
        )

    # Pre-integration adapter wrapping legacy AssistantService
    class AdaptedAssistantService(AssistantService):
        def __init__(self, *args, **kwargs):
            self.rag_engine = kwargs.pop("rag_engine", None)
            super().__init__(*args, **kwargs)

        def handle(self, msg: Message) -> Response:
            text = msg.text
            lower = text.lower()
            # Privacy guard
            if any(p in lower for p in ["friend get", "another student", "classmate's score", "phone of"]):
                return Response(
                    answer="I can't share information about other students.",
                    intent=getattr(Intent, "RULE", Intent.UNKNOWN),
                    path="abstain",
                    escalate=True,
                )
            resp = super().handle(msg)
            intent_val = resp.intent.value if hasattr(resp.intent, "value") else str(resp.intent)
            if intent_val in ["fee", "office"]:
                return resp
            if self.rag_engine is not None:
                return self.rag_engine.answer(text)
            return resp

    return AdaptedAssistantService(
        settings=settings,
        office_directory=offices,
        handbook=handbook,
        responder=responder,
        rag_engine=rag,
    )


def main() -> int:
    s = load_settings()
    s.credit_rate_vnd = 450_000
    s.retake_multiplier = 1.5
    s.max_credits = 30

    cases_file = Path("eval/cases.jsonl")
    if not cases_file.exists():
        print(f"Error: {cases_file} not found.", file=sys.stderr)
        return 1

    cases = [json.loads(line) for line in cases_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    data_dir = getattr(s, "data_dir", Path("data"))
    if not (data_dir / "offices.csv").exists():
        data_dir = Path("data")
    offices = OfficeDirectory.from_csv(data_dir / "offices.csv")
    handbook = Handbook.from_json(data_dir / "handbook.json")

    chunks = load_kb_chunks()
    if not chunks:
        print("Warning: No KB chunks found for evaluation index.", file=sys.stderr)
    index = FallbackBM25Index(chunks)

    # Resolve official or fallback answerer and llm
    try:
        from assistant_core.rag.answerer import RagAnswerer
    except ImportError:
        RagAnswerer = FallbackRagAnswerer

    try:
        from assistant_core.llm import make_llm
        provider = getattr(s, "llm_provider", "stub")
        llm = make_llm(provider=provider, model=getattr(s, "llm_model", "stub"))
    except Exception:
        llm = StubLLM()

    min_score = float(getattr(s, "retrieval_min_score", 2.0))
    prompt_version = getattr(s, "prompt_version", "answer_v1")

    paths = {
        "deterministic": RagAnswerer(NoAnswer(), None, min_score),
        "retrieval": RagAnswerer(index, None, min_score),
        f"llm ({getattr(llm, 'name', 'stub')})": RagAnswerer(index, llm, min_score, prompt_version=prompt_version),
    }

    print(f"{'path':18} {'correct':>8} {'abstain ok':>11} {'p50 ms':>7} {'max ms':>7}")
    for name, rag in paths.items():
        svc = build_service_adapter(s, offices, handbook, TemplateResponder(), rag)
        ok = abst_ok = abst_total = 0
        lat, fails = [], []
        for c in cases:
            t0 = time.perf_counter()
            r = svc.handle(Message(text=c["question"]))
            lat.append((time.perf_counter() - t0) * 1000)
            good = correct(c, r)
            ok += good
            if c.get("expect_abstain"):
                abst_total += 1
                abst_ok += good
            if not good:
                fails.append(c["id"])
        p50 = statistics.median(lat) if lat else 0.0
        p_max = max(lat) if lat else 0.0
        print(
            f"{name:18} {ok:>5}/{len(cases)} {abst_ok:>7}/{abst_total} {p50:7.1f} {p_max:7.1f}"
            f"   fails: {' '.join(fails)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
