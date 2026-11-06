# Lab 05 QA: Regression and Persistence Verification

Owner: Nhat Quynh (Member 7). QA execution and report preparation: Codex, for owner review.

## Revision and scope

| Item | Revision or source |
|---|---|
| Lab 04 baseline | `v0.4-api` (`a9ba3a416131e5993bfd82180b35c079bb8ae755`) |
| Lab 05 code under test | `main` at `94a6de937729cb48aa4c17842aeace1142bb4586` |
| QA branch | `test/lab05-qa`, created from that `main` commit |
| Assignment | `lab05_resource/CSC10014_Lab05_Phan_cong_nhom_7_REVISED.md` on `docs/lab5` |
| Verification date | 2026-11-06 (Asia/Saigon) |

PR #38 (R1-R2 persistence) is merged into the code under test. PR #41 is open and mergeable at head `aa891b8` as checked on 2026-11-06; its migration and seed scripts are not yet in the integrated source. Results below do not certify a future integration commit or the `v0.5-data` release tag.

**Status meanings:** Pass = executed and matched expectation; Fail = executed and differed; Blocked = required source or integration is absent; Not run = execution has not completed.

## Test matrix

| Case | Expected | Actual | Status | Evidence | Owner if follow-up is needed |
|---|---|---|---|---|---|
| B01: Lab 04 baseline suite | `pytest -q tests` completes at `v0.4-api` | 98 passed, 1 dependency warning | Pass | `pytest-baseline.log` in the external QA run directory | — |
| R01: Lab 05 root regression suite | `pytest -q tests` completes at the QA revision | 106 passed, 1 dependency warning | Pass | `pytest-current-final.log` in the external QA run directory | — |
| R02: SQL and Python practice | Q1-Q15 score 15/15; D1-D3 tests 5/5 | Score 15/15; 5 passed | Pass | Isolated `practice` copy: `make_school_db.py`, `check.py`; `pytest -q test_school_repo.py` | — |
| P01: Valid feedback | A chat request ID accepts rating 1; HTTP 201 returns an ID | Chat 200; feedback 201 with ID 1 | Pass | Two-process Uvicorn probe | — |
| P02: Unknown request ID | HTTP 404 `unknown_request_id`; no feedback row added | 404 with expected code; database has 2 feedback rows after 2 valid submissions | Pass | Uvicorn probe and SQLite count | — |
| P03: Admin read authorization | Missing key: 401; matching `X-API-Key`: 200 | 401 without key and 200 with local test key, before and after restart | Pass | Both Uvicorn logs | — |
| P04: Ordering and limit | Newest feedback first; `limit=1` returns only the newest; `limit=10` includes both | IDs `[2, 1]` for `limit=10`; ID `[2]` for `limit=1` | Pass | Uvicorn probe | — |
| P05: App recreation regression | Feedback survives a second app instance using the same file SQLite database | 1 passed, 1 dependency warning | Pass | `tests/test_persistence_restart.py`; `pytest-restart-final.log` | — |
| P06: Real server restart | Feedback fields remain identical after stopping one Uvicorn process and starting another | Both saved feedback objects matched exactly after a new process started | Pass | Separate Uvicorn startup logs and sanitized `result.json` | — |
| P07: Data minimization | Database has no name, phone, raw message or answer column; raw session/message absent | 3 expected tables; no forbidden columns; unique raw session/message sentinels absent from SQLite bytes | Pass | SQLite schema and content probe | — |
| H01: Git hygiene | No `.db`, `.env`, credentials or caches tracked; generated DB ignored | No matching tracked paths; `.gitignore` matches `assistant.db`, `.env` and pytest cache | Pass | `git ls-files`, `git check-ignore`, `git status` | — |
| I01: Migration and 300-row seed | Clean migration, repeat run, and 300 synthetic rows | Scripts absent from `main` | Blocked | PR #41 is open at `aa891b8`; merge pending | Trung Anh / Duy |
| I02: Release verification | Re-run the matrix on the integrated commit and published tag | Integration and tag unavailable | Blocked | No `v0.5-data` tag | Duy / Quynh |

## Execution and evidence

The baseline was exported from the immutable tag into an external QA directory. Separate Python 3.12.10 environments used the versions pinned by the respective baseline and current requirements: Pydantic 2.9.2, FastAPI 0.115.0, HTTPX 0.27.2, Uvicorn 0.30.6 and pytest 8.3.3; the current environment also used SQLModel 0.0.22. Ruff 0.6.9 was run from the existing local `.venv` because PyPI retrieval of that tool failed during isolated environment setup. The Python SQLite exercise used its own generated `school.db` in an external copy, not in the repository.

The automated persistence test creates a temporary SQLite file, records a chat and feedback through one `TestClient`, then creates a new app with the same file and checks the complete feedback response and admin authorization. It verifies application recreation. The live probe below verifies a full Uvicorn process restart separately.

### Baseline and regression results

The QA artifacts and raw logs are under `C:/Users/nminh/.codex/visualizations/2026/11/03/01a1a02f-5f85-7af2-bf74-17892dfa7465/lab05-qa-run` on the review machine. They are not committed and must be recreated on another machine.

| Revision | Command | Result |
|---|---|---|
| `v0.4-api` (`a9ba3a4`) exported snapshot | `python -m pytest -q -p no:cacheprovider tests --tb=short --basetemp <external-dir>/pytest-baseline` | 98 passed, 1 Starlette/AnyIO deprecation warning, exit 0 |
| `main` (`94a6de9`) plus the new QA test | Same command with `<external-dir>/pytest-current-final` | 106 passed, 1 matching warning, exit 0 |
| New persistence test alone | `python -m pytest -q -p no:cacheprovider tests/test_persistence_restart.py --tb=short --basetemp <external-dir>/pytest-restart-final` | 1 passed, 1 matching warning, exit 0 |
| Python SQLite practice | `pytest -q test_school_repo.py -p no:cacheprovider` from `practice/` | 5 passed, exit 0 |
| SQL practice, isolated copy | `python make_school_db.py`, then `python check.py` | Q1-Q15 OK, score 15/15, exit 0 |
| New test lint | `ruff check tests/test_persistence_restart.py`; `ruff format --check tests/test_persistence_restart.py` | Both passed |

The first attempt to run the new TestClient test inside the managed sandbox stalled. The same test and both complete suites passed when run outside the sandbox. The stalled attempt is an environment limitation, not a product test failure.

### Live Uvicorn restart and SQLite inspection

At 2026-11-06 09:29 UTC, a disposable probe started Uvicorn twice on the same local port, with two distinct startup process IDs in the logs. Both processes used the same file SQLite URL, session salt and disposable admin key. The first process returned chat 200, feedback 201 twice, unknown request ID 404 with `unknown_request_id`, read without admin key 401, and authenticated reads 200. `limit=10` returned feedback IDs `[2, 1]`; `limit=1` returned `[2]`. The first process was stopped before the second started.

The second process returned 401 without the key and 200 with it. Its `limit=10` JSON matched the pre-restart list exactly, including each feedback object's `id`, `request_id`, `rating`, `comment` and `created_at`. The SQLite file contained 2 `chat_session`, 2 `interaction` and 2 `feedback` rows. Its columns were:

| Table | Columns |
|---|---|
| `chat_session` | `id`, `channel`, `created_at` |
| `interaction` | `id`, `request_id`, `session_id`, `intent`, `topic`, `resolved`, `degraded`, `latency_ms`, `created_at` |
| `feedback` | `id`, `request_id`, `rating`, `comment`, `created_at` |

No table had a name, phone, raw message or answer column. Unique synthetic raw session and message sentinels were absent from the SQLite file; this checks this run's storage only. Feedback comments remain free text and could contain personal information if a caller supplies it. The sanitized `result.json` and two Uvicorn logs are retained in the external QA directory; the admin key and raw request text are not included here.

### Git hygiene

`git ls-files` found no tracked `.db`, `.sqlite`, `.sqlite3`, `.env`, Python bytecode or cache path. `git check-ignore -v` confirmed `assistant.db`, `.env` and `.pytest_cache` are ignored. The pre-existing untracked Lab 04 tutorial PDF remains outside this QA change and is not a database or secret. No credentials or raw logs are in the QA changes.

## Integration handoff

When Trung Anh's migration/seed work reaches the integrated branch, run migrations on a clean database, run them again to check repeatability, seed 300 synthetic interactions and verify counts. After Duy merges the remaining Lab 05 work, update this report with the new SHA and re-run the complete matrix before describing a release as verified. A failure or missing input remains Fail or Blocked with its owner; it is not converted into Pass by an earlier result.
