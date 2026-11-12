# AI Use Log

## Lab06 group retrieval - Trung Anh / philip-kkk - 2026-11-10

- Tool: Codex. The user authorized implementation and local commits; no push or GitHub mutation was performed.
- Branch: `feat/lab06-trunganh-retrieval`, base `integration/lab06-v0.6` at `27fbea699d16968ceb169b795bcf979e69bc1b61`.
- Ported lecturer-style Markdown chunking, metadata/section IDs and BM25 retrieval into root `src/assistant_core/rag/`. Existing legacy `knowledge.py`, service, router, API, settings and database code remain unchanged.
- Added three unchanged sample KB fixtures under `tests/fixtures/lab06/kb/`, sourced from `sources/lab6` at `839efd2c70df6d45d5e3c95909d8b219aba982be`. Their bytes were compared with the Git source before commit. These are teaching samples, not verified university policy or runtime KB owned by another member.
- Tests are self-contained on this branch; they do not require the exercise branch, root `data/kb`, a model or a network connection. The root interpreter's `assistant_core.__file__` was checked against root `src`, not the separate exercise starter.
- The existing root virtual environment was completed using locally available SQLModel 0.0.22/SQLAlchemy/greenlet packages from the exercise environment; Pydantic remains 2.9.2. No dependency declarations were modified and no downloads were needed.

### Contracts and usage

```python
from pathlib import Path

from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index

# Standalone check using this PR's sample fixtures:
chunks = load_folder(Path("tests/fixtures/lab06/kb"))
index = make_index("bm25", chunks)
hits = index.search("can I register my thesis with 118 credits", k=3)
assert hits[0].chunk.id == "H26#5.3"

# Application wiring after the KB owner's files are integrated:
# index = make_index("bm25", load_folder(Path("data/kb")))
```

`Chunk(id, doc_id, title, text, version, owner)` and `Hit(chunk, score)` are frozen dataclasses. `Index.search(query, k=3)` returns positive-score hits ordered by descending BM25 score, with input order retained on ties. IDs remain `doc_id#section`; loading sorts file names and preserves section order. Empty/no-match queries, empty/all-stopword corpora and nonpositive limits return `[]`. BM25 tokenization, scoring and three-decimal output follow the lecturer baseline; no stemming, embeddings, TF-IDF or hybrid retrieval is added. `make_index` explicitly raises `ValueError` for unsupported kinds. Scores rank documents; the answerer's A1 owns the relevance threshold and abstention decision.

### Verification and evidence

All commands below run from the repository root using `.venv/Scripts/python.exe`:

| Check | Command / method | Result |
|---|---|---|
| Chunking commit `7bc41f4` | `python -m pytest -q tests/test_rag_index.py -p no:cacheprovider` | 7 passed |
| Complete retrieval module | Same targeted command, fresh external `--basetemp` | 23 passed |
| Lecturer compatibility | Compared 8 queries at k=1,3,20 against the lecturer BM25 implementation from Git | All 24 source-ID/score comparisons matched; thesis top `H26#5.3`, score 4.914 |
| Root regression | `python -m pytest -q -p no:cacheprovider --basetemp E:/HCMUS/Tu_duy_tinh_toan/tmp/lab06-retrieval-final` | 129 passed, 1 dependency warning, 4.61 seconds |
| Ruff | `python -m ruff check src/assistant_core/rag tests/test_rag_index.py` | Passed |
| Formatting | `python -m ruff format --check src/assistant_core/rag tests/test_rag_index.py` | 4 files already formatted |
| Diff hygiene | `git diff --check` | Passed |

The 23 module tests cover sample metadata and 14 unique sections, exact source IDs, filename/section order, flat frontmatter/Windows newlines, empty documents, thesis ranking, top-k and score order, no-match queries, nonpositive k, empty/all-stopword corpora, equal-score ordering, multi-term relevance, tokenizer behavior and unsupported kinds. The count of 14 is asserted only for the sample fixtures, not hardcoded in implementation.

Initial baseline runs had 105 passed and one failure in the existing persistence test during HTTPX initialization: first an unsupported environment proxy scheme, then an inaccessible environment `SSLKEYLOGFILE` path. The persistence test passed in isolation when those variables were removed from the test subprocess environment; the final full regression used the same process-local environment cleanup. No application code or existing test was changed to work around these environment issues. All API tests remain local; no external request was made. The remaining warning is Starlette's deprecated AnyIO `BlockingPortal` alias.

The final full regression was run on the exact code/tests content committed as `d4c4e29`; creating that commit changed no tested bytes. This subsequent documentation-only commit records the results. The standalone module is verified; integration with other members' answerer/service/runtime KB, human review and release are not claimed. Reviewer: Dat (TV3). Downstream consumers: Dat's answerer and Duy's service.

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
| 2026-11-09 | Đạt (@Thanhdat3010) | Antigravity (Gemini) | Implement Lab 06 Response contract extension and official RagAnswerer module | Consulted AI for Python type hint syntax and Pydantic field defaults. Wrote, tested, and benchmarked all code and evaluation cases independently. |
| 2026-11-10 | Bội Anh (@htbaax) | Antigravity (Gemini) | Lab 06 Knowledge Base integration & Deterministic Privacy Guard (TV5) | Ported 3 sample Markdown Knowledge Base files into `data/kb/` (14 chunks total) with metadata intact. Implemented deterministic `is_private_request` guard and `PRIVATE_REPLY` in `src/assistant_core/guard.py` covering grades, GPA, phone, address, email, and 8-digit student IDs, with unit tests in `tests/test_guard.py`. Service wiring and integrated verification remain pending in PR #52. |
| 2026-11-11 | Đình Hùng (@benalexx007) | Antigravity (Gemini) | Lab 06 TV4 REST API ChatResponse contract extension and Lab 4-5 regression tests | Added additive `escalate`, `path`, and `confidence` fields to `ChatResponse` in `src/assistant_api/schemas.py`, documented them in `docs/api_contract.md`, added targeted API/DB tests in `tests/test_api.py` covering legacy defaults, abstain, grounded `llm`, and degraded `retrieval` responses, and verified full API/DB/persistence regression suite. |

## Lab06 TV5 - Knowledge Base Integration & Privacy Guard

Author: Hà Trần Bội Anh (@htbaax) - Member 5 (TV5)

1. **Markdown Knowledge Base (`data/kb/`):**
   - Integrated the 3 sample university policy files from the lecturer starter: `fees_2026.md`, `handbook_2026.md`, and `services_2026.md`.
   - Verified that metadata frontmatter (`doc_id`, `title`, `version`, `owner`) is fully intact and correctly produces exactly 14 chunks (`F26#1`–`F26#4`, `H26#4.2`–`H26#8.3`, `S26#1`–`S26#3`).
   - Legacy `data/handbook.json` and `data/offices.csv` remain completely untouched for backward compatibility.
   - Clarified that the Markdown files represent teaching/mock data and not verified university policy.

2. **Deterministic Privacy Guard (`src/assistant_core/guard.py`):**
   - Implemented `is_private_request(text: str) -> bool` and `PRIVATE_REPLY` to intercept inquiries requesting grades, scores, GPA, phone numbers, addresses, emails, or third-party student IDs / student numbers.
   - Evaluates queries deterministically via compiled regular expressions covering complete student records keywords (`grade`, `score`, `gpa`, `result`, `phone`, `address`, `email`, `mail`, `contact`, `student id`, `student number`, `id number`, `mssv`, `id`) with explicit word boundaries (`\b`), preventing false positives on words like `ideas` or `identify`.
   - Distinctly differentiates personal record inquiries from published rule / eligibility questions (e.g., *"Can my friend register a thesis with GPA 2.0?"*, *"What GPA does a classmate need for thesis?"*), ensuring curriculum and handbook rule inquiries pass through to retrieval.
   - Guarantees strict precedence for explicit third-party private record requests: general eligibility or policy wording in the query cannot override an explicit request for another student's record (e.g., *"What is the GPA of another student? I need it to check eligibility."*, *"What grade did my friend get? I need the minimum for a scholarship."*, *"What is another student phone number for eligibility?"* remain strictly blocked).
   - Accurately covers academic fields coupled with `for` and third-party targets (e.g., *"Show me the GPA for another student"*, *"What is the score for my friend?"*), ensuring that explicit requests for another person's actual record or imperative retrieval commands take precedence over trailing eligibility action wording (e.g., *"Show me the actual GPA for another student to register a thesis"*, *"Give me the actual score for my friend to pass the course"* remain strictly blocked), while preserving general policy inquiries (e.g., *"what is my GPA requirement for the thesis"*, *"What is the minimum GPA for another student to take thesis?"*, *"What is the GPA for another student to register a thesis?"*).
   - **Integration Boundary:** This PR provides and verifies the standalone guard predicate contract (`is_private_request`, `PRIVATE_REPLY`). The end-to-end service wiring (calling the guard before retrieval and model execution in `AssistantService`) and integrated private request tests are owned by and remain pending in PR #52.
   - **Pattern Limitations:** The guard relies on deterministic keyword/regex heuristics and does not claim semantic coverage of all possible unstructured PII queries.

3. **Automated Verification:**
   - Authored `tests/test_guard.py` with 34 positive PII cases (including academic fields with `for`, explicit actual record requests with eligibility action wording, third-party student ID/number inquiries, possessive forms, email, and mixed private/policy wording regression checks), 31 negative policy and eligibility regression cases, refusal content verification, regex pattern structure validation, and runtime KB structure validation (69 passed).
   - Executed full repository regression across Labs 01–06 (212 passed).

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
