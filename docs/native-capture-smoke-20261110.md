# Native capture smoke — 10/11/2026

Phạm vi được duyệt: runner/tests/report, hai câu tổng hợp với E5 cache + Gemini thật; tối đa **4 generateContent +14 countTokens** toàn đợt, gồm repair, ngân sách **0 USD**, cập nhật PLAN/KNOWLEDGE. Không sửa UI, `.env`, dependencies, tải weights/images, mở reviewed held-out, bật billing/paid fallback, commit/push. Không chạy lại câu lỗi để che kết quả.

## Runner và provenance

[Runner](../eval/run_capture_smoke.py) dùng scope cố định `native-dev-smoke-20261110`, tạo thư mục mới bằng exclusive mkdir; lần chạy lại bị chặn, không nhận CLI scope/output/caps mới. Một SQLite ledger cấp 4/14 tổng, chia hai batches 2/7 mỗi câu, reserve trước transport, không refund. API capture khóa câu hỏi/user/workspace/filter/top-k và actual final context, native provider không retry/fallback. Khi query lỗi kỹ thuật, dừng trước câu tiếp theo, giữ failed/not_attempted trong denominator. Không gửi warmup LLM hoặc request kiểm key riêng.

Preflight không HTTP: native Gemini constructor kiểm endpoint/model/key + hai cờ manual; guard local test DB khác dev và Qdrant local; frozen E5 profile dùng local_files_only. Model hiện cấu hình `gemini-3.5-flash-lite`, E5-small revision pin, index `9851b494ba14e5a4370604ac33064d65b40690b990118fce057e4fbcb5afc4a4`. Giá/input-output free tier được đối chiếu [Google pricing](https://ai.google.dev/gemini-api/docs/pricing); quota phụ thuộc project theo [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). Dựa trên flags thủ công và xác nhận người dùng đã lưu; không có quyền quản trị tài khoản để xác minh billing/quota độc lập. Request caps local không phải billing cap phía Google. Không ghi chi phí hóa đơn đã xác minh bằng 0; trường đó vẫn null.

Synthetic policy tiếng Việt chỉ quy định thời hạn/hồ sơ hoàn ứng, không có số ngày nghỉ phép. Hai câu hỏi là thời hạn/hồ sơ hoàn ứng (answerable) và số ngày nghỉ phép năm (unanswerable). Gold là runner-defined, không gọi là nhãn người chấm. [Toolkit](../eval/final_eval.py) thêm opt-in `synthetic_smoke` riêng: chỉ hai câu dev, một answerable/một abstention, CSV `synthetic_fixture` không tên người; không đi qua held-out kể cả allow-heldout. Mặc định reviewed vẫn giữ yêu cầu hai annotator/reviewer độc lập đã approve.

Parser/chunker/tokenizer thật lập canonical mapping trước ingestion, freeze hashes của corpus/config/mapping và Python sources hiện hữu trong backend/app + eval top-level. Giữ HEAD + dirty status, không tự commit. Config lưu model/context/timeouts/budgets/retrieval; profile giữ weight hashes/package versions, không cache path/key/DSN. Query dùng production auth, SQL/Qdrant, worker và LocalEmbedder thật, SourceCheckedProvider và SqlCanonicalSources; origin captured_api mô tả native transport, **không biến synthetic corpus thành held-out benchmark**. Human worksheet vẫn pending.

## Cô lập và môi trường

DB riêng `copilot_smoke_test` được suy và guard lại từ TEST_DATABASE_URL, có advisory lock và check queue rỗng; không cùng queue DB dev hoặc tests/integration cũ. Collection `final_<grant fingerprint prefix>`, storage trong backend/.cache/final-capture theo đúng SQL adapter contract. Cleanup giới hạn workspace/user/token/document/query IDs và collection/file của scope; không drop DB/reset volume. Output capture/ledger/replay/report giữ lại.

Bootstrap [scripts/run-capture-smoke.py](../scripts/run-capture-smoke.py) dùng Python3.12.6 pgAdmin + packages hiện có. Đối với parser child embedded Python, chỉ bootstrap import paths; parser/process/timeout thật giữ nguyên. LocalEmbedder vẫn dùng subprocess spawn production. Không sửa interpreter hệ thống hoặc cài dependencies. HTTP diagnostics chỉ ghi action/status/error type của native endpoint, không headers/body/payload/thoughts. Usage lọc từ native adapter được lưu trong execution capture.

## Kiểm chứng

Trước live: 125 tests đạt (9 tests smoke mới +116 regression), sau bổ sung status diagnostics đạt 16 tests (10 smoke +6 SQL integration), và 10 smoke tests cuối đạt sau khi bổ sung config/load-time metadata; mỗi nhóm dùng basetemp mới. Ruff check/format bốn Python files đạt. Lượt unit đầu có 3 assertion sai vì AppError.code không nằm trong str(error); guard đã chặn đúng, sửa test đọc thuộc tính code. Không sửa production guard để làm tests pass.

Các lượt kiểm thử phủ 132 tests khác nhau: 10 smoke guards/metadata +116 regression +6 SQL integration, không cộng các lượt chạy lại thành số tests mới. Logs kiểm thử: `.cache/native-smoke-validation-20261110/` (`unit-regression.txt`, `smoke-and-sql.txt`, `smoke-final.txt`). Basetemp tương ứng native-smoke-unit-r2/r3 và native-smoke-integration-r1 có ngày20261110 trong tên; không dùng lại basetemp cũ.

## Kết quả native thực tế

Lượt duy nhất từ **22:27:06 đến 22:28:45, 10/11/2026 (UTC+7)**, status completed. Một document/một chunk được ingest bằng E5 thật; model load khoảng 45,13s, parse/chunk 381,82ms, bước embedding 45.371,24ms gồm load, trước publish khoảng 47,98s. Không so các số này với latency API câu hỏi.

| Câu tổng hợp | HTTP / answer status | Quan sát output | API pipeline latency |
|---|---|---|---:|
| Thời hạn và hồ sơ hoàn ứng | 200 / grounded | Hai claims: trong 30 ngày từ khi kết thúc chuyến đi; hóa đơn và xác nhận quản lý. Cùng tham chiếu E1, backend tạo 1 citation | 7.019,732ms |
| Số ngày nghỉ phép năm | 200 / insufficient_evidence | Claims rỗng, 0 citation; vẫn retrieve và đưa 1 chunk vào context nên đây là model abstention, không phải shortcut no-hits | 16.699,936ms |

Đây là quan sát output/contract, chưa phải điểm human correctness/faithfulness. Hai worksheet entries vẫn pending; correctness_mean/faithfulness/citation metrics/strict human success đều null. Chỉ hai mẫu tổng hợp, không công bố accuracy hay p50/p95 ổn định từ chúng.

Ledger ghi **2 generateContent +6 countTokens**, mỗi câu 1 generation +3 count, không repair/retry. Native HTTP diagnostics có đúng 8 events, cả 8 HTTP200; grant cap 4/14 không reset. Usage generation do provider trả: câu 1 prompt 412/output 144/total 556; câu 2 prompt 408/output 90/total 498 — tổng prompt 820/output 234/total 1.054 tokens. Không bao gồm countTokens response usage hoặc suy thoughts/cache tokens thiếu thành 0. Ngân sách 0 USD, invoice cost vẫn null, không bật billing/paid fallback.

Protocol hash `05372f86e1e21d4a921573cc37dab8d073f81d7a7659917241cb276aaba872a7`, capture hash `6011420aaaf12c2ff8386d59a1dcc74412dba1cb63e65e827938a30135358136`. Đối chiếu lại72 Python source hashes và inputs sau run đạt; capture origin captured_api, auth_override=false. Replay run `offline_replay_dbf3be9479df4bcea1d9a336ab5fd9c9` chỉ xử lý captures, không thêm model requests; không gọi nó là lượt inference thứ hai hoặc held-out acceptance.

Cleanup trong runner hoàn tất; probe độc lập xác minh head `20261103_rag04`, cả 12 bảng fixture đều 0 rows, Qdrant còn 0 collections prefix `final_`, 0 scoped upload files và readyz 200. Ledger vẫn 2 generation/6 count. Kết quả probe lưu `cleanup.txt`. Giữ DB/schema, không giữ rows/token/doc test; giữ corpus tổng hợp/capture/protocol/ledger/evaluation trong `.cache/native-dev-smoke-20261110/`. Raw live log ở `.cache/native-smoke-validation-20261110/live.txt`; không sửa artifact sau capture hoặc gọi model lại để kiểm trạng thái.

Sau run đã tạo archive mới `frozen-root/` trong cùng output, sao chép nguyên 79 files đã được protocol hash (72 Python sources +7 inputs/config/mapping), kèm protocol riêng. Verify archive và evaluate lại hai captured rows hoàn toàn offline đạt; không tạo điểm human hoặc thêm provider calls. Archive giữ đường dẫn tương đối của protocol, có thể dùng làm root của replay sau khi source workspace thay đổi. Đây là thao tác lưu artifact đã thực hiện sau run, không phải tính năng tự động của CLI. Log `archive.txt`; rà 274 liên kết nội bộ trong năm tài liệu cập nhật không có target thiếu, Ruff và whitespace checks đạt.

## Phạm vi kết luận

Hai câu tổng hợp chỉ kiểm compatibility và đường đi end-to-end của API. Không dùng làm accuracy công khai/CV, chưa đo ổn định p50/p95/RAM, chưa human scoring hoặc benchmark corpus reviewed. Chưa browser E2E/delete/history/visual-keyboard QA, chưa đóng AT-R23 hoặc Bước11. **Tiến độ giữ 83,4% /100%** theo PLAN.
