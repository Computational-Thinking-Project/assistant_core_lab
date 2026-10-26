# HƯỚNG DẪN THỰC HIỆN & PHÂN CÔNG CHI TIẾT LAB 04
**Môn học:** CSC10014 - Computational Thinking (Thực hành)  
**Dự án:** Study Assistant (`assistant_core` / `assistant_api`)  
**Phạm vi yêu cầu:** Thực hiện từ **Mục D.3 trở xuống** (theo chỉ đạo của Giảng viên)  
**Mục tiêu điểm số:** 10/10 điểm chính thức + 1 điểm thưởng (Bonus) = **11/10 điểm**

---

## 🎯 1. TỔNG QUAN YÊU CẦU DỰ ÁN (TỪ D.3 TRỞ XUỐNG)

Các thành viên chỉ tập trung vào việc hiện thực hóa REST API trên nền framework **FastAPI**, kết nối với lõi xử lý `assistant_core` từ Lab 3, kiểm thử và nộp bài qua Git/GitHub:
1. **Core Tasks (T1 – T4 / Mục D.3 – D.6)**: Hoàn thiện 4 endpoints trong `main.py` (`POST /v1/chat`, `POST /v1/feedback`, `GET /v1/feedback`, `GET /v1/weather`).
2. **Testing & Evidence (Part E)**: Chạy test tự động với `pytest -q`, chạy kịch bản `curl_tests.sh`, chụp ảnh màn hình Swagger UI (`/docs`) gọi thành công `/v1/chat`.
3. **Homework (H1 & H2)**:
   - **H1**: Bổ sung tính năng lấy danh sách văn phòng `GET /v1/offices` và viết 2 unit tests.
   - **H2**: Đoạn văn Reflection 5 dòng ghi trong phần mô tả của Pull Request.
4. **Bonus (+1 điểm)**:
   - **Part F**: Cấu hình cơ chế Rate Limiting cho `/v1/chat` và bỏ skip test `test_rate_limit`.
5. **Quy trình Git & Release**: Mở PR cá nhân, review code chéo, merge vào `main` và gắn tag `v0.4-api`.

---

## 👥 2. PHÂN CÔNG CHI TIẾT CHO 7 THÀNH VIÊN

| TV | Vai trò | Trọng tâm công việc | Files liên quan | Sản phẩm bàn giao |
|:---:|:---|:---|:---|:---|
| **TV1** | **Tech Lead & Auth Lead** | Cấu hình, Quản trị Git, Task T3 & Tag Release | `main.py`, `.env`, `.gitignore` | Endpoint T3, Tag `v0.4-api`, link nộp LMS |
| **TV2** | **Backend Dev 1** | Task T1 (`/v1/chat`) & Soạn thảo Reflection H2 | `main.py`, `schemas.py` | Endpoint T1, Bản thảo H2 (5 dòng) |
| **TV3** | **Backend Dev 2** | Task T2 (`POST /v1/feedback`) & Validate Data | `main.py`, `schemas.py` | Endpoint T2, Test xác thực dữ liệu |
| **TV4** | **Backend Dev 3** | Task T4 (`GET /v1/weather`) & Resilience Analysis | `main.py`, `weather.py` | Endpoint T4, Giải thích Exercise P16 |
| **TV5** | **Backend Dev 4** | Homework H1 (`GET /v1/offices` + 2 tests) | `knowledge.py`, `main.py`, `test_api.py` | Hàm `all()`, route `/v1/offices`, 2 tests |
| **TV6** | **QA & Bonus Lead** | Bonus Part F (Rate Limiter) & Automation Test | `ratelimit.py`, `main.py`, `test_api.py` | Rate limiter 429, pytest 24/24 pass |
| **TV7** | **Docs & Manual Test** | Part E (curl, Postman), Hướng dẫn chụp ảnh & Docs | `curl_tests.sh`, `api_contract.md`, `external_api_failure.md` | Bộ test curl/Postman, 2 worksheets, ảnh `/docs` |

---

## 🛠️ 3. HƯỚNG DẪN CHI TIẾT TỪNG NHIỆM VỤ

### 🧑‍💻 THÀNH VIÊN 1: Tech Lead, Auth & Release
1. **Thiết lập biến môi trường:**
   - Tạo file `.env` từ `.env.example`:
     ```bash
     cp .env.example .env
     ```
   - Đảm bảo trong `.env` có `API_ADMIN_KEY=change-me` (hoặc key bí mật riêng).
   - Kiểm tra chắc chắn `.env` đã được liệt kê trong `.gitignore`.
2. **Hiện thực Task T3 (Mục D.5) trong `src/assistant_api/main.py`:**
   ```python
   @app.get("/v1/feedback", response_model=list[FeedbackOut], tags=["feedback"], dependencies=[Depends(require_admin)])
   def list_feedback() -> list[FeedbackOut]:
       return feedback_store
   ```
3. **Quy trình Git Release:**
   - Sau khi các thành viên mở PR, Tech Lead tiến hành review, duyệt merge vào nhánh `main`.
   - Tạo git tag phiên bản:
     ```bash
     git checkout main
     git pull origin main
     git tag v0.4-api
     git push origin v0.4-api
     ```
   - Nộp link tag `v0.4-api` lên LMS trước 23:59 ngày trước buổi Lab 5.

---

### 🧑‍💻 THÀNH VIÊN 2: Core Chat & Reflection (H2)
1. **Hiện thực Task T1 (Mục D.3) trong `src/assistant_api/main.py`:**
   ```python
   @app.post("/v1/chat", response_model=ChatResponse, tags=["chat"], responses={422: {"model": ErrorResponse}, 429: {"model": ErrorResponse}})
   def chat(req: ChatRequest, request: Request) -> ChatResponse:
       # TV6 sẽ thêm 3 dòng rate limit ở đầu hàm này sau
       resp = service.handle(Message(text=req.message, session_id=req.session_id))
       return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])
   ```
2. **Soạn thảo nội dung Reflection H2 (5 dòng)** để cả nhóm tham khảo đưa vào mô tả PR:
   > *"Ở Lab 3, việc gọi trực tiếp `service.handle()` là lời gọi hàm nội bộ (in-process function call), đòi hỏi client và server phải viết chung một ngôn ngữ Python và chạy trên cùng một máy tính. Sang Lab 4, việc bọc qua giao thức HTTP REST API (`POST /v1/chat`) cho phép tách rời hoàn toàn giữa client và backend. Nhờ đó, giao diện web, ứng dụng di động hay các dịch vụ khác có thể giao tiếp dễ dàng qua định dạng chuẩn JSON mà không phụ thuộc vào công nghệ của nhau. Đối với làm việc nhóm, kiến trúc này giúp phân tách trách nhiệm rõ ràng: team frontend và team backend có thể phát triển độc lập dựa trên API contract đã thống nhất từ trước mà không làm ảnh hưởng đến mã nguồn của nhau."*

---

### 🧑‍💻 THÀNH VIÊN 3: Feedback System & Validation
1. **Hiện thực Task T2 (Mục D.4) trong `src/assistant_api/main.py`:**
   ```python
   @app.post("/v1/feedback", response_model=FeedbackOut, status_code=201, tags=["feedback"])
   def add_feedback(fb: FeedbackIn) -> FeedbackOut:
       item = FeedbackOut(**fb.model_dump(), id=len(feedback_store) + 1, created_at=datetime.now(timezone.utc))
       feedback_store.append(item)
       return item
   ```
2. **Kiểm tra nghiệp vụ:**
   - Dùng Swagger UI (`/docs`) thử gửi feedback với `rating = 5` -> Phải nhận mã lỗi `422 Unprocessable Entity` (vì schema `FeedbackIn` chỉ chấp nhận `-1, 0, 1`).
   - Gửi feedback với `rating = 1` -> Nhận phản hồi mã `201 Created` kèm `id` và thời gian `created_at`.

---

### 🧑‍💻 THÀNH VIÊN 4: External Weather & Resilience
1. **Hiện thực Task T4 (Mục D.6) trong `src/assistant_api/main.py`:**
   ```python
   @app.get("/v1/weather", response_model=Weather, tags=["external"], responses={503: {"model": ErrorResponse}})
   def campus_weather() -> Weather:
       try:
           return weather.current()
       except ExternalServiceError:
           raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Weather service unavailable") from None
   ```
2. **Trả lời câu hỏi Exercise (Trang 16):**
   * *Câu hỏi:* Đọc `test_weather_down_returns_503` trong `tests/test_api.py`, giải thích trong 1 câu cách test giả lập lỗi sập server thời tiết.
   * *Câu trả lời chuẩn:* Test sử dụng fixture `weather_with(...)` truyền vào một hàm mock giả lập trả về mã lỗi HTTP 500 (hoặc exception) thay vì gửi request qua internet thật, từ đó kiểm tra endpoint `/v1/weather` có bắt đúng lỗi và trả về HTTP 503 hay không.

---

### 🧑‍💻 THÀNH VIÊN 5: Office Directory Feature (Homework H1 - 2 điểm)
1. **Bước 1: Chỉnh sửa `src/assistant_core/knowledge.py`:**
   Trong class `OfficeDirectory`, bổ sung hàm `all()`:
   ```python
   def all(self) -> list[Office]:
       """Return all offices sorted by name."""
       return sorted(self._offices.values(), key=lambda o: o.name)
   ```
2. **Bước 2: Bổ sung endpoint trong `src/assistant_api/main.py`:**
   ```python
   @app.get("/v1/offices", tags=["knowledge"])
   def list_offices() -> list[dict]:
       return [o.__dict__ for o in service.offices.all()]
   ```
3. **Bước 3: Viết 2 tests trong `tests/test_api.py`:**
   ```python
   def test_list_offices_success(client):
       res = client.get("/v1/offices")
       assert res.status_code == 200
       data = res.json()
       assert isinstance(data, list)
       assert any(office.get("name") == "Library" for office in data)
   ```

---

### 🧑‍💻 THÀNH VIÊN 6: Rate Limiting Bonus (+1 điểm) & Test Suite
1. **Hiện thực Bonus Part F trong `src/assistant_api/main.py`:**
   Chèn đoạn kiểm tra giới hạn request vào đầu hàm `chat()`:
   ```python
   def chat(req: ChatRequest, request: Request) -> ChatResponse:
       # BONUS: rate limiting
       client = request.client.host if request.client else "unknown"
       if not limiter.allow(client):
           raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests")

       resp = service.handle(Message(text=req.message, session_id=req.session_id))
       return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])
   ```
2. **Kích hoạt test bonus trong `tests/test_api.py`:**
   Tìm đến hàm `test_rate_limit` và **xóa hoặc comment** dòng `@pytest.mark.skip(...)`.
3. **Chạy toàn bộ Pytest:**
   ```bash
   pytest -q
   ```
   *Kết quả mong đợi:* **`24 passed`** (bao gồm cả test rate limit, không còn test nào bị skip).

---

### 🧑‍💻 THÀNH VIÊN 7: QA Testing, Docs & Worksheets
1. **Kiểm thử với Script curl:**
   Khởi động server trên một terminal:
   ```bash
   uvicorn assistant_api.main:create_app --factory --reload
   ```
   Mở terminal thứ hai và chạy:
   ```bash
   bash api-tests/curl_tests.sh
   ```
   Đảm bảo tất cả response codes trả về đúng như mong đợi (`[200]`, `[422]`, `[201]`, `[401]`, `[503]`).
2. **Hỗ trợ 6 thành viên chụp ảnh Swagger UI (`/docs`):**
   * Truy cập `http://127.0.0.1:8000/docs`.
   * Bấm chọn `POST /v1/chat` -> Chọn **Try it out**.
   * Nhập body:
     ```json
     {
       "message": "tuition for 18 credits and 2 retake",
       "session_id": "test-session"
     }
     ```
   * Nhấn **Execute**, chụp ảnh màn hình thấy rõ Response Code `200` và JSON trả về có `request_id`.
3. **Hoàn thiện 2 Worksheets:**
   * Điền thông tin vào `docs/api_contract.md` (hoặc `lab04/worksheets/api_contract.md`).
   * Điền phân tích sự cố bên ngoài vào `lab04/worksheets/external_api_failure.md`.

---

## 📋 4. TEMPLATE GITHUB ISSUES (CHO 7 THÀNH VIÊN)

Mỗi thành viên tạo một Issue trên GitHub theo mẫu chuẩn của môn học:

### 📌 Issue Template chung (`.github/ISSUE_TEMPLATE/task.md`):
```markdown
---
name: Task
about: A unit of work for the sprint
---
## Goal
<Mô tả mục tiêu của tính năng, liên kết với use case / hợp đồng API>

## Acceptance criteria
- [ ] Tiêu chí nghiệm thu 1
- [ ] Tiêu chí nghiệm thu 2
- [ ] Unit tests pass 100%

## Notes
<Thông tin dữ liệu, interface, rủi ro>
```

---

### 📝 Danh sách 7 Issue mẫu sẵn sàng dùng:

#### Issue cho TV1 (Admin Auth & Release):
* **Title:** `api: implement GET /v1/feedback admin endpoint and release tag (#01)`
* **Labels:** `feat`, `backend`, `security`, `M4`
* **Assignee:** `@TV1`
* **Content:**
  ```markdown
  ## Goal
  Hiện thực endpoint GET /v1/feedback trả về danh sách feedback, bảo vệ bởi API Key.
  
  ## Acceptance criteria
  - [ ] Endpoint yêu cầu header `X-API-Key` khớp với biến môi trường `API_ADMIN_KEY`.
  - [ ] Trả về danh sách `FeedbackOut` với status 200 khi đúng key.
  - [ ] Trả về 401 Unauthorized khi thiếu hoặc sai API key.
  - [ ] File `.env` không bị commit vào Git.
  - [ ] Tag release `v0.4-api` được tạo sau khi tích hợp toàn bộ API.
  ```

#### Issue cho TV2 (Chat Core Integration):
* **Title:** `api: implement POST /v1/chat endpoint (#02)`
* **Labels:** `feat`, `backend`, `chat`, `M4`
* **Assignee:** `@TV2`
* **Content:**
  ```markdown
  ## Goal
  Kết nối HTTP POST /v1/chat với service.handle() của assistant_core từ Lab 3.
  
  ## Acceptance criteria
  - [ ] Nhận ChatRequest (message: 1–2000 chars, session_id).
  - [ ] Gọi service.handle(Message(...)) và trả về ChatResponse.
  - [ ] Tự động sinh `request_id` dạng hex 12 ký tự ngẫu nhiên.
  - [ ] Trả về 422 khi message rỗng hoặc không đúng định dạng.
  ```

#### Issue cho TV3 (Feedback System):
* **Title:** `api: implement POST /v1/feedback endpoint (#03)`
* **Labels:** `feat`, `backend`, `feedback`, `M4`
* **Assignee:** `@TV3`
* **Content:**
  ```markdown
  ## Goal
  Hiện thực endpoint POST /v1/feedback để người dùng gửi phản hồi đánh giá.
  
  ## Acceptance criteria
  - [ ] Nhận FeedbackIn (request_id, rating: -1/0/1, comment tối đa 500 ký tự).
  - [ ] Sinh `id` tăng dần và `created_at` UTC.
  - [ ] Lưu vào `feedback_store` trong bộ nhớ và trả về status 201 Created.
  - [ ] Trả về 422 Unprocessable khi rating nằm ngoài {-1, 0, 1}.
  ```

#### Issue cho TV4 (Weather Resilience):
* **Title:** `api: implement GET /v1/weather endpoint with failure resilience (#04)`
* **Labels:** `feat`, `backend`, `external`, `M4`
* **Assignee:** `@TV4`
* **Content:**
  ```markdown
  ## Goal
  Cung cấp thời tiết cơ sở Nguyễn Văn Cừ qua GET /v1/weather, xử lý sự cố dịch vụ bên ngoài.
  
  ## Acceptance criteria
  - [ ] Gọi WeatherClient lấy thời tiết với timeout 3s, retry và cache fallback.
  - [ ] Bắt ngoại lệ ExternalServiceError và trả về mã sạch HTTP 503.
  - [ ] Vượt qua unit test mock mạng `test_weather_down_returns_503`.
  ```

#### Issue cho TV5 (Offices Directory):
* **Title:** `api: add GET /v1/offices endpoint and OfficeDirectory.all() (#05)`
* **Labels:** `feat`, `backend`, `knowledge`, `M4`
* **Assignee:** `@TV5`
* **Content:**
  ```markdown
  ## Goal
  Bổ sung tính năng truy xuất danh sách phòng ban trường học theo Homework H1.
  
  ## Acceptance criteria
  - [ ] Bổ sung phương thức `all()` trong `OfficeDirectory` sắp xếp theo tên phòng.
  - [ ] Bổ sung route `GET /v1/offices` trả về danh sách các văn phòng.
  - [ ] Bổ sung 2 bài tests trong `test_api.py` (kiểm tra status 200 và có phòng "Library").
  ```

#### Issue cho TV6 (Rate Limiting & Pytest Suite):
* **Title:** `perf: add IP-based rate limiting to /v1/chat and enable test (#06)`
* **Labels:** `perf`, `security`, `bonus`, `M4`
* **Assignee:** `@TV6`
* **Content:**
  ```markdown
  ## Goal
  Triển khai RateLimiter cho POST /v1/chat để chống spam request (Bonus Part F).
  
  ## Acceptance criteria
  - [ ] Giới hạn số request theo IP client, trả về mã HTTP 429 Too Many Requests khi quá ngưỡng.
  - [ ] Bỏ skip test `test_rate_limit` trong `tests/test_api.py`.
  - [ ] Chạy `pytest -q` đạt kết quả 24/24 tests pass.
  ```

#### Issue cho TV7 (QA, Docs & Evidence):
* **Title:** `docs: complete worksheets, curl tests and review swagger screenshots (#07)`
* **Labels:** `docs`, `test`, `qa`, `M4`
* **Assignee:** `@TV7`
* **Content:**
  ```markdown
  ## Goal
  Đảm bảo kiểm thử đầy đủ qua curl và hoàn tất tài liệu phục vụ báo cáo.
  
  ## Acceptance criteria
  - [ ] Chạy thành công kịch bản `bash api-tests/curl_tests.sh`.
  - [ ] Hoàn thành worksheet `api_contract.md` và `external_api_failure.md`.
  - [ ] Kiểm tra 6 thành viên chụp đúng ảnh Swagger UI `/docs` cho PR cá nhân.
  ```

---

## 📨 5. TEMPLATE PULL REQUEST (PR TEMPLATE)

Tất cả 7 thành viên sử dụng mẫu sau để mở PR lên GitHub (lưu tại `.github/pull_request_template.md`):

```markdown
## What
<!-- Tóm tắt ngắn gọn 1-2 câu về nội dung thay đổi trong PR này -->
Implement endpoint <Tên endpoint> / Tính năng <Tên tính năng>.

## Why
<!-- Liên kết Issue tương ứng -->
Closes #<Số_Issue>. Tuân thủ hợp đồng API Lab 4 của môn học CSC10014.

## How tested
- [x] Unit tests: `pytest -q` (23 passed / 24 passed if bonus).
- [x] Manual test: Đã kiểm thử qua Swagger UI `/docs` và `curl`.

## Evidence (Ảnh chụp minh chứng bắt buộc)
<!-- Dán ảnh chụp màn hình Swagger UI (/docs) khi gọi thành công POST /v1/chat tại đây -->
![Swagger UI /docs chat call](<Đường dẫn ảnh hoặc paste trực tiếp vào GitHub>)

## AI use
<!-- Ghi rõ công cụ AI đã dùng, việc đã giao cho AI, phần tự kiểm chứng - KHÔNG ĐƯỢC ĐỂ TRỐNG -->
- **Công cụ sử dụng**: Copilot / Claude / ChatGPT / Cursor
- **Yêu cầu đã giao cho AI**: Sinh code cho hàm <tên_hàm> dựa trên hướng dẫn trong `lab04_resource/guide.md`.
- **Phần tự chỉnh sửa/kiểm chứng**: Đã kiểm tra logic, gỡ bỏ code thừa, bổ sung docstrings và chạy test pass.

## Reflection (H2 - Bắt buộc 5 dòng)
Ở Lab 3, việc gọi trực tiếp `service.handle()` là lời gọi hàm nội bộ (in-process function call), đòi hỏi client và server phải viết chung một ngôn ngữ Python và chạy trên cùng một máy tính. Sang Lab 4, việc bọc qua giao thức HTTP REST API (`POST /v1/chat`) cho phép tách rời hoàn toàn giữa client và backend. Nhờ đó, giao diện web, ứng dụng di động hay các dịch vụ khác có thể giao tiếp dễ dàng qua định dạng chuẩn JSON mà không phụ thuộc vào công nghệ của nhau. Đối với làm việc nhóm, kiến trúc này giúp phân tách trách nhiệm rõ ràng: team frontend và team backend có thể phát triển độc lập dựa trên API contract đã thống nhất từ trước mà không làm ảnh hưởng đến mã nguồn của nhau.

## Checklist
- [x] Code nhỏ gọn, tập trung (< 300 dòng).
- [x] Tất cả test case đều passed, không sửa đổi/làm yếu test có sẵn.
- [x] Không commit `.env`, token hoặc secret key lên GitHub.
- [x] Đã cập nhật docs / README nếu có thay đổi.
```

---

## 🤖 6. HƯỚNG DẪN SỬ DỤNG `guide.md` & `lab04_resource` LÀM NGUỒN TRI THỨC CHO AI

Để tận dụng tối đa các trợ lý AI lập trình (như GitHub Copilot, Cursor, Claude Code, ChatGPT, Antigravity) mà vẫn tuân thủ nghiêm ngặt quy tắc liêm chính học thuật và bảo toàn kiến trúc của môn học, nhóm thực hiện theo hướng dẫn sau:

### 6.1. Cấu hình file `AGENTS.md` tại thư mục gốc của Repo
Tạo file `AGENTS.md` ở root của repository nhóm để mọi AI Agent tự động đọc hiểu bối cảnh và quy tắc:
```markdown
# AGENTS.md — Quy tắc làm việc cho AI Coding Agents

- Môi trường & Thiết lập: Python 3.12, FastAPI, Uvicorn, Pytest.
- Tri thức nguồn (Knowledge Base): Luôn đọc và tuân thủ tuyệt đối tài liệu tại `lab04_resource/guide.md`.
- Kiểm thử bắt buộc: Mọi đoạn code sinh ra phải pass `pytest -q`. KHÔNG ĐƯỢC phép sửa đổi, xóa bỏ hoặc làm yếu các unit tests đã có.
- Định dạng phản hồi: Tất cả lỗi trả về phải tuân thủ schema chuẩn: `{"error": {"code": "...", "message": "..."}}`.
- Bảo mật: TUYỆT ĐỐI KHÔNG commit file `.env`, API key bí mật, hoặc dữ liệu nhạy cảm.
- Quy tắc Git: Không bao giờ push trực tiếp vào branch `main`. Làm việc trên feature branch và mở Pull Request theo template.
```

### 6.2. Cách Prompt cho AI bằng cách tham chiếu `lab04_resource/guide.md`
Khi nhờ AI sinh code hoặc giải thích, hãy dẫn link/mention file `guide.md` để AI bám sát thiết kế:

**Mẫu Prompt chuẩn cho thành viên:**
> *"Tôi đang làm việc trong dự án Study Assistant (môn CSC10014). Hãy đọc file `@lab04_resource/guide.md`. Tôi là **Thành viên [X]**, được phân công làm **Task [T1/T2/T3/T4/H1/Bonus]**.*
> *Yêu cầu:*
> 1. *Viết mã nguồn cho task này vào đúng file quy định.*
> 2. *Giữ nguyên vẹn định dạng lỗi của hệ thống (`JSONResponse` với mã lỗi chuẩn).*
> 3. *Không sửa đổi logic của các bài unit test có sẵn.*
> 4. *Giải thích ngắn gọn cách hoạt động của đoạn mã để tôi tự review."*

### 6.3. Nhật ký sử dụng AI (`docs/ai-use-log.md`)
Theo quy định tại Chương 14 của giáo trình môn học, mỗi lần sử dụng AI có ý nghĩa cần ghi lại 1 dòng vào bảng:

| Ngày | Thành viên | Công cụ | Yêu cầu đã giao cho AI | Phần tự chỉnh sửa / Giữ lại | Đã kiểm chứng qua |
|:---:|:---:|:---:|:---|:---|:---|
| 26/10 | TV2 | Copilot | Sinh endpoint `POST /v1/chat` | Tự bổ sung `uuid.hex[:12]` | 5 unit tests pass |
| 26/10 | TV4 | Claude | Xử lý ngoại lệ `ExternalServiceError` | Bổ sung `from None` cho HTTPException | `test_api.py` pass |
| 26/10 | TV5 | ChatGPT | Hàm `OfficeDirectory.all()` | Giữ nguyên logic `sorted` theo tên | 2 tests mới pass |

---

## 🏁 7. CHECKLIST HOÀN TẤT TRƯỚC KHI ĐÓNG SPRINT

- [ ] Cả 7 thành viên đều đã mở Issue và gán Assignee đúng theo Bảng phân công.
- [ ] 7 thành viên đều đã mở Pull Request cá nhân, có ảnh chụp màn hình `/docs` và đoạn văn H2.
- [ ] Các thành viên tiến hành Review chéo PR của nhau (dùng nhãn `Praise:`, `Question:`, `Suggestion:`).
- [ ] Chạy `pytest -q` đạt kết quả tối đa **24 passed** (hoàn thành cả Bonus Rate Limiting).
- [ ] Tech Lead duyệt merge tất cả các PR hợp lệ vào nhánh `main`.
- [ ] Tech Lead gắn git tag **`v0.4-api`** và nộp đường dẫn tag/PR lên LMS đúng hạn.
