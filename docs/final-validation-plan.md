# Kế hoạch kiểm chứng cuối — Bước 10–12

**Sau merge/rescore adversarial12/11:** [human2/2](human-review-adversarial-20261112.md) hợp lệ/khớp, noadjudication; [ma trận mới](../eval/reports/final-20261112/acceptance/acceptance-matrix.json) đóngAT-R14theoscope→23/23scopedpasses. Đợt này thuần offline, giữ958protectedhashes/source167/oldheldout60/captures/ledgers/reviews. Không inference lại, không gộp devcases vàoheldoutaccuracy, không gọi consolidatedevidence làall-native/browserrerun. PLANv1.29ghi5/7mục2–5,7/**92,9%/100%**; release/mục6conditional/freshsetupBước12còn mở. Các snapshotpartial/human0/2bên dưới là lịch sử. Việc tiếp theo cần chốt scope release và packaging trước xác nhận mới; chưa tự thực hiện.

**Sau adversarial native12/11:** [hai câu synthetic/dev](adversarial-at14-20261112.md) đã hoàn tất,2generation+6count/8HTTP200 trong grant mới riêng4/14/0USD. Actual context/payload chứa attack2/2; không tools/0functioncalls, cleanup/source/heldout hashes verify. [Hai phiếu mới](human-review-guide.md) còn human0/2; không chạy lại Gemini hoặc chấm lại29heldout. AT-R14vẫnpartial,22scopedpasses, PLANv1.28giữ4/7Bước11/**91,8%/100%**. Release/freshsetup/Bước12chưa thực thi; các mô tả chưa có scope/native bên dưới là lịch sử.

**Sau acceptance rerun12/11:** [report](final-acceptance-20261112.md)/machine matrix (`.cache/at-20261112/acceptance-matrix.json`, chỉ lưu ở máy local) ghi22/23scoped passes, AT-R14partial;302backend+2newcontracts+69eval+36frontend tests đạt qua process/rerun riêng, lint/build và cleanup verify. Native/browser evidence kế thừa được ghi rõ, không calls mới hoặc reset held-out ledger. Native adversarial AT-R14cần scope/caps riêng; freshsetup/release/Bước12chưa thực thi. PLANv1.27giữ4/7mụcBước11, **91,8%/100%**. Các ghi nhận mới chỉ inventory/chưa rerun phía dưới là lịch sử trước đợt này.

**Sau human review12/11:** [report đã chấm](human-review-heldout-20261112.md) ghi29/29reviews đầy đủ/khớp, correctness2/2, strict success29/30giữ q023provider503, faithfulness34/34/citation36/36. Merge/rescore offline và60protected hashes đạt; raw snapshots pending được giữ nguyên. [Ma trận23AT/gaps](final-acceptance-gaps-20261112.md) đã đối chiếu, chưa fullAT rerun/freshsetup/release. PLANv1.26ghi4/7mục Bước11(2–5), **91,8%/100%**; snapshot pending0/29/87,3% bên dưới là lịch sử.

**Kết quả mới nhất12/11:** [continuation](final-continuation-20261112.md) chạy22/22câu còn lại, giữ nguyên productionprotocol/parentbinding/reservations và allowance60/210. Composite hai phiên30attempted/29outputs/1q023failed/0notattempted, tổng30generation/210count; count allowance đã hết. [Hai phiếu29outputs](human-review-guide.md) chưa chấm; fullAT-R/freshsetup/release còn mở,87,3%/100%. Không retry/reset/tune test. Các mô tả8/30/chưa triển khai continuation bên dưới là lịch sử trước đợt này.

**Kết quả đợt native11/11:** [held-out attempt](final-heldout-20261111.md) dừng ởq023generationHTTP503:7thành công/1lỗi/22chưa chạy trênplanned30.8generation/56count, pacing/ledger/archive/input và cleanup verified; [phiếu review mới](human-review-guide.md) chỉ có7outputs thành công. Candidate hiện tại `.cache/final-reviewed-baseline-20261111-paced/`,100files+4extras. Chưa final benchmark/full acceptance; không retry/reset scope one-shot. Continuation giữ allowance cho22câu còn lại là đề xuất chưa triển khai/duyệt. Các mục nói chưa mở test/no grant bên dưới là lịch sử trước attempt; hiện test được đọc để evaluation/review, không tuning.

**Cập nhật sau review/integration11/11:** [hai phiếu nhóm đã điền](human-review-practice-20261111.md) merge/rescore6/6, không bất đồng; [shared final runner](final-runner-sql-20261111.md) đạt5 SQL/Qdrant tests với fakes +148regression, cleanup verified. Candidate mặc định chuyển sang `.cache/final-reviewed-baseline-20261111-sql-verified/`,99files+4extras; archive cũ giữ nguyên, approval pending. Không mở/chạy30held-out hoặc gọi model. Các đoạn human0/6 dưới đây là lịch sử; final held-out/human review trên outputs mới còn pending.

**Ngày lập:**10/11/2026; **cập nhật11/11:** [Chrome E2E/QA](browser-e2e-retry-20261110.md) hoàn tất Bước10; final held-out/human review vẫn pending. Đã có [candidate/runner offline](final-eval-preparation-20261111.md), [hướng dẫn chấm](human-review-guide.md), toolkit/capture/SQL integration và native smoke. E2E dùng4generation/12count, không phải final benchmark. Candidate chỉ hash/copy câu test như bytes, chưa parse/hiển thị hoặc gọi model; dự toán60/210 chưa được duyệt. [PLAN](../PLAN.md), [spec mục14–15](../SME_Knowledge_Copilot_RAG_Specification.md), [đánh giá portfolio](portfolio-review-20261110.md).

## 1. Bằng chứng hiện tại và khoảng trống công cụ

**Browser attempt ban đầu, lịch sử10/11:** [harness](browser-e2e-20261110.md) bị tool guard chặn,0/0. [Retry được duyệt11/11](browser-e2e-retry-20261110.md) dùng chung allowance đã chạy6/6syntheticcases, source410/historyredaction/auth401/keyboard/navigation; cleanup verified. Không sửa snapshot0/0 của lượt đầu thành kết quả lượt mới. Human0/6 và final held-out vẫn pending.

| Thành phần | Đã có | Còn thiếu |
|---|---|---|
| UI | [Report](ui-step10-implementation.md):36tests/build/lint/ảnh desktop-mobile; [Chrome11/11](browser-e2e-retry-20261110.md) hoàn tất một luồng P0 hai role | Giữ coverage/giới hạn theo matrix chi tiết; final acceptance toàn bộ nằm Bước11 |
| Retrieval | [Dev baseline](search-retrieval-step07.md): 15 queries, 13 answerable, 14 chunks; toolkit mới có offline split/replay | Thu observations production được revalidate và báo số đo cuối |
| Answering | Smoke Bước08, native smoke2câu, E2E6câu đã human review; [runner SQL với fakes](final-runner-sql-20261111.md)5tests +148regression | Xác minh quota/scope rồi capture model thật trên reviewed test và human scoring outputs mới sau duyệt |
| Dataset | reviewed-v1: 45 câu đã duyệt, 15 dev/30 test; canonical mapping | Giữ split/hash và thu output thật, không tune bằng test |
| Đóng gói | Launcher dev trên máy đã setup | Fresh setup riêng và demo/release checklist Bước 12 |

Đọc source xác nhận [retrieval runner](../eval/run_retrieval_eval.py) lọc `split == dev`; [answering runner](../eval/run_answering_eval.py) chạy cases trong config smoke và chỉ nhận `--live`, `--case`, hai request caps. Không có lệnh final held-out sẵn để chạy chỉ bằng thêm `--split test`. Script gọi các services/imports có thể tạo tài nguyên; không chạy chúng để giả lập kiểm tra chỉ đọc.

**Quan sát môi trường trong đợt tài liệu 10/11:** thử dùng `backend/.venv/Scripts/python.exe -B -` để kiểm tra liên kết chỉ đọc đã thất bại trước khi script chạy: venv báo không tìm thấy Python gốc tại đường dẫn Python312 dưới LocalAppData. Đã thay phép kiểm tra tài liệu bằng PowerShell và hoàn tất; chưa sửa môi trường hoặc kết luận các dịch vụ đang chạy bị lỗi. Trước đợt runner/tests cần kiểm tra interpreter/venv hiện hữu; nếu phải khôi phục dependencies/runtime, trình bày phạm vi riêng thay vì tự cài lại.

**Cập nhật sau đợt được xác nhận tiếp:** công cụ offline đã triển khai và kiểm chứng bằng fixtures/stubs, xem [report](final-eval-tooling.md). Đợt tiếp theo cần đề xuất tích hợp runtime/capture và kiểm tra môi trường backend; phạm vi code/tests/dịch vụ/artifacts cần xác nhận riêng. Sau khi guard và capture được kiểm chứng mới chốt live batch cụ thể. Công cụ offline chưa đóng gate Bước 10 hoặc bắt đầu chấm held-out thật.

Đã tìm được Python3.12.6 sẵn có trong pgAdmin và dùng để chạy tests toolkit; chưa sửa venv thiếu interpreter gốc. Replay không thay production runner/capture adapter: nhãn `offline_replay` và pending human metrics luôn được giữ rõ trong artifacts. Hai runners cũ nói ở trên vẫn chỉ dev/smoke.

**Cập nhật sau đợt runtime:** adapter API và guard đã triển khai, 116 focused tests đạt bằng các mức stub/unit được ghi rõ trong [report](runtime-capture-step11-preparation.md). SQL adapter có code và unit test, chưa chạy với storage thật. Probes không sửa dữ liệu: Docker client/daemon27.3.1; Compose không liệt kê container đang chạy của project; DB test OperationalError, Qdrant ConnectError. Endpoint/model/key có cấu hình và hai manual flags true, chưa có provider requests hoặc kiểm chứng quota/billing. Đợt tiếp theo nên duyệt bật storage hiện hữu và SQL/Qdrant integration trên scope riêng với embeddings/provider giả, vẫn0model calls; sau đó mới chốt live batch. Không tự bật dịch vụ trong đợt kiểm tra hiện tại.

## 2. Điều kiện trước khi thực thi

- Chỉ dùng corpus synthetic/fixtures được phép, không đọc hoặc in secret từ `.env`. Xác minh cấu hình bằng trường cần thiết/giá trị đã che; không lưu resolved config chứa credentials.
- Người dùng xác nhận project free tier, không billing/paid fallback và quota còn đủ. Flags local chỉ là xác nhận thủ công, không phải cap của Google. Kiểm tra lại tài liệu provider/model availability trước live run; không tự đổi model.
- Mỗi đợt ghi số queries, `generateContent`, `countTokens`, retry/repair, warmup, oracle và mức tối đa tổng hợp. Chưa xác nhận đủ quota/caps thì chưa gọi provider. Hết quota dừng, không đổi key hoặc fallback để né giới hạn.
- API/worker cùng cwd/storage; tests/eval có DB test, workspace, collection và thư mục riêng. Không chạy chung queue với dev worker. Nếu cần dừng/khởi động dịch vụ, nêu rõ trong phạm vi đợt chạy.
- E2E dùng tài liệu/phiên test có IDs sở hữu rõ, không xóa 10 tài liệu dev hiện hữu. Fresh-volume thử setup ở Bước 12 dùng tài nguyên riêng. Cleanup chỉ dọn đúng tài nguyên của run, ghi kết quả/lỗi cleanup.
- Chốt công cụ browser thực sự khả dụng và cách thu evidence. Không coi HTTP hoặc jsdom là browser E2E; nếu thiếu công cụ, ghi blocked/skipped với lý do và giữ gate mở.

## 3. Checklist UI và phạm vi coverage

Một luồng browser P0 của Bước10 đã hoàn tất; bảng dưới giữ các biến thể để đối chiếu final acceptance, không gọi mọi biến thể là đã rerun. TXT upload, hai role,2claims/citation, abstention, delete/source/history, navigation/reload/expiry401 và keyboard có bằng chứng Chrome11/11. PDF/DOCX/multi-source/partial-conflict và endpoint RBAC dùng bằng chứng component/integration trước đó hoặc final run khi có; không gán6syntheticcases thành kiểm hết mọi dạng. Kịch bản UI dùng dev/fixture, không chọn câu demo từ held-out. Không sửa UI nếu chưa duyệt scope UI riêng.

| ID | Thao tác | Điều kiện quan sát | Evidence cần lưu |
|---|---|---|---|
| UI-01 | Admin upload PDF text, DOCX, TXT/MD | Queued/processing/ready thật; nội dung tiếng Việt và vị trí nguồn đúng | IDs, stage/status, ảnh và đối chiếu nguồn |
| UI-02 | Member mở tài liệu, hỏi và mở nguồn | Quyền đọc hợp lệ; write bị chặn ở API, không chỉ ẩn nút | Browser + HTTP 403 có nhãn kiểm tra quyền |
| UI-03 | Hỏi câu nhiều điều kiện/hai tài liệu | Answer thật; citations mở đúng đoạn/trang/block; người chấm xác minh support | Run/message IDs, output, final evidence và review |
| UI-04 | Hỏi câu thiếu bằng chứng, partial/conflict | Phân biệt trạng thái model với 503/504; không bịa để điền phần thiếu | Output và review; không coi schema pass là semantic pass |
| UI-05 | Admin xóa nguồn do run sở hữu | Query mới không lấy nguồn; source cũ bị chặn; lịch sử/replay xử lý theo contract | Trước/sau delete, request IDs, cleanup state |
| UI-06 | Đổi session/tab, reload, hết phiên đăng nhập | Không trộn câu trả lời/polling cũ; auth/recovery đúng; không gửi lại model ngoài dự toán | Video/ảnh + request ledger |
| UI-07 | Dùng bàn phím desktop/mobile layout | Focus, mở/đóng dialog, chọn citation/menu, không bị kẹt hoặc che control | Checklist thao tác và lỗi cụ thể |

Sau UI-05, hỏi lại phải chọn filter hợp lệ; request còn giữ document ID đã xóa có thể trả lỗi nguồn theo contract, không ép mọi tình huống thành abstention. Không tuyên bố thu hồi được bytes đã gửi về trình duyệt trước khi xóa. Member không có quyền xóa, nên phần xóa thực hiện bằng admin và kiểm tra đọc lại ở cả hai role.

Lỗi ngoài scope được đề xuất sửa riêng. Mục5–6 Bước10 đã đóng theo [evidence Chrome](browser-e2e-retry-20261110.md); full AT-R01–23/final model quality vẫn cần đối chiếu ở Bước11. Phản hồi “UI ổn” không thay bằng chứng chức năng.

## 4. Chuẩn bị evaluator và freeze

Candidate11/11 đã có runner/snapshot và [phiếu hai người](human-review-guide.md); prepare/verify không đọc nội dung questions JSONL. Chưa grant/capture/model run. Những phần hỗ trợ trước đây không thay thế kiểm tra native orchestration mới trên scope SQL/Qdrant riêng, và không tự cho quyền chạy60/210requests.

1. Thiết kế runner hỗ trợ split rõ ràng, kiểm tra dataset/config/index hashes, giữ denominator đầy đủ và dùng scope test riêng. Bổ sung scoring worksheet và bộ tổng hợp có tests bằng fixtures trước khi đụng held-out. Không đưa gold/oracle context vào API production.
2. Dùng dev/fixture để thử toàn bộ đường chạy, ledger, caps, mapping, lỗi provider, cleanup và kết quả thiếu human review. Chuẩn bị này không tự cần gọi model; dùng stubs có nhãn trước.
3. Chốt source/config/prompt/model/chunker/index, phiên bản dependency, corpus/mapping hashes, phần cứng, concurrency và thứ tự questions. Ghi HEAD **và** trạng thái dirty/hashes nội dung source thật; repository hiện có thay đổi chưa commit, HEAD một mình không mô tả bản đang chạy. Không tự commit. Các copies cấu hình không chứa secrets.
4. Chốt tập test từ reviewed-v1 (30 câu theo metadata đã công bố) và seed/thứ tự trước khi chạy. Trong đợt chuẩn bị này không cần đọc nội dung câu hỏi test. Sau freeze, loader mới đọc test để chạy/chấm; không bỏ câu khó hoặc sửa labels âm thầm.
5. Chạy một lần chất lượng end-to-end cho mỗi câu ở baseline dense. Retrieval-only có report riêng và không LLM. Oracle-context là chẩn đoán tách riêng, không cộng điểm vào end-to-end; nếu chạy cần budget riêng.
6. Chấm output bằng rubric mục 5. Nếu thay đổi sau khi xem test, ghi test đã ảnh hưởng tuning; cần holdout mới trước tuyên bố cải thiện tổng quát. Giữ mọi failed runs và scoped retests.

Baseline no-context trong spec 14.10 và các phép so hybrid/reranker không nằm trong budget baseline dense dưới đây; cần đợt riêng. Không tuyên bố RAG vượt no-context nếu chưa so. Đo latency so sánh nhiều lượt theo spec cũng cần dự toán riêng, không tự nhân số calls.

## 5. Rubric và mẫu số

Áp dụng spec 14.9, không đặt ngưỡng accuracy sau khi nhìn kết quả:

| Metric | Cách tính/chấm |
|---|---|
| Hit/Recall/MRR@1/3/5/10 | Dùng gold evidence groups và [span matcher](../eval/span_metrics.py); OR alternatives, AND required spans, coverage 80%, không đếm overlap hai lần |
| All-evidence@K | Đủ mọi evidence groups của câu nhiều điều kiện; báo số câu thực tế |
| Correctness | 0 sai/bịa, 1 đúng một phần/thiếu điều kiện, 2 đúng đủ; so gold/source |
| Faithfulness | Supported factual claims / tổng factual claims, so với context thực gửi model |
| Citation correctness/completeness | Tách đúng từng liên kết claim–evidence và tỷ lệ claims có dẫn chứng hỗ trợ |
| Abstention | Precision/recall và false abstention rate; partial không phải từ chối hoàn toàn |
| Technical errors | Số queries failed / tổng attempted; planned/attempted/succeeded/not-attempted đều phải hiện |
| Latency/resources | Tách retrieval/generation/total, warm/cold, throttle/provider, concurrency=1 và số mẫu |

Báo conditional metrics trên successful runs và strict end-to-end trên tổng câu được lên kế hoạch; định nghĩa strict success trước chạy là output thành công có correctness=2, đồng thời giữ metrics thành phần riêng. Unanswerable không có gold groups thì retrieval metric `null`, không cho điểm 1. Denominator 0 → `null` + count. Timeout/index/provider error không phải abstention đúng. Chạy chưa đủ 30 câu không gọi là final completed; báo coverage và phần chưa chạy.

Một thành viên chấm, thành viên còn lại kiểm tra độc lập toàn bộ tập nhỏ; ghi disagreement và quyết định thống nhất. Worksheet dự kiến gồm question/run ID, reviewer IDs, correctness, từng claim/support/citation, expected/predicted answerability, lỗi và lý do. Pending không được đổi thành approved tự động. Đây là **review output mới**, khác ledger duyệt dataset.

Một lượt mỗi câu cung cấp mô tả latency của run nhỏ, không phải SLA. Với 30 successful samples, nearest-rank p95 là mẫu thứ 29 sau sắp xếp; lỗi có duration/status riêng, không trộn thành latency thành công. Khi cần so latency, spec khuyến nghị tối thiểu ba lượt/query; ghi số lần và biến thiên, không tính câu lặp là câu độc lập. Không suy ra throughput chịu tải từ nghịch đảo latency một request.

## 6. Dự toán requests — chưa được duyệt chạy

Theo [answering service hiện tại](../backend/app/services/answering.py): context builder có một count nền, một count cho mỗi retrieved hit thử đưa vào context và một count payload thường nếu còn evidence. Với `h` hits, upper bound là **h + 2 countTokens**. Generation tối đa **2 calls/query**, gồm một repair; không tự retry quota/network. No-ready/no-hits có thể không gọi provider, nhưng dự toán không giả định unknown sẽ không có hits.

| Phạm vi giả định | Queries | Generation cap dự toán | Count cap dự toán | Ghi chú |
|---|---:|---:|---:|---|
| Một batch nhỏ, top_k=5 | 2 | 4 | 14 | Có thể làm đơn vị duyệt/run; không phải lệnh hiện đã hỗ trợ held-out |
| E2E gồm 4 truy vấn mới, top_k=5 | 4 | 8 | 28 | Chỉ ví dụ tính; phải chốt checklist thực tế, chia batches và tính query phát sinh |
| Baseline dense held-out, top_k=5 | 30 | 60 | 210 | Một lượt chất lượng; chưa gồm warmup, oracle, no-context hoặc rerun |
| Retrieval-only | 30 | 0 | 0 | Vẫn cần embedding local và tài nguyên test; chưa cho phép chạy trong đợt tài liệu |

Các số trên là **trần dự toán từ code**, không phải usage đo được, quota provider hay quyền gọi API. Top-k/hits/code đổi phải tính lại. Phải giới hạn requests cho cả browser flow; thao tác reload, ID mới hoặc retry tay không được vượt cap. API dev hiện không có ledger tổng theo đợt như eval, nên cần chuẩn bị cơ chế đo/chặn trước live E2E, không dùng riêng bộ đếm tay làm hard cap.

Runner smoke hiện giới hạn tối đa 10 generation/20 count mỗi run và chỉ có synthetic cases. Không thể đưa batch held-out hoặc 28 count vào runner này bằng một lệnh sẵn có; cần chuẩn bị tooling riêng/extension được duyệt, giữ regression caps cũ. Với budget giả định 30 câu/top5, có thể chia 15 batches × 2 câu, mỗi batch 4/14; phải có ledger tổng 60/210 và metadata chung, không reset tổng cap bằng run ID mới. Chia batch không tránh rate/quota limits và không cho phép tune giữa các batch.

Ledger phải reserve trước request, fail closed khi hết cap, đếm cả repair và request mất response. Khi provider không trả usage, ghi `null`; ghi ngân sách 0 USD tách khỏi chi phí được xác minh. Nếu chưa xác minh billing/quota thì dừng trước calls. Không ghi rằng chi phí thực bằng 0 chỉ vì không nhận hóa đơn. Trong đợt này không truy cập tài khoản, không đọc key, không gọi token counter hoặc model.

## 7. Artifacts và tiêu chí kết thúc

Các tên dưới là **đầu ra cần tạo ở đợt thực thi thật**; offline fixture artifacts hiện chỉ nằm dưới `.cache`, không phải final benchmark:

- Mỗi run mới: `manifest.json`, `config.json`, `per_question.jsonl`, `metrics.json`, `report.md`; bổ sung source hashes, execution/request ledger và worksheet human review. Không ghi đè reviewed snapshots, parser mapping hoặc reports lịch sử.
- Raw outputs/final context chỉ từ corpus synthetic được phép, tách khỏi trace production tối giản IDs/hash/spans. Không lưu key/token/credentials hoặc chain-of-thought. Chỉ render bản đã che dữ liệu cần thiết vào screenshot/report công khai.
- Bảng AT-R01–23: từng case có pass/fail/skipped/pending, timestamp, môi trường, command/tool, evidence và giới hạn; phân biệt old evidence với rerun mới. Software fakes không thành real-model semantic acceptance.
- Failure analysis: ít nhất ba lỗi nếu có đủ, hoặc toàn bộ nếu ít hơn; tách parser/chunker/retrieval/context packing/generation/citation/UI/provider. Không tạo lỗi giả để đủ số.
- Báo cleanup scoped, lỗi cleanup và tài nguyên còn lại. Không dọn dev volume/storage để giả clean setup.

Chỉ sau khi đóng gate Bước 10 và đạt report Bước 11 mới thực hiện Bước 12 theo xác nhận riêng: fresh setup, README/video, đóng góp cá nhân và release checklist. Đề xuất phần đầu README: bài toán → demo → kết quả đo/giới hạn → kiến trúc → setup; không công bố số metrics đang `null`.

**Tiến độ hiện tại:91,8% /100%.** Human review29/29 đã merge/rescore, Bước11mục2–5 có bằng chứng; fullAT/release freeze/freshsetup và Bước12 vẫn mở. Không dùng điểm review để tự đóng mọi acceptance.
