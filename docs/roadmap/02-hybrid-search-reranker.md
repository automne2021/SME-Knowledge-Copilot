# 02 — Hybrid search tiếng Việt và reranker

**Mốc:** M2 · **Công sức:** L · **Phụ thuộc:** 01 (cần `dev2`, `test2` và runner hồi quy) · **Nhánh:** `feat/02-hybrid-search`

## Mục tiêu

Kết hợp tìm kiếm từ khóa với dense retrieval, sau đó thử thêm reranker. Phải chứng minh bằng số liệu trên bộ eval v2. Nếu không cải thiện thì vẫn giữ dense làm mặc định và ghi kết quả âm tính.

## Giá trị với nhà tuyển dụng

Đây là câu chuyện "thí nghiệm có kiểm soát" mạnh nhất của project:
- Mỗi lần chỉ đổi một biến.
- Đo theo nhóm câu hỏi (slice).
- Nêu rõ trường hợp nào từ khóa thắng: mã biểu mẫu, câu không dấu.
- Phải xử lý tách từ tiếng Việt thật sự, không dùng thư viện có sẵn một cách máy móc.

## Hiện trạng

- `backend/app/services/retrieval.py::search`:
  - Chỉ chấp nhận `payload.mode == "dense"`, mode khác trả 422 `unsupported_retrieval_mode`.
  - Luồng: SQL snapshot → embed query (E5, prefix `query:`) → Qdrant top-20 → kiểm tra lại bằng SQL → top-5.
- `backend/app/schemas/search.py`: `mode: StrictStr = "dense"`.
- `chat.py` lưu `retrieval_mode` vào `config_json` và vào hash idempotency.
- Postgres dùng image `pgvector/pgvector:pg16`, có sẵn contrib `unaccent`. Qdrant v1.20 hỗ trợ sparse vector với modifier IDF.
- Baseline dev cũ (K-059): 2 câu trượt ở Recall@1, một câu do chunk chỉ có heading cạnh tranh với chunk chứa nội dung. Không tìm được ngưỡng cosine nào tách được câu có và không có đáp án.

## Thiết kế

### Lớp từ khóa: chọn bằng spike (T1)

| Phương án | Cách làm | Ưu | Nhược |
|---|---|---|---|
| **A. PostgreSQL full-text** (khuyến nghị thử trước) | Cột `chunks.lexical_tsv tsvector`, xây từ text đã chuẩn hóa: lowercase, cộng thêm bản bỏ dấu bằng `unaccent`, token là âm tiết **và** cặp âm tiết liền kề (bigram) để xấp xỉ từ ghép tiếng Việt. Index GIN. Truy vấn `ts_rank_cd` | Lọc workspace, ready, generation ngay trong SQL nên khớp nguyên tắc "SQL là nguồn sự thật"; không phải reindex Qdrant | `ts_rank_cd` không phải BM25 thật; cần migration và backfill |
| **B. Qdrant sparse vector + IDF** | Named sparse vector trong collection; token hóa ở Python (âm tiết + bigram); `modifier: idf` | Gần BM25; một lần query lấy cả hai loại | Phải tạo collection hoặc index version mới và reindex; vẫn phải kiểm tra lại bằng SQL |

- **Tách từ:** bắt đầu bằng âm tiết + bigram (không thêm dependency). Thư viện tách từ (`pyvi`, `underthesea`) chỉ thử nếu spike cho thấy bigram không đủ; thêm dependency cần người dùng duyệt.
- **Không dấu:** index cả token có dấu và token đã bỏ dấu; query cũng chuẩn hóa hai dạng.

### Gộp kết quả

- **Reciprocal Rank Fusion:** `score = Σ 1/(k + rank)`, `k = 60`, lấy top-20 dense và top-20 lexical. Không trộn điểm thô, vì cosine và `ts_rank` không cùng thang đo.
- Sau khi gộp vẫn kiểm tra lại bằng SQL như hiện tại (bất biến 2). Trả top-5.
- **Trace thêm:** `lexical_candidate_count`, `fusion`, rank theo từng nguồn cho mỗi hit (chỉ ID và rank, không lưu text).

### Reranker (T5, tùy chọn)

- Cross-encoder đa ngôn ngữ nhỏ chạy CPU, ví dụ dòng `mmarco-mMiniLMv2` (~118M tham số). Rerank top-20 sau fusion.
- **Bắt buộc đo** latency p95 trên máy hiện tại. Nếu p95 search tăng quá 1,5 s thì không bật mặc định.
- Tải model mới cần người dùng duyệt (dung lượng, license). Pin revision và fingerprint như E5 (K-029, K-050).

### API và cấu hình

- `SearchRequest.mode`: `"dense" | "hybrid"`. Thêm `"hybrid_rerank"` nếu làm T5.
- Biến cấu hình `RETRIEVAL_MODE_DEFAULT`, mặc định vẫn `dense` cho tới khi có kết quả trên `test2`. Biến `RETRIEVAL_RRF_K=60`.
- `ChatQuery.retrieval_mode` nhận các giá trị mới. Hash idempotency đã chứa mode nên không cần đổi thêm.
- Cập nhật spec mục 8.1, 10.3 và 12.2.

## Task

### T1 — Spike so sánh A và B (chỉ đo, không merge vào code chính)

- Viết script trong `eval/` dựng chỉ mục lexical tạm cho corpus v2 và chạy trên `dev2`.
- **Đầu ra:** report so sánh A và B (Recall@5 theo slice, latency, công sức triển khai), cùng **khuyến nghị**. Dừng lại để người dùng chọn.

### T2 — Lớp lexical (theo phương án đã chọn)

- Gồm: migration (nếu chọn A) kèm backfill cho chunk hiện có, service `lexical.py`, worker ghi dữ liệu lexical lúc publish.
- Publish vẫn nguyên tử. Tài liệu bị xóa không được trả về từ lớp lexical.
- **Test:**
  - Tài liệu `deleting` không xuất hiện.
  - Workspace khác không xuất hiện.
  - Generation cũ không xuất hiện.
  - Câu không dấu tìm được chunk có dấu.
  - Mã `BM-09` tìm đúng.

### T3 — Fusion và mode `hybrid`

- RRF, trace, API mode, cấu hình mặc định vẫn là `dense`.
- **Test:** hai danh sách xếp hạng cho kết quả RRF đúng (unit); hybrid vẫn đi qua kiểm tra lại bằng SQL (integration); mode lạ trả 422.

### T4 — Đo trên `dev2`, chốt, rồi chạy một lần trên `test2`

- Chạy runner hồi quy với dense và hybrid trên `dev2` và tinh chỉnh (chỉ trên `dev2`).
- Chốt cấu hình, sau đó chạy **một lần** trên `test2`.
- Report:
  - Bảng theo slice, kèm mẫu số.
  - Danh sách câu tốt lên và câu kém đi.
  - Quyết định có đổi mặc định hay không.
- Nếu đổi mặc định, cần chạy answering eval có ngân sách riêng (đợt xác nhận riêng).

### T5 — Reranker (tùy chọn, đợt xác nhận riêng vì tải model)

- Tích hợp, đo latency và chất lượng như T4.

## Số đo bắt buộc

Recall@1/@5, MRR@5 và nDCG@5 theo slice; p50 và p95 thời gian search; kích thước index lexical; thời gian backfill.

## Rủi ro

- Corpus nhỏ nên chênh lệch có thể nằm trong nhiễu. Report phải ghi số câu thay đổi, không chỉ ghi %.
- Bigram làm index to hơn. Theo dõi kích thước bảng.

## Không làm

- Không dùng LLM để viết lại query trong tính năng này (thuộc 06).
- Không đổi model embedding.
- Không đặt ngưỡng score để từ chối trả lời.
