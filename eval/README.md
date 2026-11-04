# RAG Evaluation

Nguồn yêu cầu: [Spec RAG mục 14–15](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN bước 02, 07, 11](../PLAN.md). Mục tiêu là đo retrieval/answering có thể tái lập, gồm cả thiếu bằng chứng và lỗi kỹ thuật. Các kế hoạch đánh giá STT/action items cũ không còn là tiêu chí của project RAG.

**Cập nhật Bước 09 — tiến độ75,6% /100%:** 302 backend +91 eval tests đạt; deletion/privacy/cleanup/fault-race được kiểm tra bằng PostgreSQL/Qdrant thật, provider/embeddings fakes. Không model calls hoặc thay đổi quality metrics/holdout. [Report](../docs/deletion-privacy-step09.md). Các reports dưới đây giữ nguyên lịch sử; human review vẫn pending.

**Lịch sử04/11/2026 — Bước08, tiến độ65,9% /100%:** [answering report](../docs/answering-step08.md) có3 oracle +2 API synthetic dev cases qua2runs. Run đầu4outputs validate/probes đạt,1eval_budget_exhausted trước generation; retest riêngunknown đạt. Tổng5generate+25countTokens đúng các xác nhận riêng,0USD/free tier, không sửa backend/prompt/model để retest. **276 backend +91 eval tests đạt** ở hai suites riêng; human review pending, không phải answer accuracy/held-out result. Giữ các reports lịch sử bên dưới. Runner đếm budget từ số chunks sau ingestion, hỗ trợ --case/per-run caps; full5ca cần21count calls nên cap20 mặc định từ chối preflight. Không tự tăng trần hoặc chạy lại model để kiểm tra artifacts.

**Trạng thái 03/11/2026:** reviewed-v1/gold mapping giữ nguyên 10 docs/45 approved questions/47 references. [Bước 07](../docs/search-retrieval-step07.md) có [dev retrieval run thật](reports/retrieval_dev_20261103T101104Z_968416c5/manifest.json): 15 queries (13 answerable/2 unknown), Recall@5=1/MRR@5≈0,923/0 errors; không answering accuracy hoặc held-out result. **86 eval tests pass**, backend suite riêng **222 pass**. Không LLM calls/tải model mới/test queries; ingestion/model reports lịch sử giữ nguyên. Tiến độ **56,1% / 100%**, Bước 08 chưa bắt đầu.

## Công cụ đã triển khai ở Bước 02

Từ repo root, dùng venv Python: `python -B -m eval.validate_dataset --dataset eval/snapshots/reviewed-v1 --require-reviewed` kiểm tra snapshot đã khóa. `python -B -m pytest eval/tests -q -p no:cacheprovider` kiểm thử trên bản sao tạm. Trên PowerShell máy này thay `python` bằng `.\backend\.venv\Scripts\python.exe`. Validator mặc định vẫn trỏ draft làm việc tại datasets; dùng đường dẫn reviewed tường minh cho smoke/eval.

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

## Command contract cần triển khai

Các script dưới **chưa tồn tại**; chỉ dùng sau khi được triển khai ở bước tương ứng và người dùng xác nhận đợt chạy có thể ghi artifacts/gọi model:

```bash
python eval/run_retrieval_eval.py --config eval/configs/dense.yaml --split test
python eval/run_answer_eval.py --config eval/configs/dense.yaml --split test
```

Software tests/integration kiểm tra contract và fault recovery tách khỏi benchmark model. M1 nghiệm thu AT-R01–23; P1 tương ứng AT-R24–26. Quy tắc workspace về câu xác nhận “Thực hiện đi” và cập nhật [KNOWLEDGE.md](../KNOWLEDGE.md) áp dụng cho việc tạo dataset, scripts và chạy evaluation.
