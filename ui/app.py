"""Streamlit chat UI for FIT Study Assistant.

Run:
    streamlit run ui/app.py      (the API must be running on port 8000)

The UI never imports assistant_core: it only talks to the backend through the HTTP API.
Includes:
- Full support for Part C & D core flow
- F1 (👎 feedback button & toast)
- Duy's Bonus (Part D.5: Typing streaming animation & Enhanced source citation display)
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # so "import ui..." works under streamlit

from ui.api_client import AssistantClient
from ui.logic import (
    EXAMPLES,
    WELCOME,
    format_source_badges,
    format_sources,
    status_note,
    stream_generator,
    validate_input,
)

st.set_page_config(page_title="FIT Study Assistant", page_icon="🎓", layout="centered")
client = AssistantClient(os.getenv("ASSISTANT_API_URL", "http://127.0.0.1:8000"))

# ---- session state: remembered between reruns of this script ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:12]
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
if "rated" not in st.session_state:
    st.session_state.rated = set()

st.title("🎓 FIT Study Assistant")
if not client.healthy():
    st.error("The assistant backend is not reachable. Start it with: uvicorn assistant_api.main:create_app --factory")

with st.sidebar:
    st.subheader("💡 Try an example")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex
    st.caption("This is an AI assistant. Check important decisions with the Training Office.")


# ---- Helper: Better Sources Display (Duy's Bonus Feature D.5) ----------------
def render_enhanced_sources(sources_list: list[dict], fallback_str: str = "") -> None:
    """Renders cited sources in an interactive, structured expander with badges."""
    badges = format_source_badges(sources_list) if sources_list else []
    if badges:
        with st.expander(f"📚 Cited Sources ({len(badges)})", expanded=False):
            for sid, title in badges:
                st.markdown(f"- 🏷️ **`{sid}`** — *{title}*")
    elif fallback_str:
        with st.expander("📚 Sources & References", expanded=False):
            st.caption(fallback_str)


# ---- history -------------------------------------------------------------------
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("raw_sources"):
            render_enhanced_sources(m["raw_sources"])
        elif m.get("sources"):
            render_enhanced_sources([], fallback_str=m["sources"])
        if m.get("note"):
            st.info(m["note"])
        rid = m.get("request_id")
        if rid and rid not in st.session_state.rated:
            c1, c2, _ = st.columns([1, 1, 6])
            if c1.button("👍", key=f"up{i}"):
                client.send_feedback(rid, 1)
                st.session_state.rated.add(rid)
                st.toast("Thanks for your feedback!")
            # F1 (👎 button)
            if c2.button("👎", key=f"down{i}"):
                client.send_feedback(rid, -1)
                st.session_state.rated.add(rid)
                st.toast("Thanks — we will look at this answer.")

# ---- new question ----------------------------------------------------------------
question = st.chat_input("Ask about fees, offices or the handbook…") or st.session_state.pop("pending", None)
if question:
    problem = validate_input(question)
    if problem:
        st.warning(problem)
    else:
        # 1. Immediately show user question
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # 2. Query API and display assistant response with typing/streaming animation (Bonus D.5)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result = client.ask(question, st.session_state.session_id)

            if result.ok:
                # Word-by-word streaming typing effect
                st.write_stream(stream_generator(result.answer))

                sources_str = format_sources(result.sources)
                if result.sources:
                    render_enhanced_sources(result.sources)
                note_str = status_note(result)
                if note_str:
                    st.info(note_str)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.answer,
                    "sources": sources_str,
                    "raw_sources": result.sources,
                    "note": note_str,
                    "request_id": result.request_id,
                })
            else:
                err_msg = f"⚠️ {result.error}"
                st.markdown(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

        st.rerun()
