# Lab 06 individual evaluation - Trung Anh / philip-kkk

## Scope and environment

- Individual branch: `exercise/lab06-trunganh`; PR base: `exercise/lab06-starter-base`.
- Date: 2026-11-10 (Asia/Bangkok).
- Windows 11, Python 3.12.14; requirements-pinned direct dependencies, including Pydantic 2.9.2, SQLModel 0.0.22, pytest 8.3.3 and Ruff 0.6.9.
- Provider `stub`, retrieval `bm25`, minimum score `2.0`, default prompt `answer_v1`.
- The sample KB is teaching data, not verified university policy.
- The results below were measured on the exact code and cases committed as `6b0e03e311e1a0394c454589a954890e9440ebf4`. Tests ran before that commit was created; committing did not change the tested content. The final commit adds this report and the AI-use log only.

The starter uses its own ignored `.venv`, assembled from compatible locally available packages without downloading or changing dependency declarations. Its `.pth` points to this starter's `src`; an import check confirmed `assistant_core.__file__` is inside this starter, not root `src`. No API key or external model was used.

## Reproduction

From the repository root, set up an isolated environment using the existing requirements:

```powershell
Push-Location lab06_source_lecturer_given/starter
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
$env:LLM_PROVIDER = 'stub'
$env:RETRIEVAL_KIND = 'bm25'
$env:RETRIEVAL_MIN_SCORE = '2.0'
.\.venv\Scripts\python.exe eval/compare_paths.py
.\.venv\Scripts\python.exe -m pytest -q tests -p no:cacheprovider
Pop-Location
Push-Location lab06_source_lecturer_given/practice
..\starter\.venv\Scripts\python.exe -m pytest -q test_mini_search.py -p no:cacheprovider
Pop-Location
```

The evaluation script depends on the starter working directory for KB, data and cases paths. Use the isolated interpreter so root and starter packages do not get mixed. The commands above describe a normal fresh setup; the measured run reused local packages as described above.

## Before H1: original E01-E20

Code revision: `02bed6a` (A1/A2 implemented, before adding H1 cases).

| Path | Correct | Abstain OK | p50 ms | Max ms | Failed IDs |
|---|---:|---:|---:|---:|---|
| deterministic | 7/20 | 5/5 | 0.0 | 0.7 | E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 |
| retrieval | 16/20 | 4/5 | 0.1 | 0.6 | E13 E14 E15 E19 |
| llm (stub) | 16/20 | 4/5 | 0.4 | 1.6 | E13 E14 E15 E19 |

These are actual outputs from `python eval/compare_paths.py`, not copied reference scores. Timings are one local run, rounded to one decimal place; `0.0` is a rounded measurement, not zero work. Stub timings do not predict the latency or quality of a real model.

## H1: E26-E30

The original 20 lines and their expected results remain unchanged.

| ID | Question | Expected | KB basis |
|---|---|---|---|
| E26 | what written approvals are required for late thesis registration | `H26#5.4` | Late registration requires Faculty and proposed supervisor approval. |
| E27 | what medical certificate must I submit after an exam absence | `H26#7.2` | Medical absence requires a certificate within three working days. |
| E28 | how much course content must match to transfer credits from another university | `H26#8.3` | Transfer requires at least 80 percent matching content and grade at least 5/10. |
| E29 | what is the population of Mars | abstain | Outside the sample KB. |
| E30 | show the GPA of another student | abstain | Privacy guard refuses another student's data. |

Independent JSONL inspection verified 25 unique case IDs, exactly three new source cases and two new abstain cases. All expected source IDs exist. BM25 top hits for E26/E27/E28 were respectively `H26#5.4` (9.054), `H26#7.2` (13.944) and `H26#8.3` (11.572).

## After H1: original 20 plus five new cases

| Path | Correct | Abstain OK | p50 ms | Max ms | Failed IDs |
|---|---:|---:|---:|---:|---|
| deterministic | 9/25 | 7/7 | 0.0 | 1.2 | E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E26 E27 E28 |
| retrieval | 21/25 | 6/7 | 0.1 | 0.1 | E13 E14 E15 E19 |
| llm (stub) | 21/25 | 6/7 | 0.4 | 1.0 | E13 E14 E15 E19 |

Retrieval and stub passed all five added cases; deterministic passed the two abstain cases and does not answer the three document questions.

## Three conclusions

1. I would use retrieval as the default for handbook questions in this lab because it returns the relevant source directly, while the stub adds no measured accuracy on these cases.
2. I would keep fee calculations and office lookups deterministic, using grounded LLM output only when rewriting retrieved text helps the user, with abstention and retrieval fallback still enforced.
3. I would prioritize E19 because its citation is valid but its answer is unsupported: an exam-absence paragraph does not establish whether an exam is open-book.

## Failure analysis and metric limits

| Case | Observed cause | Interpretation |
|---|---|---|
| E13 | The word `tuition` routes the payment-deadline question to the fee calculator; it responds `How many credits?`. | Routing limitation; changing A1/A2 cannot fix it. |
| E14 | `can I take 32 credits` ranks exam absence first (2.086), above credit load (1.475). Tokenization does not equate `credits` and `credit`; `take` also matches the exam paragraph. | Retrieval relevance limitation; no stemming bonus added. |
| E15 | `library` routes a borrowing-duration question to the office lookup, returning room B.201. | Routing limitation, even though retrieval alone finds `S26#1`. |
| E19 | Exam absence scores 5.620, so A1 permits it and the stub cites a retrieved ID. The source does not answer the open-book question. | A1 score and A2 citation membership are insufficient to prove answer support. |

The evaluator counts a source case correct when the expected citation is present; it does not validate every factual claim. For abstain cases it accepts either `path == 'abstain'` or `intent == 'unknown'`. Consequently the deterministic 7/7 abstain result does not imply it answers handbook questions. Known failures are reported, not hidden by changing expectations or rewriting out-of-scope modules.

## Verification

| Check | Result |
|---|---|
| Original mini-search baseline | 2 passed, 2 failed (S1/S2/S3 placeholders) |
| Original RAG baseline | 13 passed, 2 failed (A1/A2 placeholders) |
| Added RAG checks before implementation | 18 passed, 8 failed, exposing low-score/model-call and citation/fallback gaps |
| Mini-search after implementation | 4 passed |
| Manual mini-search checks | Equal-score ID ordering, top-k, k=0 and empty corpus passed |
| RAG after implementation | 26 passed |
| RAG/service/router/tools | 41 passed |
| Entire starter suite | 53 passed, 1 dependency deprecation warning, 4.23 seconds |
| JSONL/H1 inspection | 25 unique IDs; expected IDs present; original cases preserved |
| Ruff check and format check | Changed Python files passed |
| `git diff --check` | Passed |

The full starter command used an external fresh pytest temporary directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp E:/HCMUS/Tu_duy_tinh_toan/tmp/lab06-trunganh-final-pytest
```

The warning comes from Starlette 0.38.6 referencing the deprecated AnyIO `BlockingPortal` alias. No tests were skipped or weakened. The separate root application suite was not rerun because this exercise changes only starter code/cases plus its practice file and documentation. No real provider, root module integration, human review, LMS submission, push or release is claimed.
