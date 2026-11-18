# 03 — Thư mục tài liệu và hỏi theo thư mục

**Mốc:** M2 · **Công sức:** M · **Phụ thuộc:** không · **Nhánh:** `feat/03-folders`

## Mục tiêu

- Admin chia tài liệu theo nghiệp vụ, ví dụ Nhân sự, Kinh doanh, Kỹ thuật.
- Người dùng chọn một hoặc nhiều thư mục làm phạm vi khi hỏi.

## Giá trị với nhà tuyển dụng

Đây là yêu cầu thật của doanh nghiệp. Phần đáng kể khi phỏng vấn là thiết kế: phạm vi được xác định bằng SQL lúc truy vấn, nên không phải reindex và vẫn giữ nguyên tắc SQL là nguồn sự thật.

## Hiện trạng

- Sau 03-T1 (18/11/2026), `folders` và `documents.folder_id` đã có model/migration; CRUD thư mục đã có API. Migration mới chỉ kiểm chứng trên DB test, chưa áp dụng DB development. [Report](../folders-20261118.md).
- T1 dùng FK đơn `SET NULL` và FK kép bảo vệ workspace; xóa API kiểm tra mọi document row còn tham chiếu, kể cả tombstone. Bộ đếm ready không quyết định thư mục rỗng.
- API gán tài liệu/upload/lọc thư mục thuộc T2; search/chat scope thuộc T3; UI thuộc T4.
- Chat đã có `filters.document_ids`, tối đa 50 ID, được kiểm tra trong `retrieval._snapshots`.
- UI có bộ chọn tài liệu (`ChatPage.tsx`, phần `document-picker`) và chip phạm vi.

## Thiết kế

- **Bảng `folders`:**
  - Cột: `id`, `workspace_id`, `name` (1–100 ký tự, unique theo workspace, không phân biệt hoa thường), `created_by`, timestamps.
  - **Không lồng thư mục** trong phiên bản này, để đơn giản. Có thể mở rộng sau bằng `parent_id`.
- **Tài liệu:**
  - `documents.folder_id` nullable, FK có `ON DELETE SET NULL`. Tài liệu không thuộc thư mục nào hiện là "Chưa phân loại".
  - Composite FK `(folder_id, workspace_id)` để không gắn được thư mục của workspace khác, giống mẫu ở K-038.
- **API (admin ghi, mọi thành viên đọc):**
  - `GET /folders` trả kèm số tài liệu `ready` trong từng thư mục.
  - `POST /folders`, `PATCH /folders/{id}` (đổi tên).
  - `DELETE /folders/{id}`: chỉ xóa được khi thư mục rỗng, nếu không trả 409 `folder_not_empty`. Không xóa dây chuyền tài liệu.
  - `PATCH /documents/{id}` với body `{folder_id}` để chuyển thư mục; tài liệu đang `deleting` trả 410.
- **Lọc khi hỏi:**
  - Thêm `filters.folder_ids` (tối đa 20).
  - Backend lấy toàn bộ tài liệu `ready` trong các thư mục đó **tại thời điểm truy vấn**, rồi giao với `document_ids` nếu có cả hai.
  - Thư mục không tồn tại hoặc thuộc workspace khác trả 404 cho cả request.
  - Thư mục rỗng trả abstention với `reason_code: "no_ready_documents"` như hiện tại.
- **Idempotency:** hash thêm `folder_ids` đã sắp xếp. `config_json` lưu `folder_ids` và danh sách document đã resolve, để trace tái lập được.
- **Upload:** form upload có ô chọn thư mục (tùy chọn).
- **UI (cần xác nhận UI riêng):**
  - Trang Tài liệu: cột hoặc nhóm theo thư mục, bộ lọc thư mục, thao tác chuyển thư mục.
  - Hỏi đáp: bộ chọn phạm vi có thêm tab Thư mục; chip hiện tên thư mục.

## Task

### T1 — Schema, migration và API thư mục

**Hoàn tất 18/11/2026:** backend 351/351; Ruff và Alembic drift check đạt trên DB test. [Bằng chứng, đánh đổi và giới hạn](../folders-20261118.md). Chưa triển khai T2–T4.

- Migration Alembic tạo bảng và FK, kiểm tra `alembic check` không có thay đổi lạ.
- **Test:** CRUD; tên trùng 409; member ghi 403; workspace khác 404; xóa thư mục còn tài liệu 409.

### T2 — Gán tài liệu vào thư mục

- `PATCH /documents/{id}`, upload kèm `folder_id`, `GET /documents?folder_id=`.
- **Test:** chuyển thư mục; gán thư mục của workspace khác bị từ chối ở tầng DB và API; tài liệu `deleting` trả 410.

### T3 — Lọc theo thư mục khi search và chat

- **Test (PostgreSQL và Qdrant thật):**
  - Chỉ trả hit thuộc thư mục đã chọn.
  - Tài liệu chuyển sang thư mục khác giữa hai lần hỏi thì lần sau không còn trong phạm vi.
  - Giao với `document_ids` đúng.
  - Replay cùng `client_request_id` nhưng khác `folder_ids` trả 409 `idempotency_conflict`.

### T4 — UI

- Trang Tài liệu và bộ chọn phạm vi như ở phần Thiết kế.
- **Test frontend:** chọn thư mục thì request gửi đúng `folder_ids`; đổi tên hoặc xóa thư mục có xác nhận.

## Không làm

- Thư mục lồng nhau.
- Phân quyền theo thư mục (ai được xem thư mục nào). Đây là bước tiếp theo nếu cần, và sẽ đụng tới bất biến scope.
