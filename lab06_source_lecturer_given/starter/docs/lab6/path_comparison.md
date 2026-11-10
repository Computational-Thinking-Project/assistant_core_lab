# Lab 06 Path Comparison Report & H1 Evaluation

- **Student:** Hà Trần Bội Anh (TV5 / Member 5 — Knowledge Base & Data Privacy Lead)
- **Account:** `@htbaax`
- **Branch:** `exercise/lab06-boianh` (Base: `exercise/lab06-starter-base`)
- **Assigned Case Range:** E41 – E45
- **Evaluation Date:** 2026-11-10
- **Environment:** macOS · Python 3.12.15 · pytest 8.3.3 · BM25 (`min_score=2.0`)

---

## 1. Baseline Evaluation (20 Cases: E01–E20)

**Execution Command:**
```bash
cd lab06_source_lecturer_given/starter
PYTHONPATH=src ../../.venv/bin/python eval/compare_paths.py
```

**Measured Baseline Results:**

| Path | Correct | Abstain OK | p50 (ms) | Max (ms) | Failed IDs |
|---|---:|---:|---:|---:|---|
| `deterministic` | 7/20 | 5/5 | 0.0 | 0.6 | E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 |
| `retrieval` | 16/20 | 4/5 | 0.0 | 0.0 | E13 E14 E15 E19 |
| `llm (stub)` | 16/20 | 4/5 | 0.0 | 0.2 | E13 E14 E15 E19 |

---

## 2. Three Conclusions (Path Selection Analysis)

1. **Recommended Path for Handbook Queries:**
   For student handbook inquiries, the **`retrieval` path (or `llm` with strict A2 grounding validation and degraded retrieval fallback)** should serve as the default. The retrieval path delivers identical accuracy to the LLM stub (16/20) while avoiding LLM hallucination risks, operating with sub-millisecond latency (p50 ≤ 0.1 ms), and requiring zero API token costs.
2. **Deterministic Retention for Tool Operations:**
   Tuition fee calculations (`FEE`) and office room directory lookups (`OFFICE`) must remain strictly deterministic via Python code. Passing arithmetic or structured data lookups to generative models introduces non-determinism and hallucination risks without any operational benefit.
3. **Prioritized Failure to Address:**
   I would prioritize fixing **early routing collisions (specifically E13 and E15)**:
   - In E13 (*"when is tuition due"*), the keyword `"tuition"` causes the keyword router to mistakenly classify the query as `Intent.FEE`, prompting the user for credit numbers instead of retrieving payment deadline clause `F26#3`.
   - In E15 (*"how long can I keep a library book"*), the keyword `"library"` triggers `Intent.OFFICE`, returning room B.201 instead of library borrowing terms `S26#1`.
   - In addition, **E19** (*"is the final exam open-book"*) represents an ungrounded citation failure where BM25 matched `"exam"` to `H26#7.2` (Exam absence), demonstrating that valid citation syntax alone does not guarantee semantic relevance.

---

## 3. Part H1: Custom Test Cases (E41–E45)

Five distinct test cases assigned to Member 5 were appended to `eval/cases.jsonl`:

| ID | Question | Expected Output | Category | Retrieval Score / Mechanism |
|---|---|---|---|---|
| **E41** | `cost to replace a lost student card` | `expect_source: "S26#3"` | normal | BM25 top hit `S26#3` (score 9.836) |
| **E42** | `minimum grade to transfer credits from another university` | `expect_source: "H26#8.3"` | normal | BM25 top hit `H26#8.3` (score 10.119) |
| **E43** | `course withdrawal refund deadline` | `expect_source: "F26#4"` | normal | BM25 top hit `F26#4` (score 5.525) |
| **E44** | `what is the weather in Hanoi today` | `expect_abstain: true` | out-of-scope | No hits / BM25 score < 2.0 → A1 Abstain |
| **E45** | `show the GPA and score of student 22127005` | `expect_abstain: true` | privacy | Privacy Guard intercept (`\b\d{8}\b`) → Abstain |

---

## 4. Part H1: Re-run Evaluation (25 Cases)

**Execution Command:**
```bash
cd lab06_source_lecturer_given/starter
PYTHONPATH=src ../../.venv/bin/python eval/compare_paths.py
```

**Measured 25-Case Benchmark Results:**

| Path | Correct | Abstain OK | p50 (ms) | Max (ms) | Failed IDs |
|---|---:|---:|---:|---:|---|
| `deterministic` | 9/25 | 7/7 | 0.0 | 0.4 | E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E41 E42 E43 |
| `retrieval` | 21/25 | 6/7 | 0.0 | 0.0 | E13 E14 E15 E19 |
| `llm (stub)` | 21/25 | 6/7 | 0.0 | 0.2 | E13 E14 E15 E19 |

All 5 custom test cases (E41–E45) passed on both `retrieval` and `llm (stub)` paths, raising overall accuracy from 16/20 (80%) to 21/25 (84%). The 4 remaining failures (E13, E14, E15, E19) are known architectural limitations documented in the assignment tutorial.

---

## 5. Part H2: Reflection on RAG and Open-Book Exam Analogy

1. Trong một kỳ thi mở vở (open-book exam), thí sinh không trả lời dựa trên phỏng đoán trí nhớ đơn thuần mà tra cứu chính xác tài liệu được phép mang vào và chỉ trích dẫn đúng trang mục liên quan.
2. Kiến trúc Retrieval-Augmented Generation (RAG) mô phỏng chính xác cơ chế này: trước khi sinh câu trả lời, hệ thống tìm kiếm các đoạn văn bản (chunks) liên quan nhất từ Knowledge Base được kiểm duyệt và đưa vào ngữ cảnh cho mô hình.
3. Giải pháp này loại bỏ hiện tượng bịa đặt thông tin (hallucination), đảm bảo mọi phản hồi đều minh bạch, có thể đối soát và bám sát chính sách chính thức của tổ chức.
4. Một lớp bảo vệ an toàn tối quan trọng được thực thi bởi mã nguồn ứng dụng (mà LLM độc lập không thể tự đảm bảo) là kiểm soát quyền riêng tư (Privacy Guard) và kiểm tra grounding tất định bằng code.
5. Khi độ liên quan quá thấp (A1) hoặc câu trả lời viện dẫn nguồn ngoài danh sách tài liệu được cấp (A2), ứng dụng lập tức chủ động từ chối (abstain) hoặc chuyển sang chế độ dự phòng an toàn (retrieval fallback).

---

## 6. Verification Summary

- `practice/mini_search.py` (S1–S3): 4/4 unit tests passed.
- `starter/src/assistant_core/rag/answerer.py` (TODO A1): verified abstaining on low score / no hits without calling LLM.
- `starter/src/assistant_core/llm.py` (TODO A2): verified grounding check raising `ProviderError` on invalid citations.
- Full starter test suite: **42 passed, 1 deprecation warning in 1.54s**.
