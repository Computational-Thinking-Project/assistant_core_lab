# BUG-3: LLM answer with fabricated inline chunk citations and duplicate `source_ids` bypasses RAG grounding check

**Found by:** Đình Hùng (`@benalexx007`)   **Date:** 2026-11-26   **Severity:** major
**Where:** retrieval / AI (`src/assistant_core/llm.py`, `src/assistant_core/rag/answerer.py`)

## Steps to reproduce
1. Build the RAG-enabled service via `build_service()` over `data/kb` (`kb_dir="data/kb"`).
2. Query `"Can I register my thesis with 118 credits?"` (retrieving `H26#5.3`) with an LLM response that puts valid `source_ids: ["H26#5.3", "H26#5.3"]` in JSON while embedding an unretrieved inline citation `[H26#9.9]` inside `"answer"`.

## Expected
- Fabricated inline `[doc#section]` citations not present in retrieved `hits` are rejected with `ProviderError("answer cites sources that were not retrieved")`, retried once, and degraded safely to retrieval-only fallback (`path="retrieval"`, `degraded=True`, citing only retrieved `H26#5.3`) so `[H26#9.9]` never appears in the user answer.
- Repeated `source_ids` for grounded answers are deduplicated while preserving order.

## Actual (before fix)
- `parse_draft()` only validated `draft.source_ids` against `allowed_ids` and ignored `[doc#section]` citations inside `draft.answer`, returning `path="llm"` with `"According to [H26#9.9], students only need 90 credits..."`.
- `RagAnswerer.answer()` built `[sources[i] for i in draft.source_ids]` directly, returning duplicate `Source` entries `['H26#5.3', 'H26#5.3']`.

## Evidence
- `python -m pytest -q tests/test_my_regressions.py` on `main` (`b26e29f`) failed `2/4`: `test_citation_of_unretrieved_source_is_rejected` (`AssertionError: '[H26#9.9]' not in ...`) and `test_duplicate_source_ids_are_deduplicated_in_rag_response` (`AssertionError: ['H26#5.3', 'H26#5.3'] == ['H26#5.3']`).
- Related Week-7 citation trust / UI clarity context logged in `worksheets/user_test_observations.md`.

## Cause (after investigation)
`parse_draft()` checked only `set(draft.source_ids) <= allowed_ids` without scanning `draft.answer` for inline `[doc#section]` references, and neither `parse_draft()` nor `RagAnswerer.answer()` deduplicated `draft.source_ids`.

## Fix and regression test name
- **Mitigation 3 (`fix/lab08-hung-rag-grounding`):** Added `find_unretrieved_inline_citations()` and `source_ids` deduplication in `src/assistant_core/llm.py`, and enforced the grounding + deduplication check in `RagAnswerer.answer()` (`src/assistant_core/rag/answerer.py`).
- **Regression tests (`tests/test_my_regressions.py`):** `test_citation_of_unretrieved_source_is_rejected` and `test_duplicate_source_ids_are_deduplicated_in_rag_response`.
