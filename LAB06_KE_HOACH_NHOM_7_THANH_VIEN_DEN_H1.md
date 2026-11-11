# KẾ HOẠCH LAB 06 — CHỈ C, D, E, F, H1

**Phiên bản:** 11/11/2026 — điều chỉnh từ hiện trạng repo, KHÔNG triển khai lại từ đầu  
**Repo:** https://github.com/Computational-Thinking-Project/assistant_core_lab  
**Tài liệu đối chiếu:** `CSC10014_2026_Lab06_AI_Services_RAG_Tutorial.docx(3).pdf`, các trang 10–16 và 19  
**Nhóm (đúng thứ tự):** 1. Duy · 2. Trung Anh · 3. Đạt · 4. Hùng · 5. Bội Anh · 6. Quỳnh · 7. Tâm  
**Nguồn thông tin kỹ thuật:** trạng thái nhánh/PR và diff GitHub đã kiểm tra ngày 11/11/2026. Chưa có kết quả chạy toàn bộ test trên commit tích hợp cuối cùng; mọi số test trong các PR là bằng chứng của *từng snapshot*, không phải chứng nhận bản cuối.

> **Mục tiêu:** hoàn thành đúng các phần **C, D, E, F, H1** trên **một ứng dụng Assistant chung**; tận dụng code đã viết, loại bỏ công việc cá nhân trùng lặp, không phá chức năng Lab 3–5. Các thao tác Git bên dưới là **quy trình phối hợp kỹ thuật**, không phải yêu cầu riêng của PDF C/D/E/F/H1.

---

## 1. Ranh giới yêu cầu — đối chiếu PDF

| Phần | Yêu cầu cần chứng minh | Vị trí PDF | Đầu ra tối thiểu |
|---|---|---|---|
| **C — Knowledge Base** | Dùng 3 Markdown mẫu, metadata/chunks, tìm kiếm BM25; thử **3 câu hỏi** tự chọn, ghi top chunk ID và score, nhận xét trường hợp bất ngờ | Trang 10 | KB hoạt động; 3 truy vấn được ghi trong báo cáo |
| **D — LLM, A2** | `StubLLM`, prompt JSON có cấu trúc; `parse_draft()` buộc câu trả lời không abstain phải có `source_ids` không rỗng và tất cả ID thuộc nguồn được truy xuất; chạy citation test | Trang 11–12 | `llm.py`/prompt đúng; test A2 pass |
| **E — A1/abstain** | No-hit hoặc `best_score < min_score` phải abstain **trước khi gọi LLM**; chạy test và thử CLI, privacy, deterministic fee; giữ fallback khi model hỏng | Trang 13–14 | `RagAnswerer` đúng, demo/test có nguồn, abstain và fee |
| **F — Compare Paths** | Chạy `python eval/compare_paths.py` trên 20 case gốc, bảng `correct / abstain ok / p50 ms / max ms` và **3 câu**: chọn path, lý do, lỗi ưu tiên sửa | Trang 15–16 | `docs/lab6/path_comparison.md` |
| **H1 — Five more tests** | Thêm **5 case tổng cộng cho sản phẩm nhóm**: 3 `expect_source`, 2 `expect_abstain`; chạy lại bảng và giải thích một lỗi nếu có | Trang 19 | `eval/cases.jsonl` có 25 case; báo cáo trước/sau |

**KHÔNG nằm trong phạm vi đã chọn:** code S1–S3 của phần B; phần A; H2 reflection; H3; Ollama/real LLM bonus; 35 test H1 riêng cho 7 người; 7 bản starter độc lập; tag `v0.6-ai` như một yêu cầu bắt buộc; sửa hết E13–E15/E19; vector DB, embedding, frontend, migration hoặc mở rộng API không cần thiết.

**Lưu ý về chấm điểm:** Rubric tổng quát trang 20 PDF vẫn có S1–S3 và H2. Bản kế hoạch này tuân theo **phạm vi được nhóm lựa chọn**, không khẳng định LMS/giảng viên đã miễn các đầu điểm ngoài phạm vi. PR cuối/nộp LMS thực hiện theo thông báo lớp nếu có.

---

## 2. Hiện trạng repo — không giao làm lại phần đã xong

**Baseline:** `main` = `27fbea699d16968ceb169b795bcf979e69bc1b61`.  
**Nhánh tích hợp:** `integration/lab06-v0.6` = `e8ad57e7e42dad4f265b89a9c9dc30c30362f8aa` tại lúc kiểm tra; đi trước `main` 2 commit. Cần `git fetch origin` xác nhận lại trước khi thao tác.

| Phần việc/PR | Hiện trạng đã xác minh | Quyết định |
|---|---|---|
| **#50 — Đạt:** `Response`, `RagAnswerer`, A1, retry/fallback, test | Đã **merge vào integration**; có `src/assistant_core/rag/answerer.py`, `tests/test_rag_answerer.py` | **Giữ.** Chỉ cập nhật nếu test tích hợp chỉ ra lỗi; sau khi A2 thật có mặt, loại bỏ/khóa fallback parser giả lập che lỗi import |
| **#60 — Trung Anh:** `rag/chunker.py`, `rag/index.py`, BM25, fixtures, test | Đã **merge vào integration** | **Giữ.** Không port lại; chỉ xác minh KB thật và 3 truy vấn C |
| **#62 — Bội Anh:** `data/kb/*.md`, `guard.py`, guard tests | **PR mở**; GitHub từng báo `mergeable=false`, cần kiểm tra conflict/checks mới nhất | **Sửa nếu cần rồi merge**; không viết lại KB hoặc guard |
| **#52 — Duy:** service wiring, test RAG service | **PR mở**; đang có fallback import/config có thể khiến RAG âm thầm không bật | **Giữ, chỉnh nhỏ** sau khi có KB/LLM thật; chứng minh đường RAG chạy thật |
| **#64 — Hùng:** `ChatResponse` + test API | **PR mở**, branch `feat/lab06-hung-api`; GitHub báo mergeable ở lúc kiểm tra | **Giữ**, review và merge; không tạo thêm PR API mới |
| **#56 — Tâm:** `eval/compare_paths.py`, 20 case gốc, báo cáo, smoke tests | **PR mở**; evaluator đang dùng `FallbackBM25Index`, `FallbackRagAnswerer`, `build_service_adapter` | **Giữ nhưng sửa**: đánh giá bằng module production sau tích hợp, thêm 5 case H1, chạy lại bảng |
| **Quỳnh — LLM/A2:** `llm.py`, prompt, settings | **Chưa thấy PR module riêng** khi kiểm tra nhánh/PR Lab 06 | **Công việc còn thiếu ưu tiên cao**; tạo một PR module tới integration |
| **#49/#51/#55/#61/#63:** PR bài cá nhân | PR mở, target `exercise/lab06-starter-base` | **Ngừng phát triển; lưu case/báo cáo cần dùng rồi đóng** nếu LMS không yêu cầu giữ từng PR |
| **#59 — Trung Anh:** PR bài cá nhân | Đã merge vào `exercise/lab06-starter-base`, **không phải integration/main** | **Để nguyên**, không revert và không kéo code sang main |

**Điểm rủi ro đã kiểm tra trong code:**

1. `RagAnswerer` (#50) hiện có `try: from assistant_core.llm import ... except ImportError` và **bản `parse_draft` dự phòng**. Sau khi Quỳnh cung cấp module chính, các test A2 phải kiểm tra chính `assistant_core.llm.parse_draft`, không được pass nhờ parser dự phòng.
2. `build_service()` (#52) chỉ dựng RAG nếu `settings.kb_dir` đã có; một số lỗi import có thể dẫn đến `rag=None` mà không báo. **Một bài test dùng `data/kb` thật + stub thật** là bắt buộc để xác nhận RAG đã bật.
3. `compare_paths.py` (#56) dùng các implementation RAG **trùng lặp** với production. Nếu giữ, số liệu có thể phản ánh code giả lập thay vì code tích hợp; phải bỏ các bản tương đương và chạy evaluator trên module chính.
4. KB mẫu là **dữ liệu lớp học**, không phải quy chế trường được xác minh. Các kết quả 42/116/129/131 passed trong mô tả PR không được tự nhận là kết quả test cuối.

---

## 3. Phân công 7 người — CHỈ công việc còn phải làm

### TV1 — Duy: sửa PR #52, tích hợp vào service

**File đang phụ trách:** `src/assistant_core/service.py`, `tests/test_service_rag.py`.  
**Không làm lại:** router, BM25, `llm.py`, `answerer.py`, KB/guard hoặc API schema.

1. Khi #62 và PR Quỳnh đã có code sử dụng được, cập nhật nhánh #52 từ integration, giải quyết conflict thật nếu có.
2. Bảo toàn `AssistantService(..., rag=None)` và các xử lý deterministic của fee/office; `RULE` phải qua guard trước RAG.
3. Xác nhận `build_service(settings)` nhận `kb_dir=Path('data/kb')`, `retrieval_kind='bm25'`, `retrieval_min_score=2.0`, `llm_provider='stub'` và thực sự khởi tạo `RagAnswerer` **có `llm`**; không chỉ kiểm tra bằng spy/mock.
4. Khi cấu hình rõ ràng yêu cầu RAG mà import/config sai, test phải phát hiện lỗi; không chấp nhận ứng dụng lặng lẽ chạy bằng legacy và được chấm là RAG.
5. Chỉ sửa CLI nếu test/demo thực tế phát hiện lỗi; giữ API/DB Lab 4–5 không đổi.

**DoD:** chạy một câu dùng nguồn (`S26#3` hoặc `H26#5.3`) bằng service production có `path='llm'` và citation; câu hỏi ngoài phạm vi có `path='abstain'`; fee `9,450,000` không gọi LLM; tests `test_service_rag.py` và regression không fail.

### TV2 — Trung Anh: xác minh phần C (không viết lại #60)

1. Khi KB từ #62 có trên integration, chạy `load_folder(Path('data/kb'))` và `make_index('bm25', chunks)`; xác nhận **3 file, 14 chunks** với data mẫu.
2. Thử **3 truy vấn tự chọn**, ghi nguyên câu hỏi, **top chunk ID**, **score**, nhận xét truy vấn bất ngờ nếu có. Dùng cùng dữ liệu và cấu hình dùng cho F; có thể ghi thành một tiểu mục trong `docs/lab6/path_comparison.md` do Tâm tổng hợp, không cần file báo cáo khác.
3. Review retrieval contract và bảo đảm score/ID của BM25 từ production đang được Tâm và Duy sử dụng.

**DoD:** 3 truy vấn và top ID/score **đo thực** được ghi nhận; 14 chunks đúng; `tests/test_rag_index.py` pass; không còn index copy dùng trong evaluator chính.

### TV3 — Đạt: xác minh A1 và fallback sau khi Quỳnh ghép

1. **Không code lại #50.** Review import của `rag/answerer.py`: sau khi `llm.py` chính thức có mặt, bỏ hoặc khóa fallback parser/LLM tạm trong production để tránh che lỗi A2 (chỉ sửa nếu cần, trên PR nhỏ hoặc phối hợp với Quỳnh).
2. Test no hits / score dưới ngưỡng **không gọi LLM lần nào**; score sát ngưỡng; source ID đúng; LLM lỗi/JSON lỗi/citation giả → retry tối đa 1 rồi retrieval `degraded=True`.
3. Xác nhận `llm=None` là retrieval path, `StubLLM` là LLM path, không nhầm hai loại.

**DoD:** `tests/test_rag_answerer.py` và test tương thích A2 chạy trên integration; spy xác nhận 0 call tại A1 và retry/fallback đúng.

### TV4 — Hùng: review/merge PR #64, kiểm tra API tối thiểu

1. **Dùng PR #64 đã mở**, không làm lại module.
2. Giữ `ChatResponse` có `path`, `escalate`, `confidence` mặc định, không mất `request_id`, `answer`, `intent`, `sources`, `degraded`.
3. Review test API hiện có (một số dùng fake service, như mô tả PR); sau khi Duy ghép, chạy thêm **một** smoke test `/v1/chat` bằng service có RAG production nếu cần để xác nhận schema xuất ra đúng.
4. Không thay DB, schema migration, endpoint cũ hoặc mở rộng API ngoài nhu cầu C/D/E/F/H1.

**DoD:** #64 merged; schema giữ tương thích; `tests/test_api.py`, `tests/test_db.py`, `tests/test_persistence_restart.py` pass trên integration mới.

### TV5 — Bội Anh: hoàn tất PR #62

1. `git fetch origin`; đối chiếu branch PR #62 với integration mới; xử lý merge conflict/checks nếu có (trước đây GitHub báo không merge được). Không force-push hoặc reset nhánh người khác.
2. Giữ nguyên **3 file Markdown mẫu** trong `data/kb/` và `src/assistant_core/guard.py`; không thay `data/handbook.json`, `data/offices.csv`.
3. Xác nhận regex guard chặn câu hỏi về điểm/thông tin người khác **trước retrieval/model**, nhưng không chặn câu hỏi bình thường về điều kiện GPA.
4. Review và merge #62 sau targeted tests. Báo cho Duy/Trung Anh/Tâm ngay khi KB runtime đã có.

**DoD:** PR #62 merged vào integration, `data/kb` load được 14 chunks; `tests/test_guard.py` pass; không có dữ liệu thật/secret.

### TV6 — Quỳnh: triển khai D/A2 trên production (**ưu tiên cao nhất còn thiếu**)

**Owner:** `src/assistant_core/llm.py`, `src/assistant_core/prompts/answer_v1.txt`; cấu hình RAG trong `src/assistant_core/config.py`/`.env.example` **chỉ ở mức cần thiết** để app chạy offline.

1. Lấy phần LLM/stub/prompt **đã cho sẵn** ở `sources/lab6` hoặc starter giảng viên; đưa vào root repo mà không ghi đè `responder.py` legacy.
2. Chốt interface với Đạt/Duy: `LLM.complete(prompt)->str`, `make_llm(...)`, `build_prompt(question,hits,version)`, `parse_draft(raw, allowed_ids)`; nguồn ID dạng `H26#5.3`.
3. **TODO A2:** nếu `not draft.abstain` và (`not draft.source_ids` hoặc `not set(draft.source_ids) <= allowed_ids`) → `raise ProviderError`; kiểm JSON/loại dữ liệu/confidence 0–1 bằng Pydantic.
4. Cấu hình `LLM_PROVIDER=stub` hoạt động **không key, không internet**; thêm `kb_dir`, `retrieval_kind`, `retrieval_min_score`, prompt version theo nhu cầu #52. Tránh bắt API key với stub. Không bắt buộc Ollama/OpenAI adapters để hoàn thành scope này.
5. Viết test cho JSON hợp lệ, rỗng citation, citation ngoài retrieved IDs, JSON sai, confidence ngoài [0,1] và một ca `abstain=True`; test trực tiếp module production.
6. Tạo **một PR module** vào `integration/lab06-v0.6` và giao Đạt/Duy review. Khi ghép, bảo đảm `answerer.py` không sử dụng parser dự phòng.

**DoD:** citation test theo PDF trang 12 pass; stub offline trả JSON hợp lệ; grounded LLM response trả source thật; nguồn giả gây retry/degraded fallback; không tạo chi phí API.

### TV7 — Tâm: hoàn thiện F/H1 bằng code tích hợp (sửa PR #56)

1. **Giữ** `eval/cases.jsonl` 20 case gốc, `eval/compare_paths.py`, `docs/lab6/path_comparison.md` và smoke tests hữu ích trong #56.
2. **Bỏ implementation dự phòng trùng lặp:** `FallbackBM25Index`, `FallbackRagAnswerer` và subclass `build_service_adapter` nếu có thể thay bằng `BM25Index`, `RagAnswerer` và `AssistantService` thực. Không tải KB ngầm từ snapshot/commit khác; dùng `data/kb` trong repo. Một `NoAnswer`/null RAG tối thiểu để cô lập **deterministic baseline** là chấp nhận được, nhưng không copy thuật toán retrieval/LLM.
3. Dùng ba cấu hình cùng router, KB, cùng 20 case: **deterministic** (không trả lời policy bằng RAG), **retrieval** (`RagAnswerer(llm=None)`), **LLM stub** (`RagAnswerer(llm=StubLLM())`). Đảm bảo scorer tính `expect_contains`, `expect_source`, `expect_abstain` đúng ý nghĩa.
4. Chạy lại `python eval/compare_paths.py` sau khi #62 + Quỳnh + #52 được merge; ghi **SHA, lệnh, môi trường và số đo thực**. Viết **đúng 3 câu**: path chọn cho handbook, lý do, một lỗi ưu tiên sửa.
5. **H1: thêm đúng 5 case** (3 nguồn, 2 abstain), ưu tiên **tận dụng** câu hỏi đã làm ở các PR exercise, nhưng nhập **một lần** vào root `eval/cases.jsonl`. Ví dụ từ PR #49 có thể dùng E31–E35 (3 handbook, 2 abstain); kiểm lại expected IDs, không copy cả code starter. Nếu ID bị trùng thì đánh số khác.
6. Chạy lại **25 case**, lưu bảng trước/sau và **một câu** phân tích lỗi của case mới nếu có; nếu cả 5 pass, ghi rõ không có case mới fail (có thể phân tích một known failure cũ).
7. Thay smoke tests dựa trên fallback classes bằng tests chạy module production; tránh bỏ qua test khi thiếu import vì mục tiêu là xác nhận tích hợp thật.

**DoD:** #56 chỉ đánh giá code production; baseline 20 và H1 25 case chạy được offline; bảng đúng format trang 15; 3 câu F, giải thích H1; không cần 35 case hoặc H2.

---

## 4. Thứ tự triển khai và merge tối ưu

**Lưu ý:** Các owner có thể code/test độc lập cùng lúc. Chỉ chờ dependency tại thời điểm **integration check**, không chặn review những việc độc lập.

| Mốc | Công việc | Owner chính | Điều kiện chuyển bước |
|---|---|---|---|
| **P0 — ngay** | Ngừng Luồng A; giữ PR exercise làm tham chiếu, chuẩn bị đóng; xác nhận HEAD của integration | Duy + cả nhóm | Không tạo thêm exercise PR; không xóa kết quả hữu ích |
| **P1 — song song** | Hoàn tất và merge **#62** (KB/guard); hoàn tất **PR Quỳnh** (LLM/A2); review **#64** (API) | Bội Anh, Quỳnh, Hùng | KB, A2, schema chạy test độc lập trên integration; xử lý conflict thực |
| **P2** | Cập nhật và merge **#52**; xác minh A1/A2 thật; 3 truy vấn C | Duy, Đạt, Trung Anh | `build_service()` chạy RAG production bằng KB + StubLLM; fee/privacy/abstain/fallback đạt |
| **P3** | Sửa **#56** dùng production; thêm 5 case H1, chạy 20→25 và báo cáo F | Tâm | Kết quả chạy có SHA và có thể tái lập; smoke tests production pass |
| **P4 — gate cuối** | Root regression, CLI và kiểm tra API cần thiết; merge integration vào `main` **nếu nhóm muốn một bản chung**; nộp đúng kênh LMS | Duy + Hùng + Tâm, các owner review | Không regression fail; đủ minh chứng C/D/E/F/H1 |

**Thứ tự merge gợi ý:** `#62` và PR Quỳnh theo tiến độ thực, `#64` có thể merge độc lập, sau đó `#52`, cuối cùng `#56`. `#50` và `#60` đã merge, tuyệt đối không mở PR copy khác để thay thế.

### Quy tắc xử lý PR bài cá nhân cũ

- `#49, #51, #55, #61, #63`: **không merge** vào integration/main; **đóng sau khi Tâm đã chọn và chuyển dữ liệu H1 cần thiết** và sau khi xác nhận LMS không đòi giữ PR cá nhân. Nếu đã nộp link và LMS cần link tồn tại, có thể để đóng (URL vẫn hoạt động) hoặc giữ mở theo yêu cầu lớp.
- `#59`: giữ trạng thái đã merge **chỉ** trong nhánh exercise. Không revert, không đưa cả nhánh exercise vào integration.
- Không xóa `sources/lab6` hay tài nguyên gốc của giảng viên; chúng chỉ dùng làm đối chiếu, không làm runtime code thứ hai.

---

## 5. Kiểm thử đủ dùng — một lần theo từng mốc

Không bắt chạy full suite sau mỗi dòng code. Dùng targeted tests khi sửa module; **chỉ chạy full regression sau khi ghép và ở gate cuối**. Các lệnh chạy từ root repo, trong môi trường đã cài dependency.

```powershell
# C / retrieval sau #62
python -m pytest -q tests/test_rag_index.py tests/test_guard.py

# D + E sau khi Quỳnh/Đạt ghép (thêm tên file test LLM thực tế)
python -m pytest -q tests/test_rag_answerer.py

# Service/API sau khi #52, #64 được ghép
python -m pytest -q tests/test_service_rag.py tests/test_api.py

# F + H1: đánh giá chạy từ repo root, 20 case trước khi thêm H1 và 25 case sau
python eval/compare_paths.py

# Gate cuối: chạy trên HEAD của integration sau khi tất cả module đã merge
python -m pytest -q
python -m assistant_core "I lost my student card"
python -m assistant_core "what is the capital of France"
python -m assistant_core "tuition for 18 credits and 2 retake"

git rev-parse HEAD
git status --short
```

**Nhóm các test bắt buộc về hành vi:**

- `S26#3` được trích khi hỏi mất thẻ sinh viên; `H26#5.3` đối với điều kiện khóa luận.
- No-hit/score thấp → `path='abstain'`, `escalate=True`, **0 lần** gọi LLM.
- LLM trả citation không thuộc retrieved IDs hoặc JSON sai → retry tối đa 1 rồi `path='retrieval'`, `degraded=True` và nguồn có thật.
- Privacy question từ chối trước search/LLM; câu hỏi chung về GPA được cho qua.
- `tuition for 18 credits and 2 retake` → **9,450,000 VND do code tính**, không dùng LLM.
- Không làm mất các trường API cũ, `request_id`, feedback/DB hoặc endpoint Lab 4–5.
- Case known failure **E13, E14, E15, E19** được báo trung thực; **không bắt sửa** trong phạm vi này.

---

## 6. Bộ hồ sơ bàn giao tối thiểu

1. **Code chung** trên `integration/lab06-v0.6` (hoặc `main` sau merge): KB 3 Markdown, production index, production LLM stub + A2, answerer A1, service guard/wiring, API response tương thích.
2. **Minh chứng phần C:** ba truy vấn BM25 tự chọn, top chunk ID, score và nhận xét.
3. **`docs/lab6/path_comparison.md`:** bảng 20 case F, ba câu nhận xét, bảng 25 case H1, một câu giải thích lỗi nếu có, SHA/lệnh chạy.
4. **`eval/cases.jsonl`:** 20 case gốc + 5 case H1 (3 source, 2 abstain); không gộp 35 case của 7 người.
5. **Test evidence:** các targeted test và một lượt full regression cuối, có commit SHA và trạng thái lỗi/pass. Kết quả PR trước đó chỉ dùng tham khảo.
6. **Link PR nộp** theo thông báo LMS; không tự gán mốc thời gian hoặc tag là yêu cầu riêng của C/D/E/F/H1.

### Checklist nghiệm thu cuối

- [ ] **C:** KB runtime đúng 3 file / 14 chunks; có 3 truy vấn tự chọn và ID/score đo thực.
- [ ] **D:** `StubLLM` offline, JSON validation và A2 citation test pass **trên module production**.
- [ ] **E:** A1 no-hit/threshold trước model; privacy, fee, fallback kiểm chứng đúng.
- [ ] **F:** evaluation **thực** trên 20 case, bảng đủ cột và 3 câu nhận xét.
- [ ] **H1:** đúng 5 case bổ sung (3 source, 2 abstain), bảng chạy lại trên 25 case, nhận xét lỗi.
- [ ] **Tích hợp:** không có RAG/index/parser giả lập được dùng thay code production khi chạy đánh giá; toàn bộ regression cuối pass; nộp link phù hợp.

**Định nghĩa hoàn thành:** *Không phải* tất cả PR cá nhân đã merge, không phải số test minh họa trong PDF, cũng không phải có tag; mà là **một implementation RAG thống nhất chạy được offline và có bằng chứng thực tế cho đủ C, D, E, F, H1**.
