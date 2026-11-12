# Final held-out — lượt được duyệt ngày 11/11/2026

**Cập nhật12/11:** [continuation22câu](final-continuation-20261112.md) đã hoàn thành cùng productionprotocol và allowance gốc. Composite hai phiên30attempted/29outputs/1q023failed/0notattempted, tổng30generation/210count. [Bộ cần chấm mới29outputs](human-review-guide.md) thay packet7outputs cho công việc tiếp theo. Các counts/ledger8/56 và trạng thái22chưa chạy bên dưới là snapshot bất biến của lượt11/11; SQLite parent hiện được nối thêm reservations, không reset. Không sửa snapshot cũ thành số tổng hoặc retry q023.

## Phạm vi và mốc trước chạy

Người dùng xác nhận thực hiện pacing và30 câu held-out, trần **60 generateContent +210 countTokens**, ngân sách **0 USD**. Không billing/paid fallback/download/UI/commit/push. Người dùng cung cấp dòng AI Studio cho Gemini3.5FlashLite:0/15RPM,0/250K inputTPM,0/500RPD và xác nhận chưa gắn billing/thẻ/phương thức thanh toán. Đây là xác nhận do người dùng cung cấp; không giả thành truy vấn billing/quota độc lập từ Google. Chi phí invoice chưa xác minh.

Candidate `.cache/final-reviewed-baseline-20261111-paced/`, protocol `1340f78f14f054fc63196e983c5cd876939f52534d999f663cdffe8257ae4b3d`, **100 files +4 extras** verify trên source/archive. Hai candidate cũ giữ nguyên archive. Source backend/model/prompt, corpus reviewed và mapping không đổi; chỉ runner, pacing, config eval và tests. Prepare vẫn hash/copy câu hỏi như bytes, không decode test. Approval riêng gắn đúng request-plan, template gốc vẫn pending; grant/ledger chỉ tạo khi execute. Sau gate mới load30 câu và chạy theo thứ tự snapshot, không chọn câu dễ/tune prompt từ test.

Preflight: config/prompt/index cache khớp, không inference/download; PostgreSQL `*_final_test` rỗng/migration20261103_rag04 và Qdrant healthy. TLS handshake với Google có kiểm chứng certificate đã đạt ngoài sandbox; không gửi HTTP/key/prompt trong probe. Không request warmup/model nào trước lượt capture.

## Điều tiết tốc độ

[Pacer](../eval/final_pacing.py) dùng chung toàn scope và can thiệp ngay trước native HTTP dispatch, không thay Gemini bằng mock. Giới hạn12request/61giây, khoảng cách tối thiểu5,1s, tính cả count/generate một cách bảo thủ. Generation dự phòng40.000 input tokens/request, tối đa200.000/61giây; context window app32.768 và output reserve vẫn giữ. Dự phòng có headroom cho schema/overhead; nếu usage prompt thực tế vượt40.000 thì dừng run, không coi dự phòng là số token đã đo. Không kiểm soát client khác cùng project hoặc bảo đảm nhà cung cấp luôn còn quota.

Ledger reserve trước provider, pacer reserve trước send. Chờ rate limit dùng async sleep bên trong timeout HTTP hiện có; không nới deadline150s/query hoặc120s/call, không thêm retry. Request thất bại giữ reservation. Receipt `execution/pacing.jsonl` chỉ action/elapsed/wait/token reservation, flush trước send; không prompt/headers/key. SQLite ledger vẫn là nguồn bền vững cho hard caps, không biến JSONL thành distributed transaction.

Pacer giữ SSL verification bằng certifi CA bundle, dùng context nạp từ memory để tránh lặp native cafile load chậm trên Windows; không verify=False. DB native dùng127.0.0.1 khi test URL là localhost; không sửa `.env` hoặc dev DB. [Runner](../eval/final_runner.py) vẫn auth/worker/retrieval/canonical capture production trên collection/storage riêng.

Các lựa chọn khác: chỉ nghỉ giữa câu không chặn burst repair; chỉ dựa ngày500RPD không xử lý RPM/TPM; đổi model/prompt sau xem test sẽ làm sai protocol. Chọn pacer bảo thủ và chấp nhận lượt chạy lâu hơn. CountTokens có quota riêng theo các giải thích Google nhưng tài liệu FAQ/API và forum chưa đồng nhất về tên GetTokens/countTokens và schema coverage; không dùng điều đó để bỏ giới hạn count trong lượt này.

Nguồn đã tra ngày11/11: [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), [billing](https://ai.google.dev/gemini-api/docs/billing), [token counting](https://ai.google.dev/gemini-api/docs/tokens), [pricing model](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite). Ngân sách/manual flags không phải billing cap phía Google.

## Kiểm chứng trước capture

- 155 regression tests đạt; 8 pacing tests cuối đạt ở lượt riêng, trong đó 7 đã có trong suite 155. Không cộng thành 163 tests độc lập. SQL/Qdrant suite riêng 5 tests đạt. Mỗi suite regression/SQL có warning Starlette/httpx baseline; Ruff check/format 4 file đạt.
- Tests dùng đồng hồ giả/mock HTTP: spacing, rolling request/token caps, biên số thực, không reserve khi đang chờ, cancellation trước send thứ hai, transport failure không hoàn reservation, usage vượt dự phòng và TLS/scope/restoration. SQL dùng corpus tạm/inference giả, không đọc held-out.
- Lượt unit đầu 1 failed/23 passed bắt lỗi biên float; thêm buffer 1 ms tại expiry và regression. Lượt gộp offline+SQL bị guard cấm mạng/cấm constructor chồng phạm vi: 20 failed/140 passed/5 errors, không gọi model nhưng để lại 5 identities chưa dùng. Cleanup chỉ các identities đã xác minh thời điểm tạo/username/không documents/không reservations; giữ summaries lỗi. Sau đó chạy suites ở process riêng, không bỏ guard.
- Preflight đầu gặp identities của suite lỗi; lần kế chạy trùng SQL suite đang hoạt động nên không được dùng làm bằng chứng rỗng. Preflight cuối sau SQL suite đã kết thúc đạt. Sandbox chặn socket Google bằng PermissionError; TLS probe retry đúng quyền ngoài sandbox đạt.

Artifacts `.cache/final-live-validation-20261111/`: `unit-01.txt`, `checks-02.txt`, `failed-suite-cleanup.json`, `regression-03.txt`, `pacing-final.txt`, `sql-04.txt`, `preflight.json`, `preflight-03.txt`, `candidate.json`, `live-run.txt`. Giữ toàn bộ lỗi lịch sử, không reset run/ledger.

## Trạng thái lượt capture

**Lượt đã kết thúc, chưa hoàn tất bộ 30 câu.** Runner dừng ở q023 khi native `generateContent` nhận **HTTP 503**; API trả `model_unavailable`. Không có HTTP429 trong lượt này. Google mô tả503 là dịch vụ tạm quá tải/không khả dụng; không có raw provider body nên chưa kết luận nguyên nhân cụ thể. Không quy lỗi cho quota chỉ từ trạng thái503. [Tham chiếu HTTP errors](https://ai.google.dev/gemini-api/docs/api-errors).

| Số đo | Kết quả | Diễn giải |
|---|---:|---|
| Planned | 30 | Toàn bộ split test, giữ nguyên mẫu số |
| Attempted | 8 | q016–q023 theo thứ tự snapshot |
| Thành công kỹ thuật | 7 | HTTP200, structured output hợp lệ; cả7 có status grounded, chưa phải correctness |
| Lỗi kỹ thuật | 1 | q023, generation HTTP503; retrieval và7count trước đó hoàn tất |
| Not attempted | 22 | q024–q045, không biến thành câu abstention hoặc loại khỏi mẫu số |
| Error rate trên attempted | 1/8 =12,5% | Không phải error rate của30 lần gọi hoàn chỉnh |
| Model actions | 8generation +56count | Dưới trần60/210; ledger và actual dispatch khớp |
| Native HTTP | 63status200 +1status503 | 56count200,7generation200,1generation503; không repair/retry |
| Pacing thực tế | min gap5.109ms; peak12requests/61s | Peak input reservation80.000/61s; receipt rolling checks đạt |
| Tổng pacing wait | 267.379ms | Có trong end-to-end query latency |
| Latency7queries thành công | p50≈38,67s; p95 nearest-rank≈40,51s | Pacing +local retrieval +count/generate network; không phải latency LLM thuần/SLA |
| Retrieval8queries | p50≈602,50ms; p95≈634,98ms | Có query embedding, index/model đã warm từ ingestion |
| Usage trả về từ7generation200 | input6.218 /candidate721 /total6.939tokens | Không có usage cho generation503; không suy ra invoice bằng0 |
| Human review mới | 0/7 | Correctness/faithfulness/citation metrics còn null |

Ở8retrievals đã hoàn tất, Recall@5/MRR@5 đều1,0; đây là diagnostics trên8câu answerable đầu tiên, không phải kết quả toàn held-out. Strict Recall@5 trên26answerable dự kiến là8/26≈0,3077 vì18answerable chưa chạy đóng góp0; phản ánh coverage thiếu, không tự diễn giải là chất lượng retrieval31%. Capture chỉ production top5: cột@10 generic của aggregator dùng cùng danh sách5hits, không chứng minh đã retrieve/evaluate10hits. Bốn unanswerable chưa được chạy; không có cơ sở kết luận abstention quality cuối. Không công bố accuracy100% từ7grounded outputs.

Ingestion10documents (PDF/DOCX/TXT/MD) và canonical mapping đạt. Job đầu ghi embedding47.598,678ms, các job sau dùng process/model đã nạp; không xem đây là đo cold boot toàn máy. Chưa đo oracle/context/no-context ablation, ba lượt lặp/query hoặc concurrent load trong đợt này.

Process exit code **0** chỉ xác nhận orchestration đã xuất artifacts/cleanup; manifest status **incomplete**, không phải benchmark pass. Giữ nguyên source/runner sau khi nhìn test; không sửa exit behavior hoặc prompt để làm lượt này đạt. Cần đọc manifest/coverage khi nghiệm thu tự động, không chỉ shell exit.

Run `offline_replay_8a31dc4aed934244922e060f6c900063`: evaluator là offline replay của **capture API native thật**, không phải fake inference. Provenance flag độc lập trong manifest vẫn false; audit kỹ thuật không được biến thành third-party attestation. Capture SHA-256 `f05ecad5e0ec60509e2b982c41a533629da76b6bca82bc4dc0b73dfac4196bcf`, per-question SHA-256 `f9ba364992887651e121d0bb1bc76b57573e63253a56414cd0fc190a49ce8a65`.

- Metrics gốc (`.cache/final-reviewed-baseline-20261111-paced/execution/evaluation/metrics.json`, chỉ lưu ở máy local), summary (`.cache/final-reviewed-baseline-20261111-paced/execution/summary.json`, chỉ lưu ở máy local), final audit (`.cache/final-live-validation-20261111/final-audit.json`, chỉ lưu ở máy local): nguồn counts/coverage/usage/hash; không ghi đè rescore vào report gốc.
- Storage audit độc lập (`.cache/final-live-validation-20261111/postrun-storage-audit.json`, chỉ lưu ở máy local):12bảng fixture0rows,0final_collections,0ownedcanonicalfiles. DB/schema/containers/artifacts và ledger giữ lại.
- Worksheet mới (`.cache/final-heldout-review-20261111/worksheet.md`, chỉ lưu ở máy local), phiếu A (`.cache/final-heldout-review-20261111/reviewer-a.json`, chỉ lưu ở máy local), phiếu B (`.cache/final-heldout-review-20261111/reviewer-b.json`, chỉ lưu ở máy local):7outputs để hai người chấm độc lập, toàn bộ điểm/reviewer mới null. Binding còn giữ1failed+22not_attempted. Hai phiếu thực hành6câu trước không bị sửa hoặc dùng thay phiếu này.

## Bước tiếp theo sau đợt này

Nhóm chấm7outputs đã có. Với22câu chưa chạy, cần thiết kế/kiểm chứng continuation riêng, giữ global allowance và mọi reservation cũ; runner hiện one-shot, không hỗ trợ resume tự động. Không xóa execution hoặc tạo runID mới để reset60/210. Chỉ22câu chưa chạy cần dự toán44generation/154count, có thể nằm trong phần allowance chưa dùng nếu một thiết kế ledger cha/con mới được xác minh và duyệt. Đây là đề xuất, chưa có code/approval thực thi continuation. q023 đã tiêu7count/1generation và vẫn là failed của lượt gốc; không âm thầm retry rồi đổi thành pass. Không dùng bất kỳ output test nào để tune model/prompt rồi tiếp tục gọi kết quả là holdout chưa dùng.

Đã hoàn thành pacing, một lần thực thi, xuất evidence/phiếu và cleanup theo phạm vi; **final30/full acceptance/Bước11–12 chưa hoàn tất**. Tiến độ giữ **87,3% /100%**, chưa ghi thêm đầu việc final đã đạt từ lượt thiếu coverage/human review.
