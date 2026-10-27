# KẾ HOẠCH HOÀN THÀNH NHIỆM VỤ THÀNH VIÊN 1 (TECH LEAD)
**Họ và tên:** Nguyễn Bá Duy  
**Vai trò:** Thành viên 1 — Tech Lead & Auth Lead  
**Dự án:** Study Assistant (`assistant_core` / `assistant_api`)  
**Mã Issue:** `#01` (`api: implement GET /v1/feedback admin endpoint and release tag (#01)`)  
**Tên Branch:** `feat/01-feedback-admin`  
**Mục tiêu điểm số:** 10/10 điểm chính thức + 1 điểm Bonus = **11/10 điểm**

---

## 🎯 I. MỤC TIÊU VÀ TRÁCH NHIỆM CHÍNH

Thành viên 1 đảm nhận hai vai trò song song:
1. **Nhiệm vụ Kỹ thuật Cá nhân (Personal Deliverables)**:
   - Cấu hình môi trường bảo mật (`.env`, `.gitignore`, biến `API_ADMIN_KEY`).
   - Lập trình **Task T3 (Mục D.5)**: Endpoint `GET /v1/feedback` (xác thực admin bằng `X-API-Key`).
   - Chụp ảnh Swagger UI (`/docs`) cho `/v1/chat`, soạn Reflection H2 và mở Pull Request cá nhân.
2. **Nhiệm vụ Quản trị Kỹ thuật & Tích hợp Nhóm (Tech Lead Deliverables)**:
   - Điều phối 6 thành viên mở branch, issue và PR theo quy chuẩn.
   - Tiến hành Review PR chéo, kiểm soát an toàn mã nguồn (không leak secret, không suy yếu unit test).
   - Hợp nhất (merge) toàn bộ các nhánh tính năng vào `main`.
   - Đảm bảo toàn bộ 24 test cases của Pytest đều pass trên `main`.
   - Gắn release tag **`v0.4-api`** và nộp bài trên LMS.

---

## 📅 II. LỘ TRÌNH THỰC HIỆN CHI TIẾT (STEP-BY-STEP)

```
[Giai đoạn 1: Khởi tạo & Cấu hình] ──> [Giai đoạn 2: Lập trình Task T3] ──> [Giai đoạn 3: Test & Mở PR Cá nhân]
                                                                                        │
[Giai đoạn 6: Nộp bài LMS] <── [Giai đoạn 5: Kiểm định & Tag v0.4-api] <── [Giai đoạn 4: Review & Merge Nhóm]
```

---

### 🔹 GIAI ĐOẠN 1: KHỞI TẠO & CẤU HÌNH BẢO MẬT (Thời gian: 15–20 phút)

1. **Khởi tạo Issue trên GitHub:**
   - Tạo Issue `#01` với tiêu đề: `api: implement GET /v1/feedback admin endpoint and release tag (#01)`.
   - Gán `Assignee: @Duy`, Labels: `feat`, `backend`, `security`, `M4`.
2. **Cấu hình biến môi trường an toàn:**
   - Sao chép file `.env.example` thành `.env`:
     ```bash
     cp .env.example .env
     ```
   - Mở `.env` và thiết lập khóa bí mật cho Admin:
     ```env
     API_ADMIN_KEY=change-me
     ```
   - **Kiểm tra an toàn**: Chạy lệnh `git status` đảm bảo file `.env` **KHÔNG** xuất hiện trong danh sách untracked/staged files (vì đã nằm trong `.gitignore`).

---

### 🔹 GIAI ĐOẠN 2: LẬP TRÌNH TASK T3 (MỤC D.5) (Thời gian: 15 phút)

1. **Vị trí file:** `src/assistant_api/main.py`
2. **Hiện thực code:**
   Tìm đến hàm `list_feedback()` (dòng ~81) và thay thế dòng `raise NotImplementedError("T3")` bằng 1 dòng code duy nhất:
   ```python
   @app.get("/v1/feedback", response_model=list[FeedbackOut], tags=["feedback"], dependencies=[Depends(require_admin)])
   def list_feedback() -> list[FeedbackOut]:
       return feedback_store
   ```
3. **Hiểu rõ cơ chế bảo mật (Security Mechanism):**
   - Tham số `dependencies=[Depends(require_admin)]` tự động kích hoạt hàm `require_admin` trước khi request đi vào `list_feedback()`.
   - Hàm `require_admin` đọc header `x-api-key`. Nếu thiếu header hoặc giá trị khác `settings.api_admin_key`, FastAPI lập tức quăng lỗi `HTTPException(401, "Missing or invalid API key")`.

---

### 🔹 GIAI ĐOẠN 3: KIỂM THỬ CÁ NHÂN & BẰNG CHỨNG PR (Thời gian: 25 phút)

1. **Khởi động server phát triển:**
   ```bash
   uvicorn assistant_api.main:create_app --factory --reload
   ```
2. **Kiểm thử thủ công endpoint T3:**
   - Mở terminal thứ 2, kiểm tra trường hợp **không có key** (mong đợi `401 Unauthorized`):
     ```bash
     curl -i http://127.0.0.1:8000/v1/feedback
     ```
   - Kiểm tra trường hợp **có header key hợp lệ** (mong đợi `200 OK` và mảng rỗng `[]`):
     ```bash
     curl -i -H "X-API-Key: change-me" http://127.0.0.1:8000/v1/feedback
     ```
3. **Chụp ảnh Swagger UI (`/docs`) để lấy minh chứng nộp bài:**
   - Mở trình duyệt tại `http://127.0.0.1:8000/docs`.
   - Bấm vào `POST /v1/chat` -> **Try it out** -> nhập message -> **Execute**.
   - Chụp ảnh màn hình thấy rõ phản hồi HTTP `200` và `request_id`.
4. **Mở Pull Request cá nhân của Duy:**
   - Đẩy branch lên GitHub:
     ```bash
     git push -u origin feat/01-feedback-admin
     ```
   - Tạo PR vào nhánh `main` sử dụng PR Template chuẩn, kèm theo:
     - Đính kèm ảnh chụp màn hình `/docs`.
     - Đoạn văn Reflection H2 (5 dòng).
     - Khai báo mục `AI use`.

---

### 🔹 GIAI ĐOẠN 4: ĐIỀU PHỐI REVIEW & HỢP NHẤT MÃ NGUỒN (Thời gian: 45–60 phút)

Với vai trò Tech Lead, Duy phụ trách rà soát và duyệt merge PR của 6 thành viên theo thứ tự logic:

| Thứ tự merge | Thành viên | Tính năng | Checklist cần kiểm tra trước khi Approve |
|:---:|:---|:---|:---|
| **1** | **Đạt** (TV2) | T1: `POST /v1/chat` | Đã gọi `service.handle()`, có sinh `request_id`, format trả về `ChatResponse`. |
| **2** | **Hùng** (TV3) | T2: `POST /v1/feedback` | Rating chỉ nhận `-1, 0, 1` (nếu khác báo 422), tự tăng `id`, status code là 201. |
| **3** | **Tâm** (TV4) | T4: `GET /v1/weather` | Đã bọc `try/except ExternalServiceError` thành HTTP 503, pass test mock mạng. |
| **4** | **Trung Anh** (TV5) | H1: `GET /v1/offices` | `knowledge.py` có hàm `all()` sắp xếp theo tên, có 2 tests mới trong `test_api.py`. |
| **5** | **Bội Anh** (TV6) | Bonus Part F: Rate Limiter | Có middleware/check IP ra lỗi 429, test `test_rate_limit` đã bỏ skip và pass. |
| **6** | **Quỳnh** (TV7) | QA & Worksheets | Hoàn tất `api_contract.md`, `external_api_failure.md`, script curl chạy pass. |

**Quy tắc Review (Review Etiquette):**
- Sử dụng đúng nhãn comment: `Blocking:` (lỗi bắt buộc sửa), `Question:`, `Suggestion:`, `Praise:`.
- Tuyệt đối không duyệt PR nếu CI báo đỏ hoặc có commit lộ API key.

---

### 🔹 GIAI ĐOẠN 5: KIỂM ĐỊNH CUỐI & GẮN RELEASE TAG (Thời gian: 15 phút)

Sau khi hợp nhất toàn bộ 6 PR và PR cá nhân của Duy vào nhánh `main`:
1. **Chuyển về `main` và đồng bộ mã nguồn:**
   ```bash
   git switch main
   git pull origin main
   ```
2. **Chạy toàn bộ Pytest tự động:**
   ```bash
   pytest -q
   ```
   *Yêu cầu bắt buộc:* Phải đạt **`24 passed`** (bao gồm 23 test chuẩn + 1 test bonus rate limit).
3. **Tạo Release Tag:**
   ```bash
   git tag -a v0.4-api -m "Release v0.4-api: Full REST API implementation for Study Assistant"
   git push origin v0.4-api
   ```

---

### 🔹 GIAI ĐOẠN 6: BÀN GIAO & NỘP BÀI LÊN LMS (Trước 23:59 ngày trước Lab 5)

Duy kiểm tra và nộp 2 đường link lên hệ thống LMS:
1. **Link PR cá nhân của Duy** (kèm ảnh Swagger UI `/docs` và Reflection H2).
2. **Link Release Tag `v0.4-api` của nhóm** đại diện cho toàn bộ sản phẩm hoàn chỉnh của Sprint Lab 4.
