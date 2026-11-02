# RAG Evaluation

Nguồn yêu cầu: [Spec RAG mục 14–15](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN bước 02, 07, 11](../PLAN.md). Mục tiêu là đo retrieval/answering có thể tái lập, gồm cả thiếu bằng chứng và lỗi kỹ thuật. Các kế hoạch đánh giá STT/action items cũ không còn là tiêu chí của project RAG.

**Trạng thái 02/11/2026:** có 10 tài liệu giả lập, 45 câu nháp (15 dev/30 test, 6 unanswerable), 8 fixtures, builder/validator/metric primitives và **37 tests pass**. **0/45 human-approved**; chưa có human gold, parser mapping hoặc model benchmark. [Hướng dẫn dataset/review](datasets/README.md), [báo cáo Bước 02](../docs/dataset-step02.md). Tiến độ project **11,2% / 100%** theo [PLAN](../PLAN.md). Baseline Bước 00/01 là software/infra checks, không phải evaluation model.

## Công cụ đã triển khai ở Bước 02

Từ repo root, dùng venv Python: `python -B -m eval.validate_dataset` để kiểm tra chỉ đọc; `python -B -m pytest eval/tests -q -p no:cacheprovider` kiểm thử dữ liệu/metric trên bản sao tạm. Trên PowerShell máy này thay `python` bằng `.\backend\.venv\Scripts\python.exe`. `--require-reviewed` hiện từ chối vì nhãn chưa được hai người duyệt.

`eval/build_dataset.py` tạo/đối chiếu artifacts từ `seeds/` và không ghi đè files đã sửa; chỉ chạy trong đợt được xác nhận. `eval/metrics.py` nhận **evidence groups đã match hoàn chỉnh**, trả per-question Hit/Recall/MRR/All-evidence và abstention math; chưa match spans/chunks, chưa macro aggregate, chưa gọi retrieval/model hay sinh benchmark reports. Mapper cần theo spec 14.9 (revision/block và coverage 80%, multi-span/union) ở bước triển khai sau.

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

Tree là contract đích; hiện datasets có cả `source_blocks.json`, `human_review.csv`, `README.md` và fixtures. Các configs/runners/reports trong tree vẫn chưa triển khai. Không tạo report rỗng rồi trình bày như đã eval; mỗi run có ID riêng, không ghi đè kết quả cũ.

## Dataset và gold evidence

- Mục tiêu M1: 8–12 tài liệu giả lập và 30–60 câu; draft hiện có 10 tài liệu/45 câu, đủ direct fact, paraphrase, exact identifiers, multi-evidence/conflict và 6 unanswerable theo spec/PLAN; còn chờ human review.
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
