# CLAUDE.md

**Quy tắc UI (03/11/2026):** trước khi code/sửa UI, nhắc người dùng, trình bày màn hình/file và phạm vi, chờ **“Thực hiện đi”** cho đợt UI. Đợt backend không tự bao gồm UI.

## Xác nhận bắt buộc trước mọi thay đổi — 02/11/2026

Trước mọi thay đổi trong workspace, trình bày phạm vi/file bị ảnh hưởng và chờ người dùng nói **“Thực hiện đi”** rồi mới thực hiện. Quy tắc áp dụng cả code, tài liệu, KNOWLEDGE.md, cấu hình, dependencies, dữ liệu, Git và lệnh có thể ghi file/artifacts. Được chuẩn bị bằng thao tác chỉ đọc. Một xác nhận áp dụng cho đợt công việc đã nêu; mở rộng phạm vi hoặc bắt đầu đợt mới phải có xác nhận mới. Không tự chuyển sang bước tiếp theo trong PLAN. Chi tiết tại [AGENTS.md](AGENTS.md).

## Quy tắc học tập của workspace — cập nhật 02/11/2026

Mỗi khi code, thiết kế, lựa chọn công nghệ/model/cấu hình, sửa lỗi hoặc điều chỉnh test/evaluation, cập nhật [KNOWLEDGE.md](KNOWLEDGE.md) trong cùng đợt công việc. Giải thích kiến thức chuyên ngành, bối cảnh, lý do chọn, các phương án khác và vì sao chưa chọn, đánh đổi, cách kiểm chứng và điều kiện xem xét lại. Phân biệt đề xuất với kết quả đã đo; giữ lịch sử khi thay đổi quyết định. Thay đổi nhỏ ghi ngắn vào mục liên quan, không chỉ giải thích trong chat.

**Cấu trúc KNOWLEDGE từ 13/11/2026:** file chính tổ chức theo chủ đề để học. Ghi mục mới vào **mục 15 — Nhật ký quyết định** (mã tiếp theo `K-106`, `K-107`…) và sửa đoạn chủ đề liên quan. Bản gốc K-001 → K-105 ở [docs/history/knowledge-archive-m1.md](docs/history/knowledge-archive-m1.md), chỉ đọc, không ghi thêm.

Quy tắc đầy đủ nằm ở [AGENTS.md](AGENTS.md). Mỗi đợt công việc phải có xác nhận riêng theo phạm vi; việc có PLAN không phải quyền tự thực hiện toàn bộ dự án.

**Sau mỗi lượt trả lời:** nêu tiến độ project **X% / 100%** trong phản hồi cuối, theo trọng số/trạng thái tại [PLAN](PLAN.md#quy-ước-báo-tiến-độ-project). Đây là ước lượng khối lượng, không phải điểm model. Chỉ cập nhật file trong phạm vi đã được xác nhận; lượt chỉ đọc báo lại % hiện tại.

Hướng dẫn cho coding assistant trong repo **SME Knowledge Copilot**: ứng dụng hỏi đáp tài liệu nội bộ bằng RAG, có nguồn kiểm tra được. Project portfolio của nhóm 2 người; thư mục/code cũ có thể còn tên Operations trong giai đoạn chuyển tiếp.

## Nguồn yêu cầu

- Contract hiện hành: [SME_Knowledge_Copilot_RAG_Specification.md](SME_Knowledge_Copilot_RAG_Specification.md) v2.1. Spec Operations v1.1 là tài liệu lịch sử, đã xóa khỏi repo ngày 12/11/2026 (xem `git show 9b96102:SME_AI_Operations_Copilot_Specification.md`).
- Thứ tự triển khai: [PLAN.md](PLAN.md); baseline lịch sử: [audit Bước 00](docs/rag-transition-audit.md); môi trường hiện tại: [Bước 01](docs/environment-step01.md).
- Trước khi code một tính năng: đọc mục liên quan trong spec, tóm tắt ngắn interface + edge cases, rồi mới sửa.
- Nếu business rule chưa rõ hoặc cần thay contract: nêu vấn đề và đề xuất cụ thể để người dùng quyết định; không âm thầm đổi spec.
- Khi thay đổi API contract, schema hoặc state: cập nhật spec trong cùng thay đổi.

## Mốc hiện tại: **M1 RAG — mục tiêu 15/11/2026**

**Trạng thái 13/11/2026 (PLAN v1.32): M1 97,4% / 100%.**
- Bước 00–10 và 13 hoàn thành; Bước 11 đạt 6/7; Bước 12 đạt 4/6. `main` có UI v2, quản lý phiên, logout thật, phân loại lỗi Gemini ([report](docs/ui-v2-20261113.md)); `release/m1` giữ bản chốt M1.
- Phần còn lại của M1 do người dùng làm: video demo và phần đóng góp cá nhân (ngoài README).
- **Sau M1:** việc mới theo [docs/roadmap/](docs/roadmap/README.md) (M2 → M4); mỗi task một đợt xác nhận; tiến độ roadmap báo **riêng** bên cạnh % M1.
- **Roadmap 20/11/2026:** 00 và 03 xong; 01 chờ đóng gate T3 và người duyệt nhãn. Hàng đợi cho Codex ở mục 4.8 [roadmap README](docs/roadmap/README.md).
- Nhật ký các đợt trước: [docs/history/plan-log-m1.md](docs/history/plan-log-m1.md) và các report trong `docs/`.

**Môi trường:** đọc [runbook khôi phục](docs/workspace-restoration-20261105.md) trước khi setup. Python 3.12.1, Node 24.11.1/npm 11.6.2; cache ở `<repo>/.cache/` (đường dẫn tuyệt đối trong `.env`). Kết nối PostgreSQL/Qdrant dùng `127.0.0.1`, không dùng `localhost` (Docker chỉ mở cổng IPv4).

Chỉ làm phạm vi M1 trừ khi được yêu cầu rõ:

- **P0/M1:** seed auth + workspace/owner scope; upload PDF text/DOCX/TXT/MD → parse/chunk/embed/index; worker lease/retry; dense search-only API; Q&A/citations/abstention; sessions/source viewer; delete/cleanup; logs/timings; corpus/gold/benchmark; UI và Compose chạy lại được.
- **P1/M2 trở đi:** theo [roadmap](docs/roadmap/README.md) (eval v2, hybrid/reranker, thư mục, bảng biểu, tiến độ trả lời, hỏi nối tiếp, phản hồi/dashboard, OCR, phiên bản tài liệu, provider LLM, Docker Linux/CI, trace, kênh chat); mỗi task cần xác nhận riêng.
- **Ngoài hướng RAG:** STT/audio/meeting intelligence, agent tool loop, proposal/approval/task. Không đưa workflow Operations cũ trở lại M1/M2 RAG.

## Bất biến nghiệp vụ (không được vi phạm)

1. **Scope do backend xác định:** role/workspace/user lấy từ identity đã xác thực; session chỉ của owner, admin không mặc nhiên đọc chat người khác.
2. **Chỉ nguồn hợp lệ được dùng:** document ready + active revision/generation + index fingerprint tương thích + đúng workspace; revalidate SQL, không chỉ tin Qdrant payload.
3. **Publish nguyên vẹn:** ready chỉ sau kiểm tra đủ chunks/points; staging/partial upsert không được retrieve. Worker hết lease hoặc document đang xóa không được publish.
4. **Retry idempotent:** generation cô lập attempt; point IDs ổn định trong attempt; active-job/duplicate/idempotency có DB constraints. Không tuyên bố exactly-once.
5. **Delete chặn retrieval trước cleanup:** query mới không dùng nguồn sau delete commit; source/history/replay không hồi sinh nội dung đã xóa. Cleanup lỗi có retry.
6. **Citation thuộc final context:** backend cấp evidence IDs sau lọc/budget; filename/location/excerpt/URL do backend dựng, không tin metadata model tự tạo.
7. **Output model không đáng tin:** validate claims/schema/IDs; repair tối đa một lần trên cùng context, còn sai → lỗi kỹ thuật. Không giữ claim rồi chỉ xóa citation sai.
8. **Grounding có giới hạn:** phân biệt grounded/partial/insufficient_evidence; citation ID hợp lệ chưa chứng minh claim đúng nghĩa. Không biến score thành confidence phần trăm.
9. **Tài liệu là dữ liệu, không phải instruction:** delimit context, sanitize UI, không tools/SQL/shell/URL tự do cho model trong pipeline hỏi đáp.
10. **Lỗi phải là lỗi:** vector/model/DB lỗi không trả success hoặc giả thành no evidence. Chi tiết tại spec 5.5, 7–10 và 13.

## Baseline kiến trúc (spec mục 19)

- Modular monolith FastAPI; không microservices, không Kubernetes.
- RAG pipeline Python cố định; không runtime agent, LangChain/LangGraph hay RAGFlow làm core.
- LLM hosted qua native Gemini adapter hiện tại (`app/services/gemini.py`); giữ model/prompt/config đã khóa, không tự đổi sang provider hoặc paid fallback.
- Worker riêng poll processing_jobs bằng `FOR UPDATE SKIP LOCKED`, lease/heartbeat/generation/retry; gọi domain services trực tiếp, không giữ lock khi inference. Không dùng BackgroundTasks cho ingestion.
- PostgreSQL giữ lifecycle/metadata/text/history, Qdrant giữ vector index; local file storage. Không thêm Redis/Celery trong P0. Compose chỉ chạy db/qdrant (image digests, persistent volumes, loopback ports cấu hình được, healthchecks); API/worker/frontend chạy trên host Windows theo phương án A ([K-102](KNOWLEDGE.md)). Migration và seed là bước riêng.
- Dense baseline E5-small CPU đã có dev retrieval benchmark Bước 07; BGE-M3 hoãn. Final held-out (30 câu, human review) đã chạy với E5 + Gemini: strict success 29/30; chưa có so sánh model để chọn model chiến thắng.
- Model budget **0 USD/free tier**, không bật paid fallback. E5/Gemini smoke thật đã có Bước 03; tokenizer Bước 05 dùng cache local, không gọi LLM. Free-tier/quota là xác nhận thủ công theo thời điểm, không phải billing cap; không suy ra smoke/config là pipeline RAG đã triển khai.

Mọi thay đổi runtime/dependencies/hạ tầng phải nằm trong phạm vi người dùng đã xác nhận. Ghi ADR theo hướng dẫn ở docs/decisions khi triển khai quyết định, và giải thích trong KNOWLEDGE.

## Stack và conventions

- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, Ruff. Frontend: React + TypeScript + Vite + Tailwind, ESLint/Prettier. Pin runtime/dependencies khi khôi phục môi trường; không nâng version hàng loạt trong bước tài liệu.
- Cấu trúc đích theo spec mục 16; router chỉ xử lý HTTP/auth/schema, nghiệp vụ trong domain services, model qua adapters. Tree là đích, không yêu cầu move toàn code cũ một lần.
- Tên code, field, API bằng tiếng Anh; nội dung UI và prompt bằng tiếng Việt.
- Timestamps lưu UTC (`timestamptz`); hiển thị theo `Asia/Ho_Chi_Minh`.
- File upload lưu theo UUID/storage key, không dùng tên file của người dùng làm đường dẫn.
- Runtime từ Bước 04 và frontend apiFetch đã đồng bộ JSON success `{data,request_id}`, failure `{error:{code,message,details},request_id}`. Server sinh X-Request-ID, no-store; binary source theo contract vẫn thuộc bước parser/source API sau.
- Mọi thay đổi schema đi qua migration Alembic; không dùng `create_all()` ngoài test.
- Config đích theo spec 17: DATABASE_URL, QDRANT_URL, FILE_STORAGE_DIR, embedding fingerprint, LLM/prompt/budget, job limits/auth. Thêm biến phải cập nhật .env.example; không giả định Settings cũ đã đọc các biến mới.
- AuthToken chỉ lưu digest token, role/is_active đọc lại mỗi request. Write-document/job APIs đã yêu cầu admin; scope lookup trước status, admin không bypass session owner. Seed CLI idempotent, không reset hash/role khi chạy lại; private credentials ở DEMO_ADMIN_PASSWORD/DEMO_MEMBER_PASSWORD.
- Nội dung do AI tạo hiển thị trên UI phải có nhãn "AI-generated".

## Test

- Mỗi tính năng có test cho cả trường hợp thành công và thất bại; chạy test và báo kết quả thật trước khi coi là xong.
- Test DB chạy trên **PostgreSQL thật** (không SQLite) vì cần row locking và partial unique index.
- Integration retrieval dùng Qdrant thật; unit test model dùng fake/stub có nhãn, real-model eval tách trong eval/.
- Nghiệm thu M1: **AT-R01–23** (spec 15.4); P1 tương ứng AT-R24–26. Số test hiện tại (20/11/2026, `main`): 418 backend, 79 frontend; eval tooling (cần `PYTHONPATH=backend`) gần nhất 464 trên nhánh `feat/01-eval-v2` (18/11). Software tests không thay browser E2E hoặc human-quality/held-out acceptance.
- `test_worker.py::test_heartbeat_runs_during_inference_without_document_lock` có thể chập chờn khi máy bận (đã ghi trong roadmap 00-T1); chạy lại riêng trước khi kết luận là lỗi thật.
- Trước pytest, xác minh TEST_DATABASE_URL là DB test riêng trên endpoint được phép, khác DB development. Fixture hiện có tự tạo/migrate DB; không chạy với URL chưa kiểm tra.
- Baseline bị chặn thì ghi đúng nguyên nhân và command, không coi kiểm tra chưa chạy là pass. Report raw outputs/config đủ tái lập theo spec 14 và eval/README.md.

## Lệnh

Các command chỉ dùng trong đợt được duyệt. Dùng interpreter `backend/.venv/Scripts/python.exe` tường minh và `npm.cmd`, không cần Activate.ps1 hay đổi execution policy. Máy nhận dùng cache `<repo>/.cache/` trên ổ C theo runbook 05/11; kiểm tra venv/cache/services thực tế trước chạy, không suy ra chúng tồn tại chỉ từ reports lịch sử.

```powershell
# Từ backend/, sau khi dependencies và DB test được xác minh:
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\ruff.exe check --no-cache .
.\.venv\Scripts\ruff.exe format --check --no-cache .
# Từ frontend/, sau khi dependencies được cài:
npm.cmd run lint
npm.cmd run build
npm.cmd run test
# Chỉ đọc trạng thái services hiện cấu hình, từ root:
docker compose ps --all
```

Lưu ý:
- `backend/alembic.ini` chỉ được chứa ký tự ASCII (Alembic đọc file theo encoding của hệ điều hành trên Windows).
- Dependency (`DbSession`) dùng `Annotated`, không dùng `Depends()` làm default argument (ruff B008).
- Migration head trong source là `20261118_folders`, sau `20261103_rag04` (RAG), trước đó là `27b126c3c0bc` (Operations). Kiểm tra head DB thực tế rồi migrate; không sửa revision đã áp dụng, drop dữ liệu legacy hoặc tự chấp nhận autogenerate DROP TABLE. Đọc mapping trong audit.
- Backend dev dùng requirements-dev.lock (include runtime lock); API/worker local E5 cần thêm requirements-worker-cpu.lock trên Windows x64/Python 3.12. Frontend dùng package-lock.json và npm ci. Không install [stt]; tải weights hoặc gọi LLM phải thuộc đợt đã được duyệt.

## Bảo mật và dữ liệu

- Không commit .env, API key, model weights hay tài liệu riêng tư; dùng corpus giả lập/được phép. Hosted provider phải phù hợp quyền xử lý dữ liệu.
- Không log secrets/full document/context mặc định; trace gồm IDs, config an toàn, timings và errors. Nếu debug lưu text thì cleanup/retention phải bao phủ bản sao đó.

## Cách làm việc

- Thay đổi nhỏ, có phạm vi rõ; không refactor ngoài phạm vi được yêu cầu.
- Không mock kết quả rồi mô tả là đã chạy thật. Nếu bỏ qua bước nào (test, migration…), nói rõ.
- README chỉ mô tả những gì thực sự chạy được và các con số đã đo; phần chưa làm ghi vào *Roadmap*, giới hạn ghi vào *Known limitations*.
- Code phải đủ rõ để thành viên nhóm giải thích được khi phỏng vấn; ưu tiên code đơn giản, dễ đọc hơn abstraction.
