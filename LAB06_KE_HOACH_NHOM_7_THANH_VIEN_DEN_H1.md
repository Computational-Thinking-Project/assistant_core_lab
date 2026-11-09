# KẾ HOẠCH LAB 06 — AI SERVICES & RAG (BẢN CHỈNH SỬA SAU REVIEW)

**Môn:** CSC10014 · Practical Track · Lab 06 · Tuần 6  
**Nhóm/repo:** [Computational-Thinking-Project/assistant_core_lab](https://github.com/Computational-Thinking-Project/assistant_core_lab)  
**Thành viên, theo thứ tự:** **1. Duy · 2. Trung Anh · 3. Đạt · 4. Hùng · 5. Bội Anh · 6. Quỳnh · 7. Tâm**  
**Ngày:** 09/11/2026 · **Trạng thái:** kế hoạch để triển khai, **chưa xác nhận các test Lab 6 chạy thành công**.  
**Cơ sở:** PDF `CSC10014_2026_Lab06_AI_Services_RAG_Tutorial.docx.pdf` (24 trang); tài nguyên mẫu giảng viên tại folder `lab06_source_lecturer_given/` (thay thế cho link GitHub `public_materials/lab06`); mã nguồn `main` repo nhóm được đối chiếu tại `27fbea699d16968ceb169b795bcf979e69bc1b61`; bản review kế hoạch được cung cấp ngày 09/11/2026. Trước khi code, `git fetch` và xác nhận HEAD mới; nếu khác, kiểm diff trước khi áp dụng.

> **Mục tiêu quản lý:** hoàn thành phạm vi đã chọn (C, D, E, F và H1), bổ sung RAG an toàn vào ứng dụng của nhóm mà **không thay thế code Lab 3–5**, hạn chế hai người trở thành nút thắt, không dùng kết quả test trong PDF làm bằng chứng chạy thực tế.

---

## I. YÊU CẦU, PHẠM VI VÀ MỐC NỘP

### 1. Chức năng bắt buộc của sản phẩm cuối

- **Deterministic:** chào hỏi, tra phòng/văn phòng và **tính học phí bằng code**, không giao phép tính tiền cho LLM.
- **Retrieval:** tìm các đoạn văn (*chunks*) có nguồn cụ thể trong `data/kb/*.md`, dùng BM25 mặc định.
- **LLM (stub):** tạo lời giải từ các đoạn đã truy xuất; yêu cầu JSON cấu trúc cố định và xác thực nguồn trích dẫn.
- **A1/abstain:** không có đoạn phù hợp hoặc `best_score < retrieval_min_score` thì từ chối và hướng đến người phụ trách **trước khi gọi LLM**.
- **A2/grounding:** nếu model không từ chối, `source_ids` phải không rỗng và mọi ID phải thuộc tập kết quả vừa truy xuất.
- **Degraded fallback:** provider lỗi hoặc output không hợp lệ, retry tối đa một lần theo starter; sau đó dùng đoạn tài liệu đã truy xuất, có nguồn và `degraded=True`.
- **Privacy guard:** chặn câu hỏi về dữ liệu cá nhân người khác trước truy xuất/model; vẫn cho phép câu hỏi thông thường về điều kiện GPA.

**Ngoài phạm vi kế hoạch:** Ollama/OpenAI trả phí; vector DB/embedding; frontend; thay đổi schema SQLite; thiết kế lại API; bắt buộc sửa hết E13–E15/E19. Bonus chỉ thực hiện sau khi đủ phần chính.

### 2. Checklist phạm vi triển khai (PDF trang 4, 18–20)

| Công việc | Áp dụng | Bằng chứng | Điểm |
|---|---|---|---:|
| S1–S3 mini search | Mỗi người | `practice/mini_search.py`; 4 test pass | 2 |
| A2 grounding citation | Mỗi người | `llm.py`, test citation | 2 |
| A1 abstain trước model | Mỗi người | `answerer.py`, test abstain | 2 |
| So sánh ba paths | Mỗi người | `docs/lab6/path_comparison.md`: bảng và 3 câu | 1 |
| H1 thêm 5 test | Mỗi người | 3 nguồn + 2 abstain; bảng đánh giá lại + nhận xét | 2 |
| Bonus Ollama **hoặc** H3 | Không bắt buộc | Kết quả chạy thực, diff/test | +1 |
| Team integration | Cả nhóm | Merge **một** bản chức năng nhóm; **Member 1** tạo tag `v0.6-ai` | — |

**Mốc theo PDF:** Cuối buổi Lab 6 nộp PR link trên LMS (có thể là draft) với S1–S3, A1–A2, bảng + 3 câu. **23:59 ngày trước Lab 7** hoàn thành H1 và nhóm merge/tag, Tech Lead nộp tag link. **Ngày Lab 7 cụ thể không nằm trong PDF**, phải kiểm lịch lớp/LMS; không tự điền ngày tháng. Mốc nội bộ khuyến nghị: PR module sẵn review trước hạn LMS ít nhất một ngày nếu lịch cho phép.

### 3. Nguồn mẫu và known failures phải hiểu đúng

- KB mẫu **không phải quy chế thật của trường**; có 3 Markdown, tổng **14 chunks**, ID gồm `H26#5.3`, `F26#2`, `S26#3`.
- `eval/cases.jsonl` starter có E01–E20, gồm 5 case đòi abstain. E13 ("tuition due"), E14 ("credits"/"credit"), E15 ("library" bị router xử lý như văn phòng), E19 (nguồn liên quan nhưng không đủ trả lời) là **lỗi minh họa cố ý** trong PDF.
- Số `42 passed`, `7/20`, `16/20` trong PDF là **ví dụ của giảng viên**, không được ghi như kết quả nhóm nếu chưa chạy.

---

## II. ĐỐI CHIẾU REPO VÀ HỢP ĐỒNG GIAO DIỆN BẤT BIẾN (P0)

### 1. Hiện trạng quan sát được trên repo nhóm

| File/phần | Code nhóm ở baseline | Cách bổ sung, **không** ghi đè starter |
|---|---|---|
| `src/assistant_core/service.py` | `AssistantService.__init__(settings=None, router=None, office_directory=None, handbook=None, responder=None, fallback_responder=None, logger=None)`, `handle`, `_dispatch`, `build_service` | Thêm `rag` ở **cuối danh sách tham số, tùy chọn**, hoặc keyword-only để giữ positional/fixture cũ; RAG bật trong `build_service` khi `kb_dir` tồn tại. Không thay bằng constructor của starter. |
| `src/assistant_core/models.py` | `Response(answer, intent, sources, degraded)` | Thêm 3 field có default, không xóa/thay tên field trước. |
| `src/assistant_core/router.py` | Greeting → fee nếu chứa `fee`/`tuition` → office nếu khớp tên → RULE | Giữ deterministic; E13 có thể bị route sai. Bổ sung test phân biệt câu tính tiền với câu hỏi deadline, **không bắt buộc fix E13**. |
| `src/assistant_core/config.py` | `llm_provider` và settings API/DB, yêu cầu key khi provider khác `stub` | Chỉ `openai` bắt buộc key; `ollama` không, `stub` mặc định. Thêm settings KB/retrieval/provider; giữ Lab 4–5. |
| `src/assistant_core/responder.py` | `Responder.explain(question, rule)` | **Giữ interface cũ**; LLM mới dùng `LLM.complete(prompt)`. Không đồng nhất hai adapter. |
| `src/assistant_core/knowledge.py` | `Handbook` từ JSON, `OfficeDirectory` từ CSV | Giữ nguyên; thêm `data/kb/*.md`, `rag/chunker.py`, `rag/index.py` độc lập. |
| `src/assistant_api/main.py` | `/v1/offices`, `/v1/chat`, feedback, stats, weather; `record_interaction` lưu metadata | Giữ endpoint, bảo mật, persistence; cập nhật response bằng schema additive, không chép starter `main.py`. |
| `src/assistant_api/schemas.py` | `ChatResponse` chưa có `path/escalate/confidence` | Thêm có default; giữ `request_id` và các field cũ. |
| `tests/` | Có test service/router/API, DB và persistence restart | Phải tiếp tục pass; chỉ thêm test RAG liên quan, không sửa expected để làm đẹp. |

### 2. Interface contract: chốt **trước coding**, thay đổi phải được owner liên quan đồng ý

| Contract chuẩn | Owner | Quy tắc |
|---|---|---|
| `Chunk(id, doc_id, title, text, version, owner)`; `load_folder(Path) -> list[Chunk]` | Trung Anh | ID `doc_id#heading`, dùng sample KB ổn định; không hardcode `14` với KB khác. |
| `Hit(chunk: Chunk, score: float)`; `Index.search(query: str, k: int=3) -> list[Hit]`; `make_index(kind, chunks)` | Trung Anh | Trả top-k đã xếp điểm giảm dần; `bm25` default. |
| `LLM.complete(prompt: str) -> str`; `make_llm(provider, model, base_url, api_key, timeout_s)` | Quỳnh | Stub chạy offline; failure qua `ProviderError`; adapter cũ `Responder.explain` vẫn giữ. |
| `parse_draft(raw: str, allowed_ids: set[str]) -> AnswerDraft` | Quỳnh | JSON/Pydantic + A2; output không hợp lệ raise `ProviderError`. |
| `RagAnswerer(index, llm, min_score=2.0, k=3, prompt_version='answer_v1', retries=1, tool_runner=None).answer(question:str)->Response` | Đạt | A1 trước LLM; `llm=None` là retrieval; lỗi model → fallback retrieval. Test bằng SpyLLM/Index fake. |
| `Response(answer, intent, sources=[], degraded=False, escalate=False, path='deterministic', confidence=None)` | Đạt | `path` thuộc `deterministic|retrieval|llm|tool|abstain`; bảo toàn tương thích. |
| `is_private_request(text: str)->bool`, `PRIVATE_REPLY` | Bội Anh | Duy gọi guard **trước khi tìm và gửi prompt**, không lưu nội dung private. |
| `AssistantService(..., rag: RagAnswerer|None=None)`; `build_service(settings=None)->AssistantService` | Duy | Không đổi thứ tự tham số cũ, `AssistantService()` legacy hoạt động; KB có thì RAG được inject. |
| `ChatResponse` extends schema với `path`, `escalate`, `confidence` | Hùng | HTTP không mất `request_id`, `/v1/offices`, stats, feedback, weather. |
| `eval/compare_paths.py` chạy ba paths bằng cùng bộ E01–E20 | Tâm | Khả năng xây dựng 3 service instance rõ ràng; `NoAnswer`/`llm=None` để cô lập baseline. |

**Giao ước ngoại lệ:** Duy không sửa thay `llm.py`/`index.py`/`answerer.py`. Đạt và Quỳnh trao đổi tên/số tham số ngay P0; nếu muốn đổi contract sau đó, comment trên PR với lý do và báo owner downstream, tránh sửa ngầm. Mọi module test bằng fake dependency trước khi ghép; **không cần đợi** code thật của nhau để bắt đầu.

### 3. Quy tắc đúng/sai phải được test

1. No-hit hoặc score `< 2.0` (BM25 mặc định) ⇒ `abstain`, `escalate=True`, `confidence=0.0`, LLM gọi **0 lần**.
2. Có nguồn và model OK ⇒ `path='llm'`, mọi citation thuộc hit IDs.
3. Model lỗi/JSON/citation sai sau retry ⇒ `path='retrieval'`, `degraded=True`, trích source đã truy xuất.
4. `tuition for 18 credits and 2 retake` ⇒ **9,450,000 VND** bằng code, không qua model; `where is the library` vẫn hỏi địa điểm.
5. `what grade did my friend get` ⇒ private guard từ chối; không gọi retrieval/model.
6. `/v1/chat` vẫn lưu metadata của interaction/feedback như Lab 5; không lưu raw câu hỏi hay student PII.
7. E13 và E15 **được đánh dấu known failures nếu chưa sửa**: không ngộ nhận route “fee”/“office” chính xác cho mọi câu có các từ này.

---

## III. HAI LUỒNG GIT ĐỘC LẬP — KHÔNG GHÉP 7 BẢN A1/A2

### Luồng A — Bài cá nhân (cả 7, theo PDF trang 18)

**Mục tiêu:** 7 PR độc lập **chứng minh mỗi người** đã làm S1–S3, A1–A2, comparison/H1. Các PR này **không** được đưa vào queue merge của sản phẩm nhóm; tránh 7 bản sửa cùng một TODO.

**Cách tổ chức khuyến nghị trong cùng repo nhóm:** một nhánh `exercise/lab06-starter-base` chứa snapshot **nguyên vẹn** từ `lab06_source_lecturer_given/practice/` và `lab06_source_lecturer_given/starter/` của giảng viên (đặt dưới `lab06_source_lecturer_given/` hoặc `lab06/` để không đè `src/`, `tests/`, `data/` hiện tại). Duy hoặc thành viên có quyền push đầu tiên tạo một lần từ `main`. **Không merge nhánh exercise vào `main`/integration.** Mỗi người từ base này tạo `exercise/lab06-<ten>`, hoàn thành TODO rồi mở PR **base `exercise/lab06-starter-base`**, PR mô tả các test ở `lab06_source_lecturer_given/practice` và `lab06_source_lecturer_given/starter` chạy bằng cwd tương ứng. Có thể bắt đầu coding từ bản sao starter cục bộ ngay trong workspace `lab06_source_lecturer_given/` **trước khi nhánh base được push**, nên không ai phải chờ.

**Bắt buộc mỗi thành viên trong PR A:**

1. `lab06_source_lecturer_given/practice/mini_search.py`: S1 chỉ mục `dict[word] -> set[doc]`, S2 cộng điểm, S3 rank `(-score, doc_id)`; 4 test pass.
2. `lab06_source_lecturer_given/starter/src/assistant_core/rag/answerer.py`: TODO A1 no-hit/low-score → abstain **trước LLM**.
3. `lab06_source_lecturer_given/starter/src/assistant_core/llm.py`: TODO A2 non-abstain yêu cầu `source_ids` không rỗng, tập con `allowed_ids`.
4. `lab06_source_lecturer_given/starter/docs/lab6/path_comparison.md`: bảng từ `python eval/compare_paths.py` trên **starter cá nhân** và **3 câu**: chọn path cho handbook, lý do, lỗi cần ưu tiên.
5. H1: từng người thêm 5 câu riêng vào `lab06_source_lecturer_given/starter/eval/cases.jsonl` (3 câu có `expect_source`, 2 câu `expect_abstain: true`), chạy lại bảng và ghi nhận 1 trường hợp fail nếu có.
6. Kết quả chạy có command, số passed/failed, ngày và commit SHA; **không sao chép** 42 passed/16/20 từ PDF nếu chưa đo.

| Thành viên | ID 5 câu H1 trên **nhánh riêng** | Điều kiện |
|---|---|---|
| Duy | E21–E25 | 3 `expect_source`, 2 `expect_abstain` |
| Trung Anh | E26–E30 | như trên |
| Đạt | E31–E35 | như trên |
| Hùng | E36–E40 | như trên |
| Bội Anh | E41–E45 | như trên |
| Quỳnh | E46–E50 | như trên |
| Tâm | E51–E55 | như trên |

Dải ID để dễ quản lý; **PDF không bắt buộc đánh số E21–E55**. Vì PR có base riêng, các case **không tạo conflict** giữa người làm. H1 trong bài cá nhân phải dùng dữ liệu/expected đúng nguồn của từng câu. Một PR cá nhân có thể để draft khi nộp cuối buổi như PDF cho phép; nếu LMS yêu cầu PR ở repo khác hoặc đã merge thì tuân theo LMS, thông báo trước khi đổi workflow.

**Lệnh điển hình cho cá nhân (sau khi nhánh base có sẵn):**

```powershell
git fetch origin
git switch -c exercise/lab06-duy origin/exercise/lab06-starter-base
cd lab06_source_lecturer_given/practice
python -m pytest -q test_mini_search.py
cd ../starter
python -m pip install -e .
python -m pytest -q tests/test_rag.py
python eval/compare_paths.py
# Chỉ sau khi đọc lại git diff và kiểm test:
git status
git add lab06_source_lecturer_given/practice/mini_search.py lab06_source_lecturer_given/starter/src/assistant_core/rag/answerer.py lab06_source_lecturer_given/starter/src/assistant_core/llm.py lab06_source_lecturer_given/starter/eval/cases.jsonl lab06_source_lecturer_given/starter/docs/lab6/
git commit -m "feat(lab06-exercise): complete S1-S3 A1-A2 and evaluation"
git push -u origin exercise/lab06-duy
# Mở PR trên GitHub: HEAD exercise/lab06-duy -> BASE exercise/lab06-starter-base
```

> Ví dụ `duy`; mỗi người thay tên nhánh. **Không chạy `git add` trước khi tạo các file docs**. Không commit `.env`, `.venv`, `.db`, key, dữ liệu thật. Khi clone riêng teacher starter để làm trước, copy kết quả sang nhánh riêng sau; không cố merge repo teacher vào repo nhóm.

### Luồng B — Code chính của nhóm (module PR, tích hợp một bản)

- Branch đích: `integration/lab06-v0.6` tách trực tiếp từ `main` baseline **ngay P0, không chờ module**. Nếu Duy vắng, Hùng có thể tạo branch rỗng theo cùng base, thông báo SHA cho nhóm.
- Mỗi người mở một branch `feat/lab06-<ten>-<module>` từ **cùng base integration** (hoặc `main` cùng SHA) và PR **vào `integration/lab06-v0.6`**; diff **chỉ module được giao và test trực tiếp**. A1 owner Đạt, A2 owner Quỳnh; người khác không copy bản TODO cá nhân vào PR B.
- Duy có PR service glue riêng; không “cherry-pick toàn bộ starter” hoặc ghi đè file repo.
- Các PR chỉ được merge theo dependency tối thiểu; reviewer không yêu cầu người khác đã xong hết mới review. Targeted tests trên fake dependencies trước; E2E test ở gate integration.
- Sau merge các module, chạy regression và PR `integration/lab06-v0.6` → `main`; chỉ Member 1/Tech Lead tạo **tag sau merge** trên đúng commit release.

**Ví dụ lệnh branch B:**

```powershell
git fetch origin
git switch -c feat/lab06-trunganh-retrieval origin/integration/lab06-v0.6
# Sửa đúng ownership, chạy targeted tests, kiểm git diff
git status
git diff --check
git add src/assistant_core/rag/ tests/test_rag_index.py
git commit -m "feat(lab06): add document retrieval"
git push -u origin feat/lab06-trunganh-retrieval
# PR: HEAD feat/lab06-trunganh-retrieval -> BASE integration/lab06-v0.6
```

**Không** force-push nhánh người khác, rewrite history của PR sau review nếu không cần; không dùng `git reset --hard` như cách xử lý mặc định. Nếu một owner cần sửa file khác ownership, yêu cầu chủ file duyệt trước, hoặc tách PR phối hợp. Review dựa vào code và test, không chỉ tin mô tả PR.

---

## IV. PHÂN CÔNG CHI TIẾT 7 THÀNH VIÊN (LUỒNG B)

> **Tất cả 7 người còn phải làm Luồng A**; mục dưới đây chỉ mô tả trách nhiệm sản phẩm **chung** để không lặp S1–S3/A1–A2/H1 bảy lần. File test được gợi ý; có thể đặt vào test hiện hữu nếu không trùng lặp và không làm giảm coverage.

### TV1 — DUY: Service glue, CLI, integration và release

**Owner:** `src/assistant_core/service.py`, tùy nhu cầu `src/assistant_core/__main__.py`, `src/assistant_core/__init__.py`, `docs/lab6/integration_notes.md`. **Không owner:** `rag/index.py`, `rag/answerer.py`, `llm.py`, API schema.

**Thực hiện:**

1. **P0:** `git fetch origin`, kiểm SHA `main`, `git status`, chạy baseline `pytest -q`; ghi số pass/fail trong `docs/lab6/integration_notes.md`. Tạo nhánh `integration/lab06-v0.6` **rỗng** từ `main` để mọi người bắt đầu. Gửi bảng contract mục II, không viết lại code module người khác.
2. Đọc `AssistantService.__init__`, `handle`, `_dispatch`, `_handle_rule`, `build_service`; đọc fixtures `tests/conftest.py` và `assistant_api/main.py`. **Giữ constructor cũ, thêm `rag=None` ở cuối** (hoặc keyword-only) để lời gọi positional/`AssistantService()` vẫn hợp lệ. Không áp dụng nguyên constructor starter.
3. Khi chưa có module thật, viết glue dựa trên contract/fake: nhánh `RULE` kiểm `is_private_request` trước; nếu có `self.rag` thì `self.rag.answer(text)`; không có thì trả về legacy `_handle_rule`. Giữ `FEE` và `OFFICE` deterministic; không sửa `tools.py` hoặc `knowledge.py`.
4. Trong `build_service(settings=None)`, nếu `settings.kb_dir` tồn tại thì `load_folder()` một lần, `make_index(settings.retrieval_kind, chunks)`, `make_llm(...)` hoặc `None` cho retrieval-only baseline; inject `RagAnswerer`; nếu KB thiếu thì giữ legacy, **không tự tạo KB giả ngầm**. Chỉ đọc interface; không làm thay Đạt/Trung Anh/Quỳnh.
5. Với settings truyền từ fixture cũ không có `kb_dir`, dùng `getattr(settings, 'kb_dir', ...)` **nếu cần hỗ trợ cấu hình cũ**, nhưng không vô tình bật RAG trong các test legacy; bảo toàn hành vi cũ `AssistantService()`.
6. CLI: giữ `--test`, one-shot query và REPL; demo 3 paths và source nếu hữu ích, không làm hỏng stdout/CLI cũ. Chỉ điều chỉnh `__main__.py` khi có test tái hiện.
7. Tích hợp PR theo thứ tự dependency mục V, giao lại đúng owner khi import fail. Ghi nhận SHA và xung đột thật; không yêu cầu Tâm soạn báo cáo dài mới cho merge. Sau gate review/tag, nộp LMS.

**DoD:** `AssistantService()` + tests legacy pass; `build_service` dựng RAG từ KB mà không phá fee/office; demo fee 9,450,000, retrieval có nguồn, abstain; không phải tự sửa hộ module người khác; PR integration→main merged và tag đúng SHA. **Reviewer:** Đạt (service/router), Hùng (API), Tâm chỉ chặn nếu có test blocker. **Độc lập sớm:** baseline, branch, contract, fake-injection tests.

### TV2 — TRUNG ANH: Chunking/index BM25

**Owner:** `src/assistant_core/rag/chunker.py`, `rag/index.py`, `rag/__init__.py`; targeted test retrieval, ví dụ `tests/test_rag_index.py`.

**Thực hiện:**

1. Đọc starter `chunker.py` và `index.py` từ `lab06_source_lecturer_given/starter/src/assistant_core/rag/`; dùng **ngay 3 file KB mẫu** của giảng viên ở local fixture (`lab06_source_lecturer_given/starter/data/kb/`), không đợi Bội Anh nhập repo.
2. Port `Chunk`, `chunk_markdown`, `load_folder`, `Hit`, `Index`, `BM25Index`, `make_index` vào package mới. Giữ `doc_id#section` như `H26#5.3`, metadata version/owner, thứ tự load ổn định.
3. Default `bm25`; nếu copy cả TF-IDF/hybrid, **không dùng min_score=2.0 của BM25 áp cho điểm TF-IDF/hybrid** khi đánh giá. Không mở rộng sang embedding/vector DB.
4. Test `tmp_path`/fixture cho metadata, top hit thesis, score giảm dần, query không liên quan, search top-k; kiểm mẫu có 14 chunks và H26#5.3 là top hit cho câu thesis. Không coi điểm số số học cố định là tiêu chuẩn cho mọi bản indexing.
5. Chỉ push diff `rag/chunker.py`, `rag/index.py`, test; cung cấp ví dụ `make_index('bm25', load_folder(Path('data/kb')))` cho Đạt/Duy; không sửa service/router.

**DoD:** targeted index tests pass với KB fixture offline; `Index.search()` trả đúng `Hit`/`score`; không ảnh hưởng `knowledge.py` cũ. **Reviewer:** Bội Anh (metadata), Tâm (test). **Không phụ thuộc:** API, LLM, service.

### TV3 — ĐẠT: Response contract, router và RagAnswerer (A1 official)

**Owner:** `src/assistant_core/models.py`, `src/assistant_core/router.py`, `src/assistant_core/rag/answerer.py`, targeted answerer tests.

**Thực hiện:**

1. Bổ sung `Response.escalate=False`, `path='deterministic'`, `confidence=None`; giữ `Message`, `Intent`, `Source` và constructor cũ. Test gọi `Response(answer=..., intent=...)` không phải truyền field mới.
2. Nhập `RagAnswerer` từ `lab06_source_lecturer_given/starter`, sửa **TODO A1** chính thức: `if not hits or hits[0].score < self.min_score` trả `ESCALATE_MSG`, `Intent.UNKNOWN`, `path='abstain'`, `escalate=True`, `confidence=0.0`; **không gọi LLM**.
3. Có hit: `llm=None` thì trả retrieval+source; có model thì `build_prompt`, `parse_draft`, JSON hợp lệ → llm; draft `abstain=True` → abstain; provider failure/bad draft thử lại 1 lần rồi quote top chunk + source + `degraded=True`.
4. Tạo `FakeIndex`, `SpyLLM` và `FakeToolRunner` trong test để chứng minh call count 0 khi thiếu nguồn, max attempts khi model fail, source IDs đúng, `path`/`degraded` rõ ràng. Không đợi Quỳnh hoàn thành adapter mới viết test; khi code ghép, test lại cùng contract thật.
5. Đọc `router.py`: fee keyword `fee`/`tuition` và office keyword có thể bắt nhầm **E13/E15**. Viết 2 bài test đặc trưng cho `tuition for 18 credits ...` (fee), `when is tuition due` (known failure hoặc routing improvement có review). Nếu sửa router, chỉ sửa tối thiểu, **không biến câu tính tiền thành RAG** và không ghi nhận E13 đã pass nếu chưa đo.
6. Không sửa `llm.py` (Quỳnh), `service.py` (Duy); gửi cho họ contract/fake test ngay.

**DoD:** tests A1 no-hit/low-score, retry/fallback, schema mặc định pass; deterministic fees không đổi; failure E13/E15 được ghi nhận trung thực. **Reviewer:** Quỳnh (parse compatibility), Duy (service). **Độc lập:** Fake Index/LLM.

### TV4 — HÙNG: REST API contract + regression Lab 4–5

**Owner:** `src/assistant_api/schemas.py`, chỉ khi cần `src/assistant_api/main.py`, `docs/api_contract.md`, targeted API tests.

**Thực hiện:**

1. Đối chiếu `main.py`: hiện có `/health`, `/v1/offices`, `/v1/chat`, `/v1/feedback` POST/GET, `/v1/stats/intents`, `/v1/weather`, rate limit, API key, DB. **Không copy starter `main.py`** vì starter ít endpoint hơn.
2. Bổ sung `ChatResponse.path='deterministic'`, `escalate=False`, `confidence=None`; giữ `answer`, `intent`, `sources`, `degraded`, `request_id`. `ChatResponse(**resp.model_dump(), request_id=request_id)` phải hoạt động với cả Response cũ/mới.
3. Test schema bằng `Response` mẫu/fake service trước khi Duy ghép RAG; test chat fee, abstain, grounded source, provider failure; dùng TestClient/MockTransport, không gọi LLM hay weather thật.
4. Chạy `tests/test_api.py`, `test_db.py`, `test_persistence_restart.py`: feedback lưu/đọc sau restart; admin key 401 khi thiếu; stats, offices, 422/429, weather 503 không đổi. Kiểm DB không lưu raw message; no migrations mới.
5. Chỉ cập nhật `main.py` nếu mapping thật sự lỗi. Ghi schema mới trong `docs/api_contract.md`, không đổi API contract cũ ngoài trường bổ sung.

**DoD:** targeted API/DB tests pass trên nhánh integration sau ghép; không endpoint cũ mất; Response có path mới và giữ `request_id`; persistence không đổi. **Reviewer:** Tâm (API checks), Duy (contract). **Độc lập sớm:** test với fake Response/service.

### TV5 — BỘI ANH: KB Markdown, nguồn và privacy guard

**Owner:** `data/kb/handbook_2026.md`, `fees_2026.md`, `services_2026.md`, `src/assistant_core/guard.py`, test guard; tài liệu nguồn tùy nhu cầu.

**Thực hiện:**

1. Nhập chính xác 3 Markdown từ giảng viên tại `lab06_source_lecturer_given/starter/data/kb/`, giữ frontmatter `doc_id/title/version/owner`, các mục, con số, điều kiện. Đây là **dữ liệu mẫu**, không công bố như chính sách thật.
2. Đối chiếu IDs `H26`, `F26`, `S26` + chunk IDs. Không thay `data/handbook.json`, `data/offices.csv`; không ép ID cũ `H26-5.3` đổi sang `H26#5.3` trong legacy.
3. Port guard `is_private_request` và `PRIVATE_REPLY`; test `what grade did my friend get`, `show the GPA of another student`, `phone of 22127001`; test không chặn `what is my GPA requirement for the thesis`.
4. Gửi sớm KB và guard interface cho Trung Anh/Đạt/Duy; chưa cần sửa `service.py`. Trong PR giải thích giới hạn regex (không tuyên bố chặn mọi dữ liệu cá nhân), đánh dấu dữ liệu là sample.
5. Kiểm diff không chứa tên, mã SV, log thật; không thêm secret/PII.

**DoD:** KB tải được bằng `load_folder()`, bộ mẫu là 14 chunks, guard unit tests pass, nguồn cũ nguyên vẹn. **Reviewer:** Trung Anh (chunk ID), Quỳnh (prompt privacy). **Độc lập:** từ starter gốc.

### TV6 — QUỲNH: LLM adapter, structured JSON, grounding (A2 official), Settings

**Owner:** `src/assistant_core/llm.py`, `src/assistant_core/prompts/answer_v1.txt`, `src/assistant_core/config.py`, `.env.example`, targeted LLM/config tests.

**Thực hiện:**

1. Giữ `responder.py`/`Responder.explain()` cũ; port `LLM.complete()`, `AnswerDraft`, `StubLLM`, `build_prompt`, `parse_draft` và prompt theo starter tại `lab06_source_lecturer_given/starter/`; không cần API key, internet hoặc Ollama để chạy bài chính.
2. **A2:** khi `not draft.abstain` và (`not draft.source_ids` **hoặc** `not set(draft.source_ids) <= allowed_ids`) → `raise ProviderError`. Cần JSON parse/Pydantic validation, kiểm `confidence in [0,1]` và field types.
3. Test bằng fake `Hit`/`Chunk` và raw JSON: hợp lệ, extra ID, missing ID, empty list, invalid JSON, `confidence=7`, `abstain=True`, stub garbage/fail. **Lưu ý:** citation ID hợp lệ không chứng minh answer thật sự được nguồn hỗ trợ (E19).
4. Thêm Settings: `llm_model`, `llm_base_url`, `kb_dir`, `retrieval_kind`, `retrieval_min_score`, `prompt_version`; giữ `database_url`, `session_salt`, `api_admin_key`, weather, fee settings. Default `LLM_PROVIDER=stub`, BM25, min score `2.0`.
5. Sửa `load_settings` để **chỉ provider `openai`** yêu cầu API key; `ollama` và `stub` không cần. Viết test riêng cho 3 provider, nhất là cấu hình `ollama` không key và `openai` không key bị từ chối; không làm vỡ khởi tạo FastAPI ở cấu hình stub.
6. Ollama/OpenAI adapters theo starter nếu mang vào repo thì mock network trong test; **không** chạy model thật như điều kiện merge. Đưa `make_llm`/`parse_draft` contract cho Đạt/Duy trước khi code hoàn thành.

**DoD:** JSON/citation sai bị từ chối; stub offline; tests LLM **và config** pass; settings Lab 4–5 giữ nguyên; không rò key. **Reviewer:** Đạt (A2/answerer), Duy (build_service/config). **Độc lập:** fake Hit.

### TV7 — TÂM: Evaluation, targeted E2E và release QA (giảm gánh tổng hợp)

**Owner:** `eval/cases.jsonl` (20 case gốc + một số H1 có chọn lọc), `eval/compare_paths.py`, một số targeted integration tests, `docs/lab6/path_comparison.md`/file QA **ngắn**.

**Thực hiện:**

1. Port nguyên **20 case E01–E20** và script `compare_paths.py` từ starter (`lab06_source_lecturer_given/starter/eval/`). Không sửa expected/ID để khớp bug. Viết/test script bằng **starter riêng ngay từ đầu**, không đợi service nhóm hoàn chỉnh.
2. Adapt evaluator theo constructor của service nhóm (không thay `AssistantService` thành phiên bản starter). Tạo 3 cấu hình rõ: `deterministic` (RAG dùng index luôn trả `[]`, để câu RULE abstain nhưng fee/office giữ deterministic), `retrieval` (`index` thật, `llm=None`), `llm` (`index` thật, `StubLLM`). Cùng danh sách case và format: correct, abstain ok, p50, max, fails.
3. Viết một số **integration smoke tests** cho fee 9,450,000; office B.201; `S26#3`; thủ đô Pháp abstain; privacy guard; LLM garbage → retrieval fallback; không nhân bản test unit của các owner.
4. Sau ghép, chạy `python eval/compare_paths.py` và lưu bảng **số đo thật**, SHA, OS/Python trong `docs/lab6/path_comparison.md`; thêm 3 câu theo PDF và một giải thích failure. Phân loại E13–E15/E19 như known issues nếu vẫn fail.
5. **Không bắt buộc** tổng hợp 35 câu H1 thành E01–E55. Mỗi cá nhân tự nộp 5 câu trên PR A. Với sản phẩm nhóm, chỉ bổ sung **tối thiểu 5 case chất lượng đã review nếu cần** để làm ví dụ; kiểm từng `expect_source` tồn tại. Có thể giữ chỉ 20 gốc nếu lịch sát hạn và các bài H1 cá nhân đã đủ; PDF không đòi 55 case chung.
6. Khi Duy ghép core, chạy integration tests một lần; Hùng tự phụ trách API/persistence. Cuối cùng chạy **full regression một lần trên release candidate SHA**; chạy lại full suite **chỉ nếu code sau đó thay đổi**. Báo cáo ngắn gồm SHA, số passed/failed/skipped, blocker, known failure, link evidence; không tạo thêm bộ tài liệu dài nếu không cần.
7. Báo blocker có reproduction/affected test/owner, không tự gánh sửa code. **Không chặn PR module đã pass targeted** chỉ vì QA tổng hợp chưa hoàn tất; quyền chặn áp dụng cho release khi lỗi an toàn/dữ liệu/contract/regression thật.

**DoD:** evaluator chạy xong 20 case, có đủ 3 paths và số liệu thật; smoke tests + full regression release pass, hoặc có danh sách blocker minh bạch trước khi tag; không có gánh tổng hợp 35 case. **Reviewer:** Hùng (API/DB), Duy (release). **Độc lập sớm:** 20-case evaluator chạy trên starter.

---

## V. THỰC HIỆN THEO 4 GIAI ĐOẠN (TRÁNH NÚT THẮT)

| Pha | Việc làm song song | Điều kiện chuyển pha | Ai duyệt |
|---|---|---|---|
| **P0 — Baseline + contract** | Tất cả tự bắt đầu Luồng A từ starter; Duy/Hùng lập branch integration; chốt bảng interface ở II; `pytest` baseline, SHA | Branch tồn tại, contract đủ signature; không bắt ai đợi stub/service xong | Duy + Đạt; Hùng dự phòng branch |
| **P1 — Coding song song** | Trung Anh index; Bội Anh KB/guard; Quỳnh LLM/config; Đạt Response/answerer/router; Hùng schema API; Tâm eval trên starter; Duy glue dùng fake | Mỗi owner có PR B và targeted test/fixture liên quan; PR A mỗi người đang triển khai | Reviewer theo từng module |
| **P2 — Integration** | Merge các PR module độc lập theo dependency, sau đó Duy nối service; Hùng kiểm HTTP/DB, Tâm chạy 20 case + smoke | Demonstrate fee, retrieval, llm stub, abstain, fallback, privacy; test trọng điểm pass; known failures ghi lại | Duy + Hùng/Tâm |
| **P3 — Release/nộp** | Reviewer duyệt diff cuối, Tâm full regression release SHA; sửa blocker theo owner, merge main, Duy tag; từng cá nhân nộp PR A H1 | Full suite/eval chạy trên **đúng commit** được tag, không secret/PII, LMS đủ link | Duy + người review độc lập |

**Thứ tự merge B khuyến nghị:** ① Bội Anh KB/guard + Trung Anh index (có thể nhập bất kỳ thứ tự vì không sửa chung file) → ② Đạt models/answerer + Quỳnh llm/config (song song theo contract, kiểm import khi đủ cặp) → ③ Hùng schema API → ④ Duy service glue → ⑤ Tâm eval/smoke/docs. Đây là **thứ tự merge**, không phải thứ tự bắt đầu coding. Review có thể thực hiện ngay khi PR riêng đạt targeted tests.

**Giao tiếp khi có blocker:** gửi ngay tên test, command, traceback tối thiểu, commit SHA, file owner. Owner xử lý tại branch mình; reviewer kiểm lại diff và test đúng scope. Không tự ý sửa file của nhau trong nhánh integration. Nếu một test đang phụ thuộc module chưa merge, đánh dấu `integration-pending`, không coi là lỗi của PR độc lập.

---

## VI. HƯỚNG DẪN CHẠY TEST/ĐÁNH GIÁ — TỐI GIẢN NHƯNG ĐỦ BẰNG CHỨNG

### 1. Thiết lập môi trường (PowerShell)

**Trên repo nhóm sau khi integration code/requirements có đủ:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env  # thực hiện một lần nếu chưa có .env
# Không commit .env; trong .env giữ LLM_PROVIDER=stub, RETRIEVAL_KIND=bm25
```

**Bài cá nhân Luồng A:** lệnh dưới đây chạy trong repo mà branch exercise chứa `lab06_source_lecturer_given/practice/` và `lab06_source_lecturer_given/starter/`:

```powershell
Push-Location lab06_source_lecturer_given/practice
python -m pytest -q test_mini_search.py
Pop-Location
Push-Location lab06_source_lecturer_given/starter
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q tests/test_rag.py -k citation
python -m pytest -q tests/test_rag.py -k abstain
python -m pytest -q
python eval/compare_paths.py
Pop-Location
```

### 2. Các gate test tối thiểu, tránh chạy lặp không cần thiết

| Khi nào | Test bắt buộc | Mục đích |
|---|---|---|
| Sau chỉnh 1 module riêng | `pytest -q <test-file-liên-quan>` + `git diff --check` | Chứng minh owner làm đúng; không full suite lặp sau mỗi edit |
| Sau ghép core | `pytest -q tests/test_rag.py` (nếu imported) + smoke tests mới, `pytest -q tests/test_service.py tests/test_router.py` | A1, A2, guard, deterministic, fallback, source |
| Sau Hùng ghép API | `pytest -q tests/test_api.py tests/test_db.py tests/test_persistence_restart.py` | API/DB Lab 5 vẫn đúng |
| Release candidate SHA | `pytest -q` **một lần**; `python eval/compare_paths.py`; CLI smoke | Kiểm hồi quy và evidence cuối |
| Có sửa code sau lần full regression | Chạy lại targeted, **full suite trên SHA mới** trước tag | Không dùng test cũ cho commit mới |

Các filename test mới chỉ là **gợi ý**. Test có thể nằm chung `tests/test_rag.py` hoặc file hiện hữu nếu ít trùng lặp. Lệnh có `<...>` nghĩa là thay bằng tên file thật đã có trong PR; **không báo pass** khi file test chưa tồn tại.

### 3. Lệnh demo có thể dùng sau khi tích hợp

```powershell
python -m assistant_core "tuition for 18 credits and 2 retake"
python -m assistant_core "I lost my student card"
python -m assistant_core "what is the capital of France"
python -m assistant_core "what grade did my friend get"
python -m assistant_core --test
python eval/compare_paths.py
python -m pytest -q
```

**Kiểm thủ công:** (1) fee `9,450,000` đúng; (2) card có `S26#3`; (3) France abstain; (4) private refused; (5) fake provider fail trả retrieval degraded; (6) `/v1/chat` giữ `request_id`, `/v1/feedback` lưu/đọc sau restart. Với một test bị fail, báo đúng ID và nguyên nhân, **không sửa expected** để bảng đẹp hơn.

### 4. H1 — Mẫu JSONL và kiểm tra chất lượng

```jsonl
{"id":"E21","question":"how many books can I borrow","expect_source":"S26#1","category":"normal"}
{"id":"E22","question":"who will win the football match","expect_abstain":true,"category":"out-of-scope"}
```

Đây là ví dụ minh họa cho dải ID Duy; mỗi thành viên viết 5 case thực riêng, 3 câu **source có tồn tại trong KB**, 2 câu abstain thực sự ngoài phạm vi/private. Mỗi dòng là một JSON object hợp lệ, không có dấu phẩy giữa hai dòng. Sau khi thêm 5 câu **chạy lại** `compare_paths.py`, ghi bảng mới và giải thích một failure nếu có.

### 5. Bonus (chỉ sau khi hoàn thành phạm vi C, D, E, F, H1)

- **Ollama:** model local `llama3.2`, `LLM_PROVIDER=ollama`; so sánh speed và E19 so với stub; báo các khác biệt thực tế, không hứa chính xác tuyệt đối.
- **H3:** cải thiện tokenization (bỏ `s` cuối cho từ dài hơn 4 ký tự trong `rag/index.py` theo PDF), kiểm E14 và regression; làm trên nhánh riêng, **không** thay đổi module chính khi chưa có review.

---

## VII. REVIEW, QUẢN LÝ RỦI RO VÀ RELEASE

### 1. Review/ownership không cần chờ Tâm tổng hợp

| PR B của | Reviewer chính | Điều kiện approve trước merge |
|---|---|---|
| Duy | Đạt (logic), Hùng (API) | Constructor cũ tương thích; rule/fee/office không hỏng |
| Trung Anh | Bội Anh | KB metadata + retrieval score/top-k đúng |
| Đạt | Quỳnh | A1 trước LLM; fallback và source contract đúng |
| Hùng | Duy | Chat schema additive; feedback/persistence không hỏng |
| Bội Anh | Trung Anh | Đúng 3 KB mẫu; guard có positive/negative tests |
| Quỳnh | Đạt | A2/JSON/provider config test tốt; giữ stub offline |
| Tâm | Hùng | Script eval chạy, không sửa expected, có số đo/known failures |

**Chỉ chặn merge/release khi:** test thay đổi behavior cũ không chủ ý; A1 gọi LLM khi thiếu nguồn; A2 chấp nhận citation giả; leak PII/key; DB feedback mất; API contract bị phá; không chạy được evaluation; PR sửa ngoài ownership không có thống nhất. **Không chặn chỉ vì:** reviewer muốn nhiều docs hơn, E13/E15/E19 vốn là known failures, Ollama chưa cài, hoặc không đủ 55 case.

### 2. Rủi ro và cách ngăn

| Rủi ro | Mức | Chủ xử lý | Hành động |
|---|---|---|---|
| 7 PR cá nhân cùng sửa A1/A2 | Cao nếu trộn | Duy | Giữ PR A trên `exercise/lab06-starter-base`, **không merge** vào integration |
| Thay constructor service làm hỏng fixture | Cao | Duy | Thêm optional `rag` ở cuối, tests cũ |
| LLM không kiểm nguồn/tạo hallucination | Cao | Quỳnh + Đạt | A2, A1, retry, fallback; SpyLLM tests |
| Fee/office bị route sai | Cao | Đạt + Duy | Test deterministic, known E13/E15 minh bạch |
| API/DB Lab 5 bị ghi đè | Cao | Hùng | Schema additive; test persistence; không copy starter `main.py` |
| Tâm phải gộp 35 câu hỏi | Trung bình | Tâm | Mỗi người nộp PR riêng; team chỉ curated subset nếu cần |
| Không có evidence test sau sửa cuối | Cao | Duy + Tâm | Ghi release candidate SHA, full regression lại khi SHA đổi |
| File KB được hiểu như quy định thật | Trung bình | Bội Anh | Ghi rõ sample/teaching data |

### 3. Release checklist bắt buộc

- [ ] 7 link PR A sẵn nộp (S1–S3, A1–A2, bảng/3 câu; H1 theo deadline), evidence thực tế đầy đủ.
- [ ] Các module PR B qua review; một phiên bản nhóm được ghép vào integration, không có file ngoài scope bị ghi đè.
- [ ] Guard/privacy, abstain/no-LLM, grounding, source fallback có test.
- [ ] Fee/office, API endpoints, feedback/stats, restart persistence không hồi quy.
- [ ] `pytest -q` và evaluation đã **thực chạy trên SHA release**, có bảng và known failures.
- [ ] Không commit `.env`, SQLite DB, API key, raw student PII.
- [ ] PR integration → `main` merged; tag `v0.6-ai` trỏ **đúng commit sau merge**; đã nộp LMS theo PDF.

**Lệnh release (Duy, sau xác nhận review và working tree sạch):**

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git rev-parse HEAD  # đối chiếu SHA của PR merge + test evidence
# Chỉ tạo nếu tên tag chưa tồn tại và chính commit HEAD đã qua gate:
git tag v0.6-ai
git push origin v0.6-ai
# Kiểm trên remote: git ls-remote --tags origin v0.6-ai
```

**Lưu ý:** Nếu test chạy trên commit integration khác với SHA merge thực tế, cần bảo đảm diff merge chỉ là thao tác không thay đổi nội dung, hoặc chạy lại ít nhất các gate liên quan/full regression trước khi tuyên bố đã chứng minh cho release SHA. Nếu tag tồn tại, **không force-update tag**; điều tra trước.

---

## VIII. MẪU PR VÀ MẪU BÀN GIAO NGẮN

### PR A — Bài cá nhân (mỗi người, không merge sản phẩm)

```markdown
## Lab 06 individual — <Tên>
Base: exercise/lab06-starter-base
S1–S3: <path>, pytest: <N passed / fail>
A1: <file>, abstain test: <result>
A2: <file>, citation test: <result>
Comparison: <path>, command: python eval/compare_paths.py
Three conclusions: <link/section>
H1: five cases <IDs>, re-run table: <path>
SHA tested: <sha>
Known failures: <IDs + reason>
```

### PR B — Module nhóm

```markdown
## Lab 06 group — <Tên> / <Module>
Base: integration/lab06-v0.6
Scope: <1 module + targeted tests>
Contracts used: <functions/classes>
Files changed: <paths>
Verification: <commands + actual counts + SHA>
Backward compatibility: <what was checked>
Known gaps / dependencies: <none or exact contract>
Reviewer: <owner>
```

**Bàn giao tối thiểu:** link PR; SHA tested; mô tả output/interface; log targeted tests; giới hạn/known failure; người review. Không yêu cầu thêm QA report dài riêng cho từng người nếu đã có thông tin trong PR.

---

## IX. PHÂN BIỆT QUY ĐỊNH GIẢNG VIÊN VÀ QUYẾT ĐỊNH NỘI BỘ

- **Phạm vi nhóm chọn từ PDF:** S1–S3, A1–A2, comparison/3 câu, team integration và H1 theo mốc; mỗi thành viên mở PR, nhóm merge một bản và Member 1 tag `v0.6-ai`; LLM thật chỉ bonus.
- **Đề xuất nội bộ để giảm xung đột:** tách nhánh `exercise/lab06-starter-base`, branch `integration/lab06-v0.6`, file ownership, signature contract, reviewer pairing, giai đoạn P0–P3, dải E21–E55 và 20-case release baseline. Những phần này **không được diễn giải là giảng viên yêu cầu chính xác các tên branch/file/test**.
- **Cơ sở đã kiểm qua GitHub:** `src/assistant_core/service.py`, `models.py`, `router.py`, `config.py`, `responder.py`, `knowledge.py`, API/schema/DB và test cũ trong nhóm; các file starter `llm.py`, `rag/answerer.py`, `rag/index.py`, `rag/chunker.py`, `eval/*`, `data/kb/*.md` cùng `test_rag.py` và `mini_search.py`. Các lệnh/tỷ lệ test trong kế hoạch là **điều kiện phải đo**, không phải bằng chứng test đã chạy.

**Nguồn:**

1. Tài nguyên Lab 6 giảng viên tại thư mục `lab06_source_lecturer_given/` (practice, starter, worksheets).
2. [Repo nhóm](https://github.com/Computational-Thinking-Project/assistant_core_lab).
3. PDF Lab 6: trang 4 (deliverables), 8–9 (S1–S3), 11–13 (A1–A2), 15–16 (evaluation), 18 (team integration), 19–20 (homework/deadlines/rubric).
4. Review kế hoạch do người dùng cung cấp (09/11/2026); nhận định về tối ưu workflow là **khuyến nghị**, không phải kết quả chạy code.
