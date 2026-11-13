# 10 — Provider LLM thay thế và so sánh bằng eval

**Mốc:** M4 · **Công sức:** L · **Phụ thuộc:** 01 · **Nhánh:** `feat/10-llm-provider`

## Mục tiêu

Tách adapter LLM để chạy được một provider thứ hai qua giao thức **OpenAI-compatible**:
- Ollama hoặc llama.cpp server chạy local, hoặc một endpoint tự host.
- Nhóm model ứng viên: Qwen2.5 cỡ nhỏ, SeaLLM, Vistral, hoặc model tiếng Việt khác đủ chạy trên máy.

Sau đó so sánh với Gemini bằng **cùng** bộ eval, cùng prompt và cùng schema.

## Giá trị với nhà tuyển dụng

- Thể hiện khả năng đánh giá model cho tiếng Việt và ra quyết định dựa trên số liệu (chất lượng, độ trễ, chi phí, quyền riêng tư dữ liệu).
- VNG có hạ tầng GPU và hệ sinh thái AI riêng, nên "chạy được model tự host khi dữ liệu không được rời công ty" là luận điểm có giá trị.

## Hiện trạng

- `services/gemini.py` gọi native API, có các guard:
  - Model và base URL cố định.
  - Hai cờ xác nhận free tier.
  - Timeout cứng 60 s mỗi lời gọi.
  - Phân loại lỗi theo `details.reason` (K-105).
- `chat.py` nhận `provider_factory`; `SourceCheckedProvider` kiểm tra lại nguồn trước mỗi lời gọi (K-069).
- Context budget dùng `countTokens` của Gemini (K-062). Provider khác không có API này.

## Thiết kế

- **Interface:** `LLMProvider` gồm `count_tokens(payload, deadline)` và `generate(payload, deadline)`. Gemini adapter giữ nguyên hành vi.
- **Adapter OpenAI-compatible:**
  - Endpoint `/v1/chat/completions` với `response_format` JSON schema, nếu server hỗ trợ.
  - Server không hỗ trợ JSON schema thì dùng JSON mode và kiểm tra như cũ; output sai vẫn đi qua nhánh repair 1 lần.
- **Đếm token:** dùng tokenizer của chính model (file tokenizer local, pin revision), cộng margin an toàn. Không được dùng tokenizer E5 (K-062).
- **Cấu hình:**
  - `LLM_PROVIDER=gemini|openai_compatible`, `LLM_COMPAT_BASE_URL` (chỉ loopback hoặc allowlist), `LLM_COMPAT_MODEL`.
  - Không có key trả phí; preflight từ chối URL không nằm trong allowlist.
- **Fingerprint:** `config_json` của run lưu provider, model, revision và prompt version. Cache eval và kết quả của từng provider không được trộn lẫn.
- **Phần cứng:**
  - Máy dev là CPU, RAM 16 GB. Model 7B lượng tử 4-bit chạy CPU có thể chỉ được vài token/giây, nên 800 token output mất vài phút.
  - Nên ưu tiên model 1,5–3B, hoặc mượn GPU nếu có.
  - Report **phải** ghi phần cứng.

## Task

### T1 — Tách interface, Gemini không đổi hành vi

- **Test:** toàn bộ test Gemini cũ đạt; provider giả mới dùng interface.

### T2 — Adapter OpenAI-compatible với server giả

- **Test:** dùng `httpx.MockTransport`. Phải chứng minh:
  - JSON hợp lệ được nhận đúng.
  - Output sai đi qua nhánh repair 1 lần.
  - Timeout được tôn trọng.
  - URL ngoài allowlist bị từ chối.
  - Không retry.

### T3 — Smoke với model local thật (cần duyệt tải model)

- 3–5 câu dev; đo tốc độ, RAM và tỉ lệ output hợp lệ.

### T4 — Eval so sánh trên `dev2` và `test2`

- Bảng gồm: strict success, faithfulness theo người chấm, citation đúng, abstention đúng, p50/p95 latency, chi phí.
- **Không** đổi provider mặc định khi chưa được người dùng duyệt dựa trên số liệu.

## Không làm

- Fine-tune model.
- Dùng API trả phí.
- Tự động fallback sang provider khác khi provider chính lỗi. Việc này đổi hành vi "lỗi phải là lỗi" và làm trộn kết quả eval.
