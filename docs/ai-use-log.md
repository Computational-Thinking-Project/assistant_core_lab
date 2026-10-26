# AI Use Log

Track AI-assisted development, prompts, generated outputs, reviews, and modifications.

| Date | Member | Tool / Model | Task / Prompt | Changes Made & Justification |
|---|---|---|---|---|
| 2026-10-19 | Bội Anh (@htbaax) | Antigravity (Gemini) | Refactor knowledge module (OfficeDirectory, Handbook) and comprehensive unit tests | Refactored monolith global state into immutable dataclasses (Office, Rule) and encapsulating directories (OfficeDirectory, Handbook) with custom exception DataError and extensive test coverage. |
| 2026-10-26 | Trung Anh (@philip-kkk) | Codex | Implement Lab04 H1 office listing for issue #22 using `lab04_resource/guide.md` | Generated `OfficeDirectory.all()`, `GET /v1/offices`, and two API tests. Kept changes within the three assigned starter files and preserved existing tests. Verification and integration limits are recorded below. |

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
