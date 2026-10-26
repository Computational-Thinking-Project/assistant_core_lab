"""Responder interface, template responder, and stub LLM.

Phụ trách: Thành viên 6
Phạm vi: Responder (Protocol), TemplateResponder, StubLLMResponder
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .errors import ProviderError

if TYPE_CHECKING:
    from .knowledge import Rule


class Responder(Protocol):
    """Interface shared by template and provider-based responders."""

    def explain(self, question: str, rule: Rule) -> str: ...


class TemplateResponder:
    """Return the original rule without calling an AI provider."""

    def explain(self, question: str, rule: Rule) -> str:
        return f"{rule.title}: {rule.text}"


class StubLLMResponder:
    """Simulate provider success or failure without network access."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def explain(self, question: str, rule: Rule) -> str:
        if self.fail:
            raise ProviderError("stub provider unavailable")
        return f"Based on '{rule.title}': {rule.text}"


def make_responder(provider: str) -> Responder:
    if provider == "stub":
        return StubLLMResponder()
    if provider == "template":
        return TemplateResponder()
    raise ProviderError(f"unknown provider {provider!r} (real providers arrive in Week 4)")

