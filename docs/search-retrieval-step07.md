# Bước 07 — Search, mở nguồn và dev retrieval baseline

Ngày 03/11/2026. Xác nhận “Bước 7 thực hiện đi”. Phạm vi backend, local E5 query embedding, source APIs, dev-only retrieval evaluator/tests, freeze config và tài liệu; không UI, không LLM/paid fallback, không commit/push. [PLAN](../PLAN.md), [spec 8.1/8.6/10/14.9](../SME_Knowledge_Copilot_RAG_Specification.md), [ADR RAG-02](decisions/0002-dense-retrieval-baseline.md).

## APIs và phạm vi bảo vệ

POST /api/v1/search nhận query 1–4.000 ký tự sau trim, top_k 1–10 (mặc định server 5), mode=dense, filters.document_ids tối đa 50 UUID khác nhau. Pydantic extra=forbid/strict query/top_k; không cho client chọn workspace/model/provider/collection. Non-dense 422 unsupported_retrieval_mode; embedding query >512 tokens gồm query prefix/specials → 422 question_too_long, không truncate.

Resolve toàn bộ IDs trong workspace trước xét status: bất kỳ foreign/missing ID trả 404 toàn request; own nonready 409, own deleting/deleted 410. Không filter hoặc [] nghĩa toàn workspace ready. Không có ready docs → hits=[]/no_ready_documents, không initialize/query model/vector. Chọn đúng active revision/generation và index/fingerprint tương thích; explicit incompatible source hoặc không còn compatible index trả 503 retrieval_unavailable.

Service kết thúc transaction read/auth trước model/network, snapshot các IDs/lifecycle cần kiểm tra. Caller tương lai phải commit query-run setup trước gọi retrieval. E5 dùng query: cho câu hỏi, passage: cho document; cùng weights/pooling/normalization của Bước 06, IPC thêm kind mà không đổi passage embeddings. Runtime lazy, một model child dùng lại, lock nonblocking: request bận trả 429 retrieval_busy; lifespan đóng model/client. Host API cần CPU dependencies/cache như worker; Docker Linux AI image chưa build/test.

Qdrant query /points/query dùng candidate_k=20, filter workspace + tập generation hợp lệ + index_version; keyword payload indices do worker ensure_collection tạo. API reader check_collection chỉ đọc, không tự tạo collection rỗng khi mất index. Final SQL query kiểm tra ready/active generation/revision/workspace/index/lifecycle, point mapping và payload IDs; text/filename/location luôn từ SQL. Payload text giả bị bỏ qua; stale/missing/forged IDs bị loại, không backfill nguồn chưa kiểm tra. Dedup point/chunk và sort score giảm dần rồi chunk ID; trả tối đa top_k. Trace counts/timings/model index hash phục vụ debug, không coi cosine score là confidence.

Model/vector/config lỗi → 503 retrieval_unavailable; không giả thành successful no-evidence. SQL lỗi giữ handler 503 database_unavailable. Score cutoff mặc định None; local runtime serialize inference, không hidden retry/provider fallback. Search-only không gọi LLM hoặc áp token budget của LLM, chưa có E1… citations/answer claims.

Code: [retrieval service](../backend/app/services/retrieval.py), [strict schema](../backend/app/schemas/search.py), [router](../backend/app/api/search.py), [vector adapter](../backend/app/services/vectors.py), [query IPC](../backend/app/services/embeddings.py).

## Source endpoints

GET /documents/{id}/chunks/{chunk_id}: bearer/workspace + ready active source; chunk khác document 404, inactive revision/generation 410, không tự remap citation cũ sang chunk mới. Trả text/location/source_spans/file_name/document_version trong envelope. Offsets giữ normalized Unicode contract Bước 05.

GET /documents/{id}/content: scope/status trước IO. PDF trả bounded original bytes application/pdf; TXT/MD original bytes text/plain; DOCX trả extracted raw body blocks theo thứ tự dưới dạng text/plain, không bịa trang Word hoặc trả XML/HTML. File resolve phải nằm storage root, size khớp metadata/cap và SHA-256 khớp; file mất/đổi → 410. Recheck active/lifecycle sau file IO. Filename header sanitize/UTF-8 percent encode; nosniff, no-store và CSP sandbox; embedded HTML Markdown là text.

P0 trả full response trong upload cap, không advertise Accept-Ranges hoặc giả 206. Request Range vẫn phải auth và nhận full 200 khi được phép. Không tuyên bố thu hồi bytes đã gửi trước delete; delete workflow/history còn ở Bước 09. Tests chứng minh source hiện tại bị chặn khi deleting/stale, actual UI preview chưa làm.

## Protocol và canonical evidence matching

[Baseline config](../eval/configs/dense.json) được freeze trước query đầu: E5-small revision 614241f622f53c4eeff9890bdc4f31cfecc418b3, FP32 CPU/384/Cosine, chunk350/overlap50, candidate20/production top5/eval top10, cutoff None. Index version **9851b494ba14e5a4370604ac33064d65b40690b990118fce057e4fbcb5afc4a4** giữ Bước 06 vì passage preprocessing không thay đổi. Model/chunker/normalization đổi phải version config + reindex; evaluator từ chối runtime khác frozen protocol.

[Loader](../eval/retrieval_gold.py) nối reviewed-v1 + immutable parser mapping sang actual active SQL UUID bằng document checksum/parser/index/fingerprint, raw+normalized text/location và chunk text/hash/spans. Fail rõ nếu drift; benchmark có fault injection text drift và xác minh loader từ chối, không giảm denominator. Corpus manifest version (ví dụ discount version 2) là semantic dataset label, SQL revision counter là lần upload (bắt đầu 1); map qua external ref/hash/revision UUID, không so hai counter khác namespace.

[Matcher](../eval/span_metrics.py): group gồm các quote thay thế (OR), một quote qua nhiều parser blocks có required spans (AND). Union intervals của content spans trong top-k, cùng block UUID/revision; mỗi required span phải phủ >=80% code points. Không đếm overlap hai lần, context heading/header lặp không tự thêm gold hits, không fuzzy-match sau khi xem kết quả. MRR rank sớm nhất hoàn tất một group, multi-evidence phải đủ mọi group. Unknown/unanswerable không có groups → retrieval metrics null và report riêng; không dùng lỗi model/index làm đúng abstention.

Macro metrics successful-answerable là chính; strict all-answerable giữ lỗi kỹ thuật ở denominator, failed cached output không được tính thành hit. Error rate tính trên toàn queries; denominator 0 → null/count. P95 latency dùng nearest-rank, 15 samples nên bằng max trong run, chưa phải SLA.

## Run thật và số đo

[Manifest](../eval/reports/retrieval_dev_20261103T101104Z_968416c5/manifest.json), [per-question](../eval/reports/retrieval_dev_20261103T101104Z_968416c5/per_question.jsonl), [config trước chạy](../eval/reports/retrieval_dev_20261103T101104Z_968416c5/config.json), [source hashes](../eval/reports/retrieval_dev_20261103T101104Z_968416c5/source_sha256.json). Chạy production search/source APIs qua member bearer, ingestion worker/E5/PostgreSQL/Qdrant thật, không LLM key/base URL. 10 corpus documents/54 blocks/14 chunks, 15 dev questions = **13 answerable / 2 unanswerable**, **0 test queries**. Model đã warm từ ingestion.

| K | Hit (n=13) | Macro Recall | MRR | All-evidence (multi-group n=1) |
|---|---:|---:|---:|---:|
| 1 | 0,8462 (11/13) | 0,8462 | 0,8462 | 1,0 |
| 3 | 1,0 | 1,0 | 0,9231 | 1,0 |
| 5 | 1,0 | 1,0 | 0,9231 | 1,0 |
| 10 | 1,0 | 1,0 | 0,9231 | 1,0 |

Technical failures **0/15**; successful/strict denominators trùng vì không có lỗi. HTTP search latency warm p50 **82,711 ms**, p95 nearest-rank/max **131,272 ms**, gồm auth/SQL/query inference/retrieval, không gồm open-source request sau đó. Không gồm model cold load. Sampled peak parent+children RSS **1.167.622.144 bytes (~1,09 GiB)**, sampling 20 ms/có thể double-count mapped pages. Không phải RAM model riêng hoặc bằng chứng ANN throughput trên corpus lớn.

Baseline hợp lý để nối answering P0; không suy ra accuracy AI=100%, không có test result hoặc so sánh model winner. Dev nhỏ, 14 coarse chunks và chỉ một multi-group case (hai groups nằm cùng document) làm bài dễ; chưa có đánh giá cross-document/identifier/conflict trên held-out test trong đợt này. Không chạy lại model chỉ để làm số đẹp hơn.

## Failure analysis và lựa chọn

- q010 (security.sharing): FAQ top1 0,8634, security đúng top2 0,8619. Source/span còn nguyên và eligible; đây là dense ranking ambiguity, không phải parser mất dữ liệu/filter leak.
- q012 (support.ticket): standalone heading chunk FAQ top1 0,8428; chunk có ticket evidence top2 0,8337. Header đứng riêng cạnh tranh nội dung. Treatment tương lai có thể bỏ standalone heading-only retrieval hoặc gộp heading với body, nhưng cần version chunker/index và đo dev lại; giữ baseline hiện tại vì top5 đã đủ evidence.
- q014/q015 unanswerable vẫn có candidates, top score **0,84529305 / 0,8375946**. Minimum answerable top score **0,84276205**; distributions chồng nhau ngay trên dev. Một cutoff cosine không giữ hết answerable và bỏ hết unknown. Giữ cutoff None; stage answering phải xem evidence/claims và abstain khi thiếu support. Đây chưa phải failure/abstention score của LLM.

Parser/chunk/source mapping đã đối chiếu đầy đủ, scope/revalidation trace không loại sai trong run; không có context budget ở search-only. Chưa đổi model hoặc chunk config để “sửa” hai top1 misses. BGE-M3 hoãn vì chưa cache và RAM margin chưa validate (available trước run ~2,77 GiB, probe sau ~3,11 GiB). Không có BGE measurements; E5 là baseline khả dụng, không khẳng định vượt BGE. P1 hybrid/reranker/threshold calibration cần thí nghiệm riêng và test holdout giữ kín.

## Kiểm tra và bàn giao

Search/source tests dùng real SQL/Qdrant + fake embeddings có nhãn, tách run model thật. Kiểm tra auth/member/foreign IDs, extra fields/UUID/top-k/token budget, active filter, forged payload/stale IDs/dedup/ties, delete race, technical error, busy model, PDF/DOCX/MD source, checksum/storage escape và auth cho Range. Metric tests kiểm alternatives/required spans/union/overlap/MRR/null/technical denominators. Có test tái tính metrics và kiểm source snapshot hashes của run, không inference lại.

Chạy host API với CPU dependencies/cache như Bước 06, không startup download. `python -B -m eval.run_retrieval_eval` từ root tạo run mới, guard DB *_test và collection/workspace riêng, không chạy cùng worker/tests dùng chung queue. Report status=completed/cleanup_completed=true; dọn đúng collection, SQL/users/tokens/files, giữ artifacts/source snapshots. Không sửa reviewed snapshot/mapping hoặc các reports cũ.

Kết quả cuối: **222 backend passed/1 warning**, **86 eval passed** ở hai suites riêng. Ruff check/format **96 files**, pip check đạt. Warning Starlette TestClient/httpx giữ từ baseline; không skip test. Fixture reliability dùng chung worker_support.py/conftest cho full collection. Runtime không đổi dependencies/schema/applied migration; chỉ thêm config và payload indices.

Probe bàn giao: worker --once exit0, default collection đã có 5 keyword indices workspace/document/revision/generation/index_version. Dev/test head20261103_rag04; cả hai 0 documents/revisions/blocks/chunks, dev giữ2users/test0users. Qdrant chỉ còn knowledge_e5_small_v1/0points; dữ liệu dev eval được dọn đúng scope. Reviewed manifest SHA-256 vẫn efccfaeaf67e9e49035d08771977982ccd34df83d12128a4835948738f2c6b26, parser mapping vẫn a75f4b8c23c7a1270f0f911a8d8db11ce56af454913904f12501e902471d933b. Scan230 source/docs/eval/config files không có secrets thực .env; local links và Git whitespace đạt. Không giữ server/model process chạy nền sau kiểm chứng.

Bước 07 đủ 6 mục bắt buộc, mục so E5/BGE có điều kiện đã ghi hoãn; giữ trọng số10. `(47,5+10)/102,5×100 =56,097…` → **56,1% / 100%**. Bước 08 answering/citations/session cần xác nhận riêng, tiếp tục ngân sách0USD. Trước code UI phải nhắc/chờ xác nhận riêng theo AGENTS.
