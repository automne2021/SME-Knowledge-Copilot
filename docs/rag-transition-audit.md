# Bước 00 — Audit chuyển repository sang RAG

> **Ngày:** 02/11/2026  
> **Nguồn yêu cầu:** [Spec RAG v2.1](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN bước 00](../PLAN.md#bước-00--chốt-phạm-vi-và-chuẩn-bị-chuyển-hướng)  
> **Trạng thái:** hoàn thành audit và đồng bộ tài liệu; kiểm thử runtime bị giới hạn bởi môi trường hiện có.  
> **Phạm vi được xác nhận:** tài liệu, mapping/backlog, kiểm tra nền với dependencies sẵn có; chưa triển khai code, migration hay hạ tầng RAG.

**Trạng thái mới sau baseline này:** Bước 01 đã khôi phục môi trường và kiểm chứng PostgreSQL/Qdrant cùng 64 tests pass. Xem [environment-step01.md](environment-step01.md). Những kết quả bị chặn bên dưới là lịch sử Bước 00, không phải lỗi môi trường vẫn còn ở thời điểm kết thúc Bước 01.

## 1. Mốc code và cách đọc kết quả

HEAD trước thay đổi Bước 00: `53879bfa96f082489cf74a1c0dc4c41acebc493f`.

Working tree đầu phiên đã có `CLAUDE.md` modified và `AGENTS.md`, `KNOWLEDGE.md` untracked. Những thay đổi đó là quy tắc học tập/xác nhận của người dùng và được giữ lại. Spec RAG/PLAN đã có trong repository ở thời điểm audit. Không tạo commit/tag/branch trong bước này; HEAD chỉ là mốc tham chiếu, không phải snapshot đầy đủ của các file chưa commit.

Đây là kiểm tra source và công cụ tại workspace hiện tại, không phải báo cáo rằng schema trong một DB đang chạy đã được introspect. Chưa có bằng chứng model inference hay RAG end-to-end chạy được.

## 2. Phạm vi đã chốt

**P0/M1:** tài khoản seed và quyền workspace/session, upload PDF text/DOCX/TXT/MD, parsing có provenance, chunking, embedding/indexing qua worker durable, dense search-only, grounded Q&A/citations/abstention, source viewer, delete/cleanup, observability và benchmark tái lập. Mục tiêu trình bày 15/11/2026 theo PLAN; không đồng nghĩa các tính năng đã có.

**P1/M2:** reindex/update revision, hybrid/reranker, filter metadata nâng cao, follow-up retrieval-aware, structured comparison, inspector/eval UI và judge bổ sung.

**Không thuộc luồng RAG:** audio/STT, meeting intelligence, agent tool loop, proposal/approval/task và tích hợp nghiệp vụ ngoài. Các bảng/test cũ được giữ làm lịch sử và baseline trước migration; không dùng chúng làm tiêu chí hoàn thành RAG.

## 3. Audit module và hướng tái sử dụng

| Source đã đọc | Hiện trạng thực tế | Hướng xử lý trong bước triển khai sau |
|---|---|---|
| `backend/app/main.py`, `api/router.py`, `api/health.py` | FastAPI + request ID + route `/api/v1/health`; title còn Operations; health hiện truy vấn DB | Tái sử dụng bootstrapping/request ID; bổ sung auth/RAG routes; tách liveness/readiness theo spec |
| `core/db.py`, `models/base.py` | SQLAlchemy sessions, UUID/timestamps, naming convention | Tái sử dụng; bổ sung transaction/locking theo service, không giữ lock khi inference |
| `core/errors.py`, `frontend/src/api/client.ts` | Lỗi phẳng `{code,message,request_id}` | Đổi backend/client/tests cùng một thay đổi contract sang envelope RAG; không sửa riêng một phía |
| `core/config.py`, `.env.example` | Storage/upload 25 MB/STT config; embedding/Qdrant/auth config chưa có đầy đủ | Bổ sung/validate config ở bước tương ứng; spec RAG khởi đầu 20 MiB, không coi config cũ là contract mới |
| `api/`, `services/`, `ai/`, `workers/` | Router chỉ include health; các thư mục nghiệp vụ còn skeleton | Chưa có auth service, worker loop, parser, embedding hay generation adapter để tái sử dụng như tính năng hoàn chỉnh |
| `backend/pyproject.toml`, `requirements.lock` | Backend dependency set cũ, optional STT còn tồn tại | Giữ baseline; thêm parser/vector/model/auth dependencies sau khi được duyệt, cập nhật lockfile tương ứng |
| `compose.yaml` | Chỉ cấu hình db + backend; image pgvector hiện dùng như PostgreSQL | Có thể giữ DB image để tránh đổi hạ tầng không cần thiết; không coi image này là quyết định chuyển RAG sang pgvector |
| `backend/Dockerfile` | Python 3.12-slim, startup migrate rồi uvicorn | Review ở bước đóng gói; đích RAG tách migration trước API/worker, không cùng tự migrate |
| `frontend/src/App.tsx` và pages | Navigation Operations và placeholder, chưa có RAG UI | Tái sử dụng SPA/router/styles, thay screens theo PLAN bước 10 |
| Frontend toolchain | React/TypeScript/Vite; chưa thấy package lock hoặc node_modules ở frontend | Cài và tạo lockfile ở bước môi trường được duyệt; không mô tả build đã tái lập |
| `backend/tests/` | 8 test functions: 2 API basics, 6 schema constraints Operations | Giữ regression legacy tới khi migration được thiết kế; thêm tests RAG riêng, không đổi nhãn các test này thành AT-Rxx |

### Schema/enum mapping

Migration duy nhất tìm thấy: `backend/alembic/versions/2026_10_29_1738-27b126c3c0bc_initial_m1_schema.py`, revision `27b126c3c0bc`, không có predecessor. SHA-256 trước thay đổi:

```text
e504de8252dc856e8bf3e935da4fdcd78ab8e45468d604931da6526dc60ba868
```

| Entity cũ | Tình trạng trong RAG đích | Migration/reuse cần chuẩn bị |
|---|---|---|
| `workspaces` | Giữ identity/scope | Tái sử dụng ID và name; xác minh dữ liệu thật trước backfill |
| `users` | Tái sử dụng có thay đổi | Hiện có email/password_hash/role, chưa có username/is_active theo spec; cần bổ sung và backfill có kiểm tra, giữ email nếu chưa có lý do xóa |
| `projects`, `project_members` | Legacy, không phải scope P0 mới | Giữ nguyên; không tự coi membership project tương đương quyền toàn workspace |
| `processing_jobs` | Cần nâng cấp đáng kể | Hiện là entity_type/entity_id/status/attempts/locked_at/error, entity_id không có FK tới document; RAG cần document/revision/kind/stage/lease/generation/retry/manifest và active-job constraints |
| `meetings`, `transcript_segments`, `action_items` | Legacy ngoài phạm vi | Không dùng làm nguồn ingestion hay dependency bắt buộc của RAG; chưa drop |
| `task_proposals`, `tasks` | Legacy ngoài phạm vi | Giữ FKs/unique constraints và tests cũ; không gọi approval service từ RAG |
| `audit_events` | Legacy, schema gắn project | Không mặc định dùng được cho workspace-level RAG trace; P0 dùng query/job trace đã đặc tả |
| `documents`, `document_revisions` | Chưa có | Thêm identity, lifecycle, source file, active revision/generation và config manifest |
| `source_blocks`, `chunks` | Chưa có | Thêm raw/normalized text, source spans, generation, token count, point ID uniqueness |
| `chat_sessions`, `query_runs`, `chat_messages`, `answer_citations` | Chưa có | Thêm ownership, idempotency, concurrency, structured answer/citations và deletion policy |
| `eval_runs` | Chưa có | Thêm metadata theo spec; benchmark M1 chạy CLI, không bắt buộc có eval HTTP/UI |

| Enum cũ trong source | Contract đích / lưu ý |
|---|---|
| `UserRole`: member/approver/demo_admin | RAG dùng member/knowledge_admin. Không tự nâng quyền approver; mapping/backfill user cũ phải được review khi migration, seed RAG được chỉ định rõ |
| `JobStatus`: queued/processing/completed/failed | RAG job dùng queued/running/retry_wait/completed/failed/cancelled; `stage` riêng. Không chỉ đổi text `processing` khi chưa xét job cũ |
| ProposalStatus/ProposalOrigin/TaskStatus | Giữ như legacy; không dùng chung cho document/job/query states |
| Document/revision/query states | Thêm riêng theo spec 7.4 và 8.8; không tái sử dụng một enum status cho mọi entity |

Helper `str_enum()` hiện dùng `VARCHAR + CHECK` (`native_enum=False`), không phải PostgreSQL native ENUM. Migration thay giá trị phải xử lý CHECK constraint và dữ liệu đang có; không áp hướng dẫn ALTER TYPE cho native ENUM một cách máy móc.

`tasks.proposal_id` có FK/NOT NULL/UNIQUE chỉ ràng buộc liên kết và số lượng. Nó không tự chứng minh proposal đã được duyệt hay approval service đã triển khai. Đây là ví dụ cần đọc hành vi/constraints thật thay vì tin comment hoặc tên bảng.

### Thứ tự migration dự kiến — chưa tạo/chạy

1. Kiểm tra dữ liệu legacy và policy mapping user/role/job; chuẩn bị backup/restore cho môi trường có dữ liệu cần giữ.
2. Revision mới sau `27b126c3c0bc`: mở rộng identity và tạo documents/revisions; FK active revision vòng ngược được thêm sau khi hai bảng đã tồn tại.
3. Thêm source blocks/chunks, các CHECK/unique/FK/index RAG; point ID/generation phải đồng bộ với vector manifest.
4. Mở rộng job schema và backfill legacy có chủ đích; xác minh job cũ trước áp FK/NOT NULL/partial unique mới. Không giả định bảng job trống.
5. Thêm sessions/query/messages/citations/eval metadata theo thứ tự FK; dùng tombstone và nullable chunk reference đúng deletion contract.
6. Review migration sinh ra, kiểm tra upgrade trên PostgreSQL test thật và regression trước triển khai DB dev.

Đây là thứ tự kỹ thuật để chuẩn bị bước 04–06, không phải phê duyệt chạy migration. Không sửa revision đã áp dụng hoặc bỏ model legacy khỏi Alembic metadata rồi chấp nhận autogenerate DROP TABLE ngoài ý muốn.

## 4. Backlog P0 và traceability

Mọi dòng dưới là **chưa triển khai/kiểm chứng cho RAG** ở Bước 00. Các FR P1 được để trong spec/PLAN M2, không đưa vào completion checklist M1.

| Backlog | FR P0 được bao phủ | PLAN | Acceptance liên quan |
|---|---|---|---|
| B01 — Seed auth, role, scope, session ownership | FR-29; phần scope FR-11/19/20 | 04 | AT-R09/23 |
| B02 — Upload, validation, dedup và document list/status | FR-01/02/06 | 04–05 | AT-R01–05 |
| B03 — Parsing/location/source spans/chunking | FR-03/04 | 05 | AT-R01–04 |
| B04 — Embedding, index manifest và publish hoàn chỉnh | FR-05 | 03/06 | AT-R06–08/15 |
| B05 — Worker lease/recovery và retry | FR-30/31 | 06/09 | AT-R06–08/17 |
| B06 — Dense search, document/workspace filter, search-only API | FR-10/11/12 | 07 | AT-R09/10/15 |
| B07 — Context/answer schema, citation validation, abstention | FR-16/17/18 | 08 | AT-R11–15/20 |
| B08 — Chat history, idempotency, source endpoints/viewer | FR-19/20 | 08/10 | AT-R18–20/23 |
| B09 — Delete, physical cleanup, historical answer redaction | FR-07/32 | 09 | AT-R16–18 |
| B10 — Corpus/gold, metrics và reproducible reports | FR-23/24/25 | 02/07/11 | AT-R21/22 |
| B11 — Structured logs, safe errors và stage timing | FR-26 | 04–11 | AT-R06/08/13/15/22 |
| B12 — UI E2E, Compose, fresh setup và demo | P0 UI/deployment; NFR-08/09 | 10–12 | AT-R23 + E2E P0 |

Danh sách FR P0 đầy đủ: **01–07, 10–12, 16–20, 23–26, 29–32** (23 yêu cầu). FR-08/09/13–15/21/22/27/28 là P1. AT-R01–23 là bộ nghiệm thu M1; AT-R24–26 thuộc M2.

NFR-01–12 là yêu cầu xuyên suốt: ready/delete correctness, retry reliability, isolation, upload security, citation integrity, observability, reproducibility, UI, deployability, latency, resource và privacy. Mỗi feature phải giữ các bất biến spec 5.5; không đợi bước UI mới kiểm tra quyền/xóa nguồn.

## 5. Baseline thực chạy ngày 02/11/2026

### Công cụ và kết quả

| Kiểm tra | Lệnh / điều kiện | Kết quả quan sát |
|---|---|---|
| System Python | `python --version` | Python 3.12.8 |
| Project Python | Từ backend: `.\.venv\Scripts\python.exe --version` | **Blocked**, launcher không tìm thấy Python base ở đường dẫn máy cũ |
| Backend lint | Từ backend: `.\.venv\Scripts\ruff.exe check --no-cache .` | **PASS**, All checks passed; Ruff 0.17.3 |
| Backend format | Từ backend: `.\.venv\Scripts\ruff.exe format --check --no-cache .` | **PASS**, 26 files already formatted |
| Pytest baseline | Wrapper dùng project interpreter, kiểm tra endpoint local và DB test riêng trước `pytest.main(...)` | **Chưa khởi chạy Python/pytest** do broken venv; 0 test được thực thi, không phải pytest pass/fail hay skipped do pytest |
| Node/npm | `node --version`, `npm.cmd --version` | Node v24.11.1, npm 11.6.2; chưa kết luận tương thích build |
| Frontend lint | Từ frontend: `npm.cmd run lint` | **Blocked**, exit 1, thiếu executable eslint |
| Frontend build | Từ frontend: `npm.cmd run build` | **Blocked**, exit 1, thiếu executable tsc; chưa tới Vite |
| Docker | Từ root: `docker compose ps --all --format json`, chạy lại ngoài sandbox | Exit 0, không có dòng container Compose của project; không start/pull service |
| TCP DB host | Kết nối chỉ đọc `127.0.0.1:5433`, chạy lại ngoài sandbox | ConnectionRefusedError; không xác thực/truy vấn PostgreSQL |

Lần gọi Docker trong sandbox ban đầu bị hạn chế config/pipe. Lần kiểm tra ngoài sandbox là căn cứ phân biệt với lỗi quyền ban đầu. TCP probe sandbox timeout không được dùng để khẳng định server down; probe ngoài sandbox mới xác nhận cổng local đang từ chối kết nối.

### Vì sao chưa chạy được pytest/frontend

- `backend/.venv/pyvenv.cfg` ghi base interpreter Python 3.13 ở `C:\Users\Username\...`, không tồn tại trên máy hiện tại. System Python 3.12.8 có pytest nhưng thiếu FastAPI/SQLAlchemy/Alembic/psycopg/pydantic-settings. Không trộn site-packages của hai interpreter để ép tests chạy.
- Frontend không có node_modules và package lock tại thời điểm đọc. Scripts gọi eslint/tsc nên thất bại trước khi phân tích source; chưa có lỗi lint/type của app được chứng minh.
- PostgreSQL host port 5433 chưa phục vụ. Không tự khởi động DB trong Bước 00 vì đó là setup Bước 01, ngoài phạm vi đã duyệt.

Wrapper pytest ban đầu đã dự kiến dùng DB riêng `copilot_step00_test`, kiểm tra khác DB development và chỉ dùng endpoint local; launcher lỗi trước khi script chạy nên **không DB nào được tạo hoặc migrate**, không chạy collection/test case. Ở thời điểm baseline, fixture chưa có guard nội bộ; đợt hậu kiểm ở mục 7 đã bổ sung guard. Vẫn cần xác nhận môi trường/DB test đúng trước khi chạy integration.

### Giải quyết trong Bước 01 sau khi được xác nhận

1. Tạo lại virtualenv đúng Python tại máy này và cài dependencies theo manifest/lock có kiểm tra; xử lý dung lượng cache trước, giữ nguyên env cũ tới khi phương án thay thế được duyệt.
2. Cài frontend dependencies, tạo/review lockfile và chạy lại lint/build.
3. Start DB, xác minh endpoint/DB test an toàn, chạy pytest baseline và bổ sung kết quả mới vào audit; không ghi đè quan sát Bước 00.
4. Thêm Qdrant/config/healthchecks theo PLAN 01. Chỉ sau đó mới làm corpus/model smoke.

Các blockers trên tồn tại trước thay đổi tài liệu. Không có kết quả benchmark hoặc bằng chứng chất lượng RAG từ các checks này.

### Kiểm chứng thay đổi tài liệu

Đã kiểm tra 8 file Markdown trong phạm vi: UTF-8, code fences, số cột bảng, local links và anchors hợp lệ; KNOWLEDGE có K-001–K-014 không trùng; danh sách P0 khớp 23 FR trong spec. AST source xác nhận 8 test functions legacy (không chạy chúng). Migration checksum và HEAD khớp mốc trước thay đổi; source/runtime/config/dependencies không nằm trong diff Bước 00. `git diff --check` được kiểm tra riêng sau chỉnh định dạng metadata PLAN.

## 6. Checklist kết thúc Bước 00

- [x] Xác định spec RAG là contract hiện hành; spec Operations là lịch sử.
- [x] Đồng bộ CLAUDE/AGENTS/README/eval/ADR instructions, giữ quy tắc xác nhận và KNOWLEDGE.
- [x] Lập backlog bao phủ đủ 23 FR P0 và mapping schema/enum/migration từ source thật.
- [x] Ghi HEAD, trạng thái working tree ban đầu và checksum migration; không tạo commit ngoài yêu cầu.
- [x] Thử baseline bằng dependencies hiện có, phân loại PASS/blocked và chứng cứ môi trường.
- [x] Ghi bài học/kết quả vào KNOWLEDGE và trạng thái trong PLAN.
- [ ] Chạy pytest thành công — phụ thuộc khôi phục môi trường ở Bước 01.
- [ ] Chạy frontend lint/build thành công — phụ thuộc cài dependencies ở Bước 01.

**Kết luận phạm vi:** Bước 00 hoàn thành ở mức audit/đồng bộ và ghi baseline có giới hạn. Runtime giữ skeleton cũ; chưa có migration hay feature RAG mới. Bước 01 là đợt thay đổi riêng cần người dùng nói “Thực hiện đi” sau khi phạm vi được trình bày.

## 7. Hậu kiểm — vá guard DB test ngày 02/11/2026

Phạm vi được người dùng xác nhận riêng: vá fixture DB, thêm unit tests cho guard và cập nhật spec/audit/PLAN/KNOWLEDGE. Đây là phần bổ sung sau Bước 00, không thay số liệu baseline lịch sử ở mục 5 và không phải thực hiện setup Bước 01.

### Vấn đề và thay đổi

- Trước bản vá, fixture tự tạo/migrate DB từ TEST_DATABASE_URL mà không so với DB development; cấu hình nhầm có thể tác động dữ liệu ngoài ý muốn. Tên DB còn được nội suy vào DDL string.
- Thêm [tests/database_safety.py](../backend/tests/database_safety.py): chỉ nhận driver `postgresql+psycopg`, host `localhost`/`127.0.0.1`/`::1`/`db`, tên `[a-z][a-z0-9_]*_test` tối đa 63 ký tự và khác tên development (so case-insensitive, kể cả host alias khác).
- Test/development URLs phải có user/host/database rõ ràng, port hợp lệ; không raw whitespace, query parameters hoặc fragment. Không cho query `dbname`, `host`, `service`, `options` đổi đích sau validation. Credentials dùng URL encoding khi có ký tự đặc biệt; error không echo URL/password.
- URL cho SQLAlchemy được dựng lại từ các thành phần đã validate, port mặc định được pin 5432 thay vì dựa vào fallback môi trường. CREATE DATABASE dùng `psycopg.sql.Identifier` trên kết nối AUTOCOMMIT; admin/final engine được dispose trong finally.
- [conftest.py](../backend/tests/conftest.py) validate trước gọi tạo DB, revalidate ở cả `_ensure_database` và `_migrate`; imports app/DB chuyển vào fixture cần dùng. Unit guard tests vì vậy collect/run bằng system Python không có app dependencies.
- Spec đã bỏ câu trạng thái CLAUDE còn theo Operations; hướng dẫn test safety và trạng thái chuyển tiếp được cập nhật. Chưa đổi business rules RAG hoặc schema migration.

### Kết quả kiểm chứng mới

Chạy từ backend bằng dependencies sẵn có:

```powershell
python -B -m pytest tests/test_database_safety.py -q -p no:cacheprovider
.\.venv\Scripts\ruff.exe check --no-cache .
.\.venv\Scripts\ruff.exe format --check --no-cache .
```

| Kiểm tra | Kết quả |
|---|---|
| Unit guard | **56 passed**, system Python 3.12.8 + pytest 9.0.2, không kết nối DB |
| Backend lint | **PASS**, Ruff 0.17.3 |
| Backend format | **PASS**, 28 files already formatted |
| Legacy DB/API integration | **Chưa chạy**: project venv/app dependencies/DB chưa khôi phục |
| SQL CREATE DATABASE/Alembic trên DB thật | **Chưa chạy**: cần kiểm chứng với psycopg/SQLAlchemy/PostgreSQL ở Bước 01 |

56 cases bao gồm valid local targets/default port, invalid/same DB, host alias/case, reserved/unsafe/overlong names, port/driver lỗi, query override, encoded credentials và chặn các entry points trước thao tác tạo/migrate. Fixture test dùng Mock cho settings/operation tripwires; không giả lập một lần SQL execution thành integration pass.

### Giới hạn và bước tiếp

Guard là policy cố ý hạn chế cho local demo; không hỗ trợ remote test database hoặc query-string connection options trong đợt này. Alias `db` giả định thuộc mạng Compose do nhóm quản lý; không phải chứng minh DNS/port forwarding không thể trỏ nơi khác. Nó không thay thế DB user ít quyền hoặc việc kiểm tra environment thật trước integration.

Chưa cài dependencies, sửa venv, tạo lockfile, start DB/Qdrant hay tạo/migrate database. Bước 01 cần xử lý môi trường/lockfiles và chạy lại 8 test functions legacy cùng kiểm chứng đường CREATE/migrate thành công. Kiến thức/lý do/thay thế: KNOWLEDGE K-015–K-016.
