"""UI logic without Streamlit, so it can be unit-tested.

This file contains:
- Stubs for L1 and L2 (assigned to Trung Anh — do not implement here)
- Duy's Bonus D.5 helpers: stream_generator and format_source_badges
"""

from __future__ import annotations

import time
from collections.abc import Generator

from ui.api_client import ChatResult

WELCOME = (
    "Hi! I can answer questions about fees, offices and the student handbook. "
    "Try: \u201cCan I register my thesis with 118 credits?\u201d"
)
EXAMPLES = [
    "Can I register my thesis with 118 credits?",
    "Tuition for 18 credits and 2 retake",
    "Where is the library?",
    "I lost my student card",
]


def validate_input(text: str) -> str | None:
    """Return an error message for bad input, or None if it is fine."""
    t = text.strip()
    if not t:
        return "Please type a question."
    if len(t) > 2000:
        return "Your question is too long (max 2000 characters)."
    return None


def format_sources(sources: list[dict]) -> str:
    """'Sources: H26#5.3 — 5.3 Thesis registration' or '' if none. (L1 — assigned to Trung Anh)"""
    # TODO L1 (assigned to Trung Anh): return "" if no sources, otherwise
    #   "Sources: " + "; ".join(f"{s['id']} — {s['title']}" for s in sources)
    raise NotImplementedError("L1")


def status_note(result: ChatResult) -> str | None:
    """A short note shown under the answer, explaining special situations. (L2 — assigned to Trung Anh)"""
    # TODO L2 (assigned to Trung Anh):
    #   if result.escalate -> "I could not find this in the official documents. ..."
    #   elif result.degraded -> "Shown directly from the source document ..."
    #   else -> None
    raise NotImplementedError("L2")


# ---- Duy's Bonus Enhancements (Part D.5: +1 point) -------------------------


def stream_generator(text: str, delay: float = 0.012) -> Generator[str, None, None]:
    """Yield chunks of text word-by-word with a slight delay for a typing/streaming effect.

    Compatible with Streamlit's st.write_stream() or any iterable consumer.
    """
    words = text.split(" ")
    for idx, word in enumerate(words):
        if idx < len(words) - 1:
            yield word + " "
        else:
            yield word
        if delay > 0:
            time.sleep(delay)


def format_source_badges(sources: list[dict]) -> list[tuple[str, str]]:
    """Extract (source_id, title) tuples for enhanced badge / card rendering (Bonus D.5)."""
    badges: list[tuple[str, str]] = []
    for s in sources:
        sid = str(s.get("id", "")).strip()
        title = str(s.get("title", "")).strip()
        if sid or title:
            badges.append((sid, title))
    return badges
