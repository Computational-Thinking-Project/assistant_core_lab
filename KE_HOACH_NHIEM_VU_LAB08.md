# Kế Hoạch Chi Tiết Phân Công Nhiệm Vụ Lab 8: Testing, Debugging & Red Teaming (Nội Bộ Nhóm)

Tài liệu căn cứ:
- Hướng dẫn thực hành: `CSC10014_2026_Lab08_Testing_Security_RedTeam_Tutorial.docx.pdf`
- Tài nguyên tham khảo: Thư mục `lab08/` (bao gồm `lab08/starter/` và `lab08/worksheets/`)
- Phạm vi thực hiện: **Từ Part C trở đi** (Tập trung vào phần phối hợp nhóm, an toàn bảo mật, kiểm thử hồi quy và Red-Team nội bộ).
- **Cập nhật hình thức:** Không trao đổi kịch bản với nhóm bạn bên ngoài mà **tự thiết kế kịch bản tấn công mở rộng, tự chạy red-team nội bộ và tự viết báo cáo log/debrief của nhóm mình**.

---

## ⚠️ HƯỚNG DẪN QUAN TRỌNG VỀ SỬ DỤNG TÀI NGUYÊN & CODEBASE

> **NGUYÊN TẮC CỐT LÕI:**
> - Thư mục `lab08/` là **tài nguyên mẫu (Starter & Templates) của Giảng viên cấp** để tham khảo cấu trúc, copy file khung sang dự án chính.
> - **TUYỆT ĐỐI KHÔNG làm việc, viết code hay chỉnh sửa trực tiếp bên trong thư mục `lab08/`**.
> - Mọi thao tác lập trình, chạy lệnh kiểm thử (`pytest`, `run_redteam.py`), mở branch và tạo Pull Request (PR) đều phải được thực hiện trên **thư mục gốc của repository dự án (`assistant_core_lab/`)**.

### Bảng đối chiếu việc sao chép và sử dụng tài nguyên từ `lab08/`:

| Tài nguyên mẫu từ `lab08/` | Thao tác cần làm | Vị trí làm việc chính thức trên Repo gốc | Phụ trách |
| :--- | :--- | :--- | :---: |
| `lab08/starter/redteam/` | Copy toàn bộ thư mục `redteam/` sang root repo | `redteam/run_redteam.py`<br>`redteam/cases.jsonl` | **Tâm & Quỳnh** |
| `lab08/starter/src/assistant_core/guard.py` | So sánh và bổ sung hàm guard vào code gốc | `src/assistant_core/guard.py` | **Tâm** |
| `lab08/starter/tests/test_my_regressions.py` | Copy file mẫu sang thư mục `tests/` gốc | `tests/test_my_regressions.py` | **Duy, Đạt, Hùng** |
| `lab08/worksheets/failure_catalogue.md` | Copy file markdown sang thư mục `worksheets/` gốc | `worksheets/failure_catalogue.md` | **Hùng** |
| `lab08/worksheets/redteam_exchange.md` | Copy file markdown sang thư mục `worksheets/` gốc | `worksheets/redteam_exchange.md` | **Trung Anh** |
| `lab08/worksheets/bug_report_template.md` | Dùng làm form mẫu để viết báo cáo lỗi | `worksheets/bug_reports/` (nếu cần) | **Duy, Đạt, Hùng** |

---

## 1. QUY ƯỚC CODE REVIEW XOAY VÒNG NỘI BỘ (PEER REVIEW)

Không tách việc Review PR thành công việc riêng của một cá nhân mà review chéo theo vòng tròn khép kín: **Người sau review PR cho người liền trước** (Duy do Trung Anh review):

```
Duy ──(được review bởi)──> Tâm ──(được review bởi)──> Đạt ──(được review bởi)──> Hùng 
 ^                                                                                  │
 └──────────────── Trung Anh <─── Quỳnh <─── Bội Anh <──────────────────────────────┘
```

* **Tâm** review PR của **Duy**
* **Đạt** review PR của **Tâm**
* **Hùng** review PR của **Đạt**
* **Bội Anh** review PR của **Hùng**
* **Quỳnh** review PR của **Bội Anh**
* **Trung Anh** review PR của **Quỳnh**
* **Duy** review PR của **Trung Anh**

---

## 2. BẢNG PHÂN CHIA NHIỆM VỤ CHI TIẾT (7 THÀNH VIÊN)

| Thành viên | Nhiệm vụ kỹ thuật trực tiếp (Hands-on Deliverables) | File phụ trách trên Repo gốc | Được Review bởi |
| :--- | :--- | :--- | :---: |
| **Duy** | **Regression Test & Mitigation 1 (Logic/Core)**: Viết 1 test hồi quy cho lỗi logic tuần 7 + Trực tiếp viết code vá lỗi (mitigation 1). Điều phối chung, merge và gắn tag `v0.8-tested`. | `tests/test_my_regressions.py`<br>`src/assistant_core/...` | **Tâm** |
| **Tâm** | **Part D (Task G1 - Prompt Injection Guard)**: Copy `redteam/` từ `lab08/starter/`, thêm 2 Regex patterns vào guard để chặn prompt injection, đảm bảo `python redteam/run_redteam.py` pass 12/12. | `src/assistant_core/guard.py`<br>`redteam/` | **Đạt** |
| **Đạt** | **Regression Test & Mitigation 2 (API/Validation)**: Viết 1 test hồi quy cho lỗi input/API tuần 7 + Trực tiếp viết code vá lỗi (mitigation 2). | `tests/test_my_regressions.py`<br>`src/assistant_api/...` | **Hùng** |
| **Hùng** | **Regression Test & Mitigation 3 (RAG/Retrieval)**: Viết 1 test hồi quy cho lỗi RAG/Grounding tuần 7 + Trực tiếp viết code vá lỗi (mitigation 3) + Copy & chủ trì bảng `worksheets/failure_catalogue.md`. | `tests/test_my_regressions.py`<br>`worksheets/failure_catalogue.md` | **Bội Anh** |
| **Bội Anh** | **Part F.2 (Internal Red-Team Suite)**: Thiết kế và viết bộ test case tự tấn công hệ thống nhóm mình (8–10 ca mở rộng trong `redteam/cases_internal.jsonl`) bao phủ đủ 6 categories. | `redteam/cases_internal.jsonl` | **Quỳnh** |
| **Quỳnh** | **Part F.3 (Red-Team Execution & Runner)**: Chạy bộ test tấn công nội bộ trên hệ thống nhóm mình, trích xuất log và lập báo cáo chi tiết các ca PASS/FAIL vào `redteam/report.md`. | `redteam/report.md` | **Trung Anh** |
| **Trung Anh** | **Part F.4 & Bonus Mitigation**: Chủ trì họp debrief nội bộ, ghi nhận log phân tích lỗi vào `worksheets/redteam_exchange.md` + Viết thêm 1 mitigation mới cho 1 lỗi tự tìm ra (Bonus +1đ). | `worksheets/redteam_exchange.md`<br>Code fix Bonus | **Duy** |

---

## 3. KẾ HOẠCH CHI TIẾT TỪNG PHẦN (TỪ PART C TRỞ ĐI)

```
Part C (Logs & Bug Reports) ──> Part D (G1 Prompt Guard) ──> Part E (Regression Tests & 3 Mitigations) ──> Part F (Tự Red-Team Nội Bộ) ──> Team Integration
```

---

### Part C — The Debugger and Logging (Cơ sở phân tích lỗi)
* **Mục tiêu:** Nắm cách đọc log JSON trên server và chuẩn hóa việc lập phiếu báo lỗi theo mẫu `lab08/worksheets/bug_report_template.md`.
* **Phân công cụ thể:**
  - **Duy, Đạt, Hùng:** Dựa vào log server và các quan sát thực tế từ bài usability test ở Lab 7 (file `worksheets/user_test_observations.md`) để phân tích nguyên nhân gốc của 3 lỗi hệ thống. Mỗi người chuẩn bị phân tích lỗi cho phần mình sẽ phụ trách vá ở Part E.
  - **Trung Anh:** Đọc và nắm vững cấu trúc template báo cáo lỗi (`lab08/worksheets/bug_report_template.md`) để sử dụng cho việc lập log phân tích nội bộ ở Part F.

---

### Part D — Security Basics & Task G1 (Prompt Injection Guard)
* **Mục tiêu:** Đưa module `redteam/` vào repo gốc, tích hợp cơ chế phòng vệ chống Prompt Injection trong `src/assistant_core/guard.py` để vượt qua 100% bộ test red-team ban đầu (12/12 ca).
* **Phân công cụ thể:**
  - **Tâm (Làm code chính):**
    1. Đảm bảo thư mục `redteam/` đã có ở root repo (copy từ `lab08/starter/redteam/` nếu chưa có).
    2. Chạy lệnh kiểm tra ban đầu từ root repo:
       ```bash
       python redteam/run_redteam.py
       ```
       (Xác nhận có 11 ca passed, 1 ca `R03` failed do router bắt nhầm từ khóa "fee").
    3. Bổ sung 2 regex pattern vào danh sách `INJECTION_PATTERNS` trong file `src/assistant_core/guard.py`:
       ```python
       r"\b(reveal|show|print|repeat) (me )?(your|the) (system )?(prompt|instructions|rules)",
       r"\byou are now\b",
       ```
    4. Chạy lại kiểm thử từ root: đảm bảo `run_redteam.py` đạt **12/12 passed** và `pytest -q` đạt đầy đủ test xanh.
    5. Mở PR cho Task G1.
  - **Đạt (Review PR của Tâm):** Kiểm tra regex của Tâm, chạy thử test xem có bị quá rộng gây chặn nhầm câu hỏi bình thường (False Positive) hay không rồi mới Approve PR.

---

### Part E — Regression Tests & 3 Mitigations (Mỗi người 1 bài test + 1 bản fix)
* **Mục tiêu:** Khởi tạo file `tests/test_my_regressions.py` (từ mẫu `lab08/starter/tests/test_my_regressions.py`), viết đủ 3 bài regression test và cài đặt đủ **3 bản vá (mitigations)** trong mã nguồn dự án.
* **Phân công cụ thể:**
  - **Duy (Test 1 + Mitigation 1 - Logic/Backend):**
    - Viết test `test_retake_number_as_word` hoặc test lỗi tính học phí khi số tín chỉ âm/chữ vào `tests/test_my_regressions.py`.
    - Trực tiếp sửa hàm logic (ví dụ `parse_credits` hoặc `tuition`) trong `src/assistant_core/tools.py`.
    - Mở PR cho phần việc của mình.
  - **Tâm (Review PR của Duy):** Tạm thời revert bản fix trong PR của Duy để kiểm tra test có fail trên code cũ không, sau đó Approve.
  - **Đạt (Test 2 + Mitigation 2 - API/Validation):**
    - Viết test `test_oversized_or_malformed_input` kiểm tra validation request API vào `tests/test_my_regressions.py`.
    - Trực tiếp cấu hình Pydantic / router trong `src/assistant_api/` để xử lý chặn lỗi.
    - Mở PR cho phần việc của mình.
  - **Hùng (Test 3 + Mitigation 3 - RAG/Grounding & Review PR của Đạt):**
    - Review PR của Đạt trước khi merge.
    - Viết test `test_citation_of_unretrieved_source_is_rejected` hoặc test UI xử lý khi sources rỗng vào `tests/test_my_regressions.py`.
    - Trực tiếp bổ sung grounding check / xử lý empty sources trong `src/assistant_core/rag/` hoặc UI.
    - Copy `lab08/worksheets/failure_catalogue.md` vào `worksheets/failure_catalogue.md` của repo gốc, cập nhật đủ cả 3 lỗi và 3 mitigations này.
    - Mở PR cho phần việc của mình.
  - **Bội Anh (Review PR của Hùng):** Kiểm tra test của Hùng và rà soát file `failure_catalogue.md` đủ 3 lỗi và 3 mitigations trước khi Approve.

---

### Part F — Red-Team Nội Bộ (Tự thiết kế tấn công, tự chạy & viết Log nhóm)
* **Mục tiêu:** Tự xây dựng kịch bản tấn công khắt khe, tự chạy trên hệ thống của nhóm, tự phân tích log các điểm yếu bị xuyên thủng và đề xuất bản vá mới.
* **Phân công cụ thể:**

#### F.2 Soạn test case tự tấn công mở rộng (20 phút):
* **Bội Anh (Chủ trì):**
  - Tham khảo định dạng từ `redteam/cases.jsonl`, viết file `redteam/cases_internal.jsonl` gồm 8–10 test case tấn công độc đáo, sáng tạo nhằm tìm điểm yếu của chính trợ lý nhóm mình:
    1. `prompt-injection`: Các biến thể cố tình bypass regex (viết hoa xen kẽ, đổi thứ tự từ, dùng tiếng Việt lừa bypass).
    2. `privacy`: Cố tình hỏi thông tin bí mật sinh viên, xin địa chỉ, số điện thoại giáo viên/bạn học.
    3. `out-of-scope`: Các câu hỏi ngoài lề (hỏi giá vàng, thời tiết thế giới, viết code C++).
    4. `malformed-input`: Chuỗi rỗng, chuỗi hàng ngàn ký tự, JSON thiếu ngoặc.
    5. `fee-manipulation`: Số tín chỉ 0, -10, số thập phân, 100 tín chỉ.
    6. `unavailable-service`: Test tình huống DB/LLM down (`"llm_down": true`).
    7. **1–2 Control cases:** Câu hỏi học phí/thủ tục chuẩn để kiểm tra tính khả dụng.
  - Mở PR chứa file test case.
* **Quỳnh (Review PR của Bội Anh):** Rà soát độ phủ của các ca test của Bội Anh trước khi Approve.

#### F.3 Thực thi chạy Red-Team nội bộ (15 phút):
* **Quỳnh (Chủ trì):**
  - Chạy lệnh kiểm thử tấn công ngay trên hệ thống nhóm mình từ root repo:
    ```bash
    python redteam/run_redteam.py redteam/cases_internal.jsonl
    ```
  - Kiểm tra kết quả, thu thập log chi tiết các ca FAIL và PASS vào file `redteam/report.md`.
  - Mở PR chứa file `redteam/report.md`.
* **Trung Anh (Review PR của Quỳnh):** Kiểm tra tính đầy đủ của file báo cáo `report.md` trước khi Approve.

#### F.4 Tự viết log debrief nhóm & Triển khai Bonus (15 phút):
* **Trung Anh (Chủ trì) cùng Quỳnh & Bội Anh:**
  - Copy file `lab08/worksheets/redteam_exchange.md` vào `worksheets/redteam_exchange.md` ở root repo.
  - Cả nhóm ngồi họp nội bộ (debrief) phân tích kết quả chạy của Quỳnh:
    - Xác định những câu nào bị lọt lưới (FAIL - ví dụ bot vẫn trả lời câu ngoài luồng, hoặc regex bị lừa).
    - Đánh giá mức độ nghiêm trọng (Blocker / Major / Minor).
    - Xác định nguyên nhân và đưa ra giải pháp khắc phục (Mitigation).
  - Tự điền và hoàn thiện toàn bộ biên bản vào file `worksheets/redteam_exchange.md` (đóng vai trò là log tự kiểm thử bảo mật nội bộ của nhóm).
* **Trung Anh (Làm phần Bonus +1 điểm):**
  - Chọn ra 1 lỗ hổng nguy hiểm nhất vừa tìm được trong bộ test nội bộ.
  - Viết code vá lỗi (mitigation mới) và kèm 1 regression test chứng minh đã khắc phục thành công.
  - Mở PR cho phần việc này.
* **Duy (Review PR của Trung Anh):** Rà soát biên bản log `redteam_exchange.md` và chạy test kiểm tra mitigation bonus trước khi Approve.

---

### Team Integration & Đóng gói nộp bài
* **Duy (Tech Lead):**
  1. Nộp link **Draft PR** lên hệ thống LMS ngay cuối buổi học trên lớp.
  2. Trước deadline Lab 9: Kiểm tra CI pass 100% (`pytest` và `python redteam/run_redteam.py`), merge toàn bộ vào nhánh chính.
  3. Đánh Git Tag: **`v0.8-tested`** và nộp link tag của nhóm lên LMS.

---

## 4. CHECKLIST THEO DÕI TIẾN ĐỘ & SẢN PHẨM ĐẦU RA

| Thành viên | File sản phẩm bàn giao (trên Repo gốc) | Người Review PR | Hạn chót (Buổi lab) | Tiêu chí nghiệm thu |
| :--- | :--- | :---: | :---: | :--- |
| **Duy** | 1 regression test + 1 mitigation (core code), Git Tag `v0.8-tested` | **Tâm** | Phút 70 & Trước Lab 9 | Test pass, code fix hoạt động, CI xanh |
| **Tâm** | `src/assistant_core/guard.py` (G1 regex) + thư mục `redteam/` | **Đạt** | Phút 40 | `python redteam/run_redteam.py` pass 12/12 ca |
| **Đạt** | 1 regression test + 1 mitigation (API/Validation) | **Hùng** | Phút 70 | Test fail trên code cũ, pass trên code mới |
| **Hùng** | 1 regression test + 1 mitigation (RAG) + `worksheets/failure_catalogue.md` | **Bội Anh** | Phút 70 | Đủ bảng danh mục với 3 mitigations của Duy, Đạt, Hùng |
| **Bội Anh** | `redteam/cases_internal.jsonl` | **Quỳnh** | Phút 90 | Đủ 8–10 ca kiểm thử tự tấn công phủ 6 categories |
| **Quỳnh** | `redteam/report.md` | **Trung Anh** | Phút 110 | File báo cáo chi tiết log chạy kiểm thử nội bộ |
| **Trung Anh** | `worksheets/redteam_exchange.md` (log nội bộ), 1 mitigation bonus | **Duy** | Phút 130 & Trước Lab 9 | Biên bản log phân tích hoàn tất + 1 mitigation thưởng (+1đ) |
