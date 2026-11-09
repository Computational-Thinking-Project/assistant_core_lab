"""Answer policy questions with retrieval + LLM, safely.

Phụ trách: Thành viên 3 (Đạt)
Phạm vi: RagAnswerer, TODO A1 pre-retrieval abstain, retry and degraded fallback.

Order of defences:
  1. retrieve; if the best score is too low -> ABSTAIN and escalate (no LLM call)
  2. ask the LLM for structured JSON; validate schema + grounding; retry once
  3. on provider failure or invalid output -> quote the best source (retrieval-only fallback)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from assistant_core.errors import InvalidRequest, ProviderError
from assistant_core.models import Intent, Response, Source

try:
    from assistant_core.rag.index import Hit, Index
except ImportError:
    @dataclass(frozen=True)
    class Hit:  # type: ignore[no-redef]
        chunk: object
        score: float

    class Index(Protocol):  # type: ignore[no-redef]
        def search(self, query: str, k: int = 3) -> list[Hit]: ...

try:
    from assistant_core.llm import LLM, AnswerDraft, build_prompt, parse_draft
except ImportError:
    class LLM(Protocol):  # type: ignore[no-redef]
        name: str

        def complete(self, prompt: str) -> str: ...

    class AnswerDraft:  # type: ignore[no-redef]
        answer: str
        source_ids: list[str]
        confidence: float
        abstain: bool

    def build_prompt(question: str, hits: list[Hit], version: str = "answer_v1") -> str:
        sources = "\n".join(
            f"[{getattr(h.chunk, 'id', '')}] {getattr(h.chunk, 'title', '')}: {getattr(h.chunk, 'text', '')}"
            for h in hits
        )
        return f"SOURCES:\n{sources}\nQUESTION: {question}"

    def parse_draft(raw: str, allowed_ids: set[str]) -> AnswerDraft:
        raise NotImplementedError("llm module not yet integrated")

log = logging.getLogger("assistant_core.rag")
ESCALATE_MSG = (
    "I'm not confident I can answer that from the official documents. "
    "Please contact the Training Office (room I.101) or ask your academic advisor."
)


class RagAnswerer:
    def __init__(
        self,
        index: Index,
        llm: LLM | None,
        min_score: float = 2.0,
        k: int = 3,
        prompt_version: str = "answer_v1",
        retries: int = 1,
        tool_runner: Callable[[str], str | None] | None = None,
    ):
        self.index, self.llm, self.min_score, self.k = index, llm, min_score, k
        self.prompt_version, self.retries, self.tool_runner = prompt_version, retries, tool_runner

    def answer(self, question: str) -> Response:
        hits = self.index.search(question, self.k)
        # TODO A1: if no hits or the best score is below min_score, abstain before calling the LLM
        if not hits or hits[0].score < self.min_score:
            return Response(
                answer=ESCALATE_MSG,
                intent=Intent.UNKNOWN,
                path="abstain",
                escalate=True,
                confidence=0.0,
            )
        sources = {h.chunk.id: Source(id=h.chunk.id, title=h.chunk.title) for h in hits}
        top = hits[0].chunk
        if self.llm is None:  # retrieval-only baseline
            return Response(
                answer=f"{top.title}: {top.text}",
                intent=Intent.RULE,
                sources=[sources[top.id]],
                path="retrieval",
                confidence=None,
            )
        prompt = build_prompt(question, hits, self.prompt_version)
        for attempt in range(self.retries + 1):
            try:
                raw = self.llm.complete(prompt)
                if self.tool_runner is not None:
                    try:
                        result = self.tool_runner(raw)
                    except InvalidRequest as exc:
                        return Response(answer=str(exc), intent=Intent.FEE, path="tool", degraded=True)
                    if result is not None:
                        return Response(answer=result, intent=Intent.FEE, path="tool")
                draft: AnswerDraft = parse_draft(raw, set(sources))
                if draft.abstain:
                    return Response(
                        answer=ESCALATE_MSG,
                        intent=Intent.UNKNOWN,
                        path="abstain",
                        escalate=True,
                        confidence=draft.confidence,
                    )
                return Response(
                    answer=draft.answer,
                    intent=Intent.RULE,
                    path="llm",
                    confidence=draft.confidence,
                    sources=[sources[i] for i in draft.source_ids],
                )
            except ProviderError as exc:
                log.warning("llm attempt %d failed: %s", attempt + 1, exc)
        return Response(
            answer=f"{top.title}: {top.text}",
            intent=Intent.RULE,
            sources=[sources[top.id]],
            path="retrieval",
            degraded=True,
        )
