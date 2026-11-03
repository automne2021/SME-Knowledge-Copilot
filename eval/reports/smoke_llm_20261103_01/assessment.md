# Đánh giá bổ sung cho smoke LLM đầu tiên

Run nguyên gốc trong thư mục này giữ nguyên manifest/config/metrics/per_input. Báo cáo bổ sung được viết sau khi đọc kết quả, không thay kết quả `failed` thành `passed`.

- API calls attempted: **5**, đúng giới hạn đợt ban đầu; không retry hoặc fallback.
- Model version trên 4 outputs hợp lệ: `gemini-3.5-flash-lite`.
- q001, q007, q009: `grounded`, schema và citation-ID whitelist hợp lệ.
- q014: `insufficient_evidence`, claims rỗng, nêu thiếu chính sách năm 2030.
- Case `adhoc_conflict_not_human_gold`: `technical_error / invalid_provider_output`.

Đối chiếu bằng trợ lý: các claims của ba câu grounded khớp gold quotes đã được con người duyệt; q014 đúng hành vi thiếu nguồn. Đây là kiểm tra định tính bởi trợ lý, không là independent human scoring của outputs hoặc benchmark accuracy. Case conflict tự soạn không thuộc human gold 45 câu.

Lỗi conflict xảy ra sau HTTP 200 theo đường code adapter v1, nhưng exception gộp lỗi JSON/schema/contract thành một mã. Raw response và usage/model metadata của case lỗi không được lưu. Vì vậy **chưa xác định chính xác nguyên nhân**, không khẳng định do model bịa, thiếu trường hay sai citation ID. Không khôi phục response/usage bằng suy đoán.

Usage đã lưu của **4/5 calls**: prompt 529 tokens, candidate output 376, tổng 905. Usage call thứ 5 không biết; tổng cả 5 là null, không báo 905 như tổng run. Không thấy thoughtsTokenCount không chứng minh model không dùng thinking. `serviceTier=standard` là inference service metadata, không là bằng chứng billing tier Free. `api_cost_usd=null`: project Free dựa trên ảnh/xác nhận người dùng, chưa có chứng từ billing để kết luận hóa đơn.

Thời gian 5 calls: khoảng 1,61 / 1,32 / 1,51 / 1,38 / 1,09 giây; quy mô này chưa đủ p95/SLA.

Sau run: thêm diagnostics chỉ lưu code/types và usage/model metadata được allowlist, không lưu provider body/headers, Pydantic inputs hoặc thoughts. Prompt v2 nêu rõ invariants grounded/partial/missing_evidence; trước đó prompt chưa nhắc partial phải khai báo missing evidence, nhưng chưa đủ dữ liệu để kết luận đây là nguyên nhân case lỗi. Thêm CLI `--case-id` để retest đúng một case, thay vì gọi lại cả 5.

Kiểm thử offline sau thay đổi: **68 passed**, Ruff đạt. Sau đó người dùng đã xác nhận thêm đúng 1 request; [retest conflict riêng](../smoke_llm_conflict_20261103_02/assessment.md) đạt 1/1, không chạy lại cả 5. Thêm guard max_calls sau đó đưa suite lên 72 cases, không gọi thêm API. Các sửa code/prompt không thay fingerprint hoặc kết quả lịch sử của run v1.
