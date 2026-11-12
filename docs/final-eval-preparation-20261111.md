# Bước 11 — chuẩn bị offline ngày 11/11/2026

**Cập nhật đợt tiếp cùng ngày:** [review sáu câu](human-review-practice-20261111.md) đã gộp/rescore6/6; [final runner SQL integration](final-runner-sql-20261111.md) đạt5tests +148regression. Candidate mặc định thay bằng `.cache/final-reviewed-baseline-20261111-sql-verified/`; candidate cũ giữ archive, root hiện tại drift có chủ đích. Các mục bên dưới ghi trạng thái tại thời điểm chuẩn bị trước đó. Live30/held-out còn pending, không gọi model trong đợt tiếp.

**Hoàn tất phạm vi chuẩn bị đã được duyệt.** Không thực thi held-out, không model/tokenizer/embedding inference, không DB/Qdrant/worker/browser, không sửa UI/`.env`/dependencies hoặc commit/push. Tiến độ project giữ **87,3% / 100%**; candidate chưa thay thế final release freeze hoặc human review.

## Đã triển khai

- [Runner](../eval/final_runner.py), [bootstrap](../scripts/run-final-eval.py), [config public](../eval/configs/final_baseline.json): prepare/verify đọc metadata và hash/copy `questions.jsonl` như bytes, không parse hoặc hiển thị câu test. Lưu Git HEAD + trạng thái dirty + hashes, không cần tự commit. Freeze toàn bộ Python trong backend/app và eval cấp đầu, config, reviewed corpus/mapping, bootstrap thực thi và ba dependency locks. Không lấy config smoke oracle làm dataset test.
- Candidate cố định `.cache/final-reviewed-baseline-20261111/`: protocol, request-plan, approval-template và frozen-root. **99 files +4 bootstrap/locks** đã verify. Protocol `04562e68fa1c38d11188b545f9ceba4b38d2e1a49aac30cfad15cfa64f6e9f9b`. Không có execution folder, grant hoặc request ledger thực thi.
- Dự toán 30 câu, production top5/eval top10: **60 generateContent +210 countTokens**, batch mỗi câu2/7. Đây là trần dự toán, **chưa được duyệt**, không phải quota nhà cung cấp. `approval-template.json` vẫn pending, free-tier/quota false; ngân sách0 USD tách khỏi chi phí invoice chưa xác minh.
- Nhánh capture cho lần được duyệt sau này: kiểm tra approval gắn đúng hash request-plan và reference; verify source/archive/bootstrap/locks; rồi mới load split test và yêu cầu đúng30 câu, config/prompt/index runtime khớp. Import app/cache chỉ nằm sau gate. DB dẫn xuất `*_final_test` riêng; collection/storage theo fingerprint grant; thực hiện auth/worker/retrieval/chat production qua API TestClient. Concurrency1, không warmup hỏi model, khoảng nghỉ5 giây giữa câu, không retry/fallback. Một lần thực thi/output, không tự reset ledger hoặc đổi run ID để cấp lại allowance. Khi lỗi, giữ receipt/capture cho phần đã chạy và toàn bộ planned denominator. Không có resume qua process restart trong runner này.
- [Review pack](../eval/review_pack.py), [CLI](../scripts/run-review-pack.py), [hướng dẫn](human-review-guide.md): worksheet Markdown và hai JSON độc lập, điểm null; gắn id/run/output hash. Hiển thị actual final context, câu trả lời, rubric/gold; quote được render literal trong fences. Merge từ chối sai run/hash/reviewer/schema, giữ bất đồng chờ adjudication.
- Đã xuất **phiếu thực hành sáu câu E2E**, dùng archived root/protocol của chính lượt đó để không nhầm source hiện tại: `.cache/final-review-practice-20261111/`. Không có phiếu30 held-out hoặc điểm human mới. Đây không phải chạy lại model.

`approval.json` là technical gate cho CLI, không tự tạo quyền gọi API cho agent. Trước live batch vẫn phải có “Thực hiện đi” cho scope cụ thể, xác minh free tier/quota, không billing/paid fallback. Template không được đổi approved trong đợt offline. Nếu quota không đủ cả30 câu, phải chốt cách chia batch/lifecycle và kiểm tra nó trước khi chạy; runner one-shot hiện không được quảng cáo là hỗ trợ resume đa ngày. Khoảng nghỉ5 giây không bảo đảm tuân thủ mọi quota vì mỗi câu còn nhiều count/generate calls.

## Kiểm chứng và giới hạn

**148 selected tests đạt**,1warning Starlette/httpx baseline; Ruff check/format cho các file Python mới đạt. Tests dùng corpus tạm, chặn socket và đọc reviewed corpus thật. Lượt đầu146pass; bổ sung archived-protocol drift và transport exception receipt rồi lượt cuối148pass. Không dùng Alice/Bob trong fixture test để giả người thật đã chấm output.

Các guard được kiểm tra: pending/quota/free-tier/reference/hash/budget sai bị chặn trước held-out/runtime; source/config/archive/dependency/plan drift; output one-shot không reset; split không đủ30 không chạm native import; query loop dừng khi HTTP lỗi/timeout, request IDs riêng, không retry; phiếu không tự cho điểm, từ chối sửa binding/duplicate/same-reviewer/invalid score, giữ bất đồng và chặn held-out review nếu thiếu opt-in. Literal fencing chứa được backtick/script/link từ dữ liệu. Các contracts runtime/capture/budget/answer/provider/smoke/browser trước đó nằm trong suite regression.

Receipt `.cache/final-preparation-validation-20261111/offline-preparation.txt` xác nhận gate pending từ chối; không import `app.core.config`, torch, SQLAlchemy hoặc HTTPX trong quá trình prepare/verify/xuất phiếu, không execution/SQLite ledger mới. Không nạp `.env` để prepare; bootstrap offline chỉ cần standard library/root. Candidate archive được verify trên root hiện tại và archive. Logs tests ở cùng thư mục.

**Chưa kiểm chứng:** native orchestration mới trên PostgreSQL/Qdrant với10 documents hoặc model thật; chưa chứng minh `*_final_test` đã tồn tại/migrate; chưa mở và kiểm số30 từ nội dung test trong đợt này; chưa đo chất lượng, latency hay chi phí final. Các nhánh live đã viết không đồng nghĩa đã chạy. Trước khi duyệt model run nên kiểm tra storage/corpus ingestion/capture orchestration bằng inference giả trong đợt riêng; nếu cần sửa source thì tạo candidate thay thế có lịch sử, không âm thầm đổi freeze đã dùng.

Chỉ số retrieval trong end-to-end capture có thể gồm chi phí query embedding; E5 đã warm từ ingestion, không có model warmup query. Final report phải tách ingestion cold-load, answering/retrieval, oracle-context, replay và concurrency. Không suy ra SLA hoặc tải đồng thời từ một run30 câu. Nếu xem test để sửa prompt/model, đánh dấu test đã được dùng cho tuning và cần holdout mới trước tuyên bố cải thiện tổng quát.

## Lệnh offline đã sẵn sàng

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -B scripts/run-final-eval.py verify
```

`prepare` đã chạy, không gọi lại trên cùng đường dẫn. `capture` không nằm trong scope được duyệt hiện tại. Nhóm có thể bắt đầu đọc worksheet thực hành và chấm độc lập; sau đó gộp/rescore theo [hướng dẫn](human-review-guide.md). Chưa đánh dấu Bước11/AT-R toàn bộ/human/held-out/release pass.
