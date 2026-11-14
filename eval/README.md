# RAG Evaluation

**Mới nhất12/11 — human adversarial hoàn tất:** [report](../docs/human-review-adversarial-20261112.md), [combined review](reports/final-20261112/adversarial/combined-review.json), [reviewed metrics](reports/final-20261112/adversarial/reviewed-metrics.json). Hai phiếu2/2khớp, correctness2/2điểm, support1/1claim/citation1/1link; [ma trận mới](reports/final-20261112/acceptance/acceptance-matrix.json) ghiAT-R14đạt/23scopedpasses với giới hạn contract/native/browser kế thừa được nêu rõ. Không modelcalls/DBwrites hoặc ghi đè rawpending snapshots/oldmatrix/phiếuđãchấm; không gộp devvàoheldout30. PLANv1.29ghi5/7Bước11/**92,9%/100%**, chưa release/freshsetup/M1Done. Các snapshot0/2/partial bên dưới là lịch sử, không chạy lại one-shot hoặc merge vào outputs đã có.

**Mới nhất12/11 — adversarial/dev AT-R14:** [report](../docs/adversarial-at14-20261112.md), [runner](adversarial_eval.py), [bootstrap](../scripts/run-adversarial-eval.py). Hai native outputs đã có,2generation+6count/8HTTP200 trong grant riêng4/14/0USD,85frozenfiles+2extras,cleanup/oldheldout hashes verify;71unit/regression+3SQL riêng đạt. [Hai phiếu mới](../docs/human-review-guide.md) cònhuman0/2,AT-R14partial,**91,8%/100%**. Không chạy lại `capture` hoặc `review` để reset/ghi đè artifacts; `verify` chỉ kiểm hashes, không modelcall. Bộ29heldout đã chấm/gộp,ledger30/210giữ nguyên; các trạng thái7outputs/pending/chưa grant phía dưới là lịch sử. Không thêm synthetic cases vào heldoutaccuracy hoặc dùng heuristiccanaryabsence làm humanpass.

**Mới nhất11/11 — native held-out attempt:** [pacing và report](../docs/final-heldout-20261111.md), candidate mặc định `.cache/final-reviewed-baseline-20261111-paced/` (100files+4extras) đã thực thi một lần.7outputs thành công, q023generationHTTP503,22câu chưa chạy; manifest incomplete, planned30.8generation/56count trong cap60/210, không retry/reset; cleanup/audit verified. [Phiếu mới cho7outputs](../docs/human-review-guide.md) chờ hai người chấm.155regression +8pacing cuối (7overlap) +5SQLtests riêng đạt. Các trạng thái pending/no model calls của các đợt cũ dưới đây là lịch sử. Chưa final accuracy/full acceptance; **87,3%/100%**.

**Trạng thái11/11/2026:** Chrome E2E/QA đã hoàn tất; [hai người chấm6/6outputs tổng hợp](../docs/human-review-practice-20261111.md) đã merge/rescore, không phải held-out benchmark. [Final runner SQL integration](../docs/final-runner-sql-20261111.md) đạt5tests +148regression; inference giả/origin offline_fixture, cleanup verified. Candidate mặc định `.cache/final-reviewed-baseline-20261111-sql-verified/` thay bản cũ;99files+4extras verify, approval pending60/210,0model calls. Final30 và Bước11–12 còn mở; **87,3% /100%**. Các ghi nhận10/11 dưới đây là lịch sử.

**Browser E2E 10/11:** [harness](browser_e2e.py), [bootstrap](../scripts/run-browser-e2e.py), [report](../docs/browser-e2e-20261110.md). Scope disposable cùng-origin UI/API, sáu câu có budget chung8/28 (sau delete0/0);131guard/regressiontests và UI build đạt. Computer Use bị chặn bởi guard URL trên Windows, chưa chạy browser/model, ledger0/0; không tính là E2E pass. Scope đã shutdown/cleanup và giữ ledger/artifacts, không chạy lại bằng cách xóa scope directory. Cần phiên browser access hợp lệ và phạm vi thực thi tiếp, không tự đổi sang API-only benchmark.

**Native smoke 10/11:** [runner](run_capture_smoke.py) và [report](../docs/native-capture-smoke-20261110.md) đã chạy hai câu tổng hợp với E5/Gemini thật: grounded/citation và model abstention. Dùng 2generateContent+6countTokens trong cap4/14; scope cố định không nhận run ID mới để reset ledger. Input `synthetic_smoke` có nhãn riêng và không được dùng làm reviewed/held-out; worksheet outputs vẫn pending. [Bootstrap](../scripts/run-capture-smoke.py) mặc định chỉ preflight; `--live` là mutation/inference cần xác nhận và scope hiện tại đã dùng, không tự chạy lại. Không sửa `.env`, tải model hoặc fallback trả phí. Final reviewed benchmark/browser E2E vẫn chưa hoàn thành; tiến độ83,4%/100%.

**Cập nhật mới nhất 10/11 — storage/capture:** [SQL/Qdrant integration](../docs/sql-capture-integration-20261110.md) đã đạt 6 tests +116 regression tests; auth/ingestion/retrieval/publish/canonical mapping thật trên DB capture riêng, embeddings/counter/provider giả. Capture vẫn offline_fixture và human review pending, không phải benchmark model. [Runner môi trường](../scripts/run-capture-integration.py), [suite](tests/test_runtime_capture_sql.py) và [probe chỉ đọc](../scripts/check-capture-storage.py). Runner tạo DB/artifacts nên chỉ chạy theo đợt xác nhận, dùng basetemp mới; không tự bật storage/download. Chưa chạy live smoke/held-out hoặc hoàn tất Bước 10–11, tiến độ 83,4% /100%.

Nguồn yêu cầu: [Spec RAG mục 14–15](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN bước 02, 07, 11](../PLAN.md). Mục tiêu là đo retrieval/answering có thể tái lập, gồm cả thiếu bằng chứng và lỗi kỹ thuật. Các kế hoạch đánh giá STT/action items cũ không còn là tiêu chí của project RAG.

**Runtime capture 10/11/2026:** [adapter và report](../docs/runtime-capture-step11-preparation.md) đã gắn guard/capture vào app test qua hook nội bộ mặc định tắt. 116 tests tập trung đạt gồm 22 runtime tests có stubs, 57 offline regressions và 37 answering/provider unit tests. SQL/Qdrant integration chưa chạy: probe DB test/Qdrant thất bại kết nối, cần bật storage trong đợt riêng. Không có model calls, embedding, browser hoặc held-out thật; không coi `origin=offline_fixture` là model benchmark. Tiến độ **83,4% /100%**.

**Chuẩn bị offline 10/11/2026:** đã có [toolkit freeze/replay/human score và persistent request ledger](../docs/final-eval-tooling.md), entry point `python -B -m eval.final_eval`. Tests chỉ dùng fixture tự tạo, chặn network và corpus thật; không phải real-model/held-out benchmark. Hai runners dev/smoke lịch sử giữ nguyên. CLI mới chưa capture production API/browser hoặc bật provider thật; xem [protocol và phần còn thiếu](../docs/final-validation-plan.md). Tiến độ giữ **83,4% /100%**. Hướng dẫn Python thay thế cho venv hiện thiếu interpreter nằm trong report toolkit.

**Cập nhật Bước 09 — tiến độ75,6% /100%:** 302 backend +91 eval tests đạt; deletion/privacy/cleanup/fault-race được kiểm tra bằng PostgreSQL/Qdrant thật, provider/embeddings fakes. Không model calls hoặc thay đổi quality metrics/holdout. [Report](../docs/deletion-privacy-step09.md). Các reports dưới đây giữ nguyên lịch sử; human review vẫn pending.

**Lịch sử04/11/2026 — Bước08, tiến độ65,9% /100%:** [answering report](../docs/answering-step08.md) có3 oracle +2 API synthetic dev cases qua2runs. Run đầu4outputs validate/probes đạt,1eval_budget_exhausted trước generation; retest riêngunknown đạt. Tổng5generate+25countTokens đúng các xác nhận riêng,0USD/free tier, không sửa backend/prompt/model để retest. **276 backend +91 eval tests đạt** ở hai suites riêng; human review pending, không phải answer accuracy/held-out result. Giữ các reports lịch sử bên dưới. Runner đếm budget từ số chunks sau ingestion, hỗ trợ --case/per-run caps; full5ca cần21count calls nên cap20 mặc định từ chối preflight. Không tự tăng trần hoặc chạy lại model để kiểm tra artifacts.

**Trạng thái 03/11/2026:** reviewed-v1/gold mapping giữ nguyên 10 docs/45 approved questions/47 references. [Bước 07](../docs/search-retrieval-step07.md) có [dev retrieval run thật](reports/retrieval_dev_20261103T101104Z_968416c5/manifest.json): 15 queries (13 answerable/2 unknown), Recall@5=1/MRR@5≈0,923/0 errors; không answering accuracy hoặc held-out result. **86 eval tests pass**, backend suite riêng **222 pass**. Không LLM calls/tải model mới/test queries; ingestion/model reports lịch sử giữ nguyên. Tiến độ **56,1% / 100%**, Bước 08 chưa bắt đầu.

## Công cụ đã triển khai ở Bước 02

Lưu ý hiện tại: `test_runtime_capture_sql.py` và `test_final_runner_sql.py` chạy PostgreSQL/Qdrant thật với inference giả; chạy toàn thư mục cần storage và phạm vi ghi DB/artifacts được xác nhận. Để kiểm toolkit offline, chọn các test modules cụ thể. Native smoke chỉ chạy qua runner/`--live` riêng, không tự gọi Gemini từ pytest.

Từ repo root, dùng venv Python: `python -B -m eval.validate_dataset --dataset eval/snapshots/reviewed-v1 --require-reviewed` kiểm tra snapshot đã khóa. `python -B -m pytest eval/tests -q -p no:cacheprovider` kiểm thử trên bản sao tạm. **Các test `*_sql.py` import `tests.database_safety` từ `backend/tests/`, nên cần `backend` trong `PYTHONPATH`** (PowerShell: `$env:PYTHONPATH='backend'`), cùng `TEST_DATABASE_URL` hợp lệ và PostgreSQL/Qdrant đang chạy. Thiếu `PYTHONPATH`, pytest dừng ngay ở bước collect (`ModuleNotFoundError: No module named 'tests'`); lỗi này được phát hiện khi chạy trên bản cài sạch ngày 12/11/2026. Trên PowerShell máy này thay `python` bằng `.\backend\.venv\Scripts\python.exe`. Validator mặc định vẫn trỏ draft làm việc tại datasets; dùng đường dẫn reviewed tường minh cho smoke/eval.

`python -B -m eval.publish_reviewed` publish snapshot từ ledger đã duyệt, không tự approve hoặc sửa draft. `python -B -m eval.model_smoke embedding` dùng model cache local và tạo report mới; lần đầu `--download`. `python -B -m eval.model_smoke llm` có preflight key/free tier/quota trước network. Các lệnh tạo artifacts/inference cần nằm trong đợt đã được xác nhận. Cấu hình pin và reports ở `configs/model_smoke.json`, `reports/smoke_*`; không coi compatibility run là retrieval/answer benchmark.

`--case-id adhoc_conflict_not_human_gold` chọn đúng một case, cần phạm vi số requests đã được duyệt; không dùng để âm thầm retry vượt số calls. Diagnostics mới giữ safe error types/usage/model metadata khi output lỗi, không lưu input trong lỗi Pydantic. Các reports có source snapshots ở run mới; hashes/source của run cũ giữ nguyên theo phiên bản đã chạy. Không gọi lại API chỉ để làm mọi run thành passed.

`eval/build_dataset.py` tạo/đối chiếu artifacts từ seeds và không ghi đè files đã sửa; chỉ chạy trong đợt được xác nhận. `eval/metrics.py` giữ hàm math trên groups đã match; Bước 07 thêm retrieval_gold.py/span_metrics.py để load active UUIDs, union80%/alternatives/required spans và macro/strict denominators. run_retrieval_eval.py gọi production APIs/model local và ghi dev report; chưa có answering/oracle/E2E runner. Abstention math chưa được dùng để suy chất lượng LLM trong dev retrieval run.

## Dev retrieval evaluator Bước 07

`python -B -m eval.run_retrieval_eval` từ root: guard DB *_test, ingest10docs/14chunks, production search/source qua member bearer, chỉ query 15 dev cases. [Frozen baseline](configs/dense.json) candidate20/top5/eval top10/cutoff None, index9851b494…c4a4; runtime lệch config phải version/reindex trước chạy. [Loader](retrieval_gold.py) fail closed trên hash/text/location/spans drift; [matcher](span_metrics.py) union80%, alternatives/required spans, macro/strict/error denominators. [Report](../docs/search-retrieval-step07.md) ghi scores/latency/failure analysis, BGE hoãn và giới hạn; các artifacts/source snapshots giữ immutable. Dọn đúng collection/workspace/token/file; không chạy cùng tests/worker chung DB queue. Lệnh inference/artifacts cần đợt xác nhận, không LLM calls.

## Parser mapping Bước 05

**Ingestion smoke Bước 06:** `python -B -m eval.ingestion_smoke` dùng guard DB *_test, Qdrant collection/workspaces riêng, admin upload/get status và worker E5 thật; tạo run mới có manifest/per-document/source snapshots, cleanup đúng scope. Chạy độc lập, không cùng backend reliability suite/dev worker dùng chung queue. Không gọi LLM. Core inference chuyển sang backend/app/services/e5_runtime.py; eval shim và source snapshots giữ compatibility/history. Xem [report Bước 06](../docs/worker-index-step06.md) cho timing cold/warm/RSS và giới hạn.

`python -B -m eval.parser_mapping --output eval/mappings/<new-version>.json` gọi production parser/chunker, validate reviewed snapshot/hashes và tạo artifact mới, không ghi đè output đã có. Dùng tokenizer E5 local cache, không inference. `test_frozen_mapping_reproduces_all_reviewed_questions` tái tạo và đối chiếu toàn JSON; missing/ambiguous quote/location hoặc mất gold coverage đều fail. Đây là canonical span mapping, chưa phải matcher top-k/80% hoặc benchmark retrieval. Manifest reviewed-v1 giữ pending_step05 lịch sử; mapping mới nối bằng parent hash. Lệnh tạo file cần đợt được xác nhận.

## Cấu trúc dự kiến

```text
eval/
├── datasets/
│   ├── corpus/                  # Tài liệu giả lập/được phép, định dạng được hỗ trợ
│   ├── corpus_manifest.json     # Document refs, revisions, checksums, parser version
│   └── questions.jsonl          # Question, split, answerability, gold groups/spans
├── configs/
│   └── dense.yaml              # Model/chunker/retrieval/prompt config đã resolved khi chạy
├── run_retrieval_eval.py        # Cần triển khai, gọi cùng services với app
├── run_answer_eval.py           # Cần triển khai, có oracle-context và E2E modes
└── reports/
    └── <run_id>/
        ├── manifest.json
        ├── config.json
        ├── per_question.jsonl
        ├── metrics.json
        └── report.md
```

Tree là contract đích cho retrieval/answer eval; hiện đã có dataset/reviewed snapshot, smoke/ingestion/dev retrieval configs/runners/reports và canonical mapping. Answer/oracle/E2E runners và held-out reports chưa triển khai. Không tạo report rỗng rồi trình bày như đã eval; mỗi run ID riêng, không ghi đè kết quả cũ.

## Dataset và gold evidence

- Mục tiêu M1: 8–12 tài liệu giả lập và 30–60 câu; reviewed-v1 có 10 tài liệu/45 câu, đủ direct fact, paraphrase, exact identifiers, multi-evidence/conflict và 6 unanswerable; human review hoàn tất, parser spans đã map trong artifact Bước 05 riêng.
- Hai người gán nhãn/kiểm tra chéo. Ghi question ID/type, expected answer/rubric, expected abstain, evidence groups, document ref/revision, quote/location và canonical block/char spans.
- Gold bám nguồn gốc, không bám chunk UUID có thể đổi theo cấu hình. Offset dùng cùng normalized source blocks/parser version; gold mapping sai phải được báo, không âm thầm bỏ câu khỏi mẫu.
- Cố định dev/test theo nhóm câu cùng sự kiện; paraphrase của cùng câu không chia hai split. Dev dùng chọn model/chunk/threshold, test chạy sau freeze. Nếu tune trên test, ghi test đã bị sử dụng và tạo holdout mới trước tuyên bố tổng quát.
- Bộ adversarial/prompt-injection và fixture malformed/scan tách khỏi average accuracy thông thường; vẫn báo kết quả riêng.

### Schema câu hỏi v2 — 01-T1

Contract mở rộng nằm trong [roadmap 01](../docs/roadmap/01-eval-expansion.md); thực thi ở
[`validate_question_metadata` / `validate_questions`](validate_dataset.py). Đây là schema của
từng dòng `questions.jsonl`, độc lập với tên phiên bản snapshot trong manifest.

| Trường | v1 | v2 |
|---|---|---|
| `dataset_version` | Có thể bỏ qua (hiểu là `"v1"`) hoặc ghi `"v1"` | Bắt buộc `"v2"` |
| `split` | `dev`, `test` | `dev2`, `test2` |
| `slice` | Không có | Bắt buộc một trong 9 slice dưới đây |
| `history` | Không có | Chỉ có ở `follow_up`, bắt buộc là danh sách không rỗng |

Chín slice: `text`, `table`, `identifier`, `multi_doc`, `conflict`, `unanswerable`,
`no_diacritics`, `scan`, `follow_up`. `slice` là lát cắt đánh giá chính, không thay thế
`question_type` hay gold evidence hiện có.

Mỗi phần tử `history` có đúng hai trường: `role` là `"user"` hoặc `"assistant"`,
`content` là chuỗi không rỗng sau khi bỏ khoảng trắng ở hai đầu. Lượt cuối phải là
`assistant`: câu hỏi hiện tại vẫn nằm ở `question`, sau phần lịch sử đã kết thúc một câu trả lời.
Slice khác có khóa `history` đều là lỗi, kể cả `null` hoặc `[]`. Validator không ép chuyển
kiểu, không tự sửa nội dung và không thêm luật buộc các vai trò phải luân phiên.

Ví dụ phần metadata của câu hỏi nối tiếp (các trường Q/A và gold vẫn phải điền đầy đủ):

```json
{
  "dataset_version": "v2",
  "split": "dev2",
  "slice": "follow_up",
  "history": [
    {"role": "user", "content": "Quy định này áp dụng thế nào?"},
    {"role": "assistant", "content": "Quy định áp dụng theo điều kiện trong tài liệu."}
  ]
}
```

`validate_questions` kiểm tra từng câu, chống trùng ID, rò rỉ family/source block giữa
các split và kiểm tra span/quote như v1. `validate` kiểm tra thêm toàn gói: v1 giữ giới hạn
30–60 câu, 8–12 tài liệu; khi có v2, cần 60–80 câu v2 và 14–24 tài liệu (14 tài liệu mới,
có thể kèm 10 tài liệu v1). Mỗi slice v2 cần ít nhất 8 câu, riêng `scan` và `follow_up` là 6;
vì vậy tổng tối thiểu thực tế là **68 câu v2**. Số câu v1 được kiểm tra riêng nếu có trong gói.
Mỗi split của từng phiên bản phải có câu không trả lời được. Kết quả kiểm tra gói v2 có thêm
`dataset_versions` và `slices`; output kiểm tra v1 giữ nguyên cấu trúc cũ.

Đây là kiểm tra cấu trúc và nguồn, chưa phải duyệt chất lượng nhãn. Việc đóng gói chung
không cho phép ingest v1/v2 vào cùng workspace; runner vẫn phải tách theo roadmap.
01-T1 dùng bản sao dữ liệu trong thư mục test tạm để kiểm tra schema, chưa tạo corpus/câu hỏi
v2 thật, chưa publish snapshot hay chạy benchmark. T4 sẽ mở rộng publisher cho v2;
không dùng publisher v1 hiện tại để phát hành v2.

## Chỉ số bắt buộc M1

| Nhóm | Cách đo |
|---|---|
| Retrieval | Hit@5, macro Recall@5 theo evidence groups, MRR@5; thêm K=1/3/10 khi phù hợp và All-evidence cho multi-condition |
| Answer | Human correctness 0/1/2, claim faithfulness, citation correctness và completeness theo rubric spec 14.9 |
| Abstention | Precision/recall cho câu unanswerable, false abstention trên câu có đáp án; partial chấm riêng |
| Vận hành | p50/p95 từng stage, total latency, số technical errors/calls/tokens, peak RAM/VRAM khi đo được |
| Chi phí | Usage thật và đơn giá có ngày/nguồn nếu quy đổi; chưa có usage thì null, không ghi 0 |

Evidence matching theo spec 14.9: freeze quy tắc coverage span/group trước đo, dedup group để overlap chunks không tăng recall giả. Không gọi Hit@K là Recall@K. Denominator bằng 0 trả null kèm sample count. Timeout/provider/index errors không phải abstention đúng; báo error rate toàn bộ, conditional quality trên successful runs và strict E2E success với denominator rõ ràng.

## Protocol và artifact

1. Freeze dataset/corpus hashes, code commit, parser/chunker/tokenizer, embedding fingerprint/index manifest, retrieval depth/K/filters, LLM/provider, prompt/schema/budgets/decoding, phần cứng và timestamp.
2. Retrieval-only không gọi LLM. Oracle-context chỉ dùng trong eval để chẩn đoán generation với gold evidence; E2E dùng retrieval thật. Không báo oracle score như app score.
3. Dense là baseline. So model hoặc hybrid/reranker trên cùng snapshot; thay nhiều biến phải ghi đó là so cả pipeline. Không mặc định treatment thắng.
4. Per-question lưu retrieved IDs/ranks/scores, final-context IDs, cited IDs, outputs/judgments, timings/errors; không chỉ lưu số trung bình. Raw text chỉ khi corpus cho phép, không lưu secret hoặc chain-of-thought nội bộ.
5. Warmup tách khỏi latency samples; báo cold/warm, concurrency, lượt chạy. Nhiều lượt cùng câu không thành nhiều câu độc lập về thống kê.
6. Human review là baseline; judge tự động là P1, cần prompt/model của judge và kiểm tra chéo. Báo ít nhất 3 lỗi thật nếu có đủ, hoặc đúng số quan sát nếu ít hơn.
7. Mỗi số trong README/CV phải truy được run/report; unit-test stub pass không chứng minh model quality. Giữ kết quả âm, limitations và biến không kiểm soát được của hosted model.

## Runner cuối và review offline

**Acceptance12/11:** [report/scopes](../docs/final-acceptance-20261112.md) và matrix (`.cache/at-20261112/acceptance-matrix.json`, chỉ lưu ở máy local) ghi22scoped passes/AT-R14partial,409test cases khác nhau qua các process (302backend+2additional contracts+69eval+36frontend). Logs fail/retest, harness snapshots và cleanup trong `.cache/at-20261112/`; source/capture/review/ledger cũ không đổi,0Gemini mới. AT-R22rebuild kế thừa native evidence không là fresh installation; AT-R14native adversarial/human cần scope và grant mới riêng. Không chạy lại các one-shot artifacts để reset allowance; count held-out210/210đã hết.

**Sau human review12/11:** [kết quả held-out đã chấm](../docs/human-review-heldout-20261112.md), [combined review](reports/final-20261112/heldout/combined-review.json), [reviewed metrics](reports/final-20261112/heldout/reviewed-metrics.json) và [receipt](reports/final-20261112/heldout/rescore-receipt.json).29/29outputs được hai reviewer chấm đầy đủ/khớp, strict success29/30≈96,67%giữ lỗi providerq023. Raw report/binding vẫn pending theo lịch sử, không ghi đè; model/DBcalls mới0. Không chạy lại merge/rescore lên output đã có hoặc sửa phiếu đã dùng. [Acceptance gaps](../docs/final-acceptance-gaps-20261112.md) là bước tiếp; không fullAT/M1pass. Các đoạn chờ chấm/pending dưới đây là snapshot trước merge.

**Cập nhật12/11:** [continuation](../docs/final-continuation-20261112.md) đã chạy22/22câu chưa từng thử bằng `eval/final_continuation.py` / `scripts/run-final-continuation.py`. Production protocol giữ nguyên; controller có manifest riêng, child reserve parent trước, không rebind/reset. Composite hai phiên30attempted/29outputs/1q023failed/0notattempted, tổng30generation/210count (count allowance hết). [Worksheet29outputs và phiếu A/B mới](../docs/human-review-guide.md) chờ nhóm chấm; không dùng packet7outputs hoặc practice6câu. Không chạy lại prepare/capture/combine trên output đã có; lệnh `scripts/run-final-continuation.py verify` chỉ kiểm hashes, không model calls. Manifestcompleted_with_errors không là human-quality/full acceptance pass. Đoạn8/30 dưới đây giữ snapshot11/11; SQLite parent đã nối reservations mới, summary gốc8/56 giữ nguyên.

[Chuẩn bị11/11](../docs/final-eval-preparation-20261111.md) đã có `eval/final_runner.py`, public config và bootstrap. Candidate mặc định hiện là bản paced, đã [capture một lần](../docs/final-heldout-20261111.md):7success/1provider503/22notattempted, planned30. `prepare` và `capture` không chạy lại trên scope đã dùng để reset artifact/allowance. Cap60generation/210count đã được duyệt cho lượt này, thực dùng8/56; không tự chuyển phần dư sang runID khác. Model/prompt/corpus giữ nguyên; tiếp tục cần thiết kế và scope được xác nhận riêng.

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -B scripts/run-final-eval.py verify
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -B scripts/run-review-pack.py --help
```

[Phiếu sáu câu E2E](../docs/human-review-guide.md) ban đầu có điểm null, nay nhóm đã điền và [merge/rescore6/6](../docs/human-review-practice-20261111.md); file gốc/report lịch sử giữ nguyên. Final30câu sẽ có worksheet riêng sau capture, không dùng phiếu thực hành thay benchmark. Các runner retrieval-dev/answering-smoke cũ giữ contract cũ; không thêm `--split test` hoặc chuyển sang YAML khi chúng chưa hỗ trợ.

Software tests/integration kiểm tra contract và fault recovery tách khỏi benchmark model. M1 nghiệm thu AT-R01–23; P1 tương ứng AT-R24–26. Quy tắc workspace về câu xác nhận “Thực hiện đi” và cập nhật [KNOWLEDGE.md](../KNOWLEDGE.md) áp dụng cho việc tạo dataset, scripts và chạy evaluation.
