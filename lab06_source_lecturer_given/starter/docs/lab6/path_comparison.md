# Lab 6 — Three Assistant Paths

## 1. Baseline Comparison (`eval/cases.jsonl` — 20 cases: E01–E20)

Command executed in `lab06_source_lecturer_given/starter/`:

```text
python eval/compare_paths.py
```

| Path | Correct /20 | Abstain correct /5 | p50 latency | max latency | Controllability (1–5) | Main failure mode |
|---|---|---|---|---|---|---|
| deterministic | 7/20 | 5/5 | 0.0 ms | 0.7 ms | 5 | Cannot answer handbook/policy questions (fails: E01, E02, E05–E15) |
| retrieval | 16/20 | 4/5 | 0.0 ms | 0.2 ms | 4 | Lexical mismatch, router trap, and no semantic abstain on E19 (fails: E13, E14, E15, E19) |
| llm (provider: stub) | 16/20 | 4/5 | 0.2 ms | 0.8 ms | 4 | Inherits top-1 retrieval errors and cannot judge semantic insufficiency on E19 (fails: E13, E14, E15, E19) |

### Three Sentences (Path Choice & Priority Fix)

1. For handbook and policy questions, I would ship the **`llm` path** (with A1 abstain threshold, A2 citation grounding, and retrieval-only degraded fallback) alongside deterministic handlers for exact fee calculation and office directory lookups.
2. Unlike `deterministic` (`7/20`), `llm` answers `16/20` cases cleanly with grounded citations (`0.2 ms` median with `StubLLM`) while enforcing strict schema and fallback safety if the model fails or invents sources.
3. The first failure I would fix is **`E15`** (`"how long can I keep a library book"`), because `router.py` naively routes any query containing `"library"` to `Intent.OFFICE` instead of letting policy questions about library borrowing rules reach retrieval (`S26#1`).

---

## 2. H1 Re-run Comparison (`E01`–`E20` + `E36`–`E40` — 25 cases)

Added 5 original cases in `eval/cases.jsonl`:
- `E36`: `"when does thesis registration open and close"` (`expect_source: "H26#5.3"`, normal)
- `E37`: `"what grade is required for transfer credits"` (`expect_source: "H26#8.3"`, normal)
- `E38`: `"how do I reset my university account password online"` (`expect_source: "S26#2"`, normal)
- `E39`: `"what is my classmate's phone number"` (`expect_abstain: true`, privacy)
- `E40`: `"can I apply for a master scholarship"` (`expect_abstain: true`, out-of-scope)

Command executed in `lab06_source_lecturer_given/starter/`:

```text
python eval/compare_paths.py
```

| Path | Correct /25 | Abstain correct /7 | p50 latency | max latency | Fails |
|---|---|---|---|---|---|
| deterministic | 9/25 | 7/7 | 0.0 ms | 0.5 ms | E01, E02, E05, E06, E07, E08, E09, E10, E11, E12, E13, E14, E15, E36, E37, E38 |
| retrieval | 20/25 | 6/7 | 0.0 ms | 0.1 ms | E13, E14, E15, E19, E36 |
| llm (provider: stub) | 20/25 | 6/7 | 0.2 ms | 0.6 ms | E13, E14, E15, E19, E36 |

### Analysis of New Cases & Failures

- **Passed (4/5):** `E37` (`H26#8.3`), `E38` (`S26#2`), `E39` (blocked by privacy guard as abstain), and `E40` (abstained safely due to out-of-scope keywords) all passed on both `retrieval` and `llm (stub)`.
- **Why `E36` failed:** Without stemming, BM25 did not match `"open"`/`"close"` in the query against `"opens"`/`"closes"` in `H26#5.3`, so shorter chunk `H26#5.4` ("Late thesis registration", score `4.439`) outranked `H26#5.3` (score `4.318`), causing top-1 retrieval and `StubLLM` to cite `H26#5.4` instead of `H26#5.3`.

---

## 3. H2 — Reflection

Asking an AI directly is like a closed-book exam where a confident student might guess a wrong rule from memory.
With RAG, our system first uses code to search our official handbook for the exact relevant paragraphs—turning it into an open-book exam.
We hand only those retrieved paragraphs to the model and instruct it to answer strictly from that page or say "I don't know."
Unlike the model, our Python code explicitly enforces guardrails the AI skips: A1 refuses before calling the model if retrieval scores are too low (`hits[0].score < self.min_score`), and A2 (`parse_draft`) rejects any answer whose `source_ids` are empty or outside the retrieved `allowed_ids`.
This keeps the assistant verifiable, predictable, and honest when the documents do not contain an answer.

