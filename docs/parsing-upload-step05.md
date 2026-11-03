# Bước 05 — Upload, parser và chunker giữ nguồn

Ngày 03/11/2026. Đợt backend được xác nhận bằng “Vậy giờ bước 5 bạn thực hiện đi”. Không sửa UI, không commit/push và không gọi LLM. [PLAN](../PLAN.md), [spec 7.3, 10, 13.3](../SME_Knowledge_Copilot_RAG_Specification.md), [KNOWLEDGE K-043–048](../KNOWLEDGE.md).

## Kết quả và ranh giới

Hoàn thành 7 đầu việc của Bước 05: upload có authorization/stream limits/dedup; parser bốn định dạng; resource bounds; tokenizer-aware chunks; kiểm tra nguồn thật; mapping toàn bộ gold; race test PostgreSQL. Tiến độ `(25,5+12)/102,5×100 = 36,585…` → **36,6% / 100%**. Giữ nguyên trọng số.

Upload trả `202` cùng `document_id`, `job_id`, `status=queued`. Revision `staging`, chưa có active generation. Parser/chunker là services thật dùng trong kiểm thử và mapper, chưa có worker gọi từ queue. Chưa có embedding/index/search/answer/delete workflow. Các phần `202 → ready` và job terminal states của AT-R01–05 cần nối và nghiệm thu tại Bước 06; đây chưa phải full end-to-end acceptance.

## API và file storage

- `POST /api/v1/documents`: bearer `knowledge_admin`, một multipart field `file`; không cho client truyền workspace. Role/workspace lấy lại từ SQL identity. OpenAPI mô tả binary multipart.
- Giới hạn file mặc định **20 MiB** khi đọc từng 64 KiB. Tổng request tối đa file cap + 64 KiB framing; kiểm tra cả Content-Length và receive bytes để chặn request không khai báo độ dài. Multipart chỉ có một file/không có text fields; thư viện đóng spool khi parsing lỗi.
- Kiểm tra extension/MIME/signature trước khi tạo metadata; MIME generic octet-stream được chấp nhận nếu signature hợp lệ, Markdown nhận text/plain. PDF phải có `%PDF-`, DOCX có ZIP signature; text không giả PDF/ZIP/NUL. Valid UTF-8 và cấu trúc PDF/DOCX được parser kiểm tra sau, không giả rằng magic bytes chứng minh tài liệu đọc được.
- Filename chỉ là metadata hiển thị. Kiểm tra cả filename đã parse và filename trong Content-Disposition gốc, vì python-multipart có compatibility rule bỏ đường dẫn Windows. Từ chối path separators/drive/control characters; không dùng tên người dùng để mở file.
- Storage key `<workspace UUID hex>/<revision UUID hex>.<extension>` sinh tại server. Đường dẫn resolve phải nằm trong storage root; không expose key/hash/path trong upload response. Key ngắn giúp tránh Windows MAX_PATH ở workspace dài.
- SHA-256 tính trên bytes gốc. DB partial unique index `(workspace_id,sha256) WHERE status <> 'deleted'` quyết định dedup, kể cả `deleting`; đổi filename/extension không vượt được. Cùng bytes ở workspace khác được phép. Duplicate trả `409 duplicate_document` cùng ID/status đúng workspace.
- File ghi trước, document/revision/job flush trong cùng SQL transaction. Savepoint cho phép phân loại unique violation và đọc duplicate sau rollback cục bộ. Known validation/flush/commit rollback dọn file. Nếu mất commit acknowledgement, kiểm tra revision trước khi xóa; nếu DB chưa thể xác minh, giữ file và log document ID. Filesystem + PostgreSQL không có distributed transaction: process kill/DB outage kéo dài còn cần orphan reconciliation ở vòng worker/vận hành, không tuyên bố crash-proof.

Code: [upload router](../backend/app/api/uploads.py), [storage/transaction](../backend/app/services/uploads.py). Schema Bước 04 đủ dùng; không tạo/sửa migration đã áp dụng. Dev không được thêm tài liệu test; integration tests dùng DB test riêng.

## Parser contract

`parse_file` chạy Python subprocess mới, timeout cứng **60 giây** gồm native calls; timeout kill/wait tiến trình trước khi cleanup temporary directory. Không dùng thread timeout để giả vờ dừng MuPDF/XML. Child stdout/stderr không đưa nội dung tài liệu vào logs. [Parser](../backend/app/services/parsing.py) trả `ParsedDocument(blocks,warnings,parser_version)`.

| Loại | Block/location | Hành vi đã kiểm tra |
|---|---|---|
| PDF | Text block/bbox, page 1-based; chunk không xuyên trang | 200 trang; scan → needs_ocr; blank → no_extractable_text; encrypted → encrypted_document; malformed → parse_failed |
| PDF mixed | Chỉ giữ trang có text | Warning partial_text_extraction, skipped_pages=[2] ở fixture; không tuyên bố OCR |
| DOCX | Body paragraphs theo thứ tự; bảng theo table/row | Không bịa page Word; heading và header hàng đầu có provenance; header/footer không nằm trong body parser P0 |
| TXT/MD | Một nonblank source block trên mỗi dòng; giữ line number kể cả dòng trắng | UTF-8/BOM, CRLF, NFC; encoding sai bị từ chối; HTML/link/injection là text, không chạy/tải URL |
| Bảng | DOCX, bảng pipe Markdown; PDF bảng có đường kẻ dùng lines_strict | Serialize hàng với dấu ` | `, lặp header bằng context span; không cam kết bảng phức tạp/ô gộp/biểu đồ hoặc PDF không có cấu trúc kẻ |

DOCX được kiểm tra ZIP trước python-docx: tối đa **2.000 entries / 100 MiB uncompressed**, từ chối encrypted entries/duplicate names/path traversal và thiếu các Office parts bắt buộc; không extract archive ra filesystem. Thêm giới hạn **2.000.000 code points tổng raw+normalized**, **20.000 nonblank blocks**, **5.000 chunks**. Đây là guards khởi đầu, chưa là OS memory quota hoặc số đo xử lý file cực đại. Một worker concurrent job và resource measurement thuộc bước sau.

`raw_text` là text thư viện trích/serialize, không phải bytes gốc PDF/DOCX. `normalized_text` = NFC, whitespace collapse, trim, U+00AD → `-`; quy tắc soft hyphen được freeze vì PDF mẫu in BM-09 nhưng extract thành BM­09. Không sửa gold quote. Offsets là Unicode code points 0-based, end-exclusive trên normalized block; page/line/block 1-based. Không dùng offsets normalized để cắt raw text.

## Chunker / cấu hình model

[Chunker](../backend/app/services/chunking.py) dùng **tokenizer E5-small** từ tokenizer.json trong cache local, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`; không load torch/weights, không tải model mới. Token count bao gồm `passage: ` và special tokens. Target **350 là budget toàn input**, nhỏ hơn hard limit 512; overlap target 50 ở phần phải tách block dài. Không áp overlap qua page/heading/table-context boundary. Trước encode mỗi chunk được đếm lại, không truncation/padding âm thầm.

Gộp blocks có cùng cấu trúc đến budget; block dài tách ở Unicode/word boundary và giữ đủ source spans. Mỗi chunk có SHA-256, token_count, location tổng hợp + locations chi tiết và spans `{block_id,char_start,char_end,role}`. Role `context` phân biệt heading/header lặp với `content`; context vẫn trỏ nguồn thật. Parser-local block IDs ổn định trong output; Step 06 cần ánh xạ sang UUID theo generation khi persist.

Header context vượt budget trả document_limit_exceeded thay vì âm thầm cắt điều kiện. Giới hạn chiều dài lần tokenize và max chunks chặn văn bản dài bệnh lý. [prepare_document](../backend/app/services/ingestion.py) gom cấu hình parser/chunker thành entry point dùng chung cho worker tương lai. Settings và .env.example đã thêm đúng các biến thực thi; không sửa secrets .env. Parser/tokenizer dependencies đã chuyển sang runtime lock, giữ nguyên versions đang cài và không thêm torch vào runtime tối thiểu.

## Gold mapping và kiểm chứng nguồn

[Mapping version 1](../eval/mappings/reviewed-v1-source-v1-e5-350-v1.json) là artifact mới, không sửa reviewed-v1 hoặc draft labels. Manifest/ledger/source hashes được giữ. Snapshot cũ còn parser_span_mapping=pending_step05 vì bất biến; mapping mới liên kết snapshot bằng parent hash.

Kết quả: **10 documents → 54 parser blocks → 14 chunks**, tối đa **162 input tokens/chunk** trong corpus nhỏ này; **35 author blocks / 45 questions / 47 evidence references** map được bằng quote + location. Corpus ngắn không chạm budget 350; test block tiếng Việt dài riêng kiểm tra coverage/overlap/hard budget. Tất cả gold characters phải được union content spans bao phủ; ambiguous/missing quote hoặc mất location phải fail, không fuzzy-match/bỏ câu. Giữ đủ 6 unanswerable; không dùng câu test để tune retrieval.

SHA-256 mapping: `a75f4b8c23c7a1270f0f911a8d8db11ce56af454913904f12501e902471d933b`. Git attributes giữ nguyên bytes cho eval/mappings; CLI tạo mới bằng exclusive mode, không ghi đè artifact đã đóng.

Đã đối chiếu bản render thật cả hai trang `nghiem_thu_dich_vu.pdf`, gồm điều kiện C1 cuối trang 1 và BM-09 cuối trang 2; render tạm nằm trong cache bỏ qua Git. Kiểm tra tự động thêm body paragraph/line positions, dấu tiếng Việt, raw CRLF/NFD, tables/heading provenance và round-trip từng source span. Đây là xác minh extraction, không phải human relevance/answer quality mới.

## Lệnh và kết quả thực

Từ backend/, PostgreSQL test phải được kiểm tra bằng guard hiện có; Docker db đang healthy:

```powershell
# Chọn tên mới mỗi lượt; pytest có thể xóa basetemp nếu đã tồn tại.
# Giữ đường dẫn ngắn và bên trong workspace trên Windows.
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider --basetemp .cache\b-<new-id>
```

Từ repo root:

```powershell
.\backend\.venv\Scripts\python.exe -B -m pytest eval/tests -q -p no:cacheprovider
.\backend\.venv\Scripts\ruff.exe check --config backend/pyproject.toml backend/app backend/tests backend/alembic eval
.\backend\.venv\Scripts\ruff.exe format --check --config backend/pyproject.toml backend/app backend/tests backend/alembic eval
.\backend\.venv\Scripts\python.exe -B -m pip check
# Chỉ tạo đường dẫn output mới trong đợt được xác nhận; không ghi đè mapping đã đóng.
.\backend\.venv\Scripts\python.exe -B -m eval.parser_mapping --output eval/mappings/<new-version>.json
```

**166 backend tests passed, 1 warning; 76 eval tests passed** trong hai invocations riêng. Ruff check/format (75 files) và pip check đạt. Warning Starlette TestClient/httpx giữ nguyên từ baseline. Test cases gồm concurrent real PostgreSQL transactions (một 202/một 409, một doc/revision/job/file), scope, multipart không Content-Length, flush/commit rollback, lost commit acknowledgement, interruption, formats/error fixtures/resource limits, tables/token budget và mapping tái lập đúng artifact.

Probe sau tests: dev head 20261103_rag04/2 users/0 documents/0 revisions; test cùng head/0 users/0 documents/0 revisions. Old migration SHA-256 vẫn e504de8252dc856e8bf3e935da4fdcd78ab8e45468d604931da6526dc60ba868. Scan 122 source/docs/eval/config files không chứa các API key/demo passwords thực từ .env; không in secrets. Không có tài liệu upload thử bị để lại trong DB dev/test.

Các lượt test đầu đã gặp Temp ACL Windows và MAX_PATH; dùng basetemp ngắn trong workspace và UUID key ngắn để khắc phục. Full suite cũng bắt lỗi fixture chia sẻ qua plugin hoạt động khác khi collect cả thư mục: đã chuyển fixture people vào conftest, không dùng skip để che. Chỉ ghi kết quả pass sau lượt chạy đầy đủ cuối. Không chạy lại frontend build vì đợt này không sửa frontend/UI.

**Tiếp theo:** đề xuất riêng Bước 06 (worker/lease/generation/embedding/Qdrant/publish/recovery), chờ xác nhận. Trước khi code UI sẽ nhắc và trình bày phạm vi theo quy tắc đã lưu trong AGENTS.md/CLAUDE.md.
