# Đóng gói phương án A và kiểm tra cài sạch — 12/11/2026

Người dùng xác nhận đợt R2 ("Thực hiện đi") và chọn **phương án A**: Compose chỉ chạy storage, còn API, worker và frontend chạy trên host Windows.

Đợt này **không gọi Gemini**, không tải model, không đụng dữ liệu hay volume dev. Bản cài sạch dùng thư mục, venv, `node_modules`, Compose project và volume riêng.

## 1. Thay đổi đóng gói (commit `0c1862b`)

- **`compose.yaml`:**
  - Chỉ còn `db` và `qdrant`.
  - Bỏ service `backend`: image Linux build từ `requirements.lock` không có Torch/E5, nên không chạy được search hay answer. Giữ lại sẽ gây hiểu nhầm là API đã container hóa.
  - Port host cấu hình được qua `DB_HOST_PORT` / `QDRANT_HOST_PORT` (mặc định 5433/6333), để chạy song song một bản cài khác.
- **`backend/Dockerfile`:** bỏ `alembic upgrade head` khỏi `CMD`, vì migration là bước riêng. Comment ghi rõ image này không thuộc topology M1.
- **`.env.example`:** thêm biến port; thay đường dẫn cache ổ `D:` của máy cũ bằng placeholder `<absolute-repo-path>`, kèm ghi chú E5 phải có sẵn trong `HF_HOME`.

Container hóa API/worker trên Linux (lock Torch CPU cho Linux, model cache volume) chuyển vào **Roadmap**.

## 2. Môi trường kiểm tra

| Thành phần | Giá trị |
|---|---|
| Source | `git clone --branch release/m1` từ repo local, HEAD `0c1862b`, vào `.cache/fresh-setup-20261112/repo` (bị Git ignore) |
| Đối chiếu source | 167/167 file khớp bản acceptance: 103 khớp byte tuyệt đối, 64 chỉ khác line-ending ([K-101](../KNOWLEDGE.md)) |
| Công cụ | Windows 11, Docker 27.3.1, Python 3.12.1, Node 24.11.1, npm 11.6.2 |
| Storage | Compose project `smefresh`, volume mới `smefresh_db_data` / `smefresh_qdrant_data`, port 5434/6343, `--pull never` (dùng image đã có) |
| `.env` | Tạo từ `.env.example`. Mật khẩu DB và demo sinh ngẫu nhiên, không in ra. Gemini tắt (key rỗng, cờ false) |
| Model cache | `HF_HOME` trỏ vào cache E5 đã có của repo chính, đúng revision khóa; chạy với `HF_HUB_OFFLINE=1`, không tải gì |
| Dependency cache | Dùng chung `PIP_CACHE_DIR` / `NPM_CONFIG_CACHE` của repo chính |

## 3. Các bước và kết quả

Log nằm ở `.cache/fresh-setup-20261112/logs/` (local, bị Git ignore).

| # | Bước | Lệnh chính (chạy trong bản clone) | Kết quả |
|---|---|---|---|
| 1 | Storage | `docker compose -p smefresh up -d --pull never --wait db qdrant` | Healthy sau 8,2 s |
| 2 | Backend deps | `python -m venv backend\.venv`, rồi `pip install -r requirements-dev.lock -r requirements-worker-cpu.lock -e ./backend[dev,worker]` | Exit 0, khoảng 478 s; `pip check` sạch |
| 3 | Migration | `alembic upgrade head` (từ `backend/`) | DB rỗng → `20261103_rag04 (head)` |
| 4 | Seed | `python -m app.seed`, chạy 2 lần | Lần 1 tạo 2 user; lần 2 tạo 0 (idempotent) |
| 5 | API + worker | `uvicorn app.main:app --port 8001` và `python -m app.worker` | Health OK; worker tạo collection và payload index; 0 lỗi trong log |
| 6 | Ingest | Admin upload 10 tài liệu `eval/datasets/corpus` qua API | 10/10 `ready` sau 27,8 s kể từ lần upload đầu |
| 7 | Search (member) | 13 câu dev có đáp án, `top_k=5` | Xem mục 4 |
| 8 | Phân quyền | Member upload | **403** `forbidden` |
| 9 | Chat khi tắt LLM | `POST /chat/query` | **503** `model_unavailable`, không trả `answer_status`, tức không giả làm abstention |
| 10 | Delete | Admin xóa `huong_dan_bao_mat.txt` | Delete 202; source 410; document 410; tài liệu không còn trong danh sách |
| 11 | Cleanup sau delete | Kiểm tra SQL, Qdrant, storage | Job cleanup `completed`; 13 chunk SQL = 13 point Qdrant; 9 file còn trong storage (file đã xóa không còn) |
| 12 | Frontend | `npm ci`, rồi `lint` / `test` / `build` | `npm ci` 146 s; lint đạt; **36/36 tests**; build đạt, bundle `index-CMvF0uIm.js` trùng tên hash với bản build ở dev |
| 13 | Backend tests | `pytest` trên DB test riêng `copilot_test` (port 5434), API/worker đã dừng | **302 passed**, 0 failed/skipped, trong **một lần chạy**, 587,5 s; 1 cảnh báo Starlette/httpx (baseline). Khác đợt acceptance (300/302 rồi retest có phạm vi), lần này đạt trọn trong một invocation trên bản clone sạch |

## 4. Search smoke và một lỗi trong script kiểm tra

**Lỗi ở script kiểm tra, không phải ở hệ thống:**
- Lần đầu, script so tên file bằng trường `file_name`, nhưng hit chỉ có `document_id` (tên nằm trong `source`). Script vì thế báo 0/13 trúng và "tài liệu đã xóa không có trong search".
- Kết luận về delete ở lần này **không hợp lệ**, vì so sai trường.

**Lần kiểm tra lại (chỉ đọc), so bằng `document_id`, sau khi đã xóa:**
- 4/13 câu có tài liệu gold là tài liệu đã xóa, nên loại khỏi phép tính trúng.
- **9/9** câu còn lại có đủ tài liệu gold trong top 5.
- **0 hit** trỏ tới tài liệu không ở trạng thái `ready`. Đây là bằng chứng tài liệu đã xóa không quay lại search.
- Độ trễ warm: p50 khoảng 125 ms, max khoảng 2,1 s. Query đầu tiên mất 17,3 s vì API nạp E5 lần đầu (cold start).

Đây là **smoke ở mức tài liệu trên tập dev**, không phải metric theo span hay benchmark mới. Không so sánh với Recall@5/MRR của held-out.

## 5. Phạm vi và giới hạn

- **Có kiểm chứng:** setup từ Git → storage sạch → dependency từ lockfile → migrate → seed → ingest → search → phân quyền → lỗi kỹ thuật khi tắt LLM → delete/cleanup → frontend build/test → toàn bộ 302 backend tests.
- **Chưa chạy trên bản clone:** 91 eval tests (eval/). Lượt trước của chúng vẫn ở báo cáo acceptance.
- **Không kiểm chứng:**
  - Câu trả lời thật từ Gemini (cần đợt có grant riêng).
  - Tải E5 từ Hugging Face trên máy mới: model cache được dùng chung; runbook có lệnh tải đúng revision, nhưng lần này không chạy.
  - Máy hoàn toàn mới chưa có pip/npm cache.
  - Launcher `start-web.cmd`: launcher đọc `.env` của chính thư mục và dùng port cố định 8000/5173; lần này dùng lệnh trực tiếp.
  - Linux worker image.
- Image Postgres/Qdrant được dùng lại, không pull (`--pull never`); digest đã được pin trong `compose.yaml`.

**Dọn dẹp:** API và worker của bản cài sạch đã dừng. Đã gỡ Compose project `smefresh` bằng `docker compose -p smefresh down -v`, cùng 2 volume riêng của nó (còn 0 volume). Stack dev (`sme-ai-operations-copilot-*`) và volume dev không bị đụng tới. Thư mục clone, gồm venv và `node_modules`, nằm trong `.cache/`, có thể xóa khi không cần xem lại.

## 6. Tiến độ

Bước 12 ghi nhận **2/6**: mục 1 (topology Compose theo phương án A, migration tách riêng) và mục 2 (cài sạch trên volume riêng).

`(89,5 + 8×6/7 + 5×2/6) / 102,5 × 100 ≈ 95,6%`. Mục 3–6 (README, video, đóng góp cá nhân, rà soát cuối) còn mở.
