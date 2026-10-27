# AI Use Log

Track AI-assisted development, prompts, generated outputs, reviews, and modifications.

| Date | Member | Tool / Model | Task / Prompt | Changes Made & Justification |
|---|---|---|---|---|
| 2026-10-19 | Bội Anh (@htbaax) | Antigravity (Gemini) | Refactor knowledge module (OfficeDirectory, Handbook) and comprehensive unit tests | Refactored monolith global state into immutable dataclasses (Office, Rule) and encapsulating directories (OfficeDirectory, Handbook) with custom exception DataError and extensive test coverage. |
| 2026-10-26 | Đạt (@Thanhdat3010) | Antigravity (Gemini) | Consult on REST API design patterns and UUID truncation tracing for FastAPI endpoint | Reviewed FastAPI request-response lifecycle, implemented endpoint delegation to AssistantService in `POST /v1/chat` with 12-char hex request_id tracing, authored Reflection H2, executed automated pytest suite with 100% pass, and verified interactive OpenAPI docs. |
| 2026-10-27 | Bội Anh (@htbaax) | Antigravity (Gemini) | Bonus Part F: Rate Limiter for /v1/chat & enable test | Implemented IP-based client rate limiting in `POST /v1/chat` raising HTTP 429 Too Many Requests when exceeding limit, unskipped test_rate_limit, and verified with pytest. |
