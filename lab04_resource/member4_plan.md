# KẾ HOẠCH HOÀN THÀNH NHIỆM VỤ THÀNH VIÊN 4 (BACKEND DEV 3)
**Họ và tên:** Phạm Khánh Tâm  
**Vai trò:** Thành viên 4 (TV4) — Backend Dev 3 (External Weather & Resilience)  
**Dự án:** Study Assistant (`assistant_core` / `assistant_api`)  
**Mã Issue:** `#04` (`api: implement GET /v1/weather endpoint with failure resilience (#04)`)  
**Tên Branch:** `feat/04-weather-resilience`  
**Mục tiêu điểm số:** 10/10 điểm chính thức + 1 điểm Bonus = **11/10 điểm**

---

## 🎯 I. MỤC TIÊU VÀ TRÁCH NHIỆM CHÍNH

Thành viên 4 (Tâm) phụ trách tích hợp dịch vụ thời tiết bên ngoài với cơ chế chịu lỗi (Fault Tolerance & Resilience):
1. **Nhiệm vụ Lập trình (Task T4 - Mục D.6)**:
   - Hiện thực endpoint `GET /v1/weather` kết nối với `WeatherClient`.
   - Xử lý ngoại lệ `ExternalServiceError` để chuyển đổi sạch sẽ thành HTTP status code `503 Service Unavailable`.
   - Tuân thủ cấu trúc schema phản hồi `Weather` và `ErrorResponse`.
2. **Nhiệm vụ Phân tích Khả năng Phục hồi (Resilience Analysis - Trang 16)**:
   - Phân tích và trả lời câu hỏi Exercise trang 16 của tài liệu Lab 4 về cách mock lỗi mạng trong unit test `test_weather_down_returns_503`.
   - Làm rõ 3 thói quen chịu lỗi của `WeatherClient`: Timeout (3s), Retry (thử lại khi thất bại), và Backup Plan (sử dụng cache đánh dấu `stale=True`).
3. **Nhiệm vụ Kiểm thử & Bằng chứng PR (Testing & Evidence)**:
   - Chạy kiểm thử tự động pytest: đạt 100% các test liên quan đến thời tiết (`test_weather_ok`, `test_weather_down_returns_503`, `test_weather_stale_cache_when_upstream_fails`).
   - Chụp ảnh minh chứng Swagger UI (`/docs`) khi gọi `/v1/chat` thành công.
   - Soạn thảo đoạn văn Reflection H2 (5 dòng) và ghi nhật ký sử dụng AI vào `docs/ai-use-log.md`.
   - Mở Pull Request cá nhân trên GitHub theo đúng mẫu quy định.

---

## 📅 II. LỘ TRÌNH THỰC HIỆN CHI TIẾT (STEP-BY-STEP)

```
[Giai đoạn 1: Khởi tạo Issue #04 & Branch] ──> [Giai đoạn 2: Lập trình Task T4] ──> [Giai đoạn 3: Phân tích Exercise P16]
                                                                                               │
[Giai đoạn 6: Phối hợp Review & Merge] <──── [Giai đoạn 5: Mở Pull Request] <──── [Giai đoạn 4: Kiểm thử Pytest & /docs]
```

---

### 🔹 GIAI ĐOẠN 1: KHỞI TẠO ISSUE #04 & BRANCH LÀM VIỆC (Thời gian: 10 phút)

1. **Khởi tạo Issue trên GitHub:**
   - **Title:** `api: implement GET /v1/weather endpoint with failure resilience (#04)`
   - **Labels:** `feat`, `backend`, `external`, `M4`
   - **Assignee:** `@AI-WFox`
   - **Nội dung:**
     ```markdown
     ## Goal
     Cung cấp thời tiết cơ sở Nguyễn Văn Cừ qua GET /v1/weather, xử lý sự cố dịch vụ bên ngoài.

     ## Acceptance criteria
     - [ ] Gọi WeatherClient lấy thời tiết với timeout 3s, retry và cache fallback.
     - [ ] Bắt ngoại lệ ExternalServiceError và trả về mã sạch HTTP 503.
     - [ ] Vượt qua unit test mock mạng `test_weather_down_returns_503`.
     ```
2. **Tạo nhánh làm việc:**
   - Nhánh xuất phát từ `origin/docs/lab04-guide`:
     ```bash
     git checkout -b feat/04-weather-resilience origin/docs/lab04-guide
     ```

---

### 🔹 GIAI ĐOẠN 2: LẬP TRÌNH TASK T4 (MỤC D.6) (Thời gian: 15 phút)

1. **Vị trí file:** `lab04_resource/starter/src/assistant_api/main.py`
2. **Hiện thực code:**
   Thay thế đoạn `raise NotImplementedError("T4")` trong hàm `campus_weather()` bằng khối lệnh xử lý an toàn:
   ```python
   @app.get("/v1/weather", response_model=Weather, tags=["external"], responses={503: {"model": ErrorResponse}})
   def campus_weather() -> Weather:
       try:
           return weather.current()
       except ExternalServiceError:
           raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Weather service unavailable") from None
   ```
3. **Giải thích kiến trúc kỹ thuật:**
   - `weather.current()`: Gọi client thời tiết để truy vấn API Open-Meteo tại tọa độ cơ sở Nguyễn Văn Cừ (`campus_lat`, `campus_lon`).
   - `except ExternalServiceError:`: Khi dịch vụ bên ngoài gặp sự cố mạng (ConnectTimeout, ReadTimeout hoặc HTTP 5xx kéo dài qua hết các lượt retry), client ném ngoại lệ miền `ExternalServiceError`.
   - `raise HTTPException(...) from None`: Chuyển đổi ngoại lệ nội bộ thành mã lỗi chuẩn HTTP 503, đồng thời ẩn traceback gốc (`from None`) để không làm rò rỉ chi tiết hệ thống ra ngoài.

---

### 🔹 GIAI ĐOẠN 3: PHÂN TÍCH KHẢ NĂNG CHỊU LỖI (EXERCISE TRANG 16) (Thời gian: 15 phút)

1. **Câu hỏi bài tập (Tutorial Page 16):**
   * *Đọc `test_weather_down_returns_503` trong `tests/test_api.py`. Hãy giải thích trong 1 câu cách test giả lập tình huống server thời tiết sập.*
2. **Câu trả lời chuẩn:**
   > *"Test sử dụng fixture `weather_with(...)` kết hợp cùng `httpx.MockTransport` để chặn toàn bộ kết nối mạng thật và chủ động ném ngoại lệ `httpx.ConnectTimeout` (hoặc HTTP 500) ngay khi nhận request, từ đó xác minh endpoint `/v1/weather` có bắt đúng lỗi và trả về mã lỗi HTTP 503 với error code `weather_service_unavailable` hay không."*
3. **Ba thói quen chịu lỗi (3 Resilience Habits) được áp dụng:**
   - **Timeout (Chờ tối đa 3 giây):** Khởi tạo `httpx.Client(timeout=3)` tránh việc treo server khi dịch vụ thứ ba phản hồi chậm.
   - **Retry (Thử lại nếu lỗi):** Sử dụng vòng lặp retry ngắn để vượt qua các lỗi mạng chập chờn nhất thời.
   - **Backup Plan (Dùng dữ liệu cũ khi sập):** Lưu kết quả gần nhất vào cache trong bộ nhớ; khi API bên ngoài sập hoàn toàn thì trả về thời tiết đã lưu và đánh dấu cờ `stale=True`.

---

### 🔹 GIAI ĐOẠN 4: KIỂM THỬ VỚI PYTEST & SWAGGER UI (Thời gian: 20 phút)

1. **Chạy kiểm thử tự động với Pytest:**
   ```bash
   pytest lab04_resource/starter/tests/test_api.py -k "weather" -v
   ```
   *Kết quả mong đợi:* Cả 3 test case đều đạt màu xanh (**PASSED**):
   - `test_weather_ok`: Kiểm tra trường hợp thời tiết bình thường trả về HTTP 200 và mô tả `overcast`.
   - `test_weather_down_returns_503`: Kiểm tra khi upstream timeout thì endpoint trả về HTTP 503.
   - `test_weather_stale_cache_when_upstream_fails`: Kiểm tra cơ chế lấy cache cũ `stale=True`.

2. **Chụp ảnh Swagger UI (`/docs`) làm minh chứng bắt buộc:**
   - Khởi động server API:
     ```bash
     cd lab04_resource/starter
     uvicorn assistant_api.main:create_app --factory --reload
     ```
   - Mở trình duyệt tại `http://127.0.0.1:8000/docs`.
   - Tìm đến `POST /v1/chat` -> Chọn **Try it out** -> Nhập message -> **Execute**.
   - Chụp ảnh màn hình thấy rõ kết quả phản hồi HTTP 200 và `request_id`.

---

### 🔹 GIAI ĐOẠN 5: MỞ PULL REQUEST CÁ NHÂN (Thời gian: 15 phút)

1. **Commit và đẩy code lên GitHub:**
   ```bash
   git add lab04_resource/starter/src/assistant_api/main.py lab04_resource/member4_plan.md
   git commit -m "feat(weather): implement GET /v1/weather endpoint with failure resilience (#04)"
   git push -u origin feat/04-weather-resilience
   ```
2. **Nội dung PR Template chuẩn:**
   - **What:** Hiện thực endpoint `GET /v1/weather` kết nối `WeatherClient`, xử lý ngoại lệ `ExternalServiceError` trả về HTTP 503 chuẩn.
   - **Why:** Hoàn thành Task T4 theo phân công của môn học CSC10014 Lab 4.
   - **Reflection H2 (Bắt buộc 5 dòng):**
     > *"Ở Lab 3, việc gọi trực tiếp `service.handle()` là lời gọi hàm nội bộ (in-process function call), đòi hỏi client và server phải viết chung một ngôn ngữ Python và chạy trên cùng một máy tính. Sang Lab 4, việc bọc qua giao thức HTTP REST API (`POST /v1/chat`) cho phép tách rời hoàn toàn giữa client và backend. Nhờ đó, giao diện web, ứng dụng di động hay các dịch vụ khác có thể giao tiếp dễ dàng qua định dạng chuẩn JSON mà không phụ thuộc vào công nghệ của nhau. Đối với làm việc nhóm, kiến trúc này giúp phân tách trách nhiệm rõ ràng: team frontend và team backend có thể phát triển độc lập dựa trên API contract đã thống nhất từ trước mà không làm ảnh hưởng đến mã nguồn của nhau."*
   - **AI Use:**
     - Công cụ sử dụng: Google Antigravity IDE (Gemini).
     - Yêu cầu: Hiện thực Task T4 theo `lab04_resource/guide.md`, bọc try/except `ExternalServiceError` thành HTTP 503.
     - Tự kiểm chứng: Chạy bộ test pytest 3/3 passed, kiểm tra linter Ruff.

---

### 🔹 GIAI ĐOẠN 6: PHỐI HỢP REVIEW CHÉO & BÀN GIAO CHO TECH LEAD

- Gán reviewer theo vòng xoay review của nhóm.
- Đảm bảo CI GitHub Actions trên PR báo xanh toàn bộ.
- Bàn giao nhánh cho Tech Lead (Duy) để tiến hành squash-merge vào nhánh `main` khi tích hợp toàn bộ API.
