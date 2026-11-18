# Lab 7 — Usability checklist (tick before your user test)

- [x] The first screen says what the assistant can do, with example questions
- [x] Empty or too-long input shows a friendly message (not a crash)
- [x] While waiting, the user sees "Thinking…"
- [x] Every answer from documents shows its sources
- [x] "I don't know" answers tell the user who can help (escalation)
- [x] If the backend is down, the page says so clearly
- [x] Each answer has 👍 / 👎, and clicking gives a "thanks" message
- [x] The page says it is an AI assistant
- [x] Text is readable (size, contrast); buttons have clear labels
- [x] Works on a phone-width window

## Verification Notes (Live Two-Server Check & Automated Tests, 2026-11-18)

| # | Criterion | Verification Method & Observed Result |
|---|---|---|
| 1 | First screen scope + examples | Initial bubble states what the assistant answers (`WELCOME` in `ui/logic.py`); 4 clickable examples (`EXAMPLES`) appear in the collapsed sidebar (`Common questions`) and main-pane 2x2 grid (`starter_ex_0`..`starter_ex_3`), clearing once a question is submitted. |
| 2 | Empty or too-long input | Whitespace `"   "` shows warning `"Please type a question."`; 2005-char input shows warning `"Your question is too long (max 2000 characters)."` without crashing (`validate_input` in `ui/logic.py`). |
| 3 | Loading indicator | Question submission enters `with st.spinner("Thinking\u2026"):` (`ui/app.py`) while calling `client.ask(...)`. |
| 4 | Document source citations | Thesis query (`"Can I register my thesis with 118 credits?"`) renders `Cited sources (1)` expanding to `H26#5.3 — 5.3 Thesis registration`; lost-card query renders `S26#3 — 3 Student card replacement`. |
| 5 | Escalation on unknown queries | `"What is the capital of France?"` displays refusal + `st.info` note directing the user to `Training Office, room I.101` (`status_note` in `ui/logic.py`). |
| 6 | Backend outage handling | Stopping Uvicorn (`127.0.0.1:8000`) shows top `st.error` banner (`"The assistant backend is not reachable..."` directing students to retry or contact `Training Office (room I.101)`) and chat submission falls back cleanly to `"Cannot connect to the assistant backend."` without traceback. |
| 7 | Per-answer rating & acknowledgment | Monochrome Lucide thumbs-up/down SVG rating buttons render side-by-side; clicking thumbs-up shows `"Thanks for your feedback!"`, clicking thumbs-down shows `"Thanks — we will look at this answer."`, and clears that message's vote buttons. |
| 8 | AI disclosure | Visible immediately in main pane below title (`"AI assistant for handbook policies, fees, and campus offices. Confirm important decisions with the Training Office."`) and in sidebar. |
| 9 | Readability & clear labels | Light institutional portal palette (`.streamlit/config.toml`), zero Unicode emojis, Material Symbol avatars/source icons, and Lucide vector SVG rating icons verified across desktop (`1280x800`) and mobile (`375x812`). |
| 10 | Phone-width responsiveness | Verified at `375x812` with sidebar collapsed: zero clipping below the top header (`.fit-eyebrow` at `y=80`), zero horizontal overflow (`stMainBlockContainer` `y=0`, width `375.2px`), AI notice, 4 examples, and side-by-side feedback buttons cleanly visible. |
