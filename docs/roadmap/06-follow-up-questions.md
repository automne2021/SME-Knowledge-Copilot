# 06 — Hỏi nối tiếp có retrieval lại

**Mốc:** M3 · **Công sức:** M · **Phụ thuộc:** 01 (slice `follow_up`) · **Nhánh:** `feat/06-follow-up`

## Mục tiêu

Người dùng hỏi kiểu hội thoại: "Còn với hợp đồng dưới 100 triệu thì sao?". Hệ thống viết lại thành câu hỏi độc lập, rồi retrieve lại từ tài liệu. Câu trả lời cũ **không** được dùng làm nguồn.

## Giá trị với nhà tuyển dụng

Đây là tính năng chatbot người dùng mong đợi nhất. Phần kỹ thuật đáng kể khi phỏng vấn:
- Không nhét lịch sử chat vào context, vì như vậy câu trả lời có thể lấy từ câu trả lời cũ thay vì từ tài liệu.
- Tách bước "viết lại câu hỏi" ra để đo riêng.

## Hiện trạng

- Mỗi câu hỏi được trả lời độc lập (spec mục 8.8). UI nhắc người dùng ghi đủ ngữ cảnh.
- Có test bảo đảm lịch sử không lọt vào payload gửi model (K-098).
- Spec mục 8.8 đã mô tả hướng P1: viết lại câu hỏi từ lịch sử có giới hạn, lưu cả câu gốc lẫn câu đã viết lại, retrieve lại và kiểm tra quyền hiện tại.

## Thiết kế

- **Phát hiện câu cần viết lại:** heuristic rẻ trước: đại từ hoặc từ nối ("đó", "này", "thế còn", "còn … thì sao", "vậy"), câu quá ngắn, hoặc không có danh từ riêng hay mã. Chỉ những câu này mới gọi LLM viết lại, để tiết kiệm quota.
- **Viết lại câu hỏi:**
  - Một lời gọi Gemini với prompt riêng `rewrite-v1`.
  - Đầu vào **chỉ** gồm tối đa 3 cặp câu hỏi gần nhất của phiên. Có thể kèm tóm tắt claim của câu trả lời trước, nhưng chỉ phần text claim, không kèm nguồn. Giới hạn khoảng 1.000 token.
  - Output JSON `{standalone_question, changed: bool}`, kiểm tra như output trả lời. Lỗi hoặc timeout thì **báo lỗi kỹ thuật**, không lặng lẽ dùng câu gốc.
- **Lưu vết:**
  - `query_runs` thêm `rewritten_question` (nullable) và `rewrite_source_run_ids`.
  - UI hiện "Đã hiểu câu hỏi là: …" để người dùng kiểm tra.
- **Retrieval và answering** dùng câu đã viết lại. Câu gốc vẫn hiện trong lịch sử.
- **Quyền và xóa:**
  - Nếu một câu trả lời trước đã bị che vì nguồn bị xóa, nội dung của nó **không** được đưa vào prompt viết lại; chỉ dùng câu hỏi của người dùng.
  - Chủ phiên xóa cuộc trò chuyện thì các trường mới bị xóa theo.
- **Ngân sách:** mỗi câu nối tiếp tốn thêm 1 generate và 1 countTokens. Ghi rõ trong report.

## Task

### T1 — Heuristic phát hiện và prompt viết lại (offline)

- Test với provider giả: câu độc lập không gọi viết lại; câu có đại từ thì gọi; output sai schema thì lỗi.
- Đo heuristic trên slice `follow_up` (precision và recall của bước phát hiện), không gọi model.

### T2 — Lưu vết và luồng chat

- Migration, `chat.query` và hash idempotency (hash theo câu gốc cộng thêm ID run làm ngữ cảnh).
- **Test:**
  - Lịch sử bị che không vào prompt.
  - Session của người khác không dùng được.
  - Payload trả lời vẫn không chứa câu trả lời cũ.

### T3 — UI hiện câu đã hiểu (cần xác nhận UI)

### T4 — Eval có ngân sách trên slice `follow_up`

- Đợt xác nhận riêng: nêu trước số lần gọi model.
- So sánh hai cách: trả lời độc lập (baseline) với viết lại rồi trả lời.

## Không làm

- Bộ nhớ dài hạn giữa các phiên.
- Agent tự quyết định retrieve nhiều vòng.
