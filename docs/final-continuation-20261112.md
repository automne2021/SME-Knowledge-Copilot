# Held-out continuation — 12/11/2026

**Sau khi nhóm chấm xong:** [merge/rescore29/29](human-review-heldout-20261112.md) đã hoàn tất offline, không bất đồng; correctness2/2, strict success29/30giữ q023failed,34/34claims và36/36citation links theo nhóm. Phiếu gốc/capture/ledger/report không đổi. Các mục0/29/pending/chưa chấm và87,3% bên dưới là snapshot lúc bàn giao capture; kết quả mới ở [reviewed metrics](../eval/reports/final-20261112/heldout/reviewed-metrics.json). Tiếp theo [acceptance gaps](final-acceptance-gaps-20261112.md), không cần chấm lại hoặc gọi model. PLANv1.26ghi91,8%/100%, fullAT/release/freshsetup vẫn mở.

## Phạm vi đã xác nhận

Chỉ chạy **q024–q045**, là 22 câu `not_attempted` của [lượt 11/11](final-heldout-20261111.md). Không chạy lại q023 đã lỗi hoặc bảy câu đã có output. Trần riêng **44 generateContent +154 countTokens**, nằm trong allowance gốc **60/210** đã dùng **8/56**. Ngân sách **0 USD**, không billing/paid fallback/download/UI/commit/push. Người dùng xác nhận “Thực hiện đi” cho thiết kế continuation và lượt này.

Model, prompt, corpus, parser/chunker, embedding/index, retrieval top5 và timeout giữ nguyên. Protocol production vẫn `1340f78f14f054fc63196e983c5cd876939f52534d999f663cdffe8257ae4b3d`; source/archive gốc 100 files +4 extras được verify. Hai file controller mới có manifest riêng `3369045f447c10325551446e855e01baf823acb94b741318f6cb9f588880a1eb`, không giả rằng chúng có trong freeze cũ. Archive continuation lưu 100 files gốc và hai file controller, không `.env`/weights.

## Cơ chế giữ allowance và provenance

[Controller](../eval/final_continuation.py) và [bootstrap](../scripts/run-final-continuation.py) mới dùng lại `native_capture` cũ, không sửa production pipeline sau khi xem test. Prepare đọc status/report để chọn câu chưa chạy; không decode thêm nội dung câu hỏi. Chỉ sau scoped approval, preflight và kiểm config mới load các câu được chọn.

- Snapshot baseline giữ nguyên grant, runtime binding và từng reservation SQLite cũ. Một claim file tạo exclusive trong execution gốc chặn continuation thứ hai cấp lại allowance. Output/execution mới cũng one-shot.
- Mỗi request reserve **ledger cha trước**, rồi ledger con, rồi mới vào provider. Ledger cha không rebind/reset; child binding thuộc scope mới. Nếu ghi child lỗi sau parent reserve thì reservation cha bị tiêu, không refund hoặc gửi provider.
- Kiểm hashes controller/production/input/archive/evidence trước từng reservation; kiểm baseline append-only, batch và prefix scope của reservations bổ sung. Trần từng câu vẫn2/7, trần tổng cha60/210 và con44/154 cùng có hiệu lực.
- Lỗi kỹ thuật dừng trước câu tiếp, không tự retry. Pacing native cũ giữ12requests/61s, min gap5,1s, input reservation200K/61s; count/generate cùng bị điều tiết. Request caps không bảo đảm quota của clients khác cùng project.
- Composite sao chép các observations của hai capture **không trùng ID**, cùng production protocol. Giữ nguyên q023 failed và bytes bảy output cũ; nguồn/hashes/row IDs có trong provenance. Đây là **hai phiên chạy được tổng hợp**, không phải một lượt liền mạch30câu. Child report riêng vẫn có tám câu không thuộc scope mới; composite mới là nơi xem mẫu số30.

Hash/ledger phát hiện drift và chặn trước call; không cung cấp distributed transaction SQLite–HTTP hoặc bảo đảm tự phục hồi khi process/máy bị kill. Không xóa claim/execution để thử lại. Tạo scope mới không cấp thêm ngân sách.

## Kiểm chứng trước native capture

- [24 controller tests](../eval/tests/test_final_continuation.py): cap cha/con, exclusive claim, chỉ câu chưa chạy, parent binding/baseline, fail-closed khi child lỗi, concurrent reservations, approval/hash drift, composite disjoint và phiếu chấm mới còn null. Corpus/metadata trong unit fixtures là synthetic, không phải native evidence.
- [3 SQL/Qdrant tests](../eval/tests/test_final_continuation_sql.py): storage/auth/worker/parser/retrieval/capture/cleanup thật với inference giả, gồm thành công, budget0 và timeout. Parent đã dùng trước được giữ nguyên. Cả ba đạt; fixture teardown kiểm12bảng0rows/collection và canonical files đã dọn.
- Regression gộp176passed/4failed vì guard offline chặn socketpair nội bộ của asyncio trên Windows, trước mock HTTP của pacing. Chạy8pacingtests ở process riêng đạt, phủ180tests khác nhau qua hai lượt (4overlap), không cộng reruns thành tests mới. Giữ log lỗi, không tắt network guard. Ruff check/format bốn file mới đạt.
- SQL lượt đầu không kết nối vì Docker Desktop tắt. Bật lại Desktop và đúng hai containers có sẵn; không pull/build/reset volume. Lượt kế2passed/1failed vì assertion nhầm **cap14count** với **usage6count** của hai câu synthetic chỉ có một nguồn; sửa test kỳ vọng usage6, không sửa runner. Lượt cuối3passed.
- Preflight config/prompt/cache/index khớp, test DB rỗng/head20261103_rag04 và Qdrant ready; không inference/download. TLS handshake Google kiểm certificate đạt, chưa gửi HTTP/key/prompt trong probe. Final SQL suite chạy sau preflight rồi cleanup được fixture xác minh trước native capture.

Free-tier/quota dựa trên xác nhận người dùng đã cung cấp: không billing/thẻ/phương thức thanh toán,15RPM/250KTPM/500RPD. Không truy vấn độc lập trạng thái billing hoặc usage hiện tại. Tài liệu [Google rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) và [pricing model](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) được đối chiếu12/11; quota thay đổi theo project, không được bảo đảm bởi flags local. Invoice cost chưa xác minh (`null`), tách khỏi budget0USD.

Logs/receipts trong `.cache/final-continuation-validation-20261112/`; controller/capture/composite/review trong `.cache/final-heldout-continuation-20261112/`. Giữ nguyên `.cache/final-heldout-review-20261111/` và hai phiếu thực hành6câu.

## Kết quả và bàn giao

**Đã hoàn thành lượt continuation:22/22 HTTP200**, không lỗi mới/repair/retry. Composite đã attempt đủ30câu, có29outputs và giữ1lỗi q023HTTP503 từ phiên trước. Manifest **`completed_with_errors`**, không phải full acceptance hoặc human-quality pass.

| Số đo | Kết quả | Mẫu số/giới hạn |
|---|---:|---|
| Composite planned/attempted/not attempted | 30/30/0 | Hai phiên cùng production protocol |
| Thành công kỹ thuật / lỗi | 29/1 | Error rate1/30≈3,33%; không phải accuracy96,67% |
| Output status | 24grounded,1partial,4insufficient_evidence | Chỉ schema/status, chưa chấm đúng/đủ/support |
| Request continuation | 22generation +154count | 176nativeHTTP200, khớp ledger/dispatch |
| Request tổng hai phiên | 30generation +210count | Trong cap60/210; count allowance đã hết |
| Usage continuation | 19.760prompt /2.715candidate /22.475total tokens | Chỉ generation trả usage |
| Usage hai phiên | 25.978prompt /3.436candidate /29.414total tokens | 29generation200; q023503 không có usage, không suy invoice0 |
| Retrieval trên26answerable | Hit@5=1,0; Recall@5=1,0; MRR@5≈0,9808 | Bao gồm q023 đã retrieve trước lỗi generation; chỉ26câu thuộc corpus nhỏ này |
| Multi-evidence5câu | Recall@1=0,6; @3=0,9; @5=1,0 | Top1 chưa đủ toàn bộ căn cứ; không đồng nghĩa answer đúng |
| Retrieval latency30câu | p50≈586,79ms; p95≈634,98ms | Concurrency1, E5/index đã nạp lúc ingest |
| Query latency29success | p50≈38,81s; p95≈44,87s; max≈45,49s | Gồm pacing/network; không phải LLM latency thuần hoặc SLA |
| Native pacing continuation | min gap5.109ms; peak12requests/61s;80Kinput reservation/61s | Tổng wait711.283ms; kiểm rolling receipts đạt |
| Human output review | 0/29 | Correctness/faithfulness/citation vẫnnull; practice6/6 không thay thế |

Bốn `insufficient_evidence` khớp bốn expected-abstain labels và không có false-abstain theo status trên các output thành công: automated precision/recall1,0. Đây là so nhãn hành vi trên bốn mẫu, **không phải human review nội dung lý do từ chối**. Cột@10 generic trong metrics vẫn dùng capturetop5, không coi là retrieval10 thật. Một `partial` cần được chấm đúng rubric: nêu thiếu/mâu thuẫn hợp lý có thể đúng, không tự chấm sai hoặc đúng chỉ từ status.

Final audit (`.cache/final-continuation-validation-20261112/final-audit.json`, chỉ lưu ở máy local) xác minh source/input/controller/archive, original evidence/binding/reservations, dispatch/ledger/pacing, hashes capture/report và q023 không bị thay. Storage audit độc lập (`.cache/final-continuation-validation-20261112/postrun-storage-audit.json`, chỉ lưu ở máy local):12bảng fixture0rows,0final_collections,0ownedcanonicalfiles. Giữ DB/schema/containers và artifacts; `.env`/UI không đổi. Hai phiếu thực hành và packet7output cũ giữ nguyên hashes.

Composite run `offline_replay_1183a4c02b204744b58b042eed56c802`; capture SHA `ea78b6d22e907110e7c14a87d4de2edacb998969e0bd2260476c2215de0fb10f`, per-question SHA `e62bbb5131877a53693410d6479868293348f1e00e08eb5f6b54ceb01da1a754`. Evaluator offline gọi0model; các native requests thuộc hai capture, không cộng replay vào request usage. Provenance độc lập của manifest vẫnfalse, audit nội bộ không là third-party attestation.

- Report tổng hợp (`.cache/final-heldout-continuation-20261112/composite/evaluation/report.md`, chỉ lưu ở máy local), metrics (`.cache/final-heldout-continuation-20261112/composite/evaluation/metrics.json`, chỉ lưu ở máy local), provenance (`.cache/final-heldout-continuation-20261112/composite/provenance.json`, chỉ lưu ở máy local), summary continuation (`.cache/final-heldout-continuation-20261112/execution/summary.json`, chỉ lưu ở máy local).
- Hai người đọc worksheet29outputs (`.cache/final-heldout-continuation-20261112/review/worksheet.md`, chỉ lưu ở máy local), điền độc lập phiếu A (`.cache/final-heldout-continuation-20261112/review/reviewer-a.json`, chỉ lưu ở máy local) / phiếu B (`.cache/final-heldout-continuation-20261112/review/reviewer-b.json`, chỉ lưu ở máy local) theo [rubric](human-review-guide.md). Phiếu mới gắn run/hash composite, reviewer/điểm đềunull; không sửa phiếu thực hành đang mở trong IDE hoặc packet7outputs cũ.

**Bước tiếp:** nhóm chấm29outputs; sau đó đợt được xác nhận riêng sẽ validate/merge/adjudication/rescore offline và phân tích lỗi. Không cần gọi model thêm. Count allowance gốc đã hết; không retry q023, reset hoặc đổi scope để tiếp tục gọi. Chưa đo oracle/no-context ablation, lặp ba lần/query, concurrent load, fullAT-R01–23/fresh setup/release. Không tự thêm lỗi để đủ ba failure cases; hiện chỉ xác minh một lỗi kỹ thuật provider, lỗi nội dung còn chờ người chấm.

**Tiến độ:87,3% /100%.** Chưa tự chấm human quality hoặc đóng Bước11–12 bằng số tests/tooling.
