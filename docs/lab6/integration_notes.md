# LAB 06 — INTEGRATION NOTES & BASELINE LOG (PHASE P0 / TV1 DUY)

- **Owner:** Nguyễn Bá Duy (TV1 / Member 1 - Tech Lead)
- **Feature Branch:** `feat/lab06-duy-service`
- **Target Integration Base:** `integration/lab06-v0.6`
- **Baseline Commit (main):** `27fbea699d16968ceb169b795bcf979e69bc1b61`
- **Ngày ghi nhận:** 09/11/2026
- **Môi trường:** Windows 11 · Python 3.14.8 · pytest 9.1.1

---

## 1. Kết quả kiểm tra Baseline (Phase P0 Gate)

Thực hiện kiểm tra hồi quy toàn diện trên commit `27fbea699d16968ceb169b795bcf979e69bc1b61`:

```powershell
python -m pytest -q
```

- **Kết quả baseline:** **106 passed**, 0 failed (2.84s).
- **Phạm vi bảo toàn:** Toàn bộ test suite của Lab 3, Lab 4 (FastAPI REST endpoints, rate limiting, weather client) và Lab 5 (SQLite persistence, feedback roundtrip, interaction audit logs) hoạt động hoàn hảo.

---

## 2. Các nhánh Git đã khởi tạo

1. **`exercise/lab06-starter-base`**: Nhánh base nguyên vẹn cho bài tập cá nhân của cả 7 thành viên, chứa snapshot nguyên bản từ tài nguyên giảng viên.
2. **`exercise/lab06-duy`**: Nhánh bài tập cá nhân của Duy (đã hoàn thành S1–S3, A1–A2, H1 E21–E25 và báo cáo `path_comparison.md`, commit `3a3cec6`).
3. **`integration/lab06-v0.6`**: Nhánh tích hợp chính của nhóm, tách trực tiếp từ `origin/main` (`27fbea699d16968ceb169b795bcf979e69bc1b61`).
4. **`feat/lab06-duy-service`**: Nhánh công việc TV1 của Duy phục vụ tích hợp module `service.py` glue.

---

## 3. Nội dung triển khai Service Glue (`src/assistant_core/service.py`)

1. **Bảo toàn Constructor:**
   - Thêm tham số tùy chọn `rag: Any | None = None` ở cuối danh sách tham số `AssistantService.__init__`.
   - Các mã nguồn gọi theo kiểu cũ (positional arguments hoặc không truyền `rag`) vẫn hoạt động 100% tương thích ngược.

2. **Privacy Guard & RAG Delegation:**
   - Trong nhánh xử lý `Intent.RULE`:
     - Kiểm tra `is_private_request(text)` **trước tiên**. Nếu phát hiện câu hỏi vi phạm quyền riêng tư của sinh viên khác (ví dụ: điểm, GPA, số điện thoại, MSSV), trả về thông báo từ chối an toàn mà **không thực hiện retrieval hay gọi model LLM**.
     - Nếu không vi phạm và có `self.rag`, ủy quyền xử lý cho `self.rag.answer(text)`.
     - Nếu `self.rag is None`, giữ nguyên cơ chế tìm kiếm `_handle_rule(text)` legacy.
   - Các luồng tính tiền (`FEE`) và tra cứu phòng ban (`OFFICE`) được giữ nguyên dạng deterministic bằng mã Python, tuyệt đối không chuyển sang LLM.

3. **Factory `build_service(settings=None)`:**
   - Đọc cấu hình `getattr(settings, "kb_dir", None)`.
   - Nếu `kb_dir` được chỉ định và thư mục tồn tại trên đĩa, tự động nạp chunks (`load_folder`), khởi tạo BM25 index (`make_index`), khởi tạo LLM (`make_llm` hoặc `StubLLM`), và inject `RagAnswerer`.
   - Nếu `kb_dir` không tồn tại hoặc các module RAG chưa được nạp, fallback an toàn về `AssistantService()` legacy mà không làm gián đoạn hệ thống.

4. **CLI (`__main__.py`):**
   - Đảm bảo lệnh `--test`, truy vấn trực tiếp (one-shot query), và chế độ REPL hoạt động chính xác với chuẩn đầu ra stdout không bị vỡ định dạng.

---

## 4. Bằng chứng kiểm thử tự động (Verification Evidence)

1. **Unit tests mới cho Service Glue (`tests/test_service_rag.py`):**
   - `test_service_with_injected_rag`: RULE query ủy quyền chính xác cho RAG answerer.
   - `test_service_fee_is_deterministic_and_bypasses_rag`: Phép tính học phí 9,450,000 VND không bao giờ gọi RAG.
   - `test_service_office_is_deterministic_and_bypasses_rag`: Tra cứu phòng B.201 không gọi RAG.
   - `test_service_privacy_guard_intercepts_before_rag`: Chặn câu hỏi riêng tư trước khi gọi RAG.
   - `test_service_privacy_guard_various_patterns`: Kiểm tra đa dạng mẫu câu hỏi PII sinh viên.
   - `test_service_privacy_guard_allows_own_queries`: Cho phép câu hỏi điều kiện tốt nghiệp/GPA của chính mình đi qua.
   - `test_service_legacy_fallback_when_rag_is_none`: Fallback quy chế cũ hoạt động khi không inject RAG.
   - `test_build_service_with_nonexistent_kb_dir`: Factory xử lý an toàn khi thiếu KB.
   - `test_service_backward_compatibility_positional_args`: Đảm bảo 7 positional arguments cũ vẫn hợp lệ.
   - **Kết quả:** **11 passed in 0.05s**.

2. **Full Regression Suite:**
   ```powershell
   python -m pytest -q
   ```
   - **Kết quả:** **117 passed**, 0 failed (2.42s).

3. **CLI Smoke Verification:**
   - `python -m assistant_core --test` → PASS (đầy đủ các intent: greeting, fee 9,450,000 VND, office B.201, rule).
   - `python -m assistant_core "tuition for 18 credits and 2 retake"` → `Your tuition is 9,450,000 VND.` (PASS).

---

## 5. Hợp đồng giao diện (Interface Contract Confirmation) cho các thành viên

| Module / Class | Owner | Trạng thái tiếp nhận trong `service.py` |
|---|---|---|
| `Chunk`, `load_folder`, `make_index` | Trung Anh (TV2) | `service.py` sẵn sàng import từ `assistant_core.rag.chunker` và `index` |
| `Response`, `RagAnswerer` (A1) | Đạt (TV3) | `AssistantService(..., rag=rag)` đã wired; gọi `self.rag.answer(text)` |
| `is_private_request`, `PRIVATE_REPLY` | Bội Anh (TV5) | `service.py` gọi guard trước khi gọi `rag.answer` |
| `make_llm`, `StubLLM` (A2), Settings `kb_dir` | Quỳnh (TV6) | `build_service` sẵn sàng dựng RAG khi có settings |
| `ChatResponse` API Schema | Hùng (TV4) | API giữ nguyên, `Response` trả ra đầy đủ dữ liệu |
| `eval/compare_paths.py` | Tâm (TV7) | Sẵn sàng chạy đánh giá trên `AssistantService` |
