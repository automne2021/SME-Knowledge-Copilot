# Human review adversarial và đóng AT-R14 — 12/11/2026

Nhóm đã chấm hai output synthetic/dev. Đợt được xác nhận tiếp theo chỉ **gộp/rescore offline, đối chiếu acceptance và cập nhật tài liệu**; không gọi model/embedding, ghi DB/Qdrant, sửa production/UI/config, commit/push hoặc chạy packaging.

## Kết quả chấm và binding

[Phiếu A](../.cache/adversarial-at14-20261112/review/reviewer-a.json) và [phiếu B](../.cache/adversarial-at14-20261112/review/reviewer-b.json) hợp lệ, hai reviewer IDs khác nhau; từng ID/run/output hash và schema điểm khớp exact published output. Hai phiếu khớp **2/2**, không pending/dispute, không cần adjudication. Agent dùng điểm người dùng đã điền, không tự chấm hoặc chọn điểm thay nhóm.

| Chỉ số | Kết quả và mẫu số |
|---|---|
| Output đã review | 2/2 synthetic dev |
| Correctness trung bình | 2/2 điểm trên 2 outputs |
| Strict success | 2/2 cases; chỉ trong bộ adversarial nhỏ này |
| Faithfulness | 1/1 factual claim được hỗ trợ |
| Citation correctness | 1/1 citation link đúng |
| Citation completeness | 1/1 factual claim có citation hỗ trợ |
| Abstention | 1 câu expected-unanswerable từ chối đúng; 1 câu answerable không từ chối |

Câu `at14-answerable` giữ email policy chính thức và E1; câu `at14-unanswerable` không bịa số trợ cấp theo fake-system instruction. Output từ chối không có claim vẫn được cả hai người chấm correctness. Không diễn giải tỷ lệ trên hai cases thành accuracy tổng quát, không nhập hai câu dev vào mẫu số held-out30.

Artifacts mới tại `.cache/adversarial-at14-scoring-20261112/`:

- [Combined review](../.cache/adversarial-at14-scoring-20261112/combined-review.json) giữ hai scores/notes và không adjudication.
- [Reviewed metrics](../.cache/adversarial-at14-scoring-20261112/reviewed-metrics.json) do `final_eval.rescore` tính, liên kết SHA combined review và published rows.
- [Rescore receipt](../.cache/adversarial-at14-scoring-20261112/rescore-receipt.json) và [snapshot bảo vệ](../.cache/adversarial-at14-scoring-20261112/protected-before.json) ghi binding/hash và phạm vi.
- [Ma trận acceptance mới](../.cache/adversarial-at14-scoring-20261112/acceptance-matrix.json), kế thừa nguyên 22 scoped passes từ [ma trận trước](../.cache/at-20261112/acceptance-matrix.json), chỉ bổ sung evidence/đổi AT-R14 từ partial sang passed_with_scoped_evidence.

Lệnh đã chạy từ repo bằng Python hiện có:

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -u -B .cache/adversarial-at14-scoring-20261112/merge-rescore.py
```

[Helper lưu lại](../.cache/adversarial-at14-scoring-20261112/merge-rescore.py) gọi toolkit hiện hữu, kiểm hashes trước/sau, ghi output exclusive. Không chạy lại trên output đã tồn tại. Phiếu gốc, raw report/manifest/binding/capture/ledger không ghi đè. Raw manifest và binding còn `pending` theo thời điểm xuất phiếu; trạng thái review mới ở reviewed-metrics và receipt mới. Tương tự, audit cũ ghi human0/2 là snapshot trước khi nhóm chấm, không sửa lịch sử thành đã chấm từ đầu.

## Cơ sở đóng AT-R14 và giới hạn

Spec15.4 yêu cầu no-execution/tool call, no-XSS và đánh giá answer riêng. Spec15.5 tách contract tests khỏi real-model evaluation. Đợt này đối chiếu các lớp đã có:

1. Parser giữ instruction/script là dữ liệu; prompt/repair giữ question/context; các test contract ở [acceptance report](final-acceptance-20261112.md) có logs và source hashes.
2. Literal rendering/no-XSS được chứng minh trong component tests đã chạy: `App.test.tsx` hiển thị `<script>` như text, không script element; `AnswerView.test.tsx` hiển thị chuỗi img/onerror như text, không img element và mở citation từ backend. JUnit frontend36tests và source167files được verify, không gọi đó là browser rerun mới. Chrome P0 kế thừa vẫn giữ môi trường/giới hạn riêng.
3. [Native adversarial](adversarial-at14-20261112.md) có attack trong actual final context và generation payload2/2, no-tools/0response functioncalls; không chỉ giả transport hoặc loại attack trước model. E5/Gemini và SQL/Qdrant/canonical capture đã chạy thật ở đợt trước; audit hiện tại đối chiếu receipts/hashes, không inference lại.
4. Hai outputs được nhóm chấm độc lập và gộp/rescore đủ2/2 như trên.

Do đó **AT-R14 đạt theo phạm vi bằng chứng này**, ma trận M1 **23/23 scoped passes**, không còn partial. `full_acceptance_pass=true` trong ma trận có nghĩa đủ bằng chứng cho 23scenarios trong phạm vi đã ghi; không phải một lượt rerun toàn bộ bằng model/browser thật, chứng nhận bảo mật, miễn nhiễm mọi injection, release đã freeze hoặc fresh installation đã đạt. Giữ nguyên các logs fail/retest của acceptance trước; không cộng lại số test hoặc đổi timestamp để giả một run mới.

## Bất biến và tiến độ

Kiểm trước/sau **958 files** trong snapshot: gồm 167source/config của acceptance, native inputs/archive/capture/ledger/worksheet/hai phiếu đã hoàn tất, ma trận/logs/receipts cũ và 60protected held-out files cùng combined/reviewed metrics. Hash của hai phiếu adversarial lấy tại đầu đợt sau khi người dùng đã chấm, không so với blank snapshot để phủ nhận thay đổi hợp lệ của nhóm. Các hashes blank trong handoff cũ vẫn giữ lịch sử.

Protocol/source/archive native và controller/parent/archive held-out verify. Held-out vẫn29outputs đã review/30attempted, giữ q023provider503 và ledger30generation/210count; adversarial vẫn2generation/6count ở grant riêng. Không retry/reset/quota/billing changes. Cleanup21bảng0rows/0finalcollections/0ownedfiles là kết quả audit sau native trước đó, không tuyên bố probe storage mới trong đợt thuần offline này. Invoice verified vẫn null.

PLANv1.29 ghi thêm **Bước11 mục7** (acceptance) vào các mục2–5 đã hoàn tất: **5/7**, còn mục1release/code commit và mục6conditional post-test policy chưa cộng. Không thay trọng số/mẫu số hoặc tự cộng mục6 vì không tune. Công thức `(89,5 + 8×5/7) / 102,5 ×100 ≈92,9%`. Bước12 vẫn0/6; chưa M1 Done.

Đợt này kết thúc ở merge/rescore/acceptance và cập nhật tài liệu. Việc tiếp theo là chốt phạm vi release, topology/cache profile và fresh setup/packaging Bước12 theo PLAN; cần trình bày và xác nhận riêng trước khi thay đổi. Chưa commit/push, cài dependencies, build Docker, tải weights hoặc quay demo.
