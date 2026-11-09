# Lab 6 — Path Comparison & Evaluation Report

**Student:** Trương Thành Đạt (`@Thanhdat3010`) — MSSV: `25127035`  
**Team:** Team 7 (TV3 — Đạt)  
**Repository:** [Computational-Thinking-Project/assistant_core_lab](https://github.com/Computational-Thinking-Project/assistant_core_lab)  

---

## 1. Baseline Evaluation (20 Cases: E01–E20)

Command executed:
```bash
python eval/compare_paths.py
```

### Raw Output Table
```
path                correct  abstain ok  p50 ms  max ms
deterministic          7/20       5/5     0.0     1.0   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15
retrieval             16/20       4/5     0.1     0.2   fails: E13 E14 E15 E19
llm (stub)            16/20       4/5     0.3     0.8   fails: E13 E14 E15 E19
```

### Formatted Comparison Table
| Path | Correct /20 | Abstain correct /5 | p50 latency | Controllability (1–5) | Main failure mode |
|---|:---:|:---:|:---:|:---:|---|
| **deterministic** | 7/20 | 5/5 | 0.0 ms | 5/5 | Hardcoded rules cannot answer handbook/policy questions (`E01`, `E02`, `E05`–`E15`). |
| **retrieval** | 16/20 | 4/5 | 0.1 ms | 4/5 | Quotes verbatim chunks; fails on vocabulary mismatches or ambiguous queries (`E13`, `E14`, `E15`, `E19`). |
| **llm (stub)** | 16/20 | 4/5 | 0.3 ms | 4/5 | Depends on retrieval quality; produces structured answers but inherits retrieval failures (`E13`, `E14`, `E15`, `E19`). |

---

## 2. Three Conclusions

1. **Which path to ship for handbook questions:** For official student handbook and university policy queries, I would ship the **LLM (with RAG and strict grounding checks)** path in production (with the deterministic retrieval path acting as an automated degraded fallback), because it provides clear, user-friendly natural language responses while explicitly grounding each claim in verified source chunks.
2. **Why:** The retrieval and LLM paths dramatically outperform deterministic rules (achieving 16/20 vs 7/20 correct on baseline cases), as students formulate inquiries using diverse phrasings that deterministic regexes cannot anticipate, whereas RAG safely constrains model generation to official document sections.
3. **One failure to fix first:** The first failure I would fix is **E15** (`"how long can I keep a library book"`): currently, the keyword router prematurely classifies any query containing `"library"` as an office location inquiry and answers with the room number (`B.201`), which can be rectified by refining routing rules so that loan duration and borrowing queries are directed to the campus services handbook (`S26#1`).

---

## 3. Homework H1 — Five Additional Test Questions (E31–E35)

Added 5 test cases to `eval/cases.jsonl`:
- **3 Normal Questions (verified against official sample KB chunks):**
  - `E31`: `"how many semesters can I take a leave of absence"` → `expect_source`: `"H26#8.1"` (Handbook §8.1)
  - `E32`: `"approval needed for late thesis registration"` → `expect_source`: `"H26#5.4"` (Handbook §5.4)
  - `E33`: `"what is the deadline for submitting a medical certificate after exam absence"` → `expect_source`: `"H26#7.2"` (Handbook §7.2)
- **2 Questions with Expected Abstention (`expect_abstain: true`):**
  - `E34`: `"who painted the mona lisa"` → Out-of-scope question with zero relevance to university handbook.
  - `E35`: `"show the GPA of student 25127001"` → Privacy guard violation attempting to access another student's record.

### Re-run Output Table (25 Cases: E01–E20 + E31–E35)
```
path                correct  abstain ok  p50 ms  max ms
deterministic          9/25       7/7     0.0     0.7   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E31 E32 E33
retrieval             21/25       6/7     0.0     0.1   fails: E13 E14 E15 E19
llm (stub)            21/25       6/7     0.2     0.6   fails: E13 E14 E15 E19
```

### Analysis of Results
All 5 newly introduced test cases (`E31`–`E35`) passed successfully on both retrieval and LLM paths (overall accuracy increased from 16/20 to 21/25), and abstention accuracy reached 6/7 (both `E34` and `E35` correctly abstained, leaving only the intentional baseline ambiguity case `E19` failing to abstain).

---

## 4. Homework H2 — Reflection (5 Lines)

1. A standard language model takes a **closed-book exam**, answering purely from memory and statistical weights, which easily leads to plausible-sounding hallucinations and fabricated figures.
2. In contrast, **RAG transforms the task into an open-book exam**: our code first searches our official knowledge base (`data/kb/`), retrieves the exact governing section, and provides it to the model with strict instructions to answer *only* from that text or abstain.
3. Crucially, the model cannot verify its own grounding; our application code enforces a **Grounding Check (A2)** by asserting `set(draft.source_ids) <= allowed_ids`.
4. If the model attempts to invent an imaginary policy section or cite documents not in the retrieved context, our code rejects the response and falls back to quoting the verified source directly.
5. In addition, our code applies **Pre-retrieval Abstention (A1)**: if search scores fall below our threshold (`hits[0].score < min_score`), we refuse the question immediately without ever calling the model, preventing hallucination while eliminating unnecessary latency and API cost.

---

## 5. Bonus H3 — Analysis of Failure E14 (Tokenization & Stemming)

We inspected **E14** (`"can I take 32 credits"`), which fails to match `H26#6.1` (`"Credit load"`) because the query uses the plural `"credits"` while the section title uses singular `"Credit"`.
- We tested modifying `tokenize` in `src/assistant_core/rag/index.py` to strip a trailing `"s"` from tokens longer than 4 characters: `t[:-1] if len(t) > 4 and t.endswith("s") else t`.
- Upon re-running evaluation, **E14 still failed** because the query term `"take"` (which is not in stop words) appears in `H26#7.2` (`"Approved students take the exam..."`). Since `"take"` appears in only 1 chunk in the entire corpus, its BM25 Inverse Document Frequency (IDF) score is exceptionally high (`2.086`), which outweights `"credit"` (`1.425`).
- This confirms that simple heuristic suffix stripping alone cannot resolve term competition when an incidental query word carries higher corpus rarity than the core domain term, demonstrating the real-world need for query expansion or intent-weighted scoring.
