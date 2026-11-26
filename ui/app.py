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
from ui.icons import ASSISTANT_AVATAR, USER_AVATAR, avatar_for, svg_data_uri
from ui.logic import (
    EXAMPLES,
    WELCOME,
    format_source_badges,
    format_sources,
    status_note,
    stream_generator,
    validate_input,
)


@st.cache_data(show_spinner=False)
def _portal_css() -> str:
    """Build static academic portal CSS with Base64-encoded local Lucide SVG icons."""
    up_uri = svg_data_uri("thumbs-up.svg")
    down_uri = svg_data_uri("thumbs-down.svg")
    return f"""
<style>
[data-testid="stDecoration"],
[data-testid="stAppDeployButton"] {{
    display: none;
}}

header[data-testid="stHeader"] {{
    background-color: rgba(248, 250, 252, 0.92);
    backdrop-filter: blur(6px);
}}

.block-container {{
    max-width: 760px;
    padding-top: 4.25rem;
    padding-bottom: 1.75rem;
}}

.fit-eyebrow {{
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748B;
    margin: 0 0 0.15rem 0;
}}

h1 {{
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: #0F172A !important;
    padding-top: 0 !important;
    margin-bottom: 0.25rem !important;
}}

[data-testid="stChatMessage"] {{
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.55rem;
}}

[data-testid="stChatMessage"] [data-testid*="Avatar"] {{
    background-color: #EEF2F6 !important;
    color: #1E3A5F !important;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
}}

[data-testid="stSidebar"] {{
    border-right: 1px solid #E2E8F0;
}}

[data-testid="stSidebar"] button {{
    text-align: left;
    justify-content: flex-start;
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    font-size: 0.86rem;
    color: #1E293B;
}}

[data-testid="stSidebar"] button:hover {{
    border-color: #1E3A5F;
    color: #0F172A;
}}

[class*="st-key-starter_ex_"] button {{
    text-align: left;
    justify-content: flex-start;
    min-height: 3.1rem;
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    color: #0F172A;
    font-size: 0.88rem;
    font-weight: 500;
}}

[class*="st-key-starter_ex_"] button:hover {{
    background-color: #F8FAFC;
    border-color: #1E3A5F;
    color: #0F172A;
}}

@media (max-width: 640px) {{
    .block-container {{
        padding-top: 4rem;
        padding-bottom: 1rem;
    }}

    [class*="st-key-starter_ex_"] button {{
        min-height: 2.4rem;
        padding-top: 0.35rem;
        padding-bottom: 0.35rem;
    }}
}}

.stHorizontalBlock:has([class*="st-key-up"]) {{
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: fit-content !important;
    gap: 0.35rem !important;
    align-items: center !important;
    margin-top: 0.25rem;
}}

.stHorizontalBlock:has([class*="st-key-up"]) > div:nth-child(1),
.stHorizontalBlock:has([class*="st-key-up"]) > div:nth-child(2) {{
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}}

.stHorizontalBlock:has([class*="st-key-up"]) > div:nth-child(3) {{
    display: none !important;
}}

[class*="st-key-up"] button,
[class*="st-key-down"] button {{
    width: 2.2rem !important;
    height: 1.95rem !important;
    min-height: 1.95rem !important;
    padding: 0 !important;
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 15px 15px !important;
}}

[class*="st-key-up"] button {{
    background-image: url("{up_uri}") !important;
}}

[class*="st-key-down"] button {{
    background-image: url("{down_uri}") !important;
}}

[class*="st-key-up"] button:hover,
[class*="st-key-down"] button:hover {{
    background-color: #F1F5F9 !important;
    border-color: #1E3A5F !important;
}}

[class*="st-key-up"] button p,
[class*="st-key-down"] button p {{
    font-size: 0 !important;
    line-height: 0 !important;
    margin: 0 !important;
}}

[data-testid="stExpander"] details {{
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #F8FAFC;
}}

[data-testid="stExpander"] code {{
    color: #1E3A5F !important;
    background-color: #E2E8F0 !important;
    padding: 0.12rem 0.42rem !important;
    border-radius: 4px !important;
    font-weight: 600;
}}
</style>
        """


def _inject_portal_styles() -> None:
    """Inject cached academic portal stylesheet into the Streamlit page."""
    st.markdown(_portal_css(), unsafe_allow_html=True)


# ---- Bonus D.5: Enhanced Sources Display ------------------------------------
def render_enhanced_sources(sources_list: list[dict], fallback_str: str = "") -> None:
    """Render cited sources in an interactive expandable section without emojis."""
    badges = format_source_badges(sources_list) if sources_list else []
    if badges:
        with st.expander(f"Cited sources ({len(badges)})", expanded=False, icon=":material/description:"):
            for sid, title in badges:
                st.markdown(f"- **`{sid}`** \u2014 *{title}*")
    elif fallback_str:
        with st.expander("Sources & references", expanded=False, icon=":material/description:"):
            st.caption(fallback_str)


st.set_page_config(
    page_title="FIT Study Assistant",
    page_icon=":material/school:",
    layout="centered",
    initial_sidebar_state="collapsed",
)
_inject_portal_styles()
HEALTH_CHECK_TIMEOUT_SECONDS = 5.0
api_url = os.getenv("ASSISTANT_API_URL", "http://127.0.0.1:8000")
client = AssistantClient(api_url)
# Tolerate slow local/cold /health responses while bounding stalled sockets well under the 30s chat timeout.
health_client = AssistantClient(api_url, timeout=HEALTH_CHECK_TIMEOUT_SECONDS)

# ---- session state: remembered between reruns --------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:12]
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
if "rated" not in st.session_state:
    st.session_state.rated = set()

st.markdown('<p class="fit-eyebrow">Faculty of Information Technology · Academic Desk</p>', unsafe_allow_html=True)
st.title("FIT Study Assistant")
st.caption(
    "AI assistant for handbook policies, fees, and campus offices. "
    "Confirm important decisions with the Training Office."
)
if not health_client.healthy():
    st.error(
        "The assistant backend is not reachable. Please try again shortly or contact the Training Office (room I.101)."
    )

with st.sidebar:
    st.subheader("Common questions")
    for ex in EXAMPLES:
        if st.button(ex, use_container_width=True):
            st.session_state.pending = ex
    st.caption("AI assistant grounded in FIT handbook documents. Check important decisions with the Training Office.")

# ---- message history --------------------------------------------------------
chat_container = st.container()
with chat_container:
    for i, m in enumerate(st.session_state.messages):
        with st.chat_message(m["role"], avatar=avatar_for(m["role"])):
            if m.get("is_error"):
                st.warning(m["content"])
            else:
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
                    c1, c2, _ = st.columns([1, 1, 14])
                    # Labels stay compatible with F1 tests while CSS renders monochrome Lucide SVGs.
                    up_clicked = c1.button("\U0001f44d", key=f"up{i}", help="Helpful")
                    down_clicked = c2.button("\U0001f44e", key=f"down{i}", help="Needs review")
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

# ---- quick-start prompts on first screen (compact 2x2 grid on desktop) -------
starter_placeholder = st.empty()
if len(st.session_state.messages) == 1:
    with starter_placeholder.container():
        st.caption("Suggested topics")
        for row_start in range(0, len(EXAMPLES), 2):
            cols = st.columns(2)
            for offset, ex in enumerate(EXAMPLES[row_start : row_start + 2]):
                idx = row_start + offset
                with cols[offset]:
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
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(question)

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
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
                err_msg = result.error or "Unable to reach the assistant backend."
                st.warning(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg, "is_error": True})

        st.rerun()
