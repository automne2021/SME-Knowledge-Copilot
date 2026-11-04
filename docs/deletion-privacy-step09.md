# Bước 09 — Delete, privacy và fault/race tests

Ngày thực hiện: 04/11/2026, theo xác nhận Bước 09 của người dùng. Phạm vi backend/tests/docs, không UI, cài dependencies, tải weights, LLM calls hoặc commit/push. [PLAN](../PLAN.md), [spec 7.5/9](../SME_Knowledge_Copilot_RAG_Specification.md), [KNOWLEDGE K-068–071](../KNOWLEDGE.md).

**Hoàn thành phạm vi Bước 09:** full backend **302 passed/1 warning** trong379,71giây; eval riêng **91 passed/1 warning** trong8,87giây. Ruff check/format **114 files**, pip check và Git whitespace check đạt. Warning Starlette/httpx giữ nguyên, không skip hoặc ẩn. Các reports model/retrieval trước bất biến; không gọi model thật trong đợt này. Tiến độ **75,6% /100%** theo trọng số PLAN, không phải accuracy.

## API và lifecycle

`DELETE /api/v1/documents/{id}` yêu cầu knowledge_admin. Scope được kiểm tra trước status; member403, foreign/missing404. Transaction khóa document, đặt deleting/deleted_at, tăng lifecycle_version, clear active revision/generation, hủy ingestion leases, redact chat/trace và tạo cleanup job. Sau commit trả202/document_id/job_id/status. Delete lặp không tạo job mới; đã deleted trả200. GET nguồn410 ngay cả khi Qdrant đang lỗi hoặc cleanup chưa chạy. Search toàn workspace loại nguồn; filter explicit nguồn deleting/deleted trả410.

`POST /api/v1/jobs/{id}/retry` yêu cầu admin; cleanup retry chỉ khi document còn deleting và lỗi tạm thời. Có job active thì trả cùng job; terminal failure hợp lệ tạo job mới với attempt budget mới. Document lock và partial unique index bảo đảm hai retry đồng thời có một job active. Không reset document về queued/ready để retry cleanup. Route ingestion cũ POST/documents/{id}/retry giữ nguyên; generic job retry dispatch ingestion/cleanup theo kind.

## Các bản sao dữ liệu được xử lý

| Nơi lưu | Hành vi |
|---|---|
| Document lifecycle | Disable ngay trong delete transaction; tombstone IDs/hash giữ lại |
| Query run | Trace mặc định chỉ IDs/hash/spans; running run bị ảnh hưởng chuyển failed/source_changed |
| Assistant message | Xóa content và structured_answer_json, source_unavailable=true |
| Answer citations | Xóa excerpt/location snapshots của toàn answer bị ảnh hưởng; unavailable, chunk FK set null khi cleanup |
| Lịch sử/replay/GET run | Không trả cached answer/citation đã bị che; user question và answer khác giữ lại |
| Qdrant | Delete filter workspace AND document, mọi collection liên quan, wait+verify |
| Original file | Canonical key, kiểm tra root/UUID/symlink/junction, unlink từng file; missing success |
| SQL source | Delete blocks/chunks; retire revision, clear storage key/count; scrub filename/warnings |
| Logs | IDs/status/error type/code; không full text, prompt, API key hoặc raw exception |

Run bị ảnh hưởng được tìm qua **final evidence map lẫn citations**, nên context không được cite cũng không thành đường vòng giữ dữ liệu. Chuyển cách lưu map của Bước08 sang provenance tại [privacy.py](../backend/app/services/privacy.py); full text chỉ ở RAM khi xây prompt. Default trace không lưu excerpt/filename/location. Legacy debug/full-context traces bị scrub khi nguồn bị xóa; immutable synthetic reviewed corpus/eval reports là dữ liệu kiểm chứng riêng, không bị xóa cùng API storage.

Provider wrapper đọc lại nguồn trước từng countTokens, generate và repair, rồi commit transaction trước network. CountTokens cũng gửi text ra ngoài; nếu nguồn bị xóa giữa các lượt, lượt kế tiếp bị chặn. Không giữ lock qua HTTP nên vẫn có cửa sổ sau check/bytes đã in-flight; không tuyên bố thu hồi dữ liệu đã rời process.

## Worker và recovery

[CleanupQueue/CleanupWorker](../backend/app/services/cleanup.py) dùng cùng nền SQL lease/heartbeat/SKIP LOCKED/backoff, tối đa3 attempts. Xóa vector/file ngoài DB locks; transaction SQL cuối mới ghi deleted. Failure giữ deleting; missing file/collection là idempotent success, không recreate collection. Rollback DB sau physical cleanup có thể chạy lại; mất commit acknowledgment được SQL readback nhận diện. Stale attempt mất lease không được finish.

Worker bình thường ưu tiên cleanup, recover cả ingestion/cleanup rồi sweep. Worker cũ đang upsert qua network có thể ghi vector sau lần verify rỗng; quyền publish đã bị thu hồi, nên SQL không cho retrieve. Reconciliation định kỳ xóa lại theo tombstone/workspace/document/collection. Orphan sweeper không giữ generation chỉ vì citation đã unavailable. Đây là eventual physical cleanup; bảo đảm cứng là request bắt đầu sau delete commit không dùng nguồn.

Chạy từ backend/, trong đợt vận hành được xác nhận:

```powershell
# Worker thường, cùng cwd/storage profile với API:
.\.venv\Scripts\python.exe -B -m app.worker

# Không cần model cache/tokenizer/weights/inference:
.\.venv\Scripts\python.exe -B -m app.worker --cleanup-only --once

# Service cleanup/reconcile định kỳ:
.\.venv\Scripts\python.exe -B -m app.worker --cleanup-only
```

Không chạy service worker chung queue DB khi tests/eval đang chạy. Không xóa volumes để chữa job lỗi. Các collections cũ lấy từ revisions; missing collection thành success. Với số tombstones lớn cần paging/scheduling và benchmark riêng; hiện chưa stress production scale.

## Fault/race coverage

| Tình huống | Bằng chứng kiểm tra |
|---|---|
| Delete ready/nonready | queued/processing/failed/needs_ocr đều vô hiệu hóa ingestion; không ready trở lại |
| Delete/retry đồng thời | Một cleanup job active, lifecycle tăng đúng một lần |
| Vector/file unavailable | Retry/backoff; exhaustion giữ deleting; admin retry riêng |
| DB rollback / acknowledgment mất | Không false success; replay/idempotent cleanup không tạo thêm dữ liệu |
| Query đang countTokens | Barrier delete+cleanup rồi thả, không count tiếp theo mang evidence, generation hoặc ghi map mới |
| Query đang generate | Barrier delete+cleanup rồi thả,409 source_changed, không assistant draft |
| Invalid output rồi nguồn bị xóa | Không repair gửi lại context;409 và chỉ một provider generate |
| Ingestion đã bắt đầu upsert | Barrier cho late write sau cleanup, không publish SQL; reconcile xóa lại |
| Old cleanup lease | Expire/recover/claim mới; old attempt bị fence |
| Privacy | Cited/uncited context, legacy full/nested debug copies, history/replay/source URLs |
| Storage scope | Nhiều collections, workspace AND document filter, missing file/collection, path traversal |
| Không model cache | CLI cleanup-only xử lý job với HF_HOME không có weights |

[Tests](../backend/tests/test_deletion.py) dùng PostgreSQL/Qdrant thật, embeddings/provider là fakes được gắn nhãn. Suite trước vẫn kiểm tra worker kill/restart, parser/source preservation, auth/session scopes, manifest consistency, wrong citations và model/provider errors. Không gọi model thật để kiểm tra state machine hoặc suy ra semantic accuracy từ các tests này.

Lệnh full backend thực chạy từ backend/, với basetemp mới dưới .cache và TEST_DATABASE_URL đã được guard:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider --tb=short --basetemp <new-path-under-backend-cache>

# Từ root:
.\backend\.venv\Scripts\python.exe -B -m pytest eval/tests -q -p no:cacheprovider --tb=short
.\backend\.venv\Scripts\ruff.exe check --config backend/pyproject.toml backend/app backend/tests backend/alembic eval
.\backend\.venv\Scripts\ruff.exe format --check --config backend/pyproject.toml backend/app backend/tests backend/alembic eval
.\backend\.venv\Scripts\python.exe -B -m pip check
```

Các lỗi phát hiện được giữ trong KNOWLEDGE K-071: teardown phải giữ deleted tombstone khi reupload cùng hash; fault injection cần hoạt động sau flush; xử lý job phải đứng trước maintenance để sweep lỗi không gây starvation. Suite cuối thêm guard cho countTokens/repair để không gửi lại nguồn đã xóa ở lần provider operation tiếp theo. Không đổi constraints hoặc bỏ tests để đạt gate.

Probe bàn giao: dev/test head20261103_rag04, READ COMMITTED; dev2users/test0users và cả hai0documents/revisions/blocks/chunks/sessions/runs/messages/citations/jobs. Qdrant chỉ còn collection mặc định, collections test đã dọn. Scan422 candidate files không chứa3secrets thực .env;4core hashes/166historical source snapshots và10tài liệu local links đạt. Reviewed/mapping/reports/migrations cũ bất biến; không frontend thay đổi.

## Giới hạn

- Không thu hồi dữ liệu đã tải/gửi provider trước delete; không tuyên bố secure erase các block ổ đĩa, database WAL/backups hoặc bộ nhớ process.
- User question được giữ theo spec; có thể do người dùng tự gõ/trích text. Retention cho dữ liệu này cần policy riêng nếu sản phẩm public.
- Reconciliation cần worker tiếp tục chạy và services phục hồi; terminal errors hiển thị qua job để admin xử lý.
- Chưa UI/browser E2E hoặc final human-quality/held-out evaluation. UI vẫn cần xác nhận riêng trước viết/sửa.
