# AI Use Log

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
