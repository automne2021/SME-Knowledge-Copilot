# Khoảng trống final acceptance — 12/11/2026

**Sau human adversarial và merge offline:** [report](human-review-adversarial-20261112.md)/[ma trận mới](../eval/reports/final-20261112/acceptance/acceptance-matrix.json) ghiAT-R14đạt theo scope,**23/23scopedpasses**, human2/2khớp/khôngadjudication. Không còn gap scenarioM1 theo evidence đã ghi; release/codefreeze và freshsetup/packagingBước12vẫn mở, không đổi nhãnM1Done. PLANv1.29ghi5/7Bước11/**92,9%/100%**. Snapshot partial/chưa native/chưa review bên dưới giữ lịch sử; không cần thêm modelcall hoặc chấm lại.

**Mới nhất, đợt adversarial riêng:** [report](adversarial-at14-20261112.md) ghi2/2native outputs,2generation+6count/8HTTP200, actual attack exposure2/2; [human review hai câu mới](human-review-guide.md) còn0/2. AT-R14vẫnpartial_pending_human_review,22scopedpasses cũ giữ snapshot; không cần native rerun hoặc chấm lại29heldout. Release/freshsetup/Bước12còn mở, **91,8%/100%**. Inventory/đề xuất chưa native bên dưới là lịch sử trước đợt mới.

**Cập nhật sau đợt được duyệt:** [kiểm chứng acceptance](final-acceptance-20261112.md) đã chạy/đối chiếu22/23scenarios,409tests khác nhau có kết quảpass qua các process; AT-R14cònpartial vì thiếu native adversarial và human review riêng. AT-R22rebuild DB/index rỗng có thể dùng native evidence sẵn có; fresh installation vẫn ởBước12. Machine matrix (`.cache/at-20261112/acceptance-matrix.json`, chỉ lưu ở máy local) chứa testcase/log/hash và lịch sử fail/retest. Inventory/chưa chạy bên dưới là snapshot trước đợt này, không là trạng thái mới nhất. Tiến độ giữ91,8%/100%, chưa fullacceptance/M1Done.

Đối chiếu [spec15.4–15.6](../SME_Knowledge_Copilot_RAG_Specification.md#154-acceptance-scenarios-và-traceability) và [human review29outputs](human-review-heldout-20261112.md). Đây là **inventory bằng chứng và việc cần xác minh**, không phải lượt chạy fullAT-R mới, không là23fails/skips. Đợt này không chạy test/model/browser/storage và không đánh dấu pass cho toàn scenario chỉ vì có tên test hoặc một report cũ.

Các reports lịch sử giữ môi trường/lệnh/số pass riêng. Trước khi đóng acceptance phải chọn bản chốt/source hashes, kiểm lại traceability và phân biệt bằng chứng kế thừa với rerun. Unit/fake inference chứng minh contract, SQL/Qdrant integration chứng minh storage/recovery, native capture và human review chứng minh chất lượng trong scope; không gộp thành một accuracy.

| ID | Bằng chứng hiện có, không rerun trong đợt này | Cần đối chiếu/kiểm thêm để đóng full scenario |
|---|---|---|
| AT-R01 PDF text nhiều trang | [Parser/upload05](parsing-upload-step05.md), [ingestion06](worker-index-step06.md), native10docs hai phiên | Khớp202→ready, trang/quote/chunk và source viewer cho PDF nhiều trang trên bản chốt |
| AT-R02 DOCX heading/bảng, TXT/MD | Parser05, worker06, native corpus PDF/DOCX/TXT/MD | Coverage heading/bảng/line đúng, không bịa số trang DOCX; nối artifacts đến từng biến thể |
| AT-R03 scan/blank/encrypted/mixed | Worker06 real fixtures terminal/warning; parser tests | Đối chiếu từng needs_ocr/failed/warning và không embed rỗng trong matrix cuối |
| AT-R04 MIME/size/traversal/ZIP | Parser/upload05; [upload tests](../backend/tests/test_uploads.py), [parser tests](../backend/tests/test_parsing_chunking.py) | Đủ mọi biến thể boundary/storage/resource và error codes; không chỉ UI validation |
| AT-R05 upload cùng hash đồng thời | PostgreSQL race `test_concurrent_duplicate_real_transactions`, report05 | Liên kết kết quả race/409, một job/document và absence orphan trên bản chốt |
| AT-R06 kill/restart worker | Worker06; [worker tests](../backend/tests/test_worker.py) có partial-upsert/lease recovery | Phân biệt fault injection với kill process thật, ghi rõ cách thực hiện và điểm publish/recovery |
| AT-R07 stale worker | Worker06 fencing test; deletion09 late-upsert | Đối chiếu barrier/lease và không overwrite active generation mới |
| AT-R08 upsert xong/publish rollback | Worker06 publish rollback/lost-ack tests; search07 generation filter | Chứng minh staging không được retrieve, recovery/cleanup và kết quả transaction |
| AT-R09 RBAC/cross-workspace/chat ownership | [Identity04](schema-identity-step04.md), search07/chat08/delete09 integration; Chrome hai role | Member POST/DELETE denial phải có API403/404; nút bị ẩn chưa đủ, kiểm cả foreign sources/sessions |
| AT-R10 search khi tắt LLM | [Search07](search-retrieval-step07.md), chat test `test_production_search_path_remains_available_with_llm_disabled` | Nối scope/locations và no-provider evidence, không gọi LLM để xác minh search-only |
| AT-R11 multi-condition/two-doc | [Native composite](final-continuation-20261112.md), human29/29, five multi-evidence | Output/citation support đã chấm trong tập; đối chiếu kịch bản hai tài liệu và mở nguồn trong UI, không chỉ ID hợp lệ |
| AT-R12 no-ready/no-hit/unanswerable | Human chấm4unanswerable; [Chrome E2E](browser-e2e-retry-20261110.md) sau delete0hits/0calls; chat/search fixtures | Phân biệt cả ba reason; lỗi kỹ thuật không được tính thành abstention |
| AT-R13 malformed JSON/E99/excluded source | [Answering08](answering-step08.md), [answering tests](../backend/tests/test_answering.py), chat repair tests | Inference giả hợp lệ cho contract repair; đủ một repair/còn sai502/no draft và context budget exclusion |
| AT-R14 injection/fake system/script | Native API injection smoke08 có context độc hại; parser literal data; [UI report](ui-step10-implementation.md) | Smoke lịch sử không là current-freeze adversarial suite; kiểm no-execution/XSS và human content riêng. Nếu thêm native tests cần allowance riêng, không reuse count budget đã hết |
| AT-R15 vector/embed/provider failure | Search technical failure tests, worker06, SQL continuation timeout; q023native503 | Đủ ba tầng và503/504/job state; không chỉ dựa một provider503 hoặc stub timeout |
| AT-R16 delete/cleanup failure | [Delete09](deletion-privacy-step09.md) retry/fail injection; Chrome source410 | Đối chiếu cleanup failure/exhaustion/manual retry và source bị ẩn trước cleanup |
| AT-R17 delete lúc ingest/query | Delete09 count/generate/repair/late-upsert barriers | Giữ evidence409/no-resurrection và fencing; browser delete tuần tự không chứng minh race |
| AT-R18 history sau delete | Delete09 scrub legacy/full context; Chrome cả hai role | Khớp answer redaction/trace/citation/snapshot cleanup ở mức SQL/API/UI |
| AT-R19 idempotency/busy/conflict | [Chat tests](../backend/tests/test_chat.py) có lost-ack/input-owner/session concurrency | Nối từng409/replay/final-answer uniqueness, không suy từ reload UI đơn lẻ |
| AT-R20 follow-up mơ hồ/budget | Answering08 non-history evidence, context/repair budget tests | Kiểm câu nối tiếp không lấy old answer làm evidence và budget enforcement; multi-turn rewrite làP1, không phải lý do bỏ P0 |
| AT-R21 metric arithmetic/spans | [Eval toolkit](final-eval-tooling.md), [eval tests](../eval/tests/test_final_eval.py), [span tests](../eval/tests/test_span_metrics.py), rescore arithmetic receipt | Kiểm single/multi/no evidence, overlap/dedup và denominator0→null; nối command/log được kế thừa hoặc rerun |
| AT-R22 clean rebuild/mapping | Hai phiên re-ingest10docs vào isolated DB/collection và verify mapping; frozen source archives | Chưa thay thế fresh checkout/dependencies/clean volumes riêng. Cần setup/migration/seed/ingest/rebuild từ manifest với mapping/config/failure report |
| AT-R23 UI source/auth/states | Chrome P0 source410/auth401/navigation/reload/keyboard; frontend tests/build/lint/visual reports | Đối chiếu empty/loading/error/AI label/cache permissions và các variants chưa thấy trên browser; không sửa UI trong đợt này |

## Thứ tự đợt tiếp theo, chưa được thực thi

1. **Chốt acceptance scope và evidence map:** kiểm link tới commands/logs/hashes cho từngAT; chọn tests cần chạy lại theo source drift, ghi inherited/rerun rõ. Ưu tiên kiểm chứng offline/unit và SQL/Qdrant với fakes trước; nếu native/browser bổ sung cần scope riêng. Không tự dùng lại held-out để tune.
2. **Đóng scenario còn thiếu:** chọn fixture/dev, fault injection/RBAC/literal rendering và browser variants theo gaps thực tế. Scope phải nêu dịch vụ, DB/queue/storage, artifacts và cleanup; không chung worker dev/tests. Không cấp lại allowance cũ: parent đã30generation/210count, count đã hết.
3. **Fresh setup và packaging Bước12:** Compose topology, dependency/model-cache profile, DB/index/storage riêng, setup→migrate→seed→ingest→query, cleanup có ownership. Không xóa dev volume để giả môi trường sạch. Sau đó README/video/đóng góp cá nhân/CV với đúng số đã đo và giới hạn.

Release/code commit chưa chốt; đợt này không commit/push, build Docker, cài dependencies, tải model hay thay `.env`. Human held-out đã hoàn tất không tự biến toàn23AT thành pass. [PLAN](../PLAN.md) ghi Bước11mục2–5 hoàn tất, mục1/6/7 còn mở; Bước12 chưa bắt đầu. **Tiến độ91,8%/100%**, chưa M1Done.
