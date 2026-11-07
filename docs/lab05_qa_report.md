# Lab 05 QA: Regression and Persistence Verification

Owner: Nhat Quynh (Member 7). QA execution and report preparation: Codex, for owner review.

## Revision and scope

| Item | Revision or source |
|---|---|
| Lab 04 baseline | `v0.4-api` (`a9ba3a416131e5993bfd82180b35c079bb8ae755`) |
| Lab 05 integrated base | `main` at `bf0d779cff2f754b590785be3b91ba03528e5cef` |
| QA source under test | `test/lab05-qa` at `c2b75294023dc11aefbec3e576a59a6597d4bfda` (includes integrated `main`) |
| Assignment | `lab05_resource/CSC10014_Lab05_Phan_cong_nhom_7_REVISED.md` on `docs/lab5` at `23fa47a` |
| Verification date | 2026-11-07 (Asia/Saigon) |

PRs #38 (persistence), #41 (migration and seed), and #47 (analytics) are merged into the base above. QA PR #46 remains open. The tests below certify the integrated source plus the QA test at `c2b7529`. No remote `v0.5-data` tag existed at the final check on 2026-11-07, so the release tag is not certified.

**Status meanings:** Pass = executed and matched expectation; Fail = executed and differed; Blocked = required source or integration is absent; Not run = execution has not completed.

## Test matrix

| Case | Expected | Actual | Status | Evidence | Owner if follow-up is needed |
|---|---|---|---|---|---|
| B01: Lab 04 baseline suite | `pytest -q tests` completes at `v0.4-api` | 98 passed, 1 dependency warning | Pass | `pytest-baseline.log` in the external QA run directory | — |
| R01: Lab 05 root regression suite | `pytest -q tests` completes at the integrated QA revision | 106 passed, 1 Starlette/AnyIO deprecation warning | Pass | Owner-run PowerShell transcript at `c2b7529`; command reproduced below | — |
| R02: SQL and Python practice | Q1-Q15 score 15/15; D1-D3 tests 5/5 | Score 15/15; 5 passed | Pass | Owner-run `make_school_db.py`, `check.py`, and practice pytest at `c2b7529` | — |
| P01: Valid feedback | A chat request ID accepts rating 1; HTTP 201 returns an ID | Chat 200; feedback 201 with ID 1 | Pass | Two-process Uvicorn probe | — |
| P02: Unknown request ID | HTTP 404 `unknown_request_id`; no feedback row added | 404 with expected code; database has 2 feedback rows after 2 valid submissions | Pass | Uvicorn probe and SQLite count | — |
| P03: Admin read authorization | Missing key: 401; matching `X-API-Key`: 200 | 401 without key and 200 with local test key, before and after restart | Pass | Both Uvicorn logs | — |
| P04: Ordering and limit | Newest feedback first; `limit=1` returns only the newest; `limit=10` includes both | IDs `[2, 1]` for `limit=10`; ID `[2]` for `limit=1` | Pass | Uvicorn probe | — |
| P05: App recreation regression | Feedback survives a second app instance using the same file SQLite database | Included in the integrated 106/106 passing suite; previously passed alone | Pass | `tests/test_persistence_restart.py`; owner-run integrated suite and earlier `pytest-restart-final.log` | — |
| P06: Real server restart | Feedback fields remain identical after stopping one Uvicorn process and starting another | Integrated probe: Uvicorn log PIDs 30768 and 35920; feedback JSON matched across processes | Pass | Separate Uvicorn startup logs and sanitized `result.json` in `manual-e7bd26b88f` | — |
| P07: Data minimization | Interaction persistence excludes student identity, raw session/message and generated answer content | API persistence tables have the expected columns; raw session/message sentinels are absent from SQLite bytes | Pass | Integrated restart SQLite schema and content probe | — |
| H01: Git hygiene | No `.db`, `.env`, credentials or caches tracked; generated DB ignored | No matching tracked paths; `.gitignore` matches `assistant.db`, `.env` and pytest cache | Pass | `git ls-files`, `git check-ignore`, `git status` | — |
| I01: Migration and 300-row seed | Clean migration, repeat run, and 300 synthetic rows | Both migrations applied, then skipped; 300 interactions, 96 feedback, integrity `ok`, no foreign-key errors | Pass | Owner-run temporary SQLite database; Codex read-only count/integrity recheck | — |
| A01: Assistant analytics | F1-F3 and H2 execute against the seeded database and match recorded results | All four queries matched the results in `sql/my_queries.sql` | Pass | Owner-run SQL output; Codex read-only H2 recheck | — |
| I02: Release verification | Re-run the matrix on the integrated commit and published tag | Integrated QA passed at `c2b7529`; QA PR #46 and release tag are still pending | Blocked | `git ls-remote origin refs/tags/v0.5-data` returned no tag | Duy (merge/tag), Quynh (tag check) |

## Execution and evidence

The baseline was exported from the immutable tag into an external QA directory. Separate Python 3.12.10 environments used the versions pinned by the respective baseline and current requirements: Pydantic 2.9.2, FastAPI 0.115.0, HTTPX 0.27.2, Uvicorn 0.30.6 and pytest 8.3.3; the integrated environment also used SQLModel 0.0.22. Ruff 0.6.9 was run from the existing local `.venv` for the earlier QA revision because PyPI retrieval failed during isolated environment setup. The earlier Python SQLite exercise used an external copy; the integrated owner run generated an ignored `practice/school.db` in the repository.

The automated persistence test creates a temporary SQLite file, records a chat and feedback through one `TestClient`, then creates a new app with the same file and checks the complete feedback response and admin authorization. It verifies application recreation. The live probe below verifies a full Uvicorn process restart separately.

### Baseline and regression results

The QA artifacts and raw logs are under `C:/Users/nminh/.codex/visualizations/2026/11/03/01a1a02f-5f85-7af2-bf74-17892dfa7465/lab05-qa-run` on the review machine. They are not committed and must be recreated on another machine.

| Revision | Command | Result |
|---|---|---|
| `v0.4-api` (`a9ba3a4`) exported snapshot | `python -m pytest -q -p no:cacheprovider tests --tb=short --basetemp <external-dir>/pytest-baseline` | 98 passed, 1 Starlette/AnyIO deprecation warning, exit 0 |
| `main` (`94a6de9`) plus the new QA test | Same command with `<external-dir>/pytest-current-final` | 106 passed, 1 matching warning, exit 0 |
| Integrated `main` (`bf0d779`) plus QA test (`c2b7529`) | `python -m pytest -q tests` | 106 passed, 1 Starlette/AnyIO deprecation warning; owner-run PowerShell transcript |
| New persistence test alone | `python -m pytest -q -p no:cacheprovider tests/test_persistence_restart.py --tb=short --basetemp <external-dir>/pytest-restart-final` | 1 passed, 1 matching warning, exit 0 |
| Python SQLite practice, integrated QA revision | `python -m pytest -q practice/test_school_repo.py` | 5 passed; owner-run PowerShell transcript |
| SQL practice, integrated QA revision | `python practice/make_school_db.py`, then `python practice/check.py` | Q1-Q15 OK, score 15/15; owner-run PowerShell transcript |
| New test lint | `ruff check tests/test_persistence_restart.py`; `ruff format --check tests/test_persistence_restart.py` | Both passed |

The first attempt to run the new TestClient test inside the managed sandbox stalled. The same test and both complete suites passed when run outside the sandbox. The stalled attempt is an environment limitation, not a product test failure.

### Integrated migration, seed and analytics

The owner ran `scripts/migrate.py` twice and `scripts/seed.py <temp-db> 300` on a new database outside the repository at `C:/Users/nminh/AppData/Local/Temp/lab05-qa-final-20261107-183143/assistant-seeded.db`. The first migration run applied `001_init.sql` and `002_add_faq.sql`; the second skipped both. Read-only reinspection found 2 version rows, 59 hashed chat sessions, 300 interactions, 96 feedback rows and an empty FAQ table. `PRAGMA integrity_check` returned `ok`; `PRAGMA foreign_key_check` returned no rows. The empty FAQ table is expected because the seed generates interactions and feedback, not curated FAQ content. The seed was run only once against this database.

The owner ran all four statements from `sql/my_queries.sql` against the same database. The recorded outputs were:

| Query | Result |
|---|---|
| F1 requests | rule 140; fee 61; office 47; greeting 26; unknown 26 |
| F2 average latency (ms) | fee 5.1; greeting 2.4; office 3.4; rule 76.2; unknown 8.1 |
| F3 thumbs-down by known topic | H26-4.2: 8; H26-5.3: 8; H26-7.2: 2 |
| H2 fallback rate | rule 34/140 (24.3%); greeting 2/26 (7.7%); office 1/47 (2.1%); fee 1/61 (1.6%); unknown 0/26 (0.0%) |

The owner's pasted H2 output was truncated, so Codex re-read H2 from the same temporary SQLite database before marking A01 Pass. The results match the query file's recorded values. This is a real SQLite check, not a mock or a claim about a shared release database.

### Integrated Uvicorn restart and SQLite inspection

The owner first ran a manual two-terminal probe on the integrated QA revision. It returned chat 200, feedback 201, unauthorized admin read 401, unknown request ID 404, and newest-first feedback IDs `[2, 1]` with `limit=1` returning `[2]`. The final comparison of `id`, `request_id`, `rating`, `comment` and `created_at` passed after restart. Initial PowerShell 5.1 assertions failed because the commands wrapped a JSON array as one object; parsing with `ConvertFrom-Json -InputObject` corrected the test harness. Those assertion errors are not recorded as API failures.

Codex then ran an independent disposable probe at `c2b7529` outside the managed sandbox. The first Uvicorn process was stopped before the second started on the same loopback port and SQLite file. Their startup logs report distinct server PIDs **30768** and **35920**. Both pre-restart feedback objects matched exactly after restart. The probe also confirmed chat 200, feedback 201, unknown ID 404, missing admin key 401, authenticated read 200, newest-first IDs `[2, 1]` and `limit=1` returning `[2]`. The SQLite file contained 2 sessions, 2 interactions and 2 feedback rows, with integrity `ok` and no foreign-key errors. The synthetic raw session and message sentinels were absent from the file bytes.

The sanitized `result.json` and two raw Uvicorn logs are under the external QA run directory at `manual-e7bd26b88f/`; they are not committed. The result file distinguishes Python launcher PIDs from the actual Uvicorn startup PIDs reported by the logs. The disposable admin key and request text are not included in the report. The first sandboxed attempt to run this integrated probe could not reach its loopback server; the same probe succeeded outside the sandbox.

The earlier baseline probe on 2026-11-06 remains historical evidence for the pre-integration revision and is not used to certify the integrated revision.

The API persistence tables have only the expected columns: `chat_session` (`id`, `channel`, `created_at`), `interaction` (`id`, `request_id`, `session_id`, `intent`, `topic`, `resolved`, `degraded`, `latency_ms`, `created_at`), and `feedback` (`id`, `request_id`, `rating`, `comment`, `created_at`). They have no direct student name, phone, raw message or generated answer column. Migration 002 separately creates an empty `faq` table with `question` and `answer` columns for curated staff content; its `answer` column is not an interaction transcript. Feedback comments remain free text and could contain personal information if a caller supplies it; the synthetic probes did not test redaction.

### Git hygiene

At `c2b7529`, `git ls-files` found no tracked `.db`, `.sqlite`, `.sqlite3`, `.env`, Python bytecode or cache path. `git check-ignore -v` confirmed `assistant.db`, the generated `practice/school.db`, `.env` and pytest cache are ignored. The pre-existing untracked Lab 04 tutorial PDF remains outside this QA change and is not a database or secret. No credentials or raw logs are in the QA changes.

## Integration handoff

Migration, seed, analytics, regression and restart have now passed on the integrated QA source `c2b7529`. QA PR #46 still needs review and merge. Duy owns the subsequent `v0.5-data` tag. Once the tag exists, compare its SHA with the merged source and re-run the required suite on that exact tag before marking I02 Pass or calling the release verified. A missing tag remains Blocked; success on `c2b7529` does not certify a future tag.
