# BUG-2: API accepts blank/whitespace-only, null-byte, and unbounded feedback-limit requests

**Found by:** Trương Thành Đạt (`@Thanhdat3010`)   **Date:** 2026-11-24   **Severity:** major
**Where:** API / validation (`src/assistant_api/schemas.py`, `src/assistant_api/main.py`)

## Steps to reproduce
1. Send `POST /v1/chat` with `{"message": "   \t\n  "}` or `{"message": "hello\x00world"}` or `{"message": "tuition for 18 credits", "session_id": "   "}`.
2. Send `POST /v1/feedback` with `{"request_id": "   ", "rating": 1}`, or call `GET /v1/feedback?limit=-1` with a valid `X-API-Key`.

## Expected
All blank/whitespace-only or null-byte payloads and out-of-range query bounds (`limit < 1` or `limit > 500`) are rejected at the API boundary with HTTP `422 invalid_request` without calling `AssistantService.handle()` or persisting rows to SQLite.

## Actual (before fix)
- `POST /v1/chat` with `{"message": "   \t\n  "}` returned `200 OK` (`{"answer": "empty", "intent": "unknown"}`) and recorded a spurious `interactions` row while consuming rate-limit quota.
- `POST /v1/chat` with null bytes (`"hello\x00world"`) or blank `session_id="   "` returned `200 OK`.
- `POST /v1/feedback` with blank `request_id="   "` bypassed schema validation and hit DB lookup (`404 Not Found` instead of `422`).
- `GET /v1/feedback?limit=-1` executed SQLite `LIMIT -1` (returning all rows without an upper bound).

## Evidence
- `python -m pytest -q tests/test_my_regressions.py` on `main` (`561d847`) failed `5/8` cases (`AssertionError: assert 200 == 422`, `assert 404 == 422`).
- Observed during Lab 07 Part D.4 API integration review (`docs/lab7/d4_e2e_report.md` Scenario 4 & `ui/logic.py` `validate_input` mismatch vs backend Pydantic schema).

## Cause (after investigation)
`ChatRequest` and `FeedbackIn` only enforced `Field(min_length=1, max_length=...)` on raw strings without rejecting whitespace-only strings or `\x00` null bytes, and `GET /v1/feedback` accepted an unconstrained `limit: int = 100` parameter without `Query(ge=1, le=500)`.

## Fix and regression test name
- **Mitigation 2 (`fix/88-api-input-validation`, Issue `#88`):** Added `_validate_text` `@field_validator` checks in `src/assistant_api/schemas.py` (`ChatRequest.message`, `ChatRequest.session_id`, `FeedbackIn.request_id`, `FeedbackIn.comment`) and `Query(default=100, ge=1, le=500)` on `list_feedback` in `src/assistant_api/main.py`.
- **Regression tests (`tests/test_my_regressions.py`):** `test_oversized_or_malformed_input` and `test_feedback_validation_rejects_blank_ids_and_unbounded_limits`.
