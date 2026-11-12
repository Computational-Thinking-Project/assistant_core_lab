"""Offline LLM adapter and validation for retrieved answers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from assistant_core.errors import ProviderError

if TYPE_CHECKING:
    from assistant_core.rag.index import Hit


PROMPTS = Path(__file__).parent / "prompts"


class AnswerDraft(BaseModel):
    """The complete JSON shape accepted from a model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    answer: str = Field(max_length=800)
    source_ids: list[str]
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    abstain: bool


class LLM(Protocol):
    name: str

    def complete(self, prompt: str) -> str: ...


def build_prompt(question: str, hits: list[Hit], version: str = "answer_v1") -> str:
    if version != "answer_v1":
        raise ProviderError("unsupported prompt version")
    try:
        template = (PROMPTS / "answer_v1.txt").read_text(encoding="utf-8")
    except OSError as exc:
        raise ProviderError("answer prompt is unavailable") from exc
    sources = "\n".join(f"[{hit.chunk.id}] {hit.chunk.title}: {hit.chunk.text}" for hit in hits)
    values = {"sources": sources, "question": question}
    return re.sub(r"\{(sources|question)\}", lambda match: values[match.group(1)], template)


def parse_draft(raw: str, allowed_ids: set[str]) -> AnswerDraft:
    """Reject malformed output and citations outside the retrieved hits."""
    try:
        data = json.loads(raw)
        draft = AnswerDraft.model_validate(data)
    except (TypeError, ValueError, ValidationError) as exc:
        raise ProviderError("invalid structured output") from exc
    if not draft.abstain and (not draft.source_ids or not set(draft.source_ids) <= allowed_ids):
        raise ProviderError("answer cites sources that were not retrieved")
    return draft


class StubLLM:
    """Deterministic provider used without an API key or network access."""

    name = "stub"

    def __init__(self, fail: bool = False, garbage: bool = False) -> None:
        self.fail = fail
        self.garbage = garbage

    def complete(self, prompt: str) -> str:
        if self.fail:
            raise ProviderError("stub provider unavailable")
        if self.garbage:
            return "This is not JSON."
        source = re.search(r"^\[([^\]]+)\] ([^:]+): (.+)$", prompt, flags=re.M)
        if source is None:
            return json.dumps({"answer": "", "source_ids": [], "confidence": 0.0, "abstain": True})
        first_sentence = re.split(r"(?<=\.)\s", source.group(3))[0]
        return json.dumps(
            {
                "answer": f"According to {source.group(2)}: {first_sentence}",
                "source_ids": [source.group(1)],
                "confidence": 0.7,
                "abstain": False,
            }
        )


def make_llm(
    provider: str, model: str, base_url: str | None, api_key: str | None, timeout_s: float
) -> LLM:
    """Construct the offline provider; the remaining arguments preserve the team contract."""
    if provider == "stub":
        return StubLLM()
    raise ProviderError(f"LLM provider {provider!r} is not supported in this release")
