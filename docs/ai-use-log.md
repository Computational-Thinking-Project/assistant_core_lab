# AI Use Log

## 2026-10-23 - Thanhdat3010 - Lab03 H1 and H3

Contributor: Truong Thanh Dat. Tool: Codex, Antigravity.

Codex generated the initial help-command prototype and test scaffolding (Issue #18).
Dat reviewed the implementation, identified router and CLI limitations, and added three personal improvements:
1. Expanded help alias matching (`-h`, `--help`, `guide`) across public and fallback routers.
2. Replaced live responder mutation with constructor dependency injection (`NeverResponder`) to guarantee provider isolation.
3. Added CLI flag verification tests (`-h`, `--help`) and audited JSON logging privacy to prevent raw message leaks.

All 104 tests pass locally with pinned dependencies; Ruff checks clean. Completed Lab03 H1 review and H3 architectural reflection.

Track AI-assisted development, prompts, generated outputs, reviews, and modifications.

| Date | Member | Tool / Model | Task / Prompt | Changes Made & Justification |
|---|---|---|---|---|
| 2026-10-19 | Bội Anh (@htbaax) | Antigravity (Gemini) | Refactor knowledge module (OfficeDirectory, Handbook) and comprehensive unit tests | Refactored monolith global state into immutable dataclasses (Office, Rule) and encapsulating directories (OfficeDirectory, Handbook) with custom exception DataError and extensive test coverage. |
| 2026-10-23 | Thành Đạt (@Thanhdat3010) | Codex / Antigravity | Extend assistant with help command and AI review (H1/H3) | Reviewed AI prototype, added help aliases, ensured test provider isolation, verified log privacy, and completed worksheets. |
