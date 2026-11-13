# 13 — Hỏi đáp qua kênh chat (Zalo Official Account)

**Mốc:** M4 · **Công sức:** M · **Phụ thuộc:** 11 (cần endpoint HTTPS công khai) · **Nhánh:** `feat/13-chat-channel`

## Mục tiêu

Nhân viên hỏi trợ lý ngay trong Zalo, kênh nhắn tin phổ biến nhất tại Việt Nam, và nhận câu trả lời kèm trích dẫn cùng link mở nguồn trên web.

## Giá trị với nhà tuyển dụng

Zalo là sản phẩm của VNG. Một tích hợp đúng chuẩn cho thấy ứng viên nghĩ tới nơi người dùng thật sự làm việc. Phần kỹ thuật đáng kể khi phỏng vấn:
- Xác thực webhook.
- Liên kết tài khoản an toàn.
- Giữ nguyên các bất biến về quyền và xóa.

## Hiện trạng

- Chưa có kênh ngoài web.
- Pipeline hỏi đáp nằm trong `services/chat.py`, gọi được trực tiếp với một `user` đã xác thực.

## Thiết kế

- **Adapter kênh:**
  - Interface `ChannelAdapter` gồm `verify(request)`, `parse_message`, `send_reply`.
  - Bản đầu: `ZaloOAAdapter`, cùng `FakeChannelAdapter` cho test.
  - Thiết kế đủ chung để thêm Telegram hoặc Slack sau.
- **Liên kết tài khoản:**
  - Người dùng đăng nhập web, bấm "Liên kết Zalo" và nhận mã 6 ký tự (hết hạn sau 10 phút, dùng một lần), rồi gửi mã này cho OA.
  - Backend lưu `channel_links` gồm `channel`, `external_user_id` (lưu hash, không lưu bản gốc), `user_id` và timestamps.
  - Người chưa liên kết chỉ nhận hướng dẫn.
- **Webhook:**
  - `POST /channels/zalo/webhook`: kiểm tra chữ ký hoặc MAC theo tài liệu chính thức của Zalo OA, từ chối request quá cũ (chống replay), dedup theo message ID.
  - Trả 200 ngay, rồi xử lý câu hỏi bằng một job nền, vì webhook không chờ được 30–60 giây.
  - Có thể dùng lại bảng `processing_jobs` với `kind` mới, hoặc tạo bảng riêng. Quyết định trong T1 và ghi ADR.
- **Trả lời:**
  - Văn bản gồm các ý, kèm `[1]`, `[2]` và danh sách nguồn (tên file, vị trí), cùng **link** về trang web. Mở link cần đăng nhập; nội dung nguồn không được gửi đi qua Zalo.
  - Lỗi kỹ thuật được báo đúng là lỗi (dùng câu chữ từ `failure.ts`).
- **Quyền và xóa:**
  - Mỗi người dùng có một session riêng cho kênh này. Admin vẫn không đọc được session này.
  - Hủy liên kết thì không xử lý tin nhắn tiếp theo.
  - Tài liệu bị xóa thì quy tắc như trên web.
- **Bảo mật:**
  - Secret của OA nằm trong `.env`.
  - Rate limit theo từng người dùng.
  - Không gửi nội dung tài liệu qua Zalo ngoài phần câu trả lời.
- **Môi trường dev:** dùng `FakeChannelAdapter` và một script giả lập webhook. Chỉ dùng OA thật khi người dùng có tài khoản OA và đã duyệt.

## Task

### T1 — Thiết kế, ADR và FakeChannelAdapter

- Gồm: liên kết tài khoản, webhook giả, job xử lý, trả lời qua adapter giả.
- **Test:**
  - Chữ ký sai trả 401.
  - Tin trùng chỉ xử lý một lần.
  - Người chưa liên kết chỉ nhận hướng dẫn.
  - Lỗi model trả thông báo lỗi.
  - Tài liệu bị xóa không còn được dùng.

### T2 — Zalo OA adapter thật (cần tài khoản OA và xác nhận)

- Đọc tài liệu chính thức của Zalo OA tại thời điểm làm, ghi ngày kiểm tra trong report. Không dựa vào trí nhớ.

### T3 — UI liên kết tài khoản (cần xác nhận UI)

## Không làm

- Gửi file tài liệu qua Zalo.
- Group chat.
- Thông báo chủ động (broadcast).
