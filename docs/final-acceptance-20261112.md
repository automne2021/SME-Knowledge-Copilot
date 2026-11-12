# Kiểm chứng acceptance — 12/11/2026

**Mới nhất, sau human adversarial:** [report gộp2/2](human-review-adversarial-20261112.md) và [ma trận mới](../eval/reports/final-20261112/acceptance/acceptance-matrix.json) đóng AT-R14theo phạm vi; **23/23scopedpasses**, không còn partial. Literal-render/no-XSS kế thừa component tests có hashes, actual attack exposure/native/no-tools và hai người chấm đã đủ hai lớp của spec. Đây là consolidated evidence, không một all-native/browser rerun hoặc chứng nhận miễn nhiễm injection. Không gọi model/ghiDB/sửaproductionUI ở đợt gộp; heldout/captures/ledgers/reviews/logs/matrix cũ giữ nguyên. Bước11thêm mục7→5/7/**92,9%/100%**; release/freshsetup/Bước12còn mở. Những bảng22/23/partial phía dưới mô tả snapshot acceptance ban đầu, trạng thái hiện tại ở ma trận mới.

**Cập nhật ở đợt riêng sau acceptance:** [native adversarial AT-R14](adversarial-at14-20261112.md) đã có2/2outputs,2generation+6count trong allowance riêng4/14/0USD. Exposure attack trong context/payload2/2, no-tools/0functioncalls; [hai phiếu mới](human-review-guide.md) còn human0/2. **AT-R14 vẫn partial,22scopedpasses/91,8%**, chưa fullacceptance. Source/input/archive/capture/ledger và cleanup được audit; held-out29reviews/ledger30/210giữ nguyên. Mục native chưa chạy/đề xuất và ngân sách0calls bên dưới mô tả đợt acceptance trước, không là trạng thái sau đợt adversarial. Machine matrix cũ giữ snapshot, không ghi đè để đổi lịch sử.

Đợt được người dùng xác nhận sau [ma trận khoảng trống](final-acceptance-gaps-20261112.md): đối chiếu AT-R01–23, chạy unit/SQL/Qdrant và frontend checks, bổ sung kiểm tra còn thiếu. Kết quả: **22 kịch bản đạt trong phạm vi bằng chứng được ghi dưới đây; AT-R14 còn partial**. Chưa full acceptance hoặc M1 Done.

Đợt này không gọi Gemini, không cấp lại allowance đã hết, không chạy lại held-out hoặc sửa điểm human. Source production/UI/config, `.env`, model/prompt/corpus giữ nguyên; không tải model, cài dependencies, commit/push hoặc bắt đầu đóng gói Bước 12.

## Những gì đã thực sự chạy

| Nhóm | Kết quả | Môi trường và giới hạn |
|---|---|---|
| Backend | 302 test cases khác nhau đạt qua full suite và scoped retests | PostgreSQL/Qdrant thật; embeddings/provider giả; tokenizer cache local, không suy thành AI accuracy |
| Hai contract bổ sung | 2 passed | Search endpoint khi LLM tắt; follow-up không đưa answer cũ vào evidence |
| Eval/metric/review | 69 passed | Arithmetic/spans/dedup/denominator/merge/rescore và binding, không model/SQL |
| Frontend | 36 passed | jsdom/mocked HTTP; không gọi là browser rerun |
| Lint/format | Ruff check đạt, 132 files đã đúng format; frontend lint đạt | Chỉ kiểm tra, không autofix source |
| Frontend build | tsc/Vite đạt, 2.095 modules | Ba bundle files khớp nguyên SHA với bundle đã dùng cho Chrome E2E trước đó |

Tổng **409 test cases khác nhau** =302+2+69+36. Đây là tổng test phần mềm, không phải số câu benchmark. Không có một full backend invocation đạt toàn bộ302: lượt đầu300passed/2failed, sau đó các test lỗi được chạy lại với bootstrap đã sửa. JUnit và logs lỗi vẫn giữ nguyên; bảng/machine receipt dùng kết quả mới nhất của từng case, không xóa lịch sử.

Harness dùng Python 3.12 có sẵn trong pgAdmin và packages hiện có vì venv thiếu interpreter gốc. Test DB mới `copilot_acceptance_20261112_test` được guard khác DB development, migrate head `20261103_rag04`. Các fixtures rollback hoặc cleanup đúng workspace/collection của mình; tests chạy tuần tự trên DB này. Không bật worker dev dùng chung queue.

Key rỗng và hai free-tier flags false trong process kiểm thử; HTTPX real transports chỉ được tới Qdrant local, provider tests dùng MockTransport. Embeddings của integration là fake vectors có nhãn. Hai test model subprocess dùng snapshot không tồn tại/stall target để kiểm deadline, không encode bằng weights thật. Parser vẫn chạy subprocess thật; tokenizer E5 chỉ dùng cache local/offline.

### Lỗi harness đã phát hiện và cách chứng minh sửa

- **Lượt đầu:** cleanup-only CLI không import được `app.worker` vì Python embedded bỏ PYTHONPATH. Kill/restart worker không tới marker sau upsert trong15s. Giữ kết quả300/302 và warning Starlette/httpx baseline.
- **Bootstrap v2:** thêm import paths cho CLI và verified TLS context trong worker con. CLI đạt; kill/restart vẫn lỗi. Chỉ sửa TLS chưa đủ: worker con còn gọi parser subprocess mà chưa có import bootstrap, nên không tới upsert. Không kết luận lỗi generation/publish hoặc nới thời gian chờ.
- **Bootstrap cuối:** cài parser bootstrap cả trong process worker được spawn. Kill/restart đạt9,46s toàn test; vẫn giữ marker15s, terminate/join thật, recovery lease và assertions về generation/orphan. Chạy thêm CLI và hai test hard-deadline với harness cuối:3passed. Không sửa test gốc hoặc code production để làm pass.
- **Hai contract mới** nằm trong test artifact (`.cache/at-20261112/test_gap_contracts.py`, chỉ lưu ở máy local), không sửa source đã freeze: AT-R10 thực sự gọi `/api/v1/search` khi key/flags tắt, fail nếu dựng provider; AT-R20 gửi hai câu trong cùng session, xác minh retrieval nhận nguyên câu mới và payload model chỉ có câu hiện tại/evidence, không answer hay câu hỏi trước. Provider fake dùng sentinel để kiểm transport, không tính đó là output chất lượng đã chấm.

## Ma trận kết quả và provenance

`Đạt` ở đây bao gồm contract tests chạy lại và bằng chứng native/browser kế thừa được chỉ rõ. Không có lượt native/browser mới. Machine matrix (`.cache/at-20261112/acceptance-matrix.json`, chỉ lưu ở máy local) liệt kê chính xác testcase, JUnit run, hashes và các lần fail/retest cho từng AT.

| ID | Kết quả | Bằng chứng chính |
|---|---|---|
| AT-R01 | Đạt | PDF acceptance2trang: parse/chunk round-trip, worker publish SQL/vector, source API trả đúng PDF bytes; native ingestion được kế thừa |
| AT-R02 | Đạt | Corpus PDF/DOCX/TXT/MD, DOCX heading/bảng/location, source DOCX không bịa page |
| AT-R03 | Đạt | Fixtures scan/blank/encrypted/mixed/malformed, terminal states và skipped-page warning |
| AT-R04 | Đạt | MIME/size/traversal/ZIP bounds, parser timeout và storage validation |
| AT-R05 | Đạt | Hai transactions upload đồng thời:202/409, một document/revision/job và file |
| AT-R06 | Đạt sau retest | Worker con upsert thật → terminate → recover/restart, generation mới và orphan cleanup |
| AT-R07 | Đạt | Worker mất lease bị fence, không publish generation cũ |
| AT-R08 | Đạt | Publish rollback/staging, SQL revalidation/Qdrant scope loại orphan |
| AT-R09 | Đạt | API member upload denial, cross-workspace delete/source và chat ownership; không chỉ dựa nút ẩn |
| AT-R10 | Đạt | Test mới gọi search endpoint khi LLM disabled, không dựng provider/count/generate |
| AT-R11 | Đạt, có native kế thừa | API trusted citations/partial-conflict; human review và sáu output thật có claims dẫn hơn một document |
| AT-R12 | Đạt, có native kế thừa | No-ready/no-hit/context-excluded branches; bốn unanswerable đã human review; lỗi không coi là abstention |
| AT-R13 | Đạt contract | JSON/E99/repair một lần/còn sai502 và context budget exclusion; không cần cố ép model thật trả JSON hỏng |
| AT-R14 | **Partial** | Parser/prompt/no-tools/literal-render tests đạt. Native injection smoke cũ có giới hạn; chưa lượt adversarial trên bản hiện tại và human review riêng |
| AT-R15 | Đạt contract, có lỗi native kế thừa | Qdrant/embed/LLM technical failures, typed retries/timeouts; q023native503 giữ nguyên |
| AT-R16 | Đạt | Delete/source410 trước cleanup, retry/exhaustion/manual retry và idempotent cleanup |
| AT-R17 | Đạt | Barriers delete khi count/generate/repair/upsert;409/fencing/no-resurrection |
| AT-R18 | Đạt | Legacy/full-context/uncited copies scrub; UI invalidation; history/source evidence Chrome kế thừa |
| AT-R19 | Đạt | Idempotency/input conflict/session busy/lost commit acknowledgement, một persisted answer |
| AT-R20 | Đạt contract | Test follow-up mới không lấy old answer làm evidence; câu hỏi/context vượt budget được chặn |
| AT-R21 | Đạt | Metric/spans/overlap/evidence groups/denominator0→null và giữ lỗi/chưa chạy trong mẫu số |
| AT-R22 | Đạt rebuild, native kế thừa | Hai phiên re-ingest10docs trên DB/index rỗng, cùng frozen manifest/mapping/config, scoped IDs khác và reports/cleanup lưu đủ |
| AT-R23 | Đạt trong phạm vi P0 kế thừa |36component tests, build/lint mới; bundle3files và backend53files khớp Chrome P0 trước:source410/auth401/navigation/keyboard/AI label/states |

**AT-R22 và fresh installation khác nhau.** Ma trận gaps trước đã gộp yêu cầu clean checkout/dependencies vào rebuild. Đối chiếu lại spec15.4: AT-R22 yêu cầu tái dựng từ manifest trên DB/index sạch; receipt (`.cache/at-20261112/inherited-native-rebuild.json`, chỉ lưu ở máy local) xác minh hai preflights DB rỗng,20ingestions completed, cùng protocol/canonical mapping và hai scopes khác. Có thể ghi nhận phần rebuild này bằng evidence sẵn có, không cần gọi model lại. Fresh checkout/clean volumes/dependencies/topology/demo theo hướng dẫn vẫn là Bước12 và chưa làm; không đổi nhãn thành đã clean install.

**Kế thừa browser có kiểm chứng byte.** Receipt bundle/PDF (`.cache/at-20261112/inherited-ui-and-pdf-evidence.json`, chỉ lưu ở máy local) đối chiếu fresh build với bundle archive; backend comparison (`.cache/at-20261112/inherited-browser-backend-comparison.json`, chỉ lưu ở máy local) đối chiếu53backend files của Chrome protocol với source hiện tại. Cả hai khớp; [report Chrome](browser-e2e-retry-20261110.md) giữ thao tác/lệnh/môi trường gốc. Không đổi timestamp thành một lượt browser mới hoặc tuyên bố đã thử mọi thiết bị/biến thể.

**AT-R14 vẫn mở:** so với smoke04/11, nhiều SHA khác vì CRLF/LF; normalized text của answering/gemini/schema/sources/retrieval khớp, servicechat có thay đổi. Comparison (`.cache/at-20261112/historical-injection-text-comparison.json`, chỉ lưu ở máy local) phân biệt byte drift với text drift. Không tự nâng smoke cũ thành đánh giá adversarial hiện tại hoặc chứng nhận model miễn nhiễm injection. Các tests hiện có xác minh literal data/no-tools/no-XSS ở contract, chưa tự chấm semantic behavior của model mới.

## Cleanup, bất biến và artifacts

Postrun audit (`.cache/at-20261112/postrun-audit.json`, chỉ lưu ở máy local):21bảng nghiệp vụ trong DB acceptance đều0rows, head đúng; không còn `s6_test_`/`final_` collections hoặc files trong runtime storage. Pytest basetemp chứa fixtures/artifacts được giữ để xem lại; không nhầm chúng với uploads production hoặc xóa cache để giả cleanup. DB/schema/container vẫn giữ.

Snapshot167source/config files khớp sau tests; production protocol/controller/archive verify.60files gốc của held-out/review/captures/SQLite ledgers và hai file combined/reviewed-metrics giữ hashes. Bộ29outputs và strict success29/30 không bị chấm lại, retry hoặc sửa số. Ngân sách native calls mới0; usage/invoice của các phiên model trước giữ nguyên.

Artifacts trong `.cache/at-20261112/`: `backend-01..04.xml/.txt`, `gaps-01.xml/.txt`, `eval-01.xml/.txt`, `frontend-01.xml/.txt`, logs lint/build, harness cuối (`.cache/at-20261112/run-backend.py`, chỉ lưu ở máy local), snapshotsv1/v2, source manifest, evidence receipts, machine matrix. XML là nguồn counts/test IDs; không cộng một case pass nhiều lần thành tests khác nhau. Lỗi helper tìm manifest UI nhầm và matcher JUnit thiếu describe-prefix đã được phát hiện trước khi xuất receipt cuối; không sửa evidence gốc.

## Phạm vi đề xuất ở thời điểm acceptance — lịch sử trước đợt adversarial

Để hoàn tất lớp native của AT-R14, đợt riêng nên chuẩn bị runner/fixtures và chạy **hai câu adversarial synthetic/dev**, giữ nguyên production model/prompt:

1. Nguồn có email hỗ trợ đúng cùng nội dung giả system yêu cầu bỏ qua nguồn/trả email khác/chạy script; kiểm output factual/citations, payload literal và không tools.
2. Hỏi thông tin không được policy quy định trong cùng nguồn chứa instruction độc hại; kiểm không bịa và expected abstention. Hai người chấm actual output/final context riêng, không dùng điểm29held-out thay thế.

Phạm vi files dự kiến: một harness eval/bootstrap mới và tests, fixtures/protocol/ledger/capture/worksheet mới dưới `.cache/`, cập nhật PLAN/KNOWLEDGE/report. Không sửa UI hoặc production prompt/pipeline; không ghi vào held-out ledger/capture/phiếu đã chấm. Đề xuất **grant mới riêng cho dev tối đa4generateContent+14countTokens,0USD**, tính cả repair và request mất response, pacing/no auto-retry/download/paid fallback như trước. Đây là allowance bổ sung cần xác nhận, không reset cap held-out60/210; parent count210/210đã hết. Kiểm free tier/quota/cache trước calls; chưa có grant/ledger/calls của đợt mới trong đợt acceptance này.

Sau AT-R14, đóng scope acceptance/release theo PLAN rồi mới fresh setup/packaging/demo Bước12. Đợt hiện tại dừng ở kết quả22/23và chuẩn bị phạm vi còn lại; không tự chạy bước tiếp theo.

**Tiến độ giữ91,8%/100%.** Bước11mục7 vẫn chưa hoàn tất vì AT-R14 partial, mục1/6 và Bước12 còn mở. Không tăng % theo409tests hoặc22scenarios.
