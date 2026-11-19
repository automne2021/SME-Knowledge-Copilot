# Roadmap sau M1 — SME Knowledge Copilot

> **Người viết:** Claude, vai trò quản lý dự án. **Người thực hiện:** Codex, vai trò developer.
> **Ngày lập:** 13/11/2026. **Trạng thái M1:** 97,4% / 100% theo [PLAN](../../PLAN.md); phần còn lại (video, đóng góp cá nhân) do người dùng làm.
> **Mục đích:** biến project từ "RAG chạy đúng" thành "RAG có chiều sâu, đo được cải tiến, dùng được như sản phẩm", phục vụ hồ sơ VNG AI Builder Residency.

## Đọc tối thiểu khi nhận một task (tiết kiệm token)

Người dùng chỉ cần gõ: **"Làm task NN-Tk"**. Khi đó assistant đọc **đúng các phần sau**:

1. **Bắt buộc (khoảng 300 dòng):**
   - File này: **mục 4** (quy tắc, định nghĩa xong, lệnh chuẩn) và **mục 6** (mẫu báo cáo).
   - Toàn bộ file tính năng `docs/roadmap/NN-*.md`.
   - File spec phụ mà file tính năng ghi "bắt buộc đọc" (ví dụ [01-corpus-v2-spec.md](01-corpus-v2-spec.md) cho 01-T2a/b/c và T3).
   - Từ task thứ hai của một tính năng, khi mở **phiên mới**: report gần nhất của **cùng tính năng** (`docs/<tên>-<date>.md`) và `git log --oneline` của nhánh, để biết phiên trước đã làm tới đâu.
2. **Chỉ khi file tính năng trỏ tới hoặc task đụng phần đó:**
   - Mục "Bất biến nghiệp vụ" trong `CLAUDE.md`, khi task đụng retrieval, xóa, quyền hoặc chat.
   - Đúng mục spec được ghi (ví dụ "spec mục 8.8"), không đọc cả spec.
   - Đúng chủ đề trong `KNOWLEDGE.md`, dùng mục lục để nhảy tới.
   - Các file code liệt kê ở mục "Hiện trạng" của file tính năng. Mở rộng sang file khác khi thật sự cần, và nêu lý do trong phần trình bày phạm vi.
3. **Không đọc:**
   - `PLAN.md`, `HANDOFF_CLAUDE.md`, `docs/history/`.
   - Các report cũ trong `docs/` (trừ report gần nhất của cùng tính năng), `eval/reports/`, `eval/snapshots/`, `.cache/`.
   - Mục 1–3 và mục 7 của file này (bối cảnh cho người lập plan).
4. **Task tiếp theo của cùng tính năng, trong cùng phiên:** không đọc lại các file trên; chỉ xem lại phần task mới trong file tính năng.

## 1. Bức tranh hiện tại (bối cảnh, không bắt buộc đọc mỗi task)

Hệ thống hỏi đáp tài liệu nội bộ tiếng Việt. Trả lời kèm trích dẫn do backend kiểm tra, và nói "chưa đủ bằng chứng" thay vì bịa.

| Lớp | Hiện trạng | File chính |
|---|---|---|
| Ingestion | Upload PDF có text, DOCX, TXT, MD. Parser giữ vị trí nguồn (trang, đoạn, dòng, hàng bảng). Chunk 350 token, overlap 50. Worker bền: `FOR UPDATE SKIP LOCKED`, lease, heartbeat, generation fencing, retry | `backend/app/services/{uploads,parsing,chunking,ingestion,jobs}.py`, `backend/app/worker.py` |
| Embedding | `intfloat/multilingual-e5-small` 384 chiều, chạy local trên CPU, revision được pin | `services/embeddings.py`, `e5_runtime.py` |
| Retrieval | Chỉ dense: Qdrant top-20 → kiểm tra lại bằng SQL → top-5. Không có ngưỡng score | `services/retrieval.py`, `vectors.py` |
| Generation | Gemini 3.5 Flash-Lite qua adapter native. Context 4.000 token đếm bằng countTokens. Output JSON gồm các claim, sửa tối đa 1 lần. Trạng thái `grounded`, `partial`, `insufficient_evidence` | `services/answering.py`, `chat.py`, `gemini.py` |
| Xóa | Chuyển `deleting` để chặn retrieval ngay, cleanup có retry. Lịch sử và nguồn không "hồi sinh" | `services/deletion.py`, `cleanup.py`, `privacy.py` |
| Auth | Bearer token (chỉ lưu digest), role đọc lại mỗi request, logout thu hồi token. Hai tài khoản seed | `core/security.py`, `api/identity.py` |
| UI | React + TS + Vite + Tailwind. Hỏi đáp, Tài liệu, Lịch sử, panel nguồn | `frontend/src/` |
| Eval | 45 câu (15 dev, 30 held-out) do người duyệt. Held-out đạt 29/30, Recall@5 1,0, trích dẫn 36/36 | `eval/`, `eval/reports/final-20261112/` |
| Test | 316 backend (PostgreSQL và Qdrant thật), 277 eval tooling, 49 frontend | — |

Giới hạn đã biết:
- Bộ eval nhỏ (45 câu) và chỉ dùng dữ liệu giả lập. Chưa có câu nào lấy bằng chứng từ bảng; chỉ 1 câu mâu thuẫn và 3 câu cần nhiều tài liệu.
- Chỉ có dense retrieval.
- Chưa hỏi nối tiếp được.
- Chưa có OCR.
- API và worker chưa chạy được trên Linux.
- Câu trả lời trả về một lần, chưa stream.
- Chưa có kênh nào để người dùng phản hồi về câu trả lời.

## 2. Định vị với nhà tuyển dụng (VNG)

Nhà tuyển dụng AI Builder sẽ chú ý tới bốn điều. Mỗi tính năng trong roadmap phải phục vụ ít nhất một điều:

1. **Chiều sâu AI có đo lường.** Mỗi thay đổi về retrieval hay model phải có số trước/sau trên cùng bộ eval, kể cả khi kết quả không cải thiện.
2. **Xử lý tiếng Việt thật sự.** Tách từ cho tìm kiếm từ khóa, dấu và không dấu, bảng biểu, văn bản scan.
3. **Sản phẩm dùng được.** Người dùng hiểu trạng thái hệ thống, phản hồi được về câu trả lời, admin thấy được chất lượng.
4. **Vận hành có trách nhiệm.** Chi phí 0 USD có kiểm soát, quan sát được hệ thống (observability), triển khai được, lỗi phải được báo là lỗi.

## 3. Lộ trình

| Mốc | Thời gian | Mục tiêu | Tính năng |
|---|---|---|---|
| **M2: Đo được để cải tiến** | 16/11 – 30/11 | Có bộ eval đủ lớn và tìm kiếm tốt hơn, có số chứng minh | [00](00-housekeeping.md), [01](01-eval-expansion.md), [02](02-hybrid-search-reranker.md), [03](03-folders-scoped-qa.md) |
| **M3: Sản phẩm hoàn chỉnh hơn** | 01/12 – 10/12 | Demo được online, trải nghiệm mượt, có vòng phản hồi | [04](04-table-aware-retrieval.md), [05](05-streaming-progress.md), [06](06-follow-up-questions.md), [07](07-feedback-analytics.md), [11](11-deploy-linux-docker.md) |
| **M4: Mở rộng** | Sau 10/12 | Tính năng nâng cao, chọn theo phản hồi từ phỏng vấn | [08](08-ocr-scanned-pdf.md), [09](09-document-versioning.md), [10](10-llm-provider-local.md), [12](12-observability.md), [13](13-chat-channel-integration.md) |

Mốc 15/11 (nộp CV kèm video) **không** nằm trong roadmap. Không bắt đầu task nào ảnh hưởng tới bản demo trước khi người dùng quay video xong.

### Ma trận ưu tiên

| # | Tính năng | Giá trị với VNG | Công sức | Rủi ro | Phụ thuộc |
|---|---|---|---|---|---|
| 00 | Dọn nợ kỹ thuật | Thấp (nhưng cần) | S | Thấp | — |
| 01 | Mở rộng eval và chạy hồi quy | **Rất cao** | M | Trung bình (cần người duyệt nhãn) | 00 |
| 02 | Hybrid search tiếng Việt + reranker | **Rất cao** | L | Trung bình | 01 |
| 03 | Thư mục và hỏi theo thư mục | Cao | M | Thấp | — |
| 04 | Retrieval nhận biết bảng | Cao | M | Trung bình | 01 |
| 05 | Stream tiến độ khi trả lời | Trung bình | M | Trung bình | — |
| 06 | Hỏi nối tiếp | Cao | M | Trung bình | 01 |
| 07 | Phản hồi người dùng và dashboard | Cao | M | Thấp | — |
| 08 | OCR PDF scan | Trung bình | L | Cao (CPU, chất lượng) | 01 |
| 09 | Phiên bản tài liệu và reindex | Trung bình | L | Cao | — |
| 10 | Provider LLM thay thế | Cao | L | Cao (phần cứng) | 01 |
| 11 | Docker Linux và demo online | **Rất cao** | L | Trung bình | — |
| 12 | Trang xem trace | Trung bình | M | Thấp | 07 |
| 13 | Kênh chat (Zalo OA) | Cao với VNG | M | Trung bình (tài khoản OA) | 11 |

Công sức: S ≤ 0,5 ngày, M 1–2 ngày, L 3–5 ngày cho một dev.

## 4. Quy tắc làm việc cho Codex

Đây là phần bắt buộc. Quy tắc gốc nằm ở [AGENTS.md](../../AGENTS.md); phần dưới cụ thể hóa cho roadmap.

### 4.1. Phạm vi đọc

Theo mục "Đọc tối thiểu" ở đầu file. Không tin mô tả trong plan hơn code thật; nếu lệch, báo lại trước khi làm.

### 4.2. Một task là một đợt xác nhận

- Mỗi file tính năng chia thành task `T1`, `T2`… Mỗi task là **một** đợt công việc.
- Trước khi sửa bất kỳ file nào: trình bày phạm vi (file sẽ sửa, migration, API, test) và chờ người dùng nói đúng câu **"Thực hiện đi"**.
- Không gộp task, không tự chuyển sang task tiếp theo, không làm phần "Không làm" của plan.
- Task có đổi UI cần xác nhận UI riêng (quy tắc 03/11/2026).
- Gặp quyết định chưa có trong plan (đổi contract, thêm dependency, đổi model), dừng lại và hỏi; đề xuất 2–3 phương án kèm khuyến nghị.

### 4.3. Nhánh, commit, push

- Mỗi tính năng một nhánh `feat/<số>-<slug>`, ví dụ `feat/02-hybrid-search`, tạo từ `main` mới nhất.
- Commit theo task, message tiếng Anh, có dòng `Co-Authored-By` theo cấu hình của công cụ.
- **Không push, không merge vào `main`** khi chưa có xác nhận riêng. `release/m1` là bản chốt M1, không được sửa.

### 4.4. Định nghĩa "xong" cho mọi task

- [ ] Test cho cả trường hợp đúng và lỗi. Logic DB và retrieval test trên PostgreSQL và Qdrant thật.
- [ ] Backend: `pytest` toàn bộ đạt; `ruff check` và `ruff format --check` đạt.
- [ ] Frontend (nếu có sửa): `npm.cmd run lint`, `npm.cmd run test`, `npm.cmd run build` đạt.
- [ ] Eval tooling (nếu đụng `eval/` hoặc service mà eval dùng): `pytest eval/tests` đạt.
- [ ] Đổi API, schema hay state thì cập nhật spec trong cùng commit. Đổi schema phải qua migration Alembic.
- [ ] Thêm biến cấu hình thì cập nhật `.env.example`.
- [ ] Ghi một mục ngắn vào phần "Nhật ký quyết định" của [KNOWLEDGE](../../KNOWLEDGE.md) và sửa phần chủ đề liên quan.
- [ ] Viết report `docs/<slug>-<YYYYMMDD>.md`: đã làm gì, lệnh và kết quả thật, giới hạn, việc chưa kiểm chứng.
- [ ] Cập nhật bảng trạng thái ở mục 5 của file này.

Không báo "xong" nếu có bước chưa chạy. Ghi rõ bước nào bỏ qua và vì sao.

### 4.5. Lệnh chuẩn (Windows, từ thư mục gốc repo)

```powershell
# Backend (TEST_DATABASE_URL phải là DB riêng tên *_test trên 127.0.0.1)
cd backend; .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider; .\.venv\Scripts\ruff.exe check --no-cache .; .\.venv\Scripts\ruff.exe format --check --no-cache .; cd ..
# Eval tooling: cần backend trong PYTHONPATH
$env:PYTHONPATH='backend'; .\backend\.venv\Scripts\python.exe -B -m pytest eval/tests -q -p no:cacheprovider
# Frontend
cd frontend; npm.cmd run lint; npm.cmd run test; npm.cmd run build; cd ..
```

Lưu ý môi trường:
- Dùng `127.0.0.1`, không dùng `localhost`, vì Docker chỉ mở cổng IPv4 ([KNOWLEDGE](../../KNOWLEDGE.md), mục Vận hành).
- Launcher `start-web.cmd` từ chối chạy khi pytest đang chạy; dừng stack bằng `stop-web.cmd` trước khi chạy toàn bộ test.
- `test_worker.py::test_heartbeat_runs_during_inference_without_document_lock` đã đổi sang quan sát lease gia hạn ở 00-T1; kết quả và giới hạn kiểm chứng ở [report](../housekeeping-20261115.md#00-t1--ổn-định-test-heartbeat).

### 4.6. Gọi model thật và ngân sách

- Ngân sách **0 USD**: chỉ dùng free tier, không bật billing, không fallback sang dịch vụ trả phí.
- Mọi lần gọi Gemini thật (eval, smoke) phải nằm trong đợt có xác nhận riêng, nêu trước số lần gọi dự kiến, và ghi ledger. Unit test dùng provider giả có nhãn.
- Không đổi model, prompt hay cấu hình đã khóa (`rag-v1-claims`, E5 revision) khi chưa có eval so sánh và người dùng duyệt.

### 4.7. Những việc không làm trong roadmap này

- Agent loop, tool calling, LangChain/LangGraph làm core pipeline (spec mục 19).
- Microservices, Kubernetes, Redis/Celery.
- Multi-tenant thật, SSO, billing.
- Đưa lại STT/meeting/proposal của hướng Operations cũ.

## 5. Bảng trạng thái

Codex cập nhật bảng này ở cuối mỗi task. Tiến độ roadmap tính riêng, **không** trộn vào % của M1 trong PLAN.

| # | Tính năng | Task xong / tổng | Trạng thái | Nhánh | Report |
|---|---|---|---|---|---|
| 00 | [Dọn nợ kỹ thuật](00-housekeeping.md) | 2/4 | T1, T4 xong; T2–T3 chưa bắt đầu | `feat/00-housekeeping` | [00-T1 — Heartbeat](../housekeeping-20261115.md#00-t1--ổn-định-test-heartbeat), [00-T4 — GIF demo](../housekeeping-20261115.md) |
| 01 | [Mở rộng eval](01-eval-expansion.md) ([spec corpus](01-corpus-v2-spec.md)) | 4/7 | T1, T2a, T2b, T2c xong; T3–T5 chưa bắt đầu | `feat/01-eval-v2` | [01-T1 — Schema v2](../eval-v2-20261115.md), [01-T2a — Corpus](../corpus-v2-20261115.md), [01-T2b — Văn bản dài và Markdown](../corpus-v2-20261115.md#01-t2b--d01-d06-d07-d08), [01-T2c — Chốt 14 tài liệu](../corpus-v2-20261115.md#01-t2c--d09d14-chốt-corpus) |
| 02 | [Hybrid search](02-hybrid-search-reranker.md) | 0/5 | Chưa bắt đầu | — | — |
| 03 | [Thư mục](03-folders-scoped-qa.md) | 2/4 | T1–T2 xong; T3–T4 chưa bắt đầu | `feat/03-folders` | [03-T1 — Schema và API](../folders-20261118.md), [03-T2 — Gán tài liệu](../folders-20261119.md) |
| 04 | [Retrieval nhận biết bảng](04-table-aware-retrieval.md) | 0/3 | Chưa bắt đầu | — | — |
| 05 | [Stream tiến độ](05-streaming-progress.md) | 0/3 | Chưa bắt đầu | — | — |
| 06 | [Hỏi nối tiếp](06-follow-up-questions.md) | 0/4 | Chưa bắt đầu | — | — |
| 07 | [Phản hồi và dashboard](07-feedback-analytics.md) | 0/4 | Chưa bắt đầu | — | — |
| 08 | [OCR](08-ocr-scanned-pdf.md) | 0/4 | Chưa bắt đầu | — | — |
| 09 | [Phiên bản tài liệu](09-document-versioning.md) | 0/4 | Chưa bắt đầu | — | — |
| 10 | [Provider LLM](10-llm-provider-local.md) | 0/4 | Chưa bắt đầu | — | — |
| 11 | [Docker Linux và demo](11-deploy-linux-docker.md) | 0/4 | Chưa bắt đầu | — | — |
| 12 | [Trang trace](12-observability.md) | 0/3 | Chưa bắt đầu | — | — |
| 13 | [Kênh chat](13-chat-channel-integration.md) | 0/3 | Chưa bắt đầu | — | — |

**Cách tính % roadmap:** `Σ(task xong của tính năng × trọng số) / Σ(tổng task × trọng số)`. Trọng số S=1, M=2, L=3 theo cột Công sức ở mục 3. Báo riêng % từng mốc (M2, M3, M4).

## 6. Mẫu báo cáo cuối task (Codex gửi người dùng)

```markdown
**Task:** 02-T3 — <tên task>
**Nhánh / commit:** feat/02-hybrid-search @ <hash> (chưa push)
**Đã làm:** <3–6 gạch đầu dòng, nói hành vi chứ không liệt kê file>
**Kiểm chứng:** backend <n>/<n>, eval <n>/<n>, frontend <n>/<n>; <số đo nếu có, kèm mẫu số>
**Chưa kiểm chứng / giới hạn:** <...>
**Quyết định cần người dùng:** <hoặc "không có">
**Tiến độ roadmap:** M2 x% · tổng y%
```

## 7. Cách viết một file tính năng (dành cho người lập plan)

Mỗi file có các mục: Mục tiêu · Giá trị với nhà tuyển dụng · Hiện trạng · Thiết kế · Task (mỗi task có phạm vi, file, test bắt buộc, tiêu chí nghiệm thu) · Số đo · Rủi ro · Không làm · Câu hỏi mở. Giữ tên code, API, field bằng tiếng Anh; nội dung UI và prompt bằng tiếng Việt.
