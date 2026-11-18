"""Streamlit chat UI for FIT Study Assistant.

Run:
    streamlit run ui/app.py      (the API must be running on port 8000)

The UI never imports assistant_core: it only talks to the backend through the HTTP API.

Bonus D.5 (Duy): Typing streaming animation via st.write_stream and enhanced
source citation display using st.expander with badge formatting.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so "import ui..." works under streamlit

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

st.set_page_config(page_title="FIT Study Assistant", page_icon="\U0001f393", layout="centered")
client = AssistantClient(os.getenv("ASSISTANT_API_URL", "http://127.0.0.1:8000"))

# ---- session state: remembered between reruns --------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:12]
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
if "rated" not in st.session_state:
    st.session_state.rated = set()

st.title("\U0001f393 FIT Study Assistant")
st.caption("This is an AI assistant. Check important decisions with the Training Office.")
if not client.healthy():
    st.error("The assistant backend is not reachable. Start it with: uvicorn assistant_api.main:create_app --factory")

with st.sidebar:
    st.subheader("\U0001f4a1 Try an example")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex
    st.caption("This is an AI assistant. Check important decisions with the Training Office.")


# ---- Bonus D.5: Enhanced Sources Display ------------------------------------
def render_enhanced_sources(sources_list: list[dict], fallback_str: str = "") -> None:
    """Render cited sources in an interactive expandable section with badge formatting."""
    badges = format_source_badges(sources_list) if sources_list else []
    if badges:
        with st.expander(f"\U0001f4da Cited Sources ({len(badges)})", expanded=False):
            for sid, title in badges:
                st.markdown(f"- \U0001f3f7\ufe0f **`{sid}`** \u2014 *{title}*")
    elif fallback_str:
        with st.expander("\U0001f4da Sources & References", expanded=False):
            st.caption(fallback_str)


# ---- message history --------------------------------------------------------
chat_container = st.container()
with chat_container:
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
            placeholder = st.empty()
            if rid and rid not in st.session_state.rated:
                with placeholder.container():
                    c1, c2, _ = st.columns([1, 1, 6])
                    up_clicked = c1.button("\U0001f44d", key=f"up{i}")
                    down_clicked = c2.button("\U0001f44e", key=f"down{i}")
                voted = False
                if up_clicked:
                    if client.send_feedback(rid, 1):
                        st.session_state.rated.add(rid)
                        st.toast("Thanks for your feedback!")
                        voted = True
                    else:
                        st.toast("Could not submit feedback. Please try again.")
                elif down_clicked:
                    if client.send_feedback(rid, -1):
                        st.session_state.rated.add(rid)
                        st.toast("Thanks \u2014 we will look at this answer.")
                        voted = True
                    else:
                        st.toast("Could not submit feedback. Please try again.")
                if voted:
                    placeholder.empty()

# ---- quick-start examples on first screen (visible on phone-width too) ------
starter_placeholder = st.empty()
if len(st.session_state.messages) == 1:
    with starter_placeholder.container():
        st.caption("Try an example:")
        for idx, ex in enumerate(EXAMPLES):
            if st.button(ex, key=f"starter_ex_{idx}", use_container_width=True):
                st.session_state.pending = ex
else:
    starter_placeholder.empty()

# ---- new question -----------------------------------------------------------
question = st.chat_input("Ask about fees, offices or the handbook\u2026") or st.session_state.pop("pending", None)
if question:
    problem = validate_input(question)
    if problem:
        st.warning(problem)
    else:
        starter_placeholder.empty()
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking\u2026"):
                result = client.ask(question, st.session_state.session_id)

            if result.ok:
                # Bonus D.5: word-by-word streaming typing effect
                st.write_stream(stream_generator(result.answer))

                # Bonus D.5: enhanced expandable source citations
                try:
                    sources_str = format_sources(result.sources)
                except NotImplementedError:
                    sources_str = ""  # L1 not yet merged — degrade gracefully
                render_enhanced_sources(result.sources)

                try:
                    note_str = status_note(result)
                except NotImplementedError:
                    note_str = None  # L2 not yet merged — degrade gracefully
                if note_str:
                    st.info(note_str)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": result.answer,
                        "sources": sources_str,
                        "raw_sources": result.sources,
                        "note": note_str,
                        "request_id": result.request_id,
                    }
                )
            else:
                err_msg = f"\u26a0\ufe0f {result.error}"
                st.markdown(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

        st.rerun()
