"""Intent router for assistant_core.

Phụ trách: Thành viên 3 (Đạt)
Phạm vi: route()
"""

from assistant_core.models import Intent

__all__ = ["GREETINGS", "route"]

GREETINGS = frozenset({"hi", "hello", "hey", "xin chao"})


def route(text: str, office_names: set[str]) -> Intent:
    """Classify user text into an Intent based on simple deterministic rules."""
    t = text.lower().strip().rstrip("?!.")
    if t in GREETINGS:
        return Intent.GREETING
    if "fee" in t or "tuition" in t:
        return Intent.FEE
    if any(name.lower() in t for name in office_names):
        return Intent.OFFICE
    return Intent.RULE
