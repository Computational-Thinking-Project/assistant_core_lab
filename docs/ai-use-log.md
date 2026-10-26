# AI Use Log

Track AI-assisted development, prompts, generated outputs, reviews, and modifications.

| Date | Member | Tool / Model | Task / Prompt | Changes Made & Justification |
|---|---|---|---|---|
| 2026-10-19 | Bội Anh (@htbaax) | Antigravity (Gemini) | Refactor knowledge module (OfficeDirectory, Handbook) and comprehensive unit tests | Refactored monolith global state into immutable dataclasses (Office, Rule) and encapsulating directories (OfficeDirectory, Handbook) with custom exception DataError and extensive test coverage. |
| 2026-10-26 | Tâm (@AI-WFox) | Antigravity (Gemini) | Implement GET /v1/weather endpoint with failure resilience (Task T4) | Handled ExternalServiceError gracefully with HTTP 503 and `from None` suppression; verified with unit tests and mock transports. |
