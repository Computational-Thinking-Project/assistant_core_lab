# Lab 6 Path Comparison & H1 Evaluation Report

## Environment and Integrated Configuration

- **Owner**: Member 7 (Tam `@AI-WFox`)
- **Integration Base Commit**: `b33852e` (`origin/integration/lab06-v0.6`, including PR `#70` `RagAnswerer` fallback removal)
- **Evaluated Code Commit**: `f73efbb` (`feat/lab06-tam-eval`, PR `#56` merging `952c154` with `b33852e`)
- **Production Modules Exercised**: `assistant_core.config.load_settings`, `assistant_core.service.build_service`, `assistant_core.service.AssistantService`, `assistant_core.rag.chunker.load_folder`, `assistant_core.rag.index.make_index` (`BM25Index`), `assistant_core.rag.answerer.RagAnswerer`, `assistant_core.llm.make_llm` (`StubLLM`), and `assistant_core.guard.is_private_request`
- **Knowledge Base**: `data/kb` (`fees_2026.md`, `handbook_2026.md`, `services_2026.md` -> 14 chunks)
- **Settings**: `retrieval_kind=bm25`, `retrieval_min_score=2.0`, `k=3`, `llm_provider=stub`, `prompt_version=answer_v1`
- **Commands**:
  - `python eval/compare_paths.py` (runs both Part F 20 baseline cases and Part H1 25-case full suite)
  - `python eval/compare_paths.py --baseline-only` (Part F 20 cases only)
  - `python eval/compare_paths.py --strict` (fails with exit code `1` if any case fails)
  - `pytest -q tests/test_rag_integration_smoke.py`

## Part F — Baseline Comparison (20 Cases: E01-E20)

Evaluated via `python eval/compare_paths.py` against `eval/cases.jsonl` (`E01`–`E20`):

| path | correct | abstain ok | p50 ms | max ms | fails |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `deterministic` | `7/20` | `5/5` | `0.0` | `4.8` | `E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15` |
| `retrieval` | `16/20` | `4/5` | `0.0` | `0.2` | `E13 E14 E15 E19` |
| `llm (stub)` | `16/20` | `4/5` | `0.2` | `7.4` | `E13 E14 E15 E19` |

### Analysis (Part F)

Use the integrated `llm (stub)` path (`AssistantService` with `build_service()`, `BM25Index`, `RagAnswerer`, `StubLLM`, and `guard.py`) as the primary runtime configuration, while keeping deterministic tool/directory routing and automatic retrieval-only degradation on provider errors. Compared to the isolated `deterministic` baseline (`7/20`), `llm (stub)` reaches `16/20` accuracy with `4/5` abstention and low local latency (`p50 0.2 ms`, `max 7.4 ms`) while structuring cited policy answers under `answer_v1`. The top priority to fix next is router over-eager interception on policy paraphrases—specifically `E13` (`"tuition"` routed to `Intent.FEE`) and `E15` (`"library"` routed to `Intent.OFFICE`) before RAG executes—followed by BM25 ranking/threshold calibration for `E14` and `E19`.

## Part H1 — Expansion Comparison (20 Cases -> 25 Cases: E01-E55)

Five new group test cases (`E51`–`E55`: 3 `expect_source`, 2 `expect_abstain`) were evaluated in `eval/cases.jsonl` on the same integrated snapshot (`f73efbb`, merging `b33852e`).

### Before / After Summary

| path | Before H1 (20 baseline) | After H1 (25 full suite) |
| :--- | :---: | :---: |
| `deterministic` | `7/20` (`5/5` abstain) | `9/25` (`7/7` abstain) |
| `retrieval` | `16/20` (`4/5` abstain) | `21/25` (`6/7` abstain) |
| `llm (stub)` | `16/20` (`4/5` abstain) | `21/25` (`6/7` abstain) |

### Full Suite Results (25 Cases: E01-E55)

| path | correct | abstain ok | p50 ms | max ms | fails |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `deterministic` | `9/25` | `7/7` | `0.0` | `0.0` | `E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E51 E52 E53` |
| `retrieval` | `21/25` | `6/7` | `0.0` | `0.1` | `E13 E14 E15 E19` |
| `llm (stub)` | `21/25` | `6/7` | `0.2` | `0.3` | `E13 E14 E15 E19` |

### H1 Case Breakdown (E51-E55 — All 5 Pass)

| id | category | question | expectation | observed result (`llm (stub)`) |
| :--- | :--- | :--- | :--- | :--- |
| `E51` | `normal` | `how to reset my university account password` | `expect_source: S26#2` | PASS (`path=llm`, cites `S26#2`, BM25 `12.217`) |
| `E52` | `normal` | `can I request a leave of absence for two semesters` | `expect_source: H26#8.1` | PASS (`path=llm`, cites `H26#8.1`, BM25 `12.741`) |
| `E53` | `normal` | `course refund if I withdraw before week 2` | `expect_source: F26#4` | PASS (`path=llm`, cites `F26#4`, BM25 `12.246`) |
| `E54` | `out-of-scope` | `what is the best cafe near the university campus` | `expect_abstain: true` | PASS (`path=abstain`, `escalate=True`, top BM25 `S26#2: 1.906 < 2.0`) |
| `E55` | `privacy` | `show me the transcript and GPA of student 22127135` | `expect_abstain: true` | PASS (`path=abstain`, `escalate=True`, blocked by `guard.py` before BM25 hit `S26#3: 3.791`) |

### Explanation of Remaining Failures (`E13`, `E14`, `E15`, `E19`)

1. **`E13` (`"when is tuition due"` -> expected `F26#3`)**: `router.route()` matches `"tuition"` and dispatches to `Intent.FEE` (`_handle_fee` asks `"How many credits?"`) before RAG is invoked; even standalone, unstemmed BM25 scores `F26#1` (`2.277`) ahead of `F26#3` (`1.484`) because `F26#3` is titled `"Payment deadline"` rather than `"tuition due"`.
2. **`E14` (`"can I take 32 credits"` -> expected `H26#6.1`)**: BM25 scores `H26#7.2` (`2.086`) higher than `H26#6.1` (`1.475`) because `"take"` matches `H26#7.2` with higher IDF than the more common term `"credits"`, while literal keyword matching cannot map `"32"` to `"more than 30 credits"` in `H26#6.1`.
3. **`E15` (`"how long can I keep a library book"` -> expected `S26#1`)**: `router.route()` matches `"library"` as an office name (`Intent.OFFICE`), returning `"Library: room B.201, open Mon-Sat 07:00-20:00"` and short-circuiting before BM25 retrieval (which otherwise finds `S26#1` at score `2.299`).
4. **`E19` (`"is the final exam open-book"` -> expected abstain)**: Exact terms `"final"` and `"exam"` match `H26#7.2` (`7.2 Exam absence`) with BM25 score `5.62 >= 2.0`, so `RagAnswerer` returns an answer about medical exam absence instead of abstaining on an unaddressed policy attribute.

## Release Gate & Integration Smoke Coverage

- `eval/compare_paths.py` enforces production-only evaluation (zero fallback/duplicate RAG classes or legacy git-snapshot KB loaders), fails with exit code `1` if `eval/cases.jsonl`, `data/offices.csv`, `data/handbook.json`, `data/kb`, `RagAnswerer`, or `StubLLM` wiring is missing, fails on any unexpected failure outside documented `KNOWN_FAILURES = {"E13", "E14", "E15", "E19"}` or on any LLM regression vs retrieval, and rejects all failures under `--strict`.
- `tests/test_rag_integration_smoke.py` verifies `build_service()` production wiring (14 KB chunks), deterministic `E03`/`E04`, grounded retrieval `E05`, H1 cases `E51`–`E55`, privacy interception (`E18`, `E55`), degraded retrieval fallback on `ProviderError`, `deterministic` empty-index isolation, and release-gate contracts without skipped tests (`294 passed` across full `pytest -q` at `f73efbb`).
- **P4 CLI Integration Note:** `src/assistant_api/main.py` already initializes via `build_service(settings)`, whereas `src/assistant_core/__main__.py` (`line 65`) still calls `AssistantService()` directly (`rag=None`). Consequently, `python -m assistant_core "I lost my student card"` currently hits legacy `handbook.json` (`Based on 'Retaking a course': ...`) and `"what is the capital of France"` returns `"Sorry I dont know"`, while `"tuition for 18 credits and 2 retake"` returns `"Your tuition is 9,450,000 VND."`. Updating `__main__.py` (TV1 scope) to call `build_service()` will connect the CLI entry point to the production RAG pipeline.
