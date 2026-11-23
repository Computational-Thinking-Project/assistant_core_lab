# AI Use Log

## Lab06 individual exercise - Trung Anh / philip-kkk - 2026-11-10

- Tool: Codex. User authorized implementation and local commits only; no push.
- Branch `exercise/lab06-trunganh`, base `exercise/lab06-starter-base` at `c2677ce`.
- AI implemented S1-S3 mini-search and starter A1 abstention/A2 citation checks, added 11 parametrized RAG checks, drafted H1 E26-E30 and the comparison report.
- Verification: original mini-search 2 passed/2 failed and original RAG 13 passed/2 failed; added checks exposed 8 failures before A1/A2 were completed. Final mini-search 4 passed, RAG 26 passed, full starter 53 passed with one Starlette/AnyIO deprecation warning. Changed Python files pass Ruff check/format and diff check.
- Actual evaluation: E01-E20 deterministic 7/20 and retrieval/stub 16/20; with H1 deterministic 9/25 and retrieval/stub 21/25. E13-E15/E19 remain documented limitations; no expected outputs were changed to conceal failures.
- Full code/cases content is committed as `6b0e03e311e1a0394c454589a954890e9440ebf4`; tests ran on that same content before creating the commit. This subsequent documentation-only commit records evidence; no human verification is claimed.
- The ignored starter virtual environment reuses compatible local packages, including pinned Pydantic 2.9.2 and SQLModel 0.0.22, with its source path checked explicitly. No dependency declarations changed, downloads, API keys or network model calls were needed.
- Details and reproduction: `lab06_source_lecturer_given/starter/docs/lab6/path_comparison.md`. Root application behavior, root integration, LMS submission and release were outside this exercise.

Track AI-assisted development, prompts, generated outputs, reviews, and modifications.

| Date | Member | Tool / Model | Task / Prompt | Changes Made & Justification |
|---|---|---|---|---|
| 2026-10-19 | Bội Anh (@htbaax) | Antigravity (Gemini) | Refactor knowledge module (OfficeDirectory, Handbook) and comprehensive unit tests | Refactored monolith global state into immutable dataclasses (Office, Rule) and encapsulating directories (OfficeDirectory, Handbook) with custom exception DataError and extensive test coverage. |
| 2026-10-26 | Đạt (@Thanhdat3010) | Antigravity (Gemini) | Consult on REST API design patterns and UUID truncation tracing for FastAPI endpoint | Reviewed FastAPI request-response lifecycle, implemented endpoint delegation to AssistantService in `POST /v1/chat` with 12-char hex request_id tracing, authored Reflection H2, executed automated pytest suite with 100% pass, and verified interactive OpenAPI docs. |
| 2026-10-26 | Tâm (@AI-WFox) | Antigravity (Gemini) | Implement GET /v1/weather endpoint with failure resilience (Task T4) | Handled ExternalServiceError gracefully with HTTP 503 and `from None` suppression; verified with unit tests and mock transports. |
| 2026-10-26 | Trung Anh (@philip-kkk) | Codex | Implement Lab04 H1 office listing for issue #22 using `lab04_resource/guide.md` | Generated `OfficeDirectory.all()`, `GET /v1/offices`, and two API tests. Kept changes within the three assigned starter files and preserved existing tests. Verification and integration limits are recorded below. |
| 2026-10-27 | Trung Anh (@philip-kkk) | Codex | Update draft PR #23 after Lab04 API moved to the repository root | Resolved merge conflicts against main, moved H1 code and its two tests into root src/tests, preserved other members' endpoints and log entries, and captured actual Swagger chat/offices responses. |
| 2026-10-27 | Bội Anh (@htbaax) | Antigravity (Gemini) | Bonus Part F: Rate Limiter for /v1/chat & enable test | Implemented IP-based client rate limiting in `POST /v1/chat` raising HTTP 429 Too Many Requests when exceeding limit, unskipped test_rate_limit, and verified with pytest. |
| 2026-10-26 | Đình Hùng (@benalexx007) | Antigravity (Gemini) | Consult on FastAPI request validation and UTC timestamp serialization for Task T2 | Consulted AI on Pydantic .model_dump() unpacking syntax and UTC timezone-aware datetime conventions. Wrote and executed automated pytest suites, and manually verified interactive Swagger UI responses. |
| 2026-10-27 | Nhật Quỳnh (@nhatquynh1107) | Codex | Lab04 TV7 QA and documentation (#31) | Completed worksheets, curl assertions and QA report. Codex verified 98 pytest tests, 14 curl checks and weather mocks. The user supplied Swagger evidence, confirmed peers' screenshots and posted the PR #33 review. |
| 2026-11-02 | Duy (@johannguyen015) | Antigravity (Gemini) | Lab 05 baseline setup, scaffolding & release coordination (#40) | Initialized Lab 05 baseline on integration branch, added sqlmodel==0.0.22 and database environment configurations, scaffolded migration and seeding scripts, verified test suite, and established release plan. |
| 2026-11-02 | Đạt (@Thanhdat3010) | Antigravity (Gemini) | Consult on SQL aggregation, multi-table JOINs, and LEFT JOIN anti-join patterns for Lab 05 SQL practice (#37) | Reviewed `school.sql` relational schema (`students`, `courses`, `enrollments`), wrote and verified all 15 queries (`Q1–Q10` Must and `Q11–Q15` Should/H1) in `practice/my_answers.sql`, confirmed `Score: 15/15` via `python practice/check.py`, and ensured repository hygiene (`*.db` excluded). |
| 2026-11-03 | Đình Hùng (@benalexx007) | Antigravity (Gemini) | Implement Lab 05 Part D Python SQLite practice (D1–D3 in school_repo.py) | Implemented parameterized SQL queries in `add_student`, `average_grade`, and `transcript` using `?` placeholders to eliminate SQL injection risks. Verified 5/5 unit tests passed including injection defense test, and confirmed Q1–Q15 practice score 15/15. |
| 2026-11-04 | Bội Anh (@htbaax) | Antigravity (Gemini) | Complete Lab 05 data model worksheet and privacy review (H3 Bonus) (#42) | Analyzed 7 design anti-patterns in `bad_schema.sql`, formulated data minimization storage matrix, designed product queries, authored normalized ER diagram (Mermaid) across 3 entities, and audited PR #38 persistence code for privacy compliance. Revised after PR #43 review to clarify proposed retention lifecycle and logging/verbatim comment nuances. |
| 2026-11-06 | Nhật Quỳnh (@nhatquynh1107) | Codex | Prepare Lab 05 QA regression and persistence verification | Codex added a file-backed app recreation test and a QA report, ran baseline and current suites (98 and 106 passed), verified two real Uvicorn starts against one SQLite database, checked SQL/Python practice and Git hygiene, and documented that migration/seed and release checks await integration. These are Codex-executed checks for Quỳnh to review, not a claim of her personal execution. |
| 2026-11-07 | Nhật Quỳnh (@nhatquynh1107) | Codex | Complete integrated Lab 05 QA on `c2b7529` | Quỳnh ran regression, SQL practice, migration/seed, analytics and a manual restart probe; Codex checked the supplied results, ran a separate two-process Uvicorn probe, verified privacy and Git hygiene, and updated the QA report. The release tag remains unverified. |
| 2026-11-08 | Nhật Quỳnh (@nhatquynh1107) | Codex | Verify published `v0.5-data` release tag | Codex re-ran regression, practice, migration/seed, analytics, a two-process Uvicorn restart and Git hygiene on tagged commit `5ac4107`, then updated the QA report. Quỳnh supplied the tag details and will review the recorded results. |

## Lab05 H3 - Schema Design Review & Data Privacy (issue #42)

Author: Hà Trần Bội Anh (@htbaax) - Member 6 (TV6)

Completed the Lab 05 Data Model Worksheet in `worksheets/data_model.md` and `docs/lab5/data_model.md`:
1. Detailed critique of 7 anti-patterns in `sql/bad_schema.sql` (PII exposure, raw message retention, unnormalized intent, string timestamp, 1NF violation on feedback, string latency with units, missing primary key).
2. Data Minimization retention policy matrix ensuring zero raw message and zero student identity storage.
3. Operational query sketches mapping business questions to SQL statements.
4. Normalized Entity-Relationship diagram in Mermaid capturing `CHAT_SESSION`, `INTERACTION`, and `FEEDBACK`.
5. Codebase privacy audit of PR #38 verifying zero raw message logging and salted SHA-256 session hashing.

## Lab05 Part F and H2 - Assistant analytics

Codex helped draft and verify the four queries in `sql/my_queries.sql`.
H2 measures fallback requests as a percentage of all recorded requests for
each intent. The query file includes the measured results.

- Verified the queries against an empty database and a six-request fixture
  with known counts, latencies, ratings and fallback flags.
- Verified the migration and seed scripts first on a separate snapshot of
  PR #41, then from the analytics branch after merging `main` at `7377e7d`.
  The integrated run applied both migrations and skipped both on the second
  run. The fresh database had 300 synthetic interactions and 96 feedback
  rows, and passed SQLite integrity and foreign-key checks. All four query
  outputs matched an independent calculation from the seeded rows.
- Ran the integrated branch's existing pytest suite: 105 passed, with one
  dependency deprecation warning.

## Lab04 H1 - Office listing (issue #22)

Codex implemented the sorted directory method, connected the route to
`service.offices.all()`, and added two tests using the existing client fixture.
The tests check HTTP 200, the public JSON fields, the presence of Library,
and alphabetical ordering. No other member's endpoints were implemented.

Verification performed by Codex before the code commits:

- Six direct directory checks passed, including empty input and the sample CSV.
- HTTP checks passed for office listing, empty and supplied directories,
  health, and OpenAPI registration; external weather requests were mocked.
- The two new offices API tests passed.
- The starter suite reported 21 passed, 4 failed, and 1 skipped. The same four
  failures existed before these changes: unimplemented T1, T2, and T4 handlers.
  The skipped test is the existing rate-limit bonus test.
- The separate Lab03 regression suite reported 87 passed.
- Ruff checks passed for `knowledge.py` and `test_api.py`; formatting checks
  passed for all three changed Python files. The seven pre-existing Ruff
  diagnostics in the API `main.py` remained unchanged, with no new diagnostics.

API tests required execution outside the sandbox because TestClient stalled
inside it; the same health test passed outside. A separate starter virtual
environment used the existing pinned requirements without changing dependency
declarations. Imports were checked against the starter sources, not the
separate Lab03 package at the repository root.

The full API suite and lint are not yet green. Integration, the required
Swagger chat screenshot, and the contributor's own H2 reflection remain
pending; this log does not claim they have been completed.

### Integration update - 2026-10-27 (PR #23)

The notes above describe the original starter implementation on October 26.
After main moved the API to the repository root, Codex moved the H1 method,
route, and unchanged tests to root `src/` and `tests/`. The reference starter
now matches main; no duplicate H1 implementation remains there.

- Offices, chat, and health tests: 5 passed.
- Root suite: 94 passed, 3 failed, 1 skipped. An independent snapshot of main
  at `f9126c2` gives 92 passed and the same 3 failures and 1 skip. Failures are
  the existing T2 feedback handler and two T4 weather cases, outside H1.
- Ruff passes for root `knowledge.py` and `test_api.py`; all three changed
  Python files pass formatting. Root `src tests` still has 5 inherited lint
  diagnostics (4 in API main and 1 in core service).
- Actual Swagger requests on the local API returned HTTP 200: POST chat
  answered "Your tuition is 9,450,000 VND."; GET offices returned four sorted
  offices, including Library, with name/room/hours. Screenshots are saved as
  `docs/evidence/philip-kkk-swagger-chat.jpg` and
  `docs/evidence/philip-kkk-swagger-offices.jpg`.

Codex performed these checks; no human verification or full-suite success is
claimed. H2 remains for the contributor to write in their own words. The
remaining team endpoints, bonus, and baseline lint are not implemented by
this H1 update. No dependency declarations were changed.

## Lab05 Setup - Baseline, Scaffolding and Environment Configuration (issue #40)

Tech Lead Duy (@johannguyen015) established the foundational project scaffolding for Lab 05:
- Added `sqlmodel==0.0.22` dependency to `pyproject.toml` and `requirements.txt`.
- Configured persistence runtime settings (`database_url`, `session_salt`) in `assistant_core/config.py` and `.env.example`.
- Placed initial migration scripts (`scripts/migrate.py`, `scripts/seed.py`) and schema DDL (`sql/migrations/001_init.sql`, `002_add_faq.sql`, `sql/bad_schema.sql`, `sql/my_queries.sql`).
- Added Python SQLite practice templates (`practice/school_repo.py`, `practice/test_school_repo.py`) and design worksheet (`worksheets/data_model.md`).
- Verified baseline test suite pass and ensured clean git hygiene.
