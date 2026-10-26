# KẾ HOẠCH HOÀN THÀNH NHIỆM VỤ THÀNH VIÊN 2 (BACKEND DEV 1)
**Họ và tên:** Trương Thành Đạt  
**Mã số sinh viên:** 25127035  
**GitHub:** `@Thanhdat3010`  
**Vai trò:** Thành viên 2 (TV2) — Backend Dev 1 (Core Chat Endpoint & Reflection H2)  
**Dự án:** Study Assistant (`assistant_core` / `assistant_api`)  
**Mã Issue:** `#24` (`api: implement POST /v1/chat endpoint (#02)`)  
**Tên Branch:** `feat/02-chat-endpoint`  
**Mục tiêu điểm số:** 10/10 điểm chính thức + 1 điểm Bonus = **11/10 điểm**

---

## 🎯 I. MỤC TIÊU VÀ TRÁCH NHIỆM CHÍNH

Thành viên 2 (Trương Thành Đạt) đảm nhận vai trò Backend Dev 1, phụ trách kiến trúc giao tiếp HTTP cốt lõi kết nối Client với lõi `AssistantService`:
1. **Nhiệm vụ Hiện thực Code (Task T1 — Mục D.3)**:
   - Hiện thực hóa endpoint `POST /v1/chat` trong `lab04_resource/starter/src/assistant_api/main.py`.
   - Tiếp nhận `ChatRequest` (validate độ dài `1..2000` ký tự, `session_id` tùy chọn).
   - Chuyển tiếp (delegate) yêu cầu tới `service.handle(Message(text=req.message, session_id=req.session_id))`.
   - Đóng gói dữ liệu trả về thành `ChatResponse`, sinh mã định danh truy vấn `request_id` gồm 12 ký tự hex duy nhất (`uuid.uuid4().hex[:12]`).
   - Giữ nguyên tham số `request: Request` trên chữ ký hàm để hỗ trợ TV6 (Bội Anh) tích hợp Rate Limiter ở Part F.
2. **Nhiệm vụ Soạn thảo Reflection H2 (5 dòng)**:
   - Soạn thảo phân tích so sánh giữa kiến trúc In-Process Function Call (Lab 3) và HTTP REST API (Lab 4).
   - Đóng góp nội dung cho nhóm để làm tài liệu đối chiếu kỹ thuật trong PR Description.
3. **Nhiệm vụ Kiểm thử Tự động & Thực nghiệm Minh chứng**:
   - Chạy kiểm thử tự động với Pytest: Đảm bảo 100% test cases liên quan đến `/v1/chat` (`test_chat_fee`, `test_chat_validation_error`) đều PASS.
   - Chạy máy chủ Uvicorn cục bộ, thực thi request tương tác trên Swagger UI (`/docs`), chụp ảnh màn hình minh chứng HTTP 200 OK và `request_id` để đính kèm vào PR.
4. **Nhiệm vụ Review Chéo ("Người đứng trên review người đứng dưới")**:
   - Theo phân công bảng Lab 04 (TV2 đứng trên TV3): Tiến hành review PR của **Nguyễn Đình Hùng (`@benalexx007` - TV3)** về `POST /v1/feedback`.
   - Áp dụng cấu trúc phản biện 3 phần chuẩn mực: `Praise:`, `Question:`, `Suggestion:`.

---

## 📅 II. LỘ TRÌNH THỰC HIỆN CHI TIẾT (STEP-BY-STEP)

```
[Giai đoạn 1: Issue #24 & Branch feat/02-chat-endpoint]
                   │
                   ▼
[Giai đoạn 2: Hiện thực Task T1 trong main.py]
                   │
                   ▼
[Giai đoạn 3: Kiểm thử Pytest & Thực nghiệm Swagger UI]
                   │
                   ▼
[Giai đoạn 4: Soạn thảo Reflection H2 & Cập nhật AI Use Log]
                   │
                   ▼
[Giai đoạn 5: Mở Pull Request Cá nhân (Merge #1)]
                   │
                   ▼
[Giai đoạn 6: Peer Review cho TV3 & Hỗ trợ TV6/TV7]
```

---

### Giai đoạn 1: Khởi tạo Issue & Nhánh làm việc
- [x] Tạo GitHub Issue `#24` với tiêu đề `api: implement POST /v1/chat endpoint (#02)` theo đúng mẫu của `guide.md`.
- [x] Tạo nhánh `feat/02-chat-endpoint` bắt nguồn từ `origin/docs/lab04-guide`.
- [x] Tạo file kế hoạch hành động chi tiết `lab04_resource/member2_plan.md`.

### Giai đoạn 2: Hiện thực Code Task T1
- [x] Chỉnh sửa hàm `chat()` trong `lab04_resource/starter/src/assistant_api/main.py`:
  ```python
  @app.post(
      "/v1/chat",
      response_model=ChatResponse,
      tags=["chat"],
      responses={422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
  )
  def chat(req: ChatRequest, request: Request) -> ChatResponse:
      resp = service.handle(Message(text=req.message, session_id=req.session_id))
      return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])
  ```
- [x] Đảm bảo tuân thủ nguyên tắc cách ly mã nguồn: Không chỉnh sửa các hàm ngoài phạm vi được phân công (`submit_feedback`, `list_feedback`, `campus_weather`, `offices`).

### Giai đoạn 3: Kiểm thử Tự động & Swagger UI
- [x] Chạy pytest kiểm tra chat endpoint:
  ```powershell
  $env:PYTHONPATH="src"
  pytest -v -k "chat" --basetemp=.pytest_tmp
  ```
  Kết quả: `test_chat_fee` và `test_chat_validation_error` đều **PASSED 100%**.
- [x] Khởi chạy máy chủ API:
  ```powershell
  uvicorn assistant_api.main:create_app --factory --reload
  ```
- [x] Gửi payload thử nghiệm tại `/v1/chat`:
  ```json
  {
    "message": "tuition for 18 credits and 2 retake",
    "session_id": "test-session"
  }
  ```
  Nhận phản hồi HTTP 200 OK với đầy đủ `answer`, `intent: "fee"`, `request_id` (12 hex digits).

### Giai đoạn 4: Soạn thảo Reflection H2 & Ghi nhận AI Use Log
- [x] Bản thảo Reflection H2 (chuẩn 5 dòng):
  > *"Ở Lab 3, việc gọi trực tiếp `service.handle()` là lời gọi hàm nội bộ (in-process function call), đòi hỏi client và server phải viết chung một ngôn ngữ Python và chạy trên cùng một máy tính. Sang Lab 4, việc bọc qua giao thức HTTP REST API (`POST /v1/chat`) cho phép tách rời hoàn toàn giữa client và backend. Nhờ đó, giao diện web, ứng dụng di động hay các dịch vụ khác có thể giao tiếp dễ dàng qua định dạng chuẩn JSON mà không phụ thuộc vào công nghệ của nhau. Đối với làm việc nhóm, kiến trúc này giúp phân tách trách nhiệm rõ ràng: team frontend và team backend có thể phát triển độc lập dựa trên API contract đã thống nhất từ trước mà không làm ảnh hưởng đến mã nguồn của nhau."*
- [x] Cập nhật bảng `docs/ai-use-log.md` ghi nhận sự chủ động của Thành Đạt trong thiết kế, thẩm định kiến trúc và kiểm thử.

### Giai đoạn 5: Mở Pull Request Chuẩn mực
- [x] Đặt tiêu đề PR: `feat(chat): implement POST /v1/chat endpoint and H2 reflection (#24)`
- [x] Chọn Base branch: `docs/lab04-guide`
- [x] Điền đầy đủ PR Description theo template chuẩn (What, Why, How tested, Evidence, AI use, Reflection H2, Checklist).
- [x] Thông báo cho Tech Lead (Duy) để ưu tiên merge PR này đầu tiên (Merge #1), cung cấp nền tảng cho TV6 gắn Rate Limiting và TV7 viết tài liệu.

### Giai đoạn 6: Thực hiện Peer Review
- [x] Đợi PR của TV3 (Nguyễn Đình Hùng — Task T2: `POST /v1/feedback`).
- [x] Kiểm tra kỹ validation logic (`rating` trong khoảng `[-1, 1]` hoặc `[1, 5]`, mã trạng thái `201 Created`).
- [x] Gửi review `APPROVE` theo chuẩn 3 phần: `Praise:`, `Question:`, `Suggestion:`.

---

## 🔒 III. QUY TẮC AN TOÀN & RÀNG BUỘC KỸ THUẬT

1. **Bảo toàn giao ước (API Contract)**: Không thay đổi cấu trúc schema trong `schemas.py` nếu không có sự thống nhất chung của Tech Lead.
2. **Không làm lộ dữ liệu nhạy cảm**: Tuyệt đối không commit file `.env` chứa bí mật hoặc token GitHub vào git.
3. **Chống xung đột (Conflict-Free)**: Giữ các commit độc lập, rõ ràng theo Conventional Commits (`feat(chat): ...`, `docs(plan): ...`).
