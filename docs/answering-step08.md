# Bước 08 — RAG answering, citations và session

**Cập nhật sau Bước09:** runtime trace đã chuyển sang IDs/hash/spans và có source check trước mỗi count/generate/repair; delete/cleanup redaction tại [Bước09](deletion-privacy-step09.md). Nội dung/kết quả bên dưới mô tả mốc Bước08, các artifacts model giữ nguyên.

Ngày thực hiện: 04/11/2026. Người dùng xác nhận Bước08 và riêng tối đa10 generateContent +20 countTokens, free tier0USD. Phạm vi backend/eval/docs; không UI/delete workflow/commit/push hoặc tải weights.

**Hoàn thành phạm vi triển khai Bước08:** 276 backend +91 eval tests đạt ở hai suites riêng, Ruff check/format 108 files và pip check đạt. Năm ca synthetic dev có output validate/probes đạt qua hai runs; không phải5/5 trong một run, không phải answer accuracy hoặc held-out benchmark. Human review giữ pending. [Spec 8.3–8.8](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN](../PLAN.md), [KNOWLEDGE K-062–067](../KNOWLEDGE.md).

## Luồng đã triển khai

`POST /api/v1/chat/query`: owner auth → normalized input hash/idempotency → running/user message commit → dense search/SQL validation → whole-chunk context budget → cấp E1… → Gemini structured claims → validate/repair≤1 → source revalidation/locks → transaction assistant/citations/completed.

P0 không đưa lịch sử vào prompt; hỏi đủ chủ thể. Question sau trim1–4000 ký tự, vẫn phải vừa E5 query512 tokens. Filter tối đa50 UUID phân biệt, mode dense và top-k1–10 như search. Client không chọn model/collection/workspace hoặc gửi oracle evidence. Ví dụ, thay UUID bằng session thật từ POST /chat/sessions:

```json
{
  "session_id": "11111111-1111-4111-8111-111111111111",
  "client_request_id": "22222222-2222-4222-8222-222222222222",
  "question": "Nhân viên toàn thời gian có bao nhiêu ngày phép năm theo quy định mẫu?",
  "retrieval_mode": "dense",
  "top_k": 5,
  "filters": {"document_ids": []}
}
```

Response success có run/message IDs, answer_status, typed claims, limitations/missing_information, conflict_detected, backend citations, reason/timings và source_unavailable. Envelope vẫn `{data,request_id}`. GET /chat/runs/{id} trả status/result đã kiểm tra nguồn hiện tại. Session messages có nested `answer` cho assistant mới, không expose trace/config riêng tư.

## Context, model và budget

| Cấu hình | Baseline |
|---|---|
| Model | Gemini native `gemini-3.5-flash-lite`, không fallback |
| Token counter | Gemini countTokens trên full request |
| Evidence | 4000 tokens, whole chunks, E IDs sau budget |
| Output/thinking | maxOutputTokens800 tổng, thinking MINIMAL, không lưu thoughts |
| Context ceiling | App32768, margin256; không phải context tối đa model |
| Deadline | Query150s, mỗi HTTP call≤120s hoặc thời gian còn lại |
| Concurrency | Một running/session, hai pipeline LLM/app process; không đợi queue vô hạn |
| Repair | Tối đa1, cùng câu hỏi/map; không retry quota/mạng |

Những giá trị cấu hình mới có trong [.env.example](../.env.example); không ghi đè .env thật. Free-tier/quota flags mặc định false; cần xác nhận thủ công trước live calls. Native token counting thêm round trips và cùng dùng deadline/capacity. Budget tính cả system/question/wrappers/schema; bản repair được đếm trước, bản thường được kiểm tra lại. Trace lưu retrieved/final/excluded/cited IDs và source spans để phân biệt lỗi retrieval, packing, generation.

Không có ready/hits thì abstain mẫu cố định, không gọi provider. Có evidence nhưng thiếu hỗ trợ thì model có thể insufficient/partial. Conflict khai báo cần partial/≥2refs; backend không có semantic contradiction detector bảo đảm đúng. Schema/citation sai sau repair502; provider/quota503, timeout504, nguồn đổi409, capacity429. Không công bố lời giải thích tự do của model khi insufficient.

## Session, replay và nguồn đổi

Same client_request_id + cùng input replay; input khác409; running409 query_in_progress; ID mới trong session đang chạy409 session_busy. Failed run cần ID mới. GET run/query tiếp theo recovery running quá deadline; final publish không được hoàn tất run đã failed.

Không giữ SQL transaction trong model/network inference. Publish khóa documents rồi session/run, kiểm tra active revision/generation/lifecycle và text trước atomic commit. Mất commit acknowledgment trả lỗi DB, replay có thể tìm answer đã commit. Replay/GET/history không trả cached answer/citations nếu final-context source đã thay đổi hoặc citation unavailable. Đây là foundation chống stale source; delete/cleanup/redaction dữ liệu lưu lâu dài còn ở Bước09.

## Kiểm chứng và cách chạy

Backend tests dùng PostgreSQL/Qdrant thật, model/token counter giả lập được gắn nhãn; provider HTTP tests dùng MockTransport, không quota. Oracle helper chỉ trong eval. Lệnh dưới cần đợt đã được xác nhận, chạy riêng với worker/tests dùng cùng queue:

```powershell
# Từ root, sau regression và xác nhận riêng số request/free tier:
.\backend\.venv\Scripts\python.exe -B -m eval.run_answering_eval --live --case api_unknown --max-generation-calls 2 --max-count-tokens-calls 5

# Lint nhất quán với backend config:
.\backend\.venv\Scripts\ruff.exe check --config backend/pyproject.toml backend/app backend/tests backend/alembic eval
```

Smoke5 ca synthetic dev, không test holdout: oracle multi-source/missing condition/conflict và API injection/unknown. Manifest/config/ledger/source hashes/per-question/metrics/report được ghi vào run mới, không sửa reports cũ. Kết quả probes không phải accuracy; human review giữ pending đến khi người dùng đánh giá.

### Kết quả thực và lỗi dự toán budget

| Run | Kết quả | Requests thật |
|---|---|---|
| [Run đầu](../eval/reports/answering_dev_20261104T031918Z_fd3953b6/manifest.json) | 5 attempts:4 thành công,1 eval_budget_exhausted trước generation cuối; status failed, cleanup true | 4 generate +20 countTokens |
| [Retest riêng unknown](../eval/reports/answering_dev_20261104T032524Z_a2800bde/manifest.json) | 1/1 output validate/probes đạt, status completed, cleanup true | 1 generate +5 countTokens, dưới trần bổ sung2/5 được duyệt |

Run đầu: oracle multi-source dẫn E1/E2 với12 ngày/3 ngày làm việc; thiếu hạn chuyển phép dùng partial; mâu thuẫn12/14 dùng partial, dẫn cả hai và không chọn bản có hiệu lực. API injection trả support@example.invalid từ nguồn SQL; cả3 chunks, gồm payload độc hại, thực sự nằm trong final context; citation mở source API đúng. Retest API unknown trả mẫu insufficient_evidence, claims/citations rỗng. Đây là quan sát cụ thể, không chứng nhận model an toàn trên mọi injection hoặc mọi câu không có đáp án.

Nguyên nhân lỗi run đầu: dự toán dùng2 files→2 chunks, nhưng MD có heading chunk riêng nên thực tế3 chunks. Full protocol cần21 count calls, trong khi giới hạn20 đã chặn đúng request thứ21. Không có over-budget call. Sửa **runner eval**, giữ nguyên backend/prompt/model/config/cases: đếm chunks sau ingestion để tính upper bound trước live requests, hỗ trợ --case và per-run caps, ghi execution.json. Full protocol với cap20 hiện bị preflight từ chối trước model calls; cần chia batch và xác nhận quota riêng, không tự nâng trần. Retest chỉ ca cuối theo xác nhận bổ sung; tổng thực hai runs5 generate +25 countTokens. Test regression dùng parser/tokenizer thật tái hiện3 chunks, kiểm tra ledger/source hashes và giữ lỗi lịch sử.

Không gặp truncation/repair trong5 outputs model thật; repair/E99/budget exclusions được chứng minh bằng fixture tests. Tổng token usage của generation ở raw attempts/trace; count calls không có generation usage. Giữ max output800/thinking MINIMAL vì các ca này hoàn tất STOP; chưa có so sánh model hoặc output budget trên tập lớn. Timings của run gồm throttling5giây và nhiều count round trips, không dùng làm p50/p95 answering benchmark. Budget0USD dựa trên project free tier người dùng xác nhận; không xác minh hóa đơn hoặc thay billing.

**Hash lịch sử:** config_sha256 của hai manifests trỏ tới input bytes tại source_snapshot/eval__configs__answering.json.txt; config.json trong report được pretty-serialize nên bytes khác nhưng JSON tương đương. Test kiểm tra cả hai quan hệ, không sửa manifests/snapshots cũ. Runner hiện copy nguyên input bytes cho runs tương lai. Field cases_completed=5 của run đầu là5attempts theo runner cũ, trong đó technical_errors=1; runner mới phân biệt planned/attempted/succeeded.

## Giới hạn bàn giao

- Prompt instructions và validation không chứng minh semantic faithfulness hoặc miễn nhiễm injection. UI tương lai phải render text an toàn.
- Trace evidence text và citation snapshots là dữ liệu phải được xử lý khi xóa nguồn ở Bước09, không expose qua API config/debug.
- Chưa held-out benchmark, streaming, multi-turn rewrite, judge, delete workflow, UI hoặc Linux AI image test.
- Work/publication deadline có cleanup/SQL/OS overhead, không phải latency SLA150s tuyệt đối. Cần giới hạn phân tán nếu chạy nhiều API processes.
