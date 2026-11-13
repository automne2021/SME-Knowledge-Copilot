# 08 — OCR cho PDF scan

**Mốc:** M4 · **Công sức:** L · **Phụ thuộc:** 01 (slice `scan`), nên làm sau 11 nếu muốn chạy trên Linux · **Nhánh:** `feat/08-ocr`

## Mục tiêu

PDF scan (không có lớp chữ) đọc được bằng OCR tiếng Việt. Hiện các file này bị từ chối với `needs_ocr`. Chất lượng phải được đo riêng và thể hiện rõ trên UI.

## Giá trị với nhà tuyển dụng

Văn bản hành chính ở Việt Nam rất hay là bản scan. Phần đáng kể khi phỏng vấn là cách xử lý trung thực:
- Có số đo riêng cho slice `scan`.
- Gắn nhãn "văn bản nhận dạng tự động" cho phần OCR.
- Có timeout theo từng trang.
- Có lý do vì sao không mặc định bật.

## Hiện trạng

- `parsing.py` ném `ParseError("needs_ocr")` khi PDF không có text, và cảnh báo `partial_text_extraction` khi chỉ một số trang thiếu text.
- Parser chạy trong subprocess, timeout 60 giây (K-045).
- Máy dev dùng CPU, RAM 16 GB, ngân sách 0 USD.

## Thiết kế

- **Engine:**
  - Dùng Tesseract 5 với gói ngôn ngữ `vie`, gọi qua `pytesseract`, bằng một subprocess riêng.
  - Đây là dependency hệ thống mới (Windows installer; `apt` trên Linux), nên **cần người dùng duyệt** và ghi vào runbook.
  - PaddleOCR và VietOCR chỉ thử nếu Tesseract không đạt ngưỡng; tốn tài nguyên hơn nhiều.
- **Luồng:**
  1. Render trang thiếu text bằng PyMuPDF ở 300 DPI.
  2. Chạy OCR, lấy text kèm confidence từng dòng.
  3. Tạo block có `location.kind = "pdf_page"` và `ocr: {engine, version, mean_confidence}`.
  4. Dòng có confidence dưới ngưỡng (ví dụ 60) vẫn giữ, nhưng gắn cảnh báo.
- **Giới hạn:**
  - Timeout mỗi trang (ví dụ 20 s) và tổng thời gian cho cả tài liệu.
  - Tối đa N trang OCR mỗi tài liệu, ví dụ 30; vượt quá thì `document_limit_exceeded`.
- **Cấu hình:** `OCR_ENABLED=false` mặc định. Bật thì cần engine và gói ngôn ngữ có sẵn; thiếu thì worker báo lỗi cấu hình rõ ràng, **không** tải xuống tự động.
- **Version:**
  - Parser version thêm hậu tố OCR và engine version.
  - Tài liệu `needs_ocr` cũ cần thao tác "Xử lý lại" (admin retry) sau khi bật OCR. Không tự xử lý lại hàng loạt.
- **UI:** badge "Có phần nhận dạng tự động (OCR)" trên tài liệu và trên trích dẫn; panel nguồn hiện confidence.

## Task

### T1 — Spike đo chất lượng OCR (không đổi code chính)

- Chạy Tesseract trên các tài liệu scan của corpus v2.
- Đo tỉ lệ lỗi ký tự (CER) so với text gốc từ seed, và thời gian mỗi trang trên máy dev.
- Dừng lại để người dùng quyết định có đi tiếp không, với ngưỡng gì.

### T2 — Tích hợp parser OCR

- **Test:** PDF scan ra block OCR có location đúng trang; timeout từng trang hoạt động; OCR tắt thì vẫn ra `needs_ocr`; thiếu engine thì báo lỗi cấu hình.

### T3 — UI nhãn OCR (cần xác nhận UI)

### T4 — Eval slice `scan`

- Chạy hồi quy retrieval; chạy answering eval nếu được duyệt ngân sách.
- Report so sánh slice `scan` với `text`.

## Không làm

- OCR chữ viết tay.
- Nhận dạng bố cục phức tạp hoặc bảng trong ảnh.
- Gọi dịch vụ OCR trả phí hoặc dịch vụ cloud bên ngoài (vấn đề quyền riêng tư dữ liệu).
