# Bước 06 — Worker, local embeddings và publish index

Ngày 03/11/2026. Người dùng xác nhận “Bước 6 thực hiện đi”. Phạm vi: backend worker/retry/generation, E5 CPU, Qdrant, recovery/cleanup, đo ingestion và tài liệu. Không sửa UI, không gọi LLM, không tải model mới, không commit/push.

## Hành vi đã triển khai

Upload admin → queued → worker processing → parse/chunk → embed/upsert → verify manifest → atomic ready. Các lỗi parser có trạng thái terminal thật: scan needs_ocr; blank/encrypted/malformed failed; mixed giữ trang text/cảnh báo skipped_pages. Source staging không có active generation để consumer hợp lệ sử dụng. Search/source preview/answer/delete endpoints thuộc các bước sau; không coi việc có vectors là đã có retrieval/QA.

[Worker CLI](../backend/app/worker.py) là tiến trình riêng, một job đồng thời; PostgreSQL giữ durable queue. Không BackgroundTasks/Redis/Celery. [JobQueue](../backend/app/services/jobs.py) dùng transaction ngắn, khóa document trước job; claim FOR UPDATE SKIP LOCKED để worker khác không chờ cùng tài liệu. Heartbeat thread dùng session riêng, không giữ transaction trong parse/model/network. Mặc định lease 60 s, heartbeat 15 s, poll 2 s.

Mỗi attempt sinh lease token và generation mới. Source blocks/chunks/point UUID dùng UUIDv5 từ generation + block/chunk identity; retry upsert cùng attempt giữ ID, attempt sau khác ID. Source spans persist bằng UUID block thật, thêm parser_block_id/context_block_ids để Bước 07 đối chiếu canonical mapping. SQL document lifecycle/version và current lease được kiểm tra ở mọi bước ghi; worker cũ không được stage/publish/fail thay worker mới.

## Model, cấu hình và tài nguyên

Giữ E5-small revision 614241f622f53c4eeff9890bdc4f31cfecc418b3, 384 chiều, CPU FP32/eager, masked-mean pooling/L2, prefix query/passage. Batch **4**, threads **2**, concurrency **1**, complete input <=512; chunk budget 350 của Bước 05. Tokenizer/weights local-only từ D cache; thiếu files/runtime → startup error, không download/fallback. [E5 runtime dùng chung](../backend/app/services/e5_runtime.py); eval/embedding_runtime.py chuyển thành shim, reports cũ giữ source snapshots; smoke mới cũng snapshot shared runtime.

[LocalEmbedder](../backend/app/services/embeddings.py) giữ model trong child process để nạp một lần, tái dùng qua nhiều jobs. Startup và mỗi encode batch có timeout 120 s; timeout terminate/join child, lần cần sau tạo lại. Main process/heartbeat vẫn chạy. Kiểm tra số vectors/dimension, numeric type, finiteness và norm trước upsert; sai dimension/NaN/zero vector/boolean → lỗi permanent, không pad/cắt hoặc auto-retry cùng cấu hình. OOM không fallback model và không lặp vô hạn.

Fingerprint gồm model/revision, 6 model/tokenizer file hashes, dimension, preprocessing, dtype/pooling/normalization và runtime versions. Index version hash thêm parser/chunker/config; revisions lưu fingerprint/config/collection. Collection Qdrant phải 384/Cosine và metadata embedding_hash đúng. Sai fingerprint kể cả cùng dimension → từ chối, không tự đổi collection. [REST adapter](../backend/app/services/vectors.py) dùng HTTPX trực tiếp, không SDK hidden retry; 10 s timeout mỗi network I/O, trust_env=false. Đây không phải hard wall deadline cho toàn bộ scroll nhiều trang; tổng verify hữu hạn theo point manifest trên corpus P0.

Snapshot trước triển khai: RAM khả dụng khoảng **3,41 GiB**, C còn **7,78 GiB**, D còn **79,03 GiB**. Không cài/tải lại Torch hay weights để tránh thêm disk/RAM. requirements-worker-cpu.lock tách CPU runtime Windows/Python 3.12 khỏi dev/smoke và API image; requirements.lock chỉ thêm HTTPX runtime đã có trong venv. Linux worker wheel/image chưa build/kiểm chứng; Compose hiện chạy DB/Qdrant, worker chạy host với venv hiện có.

## Publish và recovery

Metadata blocks/chunks ghi staging trước inference. Job manifest có expected point IDs/count, generation, index version/collection và SHA-256; không ghi raw text lên Qdrant payload. Upsert wait=true theo batch, xác nhận completed. Scroll toàn generation, kiểm tra đúng tập IDs/count và toàn payload expected, không chỉ count hoặc một hit. Thêm/mất/sai point phải fail trước publish.

Transaction publish khóa document rồi job, kiểm tra lease còn hạn, generation/lifecycle, manifest hash/identity và SQL point set/revision metadata. Cùng commit: revision ready, document active revision+generation/ready, job completed, progress/timings. Không có ready từng batch. DB rollback sau upsert để generation staging; retry dùng generation mới. Mất commit acknowledgement thì đọc lại job/document: đã completed/active thì giữ success, không đổi sang failed. DB chưa đọc/ghi được thì để lease cho recovery, không đoán commit state.

Recovery mỗi vòng tìm running jobs hết lease: retry_wait hoặc failed nếu hết attempts; deleting/deleted thì cancel, không resurrect. Tối đa 3 attempts/job, backoff exponential có jitter trong [delay/2,delay], base 5 s/cap 60 s. Retry tự động chỉ transient errors (DB/vector unavailable, timeout/process interruption), giữ document processing. Parse/config/dimension/manifest lỗi permanent. Graceful shutdown dừng nhận việc mới, kiểm tra stop giữa stages/batches và đưa attempt đang dừng về retry; hard kill phục hồi qua lease, không hứa exactly-once.

[POST /documents/{id}/retry](../backend/app/services/retry.py): admin, workspace scope trước status; job failed/retryable=true mới tạo job mới cùng revision. Đã có active job trả cùng ID; document lock + partial unique constraint chặn race. needs_ocr/permanent error không manual retry. GET jobs trả safe progress/timings; document metadata có latest_job_id. Khi timestamps trùng, ưu tiên job active rồi created_at/id; bulk window row_number tránh trả nhầm job cũ hoặc N+1 queries.

## Orphan reconciliation

[Sweeper](../backend/app/services/orphans.py) chạy định kỳ 60 s, grace mặc định 1 giờ và ít nhất lease+embedding timeout+vector timeout. Xét generations có worker provenance trong Qdrant hoặc SQL staging; bỏ qua active document generations, live running jobs và generations có citations. Xóa vector ngoài DB transaction rồi recheck protection trước xóa chunks/blocks trong transaction ngắn. Generation cũ không được reuse; stale writes còn lại được dọn ở vòng sau. Không chuyển failed/deleting về ready. Đây là orphan cleanup, chưa phải delete workflow/tombstone/history cleanup Bước 09.

File sweeper chỉ unlink key canonical workspaceHex/revisionHex.extension, nằm trong root sau resolve, không symlink, đủ cũ và không có revision tham chiếu. File đang upload/fresh và tên file ngoài format không bị xóa. Không recursively delete folder; không xóa file gốc còn referenced để “dọn cache”. Failure network/DB không làm mất queue; retry sweep sau.

## Số đo thật: 1 rồi 10 documents

[Run 20261103T093516Z](../eval/reports/ingestion_s6_20261103T093516Z_896b9799/manifest.json), [per-document outputs](../eval/reports/ingestion_s6_20261103T093516Z_896b9799/per_document.jsonl), [source snapshots/hashes](../eval/reports/ingestion_s6_20261103T093516Z_896b9799/source_sha256.json). Dùng auth/upload/get document/get job qua ASGI TestClient, worker thật, E5 thật và Qdrant/PostgreSQL test thật. Tài liệu synthetic reviewed-v1, hai workspaces tách phase để không vượt dedup bằng đổi filename.

| Phase | Documents / chunks | Wall time |
|---|---|---:|
| Cold model | 1 / 1 | 13,0251 s |
| Model đã nạp, tuần tự | 10 / 14 | 4,5647 s |

Model load **10,1699 s** nằm trong cold phase. Sampled peak **1.181.339.648 bytes (~1,10 GiB)** cho tổng RSS parent+children, sampler mỗi 20 ms; không phải memory allocation model riêng, không phải peak toàn máy, có thể đếm chung mapped pages. Không đo throughput tải lớn, không phải quality/latency SLA; corpus chỉ 10 tài liệu ngắn. Giữ batch 4/concurrency 1 vì đã chạy trong tài nguyên máy; không có batch-size sweep để khẳng định tối ưu.

Thêm 8 fixtures, tổng **19 upload attempts**: 11 corpus uploads ready; mixed/injection ready; scan/blank/encrypted/malformed-PDF ra đúng terminal; spoofed PDF và malformed non-ZIP DOCX bị từ chối 415 trước job. Malformed DOCX gọi parser trực tiếp ở Bước 05 vẫn parse_failed; upload boundary có thể từ chối sớm hơn. Report status=passed, cleanup_completed=true: xóa collection/workspaces/users/tokens/SQL rows/files chỉ thuộc smoke; reviewed snapshot và dev corpus không bị thay. LLM calls=0, API model spend=0 USD. Các failure tests khác dùng embeddings giả có nhãn, không tính là đo chất lượng E5.

## Chạy local và kiểm chứng

Từ backend/, dùng cùng cwd/storage profile với API; migrate một lần trước khi chạy, worker không tự migrate:

```powershell
# Venv hiện có đã đủ dependencies; checkout mới cài cả dev và worker locks nếu cần eval/tests.
.\.venv\Scripts\python.exe -m pip install -r requirements-worker-cpu.lock
.\.venv\Scripts\python.exe -B -m app.worker --once
.\.venv\Scripts\python.exe -B -m app.worker
```

--once recover/sweep và xử lý tối đa một job rồi thoát; phải đọc GET jobs/documents để biết job ready/failed, exit 0 không thay cho trạng thái job. Không chạy worker dev cùng reliability tests/smoke vì durable queue là global trên từng DB. Test guard chỉ cho PostgreSQL local DB *_test tách dev; Qdrant tests dùng collections s6_test_<random>, smoke s6_smoke_<random> rồi xóa đúng scope.

Từ root: `python -B -m eval.ingestion_smoke` tạo run ID mới, không ghi đè report; inference/artifacts cần đợt xác nhận. Full backend tests dùng --basetemp .cache\<new-short-id> mới trong workspace; eval tests chạy riêng. Kết quả cuối: **196 backend passed/1 warning**, **76 eval passed** ở hai invocations riêng; Ruff check/format **85 files**, pip check đạt. Warning Starlette TestClient/httpx giữ từ baseline. Test SKIP LOCKED tăng thời gian chờ tạo connection từ 3 lên 15 s cho localhost IPv6/Windows, vẫn trả về khi document lock còn giữ. Full run đầu bắt latest_job_id sai khi timestamps trùng; đã sửa ưu tiên active/window row_number và chạy lại full.

CLI `python -B -m app.worker --once` trên profile host dev đã khởi động/xác minh collection model metadata thành công, không cần tải weights mới. Tiến độ **46,3% / 100%**, `(37,5+10)/102,5`, 6/6 đầu việc Bước 06; giữ trọng số và chờ xác nhận đợt Bước 07.

Probe cuối: dev head 20261103_rag04/2 users/0 documents/revisions/blocks/chunks; test cùng head/0 users/0 documents/revisions/blocks/chunks. Qdrant chỉ còn knowledge_e5_small_v1/0 points; các collection test/smoke đã dọn. Collection mặc định rỗng là kết quả chủ động giữ sạch dữ liệu thử, không phải chưa chạy ingestion. Scan 162 source/docs/eval/config files không chứa các secrets thực từ .env; không in giá trị. Reviewed manifest SHA-256 vẫn efccfaeaf67e9e49035d08771977982ccd34df83d12128a4835948738f2c6b26; canonical mapping vẫn a75f4b8c23c7a1270f0f911a8d8db11ce56af454913904f12501e902471d933b. Git whitespace và local documentation links đạt.

Giới hạn: chưa có search/source endpoints và context/citation/delete flow, chưa nghiệm thu end-to-end retrieval exclusion. Các tests chứng minh staging không active/không publish, actual query filter/SQL revalidation nối ở Bước 07. Không có Linux worker Docker build, load/concurrency stress, OCR hay model challenger mới. Bước 07 cần đợt xác nhận riêng; trước code UI sẽ nhắc theo AGENTS.
