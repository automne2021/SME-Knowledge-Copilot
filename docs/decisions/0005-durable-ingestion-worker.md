# ADR RAG-05 — Durable worker, leases và generation publish

Ngày 03/11/2026. **Đã triển khai và kiểm chứng Bước 06**; contract [spec 7.4–7.5](../../SME_Knowledge_Copilot_RAG_Specification.md), [report](../worker-index-step06.md), [JobQueue](../../backend/app/services/jobs.py), [worker](../../backend/app/worker.py).

PostgreSQL là durable queue, worker Python riêng, một job concurrent. Claim SKIP LOCKED/transaction ngắn; khóa document trước job nhất quán với delete tương lai. Thread heartbeat/session độc lập; model child process có hard timeout, không giữ DB lock trong inference. Chọn UUID generation mới mỗi attempt, UUIDv5 stable trong generation, current token + expiry + lifecycle fencing ở mọi mutation. Chỉ commit ready sau SQL/Qdrant exact manifest verification.

Phương án BackgroundTasks dễ mất ingestion khi web process restart và không có durable lease; Celery/Redis/RabbitMQ thêm service khi throughput chưa có bằng chứng cần. Dùng DB queue giúp học transaction/locking/recovery trên máy CPU 16 GB; nếu queue load hoặc DB contention tăng theo số đo, giữ generation/fencing contracts khi chuyển transport.

Không thực hiện distributed transaction giữa PostgreSQL/Qdrant/files. Các vector upsert staging có thể còn sau crash; chưa active thì không hợp lệ cho consumer. Commit acknowledgement không rõ phải read-back; sweeper xử lý orphan sau grace và giữ protected active/cited/live generations. Retry transient tối đa 3 lần có jitter; permanent parser/config/dimension lỗi không auto-retry. Không tuyên bố exactly-once hoặc physical cleanup tức thì sau hard kill.

Qdrant REST wait=true, collection model hash metadata, exact IDs/payload verify và SQL manifest freeze. Chọn HTTPX trực tiếp thay SDK vì API surface P0 nhỏ, timeout/error/retry phải rõ và package đã có; xem lại khi transport/features tăng. Model child giữ E5 weights warm; in-process inference nhanh hơn một ít IPC nhưng không dừng được native work bằng thread timeout. Không tạo child/model cho từng tài liệu vì cold load chiếm phần lớn thời gian đo.

Kiểm chứng bằng real PostgreSQL/Qdrant reliability tests (embeddings fake có nhãn), kill/restart giữa batch, stale worker, rollback/lost ack, manifest mismatch và orphan replay. Run model thật 1+10 documents và 8 fixtures dùng E5 CPU cache, không LLM. Worker host Windows; Linux image/concurrency stress chưa đo. Điều kiện xem lại: nhu cầu nhiều workers, remote storage, model/runtime mới, tăng corpus hoặc cần retention/reindex P1.

Nguồn chính thức: [PostgreSQL locking/SKIP LOCKED](https://www.postgresql.org/docs/16/sql-select.html), [Qdrant upsert](https://api.qdrant.tech/api-reference/points/upsert-points), [scroll](https://api.qdrant.tech/api-reference/points/scroll-points), [collection metadata](https://api.qdrant.tech/api-reference/collections/create-collection), [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small). Không thay ADR RAG-06/07; ADR này bổ sung worker quanh các contracts identity/source đã có.
