# 12 — Quan sát hệ thống: trace câu hỏi và sổ quota

**Mốc:** M4 · **Công sức:** M · **Phụ thuộc:** 07 (dùng chung phần analytics) · **Nhánh:** `feat/12-observability`

## Mục tiêu

- Khi một câu trả lời sai, đội phát triển xem được trace để biết lỗi nằm ở retrieval, context packing hay model:
  - đã retrieve những gì, rank bao nhiêu;
  - context cuối cùng gồm những đoạn nào;
  - token và thời gian của từng bước;
  - đã repair hay chưa.
- Theo dõi lượng gọi Gemini so với quota free tier.

## Giá trị với nhà tuyển dụng

Debug một hệ thống RAG phải dựa trên dữ liệu thật, không đoán. "Trang inspector" là một demo kỹ thuật tốt khi phỏng vấn: mở một câu trả lời sai và chỉ ra ngay lỗi nằm ở tầng nào (khớp với phương pháp ở K-007 và K-066).

## Hiện trạng

- `query_runs.retrieval_trace_json` lưu ID, rank, `final_context_ids`, `evidence_map` (dạng ID, hash, span) và token. Prompt text **không** được lưu (K-069).
- `GET /chat/runs/{id}` chỉ trả kết quả đã kiểm tra, không trả trace (`resources.py` có comment "never private retrieval/config traces").
- Log của API chỉ có access log của uvicorn và các cảnh báo Gemini (K-105).

## Thiết kế

- **Inspector cho chủ phiên** (không phải admin, theo bất biến 1):
  - `GET /chat/runs/{id}/trace`, chỉ chủ phiên gọi được.
  - Trả về:
    - Danh sách hit gồm filename, location, rank dense / lexical / fused và trạng thái được chọn hay bị loại; lý do loại: `sql_rejected`, `budget_excluded`, `duplicate`.
    - Timings và token.
    - Số lần generate và repair.
  - Text của đoạn nguồn chỉ được đọc lại từ SQL nếu nguồn còn hợp lệ. Nguồn đã bị xóa thì chỉ hiện "đã xóa".
- **Bật/tắt:** inspector có thể bật hoặc tắt bằng cấu hình `TRACE_INSPECTOR_ENABLED`, mặc định bật ở môi trường dev.
- **Sổ quota:**
  - Bảng `provider_usage_daily` gồm workspace, ngày (theo giờ Pacific để khớp chu kỳ reset của Gemini), số `generateContent`, số `countTokens` và số token. Cập nhật trong cùng transaction với lúc publish hoặc fail của run.
  - Admin xem tổng hợp trên dashboard ở tính năng 07.
- **Log có cấu trúc:** log JSON kèm `request_id`, `run_id`, stage, thời gian và mã lỗi. Không log câu hỏi hay nội dung tài liệu.

## Task

### T1 — API trace cho chủ phiên

- **Test:** admin và người khác nhận 404; nguồn đã xóa không trả text; không có trường prompt nào trong response.

### T2 — Sổ quota

- **Test:** đếm đúng khi có repair; run lỗi vẫn được đếm theo số lời gọi đã thực sự gửi đi.

### T3 — UI inspector (cần xác nhận UI)

- Nút "Xem cách hệ thống tìm nguồn" dưới câu trả lời, mở panel hiện bảng hit và timeline.

## Không làm

- Tích hợp OpenTelemetry, Prometheus hay Grafana. Có thể thêm sau khi có 11; ghi vào hướng phát triển.
- Lưu prompt đầy đủ.
