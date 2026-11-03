# ADR RAG-02 — Dense E5 baseline, SQL revalidation và dev-only metrics

Ngày 03/11/2026. **Đã triển khai/đo Bước 07**; [report](../search-retrieval-step07.md), [config](../../eval/configs/dense.json), [service](../../backend/app/services/retrieval.py).

Chọn E5-small CPU/Cosine, candidate20/top5, query: vs passage:, local cached weights. Qdrant filter workspace + active generation + pinned index, SQL đọc lại text/permission/lifecycle. Payload không là nguồn authorization/content; query embedding/vector failure là technical 503, không empty success. Reader check collection chỉ đọc; worker tạo payload indices. API runtime lazy một child/lock, hết capacity 429 thay vì unbounded queue.

Phương án filter SQL chỉ sau retrieval có thể để orphan/foreign candidates chiếm hết top-k; chỉ tin Qdrant payload làm stale/delete leak. Hai lớp bảo vệ có thêm SQL latency nhưng phù hợp source-of-truth contract. Không giữ DB transaction qua inference; context builder/query-run tương lai phải commit setup trước gọi search. Source chỉ active revision/generation, plain text cho MD/DOCX, PDF bounded bytes/hash/nosniff; chưa Range UI.

Giữ cutoff tắt: scores answerable/unanswerable chồng nhau trên dev; cosine không là xác suất đúng. 13 answerable có Recall@5=1, MRR@5≈0,923, không có nghĩa answering=100%. Parser/mapping đã validate, hai top1 misses là topic ambiguity/standalone heading, vẫn có đủ support trong top3. Chưa tune chunker/model/test queries để cải thiện số. BGE/hybrid/reranker hoãn; E5 là baseline chạy được trong RAM hiện tại, chưa model winner.

Metrics bám canonical quote/location → active block UUID, union 80% theo group/alternatives, tách multi-evidence, unknown, success-only và strict denominators. Thay parser/preprocessing/model/config phải version và reindex. Giữ reviewed snapshot, freeze dev protocol trước run và lưu source snapshots; test set chưa query. Xem lại khi corpus thật lớn hơn, dev có nhiều unknown/cross-document/identifier cases hoặc heading treatment cần đánh giá. Answering abstention/citations là bước kế tiếp riêng.

Nguồn: [Qdrant query](https://api.qdrant.tech/api-reference/search/query-points), [filtering](https://qdrant.tech/documentation/search/filtering/), [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small), [Starlette responses](https://starlette.dev/responses/). Không thay ADR RAG-05/06/07; bổ sung retrieval quanh ingestion/identity/source contracts.
