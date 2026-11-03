# Bước 04 — Schema RAG, migration và identity

**Ngày:** 03/11/2026.<br>
**Trạng thái:** hoàn thành nền schema/seed/auth/scope của Bước 04 trên PostgreSQL thật. **Tiến độ 24,9% / 100%**. Bước 05 chưa bắt đầu. Đây chưa phải pipeline RAG hoàn chỉnh hoặc full AT-R09/19/23.

## Kết quả sử dụng được

- Migration mới `20261103_rag04` nối sau `27b126c3c0bc`, đã upgrade cả DB test và DB development local. Dev trước đợt này không có bảng; test ở revision legacy với users/jobs trống.
- Có 21 bảng domain (gồm legacy + RAG), thêm `alembic_version` thành 22 public tables. Giữ nguyên workspaces/users/projects/meetings/proposals/tasks cũ, không drop hoặc đổi ID/data legacy.
- Seed một workspace demo và hai user `demo.admin` / `demo.member`. Mật khẩu ngẫu nhiên khác nhau, **24 ký tự**, nằm riêng ở `.env`: `DEMO_ADMIN_PASSWORD`, `DEMO_MEMBER_PASSWORD`. Không ghi giá trị vào repo/log/report.
- Login/me đã probe bằng ASGI TestClient với DB development thật; repeat seed tạo 0 users, không đổi mật khẩu. Hai token probe đã được revoke sau kiểm tra, không giữ bearer token hoạt động từ lượt xác minh.
- Bearer auth, scope lookups và JSON envelope đã nối vào app; frontend apiFetch unwrap data/đọc nested error. UI đăng nhập/upload/chat chưa triển khai.

## Schema và quyết định chuyển tiếp

| Thành phần | Thực hiện |
|---|---|
| Identity | Thêm username lowercase ASCII unique, is_active, knowledge_admin vào role CHECK; giữ email và hai role legacy |
| Legacy users | Backfill `legacy_<UUID hex>`; is_active=false cho rows có sẵn, không tự nâng quyền. Users tạo mới default active |
| Auth tokens | UUID/user/hash SHA-256 unique/expiry UTC/revocation; không lưu bearer plaintext |
| Documents/revisions | Live-hash uniqueness, lifecycle/status/size/hash checks, composite FK active revision thuộc document |
| Sources/chunks | Revision/generation/index uniqueness, point UUID unique, JSONB locations/spans, text/count/hash checks |
| Jobs | Mở rộng processing_jobs theo discriminator document_id/kind; legacy jobs giữ trạng thái processing. RAG chỉ nhận 6 statuses mới và phải khớp entity_id/document_id |
| Leases | Running RAG job cần lease token/expiry/generation; ingest/cleanup mỗi loại chỉ có một job active/document |
| Chat | Owner-bound sessions; query idempotency/session-running unique; run/session FK; một message mỗi role/run |
| Citations/eval | Evidence ID unique/message, revision/document FK, chunk ON DELETE SET NULL giữ history; eval metadata |

Constraints này bảo vệ dữ liệu ở SQL; chưa chứng minh worker locking/restart/retry/publish hay vector consistency. Active generation cần service xác minh nguồn thuộc revision và đủ index ở các bước sau. Không dùng JSON spans thay kiểm tra parser offsets thật.

Alembic autogenerate được review: phải bổ sung CHECK cho enum VARCHAR trên bảng cũ, thêm users composite unique trước khi tạo FK mới, backfill trước NOT NULL và tạo active-revision FK sau khi hai bảng tồn tại. Downgrade từ chối nếu có RAG data/admin để tránh xóa nhầm. Test roundtrip chỉ thực hiện trên schema tạm trong DB test, toàn transaction rollback.

Migration cũ giữ nguyên SHA-256:

```text
e504de8252dc856e8bf3e935da4fdcd78ab8e45468d604931da6526dc60ba868
```

Migration mới SHA-256 `84e73268f5603508c3697352e593ebd518f6ca8f15ea65261c1561e6d1fbdbb5`. Snapshot sau kiểm chứng: dev có 2 users, 0 documents, 2 token probe đã revoke; test có 0 users/documents/tokens sau rollback, cả hai head `20261103_rag04`. Không báo test fixture rollback là đã rollback migration dev.

## API hiện có trong phạm vi bước này

Base `/api/v1`. Success `{data,request_id}`; errors `{error:{code,message,details},request_id}`. X-Request-ID do server sinh; cache no-store. Validation/DB/unexpected errors không trả hoặc log request inputs, credentials hay SQL parameters.

| Method/path | Hành vi đã có |
|---|---|
| GET /health | SELECT 1 và envelope mới |
| POST /auth/login | JSON username/password, token_type bearer, expires_in; sai/inactive/legacy role trả 401 chung |
| GET /auth/me | Identity/role/workspace từ DB, không có hash/token |
| GET /documents | List giới hạn 1–100, filter workspace backend |
| GET /documents/{id} | Metadata được scope trước; missing/foreign 404, own deleting/deleted 410 |
| GET /jobs/{id} | Chỉ RAG jobs thuộc document cùng workspace; không lộ legacy/foreign jobs hoặc error_message/path |
| POST/GET /chat/sessions | Tạo/list phiên của chính user; body không nhận owner/workspace/role |
| GET /chat/sessions/{id}/messages | Owner-only kể cả admin; kiểm tra SQL nguồn/revision/generation/chunk/citation status trước trả content |
| GET /chat/runs/{id} | Owner-only status/error, không trả trace/context/config nội bộ |

`AdminUser` dependency đã qua kiểm thử HTTP trên route test riêng: member 403, admin được phép, thiếu login 401. Upload/delete/retry **chưa có endpoint nghiệp vụ** ở bước này; không tạo stub trả 202 hoặc gọi đó là full AT-R09. Chúng phải dùng dependency này khi triển khai bước 05/06/09. Document/source APIs ở đây là foundation; chưa có content/chunks/upload/pagination cursor hoàn chỉnh của release M1.

Source-history read guard có tests cho deleting source, chunk đã xóa, mismatch generation, failed revision và citation unavailable; không chờ cờ source_unavailable được worker cập nhật mới che content. Cleanup snapshots/traces, worker race và delete API vẫn thuộc Bước 09, chưa nghiệm thu AT-R18 hoàn chỉnh.

## Auth và config

Password hash **Argon2id**, time_cost 2, memory_cost 19.456 KiB, parallelism 1, random salts. Token là 32 random bytes dạng URL-safe (43 ký tự), DB chỉ giữ SHA-256; expiry mặc định **3.600 giây**, config 60–86.400. Current role/is_active được đọc lại mỗi request, token hết hạn/revoked/inactive/role legacy không hợp lệ → 401, WWW-Authenticate Bearer. Không refresh token/SSO/registration/reset-password trong P0.

Chọn opaque token vì một backend/PostgreSQL demo dễ revoke và phản ánh thay đổi quyền ngay; đổi lại có DB lookup mỗi request. Chưa cần JWT signing keys/rotation. Đây là auth demo, chưa gồm các điều kiện public như HTTPS/login rate limiting. Xem [ADR RAG-06](decisions/0006-identity-and-rag-schema.md) và KNOWLEDGE K-037–K-042.

Thêm argon2-cffi 25.1.0, bindings 26.1.0, cffi 2.1.1, pycparser 3.12 vào runtime lock. Settings kiểm tra PostgreSQL/psycopg URL và TTL; API key/seed passwords dùng SecretStr, database URL không được log. Thêm connect_timeout 5 cho engine/migration để không chờ vô hạn khi không kết nối được; nhiều địa chỉ/attempts có thể kéo dài hơn 5 giây tổng. Không dùng timeout như bằng chứng DB ready.

## Commands và kiểm chứng

Từ backend, trong đợt thực thi được xác nhận:

```powershell
.\.venv\Scripts\python.exe -B -m alembic upgrade head
.\.venv\Scripts\python.exe -B -m app.seed
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --reload
```

Swagger khi bạn chạy server: http://localhost:8000/docs. Dùng username demo.admin/demo.member và mật khẩu tương ứng trong .env. API/frontend servers không được giữ chạy sau lượt này; probe dùng ASGI client trong process. PostgreSQL đã được khởi động lại với volume cũ; Qdrant không cần cho bước schema/auth và không được kiểm tra readiness ở đợt này.

| Check | Kết quả |
|---|---|
| Full backend | **124 passed, 1 warning** — guard + legacy + schema/auth/migration tests |
| Eval regression | **72 passed**, không gọi model |
| Alembic check trên DB test | No new upgrade operations detected |
| Dev upgrade/seed/login/me | Đạt, seed lần hai 0 users; token probe revoked |
| Frontend lint/build | Đạt, TypeScript/Vite 44 modules; build chạy ngoài sandbox theo lỗi quyền máy đã biết |
| Ruff check/format, pip check | Đạt |

Hai suites được chạy riêng, không trình bày như một lệnh full suite. Backend còn Starlette TestClient/httpx deprecation warning đã có từ baseline, chưa đổi test transport/dependencies để che warning. Test schema legacy có dữ liệu giữ role/password_hash/job status và thử downgrade guard; test SQL thực chứng minh partial unique/composite FK, không dùng SQLite hay mock SQL để báo DB pass.

Không gọi Gemini, không tải model mới, không phát sinh API calls trong Bước 04. Không commit/push. Bước 05 tiếp theo là upload/parser/chunker với source mapping; trước đó cần xác nhận đợt riêng.
