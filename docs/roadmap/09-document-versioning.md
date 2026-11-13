# 09 — Phiên bản tài liệu và reindex không gián đoạn

**Mốc:** M4 · **Công sức:** L · **Phụ thuộc:** không · **Nhánh:** `feat/09-versioning`

## Mục tiêu

- Admin tải phiên bản mới cho một tài liệu đã có, ví dụ quy định nghỉ phép 2027 thay bản 2026.
- Trong lúc bản mới đang xử lý, người dùng vẫn hỏi được trên bản cũ.
- Khi bản mới xong, hệ thống chuyển sang bản mới một cách nguyên tử.
- Có thể reindex toàn bộ khi đổi cấu hình chunk hoặc embedding.

## Giá trị với nhà tuyển dụng

Đây là bài toán vận hành RAG thật: dữ liệu luôn thay đổi. Câu chuyện phỏng vấn: "Cập nhật tài liệu mà không có thời điểm nào hệ thống trả lời từ một index dở dang" (bất biến 3).

## Hiện trạng

- Schema đã có `document_revisions` (cột `version`, `status`, `storage_key`) và `documents.active_revision_id` / `active_generation_id`.
- Publish nguyên tử theo manifest đã có (K-051), cleanup generation cũ đã có (K-052).
- Upload trùng hash bị chặn bằng 409 (K-043).
- Spec có endpoint P1 `POST /documents/{id}/reindex`.
- Bất biến: chỉ revision **active** được dùng. Câu trả lời cũ trích dẫn revision cũ sẽ bị che trong lịch sử (`messages` đã kiểm tra `active_rev != rev`).

## Thiết kế

- **`POST /documents/{id}/revisions`** (admin, multipart):
  - Tạo revision mới ở trạng thái `staging` và một job ingest.
  - Tài liệu giữ `ready` với revision cũ trong lúc xử lý.
  - File trùng hash với revision active thì trả 409.
- **Khi publish:**
  - Một transaction chuyển `active_revision_id` và `active_generation_id` sang bản mới, rồi lập lịch cleanup bản cũ.
  - Revision cũ chuyển `superseded`, giữ metadata, xóa vector và text theo chính sách retention.
- **Lịch sử chat:** câu trả lời dùng revision cũ hiện "Nguồn đã có phiên bản mới". Vẫn che nội dung như hiện tại; không tự trả lời lại.
- **`POST /documents/{id}/reindex`** (admin): tạo generation mới **cùng** revision khi đổi parser, chunker hoặc embedding version. Có thêm lệnh CLI chạy reindex cho toàn workspace theo lô, có giới hạn đồng thời.
- **Đổi model embedding** cần collection mới (fingerprint khác). Thiết kế "dual index": giữ collection cũ phục vụ truy vấn cho tới khi mọi tài liệu có generation trên collection mới, rồi chuyển. Đây là phần khó nhất, nên làm sau cùng (T4).
- **Xóa trong lúc đang có revision staging:** delete thắng. Job staging bị fence và bị dọn (dùng lại cơ chế K-068 và K-070).

## Task

### T1 — Upload revision mới

- **Test:**
  - Trong lúc staging, query vẫn dùng bản cũ.
  - Publish xong thì query dùng bản mới.
  - Trùng hash trả 409.
  - Xóa tài liệu trong lúc staging thì không publish.

### T2 — Hiển thị lịch sử và trạng thái phiên bản trên UI (cần xác nhận UI)

### T3 — Reindex cùng revision

- **Test:** generation mới thay thế nguyên tử; job reindex lỗi thì bản đang active vẫn phục vụ.

### T4 — Dual index khi đổi embedding (thiết kế chi tiết trước khi code)

- Viết ADR trong `docs/decisions/`, chờ duyệt, rồi mới code.

## Không làm

- So sánh khác biệt (diff) giữa hai phiên bản.
- Khôi phục về phiên bản cũ (rollback). Ghi vào hướng phát triển.
