# Lab 6 — Path Comparison & Evaluation Report

**Student:** Trương Thành Đạt (`@Thanhdat3010`) — MSSV: `25127035`  
**Team:** Team 7 (TV3 — Đạt)  
**Branch:** `exercise/lab06-thanhdat` (Base: `exercise/lab06-starter-base`)  
**Repository:** [Computational-Thinking-Project/assistant_core_lab](https://github.com/Computational-Thinking-Project/assistant_core_lab)  

---

## 1. Baseline Evaluation (20 Cases: E01–E20)

Command executed:
```bash
python eval/compare_paths.py
```

### Raw Output Table
```text
path                correct  abstain ok  p50 ms  max ms
deterministic          7/20       5/5     0.0     1.0   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15
retrieval             16/20       4/5     0.1     0.2   fails: E13 E14 E15 E19
llm (stub)            16/20       4/5     0.3     0.8   fails: E13 E14 E15 E19
```

### Formatted Comparison Table
| Path | Correct /20 | Abstain correct /5 | p50 latency | Controllability (1–5) | Main failure mode |
|---|:---:|:---:|:---:|:---:|---|
| **deterministic** | 7/20 | 5/5 | 0.0 ms | 5/5 | Hardcoded rules cannot answer handbook/policy questions (`E01`, `E02`, `E05`–`E15`). |
| **retrieval** | 16/20 | 4/5 | 0.1 ms | 4/5 | Quotes verbatim chunks; fails on router keyword conflicts or vocabulary mismatches (`E13`, `E14`, `E15`, `E19`). |
| **llm (stub)** | 16/20 | 4/5 | 0.3 ms | 4/5 | Depends on retrieval quality; produces structured answers but inherits retrieval/router failures (`E13`, `E14`, `E15`, `E19`). |

---

## 2. Three Conclusions (Part E)

1. **Which path to ship for handbook questions:** For official student handbook and university policy queries, I would ship the **`llm` path with A2 citation grounding and A1 pre-retrieval abstention** (backed by `retrieval` as an automatic degraded fallback), because it delivers concise answers while strictly constraining every claim to retrieved official chunks.
2. **Why:** Both `retrieval` and `llm (stub)` achieve `16/20` on the baseline (`21/25` with H1) compared to only `7/20` for `deterministic` rules, while A1 (`hits[0].score < min_score`) blocks out-of-scope and privacy-violating queries before any LLM call is made.
3. **One failure to fix first:** I would prioritize fixing the router keyword conflict on **E13** (`"when is tuition due"`, expected `F26#3`) and **E15** (`"how long can I keep a library book"`, expected `S26#1`): currently `router.py` routes any query containing `"tuition"` to `Intent.FEE` and `"library"` to `Intent.OFFICE`, bypassing RAG completely. Refining `route()` so policy/deadline questions fall through to `Intent.RULE` (RAG) while keeping numeric credit calculations on `Intent.FEE` resolves both cases without risking LLM arithmetic.

---

## 3. Homework H1 — Five Additional Test Questions (E31–E35)

Added 5 test cases to `eval/cases.jsonl`:
- **3 Normal Questions (verified against official sample KB chunks):**
  - `E31`: `"how many semesters can I take a leave of absence"` → `expect_source`: `"H26#8.1"` (Handbook §8.1)
  - `E32`: `"approval needed for late thesis registration"` → `expect_source`: `"H26#5.4"` (Handbook §5.4)
  - `E33`: `"what is the deadline for submitting a medical certificate after exam absence"` → `expect_source`: `"H26#7.2"` (Handbook §7.2)
- **2 Questions with Expected Abstention (`expect_abstain: true`):**
  - `E34`: `"who painted the mona lisa"` → Out-of-scope question with zero relevance to university handbook (`abstain`).
  - `E35`: `"show the GPA of student 25127001"` → Privacy guard violation attempting to access another student's record (`abstain`).

### Re-run Output Table (25 Cases: E01–E20 + E31–E35)
```text
path                correct  abstain ok  p50 ms  max ms
deterministic          9/25       7/7     0.0     0.7   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E31 E32 E33
retrieval             21/25       6/7     0.0     0.1   fails: E13 E14 E15 E19
llm (stub)            21/25       6/7     0.2     0.6   fails: E13 E14 E15 E19
```

### Analysis of H1 Results
All 5 newly added test cases (`E31`–`E35`) passed on both `retrieval` and `llm (stub)` paths (accuracy rose from `16/20` to `21/25`, and abstention rose from `4/5` to `6/7`). Specifically, `E31`–`E33` retrieved the exact target chunks (`H26#8.1`, `H26#5.4`, `H26#7.2`), `E34` abstained prior to calling the LLM due to BM25 score `< 2.0` (`A1`), and `E35` was blocked immediately by the privacy guard before retrieval.
