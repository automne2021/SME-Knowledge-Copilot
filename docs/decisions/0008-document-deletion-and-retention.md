# RAG-08 — SQL disable, chat redaction và durable cleanup

- Ngày: 04/11/2026.
- Trạng thái: triển khai Bước09; regression/results tại [report](../deletion-privacy-step09.md).
- Nguồn: spec7.5/9 và PLAN09; không thay migration đã áp dụng.

## Vấn đề và quyết định

SQL, Qdrant và filesystem không có transaction chung. Vector deletion đơn lẻ không vô hiệu hóa nguồn SQL và không dọn bản sao trong chat. Chọn transaction SQL disable document, tăng lifecycle, thu hồi ingest lease, redact toàn answer bị ảnh hưởng và enqueue cleanup. Request mới loại deleting/deleted dựa trên SQL. Cleanup idempotent chạy ngoài document locks cho network/file, lease-fenced transaction cuối ghi deleted.

Final-context registration serialize với delete qua document lock trước model call; final publication tiếp tục revalidate. Provenance map mặc định giữ IDs/hash/spans, không full context. Redact theo map và citations, gồm uncited context; giữ questions và unrelated answers. Tombstones giữ IDs cần cho audit/reconciliation, xóa source text/snapshots/file keys/filename khi cleanup.

Late upsert không thể bị thu hồi bằng lease nếu HTTP đã rời worker. SQL publication fence chặn ready; tombstone reconciliation xóa lại vectors theo workspace/document trên các collections liên quan. Worker có cleanup-only để xóa không cần weights/cache/inference. Đây là consistency có recovery, không phải distributed ACID hoặc secure erase.

## Phương án khác và đánh đổi

- Xóa đồng bộ trong API/transaction: dễ hiểu khi thành công, nhưng giữ locks qua I/O và không giải quyết rollback file/vector.
- Chỉ xóa vector: bỏ sót SQL/history/snapshots, không đáp ứng privacy.
- Hard-delete toàn session: mất cả nội dung không liên quan, không theo contract.
- Broker/outbox riêng: thêm vận hành; SQL jobs hiện được tạo atomic và đã có lease/recovery.

Đánh đổi là redaction conservative với mọi final-context source, giảm khả năng chẩn đoán khi không lưu full prompt và cần sweeper để xử lý late writes. Cần paging/indexing/coordination bổ sung trước dùng nhiều tenants/tombstones hoặc API workers lớn. [KNOWLEDGE K-068–071](../../KNOWLEDGE.md) ghi cơ chế, lỗi fixture và cách kiểm chứng.
