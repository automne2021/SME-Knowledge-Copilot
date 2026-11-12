# PLAN — SME Knowledge Copilot

> **Phiên bản:** 1.30 — chốt release M1 trên nhánh `release/m1` (Bước 11 mục 1), 12/11/2026 (lập kế hoạch 01/11/2026)<br>
> **Nguồn yêu cầu:** [SME_Knowledge_Copilot_RAG_Specification.md](SME_Knowledge_Copilot_RAG_Specification.md), v2.1  
> **Mục tiêu:** hoàn thành project RAG thuần có demo, test và benchmark tái lập; hướng tới M1 ngày 15/11/2026.  
> **Nhân sự:** 2 người. Kế hoạch theo thứ tự phụ thuộc; thời lượng là ước lượng, không phải cam kết.  
> **Trạng thái:** Bước00–10 hoàn thành theo phạm vi; human held-out29/29 đã gộp/rescore, strict success29/30giữ provider503. Human adversarial2/2 đã gộp/rescore, AT-R14đạt; acceptance23/23đạt theo bằng chứng chạy lại/kế thừa được ghi rõ. Bước11ghi5/7mục2–5,7; release freeze và Bước12còn mở, mục6conditional chưa cộng. Held-out ledger30generation/210count không đổi.<br>

**Đợt gộp review adversarial được xác nhận12/11:** [report/giới hạn](docs/human-review-adversarial-20261112.md), [reviewed metrics](.cache/adversarial-at14-scoring-20261112/reviewed-metrics.json), [ma trận mới](.cache/adversarial-at14-scoring-20261112/acceptance-matrix.json). Hai phiếu hợp lệ/khớp2/2, correctness2/2điểm, strictsuccess2/2devcases, support1/1claim/citation1/1link/completeness1/1; không adjudication. Kết hợp actual attackexposure/no-tools/native và literal-render/no-XSS contract đã có để đóng AT-R14theo scope, không khẳng định miễn nhiễm injection hoặc rerun mọi tầng. 958protected files trước/sau giữ hashes, gồm source167/native/phiếu đã chấm/oldAT và heldout60; không ghi đè rawpending reports hoặc ma trận cũ. 0model/embedding/DBwrites/commit/push/UIchanges. Bước11thêm mục7,5/7→**92,9%/100%**, release/mục6conditional/Bước12còn mở. Các snapshot4/7/partial/human0/2/91,8%bên dưới là lịch sử trước merge này; không chấm/gọi lại.

**Đợt adversarial được xác nhận12/11:** [report](docs/adversarial-at14-20261112.md), [audit](.cache/adv-validation-20261112/final-audit.json), [hai phiếu mới cần nhóm chấm](docs/human-review-guide.md). Hai câu synthetic/dev dùng E5cache/Gemini/SQL/Qdrant thật, native2generation+6count/8HTTP200 trong grant riêng4/14/0USD; không repair/retry/tune/paidfallback/download/UI/commit/push. Attack có trong actualcontext và generationpayload2/2, không tools/0functioncalls; output email chính thức/citation và insufficient_evidence chỉ là quan sát, chưa humanpass. 26unit mới+45regression=71passed,3SQL riêng/Ruff5files đạt,85frozenfiles+2extras verify. Cleanup21tables0rows/0finalcollections/0ownedfiles;60heldoutfiles và combined/rescoredmetrics giữ hashes. Invoiceverifiednull, oldledger30/210không đổi. Human0/2, AT-R14partial, giữBước11mục2–5=4/7/**91,8%/100%**. Các mô tả chưa có grant/native mới ở snapshot acceptance bên dưới là lịch sử; ma trận cũ giữ nguyên. Tiếp theo nhóm chấm hai output mới, không chấm lại29heldout; merge/rescore/đóng acceptance cần đợt được xác nhận tiếp, không tự bắt đầuBước12.

**Đợt acceptance được xác nhận12/11:** [kết quả và provenance](docs/final-acceptance-20261112.md), [machine matrix](.cache/at-20261112/acceptance-matrix.json).409test cases khác nhau đạt qua các process:302backend+2contract mới+69eval+36frontend; không cộng retests. Backend đầu300pass/2fail do bootstrap Python embedded; CLI và child-worker parser bootstrap sửa trong artifacts, không production/assertion/deadline; scoped retests đạt, giữ logs lỗi. Ruff132files/frontendlint/build đạt; bundle3files/backend53files khớp Chrome evidence cũ. DBacceptance riêng head20261103_rag04,21bảng0rows/0testcollections/0runtimefiles;167source/config và60held-out/review files giữ hashes. AT-R22rebuild từ manifest có native evidence hai phiên10docs trên DB/index rỗng, không thay fresh installation Bước12. AT-R14contract đạt nhưng native mới/human adversarial còn thiếu;0Gemini calls mới, không cấp thêm budget/reset/tune test/UI/source/commit/push. Bước11mục7chưa đóng; giữ **91,8%/100%**. Phạm vi đề xuất hai dev adversarial queries/cap mới4generation+14count/0USD cần xác nhận riêng, chưa có grant hoặc calls.

**Đợt review được xác nhận12/11:** [kết quả/giới hạn](docs/human-review-heldout-20261112.md) và [acceptance gaps23scenarios](docs/final-acceptance-gaps-20261112.md). Hai phiếu29entries đúng run/hash/schema, hai reviewer IDs khác nhau; điểm khớp29/29, không adjudication. Correctness2/2, faithfulness34/34claims, citation36/36links, completeness34/34; strict success29/30≈96,67% giữ q023provider503. Đợt offline0model/embedding/DBwrites;60files gốc gồm reviews/captures/ledgers/reports/protocol/grants và practice giữ hashes. Report raw/binding vẫn pending như snapshot lúc xuất; đọc reviewed-metrics mới cho trạng thái hiện tại. Không sửa UI/pipeline/model/prompt/corpus, commit/push hoặc chạy fullAT. Tiến độ theo trọng số giữ nguyên: `(89,5+8×4/7)/102,5×100` → **91,8%/100%**, chưa M1Done. Các đoạn0/29/87,3% dưới đây là lịch sử trước merge/rescore.

**Đợt continuation được xác nhận12/11:** [report](docs/final-continuation-20261112.md) ghi22/22câu chưa từng thử HTTP200, dùng22generation/154count trong cap44/154. Controller mới có manifest riêng3369045f…a1eb, giữ nguyên productionprotocol1340f78f…b3d, model/prompt/corpus và parentbinding/reservations/evidence. Composite hai phiên30attempted/29success/1q023failed/0notattempted, manifestcompleted_with_errors; không một lượt liền mạch hoặc accuracy96,67%. Parent tổng30/210, count allowance đã hết; không retry/reset/paidfallback/download/UI/commit/push. 180regressiontests khác nhau đạt qua các process (lượt gộp176pass/4fail do asyncio socketpair bị guard;8pacing riêng đạt),3SQLtests/Ruff và audit cleanup12bảng0rows/0finalcollections/0ownedfiles đạt. [Worksheet và phiếu mới29outputs](docs/human-review-guide.md) đều chưa chấm; packet7output/practice6câu giữ hashes. Retrieval26answerableRecall@5=1/MRR@5≈0,9808 không là answer correctness. Tiếp theo nhóm chấm rồi merge/rescore offline sau xác nhận; fullAT-R/freshsetup/release vẫn mở, giữ87,3%/100%. Các snapshot8/30/continuation chưa triển khai phía dưới là lịch sử11/11.

**Đợt đóng gói R2, phương án A, được xác nhận 12/11:** [report](docs/fresh-setup-20261112.md), commit `0c1862b`.
- Compose chỉ còn DB/Qdrant, port cấu hình được; bỏ service API không có E5; Dockerfile không còn tự migrate.
- Cài sạch từ `git clone release/m1` trên Compose project và volume riêng: migrate → seed (idempotent) → ingest 10/10 ready → search smoke 9/9 → member 403 → chat khi tắt LLM 503 → delete/cleanup đủ SQL/Qdrant/files.
- Frontend `npm ci` + 36/36 tests; backend **302 passed trong một lần chạy**.
- Không gọi Gemini, không tải model, không đụng volume dev.

Bước 12 đạt **2/6** (mục 1–2) → **95,6% / 100%**.

**Đợt chốt release R1 được xác nhận 12/11:** [report](docs/release-m1-20261112.md).
- Đã commit 5 nhóm (backend hook, tooling eval, UI, launcher, bộ bằng chứng) cùng commit tài liệu trên nhánh `release/m1`; chưa push hoặc merge.
- Working tree khớp 167/167 hash acceptance; blob đã commit giống hệt sau chuẩn hóa line-ending.
- Quét secret: 0 trùng. Hostname trong JUnit đã được che ở bản đưa vào repo.
- Không gọi model, không ghi DB.
- Spec Operations cũ: theo quyết định của người dùng, đã xóa hẳn khỏi repo; các link được sửa sang lịch sử Git (`9b96102`).

Bước 11 đạt **6/7** (mục 6 conditional chưa cộng) → **94,0% / 100%**. Bước 12 vẫn 0/6. Các đoạn 92,9% bên dưới là lịch sử.

**Tiến độ trước R1: 92,9% / 100%.** Bước00–10 hoàn thành theo phạm vi, gồm [Chrome E2E/QA](docs/browser-e2e-retry-20261110.md). Bước11 ghi nhận5/7mục2–5,7 sau [human held-out](docs/human-review-heldout-20261112.md) và [human adversarial/acceptance23scenarios](docs/human-review-adversarial-20261112.md). Held-out29outputs đã chấm, strictsuccess29/30giữ lỗi provider; hai adversarial devcases tách riêng. Chưa chốt release hoặc freshsetup/đóng góiBước12; mục6conditional chưa cộng. Tỷ lệ đo khối lượng xác minh theo trọng số, không phải accuracy AI hoặc M1Done; acceptance có contract/native/browser kế thừa và giới hạn được ghi rõ.

**Ưu tiên được ghi nhận ngày 10/11/2026:** người dùng đã xem UI và thấy ổn, sẽ sửa sau nếu cần; tạm giữ giao diện. Phản hồi này là đánh giá trải nghiệm của người dùng, không tự thay kết quả E2E hay human scoring câu trả lời. Hoàn tất phần còn thiếu Bước 10 → Bước 11 freeze/final eval → Bước 12 đóng gói/demo/CV. Lưu [đánh giá portfolio](docs/portfolio-review-20261110.md) và [kế hoạch kiểm chứng](docs/final-validation-plan.md); hybrid/reranker/multi-turn vẫn là thí nghiệm sau baseline. Đợt ghi chú đầu ngày 10/11 chỉ cập nhật tài liệu, chưa ghi nhận thêm đầu việc hoàn thành.

**Đợt pacing/held-out được xác nhận11/11:** [report](docs/final-heldout-20261111.md) ghi candidate mới1340f78f14f054fc63196e983c5cd876939f52534d999f663cdffe8257ae4b3d,100files+4extras, giữ archives cũ.155regression/8pacing cuối (7overlap)/5SQLtests riêng và Ruff đạt. User xác nhận free/no billing và quota15RPM/250KTPM/500RPD. Run native E5/Gemini ingest10docs, hoàn tất7queries rồi q023generationHTTP503;8attempted/1error/22notattempted giữ mẫu số30.8generation+56count,63nativeHTTP200+1HTTP503; không repair/retry/paid fallback/download. Pacing receipts và ledger/archive/input/capture verify;12bảng0rows/0final_collections/0canonicalfiles. Shell0 là orchestration/cleanup, manifest incomplete. [Hai phiếu mới](docs/human-review-guide.md) có7outputs chờ chấm; không thay practice6/6. Không tune model/prompt sau test, không đánh dấu final30/full acceptance/release đạt; giữ **87,3%/100%**. Continuation22câu cần thiết kế ledger giữ allowance và đợt duyệt riêng, runner hiện chưa resume.

**Đợt review/integration11/11 đã xác nhận:** [merge/rescore](docs/human-review-practice-20261111.md) từ hai phiếu nhóm điền:6/6, không bất đồng, correctness2/2,4/4claims và4/4citation links được hỗ trợ. Chỉ là synthetic E2E, không benchmark held-out. [Final orchestration](docs/final-runner-sql-20261111.md) dùng SQL/Qdrant thật, inference giả:5tests +148regression đạt;10TXT ingestion/auth/capture, budget/timeout/mapping/ingestion failure và cleanup. Audit12bảng0rows/0final_collections/0files. Candidate thay thế `.cache/final-reviewed-baseline-20261111-sql-verified/`, protocol `d15e3cea44fe9dca9dae1ec5d24cd20e7fbb85b253f97d90a87646baa8834498`,99files+4extras verify; archive cũ giữ nguyên, root cũ drift được ghi rõ. Không model calls/download/held-out decode/UI/commit/push; chưa grant/ledger/execution, pending60/210 chưa được duyệt. Không đóng đầu việc Bước11 chỉ bằng tooling/practice review; giữ **87,3% /100%**. Các snapshot human0/6 ở các đợt trước là lịch sử.

**Đợt chuẩn bị offline được xác nhận tiếp ngày 10/11:** triển khai `eval/final_eval.py`, `final_budget.py`, `final_review.py` và fixture tests. Toolkit freeze/replay/score không có live mode; SQLite ledger/caps và provider wrapper được kiểm tra bằng fake, chưa gắn vào API/browser. **57 focused tests đạt**, Ruff check/format đạt; không mở câu hỏi held-out thật, gọi model/embedding, ghi DB/Qdrant, sửa UI/backend/`.env` hoặc commit/push. Dùng Python3.12.6 sẵn có trong pgAdmin vì venv thiếu interpreter gốc; chưa khôi phục venv. [Report và giới hạn](docs/final-eval-tooling.md), [K-087](KNOWLEDGE.md#k-087--công-cụ-offline-cho-freeze-budget-và-human-review). Chưa đóng Bước10 mục5–6 hoặc bất kỳ đầu việc final eval Bước11; giữ **83,4% /100%**.

**Đợt runtime được xác nhận sau đó cùng ngày:** [capture adapter](docs/runtime-capture-step11-preparation.md) đã nối hook mặc định tắt vào API/core chat, lấy actual final context và gắn ledger cho count/generate/repair; app test có settings/DB/collection/storage scope riêng. **116 focused tests đạt/1 warning baseline**, gồm 22 runtime tests với stubs +57 offline regression +37 unit tests answering/provider; chưa chạy SQL/Qdrant thật trong tests, model, embedding, browser hoặc nội dung held-out thật. Probes chỉ đọc: Docker27.3.1 hoạt động, Compose không liệt kê container đang chạy của project; DB test OperationalError và Qdrant ConnectError; LLM config và hai manual flags có mặt nhưng chưa xác minh với Google. Bước tiếp theo cần duyệt bật/chuẩn bị storage test và integration với fakes trước live batch. [K-088](KNOWLEDGE.md#k-088--capture-trong-pipeline-thật-với-runtime-kiểm-thử-riêng); giữ **83,4% /100%**.

**Đợt storage/integration được xác nhận tiếp:** [6 SQL/Qdrant integration tests](docs/sql-capture-integration-20261110.md) và116regressiontests đạt; Docker storage healthy từ images có sẵn, DBtest/schema/queue được xác minh. Suite dùng DB `copilot_capture_test` riêng, real login/worker/retrieval/publish/canonical sources; embeddings/counter/provider giả và origin offline_fixture. Cleanup xác minh12bảng fixture0rows, Qdrant0final_collections; DB/schema/artifacts giữ để xem lại. Không UI, native inference/download, held-out/human review hay commit/push. Đã xử lý bootstrap parser của Python embedded và timeout trong test harness; production source không cần đổi trong đợt này. [K-089](KNOWLEDGE.md#k-089--sqlqdrant-integration-và-ranh-giới-bằng-chứng). Bước tiếp theo đề xuất live dev smoke2câu với trần4generateContent/14countTokens, cần đợt duyệt riêng và xác minh free-tier/quota. Giữ **83,4% /100%**.

**Đợt native smoke được xác nhận tiếp:** [runner và report](docs/native-capture-smoke-20261110.md) đã chạy đúng hai câu tổng hợp với E5 cache + native Gemini, SQL/Qdrant/auth/retrieval/canonical context thật. Câu hoàn ứng grounded/citation, câu nghỉ phép insufficient_evidence với nguồn vẫn nằm trong context. **2 generateContent +6 countTokens** trong trần4/14,8nativeHTTP200, không repair/retry/fallback/download; invoice cost chưa xác minh (null), budget0USD. Ledger/scope cố định không tự reset;72source hashes và inputs đối chiếu sau run đạt. Tooling thêm nhãn synthetic_smoke, không giả human review; hai outputs vẫn pending chấm người. Có10smoketests +116regression +6SQLintegration được kiểm qua các lượt, không chạy browser/held-out. [K-090](KNOWLEDGE.md#k-090--native-smoke-và-phân-biệt-compatibility-với-chất-lượng). Giữ **83,4% /100%**, chưa đóng đầu việc acceptance có trọng số.

**Đợt browser E2E được xác nhận tiếp:** [harness/report](docs/browser-e2e-20261110.md) đã có scope DB/queue/storage/collection riêng, UI bundle build đạt,131guard/regressiontests và Ruff đạt; không đổi UI source/`.env`/dependencies. Bốn câu trước xóa có tổngcap8generateContent/28countTokens, hai câu sau xóa cap0/0. Chưa chạy thao tác browser hoặc model: native Brave approval ban đầu timeout, người dùng đã chấp thuận retry; sau đó Computer Use dừng vì không xác định được URL hiện tại trên Windows đủ chắc chắn để enforce policy, còn browser host tích hợp unavailable. Không bypass guard hoặc gọi API thay rồi nhận browser pass. Ledger0/0, không capture/model output; đã dừng harness và dọn scope, giữ artifacts/ledger. [K-091](KNOWLEDGE.md#k-091--browser-harness-và-tool-blocker-không-phải-acceptance). Bước10mục5–6/AT-R23/human review vẫn pending, giữ **83,4% /100%**. Cần browser access hợp lệ ở phiên thực thi tiếp; không tự reset scope one-shot đã đóng.

### Quy ước báo tiến độ project

Đợt retry được xác nhận: [harness retry-01](docs/browser-e2e-retry-20261110.md) dùng hai ledger, ledger gốc giữ tổng8generateContent/28countTokens; không reset/add allowance.119selectedtests/Ruff đạt; browser6/6cases, source410/auth401 và QA chức năng có bằng chứng; đã xuất capture/evaluation/cleanup, không còn server8012. Human0/6, held-out pending. Đóng hai đầu việc còn lại Bước10 theo bằng chứng, không theo số tests/tooling.

Mỗi phản hồi cuối báo **X% / 100%**, theo yêu cầu người dùng 02/11/2026. Dùng midpoint person-hours của bảng Bước 00–12 làm trọng số cố định ban đầu: `1,5; 4; 7; 5; 8; 12; 10; 10; 10; 10; 12; 8; 5`, tổng **102,5**. Công thức `100 × Σ(trọng số bước × tỷ lệ đầu việc đã xác minh) / 102,5`; làm tròn một chữ số thập phân. Sửa trọng số cần ghi lý do và phiên bản, không đổi để làm % đẹp hơn.

| Bước | Trọng số | Phần đã ghi nhận | Đóng góp quy đổi |
|---|---:|---:|---:|
| 00 | 1,5 | 100% — audit/hướng dẫn | 1,5 |
| 01 | 4 | 100% — môi trường/baseline, quota thật là gate trước smoke | 4 |
| 02 | 7 | 7/7 — hai người duyệt và snapshot khóa ledger | 7 |
| 03 | 5 | Đạt 5/5 mục bắt buộc áp dụng; mục 5 BGE tùy điều kiện hoãn | 5 |
| 04 | 8 | 6/6 — schema/migration/identity/scopes/envelope foundation | 8 |
| 05 | 12 | 7/7 — upload/parser/chunker/source mapping; worker ready thuộc 06 | 12 |
| 06 | 10 | 6/6 — durable worker/local E5/index/publish/recovery/measurement | 10 |
| 07 | 10 | 6/6 mục bắt buộc; mục 6 challenger có điều kiện hoãn | 10 |
| 08 | 10 | 7/7 đầu việc triển khai/smoke; human quality review/held-out còn Bước11 | 10 |
| 09 | 10 | 6/6 — disable/redaction/cleanup/retry/fault-race/retention | 10 |
| 10 | 12 | 6/6 — UI + Chrome E2E/keyboard/navigation/reload/expiry; human-quality còn Bước11 | 12 |
| 11 | 8 | 6/7 — mục 1 release (`release/m1`) và mục 2–5, 7; mục 6 conditional chưa cộng | 48/7≈6,8571 |
| 12 | 5 | 2/6 — mục 1 topology Compose (phương án A) và mục 2 cài sạch; README/video/đóng góp/rà soát còn mở | 10/6≈1,6667 |
| Tổng | 102,5 | `(89,5 + 8×6/7 + 5×2/6) / 102,5` | **95,6% / 100%** |

V1.29 không đổi trọng số hoặc mẫu số102,5. Bước11ghi nhận mục2–5 theo [held-out đã chấm](docs/human-review-heldout-20261112.md), thêm mục7 theo [acceptance23scenarios và adversarial đã chấm](docs/human-review-adversarial-20261112.md). Mục1chốt release/code commit và mục6chính sách sau-test còn mở, chưa cộng mục6khi điều kiện chưa phát sinh. Lỗi provider vẫn nằm trong mẫu số benchmark; acceptance được chứng minh theo từng contract/evidence, không có nghĩa toàn bộ native requests đều200 hoặc đãfreshsetup. Không tăng theo số tests/accuracy.

Đầu việc đang làm/chưa xác minh không tính hoàn thành; đóng gate còn cần các điều kiện của từng bước. Cách chia đều đầu việc trong một bước là ước lượng quản lý, không phải giờ thực tế đã tiêu hay độ chính xác AI. Nếu chỉ giải thích/đọc, giữ nguyên %; chỉ ghi file tiến độ trong đợt thay đổi đã xác nhận. Bước 02 đã đạt khoảng 12,2% trước cộng embedding/tokenizer Bước 03.

V1.6 giữ nguyên mọi trọng số. Mục 5 Bước 03 ghi rõ **nếu đủ tài nguyên**, nên không nằm trong gate bắt buộc khi chủ động hoãn challenger; không đánh dấu đã smoke BGE. Gate Bước 03 là có inference thật cho một embedding + một LLM và response validate được. Đạt gate này không có nghĩa mọi output đều đúng: run đầu có lỗi, retest chỉ một case/prompt v2, không phải 5/5 cùng prompt. Human quality/retrieval benchmark còn ở Bước 07/11.

## 1. Phương án khởi đầu

**Với máy hiện tại, nên bắt đầu bằng embedding local nhẹ trên CPU và LLM hosted.** Xây corpus, đánh giá retrieval và citation trước khi đầu tư vào model lớn, GPU hoặc giao diện hoàn chỉnh.

| Thành phần | Lựa chọn khởi đầu | Khi nào xem lại |
|---|---|---|
| Embedding | `intfloat/multilingual-e5-small`, CPU | So với `BAAI/bge-m3` trên dev set và cùng máy |
| Generation | Thử `gemini-3.5-flash-lite` qua adapter; xác nhận quyền truy cập tài khoản | So với `gemini-3.6-flash` nếu câu trả lời với gold context vẫn yếu |
| Retrieval | Dense-only, Qdrant, filter + SQL revalidation | Hybrid/reranker sau baseline M1 |
| Metadata | PostgreSQL, Alembic, worker lease/retry | Không thêm queue/service nếu chưa có nhu cầu cụ thể |
| Parsing | PyMuPDF, python-docx, TXT/MD UTF-8 | OCR và layout phức tạp ngoài M1 |
| Evaluation | Gold evidence + human review + scripts | Judge tự động chỉ là bổ sung P1 |
| Runtime | Dev: DB/Qdrant trong Docker, API/worker/frontend trên host; cuối M1 đóng gói Compose | Chỉ đổi topology nếu đo cho thấy thiếu tài nguyên |

Đây là **cấu hình để bắt đầu thử nghiệm**, chưa phải kết luận model tốt nhất. Spec cho phép benchmark model nhỏ hơn BGE-M3; sau khi chọn phải đồng bộ model, dimension, chunk config và index manifest, không giữ cấu hình 1024 chiều của BGE khi dùng E5.

Không fine-tune, không agent, không STT, không tự động tạo task trong kế hoạch M1/M2 RAG. Giá trị AI cần chứng minh là: dữ liệu được xử lý đúng, retrieval đo được, câu trả lời có nguồn và biết giới hạn bằng chứng.

## 2. Điểm xuất phát trong repository

Khảo sát ngày 01/11/2026 cho thấy repo vẫn là skeleton của hướng Operations:

| Thành phần đã thấy | Có thể tận dụng | Công việc còn thiếu cho RAG |
|---|---|---|
| `backend/pyproject.toml`, app FastAPI, config/DB/error handling | Khung backend, SQLAlchemy, Alembic, Ruff, pytest | Dependencies và services RAG; chuẩn lỗi/envelope theo spec mới |
| `backend/app/models/workspace.py` | Workspace/user identity và các mixin | User hiện có email; cần mapping login/username, role knowledge_admin và migration rõ ràng |
| API router | Health endpoint | Chưa có auth endpoint/RAG routes trong router đã kiểm tra |
| `compose.yaml` | PostgreSQL, backend image, storage volume | Chưa có Qdrant/worker đang cấu hình chạy; chưa kiểm chứng Docker daemon |
| Frontend React/TypeScript/Vite | Router, styles, API client, backend status | Màn hình hiện là placeholder Operations; cần Documents/Chat/Source Preview |
| Tests hiện có | API basics, schema constraints cũ | Không phải bộ nghiệm thu RAG |
| `eval/README.md` | Thư mục đánh giá | Nội dung còn hướng STT, chưa có benchmark RAG |
| `CLAUDE.md`, README | Conventions và hướng dẫn ban đầu | Còn mâu thuẫn với hướng RAG, phải đồng bộ ở bước 00 |

Không coi bảng `users` có `password_hash` là bằng chứng auth đã hoạt động. Không coi image PostgreSQL có pgvector là đã có retrieval. Chỉ đánh dấu tính năng hoàn thành sau test tương ứng.

Tại thời điểm lập v1.0 chỉ thêm PLAN.md. Trong Bước 00 ngày 02/11/2026 đã đồng bộ CLAUDE/AGENTS/README/eval/ADR instructions, thêm audit và cập nhật KNOWLEDGE; code/schema/dependencies/hạ tầng vẫn giữ baseline cũ. Bảng khảo sát 01/11 ở trên là dữ liệu lịch sử; trạng thái hiện tại xem audit. Spec là nguồn business rules; PLAN quy định thứ tự, lựa chọn thí nghiệm và cách kiểm chứng.

## 3. Cấu hình máy và cách bố trí tài nguyên

### 3.1. Máy đang dùng

Thông tin dưới đây đọc từ Windows, không phải benchmark inference:

| Hạng mục | Quan sát | Tác động đến kế hoạch |
|---|---|---|
| CPU | Intel Core i7-1165G7, 4 cores / 8 logical processors | Embedding CPU là đường chạy thực tế; tránh nhiều tiến trình inference tranh CPU |
| RAM vật lý | Khoảng 15,7 GiB, tương đương máy RAM 16 GB | Cần tính cả Windows, IDE, Docker, API và worker |
| GPU được hệ thống báo | Intel Iris Xe Graphics; không thấy NVIDIA trong kết quả khảo sát | Không lập kế hoạch dựa trên CUDA/GPU rời |
| Ổ C | Còn khoảng 8,9 GiB | Ưu tiên xử lý chỗ trống trước tải dependencies/model/images |
| Ổ D | Còn khoảng 80,0 GiB | Ứng viên đặt model cache và dữ liệu dev |
| Ổ E | Còn khoảng 90,3 GiB | Phương án thay thế cho cache/artifacts |

Dung lượng là ảnh chụp tại thời điểm đọc, sẽ thay đổi. Không dùng trường Windows `AdapterRAM` để kết luận Iris Xe có VRAM riêng dùng cho LLM. Không suy ra các phân vùng D/E là ổ vật lý khác hoặc SSD nhanh hơn C.

**Quyết định cho M1:** không cần mua GPU để bắt đầu; chưa nên lấy local LLM làm đường chạy chính. Nếu sau đo CPU retrieval đạt nhu cầu, GPU không phải điều kiện hoàn thành portfolio này.

### 3.2. Ngân sách RAM khởi đầu

Đây là ngân sách lập kế hoạch, phải thay bằng số đo RSS/working set thật:

| Nhóm | Mức dành chỗ dự kiến | Ghi chú |
|---|---|---|
| Windows + IDE + browser | 5–6 GiB | Giảm tab và ứng dụng nền khi benchmark |
| PostgreSQL + Qdrant + Docker/WSL | 2–3 GiB | Đo tổng VM/container, tránh cộng trùng cùng một vùng nhớ |
| API + worker + embedding + frontend dev | 3–4 GiB | Bao gồm khả năng hai process load hai bản model |
| Dự phòng | Ít nhất 2 GiB | Không xem swap liên tục là trạng thái ổn định |

Bắt đầu 1 ingestion worker, 1 query đồng thời khi đo, embedding batch 4; thử batch 8 chỉ khi đủ RAM. Giới hạn số threads inference, thử 2 rồi 4 và đo thay vì để mọi process tự lấy toàn bộ logical CPUs. Hạn mức 2 LLM calls đồng thời của spec là trần ban đầu, không bắt buộc phải dùng hết.

Nếu RAM vượt khoảng 85% kéo dài hoặc máy paging mạnh: giảm batch/concurrency, tắt local LLM, tránh load BGE-M3 cùng E5, rồi đo lại. Đây là ngưỡng cảnh báo vận hành đề xuất, không phải SLA.

### 3.3. Ổ đĩa, cache và Windows/Docker

1. Trước cài thư viện AI, kiểm tra chỗ trống của ổ chứa virtualenv, cache và Docker disk image. Mục tiêu dành tối thiểu 20–30 GiB cho môi trường/dependencies/images và khoảng 10 GiB cho thử nghiệm model ban đầu; đây là dự phòng, không phải dung lượng download đã đo.
2. Đề xuất cache ở `D:\AI-Cache\huggingface`; cấu hình biến `HF_HOME` trước import thư viện. Chỉ lưu tokenizer/weights của model/revision cần thử, không clone toàn bộ mọi định dạng checkpoint. Cơ chế `HF_HOME` được mô tả trong [Hugging Face environment variables](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables).
3. Kiểm tra riêng Docker data location và giới hạn WSL2. Chỉ đổi đường dẫn/cache model không làm Docker virtual disk chuyển khỏi C. Việc di chuyển Docker data phải theo hướng dẫn hỗ trợ của phiên bản đang dùng, có backup; không kéo thả/xóa VHDX thủ công. [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/).
4. Repo hiện ở C; `.venv`, pip/npm cache và build layers vẫn có thể làm đầy C. Nếu cần chuyển workspace/env sang D, thực hiện như một thay đổi riêng có kiểm tra, không tự xóa bản gốc.
5. Dev trên host dùng DB port `localhost:5433`; container dùng hostname `db:5432`. Qdrant dev dự kiến `localhost:6333`, container dùng `qdrant:6333`. Không trộn hai kiểu URL trong cùng profile.
6. Khi container cần model cache trên host, mount cache và đặt biến môi trường bằng **đường dẫn trong container**, không dùng trực tiếp `D:\...` trong Linux container.
7. Pin Python runtime và lockfiles hiện có trước khi thêm thư viện. Cài PyTorch CPU theo hướng dẫn chính thức tại thời điểm cài; không tải CUDA toolkit chỉ vì đang làm AI.

Không có thao tác di chuyển cache, cài runtime hay thay đổi Docker được thực hiện trong lần viết kế hoạch này.

### 3.4. Nếu đổi sang máy khác

| Cấu hình tham khảo | Hướng triển khai nên thử | Giới hạn cần kiểm chứng |
|---|---|---|
| 8 GB RAM, CPU-only | Embedding nhẹ + hosted LLM; tối giản process | Có thể không đủ cho toàn stack; cân nhắc máy/DB dev khác trước cài nặng |
| 16 GB RAM, CPU-only — máy hiện tại | E5 CPU + hosted LLM | Đo query embedding latency và hai bản model API/worker |
| 32 GB RAM, CPU-only | Có dư địa thử BGE và local LLM nhỏ tuần tự | RAM lớn hơn không tự làm decoding CPU đủ nhanh |
| 16–32 GB RAM + GPU 8 GB VRAM | Thử một model quantized nhỏ, hoặc dùng GPU cho embedding | Context/KV cache và model chạy đồng thời có thể gây OOM |
| 32 GB RAM + GPU 12–16 GB VRAM | Nhiều dư địa thử 4B/8B quantized và reranker | Vẫn phải benchmark tiếng Việt, JSON, citation và RAM/VRAM |

Các cấu hình này là nhánh thử nghiệm, không phải khuyến nghị mua phần cứng hay bảo đảm một model sẽ chạy vừa. Chỉ cân nhắc thuê GPU ngắn hạn khi đã có script benchmark và câu hỏi cần trả lời bằng phép đo.

## 4. Chọn model và cấu hình AI

### 4.1. Embedding: bắt đầu nhỏ, so sánh có kiểm soát

| Candidate | Thông số từ model card | Vai trò trong project |
|---|---|---|
| `intfloat/multilingual-e5-small` | 384 chiều; input tối đa 512 tokens; cần prefix `query: ` / `passage: `, kể cả tiếng Việt | Baseline CPU đầu tiên. [Model card](https://huggingface.co/intfloat/multilingual-e5-small) |
| `BAAI/bge-m3` | 1024 chiều; sequence length 8192; có dense/sparse/multi-vector; không cần query instruction như một số BGE khác | Challenger; M1 chỉ thử dense. [Model card](https://huggingface.co/BAAI/bge-m3) |

**Cấu hình thí nghiệm đề xuất:**

- E5: chunk target 350 tokens, overlap 50 theo tokenizer embedding; đếm thêm heading, prefix và special tokens. Assert input không vượt giới hạn trước encode; không để thư viện âm thầm truncate điều kiện chính sách.
- BGE: lần thử riêng bắt đầu chunk 500/overlap 75 như spec; chưa dùng context dài tối đa chỉ vì model hỗ trợ.
- CPU: bắt đầu FP32 để có baseline đơn giản. ONNX/OpenVINO hoặc quantization chỉ thử sau khi có số đo và đối chiếu retrieval; không đổi runtime + chunker + model cùng lúc rồi quy hết cải thiện cho model.
- Model adapters tách `embed_query` và `embed_documents`; normalize theo cấu hình pin; collection metric cosine. Vector dimension/fingerprint phải được kiểm tra lúc startup.
- Không trộn vector hai model hoặc revision khác nhau trong cùng collection; tên thí nghiệm dự kiến `knowledge_e5_small_v1` và `knowledge_bge_m3_v1`.
- Muốn so **chỉ model**, dùng cùng các source-span chunks có độ dài hợp lệ cho cả hai tokenizer. So E5-350 với BGE-500 là so cả pipeline, phải ghi đúng tên thí nghiệm.

**Quy tắc chọn:** đầu tiên loại cấu hình OOM, truncate âm thầm hoặc không tái lập. Sau đó so dev Hit@5/Recall@5, query latency, ingestion throughput, peak RAM và lỗi theo nhóm câu hỏi. Nếu chênh lệch chất lượng nhỏ/không rõ trên tập ít mẫu, ưu tiên cấu hình đơn giản hơn; không suy ra BGE chắc chắn tốt hơn chỉ từ kích thước.

### 4.2. LLM sinh câu trả lời: hosted trước

Shortlist được đối chiếu tài liệu nhà cung cấp ngày 01/11/2026:

| Candidate | Cách dùng đề xuất | Điều kiện chọn |
|---|---|---|
| `gemini-3.5-flash-lite` | Hosted baseline; model code stable, có structured outputs | Đạt smoke test JSON/citation/abstention trên dev. [Tài liệu model](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) |
| `gemini-3.6-flash` | Hosted challenger trên cùng gold context | Chỉ đổi mặc định nếu chất lượng/độ trễ/chi phí thực đo phù hợp. [Tài liệu model](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash) |

Danh sách trên không khẳng định quyền truy cập của tài khoản đã có, hoặc đây là hai model tốt nhất. Trước khi chốt, kiểm tra endpoint, quota, giá, vòng đời model và yêu cầu lưu trữ dữ liệu của tài khoản. Nếu model không khả dụng, chọn một model text stable khác rồi chạy lại cùng smoke set; không đổi âm thầm trong eval run.

Giữ `LLMProvider` theo adapter trong spec. Gemini có endpoint tương thích tại `https://generativelanguage.googleapis.com/v1beta/openai/`; cần smoke-test structured schema, usage, timeout và tham số cụ thể, không giả định mọi provider tương đương. Đây là endpoint **Google**, không phải sử dụng dịch vụ OpenAI. [Gemini compatibility](https://ai.google.dev/gemini-api/docs/openai).

**Cấu hình ứng dụng khởi đầu:**

- Evidence budget 4.000 tokens, output target 800 tokens, safety margin 256; đếm theo tokenizer/cơ chế counting phù hợp provider. Không dùng token count E5 thay cho LLM.
- Cap context vận hành ở mức đủ cho pipeline, ví dụ 8.192 tokens; đây là giới hạn ứng dụng tự đặt, không phải context tối đa công bố của model hosted.
- Tắt built-in web search, file search, code execution và tools. Model chỉ tổng hợp text do retrieval của project cung cấp; không upload toàn PDF để provider thay luôn RAG pipeline.
- Pin prompt/schema version và decoding settings model hỗ trợ. Không ép một temperature cho mọi model; ưu tiên cấu hình được hỗ trợ và ghi lại chính xác.
- Đặt thinking ở mức thấp phù hợp khi API hỗ trợ; đo billed usage thực. Thinking/output caps phải được kiểm tra để tránh JSON bị cắt khi còn thiếu output budget.
- Một lần repair schema/citation, tối đa hai calls/query trong deadline chung. Hết quota, refusal, JSON sai và timeout không trở thành câu trả lời doanh nghiệp giả.
- Chỉ corpus giả lập/được phép mới gửi API. Key ở backend; không đưa vào frontend, dataset, logs hay benchmark config.

### 4.3. Local LLM: thí nghiệm sau khi baseline đã chạy

Candidate: `Qwen/Qwen3-4B`, có chế độ non-thinking; có thể thử bản GGUF quantized qua runtime local. Giữ provenance của bản quantized, model digest và runtime version, không coi mọi file tên “Qwen 4B” là tương đương. [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B).

Trên máy hiện tại:

1. Chỉ tải sau khi đã giải quyết cache/đĩa, chạy thử một model tại một thời điểm.
2. Bắt đầu quantization 4-bit, context 4.096, concurrency 1, non-thinking nếu runtime hỗ trợ. Đây là cấu hình thử, chưa bảo đảm đủ nhanh trên CPU.
3. Với context 4.096, giảm evidence budget xuống khoảng 2.000 tokens, dành chỗ cho system/question/output; không giữ nguyên 4.000 evidence của hosted profile.
4. Đo cold load, first response, total latency, tokens/second, peak RAM, JSON valid rate, correctness và citation correctness trên cùng dev set.
5. Muốn so model công bằng, chạy thêm hosted ở cùng evidence budget/context package; không đổ lỗi cho local model khi nó được cấp ít bằng chứng hơn.
6. Nếu máy paging hoặc latency không phù hợp demo, giữ hosted mặc định và ghi local experiment là hạn chế đã đo. Local chưa đủ tốt không làm project RAG thất bại.

Ollama là một runtime ứng viên có bản Windows; cần cấu hình context thực tế ở runtime, không chỉ tin giới hạn trong model card. [Ollama Windows](https://docs.ollama.com/windows), [context length](https://docs.ollama.com/context-length).

Ước lượng weights thô `parameters × bits / 8` chỉ là cận dưới: 4B ở 4-bit khoảng 2 GB trước overhead. RAM/VRAM thực còn tokenizer, runtime, quantization metadata, KV cache, buffers và context; không dùng công thức này làm cam kết “máy 2 GB chạy được”.

### 4.4. Reranker và hybrid — chỉ sau M1

`BAAI/bge-reranker-v2-m3` là cross-encoder candidate để chấm lại cặp query–passage, không phải embedding thay thế. [Model card](https://huggingface.co/BAAI/bge-reranker-v2-m3).

Trên CPU hiện tại, thử top-N 10 rồi 20, batch nhỏ; đo thêm thời gian/RAM trước khi bật runtime. Reranker chỉ có thể sắp xếp evidence đã có trong candidates, không cứu được evidence chưa retrieve. Nếu lỗi chủ yếu là mã BM-07 hoặc thuật ngữ chính xác bị bỏ sót, thử lexical/hybrid trước. Nếu candidate có nguồn đúng nhưng final Top-K sai, reranker mới là giả thuyết phù hợp.

### 4.5. Những quyết định phải ghi trước khi freeze baseline

| Nhóm | Trường cần lưu |
|---|---|
| Embedding | Model/revision, tokenizer, dimension, precision, device, batch, normalization, query/document preprocessing |
| Parsing/chunking | Parser version, source-span convention, token target/overlap, xử lý heading/table |
| Retrieval | Collection/index manifest, cosine, candidate_k, final_k, filters, cutoff nếu đã calibration |
| LLM | Provider, exact model ID/version nếu có, prompt/schema, context budget, output/thinking/decoding settings |
| Môi trường | OS, CPU/GPU/RAM, Python/runtime, lockfiles, git commit |
| Evaluation | Corpus/dataset hashes, split, gold mapping, số mẫu, judge/human rubric, thời điểm chạy |

Hosted stable ID có thể không pin được toàn bộ weights: ghi ngày chạy và version metadata provider trả về, nêu giới hạn tái lập. Với local, pin revision/digest; không dùng `latest` như chứng cứ model cố định.

## 5. Ngân sách API và giới hạn thí nghiệm

**Ngân sách đã được người dùng chọn ngày 02/11/2026: 0 USD, chỉ dùng free tier.** Không tự bật billing, paid model/tier hoặc paid fallback; hết quota thì dừng/hoãn model run. API key/quota của tài khoản thật chưa được xác minh, cần chuẩn bị trước Bước 03. Ví dụ tính phí bên dưới chỉ để học cách dự toán, không phải quyền chi tiêu hoặc kế hoạch dùng paid tier.

Giá Standard đọc ngày 01/11/2026 cho Gemini 3.5 Flash-Lite: **0,30 USD/1M input tokens**, **2,50 USD/1M output tokens, gồm thinking**. Kiểm tra lại trước trả phí; free tier/quota không phải cam kết đủ cho benchmark. [Bảng giá chính thức](https://ai.google.dev/gemini-api/docs/pricing).

```text
Chi phí = input_tokens / 1.000.000 × giá_input
        + billed_output_tokens / 1.000.000 × giá_output
        + các khoản khác nếu thực sự bật
```

Ví dụ giả định 1.000 calls, mỗi call 5.000 input + 800 billed output tokens: `5 × 0,30 + 0,8 × 2,50 = 3,50 USD`. Đây là phép tính dự toán, chưa gồm repair/retries, phần thinking vượt giả định, thuế hay model khác. Không phải benchmark usage thực tế.

Quy tắc kiểm soát chi phí của project:

- Bắt đầu 5–10 câu smoke, sau đó 15–20 câu dev; chỉ chạy test đầy đủ khi đã freeze cấu hình.
- Đo retrieval không gọi LLM. Dùng oracle context để so LLM mà không re-embed corpus nhiều lần.
- Ghi calls/tokens/cost theo run; usage thiếu thì `null`, không ghi 0. Với ngân sách đã chọn 0 USD, không thực hiện paid calls; xác minh free-tier project/quota trước model run, không coi chi phí chưa biết là miễn phí.
- Giới hạn 1 request đang chạy trong benchmark đầu, backoff có giới hạn khi 429; không spam retry và không chuyển API key để né quota.
- Một query tối đa hai calls tính cả repair; timeout bị mất response vẫn có khả năng phát sinh usage, không giả định miễn phí.
- Ragas/LLM-as-judge tạo thêm calls; để P1. Human review tập nhỏ là baseline M1.
- Nếu chỉ dùng free tier, lịch eval phải tính rate limits thực của tài khoản. Khi không có API, vẫn hoàn thiện parsing/retrieval; full Q&A chỉ đánh dấu xong sau khi chạy model thật.

## 6. Chuỗi triển khai và điều kiện chuyển bước

```mermaid
flowchart TD
    S00[00 Chot scope va audit code] --> S01[01 Moi truong va tai nguyen]
    S01 --> S02[02 Corpus va gold labels]
    S02 --> S03[03 Model smoke tests]
    S03 --> S04[04 Schema va auth]
    S04 --> S05[05 Parsing va chunking]
    S05 --> S06[06 Worker va indexing]
    S06 --> S07[07 Retrieval va eval baseline]
    S07 --> S08[08 Answering va citations]
    S08 --> S09[09 Delete va failure recovery]
    S09 --> S10[10 UI va E2E]
    S10 --> S11[11 Freeze va final evaluation]
    S11 --> S12[12 Dong goi va demo M1]
    S12 --> P1[P1 Hybrid rerank local model]
```

Mỗi bước có kết quả quan sát được và kiểm tra trước khi chuyển tiếp. Viết test cùng feature; bước 09 là kiểm tra tích hợp và race/failure bổ sung, không phải lần đầu mới nghĩ đến độ tin cậy.

| Bước | Công việc chính | Ước lượng person-hours | Gate |
|---|---|---|---|
| 00 | Scope, audit và đồng bộ hướng dẫn | 1–2 | Không còn hướng dẫn mâu thuẫn cho RAG |
| 01 | Môi trường, cache, quota, resource baseline | 3–5 | DB/Qdrant healthy, đủ chỗ trống |
| 02 | Corpus và gold dataset | 6–8 | Dev/test và source refs kiểm tra được |
| 03 | Model/API smoke tests | 4–6 | Ít nhất một embedding và một LLM chạy thật |
| 04 | Schema, migrations, auth | 6–10 | Scope/role/session ownership có test |
| 05 | Parsing và chunking | 10–14 | Nguồn/offset đúng, không silent truncation |
| 06 | Worker, embedding, publish index | 8–12 | Restart/retry không publish dữ liệu dở |
| 07 | Retrieval và chọn embedding | 8–12 | Có baseline retrieval report |
| 08 | Answering, citation, session | 8–12 | Output validate và failure contract đúng |
| 09 | Delete/cleanup/race/fault injection | 8–12 | Không lộ nguồn bị xóa hoặc worker stale |
| 10 | UI và end-to-end | 10–14 | Một luồng dùng được qua browser |
| 11 | Freeze, final eval, failure report | 6–10 | Có số đo và limitations tái lập |
| 12 | Compose, README, video, release checklist | 4–6 | M1 chạy lại được từ hướng dẫn |

Tổng khoảng **82–123 person-hours**, chưa cộng thời gian chờ tải model, xử lý tài khoản hoặc học công nghệ mới; dành thêm khoảng 20% dự phòng, thành khoảng **98–148 person-hours**. Hai người không tự động làm thời gian còn một nửa vì các bước phụ thuộc nhau. Hiệu chỉnh ước lượng sau bước 03 và 07.

### Bước 00 — Chốt phạm vi và chuẩn bị chuyển hướng

**Làm lần lượt:**

1. Đọc spec mục 3, 5.5, 18.3 và liệt kê tất cả P0; không mang lại STT/agent/approval.
2. Cập nhật `CLAUDE.md`, README và `eval/README.md` sang nguồn spec RAG; ghi M1/M2 mới, Qdrant, auth, citation/delete invariants và mã AT-Rxx.
3. Đọc migrations hiện có và vẽ mapping bảng/enum cũ → schema RAG. Quyết định reuse bằng chứng từ code, không dựa vào tên bảng giống nhau.
4. Chạy và ghi kết quả test/lint hiện có nếu môi trường đủ; phân biệt lỗi trước thay đổi với regression mới.
5. Lập checklist ngay trong issue/commit cho từng bước; lưu mốc code trước chuyển đổi theo workflow Git của nhóm.

**Đầu ra:** backlog P0 theo spec, danh sách reuse/migration và tài liệu hướng dẫn thống nhất.  
**Gate:** không còn rule “RAG chỉ thuộc M2” chi phối công việc mới; không xóa bảng/dữ liệu cũ tùy tiện.

**Kết quả 02/11/2026 — hoàn thành phạm vi Bước 00:**

- [x] Đồng bộ hướng dẫn sang RAG, giữ quy tắc xác nhận và ghi kiến thức.
- [x] Liệt kê đủ 23 FR P0, phần reuse/migration và tiêu chí AT-Rxx trong audit.
- [x] Ghi mốc HEAD `53879bfa96f082489cf74a1c0dc4c41acebc493f`, working-tree ban đầu và checksum migration; chưa tạo commit/tag.
- [x] Chạy kiểm tra nền bằng công cụ có sẵn: Ruff pass; ghi đúng pytest/frontend/DB blockers, không trình bày như tests pass.
- [x] Ghi lý do/kiến thức và việc kiểm chứng trong KNOWLEDGE K-012–K-014.
- [ ] Pytest và frontend lint/build thành công: chuyển thành đầu việc khôi phục môi trường Bước 01, chưa được chứng minh ở Bước 00.

Không có migration, cài dependencies/model, start service hoặc code RAG trong đợt này. Baseline bị chặn là giới hạn đã ghi, không phải bằng chứng lỗi ứng dụng hay chất lượng RAG. Chi tiết: [rag-transition-audit.md](docs/rag-transition-audit.md).

**Hậu kiểm được xác nhận riêng, 02/11/2026:** đã thêm guard DB test nội bộ, safe SQL identifier, tách imports fixture để chạy unit độc lập và cập nhật trạng thái trong spec. `tests/test_database_safety.py`: 56 cases pass; lint/format pass. Kết quả này không thay cho 8 tests legacy/integration hoặc AT-R01–23. Xem audit mục 7 và KNOWLEDGE K-015–K-016. Ở thời điểm hậu kiểm setup/lockfiles chưa thực hiện; kết quả khôi phục sau đó được ghi ở Bước 01 bên dưới.

### Bước 01 — Dựng môi trường có ngân sách tài nguyên

1. Thực hiện các kiểm tra cache/ổ đĩa ở mục 3; xác nhận đường dẫn và storage riêng cho dev/test.
2. Kiểm tra Docker daemon/WSL, Python, Node và lockfiles; không coi CLI đã cài là service đã chạy.
3. Thêm Qdrant vào Compose, persistent volumes và healthchecks; giữ PostgreSQL hiện có nếu phù hợp. Pin phiên bản image đã kiểm thử.
4. Cấu hình API/worker đọc đúng DB/vector URLs, storage và env; giữ secrets ngoài Git.
5. Tạo tài khoản API/key phù hợp nếu chọn hosted; kiểm tra quota/pricing trước smoke test. Chưa đăng ký GPU/server dài hạn.
6. Ghi idle RAM/CPU, dung lượng đĩa và config máy trước load model.

**Bổ sung từ audit Bước 00:** khôi phục virtualenv đúng Python trên máy hiện tại, cài frontend dependencies/tạo lockfile, xác minh DB test riêng và chạy lại pytest/lint/build trước coi môi trường sẵn sàng. Virtualenv hiện trỏ Python 3.13 ở máy cũ; system Python 3.12.8 không có đủ app dependencies. Không sửa đường dẫn pyvenv.cfg rồi coi môi trường đã tái lập.

Guard hiện chỉ nhận URL PostgreSQL/psycopg với host local/Compose, DB name lowercase ASCII kết thúc `_test` khác DB development, không query/fragment. Khi khôi phục môi trường, pin cả dev tool dependencies (pytest/httpx/Ruff), tạo frontend lockfile và kiểm chứng đường tạo/migrate trên PostgreSQL thật; đừng coi 56 guard unit cases là full backend pass.

**Kết quả 02/11/2026 — hoàn thành Bước 01:**

- [x] Venv mới Python 3.12.8; giữ backup venv cũ, thêm dev lock và frontend package-lock.
- [x] Caches pip/npm/HF dự kiến trên D; HF cache rỗng, chưa tải weights. Không đổi PowerShell execution policy hoặc Docker disk location.
- [x] PostgreSQL 16.15 và Qdrant 1.20.0 healthy, image digests cố định, volumes bền vững; kết nối từ host và persistence qua recreate đã kiểm chứng.
- [x] 64 cases pass (56 guard + 8 legacy); frontend lint/build, pip check và Ruff đạt; một backend deprecation warning được ghi rõ.
- [x] Config Qdrant/storage/upload, .env.example và .env riêng đã cập nhật có giữ credentials; secrets/cache/runtime artifacts được ignore.
- [x] Người dùng chọn free tier, trần 0 USD; chưa gọi API và chưa kiểm chứng key/quota. Việc đó là điều kiện trước smoke Bước 03.
- [x] Resource snapshot, commands và giới hạn còn lại ghi tại [environment-step01.md](docs/environment-step01.md); kiến thức K-017–K-021.

C free cuối snapshot ~10,96 GiB, host free RAM ~3,2 GiB; chỉ coi đủ cho baseline đã kiểm tra, chưa cam kết chạy model lớn. Đây là snapshot kết thúc Bước 01; kết quả corpus sau đó ghi ở Bước 02.

**Đầu ra:** môi trường DB/Qdrant hoạt động, env mẫu, resource snapshot và giới hạn chi phí nhóm chọn.  
**Gate:** kết nối thật tới hai storage, không đầy C khi cài dependencies; môi trường test tách biệt.

### Bước 02 — Tạo corpus và tiêu chuẩn đánh giá trước tối ưu

1. Viết 8–12 tài liệu giả lập theo domain SME: chiết khấu, onboarding, nghỉ phép, nghiệm thu, mã biểu mẫu; đủ PDF text/DOCX/TXT/MD.
2. Tạo fixture scan, blank, encrypted, mixed PDF và malformed file riêng cho parser/security tests.
3. Soạn 30–60 câu gán nhãn; gợi ý bắt đầu 45 câu: khoảng 15 dev và 30 test. Có ít nhất 5 câu unanswerable trong toàn bộ set, và có đại diện trong cả hai split.
4. Có direct fact, paraphrase, exact identifier, nhiều điều kiện/tài liệu và mâu thuẫn; không tạo toàn câu dễ có từ trùng nguyên văn.
5. Người A gán answer/evidence; người B kiểm tra độc lập. Evidence ban đầu bám document/page/quote/block logic, hoàn thiện canonical span mapping sau bước 05.
6. Tách các paraphrase cùng sự kiện vào cùng split; giữ test khỏi quá trình chọn model/prompt.
7. Lưu corpus hashes, dataset version và rubric đúng spec mục 14; viết metric tests trên dữ liệu giả nhỏ ngay từ đây.

**Đầu ra:** corpus manifest, dev/test JSONL, answer rubric và human review notes.  
**Gate:** với từng câu, người đọc xác minh được đúng/không có đáp án; chưa phụ thuộc random chunk UUID. Không dùng output model làm gold.

**Kết quả 02/11/2026 — phần kỹ thuật xong, human gate còn mở:**

- [x] Mục 1: 10 tài liệu giả lập, đủ PDF text/DOCX/TXT/MD và 35 canonical author blocks.
- [x] Mục 2: 8 fixtures riêng, có scan/blank/mixed/encrypted, malformed/spoofed/adversarial inputs.
- [x] Mục 3: 45 câu có đáp án/evidence **nháp**, 15 dev/30 test và 6 unanswerable.
- [x] Mục 4: đủ các nhóm câu; partial cho điều kiện chưa biết và xung đột hiệu lực.
- [ ] Mục 5: **0/45 human-approved**. Người A cần gán/xác nhận nhãn từ nguồn; người B kiểm tra độc lập. Không dùng bản nháp do trợ lý soạn như human gold.
- [x] Mục 6: chia theo family, kiểm tra cả source block không rò rỉ dev/test.
- [x] Mục 7: manifest/SHA-256/version/rubric/ledger, validator và metric primitives; **37 tests pass**, Ruff/pip check đạt.

Artifacts và hướng dẫn review: [dataset README](eval/datasets/README.md), [báo cáo Bước 02](docs/dataset-step02.md). `author-v1` chưa phải parser version; remap spans sau Bước 05. `--require-reviewed` hiện từ chối đúng vì nhãn chưa duyệt; cần snapshot reviewed trước final benchmark. Không gọi model/API, không benchmark hoặc triển khai Bước 03 trong đợt này. Đợt smoke sau cần xác nhận riêng, kiểm tra quota free tier và tài nguyên theo trần 0 USD.

### Bước 03 — Smoke test models trước xây toàn bộ pipeline

1. Chạy embedding baseline trên 20–50 đoạn ngắn có tiếng Việt; kiểm tra dimension, số vector, finite values, normalization, prefix và thời gian batch.
2. Kiểm tra tokenizer với heading + đoạn gần giới hạn input. Việc encode không báo lỗi chưa chứng minh không bị truncate.
3. Gọi hosted LLM với 5–10 câu có gold context thủ công; yêu cầu structured claims/evidence IDs, có trường hợp thiếu nguồn và mâu thuẫn.
4. Kiểm tra endpoint có thực sự nhận schema/thinking/output settings; đo token usage và latency. Mô phỏng lỗi adapter bằng stub, tách khỏi smoke inference thật.
5. Nếu đủ tài nguyên, smoke BGE lần lượt sau khi unload E5; chưa chạy ma trận nhiều model hoặc reranker.
6. Lưu model fingerprint và compatibility result. Chọn một cấu hình tạm để xây pipeline, chưa tuyên bố đó là model chiến thắng.

**Đầu ra:** `model_smoke` report dự kiến với pass/fail, timings, peak RAM, số calls/cost và cấu hình.  
**Gate:** có đường inference thật cho embedding + LLM, không OOM; ít nhất một schema response được backend validate. Kết quả định tính sẽ đo đầy đủ ở bước 07/11.

**Kết quả đợt được xác nhận 03/11/2026:**

- [x] Chốt Bước 02: 45/45 human-approved, publish `eval/snapshots/reviewed-v1`, strict validator đạt và hash cả review CSV. Các mục chờ human review ở phần kết quả ngày 02/11 phía trên là lịch sử trước đợt này.
- [x] Mục 1: E5-small revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, CPU FP32, batch 4/threads 2; 35 passages + 5 dev queries, vector 384 finite/L2 đạt; peak RSS mẫu 723,13 MiB.
- [x] Mục 2: prefix/heading/special tokens được tính; input 512 tokens encode thật, 513 bị reject trước inference.
- [x] Mục 3: Gemini 3.5 Flash-Lite gọi thật trên 4 câu dev và 1 conflict ad hoc; run đầu 4/5 qua validator, conflict retest riêng 1/1 đạt. Tổng 6 requests đã được duyệt, không retry/fallback.
- [x] Mục 4: native endpoint nhận JSON schema/output config, Pydantic/status/citation IDs validate outputs thật; usage/latency lưu trong run. Thinking/temperature giữ provider defaults, không tuyên bố đã kiểm chứng override/tắt thinking. Stub errors và safe diagnostics có tests.
- [ ] Mục 5 (tùy điều kiện, hoãn): chưa smoke BGE; chọn baseline nhẹ theo tài nguyên, challenger chuyển sang đợt so sánh Bước 07. Không chặn gate model smoke bắt buộc.
- [x] Mục 6: pin E5 revision/dtype/prefix; Gemini model/version, prompt v1/v2, schema/config/code fingerprints và reports được lưu. Chọn tạm E5 CPU + Gemini hosted, chưa chọn model thắng.

**72 eval tests pass**, Ruff đạt. [Báo cáo Bước 03](docs/model-smoke-step03.md), [hướng dẫn key](docs/gemini-free-tier-setup.md), [config smoke](eval/configs/model_smoke.json). Hai preflight ban đầu 0 calls/0 USD là lịch sử; live calls có cost null khi chưa có chứng từ, không dùng số đó để suy ra phát sinh phí. Project giữ Free tier, không bật billing. Bước 04 chưa được thực hiện.

### Bước 04 — Schema, migration và identity

1. Tạo migrations mới cho document/revision/source blocks/chunks, jobs, sessions/query runs/messages/citations theo spec mục 9.
2. Bổ sung constraints/indexes: duplicate hash, active job, lease/generation, session idempotency; giữ lịch sử migrations đã áp dụng.
3. Xử lý rõ `email` hiện có và `username` trong contract, role enum cũ và `knowledge_admin`; không tự coi approver cũ là admin tài liệu.
4. Seed workspace + admin/member, password hash, login/me, expiry và server-side scope.
5. Làm resource lookup thống nhất: 401/403/404/410 theo contract; test khác workspace và session owner.
6. Chuẩn hóa errors/request IDs, config validation và transaction boundaries trước mở routes khác.

**Đầu ra:** schema và seed/auth chạy được trên PostgreSQL thật.  
**Gate:** migration upgrade hoạt động, constraints có test, member không vượt quyền. Phủ AT-R09 và nền tảng AT-R19/23.

**Kết quả đợt được xác nhận 03/11/2026 — hoàn thành nền Bước 04:**

- [x] Mục 1: revision `20261103_rag04` sau migration legacy bất biến, thêm 10 bảng gồm RAG/auth tokens; public schema 22 tables kể cả alembic_version. Upgrade dev/test đạt, không drop bảng cũ.
- [x] Mục 2: partial unique/composite FK/checks được kiểm chứng PostgreSQL thật; migration từ legacy có dữ liệu và rollback schema tạm; downgrade từ chối RAG data.
- [x] Mục 3: giữ email/roles legacy, username backfill theo UUID, legacy rows inactive; knowledge_admin chỉ seed rõ, không auto-promote approver/demo_admin. Jobs có discriminator để giữ legacy processing mà RAG dùng state riêng.
- [x] Mục 4: Argon2id + random bearer token digest/expiry/revoke; seed admin/member từ secrets .env riêng. Login/me dev probe đạt, repeat seed không trùng/reset/promote.
- [x] Mục 5: 401/403/404/410, workspace/owner/admin isolation, document/job/session/run read scopes và source-history SQL masking có tests. AdminUser qua HTTP route test riêng; full upload/delete/retry matrix AT-R09 còn chờ endpoints ở bước sau.
- [x] Mục 6: envelope RAG/request IDs/cache no-store, generic validation/DB/500 errors, settings validation và transaction boundaries. Frontend apiFetch được đồng bộ data/error envelope.

**124 backend tests, 72 eval tests đạt**, Alembic check không schema drift, frontend lint/build, Ruff/pip check đạt. 1 Starlette TestClient/httpx deprecation warning đã ghi. [Report Bước 04](docs/schema-identity-step04.md), [ADR RAG-06](docs/decisions/0006-identity-and-rag-schema.md). Đây là nền AT-R09/19/23, không đánh dấu các acceptance cases end-to-end hoàn tất. Bước 05 chưa thực hiện; cần đợt xác nhận riêng.

### Bước 05 — Upload, parser và chunker giữ nguồn

1. Upload stream → size/type validation → SHA-256 → storage key → transaction document/revision/job; dọn file orphan khi lỗi.
2. Parse từng định dạng, giữ thứ tự block/page/line, raw và normalized text theo spec 7.3.
3. Phân biệt scan/blank/mixed/encrypted; limits thời gian, trang, ZIP entries/uncompressed bytes và số chunks.
4. Chunk theo cấu trúc rồi token budget của model đang dùng; giữ source spans, heading provenance, table headers.
5. Kiểm tra quote/location bằng mở nguồn thật, cả đầu/cuối trang, dấu tiếng Việt, xuống dòng và bảng.
6. Hoàn thiện gold canonical source-block mapping từ bước 02; mapping sai phải fail rõ, không lặng lẽ bỏ câu.
7. Test upload trùng đồng thời; đổi filename không được vượt dedup.

**Đầu ra:** source blocks/chunks kiểm tra được và parser fixtures.  
**Gate:** nền upload/parser/chunker của AT-R01–05; không text rỗng, offset giả, path traversal hoặc silent truncation. Phần `202 → ready`/job terminal của acceptance cases cần worker Bước 06. Nếu nguồn trích sai, sửa parser trước tăng model. Làm rõ phụ thuộc gate, không đổi trọng số hoặc bỏ yêu cầu acceptance end-to-end.

**Trạng thái 03/11/2026 — hoàn thành 7/7 đầu việc Bước 05:** admin multipart streaming/size/MIME/signature/hash, SQL transaction + compensating cleanup, concurrent duplicate một 202/một 409; bốn parser với hard subprocess timeout/resource bounds; chunks E5 local tokenizer với nguồn/heading/header provenance. Mapping mới giữ đủ 45 câu, 35 author blocks/47 references → 54 parser blocks/14 chunks; reviewed snapshot bất biến. **166 backend + 76 eval tests đạt** ở hai suites riêng; Ruff/pip check đạt. Xem [report và giới hạn](docs/parsing-upload-step05.md), [ADR RAG-07](docs/decisions/0007-source-preserving-ingestion.md). Không gọi LLM/tải weights/sửa UI; chưa commit/push. Chờ xác nhận đợt Bước 06.

### Bước 06 — Worker, embeddings và publish index

1. Worker riêng claim bằng transaction ngắn; lease heartbeat, retry/backoff, stage progress và terminal errors.
2. Gán generation cho attempt; chunk/point IDs ổn định trong attempt, không worker cũ ghi đè attempt mới.
3. Embed batch có timeout và model fingerprint; kiểm tra dimension/finiteness trước upsert.
4. Upsert Qdrant, xác minh manifest/point IDs; publish revision active trong DB transaction sau khi toàn bộ hoàn tất.
5. Implement restart/recovery và orphan cleanup, không giữ DB lock trong inference; shutdown không làm mất job vĩnh viễn.
6. Đo ingestion trên 1 rồi 10 tài liệu; điều chỉnh batch CPU sau số đo, không tăng concurrency theo cảm tính.

**Đầu ra:** upload → queued → processing → ready/failed hoạt động bằng worker thật.  
**Gate:** AT-R06–08; kill/restart và DB publish failure không sinh ready giả; nguồn staging không retrieve được.

**Trạng thái 03/11/2026 — hoàn thành 6/6 Bước 06:** worker standalone host, SKIP LOCKED/short transactions, heartbeat/token/generation fencing, E5 CPU child process deadlines, exact Qdrant/SQL manifests và atomic publication, bounded retry/admin retry, lease recovery/orphan reconciliation. Real smoke **1 cold doc 13,0251 s (model load 10,1699 s), 10 warm docs 4,5647 s/14 chunks**, 8 fixtures đúng; không quality benchmark. **196 backend + 76 eval tests đạt**, Ruff format/check 85 files, pip check đạt. Nền AT-R01–08 ở ingestion/worker đã có; endpoint search/source và SQL revalidation nghiệm thu tiếp Bước 07. [Report](docs/worker-index-step06.md), [ADR RAG-05](docs/decisions/0005-durable-ingestion-worker.md). Không gọi LLM/tải weights/sửa UI, không commit/push; chờ xác nhận đợt Bước 07.

### Bước 07 — Search-only và chốt embedding baseline

1. Implement `/search`: validate scope/filter → query embedding → active generation filter → vector candidates → SQL revalidation → ranked source chunks.
2. Làm source chunk/file endpoint có auth để kiểm tra retrieval ngay, chưa cần chat UI đẹp.
3. Pin dense cosine, candidate_k=20, final_k=5; không đặt score threshold khi chưa calibration.
4. Chạy dev set, Hit/Recall/MRR@1/3/5/10 và All-evidence cho câu nhiều điều kiện; báo thêm latency và số query failures.
5. Phân loại lỗi: parse mất nguồn, chunk mất điều kiện, exact term, embedding sai relevance hay filter/budget. Kiểm tra lỗi tầng dưới trước đổi model.
6. Nếu đủ thời gian/tài nguyên, so E5/BGE theo mục 4.1. Chọn cấu hình bằng số đo dev và RAM/latency; chưa nhìn test để chọn.
7. Freeze embedding/chunk/index fingerprint; reindex corpus đầy đủ khi đổi config. Cập nhật env/spec baseline nếu giá trị mặc định thay đổi.

**Đầu ra:** retrieval report đầu tiên, lựa chọn embedding có lý do và tập failure cases.  
**Gate:** AT-R10, AT-R21 và phần retrieval của AT-R22; search vẫn chạy khi tắt LLM. Không đánh giá model generation bằng một retriever chưa được kiểm tra.

**Trạng thái 03/11/2026 — hoàn thành mục 1–5,7 (6 mục bắt buộc):** search/source có auth, strict filter/mode/top-k, pinned query encoder/index và SQL revalidation; source plain text/PDF có checksum/nosniff. Dev-only real run 15 queries trên 10docs/14chunks, 13 answerable Hit@1=11/13/Recall@5=1/MRR@5≈0,923; multi-group n1, technical errors0/15. Unknown scores overlap nên không bật cutoff; phân tích hai top1 misses, không đổi index hoặc tune test. Freeze [config](eval/configs/dense.json); mục6 BGE hoãn vì chưa cache/RAM margin chưa validate. **222 backend + 86 eval tests đạt**, giữ warning baseline. [Report](docs/search-retrieval-step07.md), [ADR RAG-02](docs/decisions/0002-dense-retrieval-baseline.md). Chưa answering/delete/UI, không LLM/paid calls/model download/commit/push; chờ đợt Bước 08.

### Bước 08 — RAG answering, citations và session

1. Context builder chọn final evidence trong token budget; cấp E1… sau lọc, lưu map thực sự gửi model.
2. Viết prompt/version, structured claims schema và validators theo spec 8.7; metadata citation do backend dựng.
3. Có grounded/partial/insufficient_evidence; lỗi provider/JSON/citation là lỗi kỹ thuật. Bounded repair dùng cùng evidence map.
4. Thử **oracle-context mode chỉ trong eval**: cấp gold evidence thay retrieval. Nếu gold context còn trả sai, sửa prompt/schema/model trước sửa retriever.
5. Implement session owner, standalone questions ở P0, client_request_id, concurrency guard, deadline và transaction lưu answer/citations.
6. Kiểm tra total budget/thinking/output: nếu JSON bị truncation, điều chỉnh output/evidence budget trên dev rồi ghi config; không “sửa JSON” bằng bịa phần còn thiếu.
7. Chạy các ca không có nguồn, điều kiện thiếu, mâu thuẫn, E99, evidence bị context budget loại và prompt injection.

**Đầu ra:** `/chat/query` trả answer có nguồn hoặc trạng thái lỗi/thiếu bằng chứng đúng.  
**Gate:** AT-R11–15, AT-R19–20; logs không chứa secret/full context mặc định. Không để eval oracle context trở thành shortcut trong app.

**Trạng thái 04/11/2026 — hoàn thành 7/7 phạm vi triển khai Bước08:** POST/chat/query, token counting Gemini trên full request, E IDs sau packing, schema strict/status/claims, backend citations, bounded repair và technical failures; owner/idempotency/session locks, expiry recovery, atomic publish/source revalidation/replay/history. **276 backend +91 eval tests đạt**, Ruff check/format 108 files/pip check đạt. AT-R11–15/19–20 có fixture contract tests; model thật có3 oracle +2 API synthetic dev cases qua2runs, không coi là full human-quality/held-out acceptance. Run đầu chạm trần20 count calls trước generation cuối do2files→3chunks, giữ failed report; sửa runner preflight theo chunks và retest riêng unknown sau xác nhận bổ sung. Tổng5 generate+25count calls, không repair trong5 model outputs; human review pending. [Report/giới hạn](docs/answering-step08.md), [config](eval/configs/answering.json). Backend/prompt/model không đổi giữa hai runs; reviewed/mapping/reports cũ bất biến. Không tải model/paid fallback/UI/delete/commit/push. Trọng số giữ10/tổng102,5 → **65,9% / 100%**; chờ đợt Bước09.

### Bước 09 — Delete, privacy và kiểm thử lỗi liên tầng

1. Delete transaction chặn retrieval trước rồi tạo cleanup job; delete lặp idempotent.
2. Cleanup vector/file/blocks/chunks và snapshots; failure/retry không đưa document về ready.
3. Che/xóa answer lịch sử liên quan; replay query hoặc mở source không hồi sinh cached text.
4. Tạo race tests có barrier: delete lúc ingestion/query chạy, worker lease hết nhưng còn hoạt động, publish commit mất acknowledgment.
5. Fault injection DB/vector/model và retry đồng thời; giữ nguồn đã xóa ngoài mọi search nhánh.
6. Kiểm tra logs/traces không giữ bản sao text ngoài retention policy. Phân biệt hết quyền/xóa nguồn với không tìm thấy bằng chứng.

**Đầu ra:** document lifecycle hoàn chỉnh và báo cáo fault/recovery tests.  
**Gate:** AT-R16–18 cùng regression AT-R06–09/13–15/19; 0 vi phạm scope, citation-ID hoặc deleted-source trong bộ test bắt buộc.

**Trạng thái 04/11/2026 — hoàn thành 6/6 phạm vi Bước 09:** delete idempotent/admin/workspace scope, SQL disable và revoke ingest lease atomic với redaction/job; cleanup multi-collection/file/blocks/chunks/snapshots, retry/exhaustion/manual retry, lost commit acknowledgment và tombstone reconciliation. Trace mặc định giữ IDs/hash/spans, source revalidation trước generation và publish; legacy full/debug copies được scrub khi nguồn bị xóa. **302 backend +91 eval tests đạt**, Ruff 114 files/pip check đạt. Barriers kiểm tra delete tại count/generate/upsert; Qdrant/file/DB failures, expired leases, cross-workspace/role và search/source/history/replay có assertions. CLI cleanup-only chạy với model cache không tồn tại; worker xử lý durable jobs trước maintenance lỗi. [Report/giới hạn](docs/deletion-privacy-step09.md), [ADR RAG-08](docs/decisions/0008-document-deletion-and-retention.md). Không LLM calls, downloads, UI, commit/push; human-quality/held-out vẫn Bước 11. `(67,5+10)/102,5` → **75,6% /100%**. Bước 10 cần xác nhận UI riêng.

### Bước 10 — UI và một luồng end-to-end hoàn chỉnh

**Hoàn tất6/6 ngày11/11/2026:** [report retry](docs/browser-e2e-retry-20261110.md) ghi actual Chrome UI với admin/member,6native API capture cases, citation/source410/history redaction/delete, keyboard và reload/expiry401. DB fixture/Qdrant/storage đã cleanup, giữ evidence/ledgers; không sửa UI source trong đợt này. AT-R23 có bằng chứng kỹ thuật UI; chấm người và final held-out vẫn Bước11. Các trạng thái4/6 phía dưới là lịch sử trước đợt retry. Trọng số12 giữ nguyên, `(77,5+12)/102,5=87,3%`.

1. Thay navigation Operations bằng Login, Documents, Knowledge Chat; giữ các trang cũ ngoài demo RAG.
2. Documents: upload/list/status/warnings, polling có giới hạn, retry đúng điều kiện, delete confirmation và cleanup state.
3. Chat: session list, document filter, câu hỏi độc lập, loading/error/partial/abstention và nhãn AI-generated.
4. Source panel: filename, quote, PDF page hoặc DOCX block/TXT line; sanitize render, xử lý 410/401, không nguồn giả.
5. E2E bằng browser với admin và member: upload → ready → chat → click source → delete → query/source/history lại.
6. Kiểm tra tab/session navigation, polling cũ, reload/login expiry và bàn phím. Không hiển thị mock response như kết quả thật.

**Đầu ra:** demo chức năng xuyên suốt, frontend build/lint pass.  
**Gate:** AT-R23 và toàn luồng P0; người khác dùng được mà không cần developer sửa DB bằng tay.

**Bàn giao Bước 10 ngày 05/11/2026:** người dùng xác nhận code UI theo kế hoạch. Mục 1–4 đã có source và component/HTTP checks: 30 frontend tests/7files/0failed-skipped, build/lint đạt; auth/member/source HTTP qua Vite thật đạt. Các tests trả lời dùng fixtures có nhãn, không model thật. Browser access host không khả dụng, vì vậy mục 5 chưa chạy và mục 6 chỉ có phần kiểm tra component, chưa tính hoàn thành. Không đánh dấu human review hoặc AT-R23 pass. Giữ trọng số12, ghi nhận4/6 →8điểm quy đổi →83,4%/100%. Chưa bắt đầu Bước11; xem [report UI](docs/ui-step10-implementation.md) cho giới hạn và lệnh local.

**Cập nhật 10/11/2026:** đoạn bàn giao trên là lịch sử 05/11. Đợt 06/11 đã kiểm tra Edge/CDP với dữ liệu thật và sửa hai lỗi dialog; 36 frontend tests đạt, nhưng chưa có model answer thật và chưa chạy trọn luồng xóa/kiểm tra lại với hai role. Người dùng hiện thấy UI ổn; chưa ưu tiên polish tiếp. Checklist còn lại và cách thu evidence ở [kế hoạch kiểm chứng cuối](docs/final-validation-plan.md). Giữ 4/6, chưa đóng mục 5–6 bằng nhận xét thẩm mỹ hoặc số tests.

### Bước 11 — Freeze, final eval và báo cáo lỗi thật

**Sau human review adversarial12/11 — ghi nhận5/7:** [report](docs/human-review-adversarial-20261112.md), [ma trận23scenarios](.cache/adversarial-at14-scoring-20261112/acceptance-matrix.json), [held-out đã chấm](docs/human-review-heldout-20261112.md). Mục7đạt theo scope bằng chứng contract/native/human/browser kế thừa được ghi rõ; không sửa raw snapshots. Bước11chưa đóng gate vì mục1release, mục6conditional chưa cộng; Bước12còn mở.

| Mục | Trạng thái hiện tại | Bằng chứng/giới hạn |
|---|---|---|
| 1 | Hoàn thành 12/11 (R1) | Commit `0d0c323`…`edf6dab` và commit tài liệu trên `release/m1`. Source khớp 167 hash acceptance (blob chuẩn hóa EOL); bằng chứng ở `eval/reports/final-20261112/`. [Report](docs/release-m1-20261112.md). Chưa push/merge |
| 2 | Hoàn thành báo cáo baseline | 30attempted/29outputs/1error, human29/29; retrieval/answer/abstention/latency/usage và invoiceNone được báo rõ |
| 3 | Hoàn thành phân loại số đo | Tách unit/fake/SQL/native, warm/pacing/concurrency1; oracle lịch sử khác final, final oracle/no-context chưa đo và không suy score |
| 4 | Hoàn thành lượt đo concurrency1 | p50/p95 trên29success, retrieval30, một lượt/query hai phiên; không SLA/throughput/cold-start claim |
| 5 | Hoàn thành phân tích lỗi quan sát | Một lỗi q023provider503, no-retry/giữ mẫu số; không bịa thêm lỗi, q024partial được nhóm chấm2 |
| 6 | Chưa cộng tiến độ | Không tune production bằng test; nếu thay sau test phải ghi rõ và có holdout mới trước tuyên bố cải thiện |
| 7 | Hoàn thành theo phạm vi | Acceptance23/23scoped passes; AT-R14native/human2/2 và no-XSS/literal contracts đã đối chiếu; không giả all-native/browser rerun. Fresh setup cònBước12 |

**Cập nhật12/11:** [continuation](docs/final-continuation-20261112.md) đã chạy22câu chưa từng thử, cùng productionprotocol và allowance gốc. Composite30attempted/29outputs/1q023failed/0notattempted, tổng30generation/210count, cleanup verified. [Phiếu29outputs](docs/human-review-guide.md) còn0/29reviewed; chưa correctness/faithfulness/citation, fullAT-R hoặc release freeze. Không tự đóng mục1–7 bằng coverage/thành công kỹ thuật; giữ87,3%/100%. Các trạng thái8/30/chưa có continuation bên dưới là lịch sử, không là trạng thái mới nhất.

**Kết quả native attempt11/11:** [pacing/held-out](docs/final-heldout-20261111.md) đã có frozen candidate100+4 và10docs thực. Lượt dừng q023provider503 sau7outputs hợp lệ,22câu chưa chạy, mẫu số30. Caps60/210 chỉ dùng8/56, ledger/scope không reset; code/prompt không sửa sau khi nhìn test. Capture/replay/7phiếu output/cleanup verified. Đây là bằng chứng attempt thực, chưa đủ coverage/chấm người/fullAT-R để đóng đầu việc final hoặc cộng tiến độ. Trạng thái chưa mở/chạy test bên dưới là lịch sử trước lượt này; hiện test đã được loader/review pack đọc cho evaluation, chưa dùng tuning.

**Cập nhật đợt tiếp11/11:** [human review E2E](docs/human-review-practice-20261111.md) đã6/6 từ hai người; [shared orchestration SQL](docs/final-runner-sql-20261111.md) đã5tests với fakes và audit cleanup. Candidate mới protocol d15e3cea44fe9dca9dae1ec5d24cd20e7fbb85b253f97d90a87646baa8834498 thay candidate04562... ở root hiện tại, giữ archive cũ. Live30/review mới/full acceptance chưa chạy; native E5/Gemini trên runner mới chưa kiểm chứng. Không thay phiếu thực hành cho held-out hoặc đóng mục1–7 bằng integration pass. Đợt offline dưới đây ghi lịch sử trước thay runner.

**Chuẩn bị offline được xác nhận 11/11:** [runner/candidate/review pack](docs/final-eval-preparation-20261111.md), config public và hai bootstrap đã triển khai;148selectedtests/Ruff đạt. Candidate hash04562e68fa1c38d11188b545f9ceba4b38d2e1a49aac30cfad15cfa64f6e9f9b,99files+4bootstrap/locks verify; câu test chỉ hash/copy bytes, không parse/hiển thị. Không backend settings/SQL/HTTP/model imports trên đường prepare, không grant/ledger/execution mới; pending approval bị chặn trước held-out/runtime. Cap60generateContent/210countTokens là dự toán chưa duyệt,0USD. [Phiếu thực hành sáu câu E2E](docs/human-review-guide.md) đã có, human0/6. Nhánh native runner mới chưa chạy storage/inference: kiểm chứng orchestration bằng fakes trong đợt riêng trước khi duyệt live30 câu. Chưa đóng đầu việc final/release freeze/human/held-out/AT-R bên dưới; giữ87,3%/100%. Các ghi nhận10/11 phía dưới là lịch sử các đợt chuẩn bị trước.

**Chuẩn bị ngày 10/11/2026, chưa thực thi:** [protocol dự kiến](docs/final-validation-plan.md) phân biệt smoke và held-out. `eval/run_retrieval_eval.py` hiện chỉ chọn dev; `eval/run_answering_eval.py` hiện chạy synthetic-dev cases, không phải final evaluator. Cần đợt được duyệt để bổ sung/kiểm chứng công cụ offline trước model run, không tự dùng cờ `--split test` chưa tồn tại. Mọi live batch phải có số requests dự toán, hard caps/ledger và xác nhận free-tier/quota; ngân sách vẫn 0 USD. Chưa mở nội dung held-out để tune, chưa chạy final eval. Khi freeze cần ghi cả HEAD và hashes của source hiện hữu nếu working tree dirty; không tự commit để tạo mốc.

**Bổ sung sau đợt offline cùng ngày:** [toolkit mới](docs/final-eval-tooling.md) đã có split guard, hashes nguồn/chunks, replay denominator, worksheet hai người và persistent request ledger; verified bằng fixture/stub. Đây là chuẩn bị cho bước, chưa phải freeze bản release hay final benchmark. Phần tiếp theo cần runtime/capture adapter production, cài guard vào scope E2E và xác minh môi trường backend trước khi xin duyệt live batch. Hai runner cũ và reports/mapping/reviewed snapshot giữ nguyên.

**Bổ sung sau đợt runtime:** [adapter API](docs/runtime-capture-step11-preparation.md) đã có code cùng tests đi qua route/core answering thật với storage/retrieval/identity stubs; native live mode chưa chạy. Scope nguồn SQL yêu cầu DB test thực, collection/storage riêng và profile/mapping khớp; actual SQL integration còn chờ storage hoạt động. Không dùng ASGI fakes hoặc flags local để đóng full E2E/final held-out. Chưa tăng tỷ lệ Bước11 vì các đầu việc freeze/test/human review/acceptance đầy đủ vẫn chưa đạt.

**Bổ sung sau đợt storage/integration:** SQL adapter đã được kiểm bằng SQL/Qdrant thật trong [suite tổng hợp](docs/sql-capture-integration-20261110.md); generation/embedding vẫn giả. Không còn chờ bật storage theo snapshot đợt runtime ở trên; bước thực thi model vẫn chưa được duyệt/chạy. Chưa freeze release, chấm người hoặc mở held-out thật. Không đóng đầu việc1–6 bên dưới bằng integration pass.

**Bổ sung sau native smoke:** [hai câu runner-defined](docs/native-capture-smoke-20261110.md) đã qua actual E5/Gemini capture; 72source hashes/input freeze chỉ áp cho scope smoke đó. Đây chưa phải freeze release/corpus reviewed hoặc final run/human scoring theo đầu việc1–6. Không dùng 2/2 HTTP200 hoặc hai expected statuses để tăng progress/đóng gate; browser E2E tiếp theo vẫn cần phạm vi và request budget riêng.

1. Chốt code/config/prompt/corpus, ghi git commit và hashes; ngừng đổi model theo từng câu test.
2. Chạy test holdout sau freeze: retrieval, answer correctness, faithfulness/citations, abstention, error rate, p50/p95 và cost.
3. Tách unit/stub, real-model eval, warm/cold, retrieval-only, oracle-context và end-to-end; không cộng các nhóm thành một “accuracy”.
4. Đo latency ở concurrency 1; nếu lặp nhiều lượt, ghi số runs và không coi lặp cùng câu là mẫu độc lập.
5. Review failures thủ công; viết ít nhất 3 case nếu có đủ, kèm tầng lỗi và giả thuyết sửa. Có ít hơn thì báo đúng số quan sát.
6. Nếu sửa sau khi xem test, ghi test đã bị sử dụng cho tuning; cần holdout mới trước tuyên bố cải thiện tổng quát.
7. Chạy full AT-R01–23, ghi pass/fail/skipped và lệnh/môi trường thật.

**Đầu ra:** `manifest.json`, `config.json`, `per_question.jsonl`, `metrics.json`, `report.md` cho mỗi run; bảng acceptance status.  
**Gate:** số trong README truy ngược được raw artifacts; không mất lỗi kỹ thuật khỏi denominator, không tự đặt ngưỡng accuracy sau khi thấy kết quả.

### Bước 12 — Đóng gói, tài liệu và demo M1

1. Hoàn thiện Compose API/worker/frontend/DB/Qdrant theo topology cuối; migrations chạy bước riêng, model cache persistent.
2. Kiểm tra môi trường sạch/fresh volumes riêng: setup → migrate → seed → ingest → query. Không xóa volume dev để giả lập clean install khi chưa backup.
3. README có cách chạy Windows/container, env placeholder, model/cache download, resource đo thật, tests, dataset/eval và limitations.
4. Quay video 2–3 phút: câu có nhiều nguồn, click citation, câu không có đáp án, delete/source unavailable và benchmark report.
5. Viết đóng góp cá nhân, sơ đồ kiến trúc và trade-offs dựa trên commit/work thật; CV chỉ nêu chức năng đã có.
6. Kiểm tra repo không có secret, model weights, dữ liệu riêng tư, artifacts quá lớn hoặc kết quả giả.

**Đầu ra:** repository chạy lại được, video, report và checklist M1 hoàn thành.  
**Gate:** đạt Definition of Done của spec, không chỉ “chat được một PDF”. Nếu chưa đạt, báo phần còn thiếu thay vì đổi nhãn Done.

## 7. Lịch tham khảo hướng tới 15/11/2026

Lịch dưới đây là mục tiêu có điều kiện, không ghi đè gates. Với 2 người × 4 giờ tập trung/ngày × 14 ngày ≈ 112 person-hours, phạm vi này khá sát; nếu còn nhiều việc học/setup, cần thêm thời gian hoặc hoãn phần so sánh P1.

| Khoảng ngày | Trọng tâm | Điểm kiểm tra |
|---|---|---|
| 01–03/11 | Bước 00–03: scope, môi trường, corpus ban đầu, model smoke | Máy chạy được embedding + hosted inference, có dev/test sơ bộ |
| 04–06/11 | Bước 04–06: schema/auth, parser/chunker, worker/index | Upload thật → ready; nguồn đúng, recovery cơ bản |
| 07–09/11 | Bước 07–08: retrieval metrics, answer/citation/session | Có baseline dev và Q&A API có bằng chứng |
| 10–12/11 | Bước 09–10: cleanup/failure tests, UI E2E | Delete/auth/citation guardrails đúng; demo xuyên suốt |
| 13–14/11 | Bước 11–12: freeze/eval, clean setup, README/video | Có artifact và kết quả nghiệm thu |
| 15/11 | Dự phòng và kiểm tra bản trình bày | Không mở thêm model/feature trước demo |

Tại mỗi điểm kiểm tra, cập nhật thời lượng còn lại bằng tốc độ thực tế. Thứ tự cắt phần **tùy chọn**: local LLM → reranker/hybrid → UI inspector nâng cao → thí nghiệm model thứ hai. Có thể giảm corpus theo spec nhưng phải báo quy mô mới. Không cắt auth, evidence validation, xử lý lỗi, delete filtering hoặc baseline evaluation.

Nếu không thể đạt các bất biến P0 đúng hạn, ghi demo đang phát triển và kế hoạch hoàn thiện; không nới business rules để kịp ngày.

## 8. Cách làm việc của nhóm 2 người

Thứ tự tích hợp vẫn theo bước 00–12. Hai người có thể chia ownership để giảm chờ nhưng cùng review interfaces/gates:

| Người | Trọng tâm chính | Phần phải hiểu và review chéo |
|---|---|---|
| A | Corpus/parser/chunking, embedding, retrieval và metric scripts | Citation, context budget và nguồn bị xóa |
| B | Auth/schema/jobs/API, answer validation, UI và deployment | Source mapping, model config và evaluation methodology |
| Cả hai | Gán nhãn/kiểm tra chéo, model choice, fault tests, demo/report | Không chia thành một người chỉ AI, một người không hiểu AI |

Mỗi ngày ghi ngắn: đã chứng minh được gì, lỗi hiện nằm tầng nào, model/config nào đổi, số liệu nào vừa đo và bước/gate kế tiếp. Với coding assistant, giao một feature có contract + edge cases + acceptance tests; review thay vì giao toàn project trong một prompt.

## 9. M2 — tăng chiều sâu RAG sau khi M1 đạt

Thực hiện từng thí nghiệm, không triển khai cả danh sách cùng lúc:

1. **Phân tích baseline:** chọn nhóm lỗi lớn nhất; ví dụ exact identifiers không được retrieve, hoặc evidence đã có nhưng answer bỏ điều kiện.
2. **Hybrid khi có lý do:** thêm lexical/BM25 hoặc learned sparse, dùng cùng active-generation/workspace filters, RRF; ghi rõ tokenization tiếng Việt. Giữ dense-only để đối chiếu.
3. **Reranker khi candidates có nguồn đúng:** thử top-N 10/20, đo All-evidence/citation/latency và RAM. Không mặc định cải thiện chỉ vì thêm một model.
4. **Reindex/update revision:** staging + atomic switch, rollback, cleanup generation cũ; không trộn embedding spaces.
5. **Local LLM comparison nếu còn mục tiêu học self-host:** theo mục 4.3, tách chất lượng khỏi context-budget/resource khác biệt.
6. **Retrieval inspector và follow-up P1:** chỉ sau traces đủ rõ; multi-turn rewrite phải retrieve lại và có eval riêng.
7. **Judge tự động nếu cần mở rộng:** kiểm tra bias và mẫu human review; không dùng judge thay ground truth.

Gate M2: AT-R24–26 cho enhancement tương ứng, so sánh trên cùng dataset snapshot, ghi quality/latency/resource/cost. Nếu treatment không tốt hơn baseline, giữ baseline và báo kết quả âm. Không cần thêm STT/agent để gọi project đã hoàn thành.

## 10. Bảng xử lý khi kết quả không như mong đợi

| Triệu chứng | Kiểm tra trước | Hành động kế tiếp |
|---|---|---|
| Model tải/cài lỗi, disk full | Cache, virtualenv, Docker disk, dung lượng C | Sửa nơi lưu trữ; không tải thêm model thử vận may |
| OOM/paging | Số bản model đang load, batch, concurrency, context | Giảm tải; giữ CPU embedding nhẹ + hosted LLM |
| Search chậm | Query embedding vs Qdrant time, cold load, thread oversubscription | Warm model đúng cách, điều chỉnh threads/batch; đo lại trước đổi DB |
| Source không chứa câu cần tìm | Parser output và gold source mapping | Sửa parser/chunker; model lớn hơn không khôi phục text bị mất |
| Recall thấp với mã chính xác | Prefix/tokenization và loại lỗi dev | Thử lexical/hybrid ở M2 hoặc ghi limitation M1 |
| Candidate có nguồn đúng, final context không có | Dedup/ranking/budget | Sửa context packing hoặc thử rerank; không đổi LLM trước |
| Gold context đúng nhưng answer sai | Prompt, thiếu điều kiện, output/thinking cap | Chạy LLM challenger trên cùng oracle context |
| JSON/citation sai | Schema support, truncation, evidence map | Validate/repair giới hạn; lỗi vẫn sai thì fail thật |
| API 429/mất mạng | Quota, concurrency, timeout | Backoff có giới hạn, hoãn eval; demo search-only được nhưng ghi Q&A unavailable |
| Nguồn xóa vẫn xuất hiện | SQL revalidation, cache/history, stale generations | Chặn release và sửa lifecycle; không chỉ delete vector một lần |
| Không đủ thời gian | Gates chưa đạt, P1 đang chiếm thời gian | Bỏ P1 và làm rõ trạng thái P0 còn thiếu |

## 11. Checklist để bắt đầu và checklist hoàn tất

### Việc làm ngay ở phiên triển khai đầu tiên

- [x] Đồng bộ `CLAUDE.md`/README với spec RAG; xác nhận không triển khai STT/agent — hoàn thành Bước 00 ngày 02/11/2026.
- [x] Chọn cache D, giữ venv/repo và Docker disk location, kiểm chứng dung lượng cho baseline; chưa mua GPU — Bước 01.
- [x] Chốt trần model 0 USD/free tier — người dùng 02/11/2026. Provider/key/quota thật còn phải xác minh trước Bước 03.
- [ ] Chuẩn bị 2 tài liệu nhỏ + 5 câu có gold evidence để smoke test.
- [ ] Chạy embedding CPU và một LLM request thật, lưu model/config/resource report.
- [ ] Điều chỉnh lịch sau khi biết inference/setup thực tế mất bao lâu.

### Điều kiện kết thúc M1

- [ ] Tất cả bước 00–12 có đầu ra và gate được kiểm chứng.
- [ ] Có model/index manifest cố định và tài nguyên đo thực trên máy chạy demo.
- [ ] Upload/search/Q&A/source/delete/history hoạt động đúng quyền.
- [ ] AT-R01–23 pass; skipped/failed chưa xử lý không được che bằng demo thành công.
- [ ] Có retrieval + answer + abstention + latency/error/cost report với raw artifacts.
- [ ] Clean setup tái lập, README và video khớp code thật.
- [ ] Hạn chế, kết quả chưa đạt và đóng góp cá nhân được mô tả rõ.

## 12. Nguồn và cách cập nhật kế hoạch

Các thông số model/provider có liên kết chính thức ngay tại mục 3–5; đọc lại model card, API capabilities, pricing và lifecycle khi thực thi. Nhận định về máy dựa trên khảo sát Windows ngày 01/11/2026. Các mức RAM/batch/context/effort và ngân sách là **giả định kỹ thuật của kế hoạch**, không phải thông số nhà cung cấp bảo đảm hay benchmark đã chạy.

Tham khảo cài runtime khi bước 01 được thực hiện: [PyTorch — Start Locally](https://pytorch.org/get-started/locally/). Giữ spec là nguồn contract, lưu thay đổi model/config cùng eval run và cập nhật PLAN khi một gate cho thấy giả định ban đầu không còn phù hợp.

Các tên report/script/artifact chưa có trong repo được nêu như **đầu ra cần tạo** ở bước tương ứng. Kế hoạch này không tự tạo các artifact đó, không thay file cấu hình runtime và không ghi nhận tính năng chưa triển khai là đã hoàn thành.
