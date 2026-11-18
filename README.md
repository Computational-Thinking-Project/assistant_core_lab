# FIT Study Assistant (CSC10014)

Modular student assistant featuring a deterministic & offline RAG core (`assistant_core`), a FastAPI + SQLite REST backend (`assistant_api`), and a Streamlit chat UI (`ui/`, pending Lab 7 integration toward `v0.7-mvp`).

> **Repository layout note:** This repository uses a flat root layout (`src/`, `tests/`, `data/`, `scripts/`, `eval/`, `worksheets/`), so this root `README.md` serves as the team setup and run guide (rather than `starter/README.md`).

---

## 1. Prerequisites

- **Python `>= 3.10`**
- **`sqlite3` CLI** (optional, required for running `sql/my_queries.sql`)
- **Git Bash** on Windows (recommended for `api-tests/curl_tests.sh`; WSL `bash` cannot reach Windows `127.0.0.1:8000` by default)
- **Run all commands from the repository root.** Paths such as `data/offices.csv`, `data/kb/`, and `sql/` are resolved relative to the current working directory.

---

## 2. Setup

### Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks script execution, allow it for the current session first:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Windows (Git Bash):**
```bash
python -m venv .venv
source .venv/Scripts/activate
```

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

> **Note (Lab 7 UI — pending integration):** `streamlit` is not yet pinned in `requirements.txt` on `main`. Until the Lab 7 UI integration PR updates `requirements.txt` (to include `streamlit==1.39.0`), install it manually if running the UI:
> ```bash
> pip install streamlit==1.39.0
> ```

### Configure `.env`

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Key settings in `.env` loaded by `assistant_core.config.load_settings()` (never commit `.env`):
- `LLM_PROVIDER=stub` — only `stub` (offline) is implemented in this release.
- `KB_DIR=data/kb`, `RETRIEVAL_KIND=bm25`, `RETRIEVAL_MIN_SCORE=2.0`, `PROMPT_VERSION=answer_v1` — Lab 6 RAG settings used by `build_service()` and the FastAPI server.
- `DATABASE_URL=sqlite:///assistant.db` and `SESSION_SALT` — Lab 5 SQLite persistence.
- `API_ADMIN_KEY` — required in the `X-API-Key` header for admin endpoints.

> **`ASSISTANT_API_URL` is a UI shell variable, not a `.env` setting:** `ui/app.py` calls `os.getenv("ASSISTANT_API_URL", "http://127.0.0.1:8000")` without `load_dotenv()`. Set it in the terminal running Streamlit (see Section 3).

---

## 3. Run the Two Servers

Start the backend API first, then start the Streamlit UI in a second terminal (both from the repository root with `.venv` activated).

### Terminal 1 — FastAPI Backend (Available on `main`, port `8000`)

```bash
uvicorn assistant_api.main:create_app --factory --reload --port 8000
```

- Interactive Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Terminal 2 — Streamlit UI (Pending Lab 7 `ui/` integration / `v0.7-mvp`, port `8501`)

> Requires `ui/` (`ui/app.py`, `ui/api_client.py`, `ui/logic.py`) from the Lab 7 UI PRs (reference on branch `lab07/sources`).

```bash
streamlit run ui/app.py --server.port 8501
```

- Opens at http://localhost:8501
- The UI never imports `assistant_core`; it communicates strictly over HTTP via `ui/api_client.py`.
- If the backend runs on a non-default port (for example `8001`), set `ASSISTANT_API_URL` in the Streamlit shell:
  - **Windows (PowerShell):**
    ```powershell
    $env:ASSISTANT_API_URL="http://127.0.0.1:8001"
    streamlit run ui/app.py --server.port 8501
    ```
  - **macOS / Linux / Git Bash:**
    ```bash
    ASSISTANT_API_URL="http://127.0.0.1:8001" streamlit run ui/app.py --server.port 8501
    ```

---

## 4. API Contract (`v1`)

| Method | Path | Request / Query / Headers | Success Response | Error Codes |
|---|---|---|---|---|
| `GET` | `/health` | — | `200` `{"status": "ok", "version": "1.0.0"}` | — |
| `POST` | `/v1/chat` | JSON: `message` (`1–2000` chars), `session_id` (optional, `≤64`, default `"anonymous"`) | `200` `{answer, intent, sources[], degraded, escalate, path, confidence, request_id}` (`path`: `deterministic \| retrieval \| llm \| tool \| abstain`) | `422 invalid_request`, `429 too_many_requests` |
| `POST` | `/v1/feedback` | JSON: `request_id` (`1–64`), `rating` (`-1 \| 0 \| 1`), `comment` (optional, `≤500`) | `201` feedback with `id`, `created_at` | `404 unknown_request_id`, `422 invalid_request` |
| `GET` | `/v1/feedback` | Header `X-API-Key`; optional query `?limit=100` | `200` list of feedback objects | `401 missing_or_invalid_api_key` |
| `GET` | `/v1/stats/intents` | Header `X-API-Key` | `200` `[{intent, requests, avg_latency_ms, unresolved}]` | `401 missing_or_invalid_api_key` |
| `GET` | `/v1/weather` | — | `200` `{temperature_c, wind_kmh, description, observed_at, stale}` | `503 weather_service_unavailable` |
| `GET` | `/v1/offices` | — | `200` sorted `[{name, room, hours}]` | — |

Application validation and HTTP errors use one JSON shape:
```json
{"error": {"code": "...", "message": "..."}}
```

See [`docs/api_contract.md`](docs/api_contract.md) for the v1 baseline contract and Lab 6 `ChatResponse` extension notes (note: `/v1/stats/intents` and feedback `404 unknown_request_id` are implemented in `src/assistant_api/main.py` and documented here).

---

## 5. Database, CLI & RAG Evaluation

### Database (Lab 5)

```bash
python scripts/migrate.py assistant.db      # apply sql/migrations in order
python scripts/seed.py assistant.db 300     # populate synthetic data only
```

Run analytics queries in `sql/my_queries.sql`:
- **Windows (PowerShell):**
  ```powershell
  Get-Content sql/my_queries.sql | sqlite3 assistant.db
  # or: sqlite3 assistant.db ".read sql/my_queries.sql"
  ```
- **macOS / Linux / Git Bash:**
  ```bash
  sqlite3 assistant.db < sql/my_queries.sql
  ```

### CLI — Deterministic Mode (Lab 3)

```bash
python -m assistant_core --test                      # characterization checks
python -m assistant_core "tuition for 18 credits"    # one-shot query
python -m assistant_core                             # interactive REPL
```

> **Note:** `src/assistant_core/__main__.py` instantiates `AssistantService()` directly without `build_service()` or `load_settings()`, so the CLI runs deterministic rules/tuition tools (`data/handbook.json`, `data/offices.csv`) and does **not** load `.env`, `data/kb/`, or `StubLLM`. To exercise the RAG pipeline, use `uvicorn assistant_api.main:create_app --factory` (`build_service()`) or `eval/compare_paths.py`.

### RAG Evaluation (Lab 6)

Knowledge base files live in `data/kb/*.md` and the prompt template in `src/assistant_core/prompts/answer_v1.txt`:
```bash
python eval/compare_paths.py                         # deterministic vs retrieval vs stub LLM
```

---

## 6. Testing, Linting & Manual Smoke Checks

```bash
pytest -q                                     # full test suite on main (offline; weather HTTP mocked)
ruff check src/assistant_api/main.py          # example: lint check on modified files
ruff format --check src/assistant_api/main.py # example: format check on modified files
```

- **UI tests (pending Lab 7 `ui/` integration):** `pytest -q tests/test_ui.py` once `tests/test_ui.py` is merged into `main`.
- **Note on baseline `ruff check .` / `ruff format --check .`:** `main` currently carries 5 pre-existing `ruff check` findings (`practice/`, `scripts/migrate.py`, `src/assistant_core/service.py`, `tests/test_service_rag.py`) and 12 unformatted files; check modified files cleanly on feature PRs until baseline cleanup lands.

### Manual HTTP Smoke Checks (Git Bash)

Against a running API server on port `8000`:
```bash
BASE=http://127.0.0.1:8000 API_ADMIN_KEY=change-me bash api-tests/curl_tests.sh --offices
```
To also test rate limiting (`--bonus`), restart Uvicorn (or wait 60s for a fresh quota window matching `RATE_LIMIT_PER_MIN`) and pass `--bonus`. Or import `api-tests/study-assistant.postman_collection.json` in Postman / Bruno.

---

## 7. Lab 7 Integration & Release Workflow (`v0.7-mvp`)

- **Architecture reference:** [`docs/architecture.md`](docs/architecture.md)
- **Branching & PR rules:**
  1. **Base and target branch:** Branch from `main` (for example `git checkout -b feat/lab07-<member>-<scope> origin/main`) and open PRs into **`main`** (unless an integration branch is announced by the Tech Lead). **Never branch from or target `lab07/sources`** — it is a reference-only branch for lecturer materials.
  2. **Root workspace layout:** Place all active Lab 7 deliverables at the repository root (`ui/`, `tests/test_ui.py`, `worksheets/usability_checklist.md`, `worksheets/user_test_observations.md`, `requirements.txt`, `pyproject.toml` with `pythonpath = [".", "src"]`, `README.md`). **Do not** edit `lab07_lecturer_given/starter/` or merge lecturer starter folders into `main`.
  3. **Scoped PR ownership:** Keep each PR strictly within its assigned module (`ui/logic.py` for L1/L2, `ui/app.py` for F1 or D.5 bonus, `tests/test_ui.py` for UI tests, `worksheets/` for Part E + H1/H2) without overwriting other members' tasks or importing `assistant_core` inside `ui/`.
- **Release gate:** After all module PRs pass review, merge into `main`, and pass the two-server Part D.4 E2E checks (along with removing pending-integration notes once `ui/` is landed), tag the release commit `v0.7-mvp`.

---

## 8. Troubleshooting

- **Banner `"The assistant backend is not reachable..."` in Streamlit:** Start Uvicorn (`uvicorn assistant_api.main:create_app --factory --reload --port 8000`) before opening the UI, or verify `ASSISTANT_API_URL` matches the backend port.
- **`DataError: office file not found: data/offices.csv`:** You started the server or script outside the repository root — `cd` to the repo root and re-run.
- **Port `8000` or `8501` already in use:** Start Uvicorn with another port (`--port 8001`) and pass `$env:ASSISTANT_API_URL="http://127.0.0.1:8001"` (PowerShell) or `ASSISTANT_API_URL=...` (bash) to `streamlit run ui/app.py --server.port 8501`.
- **`429 too_many_requests` during rapid testing:** Wait 60 seconds or raise `RATE_LIMIT_PER_MIN` in `.env` and restart Uvicorn.
