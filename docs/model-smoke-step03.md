# Bước 03 — Smoke model trên máy thật

**Ngày:** 03/11/2026.<br>
**Trạng thái mới nhất:** đạt gate bắt buộc Bước 03 với E5 CPU và Gemini inference thật. LLM run đầu 4/5 outputs hợp lệ, conflict retest riêng 1/1 đạt; **tổng 6 requests** sau xác nhận thêm 1 request. 72 eval tests đạt; BGE tùy điều kiện hoãn. Bước 04 chưa bắt đầu. Project giữ Free theo ảnh/xác nhận người dùng; live API cost để null khi chưa đối chiếu hóa đơn.

**Lịch sử trước live run:** sau khi điền key nhưng chưa kiểm tra tài khoản, [preflight lần 2](../eval/reports/smoke_llm_preflight_20261103_02/metrics.json) dừng đúng với 0 requests/0 USD, flags false và tiến độ 13,8%. Sau đó người dùng cung cấp ảnh project Free/quota chưa dùng; mới ghi nhận flags true và gọi API trong đợt đã duyệt. Không suy ra các hạn mức chính xác cho model từ ảnh quota bị cắt thiếu header/tên model. Các mô tả preflight bên dưới là lịch sử; kết quả live ở mục kế tiếp.

## Bước 02 đã được chốt

Sổ duyệt do hai thành viên cập nhật có **45/45 approved**, tên annotator/reviewer khác nhau, không có changes requested. `eval.publish_reviewed` kiểm tra rồi tạo bản sao riêng tại [reviewed-v1](../eval/snapshots/reviewed-v1/corpus_manifest.json): 10 tài liệu, 8 fixtures, 35 author blocks, 15 dev/30 test, 6 unanswerable. Snapshot lưu parent manifest hash, thời điểm phát hành và hash cả review ledger. Không điền/sửa danh tính hay trạng thái thay người dùng.

Draft tại `eval/datasets/` được giữ nguyên manifest `draft-v1`; sổ duyệt ở đó là bản làm việc đã được con người sửa. Đường dẫn reviewed mới là snapshot cho smoke/eval kế tiếp. `parser_span_mapping=pending_step05`: human review đã xong nhưng offset của production parser vẫn cần remap ở Bước 05.

Snapshot không chứa file khóa Word `~$*.docx`. `.gitignore` bỏ qua chúng; `.gitattributes` bảo toàn bytes dữ liệu/seed/snapshot để CRLF trên checkout Windows không làm sai hashes. Publisher stage bằng thư mục có quyền kế thừa workspace: lần đầu dùng TemporaryDirectory của Windows tạo ACL riêng, khiến process người dùng không đọc được sau rename. Đã sửa publisher và bật lại inheritance chỉ trên snapshot mới; bytes/hash không đổi. Không sửa ACL thư mục hệ thống hay dữ liệu khác.

## Cấu hình đã chạy

| Thành phần | Giá trị |
|---|---|
| Embedding | `intfloat/multilingual-e5-small` |
| Revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| Máy | Windows x64, i7-1165G7, RAM khoảng 16 GB, CPU inference |
| Runtime | Python 3.12.8; torch 2.9.1+cpu; transformers 4.57.6 |
| Dtype/pooling | FP32, attention-mask mean pooling, L2 normalization |
| Batch/threads | 4 / 2 |
| Prefix | `query: ` cho câu hỏi; `passage: ` cho nguồn |
| Giới hạn | 512 tokens gồm prefix, heading và special tokens; reject trước inference khi vượt |
| Cache | `D:/AI-Cache/sme-copilot/huggingface/hub`; chỉ 6 files cần thiết, không tải checkpoint BIN/ONNX/OpenVINO |

Tài nguyên trước install: C trống **13.969 MiB**, D **81.548 MiB**, RAM khả dụng **4.045 MiB**, đọc bằng Python disk usage/Win32 memory API. CIM bị sandbox chặn nên không dùng output Get-PSDrive rỗng như số đo thật. Đây là snapshot, chưa phải chứng cứ đủ cho BGE/local LLM lớn.

PyTorch CPU wheel tải khoảng **110,9 MB**; phần model cache tính riêng. `backend/requirements-ai-cpu.lock` pin cả dependencies mới, include dev lock và dùng URL wheel CPU Windows CPython 3.12. Lock này không dùng cho Docker Linux. Runtime production lock giữ nguyên. Không cài sentence-transformers, CUDA, torchvision/torchaudio, reranker hay local generative LLM trong lượt này.

## Kết quả inference thật

Run: [smoke_embedding_20261103_01](../eval/reports/smoke_embedding_20261103_01/report.md). Config, hashes code/model/tokenizer, timestamp, HEAD và trạng thái working tree lưu trong manifest. Working tree chưa commit tại thời điểm đo; không coi HEAD cũ là toàn bộ source đã chạy.

| Kiểm tra / số đo | Kết quả |
|---|---|
| Số input | 35 passages + 5 câu dev; thêm probe giới hạn riêng |
| Vector | Shape `[35, 384]`, FP32, CPU, finite |
| L2 norms | 0,99999988–1,00000012 |
| Padding/batch | Vector đầu tiên khi encode riêng/batch khớp trong tolerance 1e-5 |
| Giới hạn token | 512 tokens encode thật đạt; 513 tokens bị chặn trước model |
| Passage dài nhất trong corpus | 44 tokens sau prefix/heading/special tokens |
| Download/cache resolve | 12,70 giây ở lần đầu |
| Load model và imports | 5,79 giây trong process mới |
| Encode passage đầu | 49,09 ms |
| Encode 35 passages sau warmup | 0,407 giây, khoảng 86 passages/giây trên inputs rất ngắn này |
| 5 query timings | 16,14 / 18,83 / 14,17 / 16,43 / 13,57 ms |
| Process RSS trước import model | Khoảng 92,66 MiB |
| Peak RSS lấy mẫu | **723,13 MiB**, interval 20 ms |

Tokenizer báo warning khi cố ý tạo input 513 tokens; adapter chặn input đó, không chuyển nó vào model. Không coi warning này là inference vượt giới hạn đã thành công. Load là cold theo process, không kiểm soát OS disk cache; RSS lấy mẫu không bảo đảm bắt được đỉnh ngắn dưới 20 ms và không phải tổng RAM cả máy. Đây là một smoke run, 5 query timings chưa đủ để công bố p95/SLA.

Chưa đo retrieval Hit/Recall/MRR, chưa upsert collection, chưa chọn model thắng. Tất cả source blocks được encode để kiểm tra tương thích; không dùng test questions/ranking để tune. BGE-M3 hoãn vì chưa cần cho smoke baseline và RAM khả dụng ban đầu chỉ khoảng 4 GB; lựa chọn embedding cuối còn phụ thuộc dev evaluation ở Bước 07.

## LLM: giai đoạn chuẩn bị trước live run

Candidate giữ `gemini-3.5-flash-lite`. Public model card/pricing đã kiểm tra lại ngày 03/11/2026; standard input/output có free tier. Tài khoản/project thực chưa được xác minh. Người dùng xác nhận **chưa có key, cần hướng dẫn**. [Hướng dẫn thiết lập](gemini-free-tier-setup.md).

Adapter eval dùng native Google `generateContent`, không thêm OpenAI SDK. Cấu hình REST dựa trên `generationConfig.responseFormat.text` gồm `APPLICATION_JSON` và JSON Schema. Pydantic kiểm tra status/claims/missing evidence và citation-ID whitelist. Tối đa 5 requests tuần tự, 800 output tokens/request, timeout 45 giây/request; không tools, không retry/fallback. Cấu hình thinking/decoding ngoài default chưa được smoke thật, chưa khẳng định mọi tham số được provider chấp nhận.

[Preflight run](../eval/reports/smoke_llm_preflight_20261103_01/report.md) ghi `not_run`, thiếu key và hai xác nhận free tier/quota; **api_calls_attempted=0**. Không dùng stub responses để báo LLM đã chạy. Flags chỉ là xác nhận thủ công, không phải billing hard cap từ Google. Nếu sau này gọi thật và chưa có hóa đơn thì cost `null`, usage lưu như provider trả về.

Cases chuẩn bị: q001, q007, q009, q014 từ dev và một conflict ad hoc không được gọi là human gold. Case conflict không lấy câu test q024 để tune. Model response hợp schema/ID vẫn cần người chấm ngữ nghĩa; adapter chưa là production Q&A/citation service.

## Kiểm chứng và commands

Từ root, trong đợt được xác nhận:

```powershell
.\backend\.venv\Scripts\python.exe -B -m eval.publish_reviewed
.\backend\.venv\Scripts\python.exe -B -m eval.validate_dataset --dataset eval/snapshots/reviewed-v1 --require-reviewed
.\backend\.venv\Scripts\python.exe -B -m pytest eval/tests -q -p no:cacheprovider
```

Smoke embedding offline sau khi đã có cache:

```powershell
$env:HF_HOME='D:/AI-Cache/sme-copilot/huggingface'
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
$env:TOKENIZERS_PARALLELISM='false'
.\backend\.venv\Scripts\python.exe -B -m eval.model_smoke embedding
```

Lần đầu thêm `--download`; model public, không dùng paid inference endpoint. Runner tạo run directory mới và dừng nếu output đã tồn tại. `--output` chỉ dành cho một run ID mới. Publisher chạy lại cùng inputs kiểm tra snapshot, không sửa snapshot đã khóa.

Kiểm thử có cả pending review, publish/idempotency/tampered ledger, prefix/length guard, schema/ID lỗi, free-tier preflight trước network, native response parsing, bỏ thought parts, provider errors và dừng sau 429. MockTransport là software tests, không chứng minh Gemini thật hoạt động. Backend 64 cases/frontend build ở Bước 01 là bằng chứng lịch sử, không chạy lại trong đợt không sửa app/frontend này.

Kết quả lượt chuẩn bị ban đầu: **64 eval cases passed**, Ruff check/format và pip check đạt; sau live run/fixes là **72 eval cases passed**. Đây là suite `eval/tests`, khác 64 backend cases lịch sử ngày 02/11; không cộng thành một lượt full suite đã chạy.

## LLM: kết quả live và retest

User cung cấp ảnh Default Gemini Project có Free level và ảnh các counters quota ở mức 0; đây là bằng chứng thủ công, không phải truy vấn billing API. Native Google endpoint đã xác thực key và trả outputs cho `gemini-3.5-flash-lite`. Không bật billing, đổi model hay fallback.

| Run | Requests | Kết quả |
|---|---:|---|
| [Lượt đầu](../eval/reports/smoke_llm_20261103_01/assessment.md), prompt v1 | 5 | q001/q007/q009 grounded và q014 insufficient_evidence hợp lệ; conflict bị local parser/validator từ chối, run failed |
| [Retest conflict](../eval/reports/smoke_llm_conflict_20261103_02/assessment.md), prompt v2 | 1 | Người dùng duyệt thêm đúng 1 request; partial, claims dẫn E1/E2, missing_evidence nêu thiếu ngày hiệu lực, passed |

Run đầu đã dùng đủ 5 requests nên không tự gọi lại. Code/prompt được sửa và **68 tests pass** trước khi xin xác nhận request thứ 6. Retest chạy đúng một case qua CLI `--case-id`, không lặp bốn câu đã đạt. Sau đó thêm guard config max_calls phải là integer 1–5, tránh cấu hình 0 dẫn tới passed trên 0 samples; tổng kiểm thử hiện tại **72 passed**. Không gọi thêm API để kiểm tra thay đổi guard.

Kết quả run đầu vẫn failed, không ghi đè metrics/samples. Không có raw response của conflict đầu nên chưa biết chính xác nguyên nhân lỗi cũ; prompt v1 thiếu mô tả partial phải có missing_evidence là lỗi hướng dẫn phát hiện bằng đọc code, chưa chứng minh là root cause của response đã mất. Retest thành công là quan sát riêng, có cả thay đổi prompt và biến thiên model. Không trình bày thành 5/5 cùng prompt v2 hoặc cải thiện accuracy đo được.

Adapter mới tách schema validation error types và các contract errors (unknown ID, partial thiếu missing evidence...), giữ usage/model metadata được allowlist dù output bị từ chối. Không lưu Pydantic input/context, response headers/error body hoặc thoughts. Source snapshot `.py.txt` trong run retest giữ phiên bản đã chạy ngoài git HEAD; các runs cũ chỉ có source hashes không được biến thành full source snapshot bằng suy đoán.

Năm outputs hợp lệ khi gộp hai runs có usage đã biết: **717 prompt + 519 candidate = 1.236 tokens**. Usage request lỗi thứ 5 trong run đầu không được ghi nên tổng token của **6 calls là null**. Latency các calls khoảng 1,09–1,66 s; chưa đủ p95/SLA. Model version trả về khớp candidate. `serviceTier=standard` là inference metadata, không chứng minh billing tier. Không có thoughtsTokenCount không đồng nghĩa thinking bằng 0; profile không override thinking/temperature và chưa kiểm chứng các overrides đó. Native response schema/output fields đã được endpoint nhận; chưa test output đủ dài để chạm cap 800.

Đối chiếu outputs với context bởi trợ lý: ba câu grounded nêu đúng 12 ngày, thời hạn 3 ngày/người duyệt và IT/30 phút; câu thiếu nguồn từ chối; retest conflict không tự chọn hiệu lực. Đây không phải independent human scoring của generated answers. Gate smoke chỉ cần đường inference thật + output validate được, còn quality benchmark/human rubric ở Bước 07/11.

## Tiến độ hiện tại

Bước 02 hoàn thành. Bước 03 đạt các mục bắt buộc 1/2/3/4/6: có inference thật, structured outputs/ID validation, timings/usage/fingerprints và cấu hình tạm E5 CPU + Gemini hosted. Mục 5 là có điều kiện, BGE hoãn theo RAM headroom và chưa cần để đạt gate baseline; không đánh dấu đã chạy BGE. BGE còn là challenger ở đợt so sánh Bước 07. Profile thinking/temperature dùng mặc định, giới hạn đó được ghi rõ thay vì tuyên bố đã kiểm chứng tắt thinking.

`(1,5 + 4 + 7 + 5) / 102,5 × 100` → **17,1% / 100%**. PLAN v1.6 giữ nguyên trọng số, chỉ đóng gate bắt buộc; không tăng tiến độ vì số tests/docs. Bước 04 cần đợt xác nhận riêng, chưa triển khai.

Nguồn: [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small), [PyTorch install](https://pytorch.org/get-started/locally/), [Gemini model](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite), [pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite), [REST generation config](https://aistudio.google.com/api-reference/generate-content#GenerationConfig).
