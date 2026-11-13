# 05 — Báo tiến độ thật khi trả lời (stream theo bước)

**Mốc:** M3 · **Công sức:** M · **Phụ thuộc:** không · **Nhánh:** `feat/05-progress-stream`

## Mục tiêu

Trong 30–60 giây chờ câu trả lời, người dùng thấy hệ thống đang ở bước nào: tìm tài liệu, chọn ngữ cảnh, gọi model, sửa output, kiểm tra trích dẫn. Thông tin này phải lấy từ **trạng thái thật** ở server.

## Giá trị với nhà tuyển dụng

Thể hiện tư duy UX cho hệ thống AI có độ trễ cao, mà không đánh đổi tính trung thực. Câu chuyện phỏng vấn: "Trước đây chúng tôi chủ động **không** vẽ thanh % giả (K-105). Khi cần hiện tiến độ, chúng tôi phát trạng thái thật từ server."

## Hiện trạng

- `POST /chat/query` là lời gọi đồng bộ, trả kết quả một lần.
- `query_runs` có trạng thái `status` (running, completed, failed) nhưng chưa ghi bước con.
- UI hiện đồng hồ đếm giây và mốc 30–45 giây, sau 60 giây thì báo hạn chót 2:30 (`ChatPage.tsx`, `features/chat/failure.ts`).
- Không giữ transaction trong lúc gọi model. Giữ nguyên bất biến này.

## Thiết kế

- **Ghi bước vào DB:**
  - Thêm cột `query_runs.stage` (VARCHAR + CHECK) và `stage_changed_at`. Giá trị: `retrieving`, `packing`, `generating`, `repairing`, `validating`, `publishing`.
  - `chat.query` cập nhật cột này bằng transaction ngắn ở mỗi ranh giới, không giữ lock.
  - Thêm thời gian từng bước vào `timings` nếu chưa có.
- **Endpoint đọc tiến độ:**
  - Chọn **poll** `GET /chat/runs/{id}` (đã có), bổ sung `stage` và `elapsed_ms`.
  - Client cần biết `run_id` sớm. Thêm `GET /chat/sessions/{sid}/runs?client_request_id=` để tra run theo ID client tự tạo, có kiểm tra chủ phiên.
  - **Không dùng SSE ở bước đầu.** `EventSource` không gửi header `Authorization`; muốn dùng thì phải fetch stream và tự xử lý reconnect. Poll 1 giây là đủ cho độ trễ hàng chục giây. Ghi rõ lựa chọn này trong KNOWLEDGE. SSE là bước nâng cấp nếu cần.
- **UI:**
  - Stepper 5 bước, bước hiện tại lấy từ server. Bước nào chưa có dữ liệu thì không tô.
  - Giữ đồng hồ đếm giây.
  - Khi `repairing`, hiện dòng "Đang sửa định dạng câu trả lời (lần duy nhất)".
- **Không** stream từng token: output là JSON claims phải được kiểm tra xong mới hiện (bất biến 7).

## Task

### T1 — Ghi stage ở backend

- Migration và cập nhật trong `chat.query`.
- **Test:** chuỗi stage đúng thứ tự với provider giả. Lỗi ở `generating` để lại `stage = generating` và `status = failed`. Không có lock DB nào bị giữ trong lúc provider chạy (test barrier như K-071).

### T2 — API tra run theo `client_request_id` và trả stage

- **Test:** chỉ chủ phiên tra được (admin nhận 404); ID không tồn tại trả 404.

### T3 — Stepper trên UI (cần xác nhận UI)

- Poll mỗi 1 giây khi đang chờ; dừng khi xong, lỗi hoặc rời trang.
- **Test frontend:** stage nhảy đúng; lỗi mạng khi poll không làm hỏng luồng chính.

## Không làm

- Stream token.
- WebSocket.
- Hủy câu hỏi đang chạy (cancel). Có thể làm sau, nhưng sẽ đụng tới idempotency (K-064).
