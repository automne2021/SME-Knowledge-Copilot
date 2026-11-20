# Kiểm kê schema và code còn sót từ hướng Operations (00-T3)

> **Ngày:** 20/11/2026 · **Nhánh:** `feat/00-t2-t3`, từ `main` sau `7113e2c` · **Migration head:** `20261118_folders`.
> Báo cáo chỉ đọc: không sửa code, không chạy migration, không xóa dữ liệu. Việc xóa là một đợt riêng do người dùng quyết.

## Cách kiểm

- Đọc `backend/app/models/*`, `app/core/config.py`, `app/core/security.py`, `app/seed.py`, `pyproject.toml`, ba file migration và các test.
- Tìm nơi dùng từng model bằng `grep` trong `backend/app`, `backend/tests`, `backend/alembic`, `eval/`, `frontend/src`.
- Đếm dòng trên DB development `copilot` trong một transaction `READ ONLY`, qua `docker compose exec db psql`.
- Không kiểm DB test `copilot_test` (fixture tạo lại mỗi lần chạy) và không kiểm `release/m1`.
- Chính sách hiện hành: [audit Bước 00](rag-transition-audit.md) mục mapping (giữ legacy, chưa drop) và spec mục 18.3.

## Kết quả tóm tắt

- **Router, service, schema API, frontend: không còn gì thuộc Operations.** Cả 8 router và 23 module service đều là RAG.
- **8 bảng legacy vẫn còn trong DB, đều 0 dòng** trên DB development. Không code runtime nào import model của chúng; chỉ `models/__init__.py` (để Alembic không autogenerate DROP) và `tests/test_schema_constraints.py` dùng.
- **Phần lai:** `processing_jobs`, `users` và enum `UserRole` vẫn mang cột, trạng thái và giá trị cũ để tương thích migration.
- **Code chết nhỏ:** hai package placeholder mô tả kiến trúc cũ, biến `stt_model` và extra `[stt]`.

## Bảng kiểm kê

### Bảng và model legacy hoàn toàn

| Bảng (model) | Dòng (dev) | Dùng ở đâu ngoài model | FK tới / từ | Rủi ro nếu xóa | Đề xuất |
|---|---|---|---|---|---|
| `meetings` (`Meeting`) | 0 | `test_schema_constraints.py` (fixture) | → `projects`, `users`; ← `transcript_segments`, `action_items` | Thấp; cần xóa theo thứ tự FK | Xóa bằng migration (nhóm A) |
| `transcript_segments` (`TranscriptSegment`) | 0 | Không | → `meetings` (CASCADE) | Thấp | Xóa (nhóm A) |
| `action_items` (`ActionItem`) | 0 | `test_schema_constraints.py` | → `meetings`; ← `task_proposals`, `tasks` | Thấp | Xóa (nhóm A) |
| `task_proposals` (`TaskProposal`) | 0 | `test_schema_constraints.py` | → `projects`, `action_items`, `users`; ← `tasks` | Thấp | Xóa (nhóm A) |
| `tasks` (`Task`) | 0 | `test_schema_constraints.py` | → `projects`, `task_proposals`, `action_items`, `users` | Thấp | Xóa (nhóm A) |
| `projects` (`Project`) | 0 | `test_schema_constraints.py` | → `workspaces`; ← 5 bảng trên và `audit_events` | Thấp; phải xóa sau mọi bảng con | Xóa (nhóm A) |
| `project_members` (`ProjectMember`) | 0 | Không | → `projects`, `users` (CASCADE) | Thấp | Xóa (nhóm A) |
| `audit_events` (`AuditEvent`) | 0 | Không | → `projects`, `users` | Thấp; trace RAG dùng `query_runs`/`processing_jobs`, không dùng bảng này | Xóa (nhóm A) |

Enum Python đi kèm chỉ dùng cho các bảng trên: `ProposalStatus`, `ProposalOrigin`, `TaskStatus` (DB lưu dạng VARCHAR + CHECK, không có PostgreSQL enum type riêng).

### Phần lai: bảng RAG còn mang dấu vết cũ

| Thành phần | Hiện trạng | Rủi ro nếu bỏ | Đề xuất |
|---|---|---|---|
| `processing_jobs.entity_type`, `entity_id`, index `ix_processing_jobs_entity` | Code RAG (`deletion.py`, `retry.py`, upload) vẫn ghi `entity_type="document"`, `entity_id=document_id` | **Trung bình**: bảng trung tâm của worker; phải sửa code ghi và CHECK `legacy_or_rag` cùng lúc | Để sau (nhóm B) |
| CHECK `legacy_or_rag`, trạng thái `processing` trong `JobStatus` | Cho phép job generic (`document_id IS NULL`) với trạng thái cũ. Dev: 0 job legacy, 10 job RAG | Trung bình; `test_rag_identity.py` có test tạo job `entity_type="meeting"` để chứng minh worker không claim | Để sau (nhóm B): siết thành `document_id NOT NULL` trong migration riêng, kèm sửa test |
| `UserRole.APPROVER`, `UserRole.DEMO_ADMIN` và CHECK VARCHAR `user_role` | Không code nào dùng; auth RAG chỉ nhận `member`, `knowledge_admin`. Dev: 1 `knowledge_admin`, 1 `member` | Thấp ở dev; môi trường khác có thể còn user cũ (spec mục 18.3 giữ inactive để review) | Để sau (nhóm B), kiểm dữ liệu trước |
| `users.email` (unique, bắt buộc), default `username = legacy_<hex>` | Seed vẫn điền email; default username chỉ phục vụ backfill Bước 04 | Thấp | Giữ |
| `eval_runs` (`EvalRun`) | Bảng RAG theo spec, **không phải legacy**, nhưng chưa code nào ghi (eval lưu file `eval/runs/`). Dev: 0 dòng | Không | Giữ; quyết khi làm 01-T5 hoặc dashboard (roadmap 07) |

### Code và cấu hình chết

| Thành phần | Hiện trạng | Rủi ro nếu xóa | Đề xuất |
|---|---|---|---|
| `backend/app/ai/__init__.py` | Package rỗng, docstring mô tả adapter OpenAI-compatible, faster-whisper, agent (kiến trúc cũ) | Không; không ai import | Xóa (nhóm C) |
| `backend/app/workers/__init__.py` | Package rỗng, docstring mô tả worker dự kiến; worker thật ở `app/worker.py` | Không | Xóa (nhóm C) |
| `Settings.stt_model` | Không ai đọc | Không | Xóa (nhóm C) |
| `pyproject.toml` extra `[stt]` (`faster-whisper`) | CLAUDE.md đã cấm cài | Không | Xóa (nhóm C) |
| Alias `STORAGE_DIR` cho `FILE_STORAGE_DIR` | Tương thích `.env` cũ | Thấp, nhưng `.env` máy cũ có thể hỏng | Giữ |

### Test

| Test | Liên quan | Đề xuất |
|---|---|---|
| `tests/test_schema_constraints.py` (6 test proposal/task) | Chỉ kiểm bảng nhóm A | Xóa cùng nhóm A |
| `tests/test_rag_identity.py` (job `entity_type="meeting"`) | Kiểm worker không claim job generic | Sửa cùng nhóm B |
| `tests/test_rag_migration.py` (chèn job legacy và `eval_runs` khi nâng từ `27b126c3c0bc`) | Kiểm đường migrate lịch sử | Giữ; nếu nhóm A/B thêm migration mới thì bổ sung kiểm upgrade/downgrade |
| Ba file migration trong `alembic/versions/` | Lịch sử đã áp dụng | **Không sửa** (quy tắc repo) |

## Đề xuất thứ tự nếu quyết định dọn

1. **Nhóm C: code chết** (nhỏ nhất, không đụng DB). Xóa 2 package placeholder, `stt_model`, extra `[stt]`. Kiểm bằng ruff và full backend.
2. **Nhóm A: 8 bảng legacy**, một migration mới:
   - Thứ tự drop: `tasks` → `task_proposals` → `transcript_segments`, `action_items` → `meetings` → `audit_events`, `project_members` → `projects`.
   - Bỏ model và enum tương ứng, xóa `test_schema_constraints.py`.
   - Migration phải kiểm số dòng và **dừng nếu bảng có dữ liệu**, thay vì drop mù.
   - Có `downgrade()` tạo lại bảng rỗng.
   - Test upgrade/downgrade trên PostgreSQL thật.
   - Cập nhật spec mục 18.3, audit mapping và CLAUDE.md (migration head).
3. **Nhóm B: siết `processing_jobs` và role**, đợt riêng sau A:
   - Thêm `document_id NOT NULL`, bỏ CHECK `legacy_or_rag`.
   - Bỏ trạng thái `processing` và vai trò `approver`/`demo_admin`, kèm kiểm dữ liệu.
   - Cân nhắc bỏ `entity_type`/`entity_id` (đụng worker, cần full test và chạy lặp test đồng thời).

**Lợi ích:** schema khớp đúng sản phẩm RAG, dễ giải thích khi phỏng vấn; bớt 8 bảng và khoảng 300 dòng model/test không dùng (lưu ý `ProcessingJob` nằm chung file `meeting.py`, phải chuyển sang file khác trước khi xóa phần meeting).
**Chi phí và rủi ro:** nhóm A cần một migration và test (cỡ S), nhóm B chạm bảng job quan trọng nhất (cỡ M). `release/m1` vẫn giữ schema cũ, nên không ảnh hưởng bản chốt M1.

## Giới hạn

- Số dòng chỉ đo trên DB development máy này. Máy khác hoặc bản backup có thể có dữ liệu legacy; migration xóa phải tự kiểm lại.
- Tìm nơi dùng bằng `grep` theo tên; không phát hiện truy cập động qua chuỗi SQL ngoài các file đã liệt kê.
- Không chạy test trong task này, vì không có thay đổi code.
