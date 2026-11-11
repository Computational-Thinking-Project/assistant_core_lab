# Lab 06 Path Comparison and Evaluation Report

**Component Owner:** Member 7 (Pham Khanh Tam - @AI-WFox)  
**Evaluation Scope:** 3-Path Architecture Benchmark (deterministic, retrieval, llm)  
**Baseline SHA:** `27fbea699d16968ceb169b795bcf979e69bc1b61`  
**Environment:** Windows 11 (10.0.26300), Python 3.13.15, AMD64  
**Date:** 2026-11-09  

---

## Benchmark Results (20 Baseline Cases E01–E20)

Evaluated via `python eval/compare_paths.py` against `eval/cases.jsonl`:

| Path | Correct | Abstain OK | p50 (ms) | Max (ms) | Failures |
|---|---|---|---|---|---|
| deterministic | 7/20 | 5/5 | 0.0 | 1.4 | E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15 |
| retrieval | 16/20 | 4/5 | 0.1 | 0.1 | E13, E14, E15, E19 |
| llm (stub) | 16/20 | 4/5 | 0.1 | 0.1 | E13, E14, E15, E19 |

---

## Part F: Path Selection Analysis

1. For answering student handbook policies, the retrieval path should be the primary production route.
2. In the measured benchmark, the retrieval path matches the accuracy of the llm (stub) path (16/20 correct and 4/5 abstains correctly handled) while running at sub-millisecond latency (p50 of 0.1 ms) and incurring zero downstream inference cost, network latency, or LLM token expenses.
3. I would prioritize fixing E19 ("is the final exam open-book") first because it represents an ungrounded false-positive response where BM25 mistakenly retrieves the medical exam absence policy (H26#7.2) due to lexical overlap with the word "exam", which should be addressed by raising the retrieval score cutoff threshold or verifying query-chunk keyword density before returning an answer.

---

## Known Failures and Characterization

The 4 failing cases (E13, E14, E15, E19) are characterized as follows:

1. **E13 (`when is tuition due` -> expected `F26#3`):** Lexical BM25 search failed because the query word "due" does not appear verbatim in `F26#3` (which uses the title "Payment deadline" and the body phrase "paid by the end of week 6"). Without a synonym thesaurus or dense semantic embeddings, exact token matching cannot bridge the vocabulary difference.
2. **E14 (`can I take 32 credits` -> expected `H26#6.1`):** The handbook section mentions allowable loads between 14 and 30 credits and requiring approval for more than 30 credits. BM25 token matching fails on the number 32 and lacks numerical range reasoning.
3. **E15 (`how long can I keep a library book` -> expected `S26#1`):** As characterized in the Lab 06 tutorial (Part F.2), the primary root cause is **router misclassification**: the presence of the word "library" triggers the deterministic office directory router, misclassifying the inquiry to the library room location (`B.201`) on the deterministic path rather than forwarding it to the knowledge base retrieval path (`S26#1`).
4. **E19 (`is the final exam open-book` -> expected abstain):** Lexical matching against the term "exam" yielded a match against `H26#7.2` ("Exam absence"), causing the system to return an irrelevant medical absence clause rather than abstaining.

---

## Targeted Integration Smoke Tests

The evaluation module includes 7 integration smoke tests in `tests/test_rag_integration_smoke.py`:
- `test_smoke_fee_calculation_is_deterministic`: Verifies case E03 returns exactly 9,450,000 VND.
- `test_smoke_office_directory_is_deterministic`: Verifies case E04 returns B.201.
- `test_smoke_student_card_replacement_retrieves_source`: Verifies case E05 retrieves policy S26#3.
- `test_smoke_out_of_scope_france_abstains`: Verifies case E16 abstains on "capital of France".
- `test_smoke_privacy_guard_intercepts_unauthorized_records`: Verifies case E18 rejects unauthorized student record inquiries.
- `test_smoke_degraded_fallback_when_llm_fails`: Verifies that downstream LLM exceptions gracefully degrade to retrieval fallback with `degraded=True` (marked `integration-pending` until production `RagAnswerer` from TV3 is merged into integration).
- `test_smoke_deterministic_path_never_answers_rules`: Verifies that deterministic path without retrieval safely abstains on handbook policy questions.
