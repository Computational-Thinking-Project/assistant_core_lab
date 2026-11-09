# BÁO CÁO ĐÁNH GIÁ SO SÁNH BA PATHS VÀ H1 EVALUATION (LAB 06)

- **Thành viên thực hiện:** Nguyễn Bá Duy (TV1 / Member 1)
- **Nhánh cá nhân:** `exercise/lab06-duy` (Base: `exercise/lab06-starter-base`)
- **Ngày thực hiện:** 09/11/2026
- **Base commit SHA:** `c2677ce9cfcd8b913b99bf60011b5247ee88249d`
- **Môi trường chạy:** Windows 11 · Python 3.14.8 · BM25 (`min_score=2.0`)

---

## 1. Bảng số liệu thực nghiệm đo được trên 25 test cases (E01–E25)

**Lệnh thực thi:**
```powershell
Set-Location lab06_source_lecturer_given/starter
$env:PYTHONPATH="src"
python eval/compare_paths.py
```

**Kết quả chạy thực tế:**

| Path | Correct | Abstain OK | p50 latency (ms) | max latency (ms) | Fails |
|---|---|---|---|---|---|
| `deterministic` | 9/25 | 7/7 | 0.0 | 0.4 | E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E22 E23 |
| `retrieval` | 21/25 | 6/7 | 0.0 | 0.1 | E13 E14 E15 E19 |
| `llm (stub)` | 21/25 | 6/7 | 0.1 | 0.3 | E13 E14 E15 E19 |

---

## 2. Danh sách 5 câu hỏi bổ sung H1 của cá nhân Duy (E21–E25)

Được bổ sung trực tiếp vào `eval/cases.jsonl`:

| ID | Câu hỏi | Kỳ vọng | Category | Kết quả thực tế |
|---|---|---|---|---|
| **E21** | `how many books can a student borrow` | `expect_source: "S26#1"` | normal | **PASS** (Match `S26#1`, score = 5.585) |
| **E22** | `how to replace a lost student card` | `expect_source: "S26#3"` | normal | **PASS** (Match `S26#3`, score = 9.836) |
| **E23** | `can I request a leave of absence for two semesters` | `expect_source: "H26#8.1"` | normal | **PASS** (Match `H26#8.1`, score = 4.887) |
| **E24** | `who will win the world cup championship` | `expect_abstain: true` | out-of-scope | **PASS** (BM25 score < 2.0 → abstain trước LLM) |
| **E25** | `what is the email address of student 22127001` | `expect_abstain: true` | privacy | **PASS** (BM25 score < 2.0 → abstain trước LLM) |

Tất cả 5/5 test cases của Duy đều vượt qua trên cả path `retrieval` và `llm (stub)`.

---

## 3. Ba câu hỏi kết luận theo yêu cầu PDF

1. **Chọn path nào cho handbook tra cứu quy chế?**
   - Lựa chọn tối ưu là **path `llm` có ràng buộc Grounding (A2) kết hợp fallback degraded `retrieval` và cơ chế Abstain sớm (A1)**. Nếu môi trường offline/CI không có provider LLM thực, path `retrieval` là baseline hoàn toàn tin cậy vì trích dẫn trực tiếp nguồn đã được xác thực từ tài liệu chính thức.
2. **Lý do lựa chọn?**
   - Path `deterministic` hoàn toàn thất bại với câu hỏi quy chế (chỉ đạt 9/25, trượt toàn bộ các câu hỏi handbook).
   - Path `retrieval` và `llm (stub)` đạt độ chính xác cao (21/25 = 84%), phản hồi tức thì (p50 ≤ 0.1 ms), và có cơ chế A1 bảo vệ: khi câu hỏi ngoài phạm vi (như E16, E17, E24) hoặc liên quan đến dữ liệu cá nhân (E18, E25), hệ thống chủ động abstain ngay lập tức mà không gọi LLM suy đoán bừa bãi.
3. **Lỗi nào cần ưu tiên khắc phục nhất?**
   - Cần ưu tiên khắc phục **lỗi xung đột định tuyến sớm giữa Router và RAG (cụ thể là E13 và E15)**:
     - E13 ("when is tuition due") chứa từ khóa `"tuition"` nên Router định tuyến nhầm sang `FEE` (công cụ tính học phí số học), dẫn đến trả về câu hỏi yêu cầu nhập số tín chỉ thay vì tra cứu hạn đóng học phí trong quy chế tài chính `F26#3`.
     - E15 ("how long can I keep a library book") chứa từ khóa `"library"` nên Router định tuyến nhầm sang `OFFICE` (trả về phòng B.201) thay vì tra cứu quy định mượn sách thư viện `S26#1`.
     - Cần bổ sung quy tắc phân biệt câu hỏi tra cứu thông tin (có chứa từ để hỏi *when, how long, how many*) với câu hỏi tra cứu địa điểm hoặc tính toán tiền.

---

## 4. Phân tích chi tiết một trường hợp thất bại (Failure Analysis)

- **Test Case:** E13 (`"when is tuition due"`, `expect_source: "F26#3"`)
- **Nguyên nhân gốc rễ:**
  - Trong `src/assistant_core/router.py`, hàm `route` thực hiện so khớp chuỗi:
    ```python
    if "fee" in m or "tuition" in m:
        return Intent.FEE
    ```
  - Khi người dùng hỏi `"when is tuition due"`, từ `"tuition"` lập tức kích hoạt `Intent.FEE`.
  - Bộ xử lý `_handle_fee` gọi `parse_credits("when is tuition due")`, không tìm thấy con số tín chỉ nào nên trả về `"How many credits?"`.
  - Toàn bộ pipeline RAG (vốn có thể dễ dàng tìm ra đoạn `F26#3`: *"Tuition must be paid by the end of week 6..."*) bị bypass hoàn toàn.
- **Giải pháp đề xuất:**
  - Tinh chỉnh Router để phân biệt: chỉ chuyển sang `Intent.FEE` khi câu hỏi có chứa số tín chỉ hoặc từ khóa tính toán (như `"calculate"`, `"cost for"`, số nguyên kèm `"credits"`), hoặc nếu `parse_credits` trích xuất được 0 tín chỉ thì fallback chuyển tiếp sang RAG/handbook search để tra cứu quy chế học phí thay vì mặc định hỏi lại tín chỉ.
