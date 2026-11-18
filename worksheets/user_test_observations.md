# Lab 7 homework — 10-minute usability test

- **Tester (Member 7 heuristic self-evaluation per team assignment):** Tam
- **Date:** 2026-11-18
- **Task evaluated:** "Find out if you can register your thesis with 118 credits, and where to replace a lost student card." (plus out-of-scope, invalid-input, and backend-down checks)

Rule: act as a first-time user without prior setup knowledge, inspect every screen and edge case carefully, and record real UI/system issues.

| # | What happened during evaluation | What a user expects | Why the system/UI caused it | Fix idea |
|---|---|---|---|---|
| 1 | On a `375x812` phone-width window (sidebar collapsed behind top-left `>`), the initial screen showed only the title and welcome bubble—neither clickable example buttons nor the `"This is an AI assistant..."` notice appeared in view. | New mobile visitors immediately see clear AI attribution and tappable starter prompts right on the landing screen without discovering the collapsed sidebar drawer. | In `ui/app.py`, the 4 `EXAMPLES` buttons and the AI notice lived only inside `with st.sidebar:`, which Streamlit collapses on narrow screens. | Render `"This is an AI assistant. Check important decisions with the Training Office."` below `st.title` in the main pane and display full-width quick-start buttons above `chat_input` on the initial state, clearing them once submitted. **(Implemented)** |
| 2 | Answers for both `"Can I register my thesis with 118 credits?"` and `"Where can I replace a lost student card?"` rendered `Cited Sources (1)` collapsed by default (`H26#5.3 — 5.3 Thesis registration`, `S26#3 — 3 Student card replacement`). | Policy citations should be immediately scannable to verify trust without an extra click per message, and source badges should read like plain document sections rather than raw IDs (`H26#5.3`, `S26#3`). | `render_enhanced_sources` in `ui/app.py` hardcodes `st.expander(..., expanded=False)` and passes raw chunk IDs verbatim from `format_source_badges`. | Default citations to `expanded=True` on the latest answer (or show compact inline chips) and map `doc_id` prefixes to friendly labels such as `Handbook 2026, Sec. 5.3`. *(Deferred)* |
| 3 | Out-of-scope prompt `"What is the capital of France?"` repeated `Training Office (room I.101)` twice (inside the reply text and the `st.info` note) alongside rating buttons, while stopping the backend displayed a CLI command (`uvicorn assistant_api.main:create_app --factory`) to students. | A single clear human-handoff callout without repeating room details back-to-back, and plain non-technical guidance when the service is offline. | `ui/app.py` unconditionally renders `status_note(result)` even when the backend refusal already embeds the office room, and displays a developer startup command in `st.error`. | Deduplicate overlapping escalation text when the refusal already cites `Training Office`, and replace the `uvicorn` CLI snippet with student-friendly retry/office instructions. *(Deferred)* |

The one change we made (commit / code): `478984a` (`feat(ux): show AI notice and example prompts in main pane`) in [`ui/app.py`](../ui/app.py) with regression test `test_h1_first_screen_shows_ai_notice_and_examples_in_main_pane` in [`tests/test_ui.py`](../tests/test_ui.py).

## Before / after screenshots

- Desktop (`1280x800`) before: [`docs/evidence/tam-lab07-before-desktop.png`](../docs/evidence/tam-lab07-before-desktop.png)
- Desktop (`1280x800`) after: [`docs/evidence/tam-lab07-after-desktop.png`](../docs/evidence/tam-lab07-after-desktop.png)
- Mobile (`375x812`) before (no AI notice or example buttons visible on first screen): [`docs/evidence/tam-lab07-before-mobile.png`](../docs/evidence/tam-lab07-before-mobile.png)
- Mobile (`375x812`) after (AI disclosure + 4 quick-start buttons cleanly visible without horizontal overflow): [`docs/evidence/tam-lab07-after-mobile.png`](../docs/evidence/tam-lab07-after-mobile.png)
- Desktop flow after (starter buttons cleared, `Cited Sources (1)` expanded to `H26#5.3 — 5.3 Thesis registration`, thumbs-up toast shown): [`docs/evidence/tam-lab07-after-desktop-flow.png`](../docs/evidence/tam-lab07-after-desktop-flow.png)

## Homework H2 — Google PAIR Guidebook Reflection

*(From chapters Feedback + Control and Errors + Graceful Failure)*

The assistant already applies Google PAIR's *Errors + Graceful Failure* and *Feedback + Control* principles by catching invalid inputs, backend outages, and low-confidence queries with clear warnings or Training Office (`room I.101`) escalation instead of failing silently, while offering immediate per-answer thumbs-up/thumbs-down acknowledgment and safe retry when feedback delivery fails. As a next improvement under *Feedback + Control*, clicking thumbs-down could reveal an optional compact reason selector (such as outdated policy, wrong fact, or unhelpful answer) paired with a short expectation note explaining how student feedback is reviewed to improve future responses.
