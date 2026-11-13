# 01 — Mở rộng bộ đánh giá và chạy hồi quy

**Mốc:** M2 · **Công sức:** M · **Phụ thuộc:** 00-T1 · **Nhánh:** `feat/01-eval-v2`

## Mục tiêu

Có bộ eval **v2** đủ lớn và đủ đa dạng để so sánh các thay đổi retrieval và model ở 02, 04, 06, 08, 10. Kèm một lệnh chạy hồi quy retrieval **không tốn quota LLM**, chạy được sau mỗi thay đổi.

## Giá trị với nhà tuyển dụng

"Evaluation-driven development" là điểm khác biệt lớn nhất của project. Có v2 thì mọi cải tiến sau đều kể được dạng: "Recall@5 trên nhóm câu hỏi bảng tăng từ X lên Y, mẫu số Z".

## Hiện trạng

- **Dữ liệu:**
  - Corpus 10 tài liệu giả lập trong `eval/datasets/corpus/`.
  - 45 câu đã người duyệt (15 dev, 30 test), snapshot khóa ở `eval/snapshots/reviewed-v1`.
  - Phân bố loại câu: 22 direct_fact, 6 unanswerable, 6 exact_identifier, 3 multi_section, 3 paraphrase, 3 cross_document, 1 conditional, 1 conflict.
  - Bằng chứng gold chỉ ở dạng `line_range`, `docx_block`, `pdf_page`; **chưa có câu nào lấy từ bảng**.
- **Quy trình:** seeds (`eval/seeds/`) → `eval/build_dataset.py` → review của người (`docs/human-review-guide.md`, `eval/datasets/human_review.csv`) → `eval/publish_reviewed.py` tạo snapshot khóa. Snapshot không tự approve.
- **Runner:**
  - `eval/run_retrieval_eval.py`: chỉ chạy 15 câu dev, đi qua search API thật, guard DB `*_test`.
  - `eval/run_answering_eval.py` và `eval/final_*`: gọi Gemini thật, có ledger và pacing.
- **Metric:** `eval/metrics.py` (`retrieval_scores`, `abstention_scores`) và `eval/span_metrics.py`.
- **Quy tắc giữ nguyên:**
  - Held-out v1 đã chạy **một lần**; kết quả 29/30 là lịch sử, không chạy lại để "cải thiện".
  - Không tune trên test split.

## Thiết kế

### Corpus v2

- Giữ nguyên 10 tài liệu v1. Thêm **12–15 tài liệu giả lập**, ghi rõ "TÀI LIỆU GIẢ LẬP" như v1:
  - 3–4 tài liệu có **bảng**: bảng giá, định mức công tác phí, ma trận phê duyệt. Gồm cả DOCX table và PDF có bảng kẻ khung.
  - 2 tài liệu **dài** (15–30 trang PDF có text) để kiểm tra nhiễu.
  - 2 tài liệu **gần trùng** (phiên bản cũ và mới của cùng quy định) để kiểm tra mâu thuẫn.
  - 2 tài liệu chứa nhiều **mã định danh** (mã biểu mẫu, mã phòng ban) cho câu `exact_identifier`. Đây là nơi BM25 thường thắng dense.
  - 1–2 tài liệu **viết không dấu** hoặc lẫn tiếng Anh, giống email nội bộ thật.
  - 2 tài liệu **scan** (PDF ảnh), chỉ dùng cho 08-OCR; hiện tại phải ra `needs_ocr`.
- Thêm vào `eval/seeds/corpus.json`, sinh file bằng script có sẵn hoặc script mới trong `eval/`. Mọi file phải tái tạo được từ seed.

### Câu hỏi v2

- **Thêm 60–80 câu.** Mỗi câu gắn trường mới `slice` (một giá trị chính) và giữ `question_type` như cũ. Các slice:
  - `text`: văn bản thường.
  - `table`: đáp án nằm trong hàng bảng.
  - `identifier`: hỏi theo mã.
  - `multi_doc`: cần ≥ 2 tài liệu.
  - `conflict`: hai nguồn mâu thuẫn.
  - `unanswerable`: tài liệu không có đáp án.
  - `no_diacritics`: câu hỏi gõ không dấu.
  - `scan`: chỉ có ý nghĩa sau khi làm 08.
  - `follow_up`: câu cần ngữ cảnh câu trước, dùng cho 06; có trường `history`.
- **Mỗi slice tối thiểu 8 câu**, trừ `scan` và `follow_up` (tối thiểu 6).
- **Split mới:**
  - `dev2` (khoảng 40%): được dùng để tune.
  - `test2` (khoảng 60%): chỉ chạy khi chốt cấu hình của một tính năng.
  - Câu v1 giữ split cũ; không chuyển câu test v1 sang dev2.
- **Schema `questions.jsonl` v2:** thêm `slice`, `dataset_version: "v2"`, `history` (tùy chọn). Validator (`eval/validate_dataset.py`) chấp nhận cả v1 và v2.
- **Người duyệt:** Codex chỉ tạo **draft**. Người dùng và đồng đội duyệt theo `docs/human-review-guide.md` (2 người, ghi bất đồng). Codex **không** tự đánh dấu approved.

### Runner hồi quy retrieval

- Lệnh mới `python -B -m eval.regression --dataset <snapshot> --split dev2 --config <config.json>`:
  - Ingest corpus vào DB `*_test` và collection Qdrant riêng (dùng lại guard của `run_retrieval_eval`).
  - Gọi production search qua API, **không gọi LLM**.
  - Xuất `eval/reports/regression_<config>_<timestamp>/`: `metrics.json`, `per_question.jsonl`, `summary.md`.
- **Metric theo slice:** Recall@1/@5, MRR@5, nDCG@5, tỉ lệ có ≥ 1 gold trong top-5; p50 và p95 thời gian search.
- **So sánh:** `python -B -m eval.compare <report_a> <report_b>` in bảng chênh lệch theo slice, liệt kê câu tốt lên và kém đi.

### Answering eval v2 (có ngân sách)

- Tái dùng `eval/final_*` (ledger, pacing). Chỉ chạy trên `test2` khi một tính năng chốt cấu hình, trong đợt có xác nhận riêng, ghi trước số lần gọi dự kiến.

## Task

### T1 — Schema và validator v2

- Thêm `slice`, `dataset_version`, `history` vào schema; validator hỗ trợ v1 và v2; thêm test cho câu v2 hợp lệ và không hợp lệ.
- Không đổi snapshot `reviewed-v1`.

### T2 — Corpus v2 (tài liệu)

- Seed và sinh 12–15 tài liệu như ở phần Thiết kế. Thêm test: parser đọc được mọi tài liệu không phải scan, tài liệu scan ra `needs_ocr`, bảng có `location.kind` là bảng.
- Report liệt kê từng tài liệu: định dạng, số trang, số chunk, slice phục vụ.

### T3 — Draft câu hỏi v2 và gói review

- Draft 60–80 câu kèm gold evidence (span) và dùng mapping tool hiện có để gắn chunk.
- Xuất gói review (CSV hoặc markdown) cho người duyệt. **Dừng ở đây**, chờ người dùng duyệt.

### T4 — Publish snapshot v2 sau khi người duyệt xong

- Publish bằng `eval/publish_reviewed.py` (mở rộng nếu cần) ra `eval/snapshots/reviewed-v2`. Lưu hash; snapshot là bất biến.

### T5 — Runner hồi quy và so sánh

- Viết `eval/regression.py` và `eval/compare.py` kèm test (dùng fake embedder cho unit test, một test SQL/Qdrant thật cho luồng ingest → search).
- Chạy baseline dense hiện tại trên `dev2`; lưu report làm **mốc so sánh** cho tính năng 02.

## Số đo bắt buộc trong report

- Baseline dense trên `dev2`: bảng metric theo slice, kèm mẫu số từng slice.
- Thời gian ingest corpus v2 và thời gian chạy hồi quy.

## Rủi ro

- **Người duyệt là nút thắt.** Plan phải dừng ở T3 cho tới khi có nhãn.
- **Câu hỏi do Codex draft có thể thiên về cách tài liệu được viết.** Yêu cầu người duyệt viết lại ít nhất 30% câu theo cách người dùng thật hỏi.

## Không làm

- Không dùng LLM để tự chấm làm nhãn chính (LLM-as-judge chỉ là phụ, nếu có, và phải ghi rõ).
- Không chạy lại held-out v1.
- Không đưa tài liệu thật của công ty nào vào corpus.
