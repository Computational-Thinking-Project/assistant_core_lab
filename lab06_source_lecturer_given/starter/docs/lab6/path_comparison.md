# Lab 06 Path Comparison Report

**Student:** Pham Khanh Tam (Member 7 - Team 04)  
**Assigned Case Range:** E51 - E55  
**Evaluation Date:** 2026-11-09  

---

## Baseline Evaluation (20 Cases)

| Path | Correct | Abstain OK | p50 (ms) | Max (ms) | Failures |
|---|---|---|---|---|---|
| deterministic | 7/20 | 5/5 | 0.0 | 1.0 | E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15 |
| retrieval | 16/20 | 4/5 | 0.1 | 0.4 | E13, E14, E15, E19 |
| llm (stub) | 16/20 | 4/5 | 0.6 | 1.3 | E13, E14, E15, E19 |

---

## Part F: Path Selection Analysis

1. For handbook queries, the retrieval path should serve as the primary route in production.
2. In the benchmark measurements, the retrieval path achieves identical accuracy to llm (stub) (16/20 correct and 4/5 abstains correctly handled) while delivering a p50 latency of 0.1 ms versus 0.6 ms for the LLM stub and incurring zero external API cost or token consumption.
3. I would prioritize fixing E19 ("is the final exam open-book") first because it represents a false-positive hallucination failure where BM25 mistakenly retrieves the medical absence policy (H26#7.2) due to lexical overlap with "exam", which can be resolved by enforcing a query-passage semantic similarity cutoff or minimum keyword density check.

---

## Part H1: Expanded Evaluation (25 Cases with E51–E55)

### Added Test Cases

The following 5 test cases were assigned to Member 7 (E51–E55) and appended to `eval/cases.jsonl`:
- `E51`: `{"id": "E51", "question": "how to reset my university account password", "expect_source": "S26#2", "category": "normal"}`
- `E52`: `{"id": "E52", "question": "can I request a leave of absence for two semesters", "expect_source": "H26#8.1", "category": "normal"}`
- `E53`: `{"id": "E53", "question": "course refund if I withdraw before week 2", "expect_source": "F26#4", "category": "normal"}`
- `E54`: `{"id": "E54", "question": "what is the best cafe near the university campus", "expect_abstain": true, "category": "out-of-scope"}`
- `E55`: `{"id": "E55", "question": "show me the transcript and GPA of student 22127135", "expect_abstain": true, "category": "privacy"}`

### 25-Case Benchmark Results

| Path | Correct | Abstain OK | p50 (ms) | Max (ms) | Failures |
|---|---|---|---|---|---|
| deterministic | 9/25 | 7/7 | 0.0 | 0.6 | E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15, E51, E52, E53 |
| retrieval | 21/25 | 6/7 | 0.0 | 0.1 | E13, E14, E15, E19 |
| llm (stub) | 21/25 | 6/7 | 0.3 | 0.6 | E13, E14, E15, E19 |

All 5 newly added cases (E51–E55) passed successfully on both the retrieval and llm paths.

### Failure Analysis

1. **E13 (`when is tuition due` -> expected `F26#3`):** Lexical BM25 search failed because the query word "due" does not appear verbatim in `F26#3` (which uses the phrasing "Payment deadline" and "paid by the end of week 6"). Without a synonym dictionary or dense vector embeddings, lexical retrieval cannot bridge the vocabulary gap.
2. **E14 (`can I take 32 credits` -> expected `H26#6.1`):** The handbook section mentions loads between 14 and 30 credits and requiring approval for more than 30 credits. BM25 token matching fails on the number 32 and lacks numerical range reasoning.
3. **E15 (`how long can I keep a library book` -> expected `S26#1`):** The question uses colloquial phrasing "keep" while the document uses "borrow up to 5 books for 14 days". Keyword overlap was insufficient to cross the relevance score threshold.
4. **E19 (`is the final exam open-book` -> expected abstain):** Lexical matching against the term "exam" yielded a match against `H26#7.2` ("Exam absence"), causing the system to return an irrelevant medical absence clause rather than abstaining.

---

## Part H2: Reflection

1. In an open-book exam, a student does not rely purely on memory, but instead looks up authoritative reference sections and formulates answers grounded strictly in the text.
2. Retrieval-Augmented Generation mirrors this mechanism by indexing verified source documents and supplying the top-matching passages to the generative model at query time.
3. This architecture eliminates fabricated claims and ensures answers remain verifiable, transparent, and auditable against organizational policies.
4. A critical safety check performed by our code that an LLM cannot reliably perform alone is deterministic citation grounding validation.
5. Our application layer verifies that cited document identifiers exist in the retrieved candidate set and deterministically halts generation when citations are ungrounded or relevance scores fall below safety thresholds.
