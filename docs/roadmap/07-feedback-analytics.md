# 07 — Phản hồi người dùng và dashboard chất lượng

**Mốc:** M3 · **Công sức:** M · **Phụ thuộc:** không · **Nhánh:** `feat/07-feedback`

## Mục tiêu

- Người dùng đánh giá từng câu trả lời bằng 👍 hoặc 👎, kèm lý do.
- Admin xem dashboard tổng hợp: chất lượng, độ trễ, lỗi, tài liệu được dùng nhiều, nhóm câu hỏi chưa trả lời được.

## Giá trị với nhà tuyển dụng

Đóng vòng "sản phẩm AI": đo chất lượng ngoài bộ eval, từ người dùng thật. Đây là tư duy product mà VNG đánh giá cao. Phần privacy cũng là điểm phỏng vấn tốt: admin chỉ thấy số tổng hợp, không đọc được chat của người khác (bất biến 1).

## Hiện trạng

- `query_runs` đã lưu: `status`, `error_code`, timings, `answer_status` (qua `chat_messages`), trace dạng ID.
- Chưa có bảng phản hồi.
- Admin không đọc được session của người khác, và **phải giữ nguyên như vậy**.

## Thiết kế

- **Bảng `answer_feedback`:**
  - Cột: `id`, `message_id` (FK tới assistant message, `ON DELETE CASCADE`), `user_id`, `workspace_id`, `rating` (`up` | `down`), `reason` (enum: `wrong`, `incomplete`, `wrong_source`, `should_abstain`, `should_answer`, `other`), `comment` (≤ 500 ký tự, tùy chọn), timestamps.
  - Unique `(message_id, user_id)`; gửi lại thì cập nhật.
  - Chỉ chủ phiên chứa message đó mới gửi được.
- **API:**
  - `PUT /chat/messages/{id}/feedback`, `DELETE /chat/messages/{id}/feedback`.
  - `GET /admin/analytics?from=&to=`: chỉ admin, chỉ trả **số tổng hợp** trong workspace.
- **Dashboard gồm:**
  - Số câu hỏi theo ngày.
  - Phân bố `grounded` / `partial` / `insufficient_evidence` / lỗi kỹ thuật (theo `error_code` và `details.reason`).
  - p50 và p95 thời gian trả lời.
  - Tỉ lệ 👍/👎 và phân bố lý do.
  - Top tài liệu được trích dẫn.
  - Số tài liệu chưa từng được dùng.
- **Privacy:**
  - Không trả câu hỏi, comment hay tên người dùng trong analytics.
  - Nhóm nào có dưới 5 sự kiện thì hiện "< 5" để tránh suy ra cá nhân.
  - Ghi rõ trong spec.
- **Câu hỏi "chưa trả lời được":** chỉ hiện **số lượng** câu `insufficient_evidence` theo tài liệu hoặc thư mục, không hiện nội dung câu hỏi. Muốn xem nội dung phải có chính sách đồng ý riêng; ngoài phạm vi.
- **Xóa:** xóa cuộc trò chuyện hoặc message thì phản hồi bị xóa theo (cascade). Analytics tính lại từ dữ liệu còn lại. Ghi rõ rằng số liệu lịch sử có thể giảm.

## Task

### T1 — Bảng và API phản hồi

- **Test:** chủ phiên gửi và sửa được; người khác (kể cả admin) nhận 404; message bị che hoặc là user message thì 409; xóa session thì xóa phản hồi.

### T2 — API analytics

- **Test:** member gọi nhận 403; số liệu khớp dữ liệu seed; nhóm dưới 5 bị ẩn; response không có trường text tự do nào.

### T3 — UI phản hồi trong câu trả lời (cần xác nhận UI)

- Nút 👍/👎. Khi chọn 👎 thì mở danh sách lý do và ô ghi chú; có trạng thái "Đã ghi nhận".

### T4 — Trang Dashboard cho admin (cần xác nhận UI)

- Biểu đồ đơn giản bằng SVG hoặc CSS, không thêm thư viện chart nếu chưa được duyệt.
- **Test frontend:** member không thấy menu; ô "< 5" hiển thị đúng.

## Không làm

- Admin đọc nội dung chat của người khác.
- Tự động dùng phản hồi để fine-tune hay đổi prompt.
