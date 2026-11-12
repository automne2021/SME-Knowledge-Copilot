# Final runner: integration và candidate thay thế — 11/11/2026

**Cập nhật đợt tiếp:** [pacing/native held-out attempt](final-heldout-20261111.md) đã thay candidate mặc định bằng bản paced100files+4extras và chạy8/30 (7success/1provider503/22chưa chạy). Archive sql-verified trong báo cáo này được giữ nguyên; root hiện tại drift do pacing/config mới đã ghi nhận. Nội dung dưới ghi đúng trạng thái khi kết thúc đợt SQL integration trước đó.

Đã hoàn tất đợt được duyệt: gộp hai phiếu người chấm, kiểm tra final orchestration trên PostgreSQL/Qdrant với inference giả, thay candidate rõ ràng và cập nhật tài liệu. [Human review sáu câu E2E](human-review-practice-20261111.md) là nhóm bằng chứng riêng. Không gọi Gemini, chạy tokenizer/E5, tải model, mở câu hỏi held-out, sửa UI/`.env`/dependencies hoặc commit/push.

## Thay đổi và lý do

[Final runner](../eval/final_runner.py) tách `native_capture` thành wrapper chọn E5/Gemini thật và `capture_run` dùng chung ingestion → canonical mapping → login/session → query → capture/replay → cleanup. Tests cung cấp counter/embeddings/provider giả qua factory, dùng split dev tổng hợp. Runtime ghi **provider_kind=fake, origin=offline_fixture**, không giả native Gemini để nhận nhãn captured_api.

Dependency injection kiểm được orchestration thật mà không tiêu quota hoặc mở held-out. Chỉ stub database/worker không chứng minh tích hợp; monkeypatch Gemini rồi giữ nhãn native tạo provenance sai. Không thêm chế độ fake vào app sản phẩm. Gate vẫn yêu cầu approval riêng trước khi load test/import runtime; one-shot execution và ledger không được reset.

Runner kiểm hashes trước khởi tạo inference, tạm thay `config.get_settings` trong context rồi khôi phục; giải phóng embedder/vector và ghi summary trong finally. Đây là cải thiện lifecycle công cụ eval, chưa khẳng định đã kiểm hết lỗi khởi tạo/process crash. Nếu process bị kill, finally có thể không chạy; phải audit scope và dọn theo ownership, không xóa DB/collection chung.

## Kiểm chứng

[Suite mới](../eval/tests/test_final_runner_sql.py) đạt **5 tests**; **148 regression tests** đạt ở lượt riêng. Mỗi suite có một warning Starlette/httpx baseline. Ruff check/format hai file Python thay đổi đạt.

| Tình huống | Quan sát |
|---|---|
| 10 TXT tổng hợp | 10 jobs completed; 2 queries HTTP200; login thật, không identity override; capture/replay offline_fixture; 2 generate và14 count **giả** khớp ledger |
| Generation budget0 | HTTP503 `eval_budget_exhausted`, không gọi provider generate, dừng sau câu đầu |
| Provider timeout giả | HTTP504 `model_timeout`, giữ reservation đã dùng, dừng sau câu đầu |
| Hai lỗi query trên | Planned2 / attempted1 / technical_error1 / not_attempted1; không bỏ câu chưa chạy khỏi mẫu số |
| Canonical mapping sai | Từ chối trước query/provider, có summary và cleanup |
| TXT sai UTF-8 | Qua upload signature, worker thật trả `unsupported_encoding`, không retry/query/provider; có summary và cleanup |

Guards cấm khởi tạo Gemini/LocalEmbedder/E5TokenCounter thật, HTTP ngoài testserver/Qdrant loopback và đọc corpus/dataset/mapping/report thật từ test. Corpus fixture tạo trong basetemp riêng. Nhãn `human_reviewed` của fixture chỉ để kiểm loader cùng codepath, không đại diện nhóm đã duyệt dữ liệu tổng hợp; output human0. Bộ10 TXT không chứng minh lại toàn bộ PDF/DOCX hoặc mapping corpus reviewed thật.

Audit cuối: **12 bảng fixture đều0 rows, 0 collection final_, 0 canonical files** trong các attempts; migration head `20261103_rag04`. Năm summary cuối cleanup_completed=true; embedder closed được assert. DB `*_final_test`/schema/artifacts giữ lại. Bật hai container DB/Qdrant có sẵn, không pull/build/xóa volume; không chạy API/worker dev.

Artifacts trong `.cache/final-runner-sql-validation-20261111/`:

- `sql-tests-06.txt`, `pytest-06/`: lượt5/5 cuối và từng summary/capture/evaluation/ledger.
- `regression-02.txt`:148/148; regression-01 sai tên module nên không chạy tests.
- Storage audit (`.cache/final-runner-sql-validation-20261111/storage-audit.json`, chỉ lưu ở máy local), helper (`.cache/final-runner-sql-validation-20261111/audit-storage.py`, chỉ lưu ở máy local): audit độc lập, không chứa DSN/key.
- Candidate replacement (`.cache/final-runner-sql-validation-20261111/candidate-replacement.json`, chỉ lưu ở máy local), `freeze-replacement.txt`: hashes/provenance/pending gate.

Lệnh đã đạt (chỉ chạy lại trong đợt được duyệt, dùng basetemp mới):

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -u -B scripts/run-capture-integration.py eval/tests/test_final_runner_sql.py -q -p no:cacheprovider --basetemp .cache/final-runner-sql-validation-20261111/pytest-06 --tb=short
```

### Chẩn đoán được giữ lại

Lượt01 lỗi parser child do embedded Python bỏ qua PYTHONPATH. Dùng bootstrap test đã có, vẫn chạy parser subprocess thật. Lượt02 fixture answerable thiếu gold; sửa fixture, không bỏ guard loader. Lượt03 stack chỉ ra chờ nạp CA ở SSL context HTTPX; lượt04 chờ psycopg connect trong audit teardown với localhost. Các process test02/03/04 được xác minh command line và dừng riêng; giữ logs/capture/ledger. Không kết luận chắc nguyên nhân OS từ stack. Audit sau đó xác nhận DB/file không còn fixture. Helper recovery thử ngoài sandbox không mở được SQLite nên không cleanup, không tính thành evidence thành công.

Harness cuối tái sử dụng SSL context với certifi CA đọc vào bộ nhớ, vẫn CERT_REQUIRED/check_hostname; HTTP guard chỉ cho loopback. Test PostgreSQL chọn rõ127.0.0.1 khi config là localhost và connect_timeout5s. Không giảm TLS hay đổi timeout/URL production. Lượt05 đạt3/5: fake timeout ném exception khác public contract Gemini, dữ liệu hỏng bị signature chặn trước worker. Lượt06 dùng AppError504 đúng contract và byte sai UTF-8 qua signature để kiểm worker; đạt5/5. Audit đầu đếm lặp symlink pytest `current`; sửa bằng tập đường dẫn resolve duy nhất, audit cuối đạt.

## Candidate thay thế

Candidate mặc định mới `.cache/final-reviewed-baseline-20261111-sql-verified/`: **99 files +4 bootstrap/locks**, protocol SHA-256 `d15e3cea44fe9dca9dae1ec5d24cd20e7fbb85b253f97d90a87646baa8834498`.

Candidate cũ `.cache/final-reviewed-baseline-20261111/` giữ nguyên, archive cũ còn verify. Root hiện tại drift với candidate cũ do runner đổi; lịch sử được ghi rõ. Candidate mới verify source/archive, không sửa reviewed corpus/mapping/config. Prepare chỉ hash/copy questions như bytes; helper xác nhận không import app settings/torch/SQLAlchemy/HTTPX, không decode test.

Cả hai candidate chưa có execution folder, grant hoặc SQLite ledger thực thi. Template mới pending, hai manual flags false. **60 generateContent +210 countTokens** là dự toán30 câu/top5, chưa được cấp quyền chạy. Pending gate đã thử và chặn trước held-out/runtime. Thay candidate không cấp lại allowance cũ.

## Phần còn lại

Trước live30: xác minh free-tier/quota/model availability; chốt quota đủ one-shot run (chưa resume đa ngày), trình bày scope/caps/đầu ra rồi chờ đúng xác nhận. Không đổi approved JSON trong đợt này. Sau capture thật, xuất hai phiếu mới cho30 outputs, chấm độc lập, phân tích lỗi và báo cáo final có mẫu số đầy đủ. Bước11/12 và full acceptance chưa đóng; tiến độ **87,3% / 100%**.
