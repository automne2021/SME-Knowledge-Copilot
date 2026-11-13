# 04 — Retrieval nhận biết bảng biểu

**Mốc:** M3 · **Công sức:** M · **Phụ thuộc:** 01 (cần slice `table`) · **Nhánh:** `feat/04-table-aware`

## Mục tiêu

Trả lời đúng các câu hỏi có đáp án nằm trong bảng (bảng giá, định mức, ma trận phê duyệt), và trích dẫn tới đúng hàng.

## Giá trị với nhà tuyển dụng

Tài liệu doanh nghiệp Việt Nam dùng bảng rất nhiều. Câu chuyện có số đo trước và sau cho slice `table` là bằng chứng xử lý dữ liệu thật, không chỉ văn bản sạch.

## Hiện trạng (Codex đọc code để xác nhận trước khi làm)

- `backend/app/services/parsing.py` đã có:
  - PDF: bảng kẻ khung (`find_tables(strategy="lines_strict")`), giữ header và từng hàng kèm bbox và số thứ tự bảng.
  - DOCX: block `docx_table`.
- Chưa biết chất lượng thực tế vì bộ eval v1 **không có** câu nào có gold nằm trong bảng.
- Chunker (`chunking.py`) có vai trò `context` cho header lặp lại (K-046), nhưng chưa xác minh với hàng bảng.

## Thiết kế

- **Trước khi sửa, đo:** chạy hồi quy trên slice `table` của `dev2`, rồi phân tích từng câu trượt. Câu trượt do chunk thiếu header, do hàng bị cắt ngang, hay do embedding kém với dạng "a | b | c"?
- **Hướng cải thiện (chỉ làm hướng nào phân tích lỗi chỉ ra):**
  1. Mỗi hàng bảng thành một đoạn văn tự nhiên, kèm tên cột. Ví dụ: "Bảng định mức công tác phí — Chức danh: Trưởng phòng; Tiền ăn: 200.000 đồng/ngày". Giữ span gốc để trích dẫn.
  2. Lặp lại tiêu đề bảng hoặc caption trong phần `context` của mỗi chunk thuộc bảng.
  3. Không gộp hàng của hai bảng khác nhau vào một chunk.
- **Đổi định dạng text đưa vào embedding là đổi parser hoặc chunker version.** Cần tăng version, reindex trên DB test và ghi fingerprint mới. Không âm thầm đổi index đang dùng.
- **Hiển thị:** `sourceLocation` trên UI hiện "Bảng 2, hàng 3"; panel nguồn hiển thị hàng dưới dạng bảng nhỏ (text đã escape, không render HTML).

## Task

### T1 — Phân tích lỗi trên slice `table`

- Chỉ đọc và đo. Report ghi từng câu trượt và nguyên nhân. Dừng lại để người dùng chọn hướng sửa.

### T2 — Cải thiện chunk bảng theo hướng đã chọn

- Tăng version, kèm migration nếu đổi schema.
- **Test:**
  - Span của hàng vẫn round-trip về đúng block gốc.
  - Header không bị đếm vào phần content.
  - Bảng dài vẫn tôn trọng giới hạn 350 token.
- Chạy hồi quy trước và sau trên `dev2`; chạy `test2` một lần khi chốt.

### T3 — Hiển thị trích dẫn bảng trên UI (cần xác nhận UI)

- **Test frontend:** location bảng hiển thị đúng; nội dung ô có ký tự HTML vẫn là text.

## Không làm

- Không dùng model layout hay vision cho bảng phức tạp (ô gộp, bảng không kẻ khung). Ghi vào giới hạn.
- Không OCR bảng trong ảnh (thuộc 08).
