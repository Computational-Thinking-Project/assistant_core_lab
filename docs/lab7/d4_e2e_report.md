# Lab 07 — API Integration & Part D.4 E2E Verification Report

- **Member:** Trương Thành Đạt (`@Thanhdat3010`, MSSV: `25127035`)
- **Role:** API Integration & End-to-End Testing (Part C & Part D.4)
- **Verified Base Commit (`main`):** `3f4e89e` (`feat(ui): implement format_sources (L1) and status_note (L2) (#80)`)
- **Tracking Issue:** `#83`

---

## 1. Two-Server Architecture & Startup Verification (Part C)

Both processes were launched independently from the repository root with `.env` copied from `.env.example` (`LLM_PROVIDER=stub`, `KB_DIR=data/kb`, `RETRIEVAL_KIND=bm25`, `RETRIEVAL_MIN_SCORE=2.0`, `PROMPT_VERSION=answer_v1`) and editable package installed (`pip install -e .`):

1. **Terminal 1 — FastAPI Backend (`127.0.0.1:8000`):**
   ```bash
   python scripts/migrate.py assistant.db
   python -m uvicorn assistant_api.main:create_app --factory --host 127.0.0.1 --port 8000
   ```
   Observed startup log:
   ```text
   INFO:     Started server process [24452]
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   ```

2. **Terminal 2 — Streamlit UI (`localhost:8501`):**
   ```bash
   python -m streamlit run ui/app.py --server.port 8501 --server.headless true
   ```
   Observed startup output:
   ```text
   Local URL: http://localhost:8501
   ```

---

## 2. `ui/api_client.py` HTTP Contract Verification

Audited `AssistantClient` and `ChatResult` in [`ui/api_client.py`](../../ui/api_client.py) against [`src/assistant_api/main.py`](../../src/assistant_api/main.py) and confirmed zero `assistant_core` imports inside `ui/`:

| Endpoint / Failure Mode | Request Payload / Condition | Expected API / Client Behavior | Verified Outcome |
|---|---|---|---|
| `GET /health` | Startup & every Streamlit rerun (`client.healthy()`) | Returns `200 OK`; returns `False` on `HTTPError`/`OSError` | Verified (`200 OK` when running; red banner when stopped) |
| `POST /v1/chat` (normal / tool / RAG) | `{"message": question, "session_id": session_id}` | Parses `answer`, `sources`, `request_id`, `escalate`, `degraded` | Verified (`200 OK`, deterministic fee + RAG `H26#5.3` + `S26#1`) |
| `POST /v1/chat` (`escalate=True`) | Out-of-scope question (`"what is the capital of France"`) | Sets `escalate=True`; `status_note()` renders blue `st.info` note | Verified (`Training Office, room I.101`) |
| `POST /v1/feedback` (`+1` / `-1`) | `{"request_id": rid, "rating": 1 or -1}` | Returns `201 Created`; hides buttons after vote | Verified (`201 Created` for both 👍 and 👎 in Uvicorn logs) |
| HTTP `422` | Validation error from API | Returns `ChatResult(ok=False, error="Invalid request: ...")` | Verified via `tests/test_ui.py` (`test_ask_422`) |
| HTTP `429` | Rate limit exceeded (`RATE_LIMIT_PER_MIN=1`) | Returns `"Too many requests — please wait a moment before retrying."` | Verified live in browser + Uvicorn log (`429 Too Many Requests`) and `tests/test_ui.py` (`test_ask_429`) |
| `TimeoutException` | Request exceeds client timeout | Returns `"The request timed out — the server may be busy."` | Verified via `tests/test_ui.py` (`test_ask_timeout`) |
| HTTP `500` (non-200) | Unexpected server error response | Returns `f"Server error {r.status_code}: {r.text[:200]}"` | Verified by inspecting `ui/api_client.py` (lines 65–66); dedicated HTTP `500` unit test is pending PR #82 (`tests/test_ui.py`) |
| Backend unreachable (`ConnectError`) | Backend stopped on port `8000` | `Ask` returns `"Cannot connect to the assistant backend."`; banner shows `"The assistant backend is not reachable..."` | Verified live in browser (`[data-testid="stException"]` = `0`) and `tests/test_ui.py` (`test_ask_backend_down`) |

> **Note:** On live `ConnectError`, the red top banner (`ui/app.py`) renders `"The assistant backend is not reachable. Start it with: uvicorn assistant_api.main:create_app --factory"` while `AssistantClient.ask()` (`ui/api_client.py`) returns `"Cannot connect to the assistant backend."` in chat; both fail politely without crashing.

---

## 3. Acceptance Table — 7 Mandatory Part D.4 E2E Scenarios

All 7 scenarios were executed end-to-end in a live Chromium browser against `http://localhost:8501` and `http://127.0.0.1:8000`:

| # | Scenario (Part D.4) | Action Taken | Observed Result | Status | Evidence |
|---|---|---|---|---|---|
| **1** | Sidebar example click | Loaded `http://localhost:8501`; confirmed no error banner; clicked sidebar button `"Tuition for 18 credits and 2 retake"` | Question & streamed answer rendered cleanly: `Your tuition is 9,450,000 VND.`; 👍 and 👎 visible | **PASS** | [dat-lab07-d4-1-sidebar.png](../evidence/dat-lab07-d4-1-sidebar.png) |
| **2** | Handbook policy query + source citation | Submitted `"Can I register my thesis with 118 credits?"`; opened `📚 Cited Sources (1)` expander | Returned grounded answer (`"According to 5.3 Thesis registration: Students may register a thesis when they have at least 120 accumulated credits and a cumulative GPA of at least 2.0."`) + source badge `H26#5.3 — 5.3 Thesis registration` | **PASS** | [dat-lab07-d4-2-thesis-sources.png](../evidence/dat-lab07-d4-2-thesis-sources.png) |
| **3** | Out-of-scope abstain & escalation | Submitted `"what is the capital of France"` | Displayed abstain answer + blue `st.info` note: `"I could not find this in the official documents. A staff member can help: Training Office, room I.101."` | **PASS** | [dat-lab07-d4-3-escalate.png](../evidence/dat-lab07-d4-3-escalate.png) |
| **4** | Empty input handling | Focused empty chat box (`"\n"` / empty) and pressed `Enter` | Message count stayed `7` (unchanged); empty input blocked cleanly and `st.warning` showed `"Please type a question."` without calling `/v1/chat` | **PASS** | [dat-lab07-d4-4-empty-input.png](../evidence/dat-lab07-d4-4-empty-input.png) |
| **5** | Feedback buttons (`👍` and `👎`) | Clicked `👍` on thesis answer, then `👎` on out-of-scope answer | Toast `"Thanks for your feedback!"` shown after clicking `👍`; both `POST /v1/feedback` logged `201 Created`; screenshot confirms `👍`/`👎` buttons removed from both rated messages | **PASS** | [dat-lab07-d4-5-feedback.png](../evidence/dat-lab07-d4-5-feedback.png) |
| **6** | Backend stopped (`Ctrl+C`) | Stopped Uvicorn on port `8000`; submitted `"Where is the library?"` in a fresh tab | Zero crash/traceback (`stException = 0`); screenshot shows both top red banner (`"The assistant backend is not reachable..."`) and chat error (`"⚠️ Cannot connect to the assistant backend."`) together | **PASS** | [dat-lab07-d4-6-backend-down.png](../evidence/dat-lab07-d4-6-backend-down.png) |
| **7** | API rate limit / server error (`429` & `500`) | Restarted Uvicorn with `RATE_LIMIT_PER_MIN=1`; sent `"Where is the library?"` (`200 OK`), immediately followed by `"I lost my student card"` (`429 Too Many Requests`); checked `500` handling in `ui/api_client.py` (lines 65–66; unit test pending PR #82) | Zero crash/traceback (`stException = 0`); UI displayed `"⚠️ Too many requests — please wait a moment before retrying."` | **PASS** | [dat-lab07-d4-7-rate-limit-429.png](../evidence/dat-lab07-d4-7-rate-limit-429.png) |

---

## 4. Observed Backend Server Logs

First server session (Scenarios 1–5):
```text
INFO:     127.0.0.1:63939 - "POST /v1/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:63947 - "POST /v1/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:63956 - "POST /v1/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:55914 - "POST /v1/feedback HTTP/1.1" 201 Created
INFO:     127.0.0.1:62015 - "POST /v1/feedback HTTP/1.1" 201 Created
```

Second server session with `RATE_LIMIT_PER_MIN=1` (Scenario 7):
```text
INFO:     127.0.0.1:56707 - "POST /v1/chat HTTP/1.1" 200 OK
INFO:     127.0.0.1:56711 - "POST /v1/chat HTTP/1.1" 429 Too Many Requests
```

---

## 5. Automated Regression Verification

- `python -m pytest -q --basetemp="<scratch_tmp>"` on `main` (`3f4e89e`): **312 passed, 1 warning in 30.96s** (including `tests/test_ui.py` and `tests/test_api.py`).
