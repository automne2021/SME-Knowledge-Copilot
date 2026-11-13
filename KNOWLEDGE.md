# KNOWLEDGE — Kiến thức và lý do quyết định

> **Khởi tạo:** 02/11/2026  
> **Project:** SME Knowledge Copilot — RAG thuần  
> **Mục đích:** giải thích kiến thức chuyên ngành phát sinh khi thiết kế, code, chọn giải pháp, sửa lỗi và đánh giá; giúp thành viên hiểu, tự triển khai và trình bày được quyết định của mình.

## 1. Cách sử dụng tài liệu

[Spec RAG](SME_Knowledge_Copilot_RAG_Specification.md) mô tả hệ thống phải làm gì. [PLAN.md](PLAN.md) mô tả làm theo thứ tự nào. **KNOWLEDGE.md giải thích cách hoạt động, vì sao làm như vậy, phương án khác và bằng chứng cho quyết định.**

Mỗi đợt công việc cập nhật tài liệu này cùng thay đổi liên quan. Bao gồm cả quyết định giữ nguyên giải pháp sau khi đã so sánh, bài học từ lỗi và thí nghiệm cho kết quả không cải thiện. Giải thích bằng tiếng Việt, mở nghĩa thuật ngữ mới và dùng ví dụ của project khi hữu ích.

**Điều kiện thực hiện:** mọi thay đổi, kể cả cập nhật tài liệu này, phải nằm trong phạm vi đã trình bày và được người dùng xác nhận bằng câu **“Thực hiện đi”**. Quy tắc chi tiết ở [AGENTS.md](AGENTS.md). Được đọc/phân tích để chuẩn bị đề xuất; không tự ghi kiến thức hoặc thực thi bước PLAN kế tiếp khi chưa được xác nhận.

| Loại ghi nhận | Ý nghĩa |
|---|---|
| Đề xuất / giả thuyết | Cần thử; chưa có bằng chứng để kết luận phù hợp nhất |
| Quyết định thiết kế | Đã chọn trong spec/plan; chưa đồng nghĩa đã code hoặc chạy đúng |
| Đã triển khai | Có code/artifact cụ thể; ghi rõ phần kiểm tra đã/chưa chạy |
| Đã kiểm chứng | Có test/benchmark/quan sát với điều kiện, thời điểm và kết quả cụ thể |
| Đã thay thế | Giữ lý do cũ và liên kết quyết định mới; không xóa lịch sử để làm như chưa từng chọn |

Không biến một lần test pass thành kết luận tổng quát về mọi dữ liệu. Khi thông tin model/API thay đổi theo thời gian, xác minh tài liệu chính thức và ghi ngày kiểm tra. Không lưu API key, dữ liệu riêng tư, toàn bộ hội thoại hay suy luận nội bộ của model vào đây.

### Mẫu cho mục mới

```markdown
### K-xxx — Tên vấn đề hoặc quyết định

- Ngày / loại ghi nhận:
- Liên quan: bước PLAN, mục spec, file/commit hoặc mục kiến thức cũ.
- Bối cảnh và vấn đề cần giải quyết:
- Kiến thức cần hiểu: khái niệm, cơ chế, ví dụ.
- Lựa chọn / thay đổi và lý do:
- Phương án khác và vì sao chưa chọn:
- Đánh đổi / giới hạn:
- Cách kiểm chứng và kết quả thật: command, môi trường, artifact; chưa chạy ghi rõ.
- Điều kiện xem xét lại:
- Nguồn tham khảo:
```

Với sửa lỗi, bổ sung biểu hiện → nguyên nhân → cách sửa → kiểm tra chống tái diễn. Với thí nghiệm model, bổ sung dataset/config/model revision, tài nguyên, latency, chất lượng và chi phí. Thay đổi nhỏ có thể bổ sung vài dòng vào mục hiện có; các trường trên là nội dung cần cân nhắc, không bắt buộc tạo một bài dài cho mỗi dòng code.

## 2. Bản đồ kiến thức ban đầu

Các mục K-001–K-009 dưới đây tổng hợp **thiết kế/đề xuất đã có trong spec và plan**, không phải bằng chứng pipeline RAG đã triển khai. Thông tin máy được khảo sát ngày 01/11/2026; không đo lại phần cứng trong lần khởi tạo tài liệu này. K-010 ghi việc thiết lập quy trình tài liệu ngày 02/11/2026.

| ID | Chủ đề | Liên quan |
|---|---|---|
| K-001 | RAG pipeline và ranh giới với agent/fine-tuning | Spec 1, 3, 12.3; PLAN 1 |
| K-002 | Embedding, LLM và lựa chọn CPU + hosted | Spec 12; PLAN 3–4 |
| K-003 | Chunking, tokenizer và nguồn trích dẫn | Spec 7.1, 7.3; PLAN bước 05 |
| K-004 | PostgreSQL + Qdrant và consistency | Spec 6.2, 9; PLAN bước 04, 06–07 |
| K-005 | Worker, lease, generation và idempotency | Spec 7.4; PLAN bước 06, 09 |
| K-006 | Schema validation và citation grounding | Spec 8.6–8.7; PLAN bước 08 |
| K-007 | Retrieval metrics, gold context và đánh giá | Spec 14; PLAN bước 02, 07, 11 |
| K-008 | Phân quyền backend và xóa nguồn | Spec 2.5, 7.5; PLAN bước 04, 09 |
| K-009 | Baseline, trade-off và thí nghiệm có kiểm soát | Spec 14.5; PLAN 4, 9 |
| K-010 | Ghi kiến thức cùng thay đổi | Yêu cầu người dùng 02/11/2026 |
| K-011 | Xác nhận trước mọi thay đổi workspace | Yêu cầu người dùng 02/11/2026 |
| K-012 | Audit chuyển hướng và phân biệt thiết kế với code đang có | PLAN bước 00; docs/rag-transition-audit.md |
| K-013 | Virtualenv không di chuyển nguyên trạng và baseline môi trường | PLAN bước 00–01; Python venv docs |
| K-014 | Mapping schema, API contract và giới hạn của tests legacy | Spec 7–10, 15; audit Bước 00 |
| K-015 | Guard DB test trước mọi kết nối/migration và SQL identifier | tests/database_safety.py; tests/conftest.py |
| K-016 | Unit tests độc lập với app dependencies và giới hạn chứng cứ | tests/test_database_safety.py; audit mục 7 |
| K-017 | Khôi phục venv và cache theo tài nguyên máy | PLAN bước 01; environment-step01.md |
| K-018 | Runtime/dev locks và frontend reproducibility | requirements-dev.lock; package-lock.json |
| K-019 | Image digests, readiness và persistent volumes | compose.yaml; scripts/check_infra.py |
| K-020 | Config host/container, secret và ngân sách free tier | core/config.py; .env.example; yêu cầu 0 USD |
| K-021 | Đọc đúng kết quả baseline và xử lý khác biệt tooling | 64 tests; frontend build; Ruff; environment report |
| K-022 | Dữ liệu giả lập, nhãn nháp và kiểm tra chéo của con người | PLAN bước 02; eval/datasets/README.md |
| K-023 | Gold spans theo nguồn, Unicode và không rò rỉ dev/test | source_blocks.json; validate_dataset.py |
| K-024 | Fixtures thật và reproducibility của PDF/DOCX | build_dataset.py; corpus_manifest.json; dev lock |
| K-025 | Kiểm thử metric khác đánh giá model và nghiệm thu pipeline | metrics.py; eval/tests; dataset-step02.md |
| K-026 | Báo tiến độ theo khối lượng có bằng chứng | Yêu cầu người dùng; PLAN quy ước tiến độ |
| K-027 | Phát hành nhãn đã duyệt và khóa review ledger | publish_reviewed.py; reviewed-v1 |
| K-028 | Windows ACL, Git line endings và file khóa Word | Publisher; .gitattributes; .gitignore |
| K-029 | Môi trường embedding CPU tối giản và pin model/runtime | requirements-ai-cpu.lock; model_smoke.json |
| K-030 | Prefix/pooling/token budget và số đo smoke thật | embedding_runtime.py; smoke_embedding_20261103_01 |
| K-031 | Native Gemini, schema/citation-ID và free-tier preflight | gemini_smoke.py; hướng dẫn key |
| K-032 | Tiến độ sau review và phân biệt software/model evidence | Bước 02 xong; Bước 03 mới 2/6 |
| K-033 | Có API key khác với đã xác minh free tier/quota | Preflight lần 2; vị trí kiểm tra AI Studio |
| K-034 | Bằng chứng tài khoản và smoke Gemini thật đầu tiên | User screenshots; run đầu 4/5 hợp lệ |
| K-035 | Lỗi validator, diagnostics an toàn và retest một case | Prompt v2; run retest 1/1; 72 eval tests |
| K-036 | Đóng gate model smoke khác với benchmark chất lượng | PLAN v1.6; tiến độ 17,1% |
| K-037 | Migration chuyển tiếp giữ legacy và review autogenerate | 20261103_rag04; populated migration tests |
| K-038 | Partial unique/composite FK và giới hạn schema guarantees | knowledge.py; PostgreSQL constraints tests |
| K-039 | Argon2id, opaque bearer và token digest | security.py; auth_tokens; ADR RAG-06 |
| K-040 | Workspace/owner scope và error envelope nhất quán | access.py; resources.py; frontend client |
| K-041 | Seed idempotent, secrets riêng và DB transaction boundaries | app.seed; .env; dev probe |
| K-042 | Bằng chứng Bước 04 và tiến độ 24,9% | 124 backend + 72 eval; schema-identity-step04.md |

## 3. Các giải thích nền tảng

### K-001 — Chọn pipeline RAG cố định cho bài toán hỏi tài liệu

**Ngày / loại:** 02/11/2026 — tổng hợp quyết định thiết kế từ spec; chưa xác nhận triển khai.

**Kiến thức:** RAG (*Retrieval-Augmented Generation*) kết hợp truy xuất bằng chứng với sinh câu trả lời. Luồng của project là câu hỏi → tìm đoạn tài liệu → chọn context → LLM tổng hợp → kiểm tra output/citation. Vector search tìm ứng viên; LLM diễn đạt câu trả lời. Hai bước có thể sai theo những cách khác nhau.

**Vì sao chọn:** bài toán hiện tại có thứ tự xử lý rõ và không cần model tự quyết định công cụ nghiệp vụ. Pipeline cố định giúp trace được nguồn, latency và điểm lỗi; phù hợp mục tiêu học retrieval/citation trên quy mô nhóm hai người.

**Phương án khác:** agent hữu ích khi phải lựa chọn tools hoặc phối hợp nhiều hành động không cố định, nhưng chưa có yêu cầu đó trong RAG MVP. Fine-tuning có thể phục vụ hành vi/định dạng hoặc domain adaptation, nhưng không tự cung cấp cơ chế cập nhật/xóa tài liệu và mở nguồn cho mỗi câu trả lời. Hiện chưa có dataset hay kết quả baseline để chứng minh cần fine-tune. Đây là lý do hoãn trong project, không phải kết luận các kỹ thuật đó luôn kém hơn RAG.

**Đánh đổi:** pipeline ít linh hoạt hơn với yêu cầu mới ngoài hỏi đáp. RAG vẫn có thể retrieve sai hoặc LLM suy diễn; có retrieval chưa chứng minh answer đúng.

**Kiểm chứng / xem lại:** chưa có benchmark trong mục này. Dùng trace và eval tách retrieval/generation; chỉ xem lại agent khi xuất hiện workflow cần tool selection thực sự. Liên quan: spec 3, 12.3; PLAN bước 07–08.

### K-002 — Phân biệt embedding với LLM và chọn cấu hình phù hợp máy

**Ngày / loại:** 02/11/2026 — đề xuất thí nghiệm từ PLAN, chưa chạy model benchmark.

**Kiến thức:** embedding biến text thành vector dùng để tìm nội dung gần nghĩa; generation model nhận câu hỏi/context rồi sinh text. Chọn hai loại model là hai quyết định riêng. *Vector dimension* là số thành phần của một embedding; *context window* là lượng tokens model có thể xử lý trong một lần. Chúng không thay thế nhau.

**Lựa chọn khởi đầu:** PLAN đề xuất thử `intfloat/multilingual-e5-small` trên CPU và LLM hosted; BGE-M3 là embedding challenger. Bối cảnh là máy khoảng 16 GB RAM, i7-1165G7, Iris Xe theo khảo sát đã ghi trong PLAN. Đây là giả thuyết về tính khả thi cần đo, chưa phải kết luận model thắng.

**Vì sao chưa ưu tiên local LLM lớn:** hệ điều hành, IDE, Docker và embedding cùng dùng tài nguyên; weights chỉ là một phần bộ nhớ inference. Còn có runtime, buffers và KV cache — bộ nhớ giữ thông tin attention để hỗ trợ sinh token tiếp theo. Context dài và nhiều request đồng thời cũng ảnh hưởng bộ nhớ. Hosted giúp giảm phần inference generation trên máy nhưng đổi lại cần mạng, quota, chi phí và điều kiện dữ liệu phù hợp.

**Phương án khác:** thử local LLM nhỏ/quantized sau khi baseline chạy; thử BGE nếu retrieval dev chưa phù hợp và đủ tài nguyên. Không chọn model chỉ theo số tham số hoặc bảng xếp hạng không cùng domain/dataset. Không mặc định CPU embedding của máy hiện tại chắc chắn đủ nhanh.

**Kiểm chứng / xem lại:** đo query embedding latency, throughput ingestion, peak RAM, correctness/citation, token usage và lỗi. Model/prefix/tokenizer/dimension phải khớp index; đổi embedding cần reindex. Model IDs, thông số và shortlist cụ thể nằm ở PLAN 4, được kiểm tra lại trước dùng; mục này không cập nhật hay xác nhận availability/giá API.

### K-003 — Chunking phải giữ được ý nghĩa và provenance

**Ngày / loại:** 02/11/2026 — quyết định thiết kế; tham số chunk còn là giả thuyết.

**Kiến thức:** chunking chia tài liệu thành các đoạn có thể embed/retrieve. *Token* là đơn vị tokenizer xử lý, không đồng nhất với từ hoặc ký tự. *Overlap* lặp một phần nội dung giữa các chunk để giảm mất ngữ cảnh ở ranh giới; đồng thời tăng số vector và có thể tạo kết quả trùng. *Provenance* là thông tin giúp truy ngược nội dung về nguồn cụ thể.

**Vì sao chọn tách theo cấu trúc rồi giới hạn token:** điều khoản chính sách thường gồm điều kiện, ngoại lệ và mức áp dụng. Ví dụ “giảm tối đa 5%” và “trừ khi có phê duyệt” bị tách rời có thể làm câu trả lời thiếu điều kiện. Page/block/line và source spans cho phép kiểm tra parser, citation và gold evidence.

**Phương án khác:** fixed character splitting dễ làm nhưng không trực tiếp bảo đảm token budget; đưa nguyên tài liệu vào model dễ vượt giới hạn hoặc gây nhiễu; semantic chunking cần thêm thiết kế/chi phí và chưa có baseline chứng minh lợi ích ở corpus này. Không có một chunk size tối ưu chung cho mọi model/tài liệu.

**Đánh đổi:** giữ heading/table provenance làm parser/chunker phức tạp hơn. Chunk lớn có thêm ngữ cảnh nhưng giảm độ cụ thể; chunk nhỏ dễ mất điều kiện. DOCX block không được giả thành số trang PDF.

**Kiểm chứng / xem lại:** mở nguồn so quote/span; assert token limit có tính prefix/heading/special tokens; đo All-evidence và lỗi điều kiện trên dev. Chưa có số đo ở đây. Liên quan: spec 7.3; PLAN bước 05, 07.

### K-004 — Tách metadata nghiệp vụ khỏi vector index

**Ngày / loại:** 02/11/2026 — thiết kế baseline từ spec, chưa xác nhận triển khai storage mới.

**Kiến thức:** PostgreSQL giữ documents, trạng thái, quyền, revision và lịch sử. Qdrant giữ vector index để tìm candidates. *Source of truth* là nơi quyết định dữ liệu nào hiện hợp lệ. Trong project, đó là DB quan hệ cho lifecycle/quyền; vector payload có thể chậm cập nhật so với DB.

**Lựa chọn:** giữ PostgreSQL + Qdrant của spec RAG. Retrieval filter theo workspace/active generation rồi đọc lại text/metadata và xác minh trạng thái trong SQL. Qdrant có điều kiện lọc payload/point ID; quy tắc kiểm tra lại quyền/lifecycle là thiết kế riêng của ứng dụng. [Qdrant Filtering](https://qdrant.tech/documentation/search/filtering/).

**Vì sao chọn:** giữ rõ hai trách nhiệm, có đường nghiên cứu retrieval và không ép chat/job lifecycle vào vector payload. Vector hit không tự chứng minh nguồn còn được phép đọc.

**Phương án khác:** PostgreSQL + pgvector là lựa chọn đáng cân nhắc để giảm số thành phần. Chưa đổi vì spec RAG đang chọn Qdrant và mục tiêu học retrieval có chủ đích. Không khẳng định Qdrant nhanh hơn pgvector ở corpus này khi chưa benchmark; nếu chi phí vận hành vượt lợi ích thì sửa ADR/spec trước chuyển.

**Đánh đổi / kiểm chứng:** hai storage không cùng một transaction PostgreSQL; cần staging/publish và cleanup khi partial failure. Chưa có kết quả thử trong mục này. Phải test upsert xong nhưng DB commit lỗi, vector stale và xóa nguồn trước physical cleanup. Liên quan: spec 6.2, 7.5, 9; PLAN bước 06–09.

### K-005 — Worker retry được cần lease và generation

**Ngày / loại:** 02/11/2026 — quyết định thiết kế, cần fault/concurrency tests.

**Kiến thức:** job ingestion có thể lâu hơn request HTTP và process có thể chết. *Lease* là quyền xử lý tạm thời có hạn; heartbeat gia hạn khi worker còn sống. *Idempotency* nghĩa là lặp thao tác với cùng định danh không tạo thêm hiệu ứng ngoài chủ ý. Nó không đồng nghĩa job chỉ được chạy đúng một lần.

**Lựa chọn:** worker riêng claim job trong transaction ngắn, inference ngoài transaction. `SKIP LOCKED` bỏ qua row đang bị khóa, phù hợp giảm tranh chấp giữa consumers của bảng dạng queue; nó không tự tạo cơ chế retry/lease cho ứng dụng. [PostgreSQL SELECT — locking](https://www.postgresql.org/docs/current/sql-select.html).

**Ví dụ race:** worker A hết lease nhưng vẫn embed; worker B claim và hoàn thành attempt mới. Nếu hai worker ghi chung namespace, A có thể ghi đè kết quả B. Generation riêng cô lập mỗi attempt; chỉ worker còn lease hợp lệ được publish generation active. Lặp upsert trong cùng attempt dùng cùng point IDs.

**Phương án khác:** chạy ingestion ngay trong request đơn giản hơn nhưng gắn tác vụ dài với vòng đời request; in-process background task chưa giải quyết durable recovery. Queue ngoài như Redis/Celery có thể hữu ích khi cần nhiều routing/throughput nhưng tăng thành phần vận hành trong M1. DB queue vẫn phải tự làm timeout/retry/observability đúng.

**Đánh đổi / kiểm chứng:** generation bỏ dở cần cleanup; không được tuyên bố exactly-once. Chưa chạy test ở đây. Cần kill worker, lease expiry, stale-worker publish và rollback sau upsert với barrier kiểm soát. Liên quan: spec 7.4; PLAN bước 06, 09.

### K-006 — Schema đúng và citation hợp lệ chưa bảo đảm answer đúng

**Ngày / loại:** 02/11/2026 — quyết định thiết kế; chưa có kết quả chất lượng model.

**Kiến thức:** *schema validation* kiểm tra cấu trúc/kiểu/ràng buộc; *citation integrity* kiểm tra tham chiếu nguồn; *faithfulness* xem các phát biểu có được context hỗ trợ về nghĩa hay không. Ba lớp kiểm tra khác nhau.

**Lựa chọn:** LLM trả claims + evidence IDs do backend cấp, Pydantic validate và backend kiểm tra IDs thuộc final context đã gửi. `extra='forbid'` từ chối field ngoài schema thay vì mặc định bỏ qua extra data; vẫn cần validators nghiệp vụ riêng. [Pydantic Models — extra data](https://docs.pydantic.dev/latest/concepts/models/).

**Ví dụ:** E1 là nguồn có thật nhưng chỉ nói “tối đa 5%”; model viết “được giảm 10% [E1]”. Schema và ID có thể hợp lệ trong khi claim sai. Vì vậy không trình bày `grounded` như chứng nhận độ đúng tuyệt đối.

**Phương án khác:** free-text answer rồi regex citation đơn giản hơn nhưng khó kiểm tra claim/reference có cấu trúc. Để model tự trả filename/page/URL làm nguồn tạo thêm dữ liệu cần xác minh. Chỉ nhắc “đừng bịa” trong prompt chưa thay thế backend validation/human eval.

**Đánh đổi / kiểm chứng:** structured output có thể bị truncate hoặc sai schema; repair có latency/cost nên giới hạn một lần. Không xóa E99 rồi giữ nguyên câu kết luận. Cần tests cho bad JSON, reference ngoài context và human review entailment; chưa chạy ở đây. Liên quan: spec 8.6–8.7; PLAN bước 08, 11.

### K-007 — Tách lỗi retrieval khỏi lỗi generation

**Ngày / loại:** 02/11/2026 — phương pháp đánh giá của spec/plan; chưa có số đo.

**Kiến thức:** gold evidence là bằng chứng được người gán nhãn xác minh. Hit@K hỏi “có ít nhất một evidence group đúng trong K kết quả không?”. Recall@K hỏi “lấy được bao nhiêu group bắt buộc?”. Với hai điều kiện bắt buộc mà chỉ tìm thấy một, Hit@K = 1 nhưng Recall@K = 1/2; All-evidence = 0. Cách group/match spans phải cố định trước đo.

**Lựa chọn:** đánh giá retrieval trước, rồi generation với final context. Thêm *oracle-context evaluation*: cấp gold context trong eval để xem model có trả đúng khi bằng chứng đầu vào đã đúng hay không. Đây là công cụ chẩn đoán, không phải đường chạy sản phẩm.

**Vì sao chọn:** nếu parser bỏ mất ngoại lệ, nâng LLM không khôi phục được text bị mất. Nếu retrieved context đã đủ nhưng model diễn giải sai thì cần sửa prompt/model, không chỉ tăng Top-K. Oracle không lỗi cũng chưa chứng minh retrieval thực tế tốt.

**Phương án khác:** chỉ chấm answer cuối dễ làm nhưng khó biết sửa tầng nào; dùng LLM judge hoàn toàn giảm công chấm nhưng judge có thể sai. M1 dùng human rubric, tự động hóa chỉ bổ sung khi có kiểm chứng.

**Đánh đổi / kiểm chứng:** annotation tốn thời gian và tập nhỏ có bất định. Dev dùng chọn cấu hình, test giữ lại để đo sau freeze; không tune trên test rồi gọi là holdout. Báo technical error rate, sample counts và denominator bằng 0 là null. Chưa có report model thật trong mục này. Liên quan: spec 14; PLAN bước 02, 07, 11.

### K-008 — Quyền truy cập và xóa nguồn phải được thực thi ở backend

**Ngày / loại:** 02/11/2026 — quyết định thiết kế; chưa có integration test chứng minh.

**Kiến thức:** frontend là nơi hiển thị; API có thể được gọi trực tiếp nên ẩn nút không tạo authorization. Tương tự, xóa một vector chưa chứng minh text biến mất khỏi source endpoint, history, cache hoặc worker còn chạy.

**Lựa chọn:** identity/scope từ backend; DB đánh dấu document deleting để chặn request mới trước khi cleanup vector/file. Mở nguồn và đọc/replay answer đều kiểm tra quyền/lifecycle hiện tại. Khi nguồn của answer bị xóa, áp dụng chính sách che/xóa answer/snapshot liên quan của spec.

**Vì sao chưa chỉ delete Qdrant:** vector store có thể lỗi, cleanup có thể làm một phần và stale worker có thể ghi lại orphan points. Chặn nguồn theo SQL/active generation giúp giữ bất biến trong khi retry cleanup.

**Phương án khác / đánh đổi:** giữ snapshot vĩnh viễn tiện audit nhưng xung đột chính sách xóa nội dung của MVP; hard-delete mọi thứ ngay trong request làm khó recovery và có thể treo khi một storage down. Soft-disable tạo nhu cầu tombstone/sweeper và không thu hồi bytes đã gửi browser/provider trước đó.

**Kiểm chứng / xem lại:** test khác workspace/session, source 410, delete lúc query/worker chạy, đọc chat cũ và cached replay. Thay đổi retention/audit cần cập nhật spec, không tự quyết tại UI. Liên quan: spec 2.5, 7.5; PLAN bước 04, 09–10.

### K-009 — Có baseline trước tối ưu và so sánh đúng biến

**Ngày / loại:** 02/11/2026 — quy trình thí nghiệm đề xuất; chưa có treatment đã đo.

**Kiến thức:** baseline là cấu hình tham chiếu để đánh giá thay đổi. *Confounding* xảy ra khi đổi nhiều yếu tố cùng lúc nên khó biết yếu tố nào gây khác biệt. *Trade-off* là lợi ích ở một mặt đi kèm chi phí/giới hạn ở mặt khác.

**Lựa chọn:** dense-only trước; chỉ thêm hybrid/reranker khi phân tích lỗi đưa ra giả thuyết. Giữ corpus/split/model/prompt/budget ổn định khi có thể và ghi rõ biến nào đổi.

**Ví dụ:** đổi embedding đồng thời tăng chunk size và Top-K là thử cả pipeline mới; chưa thể nói riêng embedding gây cải thiện. Reranker có thể sắp xếp lại candidates nhưng không tạo evidence chưa được retrieve. Tăng K có thể tăng coverage và cũng làm context dài/nhiễu hơn; cần đo cùng budget.

**Phương án khác:** thêm ngay mọi kỹ thuật giúp demo trông nhiều thành phần nhưng làm khó giải thích lợi ích từng phần. Chọn model lớn nhất cũng chưa giải quyết bottleneck nguồn/annotation/permissions. Hoãn một kỹ thuật chưa phải bác bỏ nó.

**Đánh đổi / kiểm chứng:** controlled experiments cần thêm runs và ghi cấu hình. So quality cùng latency, peak RAM, error rate và chi phí; giữ kết quả không cải thiện. Chưa có benchmark chứng minh hybrid/reranker thắng ở corpus này. Liên quan: spec 14.5; PLAN 4, 9.

### K-010 — Ghi kiến thức trong repository cùng thay đổi

**Ngày / loại:** 02/11/2026 — đã thiết lập bằng tài liệu; chưa có thay đổi runtime.

**Bối cảnh:** người dùng yêu cầu mọi công việc code/thiết kế/lựa chọn phải có kiến thức, lý do chọn và lý do chưa chọn phương án khác trong một file KNOWLEDGE.md.

**Lựa chọn:** tạo tài liệu này với mã K-xxx để tham chiếu ổn định, mẫu ghi và các mục nền tảng; thêm rule ở AGENTS.md và liên kết ở CLAUDE.md. Các phiên sau đọc hướng dẫn workspace có thể tiếp tục cùng quy trình.

**Vì sao chọn:** giải thích đi cùng code/spec/plan giúp review, học và chuẩn bị phỏng vấn. Nội dung ghi quyết định quan sát được và lập luận kỹ thuật có thể kiểm tra; không yêu cầu sao chép hội thoại hay suy luận nội bộ của model.

**Phương án khác:** chỉ nói trong chat khó tra lại cùng repository; chỉ có ADR thường chưa bao quát bug diagnosis, model experiments và thuật ngữ mới. ADR/spec/eval report vẫn giữ vai trò của chúng, KNOWLEDGE liên kết thay vì chép lại tất cả.

**Đánh đổi:** thêm công việc bảo trì và nguy cơ lặp/outdated. Mỗi đợt sửa bổ sung vào mục liên quan; quyết định mới giữ dấu vết mục cũ và ngày áp dụng. Không gọi bản thân file hướng dẫn là cơ chế kỹ thuật bảo đảm mọi công cụ luôn tuân thủ.

**Kiểm chứng:** kiểm tra tồn tại file, liên kết nội bộ, cấu trúc Markdown và diff trong lần khởi tạo; không chạy app/model vì chỉ thay đổi tài liệu. Trạng thái đã kiểm tra được báo khi kết thúc công việc.

### K-011 — Xác nhận theo phạm vi trước khi thực hiện thay đổi

**Ngày / loại:** 02/11/2026 — thiết lập quy tắc làm việc bằng tài liệu, theo xác nhận “Thực hiện đi” của người dùng cho việc cập nhật AGENTS.md, CLAUDE.md và KNOWLEDGE.md.

**Bối cảnh và kiến thức:** quyền thực hiện một thay đổi gắn với phạm vi cụ thể đã trình bày. Yêu cầu phân tích/kế hoạch chưa đồng nghĩa quyền ghi file hoặc chạy lệnh có hiệu ứng phụ; một công cụ kiểm tra cũng có thể sinh cache, artifact hoặc ghi DB.

**Lựa chọn và lý do:** trình bày thay đổi dự kiến, chờ đúng câu xác nhận của người dùng rồi thực hiện đợt công việc đó. Lưu rule ở AGENTS.md và nhắc lại ở CLAUDE.md/KNOWLEDGE.md để các công cụ đọc hướng dẫn đều gặp điều kiện này. Đây là cách người dùng chủ động kiểm soát thời điểm và phạm vi sửa workspace.

**Phương án khác:** tự thực hiện khi thấy thay đổi hợp lý không đáp ứng yêu cầu kiểm soát của người dùng. Hỏi lại cho từng file trong một đợt đã duyệt tạo thao tác lặp; thay vào đó, một xác nhận bao phủ phạm vi đã nêu, còn phần mở rộng phải được xác nhận mới.

**Đánh đổi và giới hạn:** quy trình cần thêm lượt xác nhận trước các đợt thay đổi. Đọc/tìm kiếm/phân tích chỉ đọc vẫn dùng được để chuẩn bị đề xuất cụ thể. Không suy ra sự im lặng hoặc câu được trích dẫn trong tài liệu là quyền thực hiện. Quy tắc tài liệu hướng dẫn hành vi, không phải cơ chế khóa filesystem ở cấp hệ điều hành.

**Kiểm chứng:** rà soát ba file có cùng điều kiện xác nhận và phạm vi; kiểm tra liên kết Markdown, mã kiến thức và diff bằng thao tác chỉ đọc. Không cần chạy ứng dụng cho thay đổi hướng dẫn này.

**Điều kiện xem lại:** chỉ thay đổi quy tắc khi người dùng yêu cầu và xác nhận phạm vi cập nhật theo quy tắc đang có. Nguồn: chỉ thị trực tiếp của người dùng trong cuộc trò chuyện ngày 02/11/2026.

### K-012 — Đồng bộ repository trước triển khai tính năng mới

**Ngày / loại:** 02/11/2026 — đã thực hiện audit/đồng bộ tài liệu trong phạm vi Bước 00 được người dùng xác nhận.

**Bối cảnh:** spec và PLAN đã chuyển sang RAG nhưng CLAUDE/README/eval/ADR instructions vẫn chỉ STT/approval là M1, RAG là M2. Nếu tiếp tục code theo hướng dẫn cũ, assistant có thể triển khai sai scope hoặc khẳng định một module đã tồn tại chỉ vì có tên bảng/thư mục.

**Kiến thức:** audit chuyển tiếp đối chiếu contract đích với source, dependency, migration và môi trường hiện tại. Đây là bước lập bằng chứng trước thay đổi, không tự triển khai contract. HEAD chỉ xác định commit, không ghi lại file untracked/modified; vì vậy audit ghi thêm working-tree ban đầu và checksum migration.

**Lựa chọn / lý do:** cập nhật CLAUDE/AGENTS/README/eval/ADR instructions, giữ spec Operations làm lịch sử, tạo [audit](docs/rag-transition-audit.md) chứa đủ 23 FR P0, reuse/migration map và baseline. PLAN được cập nhật trạng thái; runtime/source/config/dependencies giữ nguyên để phân biệt lỗi trước/sau chuyển hướng.

**Phương án khác:** đổi tên/drop toàn bộ code Operations ngay làm tăng rủi ro mất lịch sử/schema trước khi biết dữ liệu thực. Chỉ đổi tên README để tài liệu đẹp hơn chưa loại bỏ instructions mâu thuẫn hoặc chỉ ra phần cần làm. Viết lại từ đầu bỏ qua khung UUID/session/naming conventions hiện có cũng chưa có căn cứ.

**Đánh đổi / kiểm chứng:** code còn title/navigation/schema cũ, README phải nói rõ. Đọc source chứng minh chỉ có health router, model users có password_hash chưa thành login feature, các domain folders còn skeleton. Bước này không tạo commit/tag; HEAD ghi trong audit là tham chiếu, không phải backup của mọi thay đổi chưa commit. Kiểm tra tài liệu/liên kết/FR coverage và migration checksum được thực hiện cuối đợt; runtime tests có giới hạn ở K-013.

**Điều kiện xem lại:** mỗi bước code tiếp theo cập nhật trạng thái tài liệu theo bằng chứng mới. Không giữ nhãn “chưa triển khai” sau khi có feature/test, nhưng cũng không biến một thiết kế trong spec thành claim đã chạy.

### K-013 — Vì sao virtualenv có thư mục nhưng Python vẫn không chạy

**Ngày / loại:** 02/11/2026 — đã quan sát lỗi môi trường; chưa sửa/cài môi trường ở Bước 00.

**Biểu hiện / nguyên nhân:** backend/.venv/Scripts/python.exe tồn tại nhưng launcher báo không tìm thấy Python base của máy cũ. pyvenv.cfg ghi Python 3.13 tại C:\Users\Username\..., trong khi system Python trên máy này là 3.12.8. System Python có pytest nhưng thiếu FastAPI/SQLAlchemy/Alembic/psycopg/pydantic-settings. Có thư mục venv hoặc một executable tool chạy được chưa chứng minh interpreter/app dependencies hoạt động.

**Kiến thức:** venv chứa liên kết/cấu hình tới interpreter và có thể có scripts dùng đường dẫn tuyệt đối; không nên coi nó là bản đóng gói di chuyển nguyên trạng giữa máy. Cách tái lập là tạo env tại đúng vị trí bằng interpreter được chọn và cài từ dependency manifest/lock. [Python venv — cách hoạt động và tính không portable](https://docs.python.org/3/library/venv.html#how-venvs-work).

**Lựa chọn / lý do:** ở Bước 00 chỉ ghi lỗi và đưa việc khôi phục sang Bước 01. Ruff standalone 0.17.3 trong venv vẫn chạy: lint pass và format check báo 26 files already formatted. Điều đó kiểm chứng static style, không thay thế pytest/import/integration/runtime.

**Phương án khác:** sửa home trong pyvenv.cfg hoặc trộn site-packages Python 3.13 vào interpreter 3.12 có thể để lại launchers/binary dependencies không tương thích. Cài thiếu gì vào system Python thì mất isolation và chưa tái lập đúng manifest. Chưa chọn các cách này.

**Kết quả thật:** pytest wrapper không khởi chạy được interpreter nên 0 tests thực thi, không DB test nào được tạo/migrate. Frontend lint/build exit 1 do thiếu eslint/tsc (không có node_modules), chưa phải kết luận app có lỗi lint/type. Docker Compose ps ngoài sandbox exit 0 không có container project; TCP localhost:5433 ngoài sandbox ConnectionRefusedError. Chi tiết command/môi trường nằm trong audit, không in secrets.

**Điều kiện sửa/kiểm chứng tiếp:** sau xác nhận Bước 01, chuẩn bị đủ disk/cache, tạo env đúng interpreter, cài dependencies/lockfile, khởi động DB, kiểm tra DB test khác DB dev rồi chạy lại baseline. Không gọi lỗi môi trường là regression do sửa Markdown. Khi đó bổ sung kết quả mới, giữ kết quả lịch sử này.

### K-014 — Tái sử dụng schema cần đối chiếu semantics và contract

**Ngày / loại:** 02/11/2026 — đã audit source/migration; mapping là đề xuất cho bước triển khai sau, chưa migrate dữ liệu.

**Kiến thức:** hai bảng cùng tên chưa chắc có cùng ý nghĩa. ProcessingJob cũ có entity_type/entity_id/locked_at và enum processing; RAG cần document/revision/kind/stage/running/retry_wait/lease/generation. Cập nhật model không tự đổi CHECK constraints hoặc backfill các rows cũ. Helper hiện có lưu enum bằng VARCHAR + CHECK, không phải native PostgreSQL ENUM.

**Lựa chọn / lý do:** giữ revision 27b126c3c0bc, lập mapping trước migration mới. Users/workspaces có thể reuse; user roles và username cần migration có review, không tự coi approver là knowledge_admin. Giữ bảng Operations và tests tương ứng cho tới khi có kế hoạch chuyển dữ liệu; không bỏ models khỏi Alembic metadata rồi vô tình tạo DROP TABLE khi autogenerate.

**Ví dụ giới hạn chứng cứ:** tasks.proposal_id có NOT NULL/FK/UNIQUE giúp bắt buộc liên kết và chặn bản sao theo proposal; nó chưa chứng minh proposal đã được duyệt hoặc approval service tồn tại. Cần đọc code thực thi và test đúng hành vi, thay vì tin comment trong model.

**API contract:** backend/errors và frontend API client hiện hiểu lỗi phẳng; spec RAG yêu cầu error envelope lồng. Khi triển khai phải đổi backend, frontend và tests cùng một thay đổi có xác nhận. Đổi một phía có thể làm UI mất error code/message dù server vẫn trả lỗi. Health hiện check DB, khác mục tiêu liveness/readiness tách trong spec; cũng được đưa vào backlog.

**Phương án khác / đánh đổi:** sửa migration cũ để fresh DB trông đúng tạo khác biệt với DB đã áp revision; tự đổi role/state text không xét dữ liệu có thể sai quyền hoặc làm job cũ mất nghĩa. Migration bổ sung tốn bước nhưng cho phép review/backfill/rollback có chủ đích. Chưa có policy chuyển dữ liệu thực được tự áp dụng trong Bước 00.

**Kiểm chứng / kết quả:** đọc migration duy nhất, source enums/models/error/client và đếm 8 tests legacy (2 API, 6 constraints); các tests chưa chạy do K-013, không ánh xạ chúng thành AT-R đã pass. Checksum migration được giữ nguyên. Audit có mapping từng entity/enum và backlog bao phủ FR P0; khi thêm RAG cần PostgreSQL/Qdrant integration, fault/concurrency tests và AT-R01–23 mới.

### K-015 — Fixture ghi DB phải tự chặn cấu hình không an toàn

**Ngày / loại:** 02/11/2026 — đã triển khai guard và kiểm chứng unit cases; đường SQL/PostgreSQL thật chưa chạy. Đợt vá được người dùng xác nhận riêng sau review Bước 00.

**Biểu hiện / nguyên nhân:** fixture cũ đọc TEST_DATABASE_URL rồi tự CREATE DATABASE/migrate mà không so với DATABASE_URL development. Cảnh báo README yêu cầu chọn DB test đúng chưa ngăn cấu hình sai trong code; nếu hai URL cùng đích, migration có thể tác động DB dev. Tên database từng được nội suy thẳng vào DDL string.

**Kiến thức:** *fail closed* là từ chối trước hiệu ứng phụ khi không xác minh được điều kiện an toàn. Validation cần kiểm tra đích hiệu lực, không chỉ tên biến: query parameters có thể được driver dùng làm connection options. SQLAlchemy có đường truyền URL query parameters tới DBAPI, tùy dialect. [SQLAlchemy — connection arguments](https://docs.sqlalchemy.org/en/20/core/engines.html#custom-dbapi-connect-arguments-on-connect-routines).

**Lựa chọn / lý do:** helper [database_safety.py](backend/tests/database_safety.py) dùng stdlib parse/validate cả test và development URL, chỉ chấp nhận driver postgresql+psycopg, có user/host/database, port hợp lệ, không whitespace/query/fragment. Test target chỉ ở localhost/127.0.0.1/::1/Compose db; tên lowercase ASCII `[a-z][a-z0-9_]*_test`, tối đa 63 ký tự, không trùng development name kể cả khác host alias/case. URL connection được dựng lại bằng URL.create với port rõ ràng; không đưa raw query options trở lại driver.

**Thứ tự thực thi:** db_engine validate trước gọi các helper; `_ensure_database` và `_migrate` cũng revalidate ngay khi được gọi riêng. Imports DB/Alembic chỉ diễn ra sau guard tại hai entry points này. Lỗi validation không in URL/password; cấu trúc target không đưa password vào repr.

**Value khác identifier:** placeholder bind dùng được cho giá trị `datname = :name`; tên database trong CREATE DATABASE là identifier, không phải value placeholder. Bản vá dùng psycopg.sql.Identifier để compose DDL trên driver connection và SQLAlchemy exec_driver_sql để thực thi; không ghép input tùy ý vào tên object. [Psycopg — SQL composition](https://www.psycopg.org/psycopg3/docs/api/sql.html).

**Phương án khác:** chỉ so raw URL bỏ sót host alias, case và các dạng encoding; chỉ kiểm tra suffix chưa ngăn nhầm DB dev nếu DB dev cũng có tên kết thúc `_test`. Chỉ dùng regex cho tên chưa giải quyết connection overrides. Allow remote host/query tùy ý tăng trường hợp phải chứng minh an toàn nhưng chưa có yêu cầu ở local demo; chưa hỗ trợ trong đợt này.

**Đánh đổi / giới hạn:** policy nghiêm có thể từ chối URL remote hoặc connection options vốn hợp lệ. Muốn hỗ trợ phải thiết kế/kiểm tra thêm sau xác nhận mới. Alias db giả định là Compose network của nhóm; guard không xác minh DNS, tunnel hoặc DB user privileges. Credential fallback/secret management và quyền DB tối thiểu vẫn cần cấu hình đúng; không coi guard là cơ chế khóa database ở cấp hệ điều hành.

**Kiểm chứng:** bộ 56 cases ở K-016 bao gồm cấu hình cùng DB, remote host, query override, malformed ports, unsafe/reserved/overlong names, encoded credentials và fixture/helper fail trước create/migrate. Chưa có bằng chứng CREATE/migrate thành công với psycopg/SQLAlchemy/PostgreSQL thật; phải bổ sung ở Bước 01. Migration revision cũ không chỉnh sửa, không DB nào được tạo/migrate trong đợt vá.

### K-016 — Chạy unit guard độc lập, không biến nó thành integration pass

**Ngày / loại:** 02/11/2026 — đã chạy unit và static checks bằng công cụ sẵn có; chưa khôi phục môi trường dự án.

**Bối cảnh / kiến thức:** conftest cũ import app/SQLAlchemy/Alembic ngay khi pytest collect, nên unit test logic thuần cũng bị chặn khi máy thiếu app dependencies. Pytest chỉ cần khởi tạo DB fixture khi một test yêu cầu fixture đó; module-level imports khiến phụ thuộc nặng xảy ra sớm hơn nhu cầu. [Pytest — requesting fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#requesting-fixtures).

**Lựa chọn / lý do:** chuyển app/DB imports vào fixture/helper sử dụng chúng; annotations dùng postponed evaluation và TYPE_CHECKING. Guard tách riêng, chỉ phụ thuộc stdlib. System Python có pytest nên có thể chạy riêng tests/test_database_safety.py ngay; full backend suite vẫn cần app dependencies/DB đúng. Không sửa venv/cài package để che lỗi môi trường ngoài phạm vi.

**Phương án khác:** cài mọi dependencies vào Python global làm mất isolation và vượt đợt vá được duyệt; stub toàn app/DB để báo full suite pass sẽ không chứng minh transaction/migration thật. Skip mọi test khi thiếu dependencies làm mất bằng chứng cho logic guard vốn chạy độc lập được. Chỉ stub settings và operation tripwires trong test kiểm tra thứ tự fixture là đủ cho mục tiêu đó.

**Kết quả thật:** từ backend, `python -B -m pytest tests/test_database_safety.py -q -p no:cacheprovider` → **56 passed** trên Python 3.12.8 / pytest 9.0.2. Ruff 0.17.3: `check --no-cache .` pass; `format --check --no-cache .` báo **28 files already formatted**. Lệnh format trước đó chỉ áp dụng 3 file test/helper trong phạm vi vá. Không chạy inference, tạo DB, Alembic upgrade hoặc 8 tests legacy trong lượt unit này.

**Ý nghĩa bằng chứng:** tests gọi validator thật và các entry points với URL không hợp lệ; một fixture test thay settings và create/migrate operations bằng Mock để khẳng định chúng không được gọi. Không có mock SQL execution được trình bày thành real PostgreSQL success. Bộ 56 là số cases sau parametrization, không phải 56 test functions hoặc 56 tình huống RAG.

**Đồng bộ tài liệu / kiểm chứng tiếp:** sửa mô tả CLAUDE còn theo Operations trong spec; giữ baseline Bước 00 cũ và bổ sung hậu kiểm trong audit/PLAN thay vì xóa kết quả bị chặn. README/CLAUDE ghi 8 tests legacy vẫn đúng cho nhóm đó. Sau khi người dùng xác nhận Bước 01, khôi phục env/lockfiles và chạy DB/API integration để kiểm tra happy path SQL/Alembic cùng unit guard. Chất lượng RAG vẫn chưa có số đo.

### K-017 — Venv có thể tái tạo, cache cần chọn theo tài nguyên thật

**Ngày / loại:** 02/11/2026 — đã thực hiện và kiểm chứng trong Bước 01, tiếp nối lỗi K-013. Chi tiết số đo và commands: [environment-step01.md](docs/environment-step01.md).

**Lựa chọn / lý do:** giữ venv hỏng thành backend/.venv.legacy-20261102 rồi tạo backend/.venv bằng Python 3.12.8 đang có. Cách này giữ dấu vết để kiểm tra nếu cần và dùng interpreter phù hợp Docker scaffold Python 3.12, thay vì sửa home của venv Python 3.13 máy cũ. App packages được cài trong venv, không vào Python global; kiểm tra sys.prefix khác sys.base_prefix và pip check đạt.

**Kiến thức về cache:** cache là bản tải có thể dùng lại, không phải model đã load vào RAM. Chọn D:\AI-Cache\sme-copilot cho pip/npm/HF/tmp vì lúc đầu C chỉ ~8,18 GiB, D ~80,04 GiB. Repo/venv vẫn ở C, Docker giữ data location riêng; thay HF_HOME không chuyển các thành phần đó. .env không tự export biến cho pip/npm hoặc mọi child process, nên phải đặt env của shell trước install/load model.

**Vướng mắc và cách xử lý:** script .ps1 khởi tạo profile bị execution policy chặn. Đã bỏ script mới đó và dùng assignments PowerShell trực tiếp cùng đường dẫn .venv\Scripts\python.exe; không dùng Activate.ps1 và không đổi policy toàn máy/user. Kiểm chứng inline profile cho HF_HOME/PIP/npm/TEMP trên D và venv Python 3.12.8 thành công.

**Phương án khác / đánh đổi:** di chuyển repo/venv hoặc Docker disk sang D có thể hữu ích khi thiếu chỗ nhưng tăng phạm vi thay đổi, đường dẫn và rủi ro; chưa cần để đạt baseline nhỏ hiện tại. Chỉ đặt cache D vẫn không bảo đảm đủ disk/RAM cho model lớn. Backup env dùng thêm ~116 MB logical files; giữ trong đợt này và ignore Git/Docker, không tự xóa.

**Kết quả / xem lại:** venv mới ~116 MB, node_modules ~115 MB logical files; HF cache 0 bytes. Snapshot cuối C ~10,96 GiB free, host RAM free ~3,2 GiB, chưa tải model. Các snapshots có tác động của ứng dụng khác nên không quy mọi chênh lệch cho project. Trước Bước 03 cần đo lại, ưu tiên batch nhỏ và không load nhiều models; chưa có bằng chứng phải mua GPU.

### K-018 — Khóa dependency theo phạm vi runtime và development

**Ngày / loại:** 02/11/2026 — đã cài và kiểm tra compatibility baseline; lockfiles mới đã tạo.

**Kiến thức:** manifest mô tả dependency/range được phép, lock ghi phiên bản cụ thể đã resolve, gồm transitive dependencies (dependencies do thư viện khác kéo vào). Chỉ pin direct dependency chưa cố định được toàn môi trường; pip check xác minh quan hệ yêu cầu đã cài, không chứng minh business logic đúng. [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/).

**Lựa chọn / lý do:** giữ runtime pins của backend/requirements.lock; thêm requirements-dev.lock include file đó và 10 pins bổ sung cho pytest/httpx/Ruff/transitives. Frontend dùng package-lock.json v3 được npm install sinh ra; npm ci là cách tái lập các lần sau theo lock. Không chép weights, node_modules hoặc venv vào Git. Editable backend giữ source thay đổi được mà không sao chép package code.

**Phương án khác:** pip freeze toàn venv vào runtime lock sẽ trộn dev tools/project-local editable path với dependencies image. Cài theo mỗi lower bound trong pyproject hoặc bỏ package lock có thể resolve phiên bản khác ở lần sau. Nâng major tất cả thư viện để loại warnings ngay làm khó phân biệt môi trường khôi phục với thay đổi behavior; giữ baseline rồi review compatibility riêng.

**Đánh đổi / kết quả:** install bằng Python 3.12.8, Node v24.11.1/npm 11.6.2; pip check đạt và frontend lint/build đạt. pytest 9.0.2/httpx 0.28.1/Ruff 0.17.3 đã pin cùng runtime hiện có. Build backend còn setuptools theo manifest build-system và chưa dùng wheel hashes; lock không có nghĩa byte-identical build hoặc đã thử mọi OS/CPU. Npm có warning deprecated ESLint 9, ghi lại thay vì che hoặc tự đổi major.

**Xem lại:** khi thêm parser/embedding/vector client/auth, cập nhật manifest/locks theo feature đã xác nhận, kiểm tra lại suite và resource. Không cài [stt], CUDA/PyTorch hoặc framework agent chỉ để đạt setup.

### K-019 — Container running khác service ready; tag khác digest

**Ngày / loại:** 02/11/2026 — đã chạy Docker/PostgreSQL/Qdrant và probe thật, chưa có vector collection/model.

**Kiến thức:** container chạy chưa bảo đảm service đã nhận request. Healthcheck đánh giá điều kiện cụ thể; Compose service_healthy dùng kết quả đó khi sắp thứ tự dependency. Image tag là nhãn có thể đổi, digest định danh image content được chọn; pin digest giúp tránh đổi image ngoài ý muốn. [Docker readiness](https://docs.docker.com/compose/how-tos/startup-order/).

**Lựa chọn / lý do:** giữ PostgreSQL 16 image lineage cũ, thêm Qdrant v1.20.0 có [release chính thức](https://github.com/qdrant/qdrant/releases/tag/v1.20.0), pull rồi pin theo digests đã kiểm tra. Chỉ publish PostgreSQL 5433 và Qdrant 6333 trên loopback cho demo local. Chưa cần Redis/Celery hoặc expose gRPC 6334.

**Health checks:** DB dùng pg_isready với user/database thực; Qdrant dùng bash TCP gửi HTTP /readyz và kiểm tra status 200, không giả định image có curl/wget. Chỉ mở TCP port chưa kiểm tra được HTTP readiness. scripts/check_infra.py còn dùng config app để chạy SELECT 1/SHOW server_version và đọc Qdrant metadata/collections, không ghi dữ liệu.

**Persistence:** dùng volumes riêng của Compose, không coi container filesystem tạm là chỗ lưu bền. Recreate sau pin digest vẫn giữ revision 27b126c3c0bc trong DB test. Việc đó kiểm chứng persistence ở lần recreate này, không phải chứng minh backup/restore/HA hay migration RAG.

**Phương án khác / đánh đổi:** tag latest/tự trôi đơn giản hơn nhưng khó tái lập; bind mount DB files trên Windows có khác biệt filesystem/quyền cần kiểm chứng; named volumes phù hợp Docker Desktop hiện tại. Giữ image có pgvector không đồng nghĩa dùng pgvector thay Qdrant cho RAG. Docker disk vẫn có thể dùng C, cache D không giải quyết riêng phần đó.

**Kết quả:** PostgreSQL 16.15 và Qdrant 1.20.0 healthy, 0 collections; container snapshot khoảng 32,08 MiB + 160,9 MiB. Trần VM ~7,613 GiB không phải usage phải cộng vào hai số đó. Xem digests/commands trong report; version mới hơn chỉ thay sau kiểm chứng và xác nhận phạm vi.

### K-020 — Tách profile kết nối, giữ secret và chốt ngân sách 0 USD

**Ngày / loại:** 02/11/2026 — config hạ tầng đã triển khai; model profile chưa smoke. Người dùng chọn **chỉ free tier, 0 USD** trong lúc thực hiện Bước 01.

**Kiến thức / lựa chọn:** localhost trong container chỉ chính container đó, không phải host hay container DB. Host dùng localhost:5433/6333; Compose backend dùng db:5432 và http://qdrant:6333. Settings thêm qdrant_url/collection, FILE_STORAGE_DIR được ưu tiên với STORAGE_DIR là alias legacy; upload default 20 MiB khớp spec. Không đổi API response contract hoặc schema Operations trong bước môi trường.

**Giữ dữ liệu cấu hình:** .env riêng chỉ được thêm keys non-secret còn thiếu và cập nhật upload limit; credentials/LLM values cũ giữ nguyên, không in toàn file. .env.example dùng placeholders/dev examples, không commit key thật. Config model E5/384/CPU/chunk350/batch4 là giá trị chuẩn bị, không chứng minh adapters đã dùng các biến này hay retrieval đạt chất lượng.

**Phương án khác / đánh đổi:** dùng chung URL localhost cho host/container gây nhầm network namespace; ghi endpoint/secret cứng vào frontend làm khó thay môi trường và lộ key. Tách hai profile cần documentation/Compose overrides rõ. Lấy một key rồi mặc định gọi paid fallback không đáp ứng ngân sách người dùng đã chọn.

**Ràng buộc model:** chưa cấu hình API key/quota thật, chưa gọi API và không có phí model trong Bước 01. Bước 03 phải kiểm tra đúng tài khoản/project free tier và quota trước smoke; hết quota thì hoãn/dừng, không bật billing hoặc tự đổi paid tier. Model budget là policy vận hành, chưa có runtime LLM adapter để tuyên bố hard cap đã enforce bằng code. Không yêu cầu gửi secrets vào chat.

**Kiểm chứng / xem lại:** preflight xác nhận DB test là copilot_test riêng, upload 20 MiB, Qdrant host profile đúng; probe hai storage thành công. Khi triển khai domain/model service cần bổ sung validation/token budget/fingerprint đầy đủ và tests của chúng; Settings scaffold chưa tiêu thụ toàn bộ config spec.

### K-021 — Baseline pass cần đúng môi trường và đúng phạm vi

**Ngày / loại:** 02/11/2026 — đã chạy software/infra baseline Bước 01, tiếp nối K-016.

**Kết quả thực:** 64 tests pass trên venv/project dependencies với PostgreSQL thật: 56 guard cases + 8 legacy API/schema tests. Đường safe identifier CREATE DATABASE và Alembic đã chạy trên DB test riêng ở lượt này. Full run báo 1 StarletteDeprecationWarning về TestClient/httpx; không bỏ warning để ghi “không vấn đề”. PostgreSQL dev không được migrate trong đợt test này.

**Frontend / sandbox:** lint và TypeScript qua, esbuild sandbox báo access denied khi đọc thư mục cha/config. Chạy lại cùng npm build ngoài sandbox đạt (44 modules, Vite 6.4.5); không sửa app source hoặc đổi config bundler để chữa một lỗi quyền môi trường. Đây là phân biệt lỗi chạy công cụ với lỗi implementation; lần build thành công không chứng minh RAG UI đã triển khai.

**Ruff / import classification:** checker từ repo root ban đầu nhận cấu hình khác cho scripts và không nhận app/tests là first-party khi ép config backend. Đã giới hạn imports/exceptions của probe, pin known-first-party trong backend/pyproject.toml và chạy lại với config tường minh. Không reorder legacy tests theo kết quả lint phụ thuộc cwd. Final app/tests/scripts check + format pass, 27 files already formatted trong scope đó; backend . check được kiểm tra riêng.

**Phương án khác / giới hạn:** gọi 56 guard passes là full backend success sẽ bỏ qua DB path; gọi 64 baseline passes là AT-R/RAG quality cũng sai vì nghiệp vụ mới chưa có. Tự chạy lại mọi test vô hạn không tăng chứng cứ khi source/environment không đổi; sau checks đạt, chuyển sang tài liệu và bước kế tiếp được xác nhận. Không dọn container/volume của project khác để làm setup chạy.

**Artifact / xem lại:** report environment-step01.md ghi commands, snapshots, warnings và lock/image versions; audit Bước 00 giữ lỗi môi trường lịch sử. Cập nhật README/CLAUDE/AGENTS/PLAN/spec theo trạng thái mới. Bước 02 sẽ chuẩn bị corpus/gold labels sau xác nhận riêng; model quality, auth/documents/worker/search/chat/citation vẫn chưa được nghiệm thu.

### K-022 — Bộ dữ liệu giả lập và human gold là hai trạng thái khác nhau

**Ngày / loại:** 02/11/2026 — đã soạn và kiểm tra cấu trúc ở Bước 02; **chưa có human gold**. Chi tiết [dataset README](eval/datasets/README.md), [báo cáo](docs/dataset-step02.md).

**Kiến thức / vấn đề:** ground truth là căn cứ chấm độc lập với model được đánh giá. Một đáp án do trợ lý soạn có thể đúng hình thức nhưng thiếu điều kiện hoặc gán sai nguồn. Nếu vừa dùng output model làm đáp án chuẩn vừa dùng nó để chấm, sai sót có thể tự củng cố. Checksum chỉ chứng minh bytes không đổi; validator chỉ kiểm tra những quy tắc được lập trình, không chứng minh mọi ý nghĩa nghiệp vụ đều đúng.

**Lựa chọn / lý do:** tạo 10 tài liệu tiếng Việt tự soạn với thông báo giả lập, 45 câu nháp (15 dev/30 test), 6 unanswerable. Có con số, ngày, mã BM-07/BM-09/TS-02, câu nhiều điều kiện và xung đột hai chính sách. Như vậy có input dùng được cho học pipeline mà không cần tài liệu riêng tư/API. Lưu `label_status=draft_pending_independent_human_review`; cả 45 dòng `pending`, annotator/reviewer để trống. Hai người cần đọc nguồn, người A gán/xác nhận nhãn độc lập rồi người B kiểm tra chéo. Code từ chối approved nếu thiếu người hoặc hai tên trùng; việc hai người thực sự độc lập vẫn cần quy trình, không thể chứng minh chỉ bằng CSV.

**Phương án khác / đánh đổi:** dùng tài liệu doanh nghiệp thật sẽ thực tế hơn nhưng cần quyền sử dụng và xử lý dữ liệu nhạy cảm; dataset công khai có thể không đúng domain/ngôn ngữ và nguồn trích dẫn của project. Tự động generate rồi tự approve tiết kiệm công sức nhưng vi phạm gate hai người của PLAN/spec. Corpus ngắn, sạch và chỉ vài nhóm sự kiện chưa đại diện tài liệu dài, bảng/layout phức tạp; 30 câu test cũng chưa cho kết luận thống kê mạnh. Sẽ bổ sung dữ liệu đa dạng ở các đợt được duyệt sau.

**Kiểm chứng / xem lại:** validator đối chiếu 35 blocks vào file thật; đủ 8 loại câu, answerability/status phù hợp. Lệnh mặc định đạt; `--require-reviewed` từ chối đúng vì **0/45 approved**. Chưa đo correctness model. Trước benchmark chính thức phải sửa nhãn theo notes, xuất snapshot reviewed, khóa ledger và remap parser spans sau Bước 05. Không tự điền approved để đóng Bước 02.

### K-023 — Gold spans theo nguồn, xử lý Unicode và tránh rò rỉ dev/test

**Ngày / loại:** 02/11/2026 — author-level mapping và validator đã có; parser-level remapping chưa triển khai. Liên quan spec 14.8–14.9, [validator](eval/validate_dataset.py), [labels](eval/datasets/questions.jsonl).

**Kiến thức:** chunk UUID có thể thay đổi khi chunk size/overlap hoặc worker generation đổi. Gold cần bám nguồn canonical rồi map sang chunks của cấu hình đang đo. Character offset chỉ có ý nghĩa trên đúng chuỗi text/normalization; NFC hợp nhất những biểu diễn Unicode tương đương nhưng không làm mọi dấu tiếng Việt thành giống nhau. Leakage xảy ra khi paraphrase cùng sự kiện ở cả dev và test, khiến việc tune nhìn như tổng quát hơn thực tế.

**Lựa chọn / lý do:** ID `document:author-v1:block`, document version, quote và page/block/line; spans là Python character offsets `[start,end)` trong NFC author text. DOCX dùng paragraph thay vì bịa page; PDF chỉ trang thật; TXT/MD chỉ dòng. Validator kiểm tra revision/location/quote/span, group ID và không chia cùng family hoặc cùng gold block qua hai splits. Corpus vẫn được index toàn bộ; chỉ câu hỏi chia dev/test. Chưa dùng test để tune bất kỳ model nào.

**Lỗi thực tế / cách xử lý:** PDF có BM-09 xuống dòng, PyMuPDF trích xuất thành `BM\u00ad09` nên kiểm tra chuỗi nguyên văn thất bại. Thêm normalization cho phép NFC, collapse whitespace và đổi soft hyphen thành dấu `-` trong phép so nội dung PDF, kèm test regression. Đây là quy ước so sánh hẹp cho corpus này; không xóa mọi dấu câu, không fuzzy match để che lỗi và không dùng offset sau normalization như offset của source khác. Bước 05 phải giữ mapping đúng khi parser chuẩn hóa. Trong test Unicode ban đầu, dữ liệu phân rã thiếu dấu mũ của `ệ`; đã sửa input test, không nới normalization để coi `ẹ` và `ệ` là một chữ.

**Phương án khác / đánh đổi:** exact byte match không chịu được line wrapping/Unicode; fuzzy matching tùy ý có thể nhận nhầm nguồn. Chia random từng câu làm paraphrase rò rỉ. Chia theo document rất chặt nhưng làm ít nhóm dev trên corpus nhỏ; hiện chia theo family/sự kiện và kiểm tra block, chưa chứng minh độc lập ngữ nghĩa tuyệt đối. Parser thay đổi phải remap có kiểm tra, không drop câu mapping lỗi khỏi denominator. Quy tắc span coverage 80% trong spec chỉ áp dụng sau khi mapping thật có; metric primitives hiện chưa thực hiện matching đó.

**Điều chỉnh khi soạn nháp:** q032 ban đầu yêu cầu hai nguồn đều chứa sẵn cùng đáp án. Nếu coi cả hai groups bắt buộc thì Recall phạt hệ thống dù đã đủ bằng chứng. Đã sửa câu sang hỏi bộ hồ sơ nghiệm thu và các trường trong BM-09, dùng hai nguồn bổ sung dữ kiện. Cập nhật seed/labels/hash trước freeze draft, chạy builder đối chiếu lại thành công. Trích đoạn thay thế cho cùng ý về sau phải chung group, không tách thành nhiều ý bắt buộc. Việc sửa này là kiểm tra tác giả, không thay independent human review.

### K-024 — Fixtures thật và reproducibility có giới hạn của PDF/DOCX

**Ngày / loại:** 02/11/2026 — đã tạo files thật, pin dev tools và kiểm tra mở/trích xuất. Liên quan [builder](eval/build_dataset.py), [manifest](eval/datasets/corpus_manifest.json), [dev lock](backend/requirements-dev.lock).

**Kiến thức / lựa chọn:** file đuôi PDF chưa chắc là PDF; một PDF không text có thể là scan hoặc trang trắng. Tạo scan bằng rasterize trang từ tài liệu tự soạn rồi đưa ảnh vào PDF mới, không giữ text layer. Mixed PDF có text trang 1 và ảnh trang 2; encrypted PDF thực sự cần password; malformed PDF/DOCX, file giả đuôi và prompt-injection tách riêng. Nhờ input thật, parser tests sau có thể kiểm tra hành vi thay vì chỉ stub một cờ `is_scan`. Hiện validator mới chứng minh tính chất file; app chưa có code trả các error/status đích.

**Công cụ / lý do:** PyMuPDF 1.28.2 cho tạo/đọc/render PDF, python-docx 1.2.0 cho DOCX, lxml 6.1.3 là dependency của DOCX. Thêm extras `corpus` và dev pins, giữ runtime lock nguyên vì chưa triển khai production parser. Không cần OCR, model hoặc thư viện GPU cho việc tạo fixtures. Dùng thư viện có sẵn khả năng tạo/đọc sẽ ít phụ thuộc hơn Office/LibreOffice GUI hoặc dịch vụ chuyển đổi tài liệu; không coi việc chọn dev tool là quyết định parser production đã hoàn tất. Khi đóng gói/phân phối production cần xem lại yêu cầu chức năng và điều khoản phân phối của từng dependency.

**Tái lập / đánh đổi:** cố định PDF metadata, DOCX core timestamps và thứ tự/timestamp ZIP entries. Lưu seed/tool/font SHA-256; Arial lấy từ máy Windows, không chép font gốc vào repo. Builder chỉ tạo file thiếu hoặc chấp nhận bytes giống hệt; khác bytes/hash thì dừng, không tự ghi đè hoặc re-bless dữ liệu đã sửa. PDF AES-256 có salt ngẫu nhiên nên reuse encrypted fixture đã freeze, xác minh password thử thay vì hứa toàn bộ output byte-identical giữa mọi lần tạo ở thư mục mới. Khác phiên bản thư viện/font cũng có thể khác bytes; dùng artifact committed + manifest để tái lập snapshot. Review ledger được giữ nguyên khi chạy lại builder, sẽ cần hash khi phát hành reviewed snapshot.

**Kiểm chứng:** kiểm tra scan có ảnh/không text, blank không có cả hai, mixed đúng trang, encrypted cần password, malformed không parse được và spoofed không có signature. Đối chiếu paragraph/dòng/trang cho corpus. Builder chạy lại cùng môi trường đạt; tổng corpus/fixtures 2.505.158 bytes. Mật khẩu `fixture-only` là dữ liệu thử công khai, không phải secret doanh nghiệp. Chưa có bằng chứng chống ZIP bomb/XSS/phân quyền hay prompt-injection của model; những tests đó thuộc pipeline các bước sau.

**Nguồn chính thức đã đối chiếu 02/11/2026:** [PyMuPDF Page: text/image/render](https://pymupdf.readthedocs.io/en/latest/page.html), [Document: lưu PDF/mã hóa](https://pymupdf.readthedocs.io/en/latest/document.html), [python-docx: mở/lưu tài liệu](https://python-docx.readthedocs.io/en/latest/user/documents.html). Đây là căn cứ API thư viện, không phải nguồn cho quy định doanh nghiệp giả lập.

### K-025 — Kiểm thử metric khác đánh giá model và nghiệm thu pipeline

**Ngày / loại:** 02/11/2026 — metric primitives và **37 cases pass** ở [eval/tests](eval/tests/); chưa chạy retrieval/LLM. Tiếp nối K-007/K-021.

**Kiến thức:** tìm được một evidence group của câu cần hai groups cho `Hit=1`, `Recall=0,5`, `All-evidence=0`; đây là ba câu hỏi đo khác nhau. Nhiều chunks trùng cùng group không tăng recall. MRR dùng nghịch đảo rank đầu tiên có group hoàn chỉnh trong cutoff K; không tìm thấy trả 0. Câu không có gold không tham gia retrieval average, trả None để caller xử lý mẫu số rõ ràng. Abstention precision đo chất lượng các lần từ chối; recall đo bao nhiêu câu thực sự thiếu nguồn được từ chối; false-abstention rate đo tác hại trên câu có đáp án.

**Lựa chọn / lý do:** [metrics.py](eval/metrics.py) nhận groups **đã được span matcher xác nhận hoàn chỉnh**, tính per-question scores và phép toán abstention; chưa làm matcher, aggregation/report hay inference. Tests dùng ví dụ tính tay để phát hiện nhầm Hit/Recall, overlap double-count, sai rank/cutoff, mẫu số 0, technical errors bị tính thành từ chối đúng. Validator tests cố ý làm sai quotes/revisions/splits/checksums trên RAM/bản sao tạm; kiểm tra review cần hai người, DOCX không fake page, PDF đúng trang và builder không ghi đè. Các tests bảo vệ lỗi có tác động đến kết luận evaluation, không chỉ mirror code cho đủ số lượng.

**Phương án khác / đánh đổi:** gọi model ngay để xem câu trả lời có vẻ hay chưa kiểm tra được toán metric, có thể lãng phí quota 0 USD hoặc làm test phụ thuộc dịch vụ. Dùng fake model rồi công bố accuracy đánh đồng correctness của code với ngữ nghĩa model. Dùng LLM judge tự động ở giai đoạn này thêm sai số/phụ thuộc trước khi có nhãn người; vẫn để P1 theo spec. Primitives đơn giản cần nối matcher/runner ở Bước 05/07 và human answer scoring ở Bước 11, chưa đủ AT-R21/22.

**Bằng chứng thật / giới hạn:** từ root, venv Python `-B -m pytest eval/tests -q -p no:cacheprovider` → **37 passed**; `pip check`, Ruff check/format đạt. Không DB/model/network trong tests. Backend 64 cases và frontend lint/build là baseline đã chạy ở Bước 01; không cộng thành một lượt 101 cases vừa thực thi. Không chạy lại app/frontend khi source của chúng không đổi. Chi phí API đợt này 0 USD vì không có model call; model accuracy/latency/token usage chưa có số đo.

### K-026 — Báo tiến độ theo khối lượng có bằng chứng

**Ngày / loại:** 02/11/2026 — thực hiện yêu cầu người dùng: **mỗi phản hồi cuối nêu X% / 100%**. Quy ước đã ghi [PLAN](PLAN.md#quy-ước-báo-tiến-độ-project), [AGENTS](AGENTS.md), [CLAUDE](CLAUDE.md).

**Kiến thức / lựa chọn:** các bước có độ lớn khác nhau; hoàn thành môi trường không tương đương hoàn thành worker hoặc answering. Dùng midpoint person-hours trong bảng kế hoạch làm trọng số cố định, tổng 102,5, và tỷ lệ đầu việc có bằng chứng trong từng bước. Bước 00/01 là 1,5 + 4; Bước 02 mới 6/7 đầu việc nên ghi thêm `7 × 6/7 = 6`. Hiện `(1,5 + 4 + 6) / 102,5 × 100 = 11,2195…`, báo **11,2% / 100%**. Chưa duyệt human labels nên không ghi 12,2% như đã xong cả Bước 02.

**Phương án khác / đánh đổi:** đếm bước ngang nhau hoặc số files/tests dễ thổi phồng phần chuẩn bị. Dùng giờ thực đã tiêu có thể tăng tiến độ chỉ vì mất nhiều thời gian gỡ lỗi, không chứng minh đầu ra. Midpoint/checklist vẫn là ước lượng quản lý; đầu việc trong một bước không thực sự bằng nhau và chưa đo actual effort. Sửa trọng số về sau cần phiên bản/lý do, không sửa để làm đẹp tỷ lệ. Đây không phải accuracy AI, mức production readiness hay cam kết ngày xong.

**Cách áp dụng / kiểm chứng:** mỗi final báo tỷ lệ, nói rõ gate còn thiếu khi có. Lượt chỉ đọc/giải thích giữ nguyên %. Chỉ sửa file tiến độ trong đợt người dùng đã xác nhận “Thực hiện đi”, tránh biến yêu cầu báo % thành quyền tự ghi workspace. Bước 02 còn người A/B rà soát; không tự điền tên/approve hoặc chạy Bước 03 để tăng tiến độ.

### K-027 — Phát hành bộ nhãn đã được con người duyệt

**Ngày / loại:** 03/11/2026 — đã publish [reviewed-v1](eval/snapshots/reviewed-v1/corpus_manifest.json), strict validation đạt. Tiếp nối K-022, K-026; [báo cáo Bước 03](docs/model-smoke-step03.md).

**Bối cảnh / kiến thức:** người dùng đã tự cập nhật 45/45 dòng approved với annotator/reviewer khác nhau, không có changes requested. Không còn lý do giữ gate human review mở, nhưng sửa một trường trạng thái manifest thôi chưa khóa được dữ liệu mà họ đã xem. Snapshot cần gồm corpus, câu/đáp án, spans và cả sổ duyệt; nếu sổ thay đổi mà không được phát hiện, benchmark sau không còn truy được bộ nhãn đã được ai kiểm tra.

**Lựa chọn / lý do:** thêm `eval.publish_reviewed` kiểm tra nguồn rồi copy đúng files trong manifest vào thư mục phiên bản riêng, không copy file khóa Word. Manifest mới ghi `dataset_version=reviewed-v1`, `label_status=human_reviewed`, parent manifest hash, publication UTC và SHA-256 review CSV. Validate toàn bản stage trước rename. Giữ working draft và ledger người dùng nguyên vẹn, không tự sửa danh tính/approved, không overwrite version đã có. Lần gọi lại cùng inputs chỉ xác minh; source/ledger khác phải tạo phiên bản mới.

**Phương án khác / đánh đổi:** promote draft tại chỗ ít tốn disk nhưng khó phân biệt trước/sau review và khiến builder ban đầu có thể vô tình hạ trạng thái. Copy snapshot lặp khoảng 2,5 MB corpus/fixtures nhưng đơn giản, tự chứa và rất nhỏ so với weights. Chỉ lưu manifest trỏ ra ngoài cần validator cho phép paths vượt root, làm yếu kiểm tra path hiện tại. Đổi version labels không tạo parser mapping: `author-v1` vẫn cần remap ở Bước 05, giữ `pending_step05` trung thực.

**Kiểm chứng:** 45/45 approvals, strict validator đạt trên reviewed-v1; tests publish/idempotency, pending review bị từ chối trước tạo output, đổi ledger nguồn không re-bless output và sửa ledger đã freeze bị phát hiện. Code chỉ xác nhận tính hợp lệ của hồ sơ; việc hai thành viên thực sự đọc nguồn dựa trên xác nhận và sổ do họ cung cấp, không suy diễn từ validator thành đánh giá ngữ nghĩa độc lập thứ ba.

### K-028 — Bảo toàn bytes và quyền đọc trên Windows

**Ngày / loại:** 03/11/2026 — sửa lỗi publish và bổ sung cấu hình repository trong đợt được xác nhận.

**Lỗi thực tế / nguyên nhân:** publish bằng `TemporaryDirectory` ban đầu qua validation trong sandbox, nhưng process người dùng chạy model báo PermissionError khi đọc reviewed manifest. `icacls` cho thấy thư mục sau rename chỉ có SYSTEM/Administrators/OWNER RIGHTS, không có quyền VY kế thừa từ workspace. Thư mục tạm Windows dùng private ACL, quyền đó giữ lại khi di chuyển cùng volume; rename không tự lấy quyền của parent mới. File dữ liệu không bị sai hash.

**Cách sửa / lý do:** publisher tạo staging directory UUID bằng mkdir trực tiếp dưới snapshot parent để kế thừa ACL workspace, validate xong rename nguyên thư mục. Cleanup lỗi chỉ được chạy khi resolved staging parent đúng parent đích đã kiểm tra. Với snapshot mới đã tạo, bật lại inheritance chỉ trong subtree đó bằng icacls; process VY sau đó đọc và chạy smoke thành công. Không cấp Everyone toàn quyền, không sửa thư mục ngoài phạm vi. Kiến thức chính: validation trong một identity không đủ chứng minh user bình thường truy cập được artifact.

**Git / bytes:** Git autocrlf có thể đổi newline khi checkout. Corpus, seed, labels và ledger có SHA-256 theo bytes nên thay LF/CRLF cũng thành khác dữ liệu dù nhìn văn bản giống nhau. Thêm `.gitattributes` dùng `-text` cho datasets/seeds/snapshots, `binary` cho PDF/DOCX. Không chạy renormalize/stage/commit trong đợt này; bytes hiện tại và hashes giữ nguyên. Không chữa checksum bằng cách tùy tiện nhận CRLF là LF sau khi đã freeze, vì quy ước cần được xác định trước.

**Phương án khác / đánh đổi:** so hash text đã normalize có ích cho nội dung nhưng không thay hash file gốc/ZIP/PDF. Tắt autocrlf toàn user gây ảnh hưởng repo khác; attributes theo paths đúng phạm vi. Xóa file `~$*.docx` đang mở có thể ảnh hưởng Word, nên chỉ thêm ignore; corpus manifest/publisher copy exact allowlist, không gom mọi file trong thư mục. Tests và run thật sau sửa đạt; lỗi ACL trước model download xảy ra trước tạo report directory, không phải failure inference của E5.

### K-029 — Môi trường E5 CPU tối giản, model revision và dependency lock

**Ngày / loại:** 03/11/2026 — đã cài và chạy thật. Liên quan K-002, K-017–018, [CPU lock](backend/requirements-ai-cpu.lock), [config](eval/configs/model_smoke.json).

**Kiến thức / lựa chọn:** model ID là tên repo có thể đổi nội dung, revision SHA xác định snapshot weights/tokenizer/config. Dùng E5-small revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, fingerprint SHA-256 sáu files, chỉ tải safetensors/tokenizer/config cần thiết vào cache D. `trust_remote_code=False`, load local-only sau download và không dùng paid Hugging Face inference endpoint. Revision được đọc từ metadata repo công khai trước khi tải.

**Runtime / lý do:** torch **2.9.1+cpu**, transformers **4.57.6**, psutil **7.2.2**. Dùng trực tiếp AutoTokenizer/AutoModel và mean pooling theo model card, thay vì thêm sentence-transformers/sklearn/scipy cho một smoke adapter nhỏ. Pin nhánh Transformers 4 đã kiểm thử thay vì nâng lên latest 5 trong cùng lần đầu inference. Wheel CPU khoảng 110,9 MB, không cần CUDA toolkit, torchvision/torchaudio hoặc GPU. Caches pip/HF ở D; venv vẫn ở C. Torch runtime không được trộn vào production lock trước khi triển khai model service.

**Phương án khác / đánh đổi:** sentence-transformers là lựa chọn tốt khi cần API encode/benchmark phong phú, nhưng hiện thêm dependency surface chưa phục vụ smoke. ONNX/OpenVINO có thể tối ưu CPU sau này; đổi runtime ngay sẽ thêm biến khi chưa có baseline FP32. BGE-M3/local generative LLM cần RAM lớn hơn và chưa có benchmark chứng minh đáng đổi. Host trước install còn khoảng 4.045 MiB RAM khả dụng; ưu tiên một model/process, batch 4 và 2 threads, hoãn BGE thay vì coi RAM 16 GB tổng là chỗ trống.

**Lock / kiểm chứng:** `requirements-ai-cpu.lock` include dev lock, pin toàn bộ packages mới và URL torch CPU **CPython 3.12 Windows x64**. URL platform-specific tránh pip tự chọn CUDA wheel; phải tạo/kiểm tra lock Linux riêng khi đóng gói Docker. Không khẳng định cùng lock chạy mọi OS. pip check đạt; actual runtime ghi torch CPU/no CUDA và package versions trong report. Model fingerprint khác phải coi là experiment khác, không trộn vectors trong cùng collection tương lai.

**Nguồn:** [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small), [PyTorch CPU installation](https://pytorch.org/get-started/locally/), [Transformers 4.57 model loading](https://huggingface.co/docs/transformers/v4.57.2/en/main_classes/model). Đây là căn cứ API/profile; tính phù hợp tiếng Việt cuối cùng vẫn cần dev retrieval evaluation.

### K-030 — Prefix, pooling, chống truncation và đọc đúng số đo embedding

**Ngày / loại:** 03/11/2026 — inference CPU thật đạt; [runtime](eval/embedding_runtime.py), [report](eval/reports/smoke_embedding_20261103_01/metrics.json).

**Kiến thức:** E5 encode query/passage khác vai trò nên dùng prefix tương ứng kể cả tiếng Việt. Mean pooling phải bỏ padding bằng attention mask, rồi L2 normalize nếu profile yêu cầu. Chỉ gọi encode không lỗi có thể đang âm thầm cắt input; số token phải tính sau heading/prefix/special tokens và kiểm tra trước forward. Một chunk target 350 tokens không có nghĩa toàn input luôn dưới 512 khi thêm metadata.

**Lựa chọn / kiểm chứng:** encode 35 author passages (document ID làm heading) và 5 câu dev, FP32/CPU batch 4/threads 2. Shape `[35,384]`, mọi giá trị finite, L2 norms 0,99999988–1,00000012. Vector đầu khi encode một mình/batch khớp tolerance 1e-5, xác minh padding không làm lệch pooling ở case đó. Runtime preflight dùng `truncation=False`; probe đúng 512 tokens inference đạt, 513 tokens raise InputTooLong trước forward. Tokenizer warning cho probe dài là dự kiến, không phải đã chạy thành công input vượt giới hạn.

**Số đo / giới hạn:** resolve/download đầu 12,70 s; process load/imports 5,79 s; passage đầu 49,09 ms; 35 passages sau warmup 0,407 s (~86/s). Năm query khoảng 13,57–18,83 ms. Peak process RSS lấy mẫu 20 ms là 723,13 MiB, không phải peak toàn Windows/Docker hoặc VRAM. Corpus rất ngắn, passage dài nhất 44 tokens; không suy rộng throughput này cho chunks 350 tokens. Cold theo process, không loại OS disk cache; năm query trong một run không đủ p95/SLA. Chưa đo chất lượng hay tốc độ retrieval Qdrant.

**Phương án khác / xem lại:** truncation tự động thuận tiện nhưng có thể cắt điều kiện cuối chính sách mà vẫn trả vector hợp lệ. Chọn reject để chunker Bước 05 có trách nhiệm chia lại. Pool CLS hoặc FP16/quantization cần thí nghiệm khác, không đổi âm thầm pooling/dtype của cùng fingerprint. Sau parser/chunker thật phải đo input dài, query concurrency và khả năng hai process load hai bản model; smoke một process chưa chứng minh RAM cho full stack.

### K-031 — Native Gemini smoke, structured output và preflight ngân sách 0 USD

**Ngày / loại:** 03/11/2026 — adapter/tests/hướng dẫn đã có; **LLM inference chưa chạy**. Người dùng trả lời chưa có key, cần hướng dẫn. [Thiết lập](docs/gemini-free-tier-setup.md), [adapter](eval/gemini_smoke.py), [preflight report](eval/reports/smoke_llm_preflight_20261103_01/metrics.json).

**Lựa chọn / lý do:** giữ candidate `gemini-3.5-flash-lite` sau đọc lại model card/pricing; public standard input/output có free tier tại ngày kiểm tra. Dùng httpx sẵn có gọi native Google REST generateContent, cố định model/endpoint; không thêm OpenAI/Google SDK cho smoke. Profile này không đồng nghĩa OpenAI-compatible adapter dự kiến trong PLAN đã được kiểm chứng: native REST giảm lớp ánh xạ schema và dùng field được tài liệu Google hiện tại mô tả. Production provider abstraction ở Bước 08 vẫn cần triển khai riêng.

**Schema / giới hạn:** `generationConfig.responseFormat.text` gồm mime enum `APPLICATION_JSON` và JSON Schema. Pydantic strict/extra forbid; claim phải có citation IDs trong whitelist, status grounded/partial/insufficient_evidence nhất quán với claims/missing evidence. Bỏ thought parts trước parse/lưu, không ghi key/header/provider error body. ID hợp lệ không chứng minh đoạn nguồn hỗ trợ claim; human semantic scoring vẫn cần. Schema/usage/thinking/decoding thật chưa được provider smoke, không gọi MockTransport pass là model compatibility.

**Ngân sách / guard:** không request trước khi có key, explicit model/native endpoint và hai flags người dùng xác nhận free tier/quota. Endpoint cố định tránh gửi key sang host tùy ý, header x-goog-api-key thay vì query string. Runner tối đa 5 calls tuần tự, output 800 tokens, timeout 45 s, không tools/retry/fallback, dừng lỗi đầu tiên gồm 429. Flags chỉ là attestation, không kiểm soát billing account bên ngoài; muốn giữ 0 USD phải dùng project chưa bật billing và kiểm tra quota. Public free pricing không tự chứng minh điều kiện tài khoản đó. Chưa gọi model → report thật ghi 0 calls/0 USD; khi có calls mà chưa có chứng từ chi phí thì để cost null, không tự công bố hóa đơn bằng 0.

**Protocol / phương án khác:** 4 câu dev có oracle evidence và 1 conflict tự soạn có nhãn ad hoc; không tune trên test q024 để minh họa conflict. Gửi context thủ công là kiểm tra generation, chưa phải app score hoặc full RAG. Compatible endpoint/SDK giúp thống nhất providers khi mở rộng nhưng thêm hành vi cần smoke; local LLM tránh key nhưng chưa biết tốc độ/RAM phù hợp, không tự tải model lớn thay hosted chỉ vì thiếu key. Hướng dẫn người dùng cấu hình riêng là phần còn thiếu, không cần yêu cầu họ gửi secret qua chat.

**Nguồn chính thức 03/11/2026:** [Gemini model](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite), [pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite), [GenerationConfig](https://aistudio.google.com/api-reference/generate-content#GenerationConfig), [API keys](https://aistudio.google.com/docs/api-key), [billing](https://aistudio.google.com/docs/billing), [rate limits](https://aistudio.google.com/docs/rate-limits). Dùng tài liệu key hiện hành thay hướng dẫn cũ giả định mọi key mới đều standard/unrestricted.

### K-032 — Cập nhật tiến độ khi human review xong, model run còn thiếu

**Ngày / loại:** 03/11/2026 — tiếp nối K-026; [PLAN v1.5](PLAN.md), [report](docs/model-smoke-step03.md).

**Bằng chứng / cách tính:** Bước 02 đã publish/strict validate sau 45 approvals nên 7/7, tổng đến đó `(1,5+4+7)/102,5` ≈ 12,2%. Bước 03 chỉ ghi nhận đầu việc 1 (embedding thật) và 2 (tokenizer boundary), tức 2/6. Fingerprint/report embedding đã có nhưng cấu hình chung embedding/LLM chưa smoke nên mục 6 chưa tính; adapter tests không thay mục 3/4. Tổng `(12,5 + 5 × 2/6) / 102,5 × 100 = 13,8211…` → **13,8% / 100%**. Chưa bắt đầu Bước 04, không tự tăng phần trăm vì thêm docs/tests.

**Phân biệt tests:** lượt hiện tại `pytest eval/tests` **64 passed**, Ruff check/format và pip check đạt. Đây là 64 eval cases khác với 64 backend baseline cases đã chạy Bước 01; không cộng thành một lượt 128 cases vừa chạy. Dữ liệu synthetic trong test publication có tên Test A/B để kiểm tra code trên temp copy, không thay thông tin thật trong reviewed ledger. Fake HTTP responses chỉ kiểm tra preflight/schema/error behavior; E5 run riêng mới là chứng cứ model inference thật. LLM `not_run` là thiếu đầu vào tài khoản, không phải đã quan sát model trả lời sai.

**Điều kiện tiếp tục:** người dùng tạo key riêng, xác minh project Free/quota và cấu hình .env theo hướng dẫn; đợt LLM thật tiếp theo vẫn cần xác nhận phạm vi trước thực hiện. Không mở billing, tự tạo giả API success hoặc đổi local generative model để đóng gate. Không commit/push thay đổi mới khi đợt này chỉ duyệt snapshot/model preparation; giữ Git operations cho yêu cầu riêng.

### K-033 — Key đã điền chưa chứng minh model hoặc ngân sách đã sẵn sàng

**Ngày / loại:** 03/11/2026 — người dùng điền key và yêu cầu tiếp tục LLM; chưa xác minh free tier/quota. [Preflight lần 2](eval/reports/smoke_llm_preflight_20261103_02/metrics.json), [hướng dẫn](docs/gemini-free-tier-setup.md).

**Kiến thức / lựa chọn:** key là thông tin xác thực gắn với project; billing tier, quyền model và quota là các thuộc tính khác. Đọc được một chuỗi trong .env không chứng minh key hợp lệ, model được cấp quyền hoặc cuộc gọi miễn phí. Người dùng đã cho phép chạy, nhưng vẫn giữ trần 0 USD. Khi họ trả lời chưa kiểm tra tài khoản, không tự đặt hai flags thành true và không dùng một generation request để dò điều kiện đó.

**Đã làm / bằng chứng:** kiểm tra key bằng boolean, không in nội dung; endpoint/model khớp cấu hình. Public pricing/model card kiểm tra lại ngày hiện tại; reviewed snapshot hợp lệ, chuẩn bị 5 cases với 0 retries/fallbacks. Runner ghi `not_run`, chỉ thiếu xác nhận free/quota, **0 requests/0 USD**. Không gọi provider, không tuyên bố key đã hoạt động. Không chạy lại toàn bộ software suite khi code không đổi; kết quả 64 eval tests ở đợt trước vẫn là bằng chứng đúng thời điểm đó.

**Vì sao không chọn cách khác:** bỏ guard vì có key sẽ làm quyết định ngân sách dựa trên suy đoán. Nhìn No credits rồi gọi đó là Free cũng sai: đây có thể là paid billing plan chưa có số dư. Người dùng kiểm tra project của key trong Projects/Billing Tier, rồi model trong Rate limits; nhãn Set up billing theo tài liệu Google chỉ project chưa gắn billing account, còn Set up Prepay/No credits cần phân biệt. RPM/TPM/RPD là quota toàn project, không tăng chỉ vì tạo key mới. Nếu quota thấp cần giãn nhịp hoặc chờ; không nâng billing.

**Điều kiện tiếp tục:** cần người dùng xác nhận tier/quota thực, không cần gửi key qua chat hoặc cấp lại quyền cho cùng đợt đang chờ đầu vào. Hiện % giữ **13,8% / 100%**, Bước 03 chưa có LLM inference thật. Nguồn: [Google billing status](https://aistudio.google.com/docs/billing#verify-billing), [rate limits](https://aistudio.google.com/docs/rate-limits), [pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite).

### K-034 — Từ xác nhận Free tier đến inference Gemini thật

**Ngày / loại:** 03/11/2026 — API thật đã chạy sau khi người dùng bổ sung thông tin còn thiếu. Tiếp nối K-033; [run đầu](eval/reports/smoke_llm_20261103_01/assessment.md).

**Bối cảnh / lựa chọn:** người dùng đã yêu cầu tiếp tục smoke và cung cấp ảnh project có Free level, rồi xác nhận quota chưa dùng kèm ảnh counters 0. Ghi nhận hai flags true trên .env riêng sau các thông tin đó; không yêu cầu lại quyền cho cùng phạm vi đang chờ đầu vào. Ảnh quota bị cắt thiếu header/tên model nên không khẳng định các số 15/250K/500 chính xác là RPM/TPM/RPD của model từ ảnh. Đây là xác nhận thủ công, không phải trợ lý truy vấn billing API. Model/API access sau đó được kiểm chứng trực tiếp bằng live responses; chưa kiểm chứng trạng thái billing tự động.

**Kết quả thật:** đúng 5 requests, không retry/fallback. q001/q007/q009 grounded và q014 insufficient_evidence qua schema/status/citation-ID whitelist. Model version trả về `gemini-3.5-flash-lite`; claims được trợ lý đối chiếu đúng context đã có, không gọi đó là independent human scoring. Conflict ad hoc bị local parse/validation từ chối với mã gộp invalid_provider_output; run đầu **failed**, giữ nguyên tất cả artifacts. HTTP 200 đã qua nên lỗi này không phải bằng chứng key/quota không hoạt động hoặc thiếu nguồn trong corpus.

**Usage / chi phí:** 4 successful outputs lưu được 529 prompt + 376 candidate = 905 tokens. Call lỗi thứ 5 mất usage trong adapter cũ, không lấy 905 làm tổng 5 calls. serviceTier standard là metadata inference, không chứng minh project paid hoặc Free. Giữ `api_cost_usd=null` sau calls vì không có đối chiếu hóa đơn, dù tài khoản dự kiến Free theo bằng chứng người dùng và không bật billing. Không diễn giải null thành đã phát sinh phí. Các preflight trước đó 0 calls/0 USD vẫn giữ lịch sử đúng.

**Phương án khác / đánh đổi:** auto-approve Free ngay khi thấy key có thể trái trần 0 USD; tiếp tục đòi xác nhận lại sau ảnh và lời người dùng không thêm bằng chứng thực tế. Chọn ghi đúng mức chứng cứ, giữ model và endpoint cố định, chạy số calls đã duyệt. Không lưu key trong report hoặc đổi sang model/provider khác để làm smoke passed. Public model/pricing đã đọc lại ngày chạy; dữ liệu gửi là synthetic/oracle context, chưa có retrieval/app API.

### K-035 — Chẩn đoán output bị từ chối và retest có giới hạn

**Ngày / loại:** 03/11/2026 — sửa adapter/prompt và kiểm chứng; [retest](eval/reports/smoke_llm_conflict_20261103_02/assessment.md), [tests](eval/tests/test_model_smoke.py).

**Lỗi quan sát / giới hạn:** adapter v1 gộp JSON/schema/contract exceptions và bỏ usage/model metadata khi validation lỗi. Vì response conflict đầu không được lưu đủ, không biết chính xác lỗi thuộc nhánh nào; không gọi thiếu missing_evidence là root cause đã chứng minh. Đọc code phát hiện prompt chỉ nói partial cho xung đột, chưa yêu cầu partial phải có missing_evidence theo validator, là khoảng trống hướng dẫn cần sửa; chưa biết nó có liên quan trực tiếp đến response đã mất hay không.

**Cách sửa / lý do:** prompt v2 ghi rõ grounded có claims/không missing; partial có claims có nguồn và nêu căn cứ/điều kiện thiếu; insufficient_evidence không có claims. Diagnostics phân biệt schema error types, unknown IDs, invalid abstention và partial thiếu missing evidence; giữ usage/model metadata được allowlist trên HTTP 200 kể cả output bị từ chối. Không log response body/header, Pydantic input/context hoặc thoughts. CLI case-id chọn đúng một dev/ad hoc case, từ chối test q024; max_calls strict int 1–5, không cho 0 samples bị báo passed. Source snapshots `.py.txt` ở run mới giữ code thực đã chạy ngoài HEAD dirty; không tự tái tạo source lịch sử khi chỉ có hash.

**Phương án khác / đánh đổi:** bỏ validator hoặc cho partial thiếu trường để báo thành công sẽ làm yếu contract. Lưu toàn provider body/Pydantic errors tăng khả năng lộ inputs/secrets/thoughts; chỉ cần error type/rule và usage để biết nhóm lỗi. Gọi lại toàn bộ 5 câu lãng phí quota và vượt giới hạn đợt đầu. Đã hoàn thành offline fixes + **68 tests pass** trước hỏi mở rộng đúng 1 request; người dùng trả lời “Thực hiện đi”, rồi mới retest riêng conflict. Không có retry tự động hoặc paid fallback.

**Retest thật:** 1 request, partial, claims E1/E2 ghi đúng 12/15 ngày và missing_evidence nêu thiếu ngày hiệu lực/thay thế; schema/IDs đạt. Version giữ Gemini 3.5 Flash-Lite; 188 prompt + 143 candidate = 331 tokens, ~1,663 s. Run đầu vẫn 4/5 hợp lệ/failed, run retest 1/1 passed; **6 total requests**, không trình bày thành 5/5 trên prompt v2. Retest khác prompt và có biến thiên model nên không dùng nó chứng minh nguyên nhân lỗi cũ hay accuracy cải thiện. Năm outputs lưu usage đủ tổng 1.236 tokens; tổng cả 6 calls vẫn null do thiếu usage call lỗi đầu.

**Kiểm chứng cuối:** thêm tests giữ usage/model khi invalid response nhưng không lộ inputs, chọn case gửi 1 request, unknown test case bị chặn và max_calls=0/-1/bool/6 bị từ chối; **72 eval cases pass**, Ruff đạt. Đây là suite eval hiện tại, không phải chạy lại backend 64 baseline cases. Không cần thêm API requests để kiểm tra các guards thuần logic.

### K-036 — Gate Bước 03, cấu hình tạm và phần chưa chứng minh

**Ngày / loại:** 03/11/2026 — PLAN v1.6, tiến độ **17,1% / 100%**. [Báo cáo tổng hợp](docs/model-smoke-step03.md).

**Quyết định / lý do:** chọn tạm E5-small CPU FP32/384/mean pooling và Gemini 3.5 Flash-Lite native REST, structured response, output cap gửi 800 tokens. E5 token boundary/RAM đã đo; Gemini có live output được Pydantic validate và các case grounded/thiếu nguồn/conflict được kiểm tra định tính. Gate Bước 03 yêu cầu inference thật cho một embedding + một LLM và ít nhất một response validate được, đã đạt. Không cần biến smoke thành quality benchmark đầy đủ hoặc bảo đảm mọi lần generation đều thành công.

**Cấu hình chưa đo:** không override thinking/temperature nên ghi provider defaults, không khẳng định đã tắt thinking; không có thoughtsTokenCount không chứng minh số thinking tokens bằng 0. Output field được endpoint nhận nhưng chưa gửi case đủ dài để kiểm tra chạm cap 800. Năm mẫu/runs khác prompt chưa đủ p95/accuracy; source/citation ID tồn tại vẫn không chứng minh claim luôn faithful. App schema/auth/worker/retrieval/answering còn chưa triển khai. Human response rubric và benchmark dev/test ở Bước 07/11 vẫn cần thực hiện.

**BGE tùy điều kiện / tiến độ:** đầu việc 5 ghi rõ “nếu đủ tài nguyên”, hoãn challenger do RAM headroom hạn chế và baseline đã đáp ứng gate. Không đánh dấu đã smoke BGE và không loại nó khỏi kế hoạch so sánh sau. Các mục bắt buộc 1/2/3/4/6 hoàn tất theo phạm vi profile; mục tùy chọn không chặn gate. Giữ nguyên mọi trọng số/tổng 102,5 person-hours; `(1,5+4+7+5)/102,5 ×100 =17,073…` → 17,1%. Ghi điều kiện áp dụng ở PLAN thay vì coi 6/6 thí nghiệm đã chạy hoặc tăng % theo số tests. Bước 04 cần đợt được xác nhận riêng; không tự migrate/schema/auth hay commit/push trong đợt smoke này.

### K-037 — Migration RAG giữ dữ liệu legacy, autogenerate cần review

**Ngày / loại:** 03/11/2026 — Bước 04 đã upgrade PostgreSQL dev/test; [report](docs/schema-identity-step04.md), [ADR](docs/decisions/0006-identity-and-rag-schema.md). Migration cũ SHA-256 giữ nguyên, revision mới `20261103_rag04`.

**Lựa chọn / lý do:** giữ workspaces/users và các bảng Operations, thêm username/is_active/knowledge_admin. User cũ được username `legacy_<UUID hex>` để không trùng/lộ email; inactive cho đến khi review, không nâng approver/demo_admin lên admin. Email và password_hash cũ không xóa/đổi. Jobs giữ generic entity fields/state cũ và thêm document/kind/revision/lease; CHECK discriminator phân biệt legacy với RAG, RAG worker sau này phải lọc kind/document_id. Vừa giữ rows cũ vừa tránh dùng nhầm status processing cho pipeline mới.

**Kiến thức / lỗi cần tránh:** autogenerate so metadata với DB không tự viết business backfill hoặc nhận ra mọi CHECK thay đổi. Đã review và bổ sung CHECK VARCHAR enums, backfill trước NOT NULL, users composite unique trước các creator-scope FKs và FK active revision sau khi cả document/revision tồn tại. Không dùng ALTER TYPE của native enum vì project dùng VARCHAR + CHECK. Không import models hiện tại vào migration để tạo DDL động; migration snapshot được sinh và review riêng.

**Phương án khác / đánh đổi:** drop/rename toàn legacy nhanh nhưng mất dữ liệu/FKs và trái phạm vi. Nhân đôi users/jobs cho RAG làm scope/migration khó đối chiếu hơn. Additive discriminator giữ dữ liệu, đổi lại CHECK/filter phức tạp hơn; username legacy không tự thành tài khoản mới đăng nhập được. Downgrade có guard từ chối nếu RAG tables/admin đã có dữ liệu, thay vì DROP TABLE rồi coi là rollback an toàn.

**Kiểm chứng:** test trên schema tạm của PostgreSQL test có user approver/password hash/job processing thật trước upgrade: các giá trị giữ nguyên, username backfill đúng, inactive; downgrade/upgrade khi chưa có RAG data đạt. Có RAG data thì downgrade từ chối trước xóa bảng. Toàn schema tạm rollback, không drop dev DB. Dev ban đầu trống, test ở revision legacy với rows trống; sau tests dev mới được migrate/seed theo phạm vi đã duyệt.

### K-038 — Bất biến ở PostgreSQL và phạm vi chúng thực sự bảo đảm

**Ngày / loại:** 03/11/2026 — schema mới và SQL constraint tests đã chạy thật. [models](backend/app/models/knowledge.py), [tests](backend/tests/test_rag_constraints.py).

**Kiến thức / lựa chọn:** validation Python chỉ bảo vệ đường gọi qua service, còn DB constraints bảo vệ cả writer khác và yêu cầu đồng thời. Partial unique live hash giữ chỗ cả status deleting; chỉ status deleted mới cho upload cùng hash. Unique theo kind/status chặn hai jobs active cùng loại/document; partial unique running/session chặn hai query đang chạy. Idempotency session/client_request_id khác invariant running: hai request ID khác nhau vẫn có thể tranh cùng session, cần cả hai ràng buộc.

**Scope FKs:** creator+workspace FK bảo đảm owner thuộc workspace; active_revision+document FK chặn dùng revision của document khác. Query/run-session composite FK chặn message gắn run của phiên khác. Citation chunk ON DELETE SET NULL giữ lịch sử/tombstone, không cascade xóa cả chat. Các JSONB spans và generation membership còn cần domain service/parser kiểm tra; DB không tự chứng minh đủ vector points, text faithful hoặc lease chưa bị worker khác thay thế.

**Phương án khác / đánh đổi:** chỉ SELECT rồi INSERT có race trước khi commit; chỉ unique session/client ID không chặn hai input khác nhau chạy cùng phiên. SQLite/mock SQL không chứng minh partial indexes/UUID/FK/locking PostgreSQL. Dùng constraints mạnh giảm dữ liệu sai nhưng phải review migration/FK cycles và xử lý IntegrityError ở service tương lai, không trả raw SQL error cho client.

**Bằng chứng:** real inserts/raw SQL kiểm tra hash/count/text, duplicate revision/source block/chunk/point, live dedup, active ingest/cleanup, running lease fields, query/message/citation uniqueness và active revision sai document. Alembic check báo không có operations mới. Chưa chạy worker concurrency/restart/race/publish transaction, không gọi constraint test tuần tự là đã nghiệm thu fault recovery. [PostgreSQL constraints](https://www.postgresql.org/docs/16/ddl-constraints.html).

### K-039 — Mật khẩu khác token: Argon2id và SHA-256 dùng ở hai chỗ khác nhau

**Ngày / loại:** 03/11/2026 — auth backend đã triển khai/probe. [security.py](backend/app/core/security.py), [ADR RAG-06](docs/decisions/0006-identity-and-rag-schema.md).

**Kiến thức / lựa chọn:** mật khẩu do con người chọn có entropy thấp, cần hash chậm/memory-hard và random salt để tăng chi phí dò khi DB lộ. Dùng Argon2id time_cost=2, memory=19.456 KiB, parallelism=1; mỗi lần hash có salt khác. Token lại do CSPRNG sinh 32 random bytes (~256-bit), dạng URL-safe 43 ký tự; hash SHA-256 đủ để không lưu bearer plaintext mà không cần Argon2 tốn RAM cho mỗi API request. Token hash không phải mật khẩu hash và không gửi được như bearer gốc.

**Opaque thay JWT:** demo chỉ một backend/PostgreSQL, lưu user/hash/expiry/revoke dễ kiểm soát và phản ánh role/is_active mới mỗi request. TTL mặc định 3.600 giây, hết hạn/revoked/inactive/role legacy trả 401. Không cần JWT signing secret/algorithm/rotation/refresh ngay; đánh đổi là DB lookup mỗi request. Khi nhiều services/traffic mới xem lại JWT/central auth provider. Bcrypt/PBKDF2 chưa chọn vì không có compatibility/FIPS bắt buộc; Argon2id đáp ứng baseline hiện tại.

**Bảo vệ đầu vào:** username ASCII lowercase/case-normalized, extra identity/role fields bị từ chối. Password không truncate, login giới hạn tối đa 128 ký tự; seed cần 12–128 và thực tế sinh 24 ký tự ngẫu nhiên. Unknown user vẫn verify dummy hash để giảm early return, không gọi đó là chống enumeration/timing tuyệt đối. Generic 401 không phân biệt sai password, inactive hay role bị loại. Bearer malformed bị chặn trước hash lookup, token chỉ nằm trong success response/Authorization của người dùng.

**Kiểm chứng / giới hạn:** salted hashes khác nhau, đúng/sai/malformed legacy hash an toàn; login/me, expired/revoked/inactive/role change và raw token không ở DB. Argon2 dependencies được pin runtime và pip check đạt. Không triển khai refresh/SSO/reset/registration; public HTTPS/login rate limiting còn cần trước dùng ngoài demo. [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

### K-040 — Authorization theo resource, error/request ID và read guard

**Ngày / loại:** 03/11/2026 — [access service](backend/app/services/access.py), [resource routes](backend/app/api/resources.py), [API tests](backend/tests/test_rag_identity.py).

**Lựa chọn / lý do:** role/workspace/user lấy từ token user đã xác thực qua DB, không từ body/query hoặc UUID client gửi. Lookup document scope trước rồi mới kiểm tra deleted: foreign/missing đều 404, own deleting/deleted 410; role thiếu quyền 403, không login 401. Chat session/run lookup còn ràng buộc created_by, kể cả knowledge_admin không bypass owner. Jobs join documents để lọc scope, legacy generic jobs không lọt vào RAG read API.

**Source history:** cờ redaction lưu trong message có thể cập nhật chậm sau soft-delete. Read API kiểm tra SQL hiện tại: document/revision ready, workspace/active revision/generation, chunk association và citation available; bất kỳ nguồn không hợp lệ thì che content. Không trả excerpt snapshots/structured payload/trace để vòng qua guard. Tests đổi source/deleting, xóa chunk, mismatch generation, failed revision và unavailable citation trước khi cờ message cập nhật. Đây là read guard foundation, chưa phải cleanup/race workflow Bước 09 hoặc full AT-R18.

**Envelope / errors:** đổi runtime về contract spec 10 `{data,request_id}` và `{error:{code,message,details},request_id}`; frontend apiFetch unwrap data và nested error, không giữ contract lỗi phẳng legacy. Server sinh request ID, thêm X-Request-ID/no-store, 401 có WWW-Authenticate. Error handler cũng đặt headers để lỗi 500 ngoài middleware không mất ID. Không echo validation inputs hoặc log exception text/SQL params có thể chứa credentials; log loại lỗi + ID thay traceback đầy đủ. Đánh đổi là debugging cần trace có kiểm soát, không chép secrets vào log mặc định.

**Kiểm chứng / giới hạn:** real API tests cho cross-workspace/owner, role body spoofing, admin dependency qua route test riêng, missing auth, source masking và 500 có request ID nhưng không lộ secret giả. Frontend lint/build đạt sau helper đổi envelope; chưa có browser E2E/auth UI. Không triển khai upload/delete/retry ở đây để tạo kết quả giả: dependency đã chứng minh HTTP 403, nhưng full write-action matrix cần routes/service bước 05/06/09. UUID khó đoán không thay authorization; chưa tuyên bố DB RLS/production multi-tenant.

### K-041 — Seed có transaction và credentials không thuộc source code

**Ngày / loại:** 03/11/2026 — [seed CLI](backend/app/seed.py), .env riêng và dev auth probe.

**Lựa chọn / lý do:** seed workspace ID/user IDs deterministic và usernames demo.admin/demo.member rõ role. Mật khẩu sinh ngẫu nhiên khác nhau bằng secrets, chỉ thêm keys còn thiếu vào .env bị ignore, giữ API key/DB credentials đã có. Chỉ placeholders vào .env.example. Kiểm tra cả hai password trước writes; caller dùng một transaction. Repeat seed không trùng users, không reset password hash hoặc tự promote/deactivate; identity/role conflict phải review, không lấy seed như đường nâng quyền.

**Phương án khác / đánh đổi:** hardcode mật khẩu demo trong Git dễ dùng nhưng làm mất boundary secrets. Reset theo env mỗi lần startup có thể đổi tài khoản đang dùng hoặc nâng quyền ngoài ý muốn; seed tách CLI để chủ động chạy. Opaque tokens probe được revoke sau khi thử; không giữ raw tokens trong report. Đổi DEMO_ADMIN_PASSWORD trong .env sau khi seed không tự đổi mật khẩu đã hash trong DB, cần workflow reset riêng nếu được yêu cầu sau.

**Tài nguyên / lỗi môi trường:** Docker Desktop tắt khiến DB chưa ready; khởi động hidden rồi chỉ up db bằng volume hiện có. Một lượt autogenerate chờ kết nối lâu đã dừng trước ghi revision; thêm libpq connect_timeout=5 cho app/migration, không kết luận timeout nguyên nhân schema sai. Libpq có thể thử nhiều địa chỉ nên đây không phải deadline tổng 5 giây. Readiness/probe thực mới xác nhận service nhận kết nối. Qdrant không cần cho auth/schema, không claim đã probe lại.

**Bằng chứng:** seed dev tạo 2 users, seed lần hai tạo 0; login/me cả hai roles qua ASGI TestClient với Postgres dev thật, token probe revoke rồi 401. Dev 2 users/0 documents/2 revoked tokens; test 0 users/documents/tokens sau rollback. Không in password/token/API key. CLI seed và API DB errors báo generic type/message để không dump SQL bound parameters. DB dev đã migrate, không nhầm fixture rollback ở test là rollback schema dev.

### K-042 — Definition of done Bước 04 và tiến độ

**Ngày / loại:** 03/11/2026 — [report](docs/schema-identity-step04.md), PLAN v1.7. Bước 04 đủ 6 đầu việc foundation: schema/constraints, chuyển tiếp roles/jobs, seed/auth, scopes và envelope/config/transactions.

**Kết quả thật:** full backend **124 passed, 1 warning**, gồm 56 guard, 6 legacy schema, 2 API envelope, 35 identity/security cases, 23 RAG constraint và 2 migration cases. Suite eval chạy riêng **72 passed**, không gọi model. Alembic check không drift; old migration SHA bất biến; dev/test head mới. Frontend lint + TypeScript/Vite build (44 modules), Ruff check/format và pip check đạt. Không cộng thành một lệnh 196 cases đã chạy; đây là hai invocations riêng. Warning TestClient/httpx đã có từ trước, không skip/sửa major dependencies để che.

**Giới hạn nghiệm thu:** auth/scoped resources và write-role dependency đã có, AT-R09/19/23 chỉ nền phù hợp bước này. Upload/source file API/parser/worker/retrieval/answer/delete lifecycle chưa có; chưa tuyên bố full acceptance hoặc production auth. Không gọi model/API hoặc tải weights trong Bước 04. UI vẫn placeholder, helper mới tương thích envelope; không làm UI login ngoài phạm vi.

**Tiến độ / tiếp tục:** giữ trọng số 8 cho Bước 04 và tổng 102,5. `(1,5+4+7+5+8)/102,5×100 =24,878…` → **24,9% / 100%**. Bước 05 tiếp theo là upload/parser/chunker với canonical mapping, chưa bắt đầu và cần xác nhận đợt riêng. Không tự commit/push các thay đổi đang có của Bước 03/04. Các báo cáo cũ giữ thời điểm/kết quả lịch sử thay vì viết lại như mọi feature đã tồn tại trước đó.

### K-043 — Multipart streaming, authorization và dedup dưới tải đồng thời

**Ngày / loại:** 03/11/2026 — đã code và kiểm chứng ở [Bước 05](docs/parsing-upload-step05.md), [router](backend/app/api/uploads.py), [service](backend/app/services/uploads.py).

**Kiến thức:** `UploadFile` spool giúp không giữ toàn bộ file trong RAM, nhưng `request.form(max_part_size=...)` chỉ giới hạn non-file fields trong Starlette đang cài. Vì vậy cần hai giới hạn: tổng bytes receive (kể cả không Content-Length) và file bytes khi stream 64 KiB. Mặc định 20 MiB/file + 64 KiB request framing. Bắt đầu bằng AdminUser nên member/anonymous không được ghi; workspace lấy SQL identity, không nhận trong multipart.

**Lựa chọn:** extension/MIME/signature cùng kiểm tra; hash bytes gốc SHA-256; UUID storage key tách tên hiển thị. DB partial unique index `(workspace,sha256)` cho mọi trạng thái chưa deleted xử lý race. Hai request cùng kiểm tra “chưa tồn tại” vẫn có thể insert đồng thời; unique violation được bắt qua savepoint rồi trả 409 + ID đúng scope. Đổi filename/extension không làm đổi hash. Cùng bytes ở workspace khác vẫn là hai tài liệu riêng; không tiết lộ nguồn giữa workspaces.

**Phương án khác / đánh đổi:** đọc hết request rồi kiểm size đơn giản nhưng đã dùng hết memory/disk trước khi chặn. Dedup bằng filename sai vì hai bản khác nội dung có thể trùng tên. Global dedup tiết kiệm disk nhưng gây rủi ro lộ sự tồn tại và phức tạp ownership/cleanup. P0 chọn scoped dedup với local storage; object storage cân nhắc khi nhiều máy deploy.

**Bug thực:** python-multipart bỏ Windows full path vì compatibility IE, khiến chỉ validate filename đã parse không thấy traversal. Đã validate thêm Content-Disposition gốc bằng standard email header parser. UUID key sâu và tên thư mục test dài gây MAX_PATH trên Windows; chuyển key thành workspace hex/revision hex và dùng basetemp ngắn. Không đổi registry/chính sách Windows để che lỗi. Tests gửi cả Unix/Windows traversal, fake MIME/signature, oversized streamed body và cùng bytes đổi tên. Race với hai PostgreSQL transactions thật cho đúng một 202, một 409, một document/revision/job/file.

Nguồn: [Starlette request files](https://starlette.dev/requests/); thư viện python-multipart phiên bản đã pin được kiểm tra trực tiếp. Đây là validation boundary, không phải bảo đảm PDF/DOCX đã parse thành công sau magic check.

### K-044 — Filesystem và SQL không có một transaction chung

**Bối cảnh:** upload vừa ghi file vừa insert metadata. SQL rollback không tự xóa file, còn xóa file khi commit thực ra đã thành công sẽ làm document mất nguồn.

**Cách làm:** ghi file theo key server, flush document → revision → job trong transaction, chỉ trả 202 sau commit. Lỗi validation/flush hoặc commit được xác minh rollback thì unlink file. Khi commit acknowledgement bị mất, rollback connection state rồi query revision: đã tồn tại thì giữ file; không tồn tại thì dọn. Nếu DB chưa thể trả lời, giữ file và log document ID cho reconciliation. Không log bytes/path/secrets.

**Phương án khác:** lưu bytes trong PostgreSQL có thể gom atomicity nhưng làm DB/backup lớn; object storage + outbox/reconciler phù hợp deployment lớn hơn. File rename không biến filesystem và SQL thành distributed transaction. P0 dùng compensating action, chấp nhận cần sweeper cho process kill hoặc DB outage dài; phần recovery vận hành nối tại worker, không tự triển khai Bước 06 trong đợt này.

**Bằng chứng:** fault injection job flush và commit trước khi ghi thành công đều không còn file/document/revision. Test mất acknowledgement sau commit giữ nguyên source và metadata. Interrupted stream dọn file. Kết quả trên DB test thật; không suy ra mọi failure/OS crash đã được xử lý.

### K-045 — Source fidelity, normalization và hard timeout parser

**Đã triển khai:** [parsing.py](backend/app/services/parsing.py) dùng PyMuPDF 1.28.2/python-docx 1.2.0, UTF-8/BOM TXT/MD. Giữ raw extracted/serialized text, normalized text và location. NFC thống nhất dấu tiếng Việt; whitespace collapse tránh quote sai chỉ vì line wrap. U+00AD → `-` là quyết định khai báo cho PDF mẫu BM-09, không phải quy tắc phổ quát đúng với mọi ngôn ngữ. Nếu dữ liệu thật có discretionary hyphen cần đổi normalization version, remap và reindex.

**Offset:** Unicode code point trên normalized block, từ 0 đến end-exclusive; page/line/block từ 1. Không phải byte offset hay raw-text offset. Ví dụ NFD `To\u0302i` và NFC `Tôi` khác số code points dù hiển thị tương đương. Việc giữ raw không có nghĩa có thể lấy normalized offsets cắt raw. DOCX body paragraph/table là location thật; không bịa số trang vì pagination phụ thuộc Word/fonts/layout. Header/footer ngoài phạm vi body parser hiện tại; PDF bảng đơn giản có đường kẻ, DOCX/Markdown rows serialize có provenance, không hứa đọc biểu đồ/merged table phức tạp.

**Giới hạn / lỗi:** 200 PDF pages; DOCX 2.000 ZIP entries/100 MiB uncompressed kiểm trước XML, không extract paths ra disk; 2 triệu tổng raw+normalized characters/20.000 blocks/5.000 chunks. PDF text ngắn có nghĩa vẫn giữ, không dùng character threshold tùy tiện làm OCR heuristic. Scan có ảnh không text → needs_ocr; blank → no_extractable_text; mixed chỉ giữ trang text và cảnh báo skipped pages; encrypted/malformed/encoding sai có mã riêng. HTML/prompt injection là dữ liệu, không thực thi hoặc tải link.

**Tại sao subprocess:** thread timeout chỉ ngừng chờ, không dừng native C parse đang treo. `subprocess.run(timeout=60)` kill/wait child để parser không giữ worker vô hạn. Guards hiện tại không phải OS RAM sandbox; phải đo resource trước tăng concurrency. OCR/layout AI/API parser hoãn vì máy CPU 16 GB/corpus text/ngân sách 0 USD; pypdf/pdfplumber xem xét nếu layout/footprint hoặc cách phân phối yêu cầu đổi. PyMuPDF đang có dual AGPL/commercial license theo nhà cung cấp; khi phân phối cần kiểm tra lựa chọn license phù hợp, chưa mua commercial license.

**Kiểm chứng:** real format fixtures, scan/blank/mixed/encrypted/malformed, ZIP bounds/path, subprocess deadline 1 ms để chứng minh hard timeout path, UTF-8 BOM/NFD/CRLF, bảng DOCX và PDF có kẻ, quote ở cả hai trang PDF render thật. Các text fixtures nhỏ không chứng minh throughput của file 20 MiB/200 trang.

Nguồn: [PyMuPDF extraction/tables](https://pymupdf.readthedocs.io/en/latest/page.html), [python-docx body iteration](https://python-docx.readthedocs.io/en/latest/api/document.html). Parser version hiện tại gắn normalization và pinned libraries; đổi parser phải version artifact.

### K-046 — Token budget thật, structure boundaries và context provenance

**Bối cảnh:** E5 có input tối đa 512 tokens; đếm ký tự hoặc để tokenizer truncate có thể mất điều kiện chính sách mà không báo. Tokenizer LLM và embedding cũng không thể thay nhau.

**Quyết định:** [chunking.py](backend/app/services/chunking.py) nạp tokenizer.json local-only từ E5-small revision cố định; dùng Rust tokenizers trực tiếp, không cần load torch/weights để đếm. Cả `passage: ` + heading/header + text + special tokens phải nằm trong **350 tokens toàn input**, nhỏ hơn 512. Đây là cách hiện thực bảo thủ của target 350 trong PLAN, không phải 350 body tokens cộng thêm overhead. Không padding/truncation. Settings chặn overlap >= size hoặc đổi model/revision chưa được hỗ trợ. Parser/tokenizer deps chuyển sang runtime locks; Torch vẫn chỉ thuộc CPU smoke/model environment.

**Cách hoạt động:** gộp cùng cấu trúc đến budget, không xuyên trang PDF hoặc heading/header context boundary. Block dài tách ở Unicode/word boundary, đếm lại input cuối; overlap target 50 chỉ trong block phải tách, ưu tiên boundary cấu trúc khi gộp block. Mỗi substring có source span chính xác và mọi ký tự nội dung đều được bao phủ. Header dài đến mức không còn chỗ cho nội dung → lỗi document_limit_exceeded; không cắt heading âm thầm. Giới hạn input ký tự mỗi lần tokenize và tổng chunks để tránh công việc bệnh lý.

**Provenance:** heading/table header lặp có `role=context` và trỏ block/offset gốc; nội dung chính có `role=content`. Vì vậy UI/retrieval evaluator tương lai không nhầm header lặp thành câu gốc mới hoặc evidence độc lập. Chunk lưu token count/hash/location tổng hợp + locations chi tiết. Parser-local block IDs sẽ ánh xạ UUID theo generation ở Bước 06.

**Phương án khác:** fixed character chunks nhanh nhưng không kiểm được input budget; fixed token windows dễ cắt điều kiện/bảng; recursive splitters tổng quát thêm abstraction mà vẫn phải viết provenance riêng. BGE-M3 có tokenizer/context/index khác, chưa đổi chỉ để chunk dài hơn; phải benchmark và reindex. Giữ baseline đơn giản có thể giải thích, xem lại size/overlap bằng dev retrieval benchmark thay vì suy từ số chunk.

**Bằng chứng:** round-trip source spans trên 10 tài liệu, E5 count gồm prefix/special thực, block tiếng Việt dài kiểm không mất ký tự/có overlap/không vượt 350 và fail max_chunks. Corpus hiện tại chỉ 14 chunks, max 162 tokens, không lấy corpus nhỏ này làm bằng chứng đã stress 512 tokens. [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small).

### K-047 — Remap gold mà không sửa lại lịch sử human review

**Đã kiểm chứng:** [mapper](eval/parser_mapping.py), [artifact version 1](eval/mappings/reviewed-v1-source-v1-e5-350-v1.json). Author-v1 của Bước 02 là cách tác giả chia fact, không phải blocks parser. Nếu so char offsets của hai namespace trực tiếp, retrieval metric có thể báo đúng/sai giả.

Mapper validate snapshot reviewed/hashes trước, chạy cùng production parser/chunker trên 10 files, tìm quote duy nhất đúng page/paragraph/line, rồi ghi parser spans mới. Missing/ambiguous quote hoặc content chunks không phủ đủ ký tự gold đều fail; không fuzzy-match tùy output và không bỏ câu khó. Context headers lặp không được dùng để “bù” coverage của content bị mất. Artifact giữ author spans, new spans, raw/normalized blocks, chunks, tokenizer/config và parent manifest/questions/review hashes.

Kết quả **35 author blocks → 54 parser blocks, 14 chunks; đủ 45 câu/47 evidence references**, giữ 6 câu unanswerable. Test tái tạo report từ nguồn thật so toàn JSON với artifact. Source snapshot/ledger không thay đổi; pending_step05 trong manifest lịch sử giữ nguyên, artifact mới xác nhận mapping bằng hash. Đọc toàn corpus/gold để kiểm extraction compatibility không phải tune retrieval trên test; chưa có retrieval scores hay quality benchmark. Công thức match 80%/union top-k để tính retrieval metric vẫn cần ở Bước 07/11.

### K-048 — Nghiệm thu Bước 05, lỗi môi trường và quy tắc UI

**Kết quả thật:** full backend **166 passed, 1 warning**; eval **76 passed** ở lệnh riêng; Ruff check/format 75 files và pip check đạt. Warning Starlette TestClient/httpx giữ từ baseline. Không chạy frontend tests/build vì frontend không đổi. Source render PDF kiểm trực quan dấu/câu C1 và BM-09; không coi đây là review chất lượng RAG mới.

Các lỗi đầu lượt gồm shared Temp ACL khác sandbox/host, MAX_PATH và fixture module plugin chỉ chạy riêng được nhưng không được full collection nhận như mong đợi. Dùng basetemp ngắn duy nhất trong workspace; fixture identity dùng chung chuyển vào conftest. Chạy lại full suite sau sửa, không skip cases. Basetemp phải mới vì pytest có thể xóa đường dẫn đã tồn tại; không đổi ACL toàn user hay xóa thư mục ngoài workspace.

**Definition of done:** hoàn thành 7/7 đầu việc Bước 05 ở tầng upload/parser/chunker/mapping. Chưa có worker chuyển queued → ready, publish vector hoặc cập nhật terminal job errors; phần đó của AT-R01–05 nghiệm thu ở Bước 06. Không sửa applied migration/legacy data, không gọi API model hoặc tải thêm weights, không commit/push. Tiến độ `(25,5+12)/102,5×100` → **36,6% / 100%**, không phải AI accuracy.

**Quy tắc người dùng 03/11/2026:** trước khi code/sửa UI phải nhắc, nêu màn hình/file/phạm vi và chờ “Thực hiện đi” cho đợt UI. Đã lưu [AGENTS.md](AGENTS.md)/[CLAUDE.md](CLAUDE.md) trong đợt backend được duyệt; xác nhận backend không tự cho phép UI. Bước 06 hoặc bất kỳ đợt mới nào cũng chờ phạm vi/xác nhận riêng.

### K-049 — Durable queue, lease và fencing không phải exactly-once

**Ngày / loại:** 03/11/2026 — đã code/kiểm chứng Bước 06; [JobQueue](backend/app/services/jobs.py), [worker](backend/app/worker.py), [ADR RAG-05](docs/decisions/0005-durable-ingestion-worker.md).

PostgreSQL lưu job bền qua restart; worker riêng claim FOR UPDATE SKIP LOCKED trong transaction ngắn. Khóa document trước job ở mọi đường ghi để cùng thứ tự với publish/delete tương lai; không giữ DB transaction/lock khi parse hoặc inference. Heartbeat thread dùng session riêng, default 15 s gia hạn lease 60 s. DB clock quyết định hạn lease, không dựa wall clock client để cấp quyền publish.

**Generation/fencing:** lease token xác định chủ job hiện tại; generation mới cho mỗi attempt cô lập chunks/points. UUIDv5(generation, block/chunk identity) tạo ID ổn định trong attempt để upsert lặp không nhân bản, nhưng attempt mới không ghi đè attempt cũ. Check cả token, generation, lease expiry, document status/lifecycle và revision khi ghi stage/persist/publish/fail. Worker cũ còn chạy sau mất lease không được cập nhật hoặc fail thay worker mới. Source spans chuyển parser-local IDs sang SQL block UUID, giữ parser_block_id/context IDs để mapping canonical sau này.

**Vì sao chọn:** BackgroundTasks gắn web process không giải quyết durable restart; Celery/Redis/RabbitMQ thêm hạ tầng chưa cần với một CPU worker/corpus nhỏ. SKIP LOCKED tránh đợi cùng hàng queue, không phải bảo đảm exactly-once. Chấp nhận retry và orphan staging, quản bằng generation/manifest/reconciliation. Xem lại transport khi có số đo queue contention hoặc nhiều workers; không bỏ fencing khi đổi queue.

**Bằng chứng:** hai claim không sở hữu cùng job; document đang bị khóa được bỏ qua; heartbeat vẫn gia hạn khi inference chờ lâu hơn lease gốc và session khác vẫn khóa document NOWAIT được. Kill tiến trình thật sau batch Qdrant đầu rồi restart tạo generation mới, active generation đủ points, old token touch/persist/publish/fail đều bị từ chối. Tests dùng vector giả có nhãn, DB/Qdrant thật; không gọi đây là AI quality. [PostgreSQL locking](https://www.postgresql.org/docs/16/sql-select.html).

### K-050 — Model process, hard timeout và fingerprint đủ để tái tạo

**Đã chọn/kiểm chứng:** giữ E5-small CPU FP32/eager, 384 chiều, masked mean/L2, threads 2/batch 4/concurrency 1. [LocalEmbedder](backend/app/services/embeddings.py) giữ một child process nạp model, tái dùng nhiều tài liệu. Không chuyển sang GPU vì máy không có NVIDIA, không tải challenger hoặc đổi paid API trong ngân sách 0 USD.

Thread timeout chỉ ngừng chờ, không dừng Torch/native work. Child process có startup/batch timeout 120 s; hết hạn terminate/join, process sau nạp lại khi cần. Persistent child tiết kiệm cold load so với spawn model cho mỗi file; đánh đổi IPC, lifecycle và memory management phức tạp hơn in-process inference. Heartbeat ở parent nên model chậm không tự làm job hết lease. Parent kiểm tra lại lease trước upsert/publish, không dùng vector trả muộn của attempt mất quyền.

**Fingerprint:** ID/revision và 6 file hashes cố định weights/tokenizer thực; lưu dimension/device/dtype/pooling/normalization/prefix/max input/runtime versions. Index version thêm parser/chunker/config. Chỉ tên model không phân biệt revision hoặc preprocessing; chỉ dimension không phân biệt hai vector spaces khác nhau. Kiểm tra shape/count/finiteness/norm, từ chối NaN/zero/boolean/sai chiều trước Qdrant. Không cắt/pad vector hay silently truncate text. Thiếu cache/runtime → startup lỗi local-only, không download/fallback.

Core [e5_runtime.py](backend/app/services/e5_runtime.py) chuyển từ eval sang backend để worker và smoke dùng cùng implementation; eval shim giữ import compatibility. Source snapshots cũ giữ nguyên, smoke mới capture cả shared runtime. requirements-worker-cpu.lock dành Windows CPython 3.12; không đem URL wheel Windows vào Linux image. API runtime không phải load Torch ở startup. ONNX/OpenVINO/quantization hoặc BGE chỉ xét sau dev retrieval/resource benchmark, đổi runtime cũng cần fingerprint/reindex.

**Kiểm chứng:** model thật chạy 1+10 documents; unit tests kiểm startup timeout và batch timeout sau khi child đã báo ready, đều terminate child; invalid vectors không vào index. Không có stress/OOM benchmark, không suy ra mọi file lớn đều dưới 120 s. [E5 model card](https://huggingface.co/intfloat/multilingual-e5-small).

### K-051 — Atomic publish qua hai hệ thống bằng manifest và SQL authority

**Bối cảnh:** Qdrant đã ghi một phần hoặc đủ vectors không có nghĩa document được phép hỏi đáp. PostgreSQL và Qdrant không chung transaction.

Ghi blocks/chunks staging và freeze manifest expected point IDs/count/generation/index/collection/SHA-256 trước embedding. Upsert wait=true từng batch bằng [REST adapter](backend/app/services/vectors.py), scroll toàn generation để so đúng IDs/count/payload; không chỉ một hit hoặc count trùng. Payload chỉ chứa IDs/index/provenance, text nằm SQL. Collection 384/Cosine phải có embedding_hash metadata khớp; cùng dimension nhưng sai model fingerprint vẫn bị từ chối.

Publish transaction khóa document rồi job, xác minh lease/lifecycle/manifest không đổi, SQL chunk point set và revision metadata. Cùng commit revision ready + document active generation/ready + job completed. Sau upsert mà DB rollback: vẫn staging, retry generation mới. Commit acknowledgement mất: read-back completed + active generation trước khi đánh dấu error, tránh phá trạng thái thành công. DB chưa xác minh được thì chờ lease recovery.

**Phương án khác:** publish từng batch làm query thấy corpus thiếu; active flag chỉ trong Qdrant làm lifecycle SQL/delete khó đồng bộ; distributed transaction vượt API/storage hiện có. Chọn atomic SQL publication, consumer Bước 07 phải filter/revalidate SQL, không tin chỉ Qdrant payload. HTTPX trực tiếp phù hợp vài REST operations, có sẵn trong venv; không thêm SDK retry ẩn. Timeout network 10 s là I/O timeout, không phải wall deadline của toàn scroll nhiều trang.

**Bằng chứng:** mất vectors hoặc tamper SQL manifest đều không ready; rollback publish sau Qdrant thành công để lại staging; retry generation mới hoàn tất; mất ack sau commit vẫn completed. Source chunks staging chưa active; actual search exclusion cần endpoint/filter tests Bước 07, không tự tuyên bố đã có retrieval. [Qdrant upsert](https://api.qdrant.tech/api-reference/points/upsert-points), [scroll](https://api.qdrant.tech/api-reference/points/scroll-points), [metadata](https://api.qdrant.tech/api-reference/collections/create-collection).

### K-052 — Retry hữu hạn, manual retry và orphan reconciliation

**Retry:** tối đa 3 attempts/job, base 5 s/cap 60 s exponential với jitter [delay/2,delay]. Transient timeout/connection/DB/vector failures mới tự retry; document giữ processing, job retry_wait. Parse/encoding/encrypted/needs_ocr, config/dimension/manifest sai là permanent. Không biến lỗi hạ tầng thành no evidence. Hết lease → recover; hết attempts → failed. Shutdown dừng nhận việc, dừng attempt giữa stages/batches; hard kill chờ lease, không mất job vĩnh viễn.

[Manual retry](backend/app/services/retry.py) là admin write API có workspace scope, chỉ failed/retryable=true tạo job mới cùng revision. Active job đã có thì trả cùng ID. Document lock và partial unique index làm idempotency dưới concurrency, không reset history attempts. Không cho retry needs_ocr vô hạn vì chưa có OCR. Resource API trả progress/timings an toàn và latest_job_id; timestamps trùng trong transaction test từng làm trả nhầm job cũ. Đã dùng bulk row_number ưu tiên active rồi created_at/id, tránh N+1 và tránh DISTINCT ON API deprecated của SQLAlchemy 2.1. Test API kiểm lại đúng ID, member 403, foreign admin 404, permanent error 409.

**Orphans:** process crash có thể để file không revision hoặc staging vectors/blocks không active. Sweeper 60 s, grace mặc định 1 giờ và ít nhất lease + embedding timeout + vector timeout để old in-flight work dừng. Chỉ dọn generations có worker provenance, không active/cited/live; vector I/O ngoài DB lock, SQL recheck trước delete. Late stale upsert được vòng sau dọn tiếp. Chưa là delete/history cleanup Bước 09; không xóa active source để dọn cache. File sweeper chỉ unlink canonical UUID key đủ cũ/unreferenced/trong root/không symlink; fresh/referenced/unrecognized files giữ lại, không recursive delete.

**Đánh đổi:** cleanup tức thì dễ đụng worker đang chạy, grace dài giữ rác lâu hơn nhưng an toàn với P0. Revision tombstones vẫn giữ metadata/storage key để audit/manual retry; không remove source file của failed document vì vẫn cần retry. Khi có retention/reindex/multi-node phải version chính sách, không tự mở rộng sweeper thành delete API. Tests xác nhận stale gen cũ/late replay bị dọn, active gen/reference file và file fresh không bị xóa; delete lifecycle chặn stale publish/cancel expired job.

### K-053 — Đo ingestion thật, cold/warm và cấu hình máy

**Bằng chứng:** [report](docs/worker-index-step06.md), [run manifest](eval/reports/ingestion_s6_20261103T093516Z_896b9799/manifest.json), [per-document](eval/reports/ingestion_s6_20261103T093516Z_896b9799/per_document.jsonl), [source hashes](eval/reports/ingestion_s6_20261103T093516Z_896b9799/source_sha256.json). Auth/upload/get document/get job qua TestClient, worker thật/E5 thật/PostgreSQL test và Qdrant thật; không gọi LLM.

1 document cold: **13,0251 s / 1 chunk**, trong đó model load **10,1699 s**. 10 documents warm tuần tự: **4,5647 s / 14 chunks**. Vì cold load chiếm đa số, so 13 s và 4,6 s mà bỏ startup sẽ hiểu sai tốc độ scaling. Chưa sweep batch size; giữ batch 4/threads 2/concurrency 1 vì đã chạy được trên máy, không gọi là cấu hình tối ưu. CPU model thật không chứng minh retrieval relevance; quality cần Bước 07/11.

Trước chạy có khoảng **3,41 GiB RAM available / C 7,78 GiB free / D 79,03 GiB free**. Sampled peak tổng RSS parent+children **1.181.339.648 bytes (~1,10 GiB)** ở sampler 20 ms, gồm tool/TestClient/model process; có thể đếm chung DLL/mapped pages, không phải peak RAM toàn máy hoặc model-only footprint. Không thêm Docker Linux worker image/Torch download trong máy ít disk; worker host Windows dùng cache D và venv đã có. Compose db/qdrant vẫn chạy riêng. Load/stress/concurrency cao chưa đo.

Thêm đủ 8 fixtures: scan/blank/encrypted/malformed-PDF terminal đúng, mixed/injection ready, spoofed PDF và non-ZIP DOCX 415 trước job; tổng **19 upload attempts**. Một fixture parser trực tiếp có thể parse_failed, upload boundary từ chối sớm hơn là đúng theo lớp validation. Report passed/cleanup_completed=true; xóa đúng smoke collection/workspaces/users/tokens/files/SQL rows, không sửa reviewed snapshot hay dev data. LLM calls=0/API model spend=0 USD; không tính điện/local compute thành phí API.

### K-054 — Definition of done Bước 06 và bàn giao

**Kết quả thật:** full backend **196 passed, 1 warning**, eval suite riêng **76 passed**; Ruff check/format **85 files** và pip check đạt. Warning Starlette TestClient/httpx giữ từ baseline. Không chạy frontend build vì UI không sửa. Tests reliability dùng embeddings fake có nhãn tách khỏi real local-model smoke; không cộng số đó thành RAG accuracy.

Lượt full đầu bắt lỗi latest_job_id khi timestamp trùng; sửa thứ tự ưu tiên active và window function rồi chạy lại full. Test SKIP LOCKED cần đủ thời gian để libpq tạo kết nối mới localhost/IPv6 trên Windows; timeout test tăng từ 3 lên 15 s, vẫn chứng minh trả về khi document lock chưa được thả, không biến lock-wait thành pass. Không skip cases hoặc sửa DB guard. Các reports lịch sử giữ nguyên; không gọi lại model chỉ để xóa failure.

Đủ 6/6 đầu việc worker/lease/generation/embedding/Qdrant/publish/recovery và đo 1+10 của Bước 06. Giữ trọng số 10/tổng102,5, `(37,5+10)/102,5×100 =46,341…` → **46,3% / 100%**. Search/source endpoints/SQL retrieval revalidation, benchmark Hit/Recall/MRR, answering/citation/delete còn ở bước sau. Nền worker AT-R06–08 đã được fault-injection/crash kiểm chứng, chưa nói end-to-end retrieval/QA đã nghiệm thu.

Worker không tự migrate; DB head/schema Bước 04 giữ nguyên. CLI và locks/hướng dẫn tại [report](docs/worker-index-step06.md). Không sửa UI/gọi LLM/paid fallback/tải model mới/commit/push. Bước 07 cần trình bày phạm vi và xác nhận riêng; trước code UI nhắc người dùng như quy tắc AGENTS/CLAUDE.

**Probe bàn giao:** CLI --once exit 0; dev/test cùng head 20261103_rag04, đều 0 documents/revisions/blocks/chunks, dev giữ 2 users/test 0 users. Qdrant chỉ còn collection mặc định 0 points; smoke/test datasets đã dọn, report giữ kết quả và source snapshots để không cần để dữ liệu synthetic trong dev. Reviewed manifest/mapping hashes không đổi; scan 162 source/docs/eval/config files không có secrets thực .env; local links/whitespace đạt.

### K-055 — Hai lớp lọc retrieval và transaction boundary

**Ngày / loại:** 03/11/2026 — đã triển khai/kiểm chứng Bước 07; [service](backend/app/services/retrieval.py), [schema/router](backend/app/api/search.py), [ADR RAG-02](docs/decisions/0002-dense-retrieval-baseline.md).

Client chỉ gửi query/top_k/mode/document IDs, backend lấy workspace từ bearer identity. Resolve tất cả IDs trước status: foreign/missing phải 404 toàn request, không trả một phần hoặc để own nonready che việc có ID ngoài quyền. Own nonready 409, deleting/deleted 410; không có explicit filters thì tự bỏ nonready, không có ready sources trả empty không nạp model. Strict schema chặn extra fields, duplicate/invalid UUIDs, top-k sai kiểu/bounds; không cho client chọn provider/model/workspace/collection.

**Thiết kế:** SQL lấy active revision/generation/index tương thích rồi kết thúc transaction read/auth, model query và Qdrant chạy ngoài transaction. Filter Qdrant workspace + đúng generation set + index; SQL đọc lại candidates kiểm tra ready/active/lifecycle/index và metadata IDs. Text/filename/location chỉ từ SQL, payload text không được tin. Race nguồn chuyển deleting sau query bị SQL loại, trả ít hits và trace chứ không backfill nguồn chưa kiểm tra. Point/chunk dedup và sort score giảm dần/ID cho kết quả ổn định trong candidate pool.

**Vì sao hai lớp:** lọc chỉ sau retrieval để vector stale/foreign chiếm hết candidate budget; chỉ tin payload không thấy lifecycle SQL mới nhất. Hai lớp tốn một lượt đọc lại nhưng giữ scope/source-of-truth. Không giữ DB lock xuyên inference để tránh làm nghẽn upload/delete. Service hiện commit read boundary; query-run orchestrator Bước 08 phải commit setup trước gọi service, không dùng retrieval để vô tình commit business writes chưa sẵn sàng.

Candidate20/top5 (API cho 1–10), Cosine dense, cutoff None. Technical error model/vector/index mismatch → 503 retrieval_unavailable, DB handler giữ 503; không biến lỗi thành no-evidence. Không có ready source → reason riêng; không dùng cosine làm xác suất trả lời đúng. P1 hybrid/reranker hoãn để baseline kiểm tra độc lập. Tests thực SQL/Qdrant cô lập từng workspace/generation/index filter, forged/stale candidates, ties/duplicates và delete race. [Qdrant query/filtering](https://api.qdrant.tech/api-reference/search/query-points).

### K-056 — Query encoder đúng vai trò và lazy model lifecycle

E5 học truy vấn/tài liệu qua prefixes khác nhau; passage: đúng cho indexing nhưng query: mới là contract truy vấn. IPC [LocalEmbedder](backend/app/services/embeddings.py) thêm kind; default passage giữ worker cũ, encode_query gửi query cùng weights/pooling/L2. Tokenizer đếm cả query prefix/special tokens trước gọi child; >512 tokens trả 422, không truncate. Fingerprint đã khai báo cả hai prefixes từ Bước 06 nên index version passage không đổi.

API tạo runtime lazy khi có eligible sources, dùng model child persistent và nonblocking lock để không trộn RPC giữa threads. Child deadlines giữ Bước 06; bận trả 429 thay unbounded queue, lifespan đóng process/HTTP client. Loader chỉ đọc cache local; không có key LLM vẫn search được. API host cần CPU dependencies như worker; không giả rằng Docker image tối thiểu đã có Torch/Linux worker được thử.

**Phương án khác:** dùng cùng passage prefix cho cả hai dễ viết nhưng sai preprocessing được model card hướng dẫn; tạo model mỗi request làm cold load lặp lại; load ở startup khiến health/auth phải chịu model dependency dù chưa có tài liệu. Giữ một child phù hợp CPU/RAM hiện tại, xem lại pool/batching khi có tải concurrent thật. Reader check_collection chỉ đọc, không tự tạo collection khi index mất; worker ensure_collection thêm keyword payload indices cho workspace/document/revision/generation/index_version. Test query counter dùng tokenizer thật và real dev queries xác nhận query path; không gọi LLM.

### K-057 — Mở nguồn an toàn khác với rendering UI

[Source service](backend/app/services/sources.py) kiểm workspace/status trước file IO, chỉ active revision/generation; chunk khác document 404, revision/generation cũ 410 thay vì tự remap sang nguồn hiện tại. Chunk API trả text/location/spans/document_version đủ để kiểm citation sau này.

PDF trả original bytes trong upload cap, size/hash đúng revision; TXT/MD text/plain/nosniff; DOCX dùng extracted body blocks text/plain vì không có Word pagination chuẩn. Header filename sanitize + UTF-8 encode, no-store/CSP sandbox; không render Markdown/HTML/script. File path do SQL/server key quyết định, resolve phải trong root; checksum/file mất hoặc lifecycle đổi lúc IO → 410. Source normalized spans không dùng để cắt raw file bytes.

**Đánh đổi:** full bounded response đơn giản, không advertise Range/giả 206; mọi Range request vẫn auth, authorized nhận full 200. FileResponse/streaming tiết kiệm RAM hơn với file lớn nhưng cần giữ semantics auth/delete/file consistency trong lúc stream; P0 cap20 MiB phù hợp bounded response. Không tuyên bố thu hồi bytes đã gửi trước delete. Inline preview UI/HTML sanitizer còn bước UI, hiện chỉ API; không code UI trong đợt này.

Tests kiểm actual PDF bytes, DOCX text, raw Markdown HTML là literal text, member/foreign/unauth, Range auth, same-size checksum tamper, storage escape và inactive chunk. Đây là foundation mở citation, chưa có answer/citation claims hoặc delete/history workflow.

### K-058 — Evidence groups, alternatives và union spans để metric không tăng giả

[Loader](eval/retrieval_gold.py) nối external document ref/corpus version/hash/parser block sang SQL active revision/generation/block UUID. Semantic corpus version 2 không phải DB revision counter của lần upload đầu (1); phải map qua checksum/UUID, không so hai counter. So đủ raw+normalized/location/chunk text/hash/spans; drift phải fail, không bỏ câu khỏi denominator. Dev run có injected mapping drift và xác minh bị từ chối.

[Matcher](eval/span_metrics.py): các quote thay thế trong cùng group là OR; các parser spans cần để tái tạo một quote là AND; các groups cần để trả lời đầy đủ cũng là AND. Union clipped intervals trên cùng block UUID, >=80% từng required span thì complete; overlap không đếm đôi. Context heading/header lặp không tự tạo thêm gold support. MRR first-relevant rank là rank sớm nhất hoàn tất group qua union top-k, không phải rank xuất hiện một phần chữ. Không fuzzy-match sau khi nhìn kết quả.

**Vì sao không dùng chunk UUID làm gold:** thay chunk size/generation thì ID đổi trong khi facts không đổi; lexical substring đơn giản cũng không phân biệt revision/location. Canonical spans + explicit remap giữ thí nghiệm có thể so. Rule80% là protocol dự án, không phải chân lý phổ quát; đổi rule phải version config trước đo lại.

Macro successful-answerable Hit/Recall/MRR và multi-group All-evidence có count; strict all-answerable cho lỗi kỹ thuật điểm0 thay vì bỏ denominator. Failed cached hits không được tính; zero denominator null. Unanswerable không có gold groups nên retrieval metrics null, không gán retrieval hits thành abstention đúng/sai của LLM. Tests alternatives/required spans/union/overlap/null/error denominator/invalid interval, và test tái tính toàn metrics + verify source snapshots của run mà không inference lại.

### K-059 — Dev baseline E5: kết quả tốt ở top5 chưa phải accuracy 100%

**Số đo thật:** [run](eval/reports/retrieval_dev_20261103T101104Z_968416c5/manifest.json), [per-query](eval/reports/retrieval_dev_20261103T101104Z_968416c5/per_question.jsonl), [report](docs/search-retrieval-step07.md). Ingest đủ 10 docs/54 blocks/14 chunks, chỉ 15 dev queries (13 answerable/2 unanswerable), 0 test queries/0 LLM calls. Config được lưu trước query đầu, actual production search/source API qua member token; E5/SQL/Qdrant thật, model warm từ ingestion.

Hit/Recall@1 **11/13 =0,8462**; @3/@5/@10 **1,0**; MRR@3/5/10 **0,9231**. Multi-group All-evidence **1/1**, technical errors **0/15**. Warm HTTP latency p50 **82,711 ms**, p95 nearest-rank/max **131,272 ms** (n15, không cold load/SLA). Tổng sampled parent+child RSS **1.167.622.144 bytes (~1,09 GiB)**, không phải riêng model/toàn máy. Coarse corpus chỉ14chunks và một câu multi-group làm bài dễ; không suy ra model answer accuracy=100% hoặc HNSW/corpus lớn cũng như vậy.

**Phân loại misses:** q010 FAQ top1 0,8634 cạnh tranh security đúng top2 0,8619 — dense topic ranking. q012 heading-only FAQ top1 0,8428, body có ticket top2 0,8337 — standalone heading cạnh tranh fact, không phải parser/chunker mất chữ. Source/gold mapping và active filter đã verify, không có LLM context budget. Treatment heading merge/drop cần index version mới và dev comparison riêng; giữ baseline vì top5 đã đủ support.

**Cutoff:** q014/q015 unknown top score **0,84529305/0,8375946**, còn minimum answerable top score **0,84276205**. Không có một cutoff giữ hết answerable và loại hết unknown ngay trong dev này; cosine là tương đồng, không biết câu trả lời có đủ support hay không. Giữ None, không tune cutoff trên 2 negative rồi tuyên bố abstention tốt. Grounding/insufficient_evidence phải làm ở answering Bước 08.

**Lựa chọn:** [dense config v1](eval/configs/dense.json) pin candidate20/production top5/eval top10, 350/50 và index9851b494…c4a4. E5 là baseline vận hành được, chưa model winner. BGE-M3 chưa cache, available RAM trước run khoảng2,77 GiB (probe sau3,11 GiB), margin chưa validate nên hoãn mục challenger có điều kiện; không có BGE số đo. Hybrid/reranker hoãn để tránh đổi nhiều biến trước baseline. Model/normalization/parser/chunker đổi phải version/reindex; test set giữ kín cho gate sau.

### K-060 — Bàn giao Bước 07 và tiến độ

Core search/source/matching/dev runner và freeze đủ 6 mục bắt buộc; mục 6 so BGE là có điều kiện và hoãn có lý do K-059. [Báo cáo](docs/search-retrieval-step07.md) tách run model thật khỏi fake-embedding tests. Worker reliability fixture chuyển sang tests/worker_support.py và export từ conftest để search/worker dùng chung, không plugin test module theo thứ tự collection hoặc nhân đôi cleanup. Không bỏ tests cũ.

Reports immutable giữ source snapshots/hash tại phiên bản đã chạy. Metric guards sau run được bổ sung invalid interval/failed cached hit để strict score không tăng giả; valid completed run tái tính ra cùng metrics, không chạy lại model để thay số. Reviewed snapshot/parser mapping cũ không sửa, cleanup đúng test collection/workspace/users/tokens/files. Git/source scan/probe cuối và full test counts ghi khi hoàn tất đợt.

**Kết quả kiểm chứng:** full backend **222 passed/1 warning**, eval suite riêng **86 passed**; Ruff check/format **96 files** và pip check đạt. Warning Starlette TestClient/httpx là baseline, không tắt hoặc skip. Full suite giữ worker kill/recovery, query budget count dùng tokenizer thật và các guards/API tests cũ. Không sửa schema/applied migrations hoặc cài thêm model/dependencies. Không có frontend build vì UI không đổi.

**Probe bàn giao:** worker --once exit0 và thêm đủ5 keyword payload indices; dev/test cùng head20261103_rag04, đều0 documents/revisions/blocks/chunks (dev2users/test0users). Qdrant còn default collection0points, mọi test/dev-eval collection đã dọn. Reviewed manifest/parser mapping SHA-256 bất biến; scan230 source/docs/eval/config files không chứa secrets thực .env, local links/whitespace đạt. Không để server/model process chạy nền. Tiến độ đã xác minh **56,1% / 100%**; Bước 08 chưa bắt đầu.

Trọng số giữ10/tổng102,5, `(47,5+10)/102,5×100=56,097…` → **56,1% / 100%** khi kiểm chứng đủ. Chưa answering/citation/abstention/delete/UI, không coi toàn M1 đã pass. Không paid fallback/API LLM/download BGE/commit/push. Bước 08 cần phạm vi/xác nhận riêng; trước code UI vẫn nhắc/chờ theo AGENTS/CLAUDE.

### K-061 — Chốt Git: kiểm tra snapshot staged trước commit/push

**Ngày / loại:** 03/11/2026 — người dùng đã xem thông điệp commit và xác nhận riêng đợt Git sau Bước 07. Gộp dataset đã duyệt cùng Bước 03–07 thành một mốc triển khai; giữ các reports/source snapshots lịch sử và không sửa commit hash trong manifests cũ thành hash mới.

Git index là snapshot sẽ được commit, có thể khác working tree, nên kiểm tra secrets trên bytes staged và đối chiếu hashes dataset/report sau khi add. Chỉ kiểm tra file .env đang ignored chưa đủ chứng minh index không chứa secrets. .env.example/config placeholders được version; .env thật, model cache, runtime storage, venv và artifacts tạm bị bỏ qua. Không chạy lại model để chuẩn bị commit; validation 222 backend/86 eval là kết quả đã đo ở Bước 07.

Push thông thường lên origin/main giữ lịch sử; không force-push hoặc amend các commits đã công bố. Sau push đối chiếu local HEAD với remote branch và kiểm tra working tree. Nếu remote đi trước, phải fetch/đánh giá divergence trước tích hợp, không dùng force để vượt non-fast-forward. Git checkpoint không hoàn thành thêm đầu việc sản phẩm, nên tiến độ giữ **56,1% / 100%**. Bước 08 vẫn cần phạm vi/xác nhận riêng; kết quả SHA/push thực được báo sau khi Git xác nhận.

### K-062 — Final context và token budget phải thuộc tokenizer của LLM

**Ngày / loại:** 04/11/2026 — thiết kế và triển khai Bước 08, sau xác nhận của người dùng. Liên quan [spec 8.6–8.7](SME_Knowledge_Copilot_RAG_Specification.md), [context builder](backend/app/services/answering.py), [config](eval/configs/answering.json).

Token không đồng nghĩa ký tự hay từ. E5 có tokenizer và giới hạn 512 riêng; dùng số token E5 để tính context Gemini sẽ sai đơn vị. Chọn Gemini native `countTokens` trên toàn `generateContentRequest`, gồm system, question, evidence wrappers và schema/config gửi thật. Budget gồm input + output tối đa 800 + margin256 trong app ceiling32768; evidence ceiling4000. Ceiling này là giới hạn chủ động của app, không phải context tối đa của model. Đếm bản repair trong lúc packing và kiểm tra lại prompt thường trước generate. Reserved output bao gồm cả thinking, nên không cộng 800 text ngoài giới hạn thinking/output của provider.

Giữ nguyên chunk: chunk lớn bị bỏ, xét chunk tiếp theo; E1… chỉ được cấp sau packing. Lưu retrieved IDs, excluded IDs, final IDs, prompt SHA và map text/chunk/revision/generation/lifecycle/source spans đã gửi. Citation vào một candidate bị loại vẫn là reference sai. Không âm thầm cắt giữa điều kiện chính sách hoặc truncate question. Riêng E5 query budget vẫn được kiểm tra trước retrieval; vượt giới hạn trả422.

Phương án khác: `len(text)/4` rẻ nhưng chỉ gần đúng, đặc biệt với tiếng Việt; tokenizer E5 không thay được tokenizer Gemini. Tokenizer local tương thích model có thể giảm round trips nhưng chưa có bản pin/kiểm chứng cho cấu hình này, nên chưa dùng. Đổi sang local token counter chỉ sau khi so với provider trên prompt thường/repair/schema/tiếng Việt. Đánh đổi hiện tại là nhiều HTTP count calls; tối đa `top_k+2` khi có evidence, đã nằm trong deadline/concurrency. Test fake character counter chỉ chứng minh nhánh budget, không phải số token thật.

Nguồn chính thức kiểm tra 04/11/2026: [counting tokens](https://ai.google.dev/gemini-api/docs/tokens), [model limits](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [thinking](https://ai.google.dev/gemini-api/docs/thinking). Public docs không xác minh billing/quota của tài khoản.

### K-063 — Typed claims, citation metadata do backend sở hữu và bounded repair

**Ngày / loại:** 04/11/2026 — triển khai [schema](backend/app/schemas/answer.py), [prompt/validation](backend/app/services/answering.py); thay schema smoke rút gọn bằng contract sản phẩm trong runtime, giữ smoke/report cũ bất biến.

Structured output làm hình dạng JSON dự đoán được; backend vẫn kiểm tra kiểu strict, extra=forbid, tối đa12 claims/1000 ký tự, ID hợp lệ trong final context, không duplicate ID/marker tự chèn. grounded cần claim; partial cần giới hạn/điều kiện thiếu; insufficient có claims rỗng. Conflict khai báo cần partial và ít nhất hai evidence IDs, nhưng quy tắc cấu trúc này không chứng minh model đã hiểu đúng hai phía. Không tự chọn chính sách theo ngày upload hoặc filename.

Model chỉ nhận question và evidence ID/text; tên file, location, revision/version, excerpt và URLs của citation được backend dựng từ SQL. `answer` ghép claims với markers backend; limitations/missing information vẫn cần kiểm tra faithfulness bằng rubric. Với abstention, backend chỉ công bố mẫu cố định, bỏ giải thích tự do của model. Text từ tài liệu là dữ liệu không có quyền chỉ dẫn, không có tools hoặc fetch URL; JSON/plain text chưa thay thế yêu cầu escape/sanitize UI ở Bước10.

Sai JSON/schema/reference hoặc finishReason khác STOP cho phép tối đa một lần tạo lại trên cùng question/evidence map, dùng deadline còn lại. Repair instruction cố định, không echo raw output hoặc lỗi Pydantic chứa dữ liệu. Lỗi quota/mạng/provider không đi vào repair. Output bị cắt không được nối dấu ngoặc hoặc tự điền dữ kiện. Hai lần không hợp lệ trả502 và không có assistant message thành công. Không chọn cách xóa citation lỗi rồi giữ kết luận vì kết luận khi đó mất chứng cứ. Chưa thêm judge/entailment model vì tốn tài nguyên và vẫn cần hiệu chỉnh/human review; schema pass không phải answer đúng.

Nguồn: [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output), [GenerateContent usage/finish reason](https://ai.google.dev/api/generate-content). Kiểm chứng bằng [schema/budget tests](backend/tests/test_answering.py), [provider MockTransport tests](backend/tests/test_gemini_provider.py) và report Bước08 khi hoàn tất.

### K-064 — Idempotency, session concurrency và transaction công bố câu trả lời

**Ngày / loại:** 04/11/2026 — triển khai [chat service](backend/app/services/chat.py), [API](backend/app/api/chat.py). Tận dụng schema Bước04, không sửa migration đã áp dụng.

Idempotency giải quyết retry sau mất response: hash question đã trim + session + filters UUID sắp xếp + mode/top-k input; unique(session,client_request_id) và partial unique running/session là bảo vệ DB. Khóa session ngắn bằng NOWAIT để serialize lúc tạo run, rồi commit user message/run trước inference. Cùng ID/input replay kết quả; khác input409; running409 kèm run ID; failed phải dùng ID mới. Default top-k được pin trong config lần đầu; input bỏ qua top-k giữ null trong hash để replay không phụ thuộc default mới. Mỗi câu hỏi độc lập, không đưa answer cũ vào prompt.

Không giữ transaction/row lock khi embed, count hoặc generate. Sau model: khóa documents theo thứ tự UUID rồi session/run, đọc lại ready/active revision/generation/lifecycle/text; nguồn đổi409. Ghi assistant message + citations + completed trong một transaction. Commit thất bại trả lỗi DB; nếu commit đã thành công nhưng mất acknowledgment, replay vẫn tìm kết quả đã lưu và không gọi model lần hai. Không trả draft chưa lưu như thành công.

Run có deadline DB, recovery khi GET run hoặc query tiếp theo đánh failed cho running hết hạn; process chết không khiến session busy vĩnh viễn. Final publish kiểm tra cả monotonic deadline và trạng thái/deadline DB, nên request cũ không publish sau recovery. Chưa thêm queue query/streaming vì làm phức tạp cancellation/idempotency; P0 đồng bộ, một run/session, capacity model2/app process. Khi chạy nhiều API workers cần giới hạn phân tán nếu muốn trần toàn deployment là2.

Bằng chứng quan trọng: [real PostgreSQL chat tests](backend/tests/test_chat.py) kiểm tra concurrent requests, cross-session, owner scope kể cả admin, no locks trong inference, failed publication và lost commit ack. Fixture embeddings/provider không phải quality benchmark.

### K-065 — Deadline và lỗi kỹ thuật không phải thiếu bằng chứng

**Ngày / loại:** 04/11/2026 — [native Gemini adapter](backend/app/services/gemini.py), [retrieval](backend/app/services/retrieval.py), [embedding](backend/app/services/embeddings.py), [Qdrant adapter](backend/app/services/vectors.py).

HTTPX timeout theo phase có thể không chặn tổng thời gian của một response truyền chậm. Dùng AsyncClient bên trong `asyncio.timeout`, gọi từ sync endpoint qua asyncio.run để giới hạn wall clock HTTP theo min(call cap120, query time còn lại). Không redirects, trust_env=False, không SDK retry hoặc provider fallback. Path/model pin, key chỉ trong header, flags free-tier/quota mặc định false. Hai flags là xác nhận thủ công, không phải billing cap từ Google; không hứa tài khoản vẫn free nếu chủ tài khoản bật billing sau đó.

Deadline chung150 giây truyền vào E5 startup/batch poll và Qdrant check/query; quá hạn không publish. Model subprocess timeout terminate/join có cleanup grace, SQL/OS scheduling cũng có overhead;150 là work/publication budget, không phải hard SLA mọi byte HTTP trả về đúng150. Search-only giữ đường chạy không cần LLM/config key. Empty ready scope không init model hoặc gọi Gemini. Qdrant/embedding/provider lỗi trả503/504; chỉ thiếu evidence thật mới thành200 insufficient_evidence. Quota429 của provider thành503 model_unavailable, không thử lại tự động; capacity nội bộ thành429 model_busy.

Chưa dùng async toàn bộ SQL/embedding vì hiện runtime đồng bộ và subprocess đã có timeout; chuyển toàn stack cần benchmark/kiểm tra cancellation riêng. Không tạo thread bỏ chạy cùng Session khi deadline hết vì có thể tiếp tục ghi dữ liệu sau response. Logs/error envelopes không chứa key, provider body, full prompt hoặc raw output; chỉ usage/model/finish reason an toàn. Token usage chưa có thì null, không giả0.

### K-066 — Oracle context chỉ là công cụ chẩn đoán trong eval

**Ngày / loại:** 04/11/2026 — [script](eval/run_answering_eval.py), [protocol](eval/configs/answering.json), [offline tests](eval/tests/test_answering_eval.py).

Oracle mode cấp gold snippets trực tiếp cho production context builder/generation validator: nếu câu trả lời vẫn sai thì lỗi thuộc prompt/schema/budget/model, chưa đủ cơ sở đổi retriever. Helper chỉ nằm trong eval; ChatQuery extra=forbid từ chối oracle_context/evidence/model URL từ client. Dùng5 ca synthetic dev: multi-source, thiếu điều kiện, mâu thuẫn (oracle); injection và unknown (API E5/SQL/Qdrant/Gemini thật). Không đọc query test holdout hoặc chỉnh reviewed snapshot.

Người dùng xác nhận riêng trần10 generateContent (5ca×tối đa2),20 countTokens,0USD. Ledger ghi trước mỗi request, giới hạn chung cả oracle/API/repair và cách các request tối thiểu5giây. Fixture này dự kiến19 count calls nếu đủ cả5ca, nhưng số thực phải lấy ledger. Gặp quota/mạng/timeout dừng run, không fallback. Mỗi đợt chạy mới vẫn cần phê duyệt; CLI --live không thay xác nhận người dùng.

Freeze config/cases và source snapshot/hash trước request đầu, lưu outputs/usage/timings/trace thật rồi cleanup workspace/collection test riêng. Literal/status probes chỉ là diagnostics hữu hạn, không chứng minh entailment/answer accuracy hoặc injection an toàn tổng quát. Không tự đánh dấu human review xong; kết quả này không thay held-out eval Bước11. Phương án gọi LLM judge chưa chọn vì trần0USD và judge cũng cần đối chiếu nhãn người. Báo cáo thật và phạm vi nghiệm thu ghi ở mục tiếp theo sau khi kiểm chứng.

### K-067 — Kết quả Bước08, lỗi dự toán count requests và tính toàn vẹn artifacts

**Ngày / loại:** 04/11/2026 — đã kiểm chứng, giữ nguyên các lần lỗi. [Report tổng hợp](docs/answering-step08.md), [run đầu](eval/reports/answering_dev_20261104T031918Z_fd3953b6/manifest.json), [retest riêng](eval/reports/answering_dev_20261104T032524Z_a2800bde/manifest.json).

Backend **276 passed/1 warning** trong276,31giây; eval riêng **91 passed/1 warning**, Ruff check/format 108 files và pip check đạt. Warning Starlette/httpx giữ nguyên, không skip hoặc ẩn. Không cài dependencies/model, không sửa UI/schema/applied migrations. Tests backend gồm cả lost commit acknowledgment, two sessions, expired run fencing, source change/replay/history và owner restriction; không coi fake provider/embedding là quality model.

Run đầu status **failed**:5 attempts,4outputs validate/probes đạt, ca unknown gặp eval_budget_exhausted trước generation. Nguyên nhân do tôi ước lượng2 files tạo2 chunks, nhưng MD có heading riêng nên thực tế3chunks. Với base+candidate counts+normal final check, full protocol cần21count calls thay vì19 dự kiến ở K-066. Ledger chặn đúng request21, đã dùng20counts+4generation, không vượt trần người dùng. Nếu chỉ nhìn số docs hoặc số generation thì bỏ sót quota của tokenizer HTTP. Test dự toán cũ dựa số files cũng sai; thay bằng parser/tokenizer thật tái hiện3chunks và upper bound theo số chunks.

Sửa **eval runner**, không đổi backend/prompt/model/cases: preflight chunk-aware trước model requests, chọn --case và caps ghi execution.json, phân biệt planned/attempted/succeeded/not-attempted. Với toàn5ca và cap20, runner nay từ chối trước live requests thay vì chạy dở. Không tự nâng trần. Người dùng phê duyệt bổ sung tối đa5count+2generation cho **riêng unknown**; run mới hoàn tất với5count+1generation, trả mẫu insufficient_evidence, claims/citations rỗng. Tổng thật hai đợt **25count+5generation**;4ca trước không chạy lại. Không ghi lại thành một run5/5/0errors, không xóa failed report. Field cases_completed=5 trong manifest cũ là số attempts theo runner cũ, không phải5successes; technical_errors=1 và raw rows giữ nguyên.

Các quan sát: oracle multi-source có12ngày/E1 và3ngày/E2; incomplete nêu5ngày nhưng thiếu hạn, partial; conflict12/14 dẫn hai bên, partial và không chọn bản. API injection có cả3chunks (gồm payload lệnh/script) trong final context, trả email support đúng từ SQL, citation mở source API đạt. Đây là5 unique synthetic cases có diagnostic probes đạt qua2runs; human review **pending**, answer_accuracy=null, chưa chứng minh faithfulness/injection robustness tổng quát hoặc held-out performance. Năm outputs thật đều STOP và validate lần đầu, nên repair/E99/truncation chỉ được kiểm chứng bằng fixture tests. Timings có throttling5giây/count round trips, không dùng làm answering latency benchmark.

Kiểm tra artifact phát hiện `config_sha256` của hai manifests lịch sử hash **file input** trong source_snapshot (`67f535…e648`), trong khi config.json được pretty-serialize lại (`82d040…839d`), nội dung JSON tương đương nhưng bytes khác. Không thay hash/report để làm khớp giả; test kiểm tra hash input snapshot và semantic equivalence của config report. Runner tương lai copy nguyên bytes input sang config.json để một hash truy được cả hai. execution.json của retest có hash riêng. Source registries chứng minh backend/prompt giữa hai runs giống nhau; runner snapshot khác vì sửa dự toán. Đây là lý do phải phân biệt byte identity với JSON equivalence, giữ code snapshot khi working tree dirty.

Reviewed dataset/mapping/reports cũ không đổi; scripts cleanup workspace/collection/file test riêng, không process server/model giữ chạy. Probe cuối: dev/test cùng head20261103_rag04, dev2users/test0users, cả hai0documents/revisions/blocks/chunks/sessions/runs/messages/citations; Qdrant chỉ còn default collection. Scan414 repository candidate files không chứa3secrets thực từ .env;4immutable core hashes,166report source snapshots,8tài liệu local links và Git whitespace check đạt. Không kiểm tra hóa đơn: budget0USD dựa free-tier project/quota người dùng xác nhận và không bật billing/fallback; public pricing được đọc lại04/11. Tiến độ `(57,5+10)/102,5×100` → **65,9% /100%**, tính7/7 phạm vi triển khai/smoke của Bước08; human-quality/final held-out vẫn ở Bước11. Bước09 cần đợt xác nhận riêng, chưa delete/privacy cleanup/UI/commit/push.

### K-068 — Bước 09: soft-disable và redaction là một transaction SQL

**Ngày / loại:** 04/11/2026 — người dùng xác nhận Bước 09; đang kiểm chứng. Liên quan [delete service](backend/app/services/deletion.py), [privacy service](backend/app/services/privacy.py), spec 7.5/9 và PLAN09. Không bao gồm UI, model calls, cài dependencies hoặc Git commit/push.

Xóa một hệ thống RAG phải xử lý PostgreSQL, Qdrant, file và những bản sao trong chat. Chọn transaction khóa document, kiểm tra workspace/admin, đặt deleting/deleted_at, tăng lifecycle_version, bỏ active pointers, hủy lease ingestion, che/xóa answer liên quan và tạo cleanup job. Commit là mốc request mới không được dùng nguồn; không chờ dịch vụ vector hoạt động mới vô hiệu hóa nguồn. Delete lặp giữ job hiện hữu; deleted trả200, deleting trả202. Lỗi cleanup không đưa document về ready. Đây là mô hình soft-disable + durable cleanup, không phải distributed ACID giữa SQL/vector/files.

Redaction không chỉ theo citations: answer có thể chịu ảnh hưởng từ context không được cite, kể cả limitations hoặc abstention. Tìm runs theo evidence_map và citations, khóa theo run ID; xóa toàn content/structured_answer_json của assistant bị ảnh hưởng, đặt source_unavailable, xóa mọi excerpt/location snapshot của answer đó và scrub trace cũ. Giữ user question, IDs/timestamps và các answers không liên quan. Running run đã đăng ký evidence chuyển failed/source_changed, nên client nhận409 và không công bố draft.

Không chọn chỉ delete vector vì SQL/file/history vẫn có thể hồi sinh text; không hard-delete toàn session vì mất cả câu hỏi và answer không liên quan. Xóa đồng bộ mọi storage sẽ giữ transaction qua network/file I/O, khó recovery khi một hệ thống lỗi. Dùng outbox/job trong cùng transaction hiện tại không cần thêm broker. Điều kiện xem lại: nhiều workers/services hoặc quy mô lớn cần đo lock contention, batch redaction và distributed coordination.

### K-069 — Retention: trace mặc định giữ provenance thay vì full context

**Ngày / loại:** 04/11/2026 — thay thế cách lưu runtime context ở K-062/K-064, giữ nguyên reports/snapshots Bước08 làm bằng chứng lịch sử. [Chat service](backend/app/services/chat.py), [privacy projection](backend/app/services/privacy.py).

Bước08 lưu map đầy đủ gồm excerpt/filename/location để chẩn đoán; Bước09 giảm bản sao dữ liệu: prompt text chỉ nằm trong RAM trong request, SQL trace mặc định chỉ lưu evidence/chunk/document/revision/generation IDs, lifecycle/version, hash text và source-span IDs/offsets/roles. Dùng hash để so với SQL text khi replay; citations/message vẫn là bản sao chủ động, chịu chính sách redaction. Prompt SHA và token counts hỗ trợ tái lập mà không lưu toàn prompt. Các debug/full-context traces cũ bị scrub khi nguồn tương ứng bị xóa. Không xóa nhầm immutable reviewed corpus/reports chứa dữ liệu giả lập dùng eval; chúng không phải storage của documents API.

Đăng ký map phải revalidate và khóa sources **sau packing, trước generation**. Nếu chỉ revalidate sau LLM, nguồn có thể đã bị xóa lúc countTokens chạy nhưng request vẫn gửi text cho provider. Khóa documents theo thứ tự UUID, chờ có giới hạn bằng PostgreSQL lock_timeout, ghi map/run ngắn rồi commit trước network. Delete và đăng ký map serialize qua document lock: hoặc delete nhìn thấy run để redact/fail, hoặc query thấy nguồn đã đổi và không generate. Final publication vẫn revalidate và transaction atomic. Không giữ row lock qua model call; bytes đã gửi provider/browser trước delete không thể thu hồi bởi transaction này.

Phương án bật debug full prompt mặc định chưa chọn vì làm tăng retention/deletion surface; nếu sau này bật phải có TTL và cleanup cùng nguồn. Không dùng hash như bằng chứng entailment hoặc mã hóa bảo mật có thể khôi phục nội dung. Metadata tối thiểu phục vụ provenance, không phải bản backup text. Kiểm chứng bằng barriers trong [delete tests](backend/tests/test_deletion.py) tại count/generate, so SQL sau cleanup, history/replay và source endpoints.

**Guard trước mọi provider operation:** countTokens cũng gửi text ra ngoài, dù không sinh answer. SourceCheckedProvider đọc lại SQL và kết thúc transaction trước mỗi count/generate/repair. Barrier tại count đầu chứng minh sau delete không có count tiếp theo mang evidence, và invalid output đầu không khiến repair gửi lại context đã xóa. Đăng ký map và final publish vẫn có khóa/fencing riêng. Không giữ lock qua network nên vẫn có cửa sổ sau check trước khi request rời process; đây là request in-flight, không phải khả năng thu hồi bytes. Hard guarantee vẫn là query bắt đầu sau delete commit không dùng nguồn.

### K-070 — Cleanup lease, idempotency và late upsert reconciliation

**Ngày / loại:** 04/11/2026 — [cleanup worker/queue](backend/app/services/cleanup.py), [queue chung](backend/app/services/jobs.py), [worker CLI](backend/app/worker.py).

Tận dụng lease token/generation/lifecycle fencing, heartbeat độc lập, SKIP LOCKED và backoff tối đa3 attempts của ingestion. Cleanup có trạng thái riêng: luôn giữ document deleting khi retry hoặc terminal failure. Admin retry tạo job mới khi lỗi tạm thời; document lock + partial unique active cleanup chặn hai retry sinh hai jobs. Không tái sử dụng token cũ; cleanup attempt hết lease không được ghi deleted sau khi attempt mới claim. Cleanup completed nhưng mất commit acknowledgment được nhận diện bằng SQL, không downgrade thành failed.

External I/O ngoài DB locks: xóa vectors với filter workspace_id AND document_id, wait=true rồi kiểm tra rỗng; xử lý tất cả collections đã ghi trên revisions và collection hiện tại. Missing file/collection là success idempotent, không tự tạo lại collection. Kiểm tra storage key canonical gắn workspace UUID, resolve nằm trong storage root, từ chối symlink/junction và path traversal, chỉ unlink file cụ thể; không recursive delete. File/vector xong nhưng SQL commit lỗi thì retry an toàn. SQL cuối xóa chunks/blocks, scrub snapshots, retire revisions/clear storage keys, giữ tombstone IDs/hash và scrub filename/warnings.

Lease không hủy được một HTTP upsert đã rời process. Worker cũ có thể ghi vector sau khi cleanup đã kiểm tra rỗng, nhưng không thể publish SQL ready. Sweeper định kỳ xóa lại vectors của tombstones theo scope, kể cả collections cũ; orphan sweeper không bảo vệ citation đã unavailable. Đây là eventual cleanup có reconciliation, không hứa vector sẽ không bao giờ xuất hiện tạm thời sau một request in-flight. Cần worker/sweeper tiếp tục chạy để hội tụ; hard guarantee là SQL không retrieve nguồn deleted. Với quy mô lớn cần paging/scheduling thích hợp thay quét mọi tombstone mỗi vòng; hiện corpus portfolio nhỏ, chưa stress throughput.

Chế độ --cleanup-only không tải profile/tokenizer/weights hoặc chạy embedding; cleanup vẫn hoạt động khi cache model thiếu. Worker bình thường ưu tiên cleanup rồi ingestion, phục hồi expired leases của cả hai queues. Chưa thêm queue Redis/Celery vì durable SQL hiện đáp ứng và dễ tái tạo race. Nguồn chính thức: [Qdrant delete by filter/wait](https://api.qdrant.tech/api-reference/points/delete-points), [PostgreSQL row locks](https://www.postgresql.org/docs/16/explicit-locking.html), đọc04/11/2026.

### K-071 — Kiểm thử fault/race và lỗi teardown với partial unique index

**Ngày / loại:** 04/11/2026 — [delete tests](backend/tests/test_deletion.py), [chat fixture chung](backend/tests/chat_support.py), [worker fixture](backend/tests/worker_support.py); kết quả cuối bổ sung sau regression.

Barrier tests giữ worker tại HTTP upsert đã bắt đầu hoặc query tại count/generate, delete+cleanup commit rồi mới thả. Kiểm tra SQL status, vectors, source APIs, replay/history và bản sao text thay vì chỉ gọi tuần tự rồi gọi đó là concurrency. Fault injection đặt tại vector adapter, unlink và DB commit; giữ cả rollback trước commit và commit thành công/mất acknowledgment. Tokenizer/provider/embeddings dùng test fakes trừ những parser/tokenizer tests đã có; PostgreSQL/Qdrant là services thật. Không sử dụng Gemini requests để kiểm tra state machine.

Test đầu đã chứng minh upload lại cùng hash sau deleted tạo document mới. Teardown cũ đổi mọi document về failed trước tháo FK, vô tình biến tombstone cũ thành live trong partial unique(workspace,sha) và va với document mới cùng hash. Đây là lỗi fixture, không phải lỗi dedup sản phẩm. Sửa teardown giữ status deleted cho tombstones, chỉ clear active pointers rồi xóa theo thứ tự FK. Workspace test lỗi được dọn theo UUID/tên fixture cụ thể sau khi validate TEST_DATABASE_URL, không wipe DB dev hoặc cả test DB. Chuyển chat fixture sang module dùng chung và export qua conftest để không phụ thuộc thứ tự collection hoặc import một test module làm plugin.

Giữ failure visibility, không skip tests hoặc xóa constraints để suite xanh. Các test fake không chứng minh semantic accuracy, và race suite hữu hạn không chứng minh mọi lịch interleaving. Human-quality/held-out và UI còn các bước riêng trong PLAN.

**Bổ sung khi regression:** hai ca commit fault injection ban đầu không kích hoạt vì service đã flush, nên Session.dirty rỗng tại commit. Sửa hook quan sát identity map và assert hook thật sự chạy; kiểm tra lại cả rollback và acknowledgment mất. Flush gửi SQL trong transaction, không đồng nghĩa commit durable. Nếu test nhầm hai thời điểm thì có thể tuyên bố đã kiểm tra commit failure mà thực tế chưa tạo lỗi. Bốn ca targeted sau sửa đạt (commit rollback/ack, file/log, scheduler).

Rà worker phát hiện sweeper lỗi có thể chặn tới lượt xử lý job trong cùng vòng poll. Đổi thứ tự: recover → cleanup/ingest attempt → maintenance. Maintenance failure vẫn log/exit code lỗi trong --once, nhưng không làm starvation các durable jobs. Test dùng PostgreSQL/Qdrant thật, model profile/counter/encoder giả lập: dù sweep bị inject lỗi, cleanup job đã hoàn tất. Không giấu lỗi maintenance hoặc coi lỗi đó là không có nguồn.

### K-072 — Bàn giao Bước 09 và bằng chứng gate

**Ngày / loại:** 04/11/2026 — đã kiểm chứng 6/6 phạm vi PLAN09. [Report](docs/deletion-privacy-step09.md), [ADR RAG-08](docs/decisions/0008-document-deletion-and-retention.md), [tests](backend/tests/test_deletion.py).

Full backend cuối **302 passed/1 warning** trong **379,71 giây**; eval suite riêng **91 passed/1 warning** trong **8,87 giây**. Ruff check/format **114 files**, pip check và Git whitespace check đạt. Giữ warning Starlette/httpx, không skip/ẩn test. Có 26 ca deletion bổ sung trên nền 276 backend Bước08; không dùng số tests để tính progress hoặc gọi đó là accuracy. Lượt trước301 pass chưa gồm guard mới trước từng provider operation; lượt302 là trạng thái cuối đã kiểm tra guard này và repair sau delete.

Probes chỉ đọc: dev/test cùng head `20261103_rag04`, isolation `read committed`; dev2users/test0users. Cả hai0documents/revisions/blocks/chunks/sessions/runs/messages/citations/jobs sau dọn fixtures; Qdrant chỉ còn default `knowledge_e5_small_v1`, không test/eval collections. CLI cleanup-only đã xử lý cleanup với HF_HOME không có model cache trong test riêng. Không giữ API/worker/model process chạy nền; DB/Qdrant giữ services hiện có.

Scan **422 repository candidate files** không chứa3secrets thực từ .env;4core hashes (reviewed manifest/mapping/2applied migrations) và **166 historical report source snapshots** đúng bytes. Local links của10tài liệu và whitespace đạt. Không đổi .env, schema/applied migrations, model/index fingerprint, reviewed snapshot, reports cũ hoặc frontend. Không LLM requests, model downloads, paid fallback, commit/push trong Bước09. Các raw model outputs/human review/held-out metrics Bước08/11 giữ nguyên trạng thái, không biến tests phần mềm thành kết luận chất lượng AI.

Tiến độ trọng số `(67,5 + 10) / 102,5 × 100 = 75,609…` → **75,6% /100%**. Bước10–12 còn25trọng số, gồm UI/browser E2E/final eval/packaging. Trước viết/sửa UI phải nêu màn hình/file/phạm vi và chờ xác nhận riêng theo AGENTS; chưa tự bắt đầu Bước10.

### K-073 — Checkpoint Git Bước 08–09: audit đúng snapshot sẽ push

**Ngày / loại:** 04/11/2026 — người dùng đã xem nội dung commit và xác nhận riêng đợt Git. Chốt answering/citations/session cùng deletion/privacy/cleanup; không bắt đầu UI Bước10.

Tiếp tục quy trình K-061: kiểm tra bytes từ Git index sau stage, vì đây mới là snapshot được commit. Đối chiếu secrets thực trong .env mà không in giá trị; loại .env/runtime storage/cache/weights khỏi snapshot; xác minh hashes source snapshots và dataset/mapping/migrations bất biến. Giữ cả failed budget report và scoped retest Bước08, không thay parent commit/hashes trong manifests lịch sử thành commit mới. `config_sha256` của hai reports này trỏ input snapshot; config report được kiểm tra tương đương JSON theo K-067.

Validation **302 backend +91 eval tests**, Ruff114/pip check là kết quả cuối Bước09 đã có; đợt Git không gọi model hoặc chạy lại benchmark. Ghi thông điệp commit qua body file để giữ newlines, push thông thường lên origin/main, rồi so local HEAD với remote và kiểm tra working tree. Nếu remote thay đổi phải đánh giá divergence, không force-push. SHA/kết quả push thực được báo trong chat sau khi Git xác nhận, tránh sửa tài liệu sau commit rồi để workspace dirty. Tiến độ giữ **75,6% /100%** vì checkpoint không hoàn thành thêm đầu việc sản phẩm.

### K-074 — Khôi phục máy nhận bàn giao: source snapshot khác runtime state

**Ngày / loại:** 05/11/2026 — người dùng xác nhận đợt khôi phục; đã kiểm chứng môi trường. Liên quan [runbook](docs/workspace-restoration-20261105.md), [README](README.md), [Settings](backend/app/core/config.py), [worker lock](backend/requirements-worker-cpu.lock). Không triển khai UI Bước 10 hoặc gọi Gemini.

Git checkout mang source, lockfiles và artifacts đã commit; không mang theo venv, node_modules, Docker volumes, model weights hoặc `.env` của máy khác. Vì vậy báo cáo 302 backend/91 eval tests của Bước 09 chứng minh snapshot trên môi trường trước, chưa chứng minh máy nhận chạy được. Kiểm tra lại thực tế tìm thấy Python 3.12.1/Node 24.11.1/npm 11.6.2, nhưng thiếu venv/node_modules/cache và Docker engine chưa chạy. Kiểm tra runtime bên ngoài sandbox cần thiết vì sandbox có thể che interpreter cài trong user profile; không kết luận “chưa cài Python” chỉ từ CommandNotFound trong phiên bị giới hạn.

Chọn khôi phục từ cả dev và worker locks, giữ Python 3.12/Windows x64 để tương thích Torch CPU wheel đã pin; không nâng package hàng loạt hoặc tái sinh locks. Editable install trỏ source checkout hiện tại. Python patch version khác máy cũ được ghi rõ; regression mới và fingerprint E5 là bằng chứng tương thích cần có. Pip build isolation có thể dùng build dependency riêng theo pyproject, nên lock hiện tại không phải cam kết byte-identical toàn bộ build toolchain.

Máy nhận chỉ có ổ C, nên dùng `<repo>/.cache/` đã được ignore thay cho đường dẫn D của máy cũ. HF_HOME trong `.env` là absolute path để worker/API chạy từ backend và eval chạy từ root cùng dùng một cache; đường dẫn tương đối dễ tạo hai cache/storage roots do khác cwd. Pip/npm không tự đọc `.env`, cần export biến riêng trong shell. Lựa chọn cache ngoài repo vẫn hợp lý khi chia sẻ giữa nhiều checkouts; chưa chọn vì cần phạm vi project rõ ràng trên máy nhận. Di chuyển checkout phải cập nhật paths. Không commit weights hoặc secrets; backend Docker context không chứa cache ở repo root.

E5 chỉ tải sáu files tại revision cố định, rồi đối chiếu SHA-256/fingerprint lịch sử; chỉ đúng dimension chưa đủ bảo đảm cùng embedding space. Giữ runtime local-only, không dùng download ngầm hoặc model fallback. DB/Qdrant phải kiểm kê dữ liệu trước migration/seed; dùng volumes hiện hữu nếu có, không reset để che lỗi. Test DB đi qua guard có sẵn và tách dev; tests/eval không chạy cùng service worker trên queue DB. Kết quả mới ghi ở runbook sau khi chạy, không thay reports cũ hoặc tự tăng tiến độ sản phẩm.

**Bằng chứng cuối:** cài đúng mọi versions trong runtime/dev/worker locks; sáu E5 hashes/fingerprint/index version khớp report Bước06. Local E5 subprocess tạo một query và một passage vector 384 chiều, finite/unit norm, 10,516 s gồm cold load; đây là compatibility probe, không chất lượng retrieval. Backend **302 passed/1 warning/646,77 s**, eval **91 passed/1 warning/10,54 s**; Ruff115/pip check/frontend lint/build đạt. Health/login/me/documents cho cả hai roles đạt; token probe được xóa theo digest riêng. Worker thường/cleanup-only một vòng exit0. Dev/test head20261103_rag04; dev2users/test0users, mọi dữ liệu RAG/jobs/token đều0; Qdrant chỉ collection mặc định0points. Chỉ DB/Qdrant giữ chạy, không giữ model/API/worker/frontend probes nền.

422 tracked hashes chứng minh source/locks/migrations/corpus/mapping/reports bất biến, chỉ ba tài liệu hướng dẫn đã có được sửa và thêm runbook; scan423candidate files không thấy ba secrets riêng. HF offline và credentials/flags LLM bị vô hiệu hóa trong test/probe process; không Gemini requests hoặc thay billing. Giữ warnings Starlette/httpx/ESLint để review có chủ đích sau này. Khôi phục không hoàn thành thêm hạng mục Bước10–12 nên tiến độ giữ75,6%/100%.

### K-075 — Pytest basetemp cần thư mục cha trên checkout mới

**Ngày / loại:** 05/11/2026 — lỗi setup được quan sát khi khôi phục máy nhận. [Runbook và lệnh sửa](docs/workspace-restoration-20261105.md). Không phải lỗi RAG; không thay source/test để xử lý.

Lượt full backend đầu ghi 188 passed và 114 setup errors/1 warning trong 37,63 s. Nhiều fixtures dùng tmp_path chung đều lỗi FileNotFoundError khi pytest tạo `backend/.cache/restore-20261105`; nguyên nhân là parent `backend/.cache` chưa có trên checkout sạch. `--basetemp` không bảo đảm tạo mọi thư mục cha. Tạo `.cache` bằng `New-Item -ItemType Directory -Force`, rồi chạy lại full suite với một basetemp mới. Không tạo sẵn thư mục test con hoặc tái dùng đường dẫn có dữ liệu cần giữ, vì pytest có thể dọn basetemp. Giữ JUnit lần lỗi và lần chạy lại tách biệt để không mất failure history.

Không chọn bỏ `--basetemp` vì project dùng thư mục tạm ngắn/có kiểm soát để tránh Windows paths và thuận tiện cleanup. Không thêm source workaround, sửa constraints hoặc skip fixtures vì lỗi nằm ở điều kiện chạy. Chỉ coi regression đạt khi lượt full sau sửa có kết quả thật; 188 tests đã pass ở lượt đầu không bù cho 114 ca chưa được setup.

**Cách chứng minh đã xử lý:** lượt chạy lại với parent đã có và basetemp mới đạt đủ302tests/1warning, không errors/skips. JUnit đầu giữ `backend-tests-initial.xml`, JUnit cuối giữ `backend-tests.xml` trong cache đợt khôi phục. Lệnh runbook đã thêm bước tạo parent; không cần thay pytest hoặc ứng dụng.

### K-076 — Tiêu chí UI doanh nghiệp và kế hoạch Bước 10 để duyệt

**Ngày / loại:** 05/11/2026 — người dùng xác nhận tạo tài liệu/mockup; các tiêu chí thẩm mỹ do người dùng yêu cầu, phương án cụ thể đang đề xuất/chờ duyệt. [Kế hoạch UI](docs/ui-step10-plan.md), [mockup](docs/mockups/step10-ui.html), spec11 và PLAN10. Chưa triển khai frontend hoặc thêm dependencies.

Yêu cầu đã chốt từ người dùng: giao diện sạch/dễ dùng, hướng doanh nghiệp và văn phòng; icon tiêu chuẩn dùng vừa phải, chỉ khi cần; màu đơn giản/hài hòa; hiệu ứng đủ nhận biết, không cầu kỳ. Chuyển thành UX-01–06 và checklist duyệt để không phụ thuộc nhận xét cảm tính sau khi code. Đề xuất nền trắng/xám, một accent navy, font hệ thống tiếng Việt, điều hướng chữ, viền nhẹ, nút có nhãn và motion120–180ms/reduced-motion. Màu success/warning/error có text, không dùng score thành confidence. Lucide là bộ icon dự kiến, chưa cài; không dùng icon/illustration để lấp chỗ trống.

Sidebar chỉ Hỏi đáp/Tài liệu, phiên gần đây nằm trong ngữ cảnh chat; source panel mở khi chọn citation. Cách này giữ vùng đọc thoáng và đối chiếu evidence gần claim. Không chọn dashboard nhiều cards/chart vì P0 là làm việc với tài liệu, không có metric nghiệp vụ cần tổng hợp. Không chọn sidebar nguồn luôn mở vì chiếm chiều ngang; dùng overlay khi thiếu chỗ. Dark mode/UI kit nặng chưa chọn để giảm số trạng thái/dependencies trước khi có baseline được duyệt; xem lại khi nhu cầu người dùng hoặc maintenance chứng minh cần thiết. Mật độ dòng và bo góc có thể thử trong công cụ duyệt, không tự đưa vào product settings.

Đối chiếu source API cho thấy GET documents/sessions/messages có limit nhưng chưa cursor; history lấy các message cũ nhất, chưa streaming/cancel-query/revoke-token. Kế hoạch ghi rõ giới hạn này, không vẽ chức năng như đã được backend hỗ trợ. Đề xuất sessionStorage theo tab là đánh đổi thuận tiện reload với persistence/XSS; memory-only hoặc HttpOnly cookie là lựa chọn khác cần cân nhắc, chưa triển khai. Binary sources cần bearer fetch/object URL/revoke; không nhét token vào link hoặc giữ excerpt sau410. Abort request không đồng nghĩa hủy server job; cần client_request_id/run recovery thay retry UUID mới một cách mù quáng.

Mockup độc lập dùng dữ liệu giả lập, có nhãn rõ, không đọc secrets hoặc gọi API/model; câu trả lời mẫu không phụ thuộc suy luận từ câu người dùng nhập. Static verification: preview renderer chấp nhận fragment, Node syntax check đạt, dưới1MB/không network APIs. **Chưa visual/browser QA:** browser host không khả dụng; Windows Computer Use dừng do URL policy enforcement chưa được hỗ trợ. Đã dừng computer input, không dùng đường vòng. Chưa tuyên bố responsive/focus/runtime interactions đã đạt, chưa tính AT-R23 pass hoặc human design approval. Kế hoạch ghi rõ hạn chế và bước kiểm chứng còn lại. Giữ tiến độ75,6%/100%; đợt code UI cần xác nhận phạm vi riêng.

### K-077 — UI doanh nghiệp: ít chrome, nguồn cạnh câu trả lời

**Ngày / loại:** 05/11/2026 — người dùng xác nhận “bắt đầu code UI, thực hiện đi”; đã viết frontend theo K-076. [Report](docs/ui-step10-implementation.md), [shell](frontend/src/components/layout/AppShell.tsx), [CSS](frontend/src/index.css), [Chat](frontend/src/pages/ChatPage.tsx), [Documents](frontend/src/pages/DocumentsPage.tsx).

Giữ React/TypeScript/Vite/Tailwind/router hiện có, dùng token navy/trung tính và font hệ thống, navigation bằng chữ. Chỉ import Lucide Plus/Upload ở hai hành động phù hợp, không icon theo mọi hàng. Native dialog xử lý lớp nổi mobile và confirmation, source dock bên cạnh ở desktop. Không thêm UI kit/state framework vì số màn hình và shared state hiện nhỏ; context cho identity/sessions/source, hooks cho document/query lifecycle, components cho presentation. UI kit/headless primitives có thể xem lại nếu native focus/PDF/browser QA cho thấy chi phí accessibility lớn hơn lợi ích giữ ít dependencies. Không tuyên bố layout/focus đã đạt chỉ từ CSS; browser QA còn pending.

### K-078 — Credential epoch và idempotency phải đi cùng trạng thái UI

**Ngày / loại:** 05/11/2026 — [API client](frontend/src/api/client.ts), [auth](frontend/src/auth/AuthProvider.tsx), [session](frontend/src/auth/session.ts), [pending](frontend/src/features/chat/pending.ts), [query hook](frontend/src/features/chat/useChat.ts).

SessionStorage theo tab giữ token/expiry; identity và role luôn lấy từ `/auth/me`, không tin role cài trong trình duyệt. Client kiểm token trước response và sau JSON/blob decode: response401 của token cũ không được logout token mới, body thuộc identity cũ không được trả cho UI mới. AbortController ngăn stale response ghi state khi đổi route/logout. Auth revalidate lúc focus giữ cây UI nếu identity còn hợp lệ, tránh mất draft không liên quan; workspace provider reset khi user/workspace/role thay đổi. Backend vẫn kiểm quyền mỗi request; ẩn nút không thay403.

Network abort không hủy server query. Pending giữ snapshot UUID/input/document IDs và optional run_id, retry cùng client_request_id hoặc GET run, không tạo UUID mới khi outcome chưa rõ. Snapshot chỉ gồm câu hỏi người dùng và IDs, không chứa evidence/answer; vẫn là dữ liệu nhạy cảm tiềm tàng, cần xóa ở terminal/logout/expiry. Khôi phục chấp nhận dưới10phút; chưa có background secure erase đúng phút thứ10. Memory fallback dùng được trong tab nhưng không sống qua reload. Không chọn localStorage dài hạn vì tăng persistence; memory-only mất reload recovery, HttpOnly cookie cần backend contract khác. Khi cần public app/multi-device phải xem lại auth/retention/revoke; logout hiện chỉ local.

### K-079 — Source preview là một lần đọc được xác thực, không phải snapshot đáng tin

**Ngày / loại:** 05/11/2026 — [SourcePanel](frontend/src/features/sources/SourcePanel.tsx), [AnswerView](frontend/src/features/chat/AnswerView.tsx), [source tests](frontend/src/features/sources/SourcePanel.test.tsx).

Chỉ dựng request từ document/chunk IDs và bearer; không dùng URL model/citation như đường mở tự do, không nhét token vào href. Trước render excerpt đọc lại source/metadata; failure404/409/410 clear text/filename/blob và invalidate history. Hidden tab clear bytes trong UI; focus hoặc delete event revalidate trước hiển thị. Binary allowlist PDF/text; text React escape, PDF object URL revoke khi đổi/đóng/logout. React không render HTML/Markdown từ tài liệu hoặc claims; không có raw assistant content fallback khi thiếu structured claims/citations. Đủ ID chưa chứng minh semantic faithfulness; chất lượng model vẫn Bước11.

Không chọn iframe trực tiếp vào endpoint cần bearer vì iframe/link không tự có Authorization header; không giữ cached excerpts để “xem offline” vì có thể vượt410/redaction. Browser PDF bytes đã tải không thể thu hồi từ máy/provider; app chỉ dọn state/object URL mình giữ. Native PDF viewer/focus/assistive technology cần nghiệm thu browser thật, chưa được jsdom chứng minh.

### K-080 — Kiểm thử UI phân biệt DOM fixtures, HTTP thật và browser E2E

**Ngày / loại:** 05/11/2026 —30frontend tests/7files đạt, build/lint đạt; [tests xuyên màn hình](frontend/src/App.test.tsx), [API boundary](frontend/src/api/client.test.ts), [query recovery](frontend/src/features/chat/useChat.test.tsx), [polling](frontend/src/features/documents/useDocuments.test.tsx). Raw reports ở `.cache/ui-review/`, không thay immutable `eval/reports`.

Testing Library tương tác qua labels/buttons thay component internals; Vitest/jsdom cho phép test credential races, role controls, session→query→citation→source, error states, exact-name delete, pending recovery và terminal polling. Đây là fixtures được ghi nhãn và không chạy provider thật; native dialog/Blob.text polyfills chỉ bù API môi trường test, không chứng minh focus trap/PDF/layout. Lỗi integration ban đầu xác định jsdom Blob thiếu.text và matcher “Trang2” trùng giữa nguồn/panel; sửa polyfill test-only/matcher, không sửa semantics nguồn để tests xanh. Typings mockfetch và exhaustive deps cũng đã sửa, không tắt lint/skip tests.

HTTP smoke qua Vite thật tới FastAPI/PostgreSQL kiểm health/login/me/documents/sessions hai roles, memberupload403 và missing-source404; dọn đúng2tokens tạo bởi probe, không tạo tài liệu/chat/generation. Browser access host không khả dụng; dừng ở đó, không vòng qua Windows browser bị policy chặn. Vì vậy chưa có upload→ready→Q&A→source→delete browser E2E hoặc visual/keyboard acceptance. Baseline302backend+91eval là đợt khôi phục trước, không nói là rerun trong đợt UI. Đây là ba lớp chứng cứ khác nhau, không cộng thành accuracy AI.

Dependency test ban đầu Vitest3 có audit critical tinypool; chuyển4.1.11 sau xác minh registry peer Node24/Vite6, giữ stack cũ. Audit cuối0critical/0high/9moderate:7thuộc ESLint/minimatch cũ,2thuộc Vitest/mocker test-only; chưa force major5/Vite mới vì cần đánh giá tương thích riêng. Chỉ chạyvitest run, không mở test UI server. [Lucide React](https://lucide.dev/guide/react), [Testing Library](https://testing-library.com/docs/react-testing-library/intro/) và metadata npm là nguồn chính thức đã đối chiếu05/11. Lucide pin1.68.0, Vitest4.1.11, jsdom26.1.0 và Testing Library được ghi trong package-lock; không freeze dependencies Python không liên quan.

### K-081 — UI không thể tự tạo khả năng backend còn thiếu

**Ngày / loại:** 05/11/2026 — [kế hoạch/giới hạn](docs/ui-step10-plan.md), [report](docs/ui-step10-implementation.md). API GET có limit100, chưa cursor; messages lấy tin cũ nhất. UI không vẽ pagination/full-library search giả; filter ghi phạm vi trong danh sách đã tải. Chat chặn gửi từ98messages để cặp question/answer tiếp theo không rơi ngoài100tin khi reload. Muốn lịch sử dài/full pagination cần backend contract và đợt riêng; không tănglimit trái schema để che thiếu sót.

Poll có backoff/dừng terminal và hết thời gian theo dõi thì báo chờ tiếp, không tự gán jobfailed hoặc suy phần trăm từ elapsed time. Source/partial/abstention/technical failures tách riêng; non-streaming không tạo token animation/stage giả. Đây là lựa chọn trung thực theo contract hiện có, đổi lại còn giới hạn UX cần ghi rõ.

Bước10 ghi nhận mục1–4 bằng source/component/HTTP evidence; mục5browser E2E và mục6visual-keyboard QA chưa tính hoàn thành. Giữ trọng số12 và các bước cũ77,5: `(77,5 + 12×4/6)/102,5×100 =83,4146…` →83,4%/100%. Không đổi trọng số, không tự duyệt human review/AT-R23. Local frontend/API/worker sẵn cho người dùng xem; API test process chặn Gemini bằng envkeyrỗng/flagsfalse, private.env không sửa. Không model spend, paid fallback, backend change, commit/push hoặc tự bắt đầu Bước11.

Audit bàn giao cuối:384protected file hashes không đổi,455candidate files không thấy3private secrets, bundle không chứa test fixtures,234local links/whitespace đạt. `npm audit --omit=dev` có0runtime vulnerabilities ở thời điểm kiểm tra; vẫn giữ9moderate ở full dev/test graph. Formatter có thay EOL ở3legacy frontend files, đã restore chỉ khi bytesCRLF khớp hash trước đợt để tránh đụng nội dung ngoài phạm vi. Không dùng số dòng code hoặc số tests để cộng tiến độ.

### K-082 — Polish UI cho demo/CV: thay một phần quyết định K-077

**Ngày / loại:** 06/11/2026. Người dùng xác nhận đợt UI polish ("Thực hiện đi"). Đã triển khai và đo bằng test. Files: [CSS](frontend/src/index.css), [AnswerView](frontend/src/features/chat/AnswerView.tsx), [Chat](frontend/src/pages/ChatPage.tsx), [Documents](frontend/src/pages/DocumentsPage.tsx), [Login](frontend/src/pages/LoginPage.tsx), [SourcePanel](frontend/src/features/sources/SourcePanel.tsx), [AppShell](frontend/src/components/layout/AppShell.tsx), [gợi ý câu hỏi](frontend/src/features/chat/suggestions.ts).

**Bối cảnh:** người dùng đánh giá UI hiện tại "sơ sài, xấu". Project sẽ dùng để làm sáng CV và nộp AI Builder Residency của VNG, hạn 15/11/2026; người lọc hồ sơ xem video demo trước. Ấn tượng thị giác trong vài giây đầu vì vậy trở thành yêu cầu, không chỉ là sở thích.

**Thay đổi so với K-077 (lịch sử được giữ nguyên ở K-077):**
- Font hệ thống → **Be Vietnam Pro** qua Google Fonts, vì font này hiển thị dấu tiếng Việt đẹp hơn. Font hệ thống vẫn là fallback.
- Navigation chỉ có chữ → **icon + chữ** cho nav, nút hành động và loại file. Icon chỉ đi kèm chữ, không thay chữ; ngoại lệ duy nhất là nút gửi và nút đóng, có tên accessible qua `sr-only`/`aria-label`.
- Trước đây không dùng dashboard cards → trang Tài liệu có **4 thẻ đếm** (tổng/sẵn sàng/đang xử lý/cần chú ý). Số đếm chỉ tính từ danh sách đã tải (tối đa 100), không phải metric nghiệp vụ.
- Accent navy #254564 → xanh chàm #3b5bdb. Chữ trắng trên nền accent có tương phản khoảng 5,6:1, đạt AA.

**Giữ nguyên các bất biến:**
- Citation hiển thị số thứ tự theo đúng thứ tự backend trả về. `evidence_id` vẫn là danh tính và nằm trong aria-label `Mở nguồn E1`.
- Popover xem trước chỉ dùng `excerpt`/`file_name`/`location` do backend dựng, render dạng text, không dùng HTML.
- Badge "Có nguồn dẫn"/"Trả lời một phần" lấy từ `answer_status`. Không hiển thị score hay phần trăm confidence; test kiểm tra không có chuỗi `%`.
- Abstention có giao diện riêng (`SearchX`, viền đứt), tách khỏi lỗi kỹ thuật (`role=alert`).
- Khi chờ trả lời, UI chỉ mô tả pipeline chung ("tìm, soạn, kiểm tra nguồn"), không giả từng stage hay animation token, vì API không stream (K-081).
- Thanh tiến trình ở Documents lấy vị trí của `job.stage` thật trong 6 stage ingest, không suy từ thời gian chờ. Đây là vị trí bước, không phải % khối lượng thật.
- Câu hỏi gợi ý chỉ điền vào ô nhập, không tự tạo session hay gửi query (có test). Gợi ý lấy từ tập **dev**, không dùng câu held-out test; câu thứ 4 dùng để demo abstention.

**Đánh đổi của Google Fonts:** khi tải trang, trình duyệt gửi request tới Google (lộ IP và referrer). Khi offline, giao diện rơi về Segoe UI. Phương án khác là tự host bằng gói `@fontsource`; chưa chọn vì cần thêm dependency và đợt này giữ phạm vi nhỏ. Xem lại nếu deploy cho dữ liệu thật hoặc cần chạy hoàn toàn offline.

**Kiểm chứng:**
- 34 frontend tests (7 files) đạt, gồm 4 test mới: số citation, badge grounding/partial/abstention, gợi ý không gửi query, ẩn gợi ý khi chưa có tài liệu ready. 30 test cũ giữ nguyên.
- Lint và build đạt.
- Đã chụp trang Login bằng Edge headless ở 1440×900. Ảnh mobile 390px không đáng tin vì headless có viewport tối thiểu khoảng 500px.
- **Chưa** visual QA các trang Chat/Documents/Source với dữ liệu thật vì DB/API đang tắt. Browser E2E (Bước 10 mục 5–6) vẫn pending.

**Tiến độ:** đợt polish không phải đầu việc mới của Bước 10, nên giữ **83,4%/100%**.

### K-083 — Hai lỗi dialog chỉ lộ ra trên trình duyệt thật

**Ngày / loại:** 06/11/2026. Sửa lỗi trong đợt chạy UI với dữ liệu thật đã được người dùng xác nhận. Files: [Dialog](frontend/src/components/ui/Dialog.tsx), [Dialog test](frontend/src/components/ui/Dialog.test.tsx), [CSS](frontend/src/index.css). Cả hai lỗi đều có từ Bước 10 (05/11), không phải do đợt polish K-082 gây ra.

**Lỗi 1: dialog tự đóng ngay sau khi mở trong bản dev.**
- Ảnh hưởng: upload, xác nhận xóa, menu mobile, panel nguồn trên màn nhỏ.
- Nguyên nhân: React StrictMode chạy effect mount → cleanup → mount. Cleanup gọi `dialog.close()`. Theo HTML spec, sự kiện `close` được **đưa vào hàng đợi task**, không bắn đồng bộ. Lúc nó bắn, effect lần hai đã mở lại dialog và gắn listener mới, nên `onClose` chạy và parent unmount dialog.
- Vì sao test không bắt được: mock `close()` trong jsdom bắn sự kiện đồng bộ.
- Cách sửa: listener bỏ qua `close` khi `dialog.open` vẫn là true. Đóng thật (dialog không còn open) vẫn gọi `onClose`.
- Phương án khác chưa chọn: bỏ StrictMode, hoặc không gọi `close()` trong cleanup. Cả hai đều chỉ che triệu chứng, còn StrictMode thì có ích để phát hiện effect không idempotent.
- Test mới: sự kiện close cũ không đóng dialog dưới StrictMode; close thật vẫn được báo.

**Lỗi 2: dialog dính góc trên bên trái.**
- Nguyên nhân: Tailwind v4 preflight đặt `margin: 0`, làm mất `margin: auto` mặc định mà trình duyệt dùng để căn giữa modal.
- Cách sửa: thêm `margin: auto` vào `.dialog`. `.source-dialog` vẫn giữ `margin-right` riêng.

**Bài học:** test component trên jsdom không thay được trình duyệt thật cho native `<dialog>` hay thứ tự sự kiện. Điều này khẳng định lại K-080.

**Cách kiểm chứng:**
- Edge headless qua CDP, dữ liệu thật: DB/Qdrant Compose, API và worker chạy trên host với Gemini bị chặn trong process.
- Upload 10 tài liệu corpus giả lập qua API thật, cả 10 đều `ready`.
- Chụp Login, Documents, Source, Upload/Delete dialog, Chat trống, đang xử lý, lỗi 503, và mobile 390px. Emulation của CDP khắc phục được giới hạn viewport tối thiểu nêu ở K-082.
- 36 frontend tests (8 files), lint và build đạt. Log API có 0 request tới Gemini.
- **Chưa** có ảnh câu trả lời thật, citation hover hay abstention thật, vì các trạng thái này cần gọi model. Truy vấn trả 503 và UI hiển thị đúng là lỗi kỹ thuật, không giả làm "chưa đủ bằng chứng".

### K-084 — Launcher Windows cho workspace dev đã setup

**Cập nhật cùng ngày:** quyết định luôn tắt Gemini của bản đầu được thay bằng chế độ dotenv mặc định và `-NoAI` tại K-085 bên dưới. Nội dung K-084 giữ lịch sử thiết kế/kiểm chứng bản đầu.

**Ngày / loại:** 09/11/2026. Tiện ích khởi động local theo đợt người dùng xác nhận “Thực hiện đi”. Files: [start-web.cmd](start-web.cmd), [stop-web.cmd](stop-web.cmd), [PowerShell launcher](scripts/web-dev.ps1), [hướng dẫn](README.md#bấm-đúp-để-mở-web-trên-windows). Không đổi UI, backend, dependencies hay cấu hình `.env`.

**Bối cảnh và lựa chọn:** môi trường máy nhận đã có venv, Node dependencies, Docker images, schema/seed và cache E5; chạy web thủ công cần mở storage, API, worker và Vite đúng thư mục. Hai wrapper CMD xác định đường dẫn bằng `%~dp0`, gọi Windows PowerShell 5.1 để điều phối, chờ health API/DB và HTTP frontend/proxy trước khi mở trình duyệt mặc định. API/worker cùng cwd `backend/`, Vite bind loopback `127.0.0.1:5173` với `--strictPort`; API bind loopback cổng 8000. Không dùng reload để giảm cây tiến trình và việc tự khởi động lại ngoài launcher. `ExecutionPolicy Bypass` chỉ áp dụng cho tiến trình được gọi, không ghi policy hệ thống.

**Vòng đời tiến trình:** mỗi dịch vụ có PowerShell supervisor ẩn, mang đường dẫn script hiện tại, tên dịch vụ và instance ID. File lock ngăn hai thao tác start/stop đồng thời. Khi bấm lại, ba supervisor còn sống và health đạt thì dùng phiên cũ; phiên sở hữu bị thiếu/hỏng được dừng rồi khởi động lại. Cổng bị tiến trình ngoài launcher chiếm thì báo lỗi, không giết tiến trình đó. `stop-web.cmd` đối chiếu command line, executable, PID và thời điểm tạo trước khi dừng cây tiến trình sở hữu; `state.json` chỉ để chẩn đoán, không dùng PID trong file làm quyền dừng. Log stdout/stderr theo phiên nằm trong `.cache/web-dev/`, đã được Git ignore. Dừng dùng `taskkill /T /F` cho cây supervisor đã xác minh; không dừng Docker, không xóa volumes/storage. Có thể ngắt job đang xử lý, nên dừng sau khi tác vụ hoàn tất; cơ chế lease/retry/fencing hiện hữu xử lý phục hồi job, không phải cam kết shutdown graceful. Nếu supervisor bị kết thúc từ bên ngoài và để lại child, launcher sẽ báo cổng bị chiếm thay vì đoán PID để dọn.

**Ngân sách và offline:** launcher đặt sentinel key không bí mật `disabled-by-web-launcher`, hai cờ free-tier/quota `false` và cờ Hugging Face/Transformers offline trong process environment. Lý do không chỉ gán key rỗng: Windows PowerShell 5.1 có thể xóa biến môi trường rỗng, khiến Settings đọc lại key riêng từ `.env`. Hai cờ `false` làm [Gemini adapter](backend/app/services/gemini.py) chặn trước request; sentinel bổ sung tránh kế thừa key thật. Preflight xác minh guard, DB/Qdrant local, DB dev khác DB test và sáu file E5/runtime bằng `frozen_profile`, không chạy embedding inference. Worker vẫn dùng embedding local khi có job, search vẫn cần E5; sinh câu trả lời Gemini chưa khả dụng trong profile này. Không có tùy chọn bật Gemini. Docker chỉ `compose up` hai storage với `--pull never --no-build`; không tự install, migrate, seed hay download. Trường hợp thiếu môi trường phải theo runbook, không âm thầm sửa máy.

**Phương án khác và đánh đổi:** CMD thuần ngắn hơn nhưng khó quản lý ownership/health/lock; chỉ ghi PID có nguy cơ PID tái sử dụng. Compose toàn bộ app phù hợp packaging/deploy hơn nhưng backend container hiện là scaffold, worker lock dành Windows/CPU; chuyển sang container cần đợt riêng. Windows Service/Task Scheduler phức tạp hơn nhu cầu dev và đòi hỏi cấu hình máy. Launcher hiện dành cho workspace đã setup, không thay thế installer hoặc nghiệm thu đóng gói trên máy sạch. Cơ chế nhận diện hỗ trợ dev local, không phải ranh giới bảo mật chống tiến trình cùng tài khoản cố tình giả mạo. Xem lại khi làm Bước 12 hoặc cần graceful shutdown/reload.

**Kiểm chứng thực chạy trong đợt này:**

- Parse PowerShell không lỗi; CMD dùng CRLF. Khởi động qua wrapper từ cwd khác repo đạt: API health/DB, HTTP Vite và proxy health đều đạt; ba supervisor tồn tại. Bấm lại giữ nguyên instance và ba PID, không mở trùng.
- Dừng và dừng lại đạt; cổng 8000/5173 được giải phóng, DB/Qdrant vẫn healthy. Cố ý thay PID trong manifest bằng tiến trình giả lập của bài kiểm tra: stop vẫn dừng đúng cây web, giữ tiến trình giả lập.
- HTTP server giả lập chiếm 5173: start thất bại với thông báo cổng/PID; stop không dừng server giả lập. Bản sao wrapper/script dưới đường dẫn có khoảng trắng nhưng thiếu dependency báo lỗi rõ, không tự cài.
- Preflight xác minh Gemini guard bị tắt và cache local có sẵn; không gửi truy vấn model. `.env` giữ nguyên SHA-256 so với trước đợt. Artifacts kiểm chứng riêng ở `.cache/web-dev-checks/`, không commit; không chứa key hay nội dung tài liệu.
- Khởi động lại cuối đạt và để web chạy sẵn. Fingerprint SQL chỉ đọc của chín bảng users/documents/revisions/source blocks/chunks/chat sessions/query runs/messages/citations và SHA-256 các file storage giữ nguyên trước/sau lần khởi động này; vẫn có 10 tài liệu `ready`. Không tạo dữ liệu nghiệp vụ, migrate hoặc seed trong bài kiểm tra; fingerprint không bao quát mọi bảng nội bộ của worker.
- Chưa kiểm chứng nhánh mở Docker Desktop từ trạng thái tắt vì không dừng Docker đang dùng để tạo tình huống; nhánh storage đã chạy được kiểm chứng. Các lần chạy thử dùng `-NoBrowser`; chưa nghiệm thu thao tác bấm đúp/mở trình duyệt thực tế hay browser E2E. Không suy từ HTTP checks thành AT-R23 hoặc human acceptance.

**Tiến độ:** giữ **83,4% / 100%** theo PLAN v1.13. Tiện ích launcher chưa đóng Bước 10 mục 5–6, final held-out hay Bước 12 packaging.

### K-085 — Launcher đọc cấu hình AI từ dotenv và nạp lại phiên cũ

**Ngày / loại:** 09/11/2026. Sửa launcher theo đợt “Thực hiện đi” sau khi người dùng gặp lỗi “Cần cấu hình model và xác nhận free tier/quota”. Thay phần luôn tắt AI ở K-084; không đổi backend/UI hoặc giá trị trong `.env`. Files: [launcher](scripts/web-dev.ps1), [wrapper](start-web.cmd), [README](README.md#bấm-đúp-để-mở-web-trên-windows).

**Nguyên nhân:** bản đầu gán sentinel key và hai cờ `false` trong environment của mọi dịch vụ. [Settings](backend/app/core/config.py) ưu tiên environment hơn dotenv nên điền key/xác nhận trong `.env` không làm AI hoạt động. Bấm start lại còn tái sử dụng phiên API đã chặn AI. [GeminiProvider](backend/app/services/gemini.py) chủ động trả lỗi 503 trước HTTP khi cấu hình chưa đạt; thông báo này không chứng minh key sai hoặc quota đã hết.

**Cách sửa:** `start-web.cmd` mặc định bỏ năm override LLM endpoint/model/key/free-tier/quota kế thừa từ shell để backend đọc dotenv; không export key qua command line hoặc in key trong log. Settings hiện đọc root `.env` rồi `backend/.env` nếu tồn tại, với file sau ưu tiên hơn. Preflight kiểm tra endpoint/model đúng contract adapter, key có nội dung, hai cờ xác nhận đều true và cache E5 có sẵn; gọi constructor provider để kiểm tra cùng contract nhưng không gọi `countTokens`/`generateContent`. Thiếu biến nào thì báo tên biến đó và dừng, không tự sửa key/cờ. Key có nội dung chỉ là kiểm tra cấu hình, không phải chứng thực key với Google.

**Chế độ tắt AI:** `start-web.cmd -NoAI` vẫn dùng sentinel và hai cờ false để chặn Gemini dù dotenv có key hợp lệ. Giữ các cờ offline cho Hugging Face/Transformers trong cả hai chế độ: chúng chặn tải weights, không chặn API Gemini. `-NoBrowser` chỉ ngăn mở trình duyệt, không tắt AI. `-Action Check` trên script PowerShell chỉ kiểm tra cấu hình/cache, không start/stop dịch vụ, không bật Docker hay gọi model; có thể thêm `-NoAI` cho profile kiểm thử.

**Nạp lại cấu hình:** supervisor mới mang mode và fingerprint SHA-256 của chế độ + nội dung hai dotenv + version launcher. State schema 2 ghi thông tin chẩn đoán này; quyền dừng vẫn lấy từ supervisor thực tế như K-084, không lấy PID trong state. Phiên legacy hoặc khác mode/fingerprint được dừng trước khi kiểm tra phiên thay thế, nên không giữ key/xác nhận cũ khi người dùng thay dotenv. Cấu hình mới sai thì không tự bật lại web; sửa biến được báo hoặc dùng `-NoAI`. Phiên cùng mode/fingerprint và health đạt được tái sử dụng. Child kiểm tra lại fingerprint trước khi chạy để tránh nạp dotenv khác với preflight. Không hot reload `.env`: phải chạy lại start hoặc stop để cấu hình mới có hiệu lực; nên hoàn tất tác vụ đang chạy trước khi đổi phiên.

**Ngân sách và đánh đổi:** launcher không tự xác minh billing/quota của tài khoản; hai cờ là xác nhận thủ công của người dùng, không phải billing cap. Giữ điều kiện project Free/chưa billing/quota đủ theo [runbook](docs/gemini-free-tier-setup.md); không đổi model, bật billing hay thêm paid fallback. Chưa gửi request model trong đợt sửa này. Phương án giữ mặc định tắt AI và thêm launcher thứ hai sẽ ít thay hành vi hơn, nhưng dễ lặp lỗi “web chạy mà chat không dùng được”; chọn một lệnh mặc định phục vụ hỏi đáp và switch `-NoAI` rõ ràng. Fingerprint toàn bộ dotenv có thể khởi động lại cả ba dịch vụ khi sửa biến không liên quan LLM, đổi lại đơn giản và không để DB/cache/auth cấu hình cũ; xem lại nếu cần reload riêng từng dịch vụ.

**Kiểm chứng trong đợt này:**

- PowerShell parser và `git diff --check` cho tài liệu đạt; wrapper giữ CRLF. `Check` trên `.env` hiện tại đạt, không in key và không xác minh key/billing/quota bằng request tới Google.
- Bảy ca cấu hình dùng dotenv/key giả ở đường dẫn có khoảng trắng: cấu hình hợp lệ vẫn đạt khi shell cha có năm LLM override sai; thiếu/sai riêng từng endpoint, model, key, free-tier flag, quota flag đều thất bại và báo đúng tên biến; `-NoAI` không có cấu hình LLM vẫn đạt. Fixture dùng Python audit hook chặn `socket.connect/getaddrinfo`, nên các ca đạt không phụ thuộc kết nối mạng. Output được kiểm tra không chứa key giả hoặc credentials DB fixture.
- Hàm fingerprint của script thật được kiểm tra với dotenv giả: sửa nội dung hoặc đổi mode đều làm fingerprint khác. Không sửa dotenv thật để tạo tình huống.
- Chạy thật qua CMD với `-NoBrowser`: thay phiên legacy bị chặn AI bằng phiên `-NoAI`, chuyển sang mặc định đọc dotenv, cả hai đều health đạt; chạy lại từng mode giữ nguyên instance và ba PID, không mở trùng. API health/DB và proxy qua Vite đạt. Để phiên cuối ở mode `env` phục vụ người dùng.
- SHA-256 `.env` giữ nguyên so với đầu đợt. Fingerprint chỉ đọc chín bảng nghiệp vụ và các file storage giữ nguyên trước/sau chuỗi chuyển phiên, vẫn có 10 tài liệu `ready`; không migrate/seed hay gửi câu hỏi tới Gemini trong các lệnh kiểm chứng. Artifacts kiểm tra nằm riêng trong `.cache/web-dev-ai-checks/`, không commit.
- Không chạy lại backend/frontend/eval suites vì không sửa source ứng dụng. Chưa kiểm thử câu trả lời model thật, quyền dùng key, quota/billing tại Google hoặc browser E2E; không suy từ cấu hình hợp lệ/HTTP health thành chất lượng AI hay AT-R23.

**Tiến độ:** giữ **83,4% / 100%** theo PLAN v1.13; không đóng thêm gate UI/held-out/packaging.

### K-086 — Ưu tiên bằng chứng chất lượng và demo trước mở rộng RAG

**Ngày / loại:** 10/11/2026 — đánh giá portfolio và quyết định thứ tự chuẩn bị; chưa triển khai enhancement hoặc chạy kiểm chứng mới. Người dùng xác nhận đợt tài liệu sau khi yêu cầu lưu đánh giá và cho biết UI hiện ổn, có thể sửa sau. Files: [đánh giá portfolio](docs/portfolio-review-20261110.md), [PLAN v1.14](PLAN.md), [kế hoạch kiểm chứng](docs/final-validation-plan.md).

**Bối cảnh:** nhóm SWE muốn ứng tuyển AI Builder Residency của VNG, lo project ít chức năng. Đọc source/reports và repo tham khảo cho thấy phần ingestion, source mapping, SQL revalidation, worker recovery và delete/privacy đã có chiều sâu; phần chứng minh chất lượng semantic và diễn giải giá trị sản phẩm còn thiếu. [Trang chương trình chính thức](https://humanforward.academy/vi/AIBuilderResidency) đã được đọc trong phiên 10/11; nhận định về sức hút CV là tư vấn, không phải rubric tuyển dụng công khai hoặc xác suất trúng tuyển.

**Kiến thức cần phân biệt:** software tests kiểm tra hành vi đã định nghĩa, không đo trực tiếp tỷ lệ model trả lời đúng nghiệp vụ. 91 eval tests không phải 91 câu trả lời model đúng; 45 câu/nhãn đã human-reviewed cũng không có nghĩa output model đã được chấm. Retrieval Recall@3=1 trên 13 answerable dev queries/14 chunks là số đo tập nhỏ, không thể suy rộng sang SME thực tế. Citation ID hợp lệ không chứng minh nguồn hỗ trợ từng claim; similarity giữa câu trả lời và nguồn cũng không thay correctness/faithfulness theo rubric. Bằng chứng: [Bước 07](docs/search-retrieval-step07.md), [Bước 08](docs/answering-step08.md), [dataset](eval/datasets/README.md).

**Lựa chọn:** giữ UI theo phản hồi người dùng; hoàn tất phần E2E/navigation/keyboard còn thiếu, rồi freeze và đánh giá baseline, sau đó đóng gói/demo/CV. Phản hồi “UI ổn” chỉ ghi là đánh giá trải nghiệm. [Report 06/11](docs/ui-step10-implementation.md) đã có Edge/CDP và 36 frontend tests; nhận xét trước đó chỉ dựa mốc 05/11 là thiếu cập nhật. PLAN v1.14 bổ sung evidence mới, giữ lịch sử bàn giao và không đóng AT-R23/human-quality. Không thay đổi trọng số hay tiến độ 83,4%/100%.

**Phương án khác và đánh đổi:** thêm hybrid/reranker/multi-turn có thể tăng chiều sâu thí nghiệm hoặc tính tiện dụng nhưng chưa giải quyết việc thiếu baseline cuối. Hybrid nên xuất phát từ lỗi exact identifiers; reranker từ nguồn đúng nằm thấp trong candidates; multi-turn từ nhu cầu hỏi nối tiếp và phải retrieve lại. OCR phụ thuộc tỷ lệ tài liệu scan. Fine-tuning/GraphRAG/agent chưa có nhu cầu hoặc phép đo đủ rõ. Giữ phạm vi hiện tại giúp hoàn thiện bằng chứng trước hạn hồ sơ; xem lại sau M1 hoặc khi failure analysis chỉ ra nút thắt. Không khẳng định kỹ thuật mới sẽ cải thiện khi chưa đối chiếu cùng dataset/config.

**Khoảng trống công cụ và dự toán:** đọc [retrieval runner](eval/run_retrieval_eval.py) thấy chỉ chọn dev; [answering runner](eval/run_answering_eval.py) chỉ chạy synthetic smoke. Spec có command contract dự kiến, chưa có final held-out runner hoàn chỉnh. Vì vậy phải chuẩn bị tooling offline và kiểm tra bằng fixtures trong đợt code riêng trước live run. [Context builder](backend/app/services/answering.py) hiện dùng tối đa h+2 countTokens cho h hits và tối đa hai generation calls gồm repair. Ví dụ 30 test queries/top5 cho trần 60 generation +210 count, chưa gồm warmup/oracle/no-context/rerun; đây là dự toán, không phải request allowance hay usage thật. Hard caps/ledger cần bao trùm browser và các batch, không chỉ smoke runner; không dùng cờ free-tier làm billing cap. Ngân sách vẫn 0 USD.

**Protocol dự kiến:** freeze source thực tế gồm HEAD, dirty status và hashes, vì HEAD không bao quát source chưa commit. Chốt split/config trước held-out; giữ failed runs và các mẫu số kỹ thuật, chấm claim/citation bằng con người. Nếu dùng test để sửa pipeline thì công bố contamination và cần holdout mới trước kết luận cải thiện. Một lượt/câu chỉ là mô tả chất lượng/latency trên mẫu nhỏ; so sánh latency nhiều lượt và oracle chẩn đoán cần budget riêng. Các chi tiết kiểm chứng, artifacts và checklist nằm ở [protocol](docs/final-validation-plan.md), không phải lệnh được tự chạy tiếp.

**Kiểm chứng của đợt tài liệu:** đối chiếu source runner/context builder, report UI 06/11, baseline retrieval/answering và spec 14–15; rà liên kết nội bộ, whitespace và diff giới hạn bốn files. Lệnh Python `-B` dùng cho kiểm tra liên kết không khởi chạy được do venv báo thiếu interpreter Python312 gốc; chuyển kiểm tra sang PowerShell đã đạt, chưa sửa venv hoặc suy ra trạng thái dịch vụ đang chạy. Cần kiểm tra môi trường trước đợt runner/tests. Nội dung KNOWLEDGE trước K-086 được giữ nguyên khi đối chiếu bản đầu đợt. Không chạy model/tests ứng dụng, không sửa UI/backend/config/`.env`, không ghi DB, không commit/push. Việc ghi tài liệu chưa tạo bằng chứng E2E hoặc human scoring; kết quả chất lượng mới vẫn pending.

### K-087 — Công cụ offline cho freeze, budget và human review

**Ngày / loại:** 10/11/2026 — code và kiểm chứng công cụ chuẩn bị sau xác nhận “Thực hiện đi bước tiếp theo”. Files: [runner offline](eval/final_eval.py), [ledger/provider wrapper](eval/final_budget.py), [human scoring](eval/final_review.py), [fixture tests](eval/tests/test_final_eval.py), [hướng dẫn](docs/final-eval-tooling.md), eval README, PLAN v1.15 và protocol. Không thêm dependency hoặc sửa runtime backend/UI.

**Vấn đề:** runners Bước07/08 chỉ dev/synthetic smoke; chạy chúng không tạo final held-out benchmark. Đồng thời budget per-run trong smoke chưa bao trùm nhiều batch hoặc browser, và schema/citation pass chưa chứng minh semantic quality. Cần chuẩn bị đường xử lý có thể kiểm tra không dùng quota và không mở test thật.

**Thiết kế đã triển khai:** tách phần stdlib offline thành freeze → replay observations → human rescore, có split test guard. Freeze kiểm checksum published snapshot/mapping, opaque questions bytes và Python source thực tế cùng HEAD/dirty state; chưa parse câu hỏi hoặc freeze bản release trong đợt này. Replay gắn protocol hash, reference canonical chunks theo document/index/text hash, namespace source blocks theo document, dùng span matcher hiện hữu; final evidence là tập con của top-k đã capture. Full structured answer giữ claims, thiếu thông tin/limitations/conflict để người chấm đánh giá đủ output. Report luôn có nhãn offline replay/origin, model_calls_this_run=0 và live acceptance chưa xác lập; không dùng latency xử lý lại làm latency model. Chuẩn hóa Unicode/soft-hyphen giữ cùng quy tắc parser, tránh mất match mã biểu mẫu PDF.

**Budget:** một SQLite ledger cho scope được duyệt, grant/caps/batches cố định, `BEGIN IMMEDIATE` check + reserve atomic trước transport. Wrapper lazy có cùng interface count_tokens/generate để đợt runtime sau cài provider factory; mất response vẫn tính reservation và không hoàn budget. Attach khác grant hoặc mất ledger bị từ chối; run ID mới không thay ledger. Đây là request cap trong runtime đã cài wrapper, không xác minh Google billing/quota và không bảo vệ API dev ngoài scope. Không lưu payload/key trong ledger.

**Lỗi phát hiện trong kiểm thử:** lần đầu 1 failed/53 passed; ledger giữ handle trên Windows. Nguyên nhân là `sqlite3.Connection` context manager commit/rollback nhưng không đóng connection. Sửa dùng `contextlib.closing` và transaction context; test xóa ledger sau thao tác chứng minh handle được đóng và request tiếp fail trước transport. Dùng mode=rw để không tự tái tạo ledger rỗng khi file mất. Kiểm tra thêm nhiều threads/instances cùng ledger chỉ reserve đúng cap; đây không phải load test provider hoặc multi-host distributed quota.

**Human scoring:** hai reviewer độc lập, correctness và từng claim/citation support; thiếu điểm hoặc còn bất đồng thì pending. Chỉ nhận adjudication có lý do và đúng hai người cùng đồng ý. Worksheet gắn exact run/output hash, rescore kiểm immutable published row hash rồi ghi file mới, không sửa history. Báo số đã chấm, strict planned denominator và errors/not-attempted riêng; zero denominator/pending là null. Script không tự tạo điểm semantic hoặc chứng minh người chấm đã đọc; scores trong tests đều là fixture.

**Phương án khác:** mở rộng runner cũ trực tiếp giảm số entry points nhưng dễ trộn smoke/dev với final và ảnh hưởng caps/regression lịch sử; giữ runners cũ, tạo công cụ offline độc lập. JSON ledger đơn giản hơn nhưng read-modify-write dễ vượt tổng cap giữa threads/processes; SQLite có transaction và có sẵn trong stdlib. Provider proxy sửa backend/gateway lớn hơn nhu cầu chuẩn bị; hiện chỉ chuẩn bị injection wrapper, chưa gắn runtime hoặc thu captures thật. LLM judge tạo quota và thêm sai số, chưa thay human rubric. Xem lại khi làm runtime capture adapter hoặc cần nhiều hosts; ledger local không phải ranh giới bảo mật chống người có quyền ghi cố ý sửa file.

**Môi trường và kết quả:** venv không khởi chạy vì thiếu Python312 gốc, `py -0p` không thấy bản đăng ký; tìm được Python3.12.6 trong pgAdmin và Ruff0.17.3 hiện hữu. Dùng interpreter đó với paths tường minh và pytest hiện có, không sửa pyvenv/config/dependencies. **57 focused tests đạt** gồm toolkit mới và metric/span regressions; network và corpus/mapping/report thật bị chặn trong tests. Ruff check/format đạt, CLI help và fixture freeze/replay/score đạt. Raw output `.cache/final-prep-20261110/pytest.txt`, thư mục test riêng `.cache/final-eval-offline-tests-20261110-r3`; không tạo benchmark thật trong eval/reports. Không suy từ tests này rằng backend venv/DB hoặc model pipeline thật đã hoạt động.

**Giới hạn/bước tiếp:** chưa triển khai production capture adapter hoặc runtime test có guard cho browser, chưa chạy model/embedding/DB/Qdrant/browser, chưa mở câu hỏi held-out thật hay chấm output model; chưa thay `.env`, code ứng dụng, UI, reviewed/mapping/reports cũ hoặc commit/push. Cần đợt riêng kiểm tra môi trường, tích hợp runtime/capture và xác minh mọi calls qua ledger trước live batch/free-tier quota. Không đóng Bước10 mục5–6 hoặc Bước11, không tăng tiến độ theo số lines/tests: giữ **83,4% /100%**.

### K-088 — Capture trong pipeline thật với runtime kiểm thử riêng

**Ngày / loại:** 10/11/2026 — triển khai tích hợp sau xác nhận “Thực hiện đi bước tiếp theo”. Liên quan [report runtime](docs/runtime-capture-step11-preparation.md), [adapter](eval/runtime_capture.py), [tests](eval/tests/test_runtime_capture.py), [API chat](backend/app/api/chat.py), [search/source](backend/app/api/search.py), [chat service](backend/app/services/chat.py), [ledger](eval/final_budget.py), PLAN v1.16 và protocol. Không sửa UI, dependencies hoặc `.env`; không gọi model/embedding, chạy browser, ghi SQL/Qdrant hoặc commit/push.

**Bối cảnh/cách hoạt động:** toolkit K-087 replay được observations nhưng chưa thu được context thực từ pipeline hoặc bao trùm calls của app. Thêm observer tùy chọn vào core chat sau SQL/source validation và sau context packing/revalidation, trước generation; API chỉ tạo observer khi có factory nội bộ trên app.state. App mặc định không capture full context. Collector nhận cả evidence không cited; suy context từ citations sẽ làm sai denominator faithfulness và không giải thích được lỗi context packing. Không chạy search phụ rồi nhận đó là retrieval của câu trả lời. SourceCheckedProvider vẫn kiểm nguồn trước mọi count/generate/repair.

**Cô lập đã chọn:** runtime mới giữ snapshot settings theo app cho query/search/source-content, cùng get_db override sang sessionmaker test đã kiểm target thực. SQL scope cần local *_test khác dev, collection `final_<grant fingerprint prefix>`, storage dưới backend/.cache/final-capture và profile/mapping khớp. Không mutate settings global để tránh ảnh hưởng app dev khác. Runtime thu baseline chặn mutation upload/delete/retry; corpus phải chuẩn bị riêng, lifecycle/browser acceptance chưa nằm trong bộ capture này. Query specs khóa exact question, user/workspace, filters, top-k/batch; hash plan được pin vào SQLite và kiểm lại, tránh đổi config sau freeze.

**Canonical mapping:** SqlCanonicalSources tái dùng load_active_mapping cho các tài liệu thực được tham chiếu, kiểm revision/generation/text/location/spans rồi map SQL UUID sang canonical external ref/index/hash. Empty hits không tạo nguồn giả; mismatch/foreign source fail trước provider. Native Gemini cần explicit live mode/flags và đúng adapter; fake generation luôn gắn origin offline_fixture kể cả dùng SQL thật để replay/report không biến stub thành real-model benchmark. Provider ngoài admitted observer bị chặn; cùng client_request_id replay không thêm calls/capture, ID mới cho spec đã dùng cần phạm vi attempt mới. Capture RAM chưa có crash resume; budget reservations bền vững vẫn giữ nếu process mất.

**Lỗi/đánh đổi:** generic OSError bao gồm TimeoutError của transport nên nếu bắt chung quanh cả reserve + provider sẽ phân loại nhầm timeout thành lỗi ledger. Tách LedgerUnavailable ngay tại reservation trong GuardedProvider; timeout sau transport giữ đúng loại và vẫn tính call. Lỗi capture sau publish có thể làm HTTP lỗi dù answer đã commit; không tự generate lại để che lỗi. Export lấy snapshot ledger trước tạo thư mục để mất ledger không để artifact dở trông như hoàn tất. SQL binding và caller settings không phải chữ ký chống chủ máy cố ý sửa mọi files; các guards chủ yếu chặn drift/sai scope và vượt request cap trong runtime được cài.

**Phương án khác:** sửa global search bằng monkeypatch cho capture sẽ ảnh hưởng app khác và khó giữ ranh giới; hook mặc định tắt giúp tests/runtime explicit. Lấy context qua SQL citations sẽ thiếu nguồn không cited, còn trace production chỉ giữ IDs/hash/spans; observer eval riêng thu synthetic text cần thiết mà không đổi privacy default. Proxy HTTP có thể kiểm mọi calls qua endpoint nhưng thêm service/TLS/config; dùng factory injection đã có, bổ sung route observer và fallback fail-closed. Xem lại khi cần multi-host quota hoặc full lifecycle browser harness.

**Kiểm chứng:** 116 tests đạt/1 Starlette-httpx deprecation warning baseline: 22 runtime ASGI tests với identity/storage/retrieval/publish stubs, 57 offline metric/span regressions và 37 unit tests gốc answering/Gemini (MockTransport). Route/controller, SourceCheckedProvider, context builder và repair/validation là code thật; không gọi SQL/model thật trong tests. Ruff check/format trên7files đạt; raw log `.cache/runtime-capture-20261110/pytest.txt`, basetemp final `runtime-capture-tests-20261110-r6`. Không mở reviewed holdout/corpus thật trong tests. Fixture network guard lần đầu chặn self-pipe của asyncio Windows nên TestClient không khởi tạo; sửa chỉ cho phép socketpair nội bộ tự tạo, giữ chặn app connect/DNS. Test DB guard sau đó kỳ vọng nhầm ValueError thay RuntimeError; guard gốc đã chặn đúng dev DB, đã sửa test theo contract gốc.

**Môi trường quan sát, không phải acceptance:** Python3.12.6 pgAdmin import được backend packages hiện hữu; venv thiếu interpreter gốc vẫn chưa sửa. Sandbox không đọc được Docker pipe/config ban đầu; kiểm tra chỉ đọc ngoài sandbox đạt client/daemon27.3.1. Compose ps không liệt kê container chạy của project; DB test qua guard thất bại OperationalError trước khi SELECT1/schema/job count thành công, Qdrant readiness ConnectError. Không xác định nguyên nhân chỉ từ exception type, không tự bật dịch vụ. LLM endpoint/model/key có nội dung và manual free-tier/quota flags true; không in secrets hay kiểm key/billing/quota tại Google, provider requests0. Cần duyệt bật/chuẩn bị storage và SQL integration với fakes trước live batch. Không dùng flags hoặc số tests để đóng Bước10 mục5–6, human review/held-out/Bước11; tiến độ giữ **83,4% /100%**.

### K-089 — SQL/Qdrant integration và ranh giới bằng chứng

**Ngày / loại:** 10/11/2026 — đợt storage/integration được xác nhận sau K-088. Liên quan [report](docs/sql-capture-integration-20261110.md), [suite](eval/tests/test_runtime_capture_sql.py), [runner môi trường](scripts/run-capture-integration.py), [probe](scripts/check-capture-storage.py), PLANv1.17, protocol và evalREADME. Không sửa production code, UI, `.env`, dependencies, snapshot/mapping/reports lịch sử; không inference/download/held-out/browser/commit/push.

**Bối cảnh:** K-088 mới chứng minh controller/context/ledger qua stubs; SQL adapter chưa đi qua storage thật. Docker daemon hoạt động không đủ chứng minh PostgreSQL/Qdrant ready. Đợt này bật đúng hai service từ images hiện có bằng `--pull never --no-build`, giữ volumes. Probe xác minh DBtest khác dev, SELECT1, migration head và queue rỗng trước integration; readiness HTTP200. Các kết luận chưa kết nối được ở K-088 là lịch sử trước khi storage được bật.

**Cô lập và cách hoạt động:** từ TEST_DATABASE_URL đã qua guard, suy thêm `copilot_capture_test`, kiểm lại target local `_test` khác dev trước tạo/migrate. Đây là DB/queue riêng, tránh IngestionWorker claim job của tests/dev khác; collection/workspace riêng trong cùng DB không đủ vì queue claim không giới hạn workspace. Advisory lock ngăn hai lượt suite cùng DB, không ngăn worker ngoài suite được cấu hình nhầm target. Mỗi test có workspace/user/bearer thật, collection và storage khóa theo grant fingerprint, mapping từ parser/chunker thật trên policy tổng hợp. Worker thực hiện SQL persist → fake embedding → Qdrant upsert/verify → publish; query dùng real auth/retrieval/source revalidation/context/publish/SqlCanonicalSources, không stub identity hoặc SQL. Unit vectors/counter code points/provider JSON cố định chỉ kiểm giao thức và dữ liệu, không đo ranking, tokenization hay semantic quality.

**Môi trường và lỗi harness:** Python3.12.6 pgAdmin dùng `python312._pth`, không nhận PYTHONPATH như Python thông thường; parser child lần đầu không import project và trả parse_failed. Suite bootstrap sys.path cho đúng subprocess module, vẫn giữ parser/process/timeout/serialization thật; không sửa Python hệ thống hoặc thay parser bằng inline fake. Fixture admin engine ban đầu thiếu connect_timeout, stack dump cho thấy chờ psycopg connect; thêm5s như engines còn lại, chưa khẳng định nguyên nhân DNS/IPv6. Hai process test tự tạo bị dừng khi chẩn đoán, không dừng Python/dev khác. Test canonical drift từng kỳ vọng ValueError nhưng contract collector đã chuyển503eval_source_drift; sửa assertion thay vì sửa production hành vi đúng. Giữ basetemp cũ để phân biệt các lần chưa đạt và lần cuối.

**Guard và giới hạn:** runner bỏ key khỏi process, free-tier/quota flagsfalse, offlineHF; tests chặn LocalEmbedder/GeminiProvider construction, HTTP ngoài localQdrant/TestClient và mở thư mục corpus/mapping/report thật. Không thay `.env`. Native requests thực0; các reservations trong ledger ở đây là fake calls. Manifest review approval chỉ là fixture input contract, không có người đã chấm outputs. Capture origin offline_fixture, provider_kindfake, auth_overridefalse; human correctness/faithfulness vẫn pending/null. Không dùng fake answer để đóng AT-R23 hoặc tính accuracy.

**Kiểm chứng đạt:** 6integrationtests/66,44s: grounded citation và idempotent replay không gọi lại; exhausted ledger trước transport; source change giữa generation chặn publish; canonical SQL text drift chặn trước provider; bearer/mutation scope; no-ready-source abstention không provider. 116regressiontests/18,29s đạt, mỗi suite cùng warning Starlette/httpx baseline; Ruff check/format3files đạt. Probe sau dọn cho thấy12bảng fixture đều0rows và Qdrant0collections prefixfinal_; DBtest gốc0pendingjobs, schemahead20261103_rag04, readiness200. Giữ DB/schema, source/capture/report/SQLite trong `.cache` và để storage containers chạy; không drop DB/reset volume. Logs và basetemp cụ thể ở report. Không gọi việc dọn fixture là acceptance xóa tài liệu trong sản phẩm.

**Phương án và đánh đổi:** dùng chung copilot_test ít setup hơn nhưng dễ chạm global queue khi test/worker khác chạy; chọn DB capture riêng vì isolation quan trọng hơn thêm một schema nhỏ. Chạy E5/Gemini ngay có thể kiểm chất lượng nhưng trộn lỗi môi trường và provider/quota, cần budget riêng; chọn inference giả trước. Mock cả SQL/Qdrant nhanh hơn nhưng bỏ sót canonical mapping/generation/auth/publish, đã có K-088 nên không lặp làm bằng chứng mới. Sửa/cài Python hệ thống có thể đơn giản hóa launcher lâu dài nhưng vượt nhu cầu integration; bootstrap trong test tạm thời, xem lại trong đợt clean setup Bước12. Không mở rộng hybrid/reranker khi chưa có failure analysis từ model thật.

**Bước tiếp đề xuất, chưa thực thi:** live dev smoke2câu tổng hợp với E5 cache và nativeGemini, hard cap toàn đợt4generateContent+14countTokens gồm repair, không paidfallback/warmupLLM/auto-rerun ngoài cap. Cần phạm vi runner/model/free-tier/quota được duyệt riêng; thiếu cache/quota thì dừng trước calls. Chưa human/held-out hoặc browser E2E; giữ **83,4% /100%** vì chưa hoàn thành thêm đầu việc có trọng số trong PLAN.

### K-090 — Native smoke và phân biệt compatibility với chất lượng

**Ngày / loại:** 10/11/2026 — code và lượt E5/Gemini thật sau xác nhận “Thực hiện đi” cho hai câu tổng hợp, cap toàn đợt 4 generateContent +14 countTokens, ngân sách 0 USD. Liên quan [runner](eval/run_capture_smoke.py), [bootstrap](scripts/run-capture-smoke.py), [tests](eval/tests/test_capture_smoke.py), [toolkit](eval/final_eval.py), [report](docs/native-capture-smoke-20261110.md), PLAN v1.18 và protocol. Không UI, `.env`, dependencies, download, reviewed held-out, bật billing/paid fallback hoặc Git mutation.

**Vấn đề và quyết định:** SQL integration K-089 dùng fake vectors/counter/provider nên chưa chứng minh cache E5 và Gemini hoạt động cùng canonical capture trên máy nhận. Chọn một policy tổng hợp tiếng Việt và hai câu: thời hạn/hồ sơ hoàn ứng và số ngày nghỉ phép không được quy định. Câu thứ hai vẫn retrieve một chunk, buộc model từ chối dựa trên nội dung thay vì chỉ kiểm no-hits shortcut. Đây là compatibility/API smoke có expected behavior, không thay bộ reviewed corpus hoặc human quality benchmark.

**Budget và cô lập đã triển khai:** scope/output cố định `native-dev-smoke-20261110`, exclusive mkdir chặn chạy lại bằng run ID/output/caps mới; SQLite ledger chia hai batches 2/7 với tổng 4/14, reserve trước count/generate và không refund. Không warmup LLM; lỗi kỹ thuật dừng trước câu tiếp theo, không tự retry/fallback. DB `copilot_smoke_test` được guard lại khác dev, migrate riêng, advisory lock và check queue; source workspace/user/token/document, collection và storage đều scope riêng. Cleanup đúng IDs/collection và canonical file key được kiểm nằm dưới storage root, không reset volume/drop DB. LocalEmbedder giữ subprocess production và cache-only; parser child chỉ bootstrap import path của Python embedded. Không sửa runtime Python hệ thống.

**Nguồn xác minh trước calls:** constructor Gemini kiểm endpoint/model/key và hai flags thủ công true; frozen_profile đọc cache local đạt, index giữ9851b494…c4a4. Đối chiếu [pricing Google](https://ai.google.dev/gemini-api/docs/pricing) cho Gemini3.5Flash-Lite có free input/output và [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) cho quota theo project, ngày10/11. Xác nhận account dựa trên flags/manual authorization đã có, không có account billing verification độc lập; không biến request cap local thành billing cap. Invoice cost vẫn null, budget0USD riêng. Native HTTP instrumentation chỉ giữ action/status/error type, không headers/raw provider body/payload/thoughts; usage lọc từ adapter.

**Nhãn synthetic và freeze:** toolkit trước đây chỉ nhận human_reviewed. Gán hai tên người/approved giả cho lượt model thật sẽ làm sai provenance, nên thêm opt-in synthetic_smoke: đúng hai câu dev, một answerable/một expected_abstain, CSV synthetic_fixture không tên annotator/reviewer; từ chối dùng làm held-out kể cả có allow-heldout. Mặc định reviewed vẫn kiểm độc lập/approved như trước. Freeze mapping/config/corpus và72Python source files thực tế backend/app + eval top-level, HEAD/dirty status; không tự commit. Config ghi model/context/timeouts/budgets, profile ghi hashes weights/package versions. Sau run đối chiếu source/input hashes đạt. Capture origin captured_api chỉ nói SQL/native thật, còn dataset_kind vẫn synthetic_smoke; human worksheet pending.

**Kết quả thực đo:** một lượt22:27:06–22:28:45 UTC+7, một document/chunk. Hoàn ứng HTTP200/grounded, hai claims đúng nội dung policy (30ngày từ khi kết thúc chuyến đi; hóa đơn và xác nhận quản lý), một citation E1; API pipeline7.019,732ms. Nghỉ phép HTTP200/insufficient_evidence, claims rỗng/không citation, retrieved/final context vẫn một chunk;16.699,936ms. Đây là quan sát output, không tự chấm correctness/faithfulness thay con người. Ledger2generation+6count, cả8HTTP200, không repair/rerun. Generation usage prompt820/output234/total1.054tokens; thoughts/cache usage thiếu không suy thành0. E5 load45,13s thuộc ingestion, không cộng vào query latency warm hoặc suy p95 từ hai mẫu.

**Kiểm chứng và lỗi:** phủ132tests khác nhau qua các lượt (10smoke +116regression +6SQLintegration), không cộng reruns thành tests mới; Ruff check/format đạt bốn files. Lượt đầu3assertions sai vì str(AppError) là message tiếng Việt, không chứa code; guard đã chặn trước cache/DB đúng, sửa test kiểm thuộc tính code. Test mới kiểm thiếu manual flags/key, dev DB/remote Qdrant, nhãn synthetic/held-out guard, scope không reset, setup failure giữ ledger và HTTP diagnostics không lộ key/body. Probe sau cleanup:12bảng fixture0rows,0final_collections,0scopeduploadfiles, head20261103_rag04, readyz200; ledger vẫn2/6. Corpus/capture/ledger/report giữ trong `.cache`, không ghi đè historical eval/reports.

**Phương án thay thế/đánh đổi:** dùng runner smoke cũ giảm code nhưng không có actual retrieval/context capture và shared API ledger; dùng bộ mới để nối bằng chứng production. Full30test queries sớm hơn có thêm số đo nhưng rủi ro contamination khi môi trường chưa xác minh; giữ held-out đóng. Tự tạo human approvals cho synthetic đỡ sửa toolkit nhưng sai nhãn; explicit dataset_kind giữ ranh giới. Một scope one-shot không hỗ trợ crash resume có thể làm gián đoạn đợt nếu setup/provider lỗi; ưu tiên không reset quota, xem lại khi cần durable attempts với cùng ledger. Fix Python toàn máy/đổi model hoặc thêm reranker chưa cần cho lượt compatibility đã đạt; dành cho clean setup/failure analysis có bằng chứng.

**Lưu source để tái lập:** hash phát hiện drift nhưng không tự phục hồi code trong working tree dirty khi chỉnh về sau. Sau run đã sao chép nguyên 79 files được freeze (72 Python +7 inputs/config/mapping) và protocol sang archive root mới bên trong output; kiểm hashes và evaluate lại hai captured rows ở root đó đạt, không provider calls. Giữ relative paths để replay độc lập với source workspace tương lai. Đây là thao tác lưu artifact của đợt, chưa tự động hóa trong CLI và không sửa capture/ledger đã xuất. Không sao chép `.env`/weights. Chỉ giữ hashes ít tốn dung lượng hơn nhưng thiếu source cũ khi chưa commit; archive nhỏ phù hợp với đợt dirty working tree. Rà 274 local links đạt.

**Giới hạn/bước tiếp:** human reviewed 0/2, các metric human vẫn null; không đưa 2/2 expected statuses lên CV như accuracy. Chưa browser E2E/hai role/delete/history/keyboard QA hoặc final held-out/release. Phần tiếp theo là E2E trên UI hiện có và request budget riêng, không tự bắt đầu từ scope smoke này. **Tiến độ giữ 83,4% /100%** vì chưa đóng thêm đầu việc có trọng số trong PLAN.

### K-091 — Browser harness và tool blocker không phải acceptance

**Ngày / loại:** 10/11/2026 — đợt browser E2E được xác nhận với trần8generateContent/28countTokens, ngân sách0USD. Đã viết [harness](eval/browser_e2e.py), [bootstrap](scripts/run-browser-e2e.py), [tests](eval/tests/test_browser_e2e.py), mở rộng helper/nhãn fixtures trong [smoke](eval/run_capture_smoke.py)/[toolkit](eval/final_eval.py), [report](docs/browser-e2e-20261110.md), PLANv1.19. Không sửa frontend source, `.env`, dependencies, API production, tải model, bật billing/fallback hoặc Git state. UI execution bị tool guard chặn, không có model calls trong scope.

**Bối cảnh/thiết kế:** native smoke K-090 chỉ qua API TestClient nên không chứng minh UI login/upload/citation/delete/history. Harness dùng bundle UI build hiện tại và API cùng origin loopback8012 để không đổi Vite/proxy/configdev. DBcopilot_browser_test và queue riêng, hai disposable users trong workspace riêng, collection/storage theo grant fingerprint; tránh global worker claim nhầm DB dev/test khác. Corpus là policy tổng hợp, không reviewed held-out. Controller lazy bind sau đúng một document khớp SHA và ready từ browser upload/worker thật; trước ready không provider. SQL auth/retrieval/context/publish vẫn code production. Harness cài hooks app nội bộ để cho phép upload đầu tiên và delete đúng fixture, không nới default CaptureRuntime.install hoặc thêm public production flags. App mutation khác bị chặn.

**Giai đoạn và caps:** mở rộng opt-in synthetic_browser_e2e gồm sáu fixtures dev: mỗi role có answerable/abstention trước delete và một câu sau delete. CSV không giả human review. Một ledger tổng8/28, bốn batches2/7 và hai batches0/0; câu sau delete bị chặn cho tới document deleting/deleted. Zero model budget sau delete làm lỗi retrieval không âm thầm thành một lượt generation; query no-hits đúng không cần provider. Không nhận scope/output CLI tùy ý để reset caps; ledger đã tạo được giữ dù browser chưa chạy.

**Housekeeping:** helper cleanup trước chỉ dùng một user và document còn ready; E2E có hai users và document có thể đã deleted. Bổ sung danh sách users scoped, dọn references trước users/workspace, giữ deleted khi UPDATE để không vi phạm lifecycle bằng cách chuyển ngược về failed. Không coi fixture housekeeping là product delete acceptance. Server có finish sentinel riêng, join worker rồi cleanup; không kill browser/dev services. Do chưa upload, những nhánh product ingestion/delete chưa được chạy trong đợt này.

**Kiểm chứng phần mềm:** UI build tsc/Vite6.4.5 đạt,2095modules/3bundlefiles, dùng Node/npm đã cài ngoài sandbox sau khi sandbox không có PATH/quyền ProgramFiles; automatic approval cho build được cho phép, không có auto-review rejection.131tests đạt/1warning Starlette-httpx baseline, gồm5E2Eguards+10smoke+116regression; Ruff check/format5files đạt. Lượt đầu pytest không tìm thấy inputs fixture vì unused-import autofix loại registration; dùng module alias để đăng ký fixture và lint, không thay behavior. Các tests không chạy browser/model. Byte hashes40UI source/config/packagefiles không đổi; chỉ build dist artifacts.

**Blocker quan sát:** browser inventory báo access host unavailable. Native getApp Brave đầu tiên chờ approval rồi timeout; người dùng đã trả lời “Đã chấp thuận, thử lại”. Retry getApp thành công nhưng lệnh mở tab mới bị Computer Use dừng vì **không xác định được current browser URL trên Windows đủ chắc chắn để enforce policy**. Đã dừng UI automation và gửi completion_summary; không chuyển sang CDP/Playwright tự dựng hoặc tiếp tục click/type. Đây là policy/runtime blocker của công cụ, không phải khẳng định UI sản phẩm hỏng, quota hết hoặc người dùng chưa xác nhận scope. Không ghi nội dung tab cá nhân vào project artifacts.

**Kết quả đợt:** status API của harness cho documents/jobs/api_events/native_http_events rỗng; ledger0generation/0count. Không có upload, login, query, source, delete hoặc history thực trên browser, không có capture/evaluation/worksheet mới.131tests/build không được đổi thành AT-R23 pass. Đã shutdown server/worker, summary cleanup_completed=true; probe head20261103_rag04,12bảng fixture0rows và Qdrant0final_collections. DB/schema/ledger/fixtures/logs giữ trong `.cache`; không xóa scope để thử lại. Source archive K-090 vẫn verify được sau thay đổi helper/toolkit hiện tại.

**Phương án/đánh đổi:** browser plugin là đường ưu tiên nhưng host unavailable; native Computer Use được thử sau khi đọc skill và đã gặp guard URL. API-only vẫn kiểm được contract nhưng không trả lời câu hỏi acceptance browser, nên không tiêu ngân sách model để thay thế và không báo E2E pass. Tự dựng CDP có thể chụp được trang nhưng sẽ đi vòng restriction UI runtime trong lượt này, không chọn. Một scope one-shot tránh reset budget nhưng chưa hỗ trợ resume sau lỗi tool; cần thiết kế attempt tiếp được duyệt khi browser host hoạt động, giữ ledger và lịch sử thay vì sửa kết quả pending thành pass. Không hỏi lại quyền cho login/delete đã được duyệt; runtime URL guard vẫn phải được tôn trọng.

**Tiến độ/giới hạn:** Bước10mục5–6/AT-R23, visual-keyboard QA, human scoring và held-out vẫn pending. Chưa thay đổi trọng số hoặc đánh dấu thêm human review. **83,4% /100%**; phần code chuẩn bị đã xong, luồng browser chưa thực hiện được.

**Bổ sung K-091 — retry Chrome theo yêu cầu:** đọc Vite/launcher và probe ngoài sandbox xác nhận URL phát triển5173, API8000, harness8012; cả ba đều ngừng trước đợt retry. Chrome thực tế đang mở8012 và báo ERR_CONNECTION_REFUSED, phù hợp với harness đã dừng chứ không chứng minh UI hỏng. Đã bật Vite preview loopback5173 từ bundle hiện có, không API/worker/model hoặc reset ledger; để UI preview chạy cho người dùng mở thủ công. Native getApp Chrome đọc được address bar nhưng lệnh chuyển URL vẫn bị runtime URL guard dừng. Không bypass guard, không nhận preview startup là browser/E2E pass. API8000 chưa bật nên chưa login/Q&A; model calls0, tiến độ83,4%/100%. Đây là ghi nhận retry, không thay bằng chứng native smoke đã đạt trước đó.

### K-092 — Thử lại browser mà không đặt lại allowance

**10/11/2026, phạm vi đã được xác nhận.** One-shot harness K-091 đã cleanup mà chưa chạy query; khởi động lại trực tiếp sẽ FileExistsError. [Retry harness](eval/browser_e2e.py) chỉ nhận `--retry-unused` cho đường dẫn cố định retry-01. Kiểm tra ledger SQLite thật0reservation/0binding, summary/finish/cleanup, grant/caps, archive source và bundle hashes trước khi chuẩn bị. Config, policy và sáu câu phải giữ nguyên; protocol mới freeze source hiện tại, protocol/archive cũ không viết lại. Không thay UI source hay production API.

**Cơ chế:** ledger con pin protocol mới và actual runtime; mọi count/generate phải reserve ledger gốc trước, ledger con sau. Ledger gốc pin retry grant bằng runtime_binding, không sửa immutable grant. Nhờ đó allowance tổng8/28 của scope đã duyệt được giữ cả qua attempt; không tự cấp thêm ngân sách. Không có distributed transaction giữa hai SQLite files: lỗi file con có thể tiêu reservation gốc mà không gọi model. Chọn fail-closed/no-refund; refund không chứng minh request chưa tới provider. Chỉ hỗ trợ một retry của scope chưa sử dụng, không khôi phục runtime đã có query hoặc reset output/finish cũ. Có thể xem xét resumable durable runtime tổng quát khi có nhu cầu thực tế, nhưng cần lưu identity/specs/admitted requests và session lifecycle qua process restart.

**Bằng chứng:** [tests](eval/tests/test_browser_e2e.py) chứng minh cap gốc chặn dù ledger con còn chỗ, parent binding không đổi, child failure giữ reservation, post-delete0/0, từ chối scope đã dùng/mất ledger/đổi bundle/archive/grant.119selectedtests và Ruff2files đạt;1warning Starlette/httpx baseline. Các lỗi gọi pytest/basetemp/fixture exclusive-write trước lượt đạt được ghi ở [report](docs/browser-e2e-retry-20261110.md); không đổi guard để né lỗi. Preflight không model calls, status đầu ledger tổng/con0/0, archive retry80files+3UIfiles và archive gốc verify. Server loopback8012 dùng DB/queue riêng; preview5173 không phải origin E2E. Manual browser checklist là phương án khi tool input còn lỗi, không phải tự chấm pass. Chi phí invoice chưa xác minh;0USD là ngân sách/manual flags, không phải billing cap phía Google. Bước10mục5–6/human/held-out pending,83,4%/100%.

**Bổ sung K-092, kết quả11/11:** Chrome đã điều khiển được bằng native CUA sau chọn đúng cửa sổ/Raise, không sửa plugin/permissions hoặc bypass guard. Hoàn tất6/6query (2grounded/4insufficient_evidence), hai role/citation, upload/publish/delete, stale source panel410 trên member khi admin xóa ở cửa sổ riêng, history redaction và hai query sau xóa0hits/0provider.4generateContent+12countTokens,16nativeHTTP200; ledger gốc/con cùng số và không reset. Output human reviewed0/6, không biến synthetic expected-status success thành accuracy. [Báo cáo đầy đủ](docs/browser-e2e-retry-20261110.md) giữ hashes/latency và giới hạn.

**Kiến thức từ E2E:** khi nguồn bị xóa, cả câu abstention trước đó cũng redacted vì actual final context chứa nguồn, dù claims/citations rỗng; evidence provenance/retention phải tính context đã dùng, không chỉ citation hiển thị. Member panel đang mở revalidate khi quay lại cửa sổ, trả410 rồi ẩn quote; browser history reload cũng không khôi phục nội dung bị xóa. Token expiry test dùng2tokens disposable admin tại DBtest, expires_at=created_at+1s; không đổi TTL/config thật, không sửa DB để hoàn thành happy path. Browser reload nhận auth401 và thông báo hết hạn. Shift+Tab focus/preview, Enter citation, Escape dialog, Shift+Enter không submit, session navigation/reload không tạo query trùng đã quan sát. Không khẳng định POST/DELETE403 qua browser khi UI đã ẩn nút; RBAC endpoint có bằng chứng integration trước đó.

**Kết thúc:** summary cleanuptrue,12bảng fixture0rows, Qdrant0final_collections, scoped canonicalfiles0; capture/replay/80filearchive/3UIbundle verified. Shell server trả1 nhưng không Python traceback, không nhận là exit0; audit độc lập xác minh kết quả và cleanup. Audit helper từng assertion quá rộng (bao gồm hợp lệ Documents revisit) và nhầm worksheetlist/dict; giữ logs lỗi, audit-final đọc đúng phạm vi. Bước10 đóng6/6 theo hành vi thật,87,3%/100% với trọng số cũ; Bước11–12/human/held-out không tăng. Các snapshot83,4% của K-091/đầu K-092 là lịch sử trước khi browser chạy xong.

### K-093 — Candidate offline, runner held-out và phiếu chấm độc lập

**11/11/2026, phạm vi đã xác nhận.** Sau khi Bước10 hoạt động xuyên suốt, vấn đề còn lại là số đo chất lượng có thể truy ngược output. [Runner](eval/final_runner.py), [config](eval/configs/final_baseline.json), [bootstrap](scripts/run-final-eval.py), [review pack](eval/review_pack.py)/[CLI](scripts/run-review-pack.py), [tests runner](eval/tests/test_final_runner.py)/[tests review](eval/tests/test_review_pack.py) và [hướng dẫn hai người](docs/human-review-guide.md) đã viết. Không thay production backend/UI, dataset/mapping/report cũ, `.env`, dependencies hoặc gọi model trong đợt này.

**Freeze không có nghĩa đã chạy test:** prepare dùng metadata và hash/copy question JSONL như bytes, chưa đọc câu test để chọn câu dễ hoặc tune prompt. Candidate lưu HEAD và trạng thái dirty; hashes source thật mới mô tả bản đang làm, không ép commit. Native Python/prompt source, config/index/model revision, corpus/mapping và bootstrap/dependency locks đều được pin. Candidate99files+4extras verify trên root và archive, protocol04562e68fa1c38d11188b545f9ceba4b38d2e1a49aac30cfad15cfa64f6e9f9b. Đây là candidate, chưa tự đóng final release freeze; nếu code đổi phải kiểm tra drift và có candidate thay thế rõ ràng.

**Tách allowance dự kiến khỏi quyền thực thi:** request-plan cho30câu/top5/concurrency1 dự toán60generation/210count, mỗi câu2/7. Template pending và hai flags false; không tạo RequestLedger hay execution folder khi prepare. Nhánh capture kiểm tra approval hash/reference/manual confirmations trước khi load held-out, app imports hoặc storage. File approved chỉ là technical gate, không thay câu xác nhận thực thi của người dùng. Sau gate, runtime config/prompt/cache index phải khớp freeze; DB*_final_test, collection/storage theo grant riêng, canonical mapping kiểm lại sau ingestion. Capture dùng API production, không đưa gold context vào model. Dừng khi HTTP/transport lỗi, giữ receipt/coverage, không reset hoặc tự retry. Một run one-shot chưa hỗ trợ resume nhiều ngày. Thời gian nghỉ5s giữa câu không bảo đảm quota provider vì còn nhiều count/generate calls bên trong câu. Quota/billing/model availability phải kiểm chứng lại trước live scope; ngân sách0USD không phải billing cap phía nhà cung cấp.

**Vì sao hai file review:** duyệt gold dataset trước đó khác với chấm output mới. Mỗi reviewer nhận score null, id/run/output hash giống nhau nhưng điền file riêng. Correctness0/1/2 đánh giá câu trả lời đúng/đủ theo câu hỏi; supported và từng citation kiểm claim với actual final context. `partial` có thể đúng hoàn toàn nếu nêu chính xác giới hạn; abstention vẫn cần chấm correctness. Hit@k không thay faithfulness. Merge giữ disagreement, không tự adjudicate hoặc đánh dấu AI-generated judgement thành human-approved. Reviewer thấy gold để tìm phần thiếu nhưng không được dùng kiến thức ngoài bù support. Text không đáng tin được đặt trong code fence đủ dài để không phá fence/render HTML/link. Chọn Markdown+JSON thay UI/Excel mới để giữ phạm vi offline, tận dụng score schema/rescore đã có; cân nhắc giao diện chấm nếu số lượng/nhu cầu nhóm tăng.

**Bằng chứng/giới hạn:**148tests đạt/1warning Starlette-httpx baseline, Ruff đạt. Tests corpus tạm/network bị chặn; guard pending/budget/hash/drift/one-shot/split-size, timeout/stop-on-error và review binding/độc lập/bất đồng/literal rendering. Receipt offline xác nhận không import app settings/torch/SQLAlchemy/HTTPX, không grant/ledger/execution, không parse/print question test. Đã xuất phiếu sáu output E2E từ archived root đúng run, human0/6; không phải sáu output mới hoặc held-out report. Native orchestration mới chưa chạy PostgreSQL/Qdrant/10documents/inference; cần kiểm chứng riêng trước live30 câu. [Report](docs/final-eval-preparation-20261111.md) ghi lệnh và artifacts. Không tăng87,3%/100% theo số tests/tooling, không tự chấm người hoặc đóng Bước11/12.

### K-094 — Human review thực hành và shared final orchestration

**11/11/2026, phạm vi đã xác nhận.** Nhóm cung cấp hai phiếu đã điền; [merge/rescore](docs/human-review-practice-20261111.md) xác minh id/run/output digest/schema và reviewer khác nhau, giải quyết6/6 vì hai điểm khớp. Correctness trung bình2/2; faithfulness4/4claims, citation correctness4/4links. Không tự adjudicate hoặc thêm điểm. Hai phiếu, binding và báo cáo E2E gốc giữ nguyên hashes; kết quả mới có receipt riêng. Giữ lịch sử pending thay vì sửa báo cáo ban đầu để truy nguyên việc ai chấm output nào/lúc nào. Sáu case lặp role/lifecycle quanh hai câu hỏi tổng hợp không phải sáu mẫu kiến thức độc lập; tỷ lệ100% không suy ra accuracy tổng quát. Chưa có human review cho30 outputs held-out.

**Thiết kế:** [runner](eval/final_runner.py) có wrapper native và `capture_run` chung; [tests SQL](eval/tests/test_final_runner_sql.py) bơm counter/embedder/provider giả, vẫn chạy database/worker/parser/auth/retrieval/API/canonical capture/replay/cleanup thật. Dependency injection giữ provenance fake/offline_fixture; monkeypatch Gemini rồi gắn captured_api sẽ sai bằng chứng, còn stub toàn bộ storage không kiểm được liên kết SQL/Qdrant. Chưa cần plugin inference hoặc UI mới vì chỉ công cụ eval dùng factory. `config.get_settings` được patch theo context/khôi phục, verify trước inference, close tài nguyên và summary trong finally. Không quảng cáo chống được process kill hoặc mọi startup failure chỉ vì đã viết finally.

**Kiểm chứng:**5integrationtests +148regression ở hai lượt riêng, Ruff đạt; warning Starlette/httpx baseline.10TXT thật được ingest,2queries HTTP200; fake2generate/14count khớp ledger. Budget0 trả503 không generation, timeout theo public contract AppError504 giữ reservation; planned2/attempted1/error1/notattempted1, không mất mẫu số. Mapping sai và worker unsupported_encoding dừng trước model/query. Guards chặn constructor model/tokenizer thật, HTTP ngoài testserver/Qdrant, và đọc corpus thật. Audit12bảng0rows/Qdrant0final_/0canonicalfiles,5summarycleanuptrue, migration20261103_rag04; giữ DB/schema/containers/artifacts. Bộ10TXT không chứng minh corpus PDF/DOCX reviewed thật hoặc latency chất lượng model. [Report/logs và giới hạn](docs/final-runner-sql-20261111.md).

**Kiến thức harness:** embedded Python bỏ PYTHONPATH nên parser child cần bootstrap packages, không sửa parser thành inline fake. Chẩn đoán stack cho thấy chờ native CA loading và psycopg localhost trong các lượt; chưa đủ kết luận nguyên nhân OS. Harness dùng certifi CA từ memory trong SSL context dùng lại (CERT_REQUIRED/check_hostname giữ), và PostgreSQL loopback IPv4 rõ ràng/connect_timeout5s; chỉ thay môi trường tests. Không chọn verify=False hoặc sửa TLS production. Fixture timeout phải mô phỏng public AppError504 của provider, byte hỏng phải qua signature mới kiểm được worker; các lượt lỗi trước đạt được giữ lại. Audit phải deduplicate đường dẫn resolve vì symlink pytest current, không nhân đôi số summary. Helper recovery ngoài sandbox không mở được SQLite và không cleanup; audit thành công sau cùng là bằng chứng, không lấy helper lỗi làm pass.

**Candidate thay thế:** đổi runner làm source drift với candidate04562e68fa1c38d11188b545f9ceba4b38d2e1a49aac30cfad15cfa64f6e9f9b; giữ nguyên frozen-root cũ, xác minh archive và ghi thay thế rõ ràng. Candidate mặc định `.cache/final-reviewed-baseline-20261111-sql-verified/`, protocol d15e3cea44fe9dca9dae1ec5d24cd20e7fbb85b253f97d90a87646baa8834498,99files+4extras verify source/archive. Không sửa freeze cũ hoặc reviewed/mapping/config. Hash/copy test như bytes, không decode; helper không import app settings/torch/HTTPX/SQLAlchemy. Pending gate chặn trước loader/runtime, không grant/ledger/execution mới; dự toán60generation/210count vẫn chưa được duyệt. Đây không phải cấp lại allowance hay final release freeze. Chỉ chạy thật sau xác minh free-tier/quota/lifecycle và scope mới được xác nhận; chưa resume nhiều ngày. Không model/download/UI/commit/push; PLANv1.23 giữ87,3%/100%, Bước11–12 còn mở.

### K-095 — Pacing trước native held-out và quota theo project

**11/11/2026, đã xác nhận phạm vi sửa runner/pacing/tests, candidate thay thế, chạy30held-out với caps60generation/210count và xuất hai phiếu mới.** Người dùng xác nhận không billing/thẻ/payment và cung cấp0/15RPM,0/250KTPM,0/500RPD. Số0 là usage, không phải quota được cấp bằng0. Quota ngày đủ chưa bảo đảm burst theo phút: runner nghỉ5s giữa câu vẫn có thể có hai generation do repair. [Report và nguồn chính thức](docs/final-heldout-20261111.md) phân biệt user-reported quota, manual flags và invoice chưa xác minh.

**Thiết kế đã viết:** [pacer](eval/final_pacing.py)/[tests](eval/tests/test_final_pacing.py) và [runner](eval/final_runner.py) dùng rolling window61s/max12native requests/min gap5,1s, chung count/generate. Generation dự phòng40K/request và200K/61s, ứng dụng giữ context32.768/output budget/deadline cũ. Dự phòng không phải input tokens thật; usage vượt dự phòng dừng run. Không kiểm soát project clients khác hoặc bảo đảm quota provider. Chọn pacing bảo thủ thay chỉ tăng query sleep, suy luận từ RPD hoặc đổi model; đổi lấy thời gian chạy lâu hơn. Chờ async nằm trong provider timeout, không nới deadline/retry. Ledger reserve trước provider, pacer trước send; failure giữ allowance, JSONL chỉ dispatch metadata và flush trước send, không chứa prompt/headers/key. Không có atomic transaction giữa SQLite và HTTP; fail-closed/no-refund, không reset hoặc resume scope bằng run ID mới.

**Kiểm chứng trước model:**155regressiontests,8pacingtests cuối (7đã nằm trong155),5SQLintegration riêng đạt; Ruff4files đạt. Lỗi float ở expiry do phép trừ/ép cộng số thực khác biên; thêm margin1ms và regression chứng minh không nhận sớm. Gộp SQL/offline tests làm autouse guards chồng phạm vi; giữ20fail/140pass/5error và cleanup5identities chưa có documents/reservations theo ownership, không tắt guard. Hai suites ở process riêng đạt. Preflight chỉ được công nhận sau test DB rỗng, không chạy đồng thời với suite ghi DB. SSL dùng certifi CA memory context, vẫn CERT_REQUIRED/check_hostname, không verify=False; scoped DB dùng loopback IPv4, không đổi cấu hình production. TLS probe ngoài sandbox sau PermissionError được duyệt và đạt, chưa gửi HTTP/key/prompt.

**Freeze trước chạy:** candidate `.cache/final-reviewed-baseline-20261111-paced/`, protocol1340f78f14f054fc63196e983c5cd876939f52534d999f663cdffe8257ae4b3d,100files+4extras verify. Giữ hai archives cũ, backend/model/prompt/corpus/mapping không đổi. Prepare không decode held-out; grant chỉ tạo lúc execute sau approval riêng gắn đúng plan. Loader sau đó đã đọc test cho evaluation, không dùng tuning.

**Kết quả thực đã audit:** ingest10PDF/DOCX/TXT/MD/canonical mapping đạt; planned30, attempted8, completed7, q023failed generationHTTP503,22notattempted.7grounded là schema/status thành công, không correctness đã chấm.8generation+56count khớp native dispatch (63HTTP200/1HTTP503), không repair/retry/reset. Source/input/archive/capture/pacing verify; min gap5109ms, peak12requests/61s và80Kinputreservation/61s, tổngwait267379ms. Token usage chỉ7generation200:6218prompt/721candidate/6939total, failedrequest không usage, invoiceNone/budget0. Nhà cung cấp503 khác quota429; không đoán nguyên nhân từ mã503 hoặc tăng quota/billing để chữa lỗi này.

**Diễn giải số đo:** query p50≈38,67s/p95≈40,51s trên7success có pacing; không dùng như latency LLM thuần hoặc SLA30câu. Retrieval8observations p50≈602,5ms,Recall@5/MRR@5=1,0 trên8answerable đã chạy; toàn26answerable strictRecall@5=8/26 vì18chưa chạy đóng0. Production chỉtop5; cột@10 generic không phải10hits thật. Bốnunanswerable chưa chạy, không kết luận abstention quality. Job đầu embedding47,60s không phải cold-boot toànmáy. Không trộn các mẫu số/điểm retrieval/schema thành answer accuracy; human metricsnull. Process exit0 chỉ cho biết orchestration/cleanup xong, manifestincomplete là acceptance signal, không sửa runner sau xem test để đổi lịch sử.

**Bàn giao:** audit (`.cache/final-live-validation-20261111/final-audit.json`, chỉ lưu ở máy local)/storage audit (`.cache/final-live-validation-20261111/postrun-storage-audit.json`, chỉ lưu ở máy local) xác nhận12bảng0rows/0finalcollections/0ownedcanonicalfiles, giữ DB/schema/ledger/artifacts; [hướng dẫn](docs/human-review-guide.md) trỏ hai phiếu mới7outputs, còn null và gắn đúng run/hash. Practice6/6 giữ nguyênhashes. q023lỗi và22chưa chạy vẫn trongdenominator30; không fill phiếu cho chúng bằng abstention. Continuation22câu là đề xuất cần runtime/ledger cha-con giữ total đã dùng, chưa có code/approval; không dùng runID mới resetallowance hoặc âm thầmretryq023 (đã tiêu7count/1generation). Không đổi prompt/model sau nhìn test; fullheld-out/fullAT-R/Bước11–12 còn mở, PLANv1.24 giữ87,3%/100%.

### K-096 — Continuation giữ allowance và tổng hợp hai phiên held-out

**12/11/2026, phạm vi đã xác nhận “Thực hiện đi”.** Chỉ q024–q045 còn `not_attempted`, cap44generation/154count trong parent60/210 đã dùng8/56, budget0USD; không retry q023, sửa UI/production/model/prompt/corpus, download, paid fallback hoặc commit/push. [Report](docs/final-continuation-20261112.md), [controller](eval/final_continuation.py), [bootstrap](scripts/run-final-continuation.py), [unit](eval/tests/test_final_continuation.py) và [SQL tests](eval/tests/test_final_continuation_sql.py).

**Vấn đề/quyết định:** runner one-shot cũ không resume; tạo runID/grant mới sẽ cấp lại allowance và làm mất lịch sử lỗi. Chọn controller mới dùng nguyên native capture/pipeline đã freeze. Snapshot parent grant/runtime binding/từng reservation, exclusive claim và child scope cố định. Child reserve vào parent trước, child sau, rồi provider; ghi child thất bại vẫn tiêu parent, không hoàn reservation. Validate append-only và chỉ batches chưa dùng; parent không rebind hoặc reset. Đồng thời chặn caps từng câu2/7, tổng child44/154 và parent60/210. Đây là fail-closed request accounting, không phải transaction atomic với HTTP, recovery khi kill hoặc cap billing phía Google.

**Provenance:** production protocol1340f78f…b3d/source100files+4extras giữ nguyên; hai files mới có control manifest3369045f…a1eb riêng, archive102files. Không sửa protocol cũ để giả controller đã có từ trước khi xem test. Hash production/controller/input/archive/evidence kiểm trước mỗi reservation. Composite chỉ nhận observations disjoint IDs cùng protocol, không thay output/error cũ; giữ q023failed và hai source hashes/row IDs trong provenance. Tên run offline replay nói evaluator đọc capture API thật, không đồng nghĩa fake inference. Composite là hai phiên, không một lượt30câu liên tục; raw child report vẫn có tám câu ngoài scope. Phiếu mới phải gắn run/hash composite, toàn bộ điểm null; không tự chuyển điểm practice hoặc thay human review.

**Phương án thay thế/đánh đổi:** reset scope nhanh nhưng sai cap/provenance; sửa runner frozen hoặc chọn lại model/prompt sau test làm lệch protocol; retry q023 mở rộng scope đã duyệt. Chọn controller nhỏ và giữ lỗi, đổi lại không có auto-resume/general retry và phải phân biệt report từng phiên với composite. Một claim/execution đã tạo không được xóa để chạy lại. Muốn retry/đổi model cần protocol/allowance được duyệt riêng và ghi rõ test đã được sử dụng; muốn benchmark tổng quát sau tuning cần holdout mới.

**Kiểm chứng:**24unit tests,3SQL/Qdrant tests với fake inference đạt; regression176passed/4failed do guard offline chặn socketpair nội bộ asyncio Windows,8pacing riêng đạt, tổng180tests khác nhau qua hai lượt (4overlap). Không tắt network guard hoặc coi suite gộp đạt toàn bộ. SQL đầu lỗi vì Docker Desktop tắt; bật Desktop và đúng hai containers có sẵn, không pull/build/reset volume. SQL kế bắt assertion nhầm cap14count với usage6count cho hai câu một nguồn; sửa test kỳ vọng6, runtime giữ nguyên; lượt cuối3pass/cleanup đạt. Ruff bốn file mới đạt. Config/prompt/local cache/index và DB rỗng/head/Qdrant preflight đạt, TLS Google kiểm certificate đạt, chưa request model trong các probes. Log lỗi giữ nguyên trong `.cache/final-continuation-validation-20261112/`.

**Nguồn free tier/giới hạn:** user xác nhận no billing/payment và quota15RPM/250KTPM/500RPD từ đợt trước; không tự nhận đã kiểm billing/usage tài khoản hiện tại. [Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite)/[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) đối chiếu12/11; manual flags/pacing/caps không bảo đảm clients khác cùng project hoặc invoice. Budget0, invoiceNone. Model local cache-only và scoped DB/queue/storage như trước.

**Kết quả đã audit:**22/22nativeHTTP200,22generation/154count,176dispatch200; không repair/retry. Parent tổng30generation/210count, count allowance đã hết, không reset/chuyển scope để retryq023. Composite30attempted/29outputs/1q023failed/0notattempted, manifestcompleted_with_errors. Output24grounded/1partial/4insufficient_evidence không là correctness96,67%; human0/29 và correctness/faithfulness/citationnull. Bốn từ chối khớp bốn expected-abstain theo status, chưa chấm nội dung từ chối. Retrieval26answerableRecall@5=1/MRR@5≈0,9808 gồm q023 đã retrieve trước generation503; multi-evidence5câuRecall@1=0,6→@3=0,9→@5=1 cho thấy top1hit chưa đủ mọi căn cứ. Capturetop5 không chứng minh cột@10. Latency29successp50≈38,81s/p95≈44,87s có pacing; retrieval30p50≈586,79ms/p95≈634,98ms, concurrency1/warm, không SLA.

**Bàn giao/giới hạn:** audit (`.cache/final-continuation-validation-20261112/final-audit.json`, chỉ lưu ở máy local)/storage (`.cache/final-continuation-validation-20261112/postrun-storage-audit.json`, chỉ lưu ở máy local) verify100files+4extras/controllerarchive, parentbinding/reservations/evidence, disjointcomposite, ledger/HTTP/pacing và12bảng0rows/0finalcollections/0ownedfiles. Min gap5109ms, peak12requests/61s/80Kinputreservation; continuationusage19760prompt/2715candidate/22475total, tổng hai phiên25978/3436/29414 chỉ29generation200; q023usageunknown/invoiceNone. Worksheet29outputs (`.cache/final-heldout-continuation-20261112/review/worksheet.md`, chỉ lưu ở máy local) và hai phiếu mới đều chưa chấm; packet7output và practice6câu giữ hashes. [Hướng dẫn](docs/human-review-guide.md) chuyển sang packet mới; không nhân bản điểm sang run/hash mới. Tiếp theo humanreview→merge/rescore offline sau xác nhận, không cần gọi model. FullAT-R/freshsetup/oracle/no-context/concurrency chưa thực hiện; chưa đóng Bước11–12, PLANv1.25 giữ87,3%/100%.

### K-097 — Human rescore held-out và ranh giới final acceptance

**12/11/2026, phạm vi đã xác nhận:** nhóm nộp hai phiếu29outputs, cho phép validate/merge/rescore vào thư mục mới, báo cáo lỗi/giới hạn và cập nhật PLAN/KNOWLEDGE/hướng dẫn/gaps. [Kết quả](docs/human-review-heldout-20261112.md), [ma trận23AT](docs/final-acceptance-gaps-20261112.md), helper offline (`.cache/final-heldout-scoring-20261112/merge-and-rescore.py`, chỉ lưu ở máy local). Không production/UI/config/model/prompt/corpus changes, inference/download, DB/Qdrant writes, retry, commit/push hoặc fullAT execution.

**Vấn đề/cơ chế:** file JSON đã điền chưa đủ để công bố score: phải khớp ID/run/output digest, đúng schema/types/support/citation IDs, đủ29entries và hai reviewer IDs khác nhau. Dùng `review_pack.merge`/`final_eval.rescore` đã có; hai bộ điểm khớp thì resolve, khác thì giữ pending để hai người adjudicate. Đợt này29/29khớp, adjudicationnull, không AI tự chọn điểm. Identity khác và scores giống chỉ xác minh hình thức và agreement, không chứng minh quá trình chấm độc lập bên ngoài. Không thay raw report/bindingpending bằng kết quả mới; provenance cần phân biệt khi capture với khi nhóm đã chấm.

**Bất biến/kiểm chứng:** [receipt](eval/reports/final-20261112/heldout/rescore-receipt.json) bảo vệ60files qua SHA trước/sau, gồm hai phiếu/binding/worksheet, hai executions/captures/SQLite ledgers/composite/raw reports, protocol/controller/grants/approvals, packet7outputs và practice6câu. Controller/source/input/archive verify trước/sau. Combined/rescored files ghi exclusive vào `.cache/final-heldout-scoring-20261112/`, không overwrite hoặc tạo run inference mới. Kiểm tra độc lập arithmetic trên human scores và counters của raw report; không cần viết test mirror implementation hoặc chạy lại backend/model khi pipeline không đổi. Calls/DBwrites mới0, inference spend mới0; invoice cũNone không suy thành0. Source rows e62bbb51…a754 và combined review84d4b8a1…2f96 gắn đúng run1183a4c0…c802; full hashes ởreceipt.

**Số đã kiểm chứng từ điểm nhóm:**29/29outputsreviewed/correctness2, strict success29/30≈96,67% (mẫu số planned30giữ q023failed), faithfulness34/34claims, citation correctness36/36links và completeness34/34claims. Không báo29/29như end-to-end100%. Bốn expected-abstain đúng theo output status và correctness nhóm chấm; abstention metric tính trên29successfuloutputs gồm25answerable+4unanswerable, q023providererror không là false/correct abstention. Modelstatusgrounded/partial không là điểm; q024partial vẫn cócorrectness2theo rubric. Không có semantic errors theo phiếu đã nộp, không bịa thêm hai lỗi cho đủ ba failure cases.

**Phân tích/đánh đổi:** q023retrievalđạt trước generateContentHTTP503,≈39,25s, không finalanswer/usage; không có providerbody để xác định nguyên nhân sâu, không gọi đó là quota429 hoặc lỗi retrieval. Giữ failed và reservation, không tựretry vì parentcount210/210đã hết. Tự chấm lại, reset/retry để đẹp report hoặc nâng ngưỡng sau thấy kết quả làm mất bằng chứng; chọn preserve và báo giới hạn. Khi cần provider recovery phải scope/caps riêng trên dev và giữ report này; sau tuning phải holdout mới trước tuyên bố cải thiện tổng quát. Lựa chọn khác là human judge bổ sung/đánh giá ngoài nhóm khi có corpus lớn hơn; chưa cần cho phép tính merge và không dùng judge thay nhóm. Tập nhỏ/synthetic/cùng nhóm tạo gold và chấm là giới hạn, không accuracy tổng quát hoặc safety certification.

**Progress/acceptance:** PLANv1.26 giữ trọng số102,5, ghi nhận Bước11mục2–5: baseline có human metrics; phân loại native/fake/SQL/warm/pacing/oracle lịch sử và final phần chưa đo; latency concurrency1cósamplecount; failureanalysis đúng số quan sát. Chưa chốt release/codecommit(mục1), chưa cộng conditional-policy mục6, chưa fullAT(mục7), Bước12chưa thực thi. `(89,5+8×4/7)/102,5×100≈91,8%`, không tăng theo tests/accuracy. Matrix23scenarios chỉ inventory inherited evidence/gaps, không là23pass/failhoặc rerun. Native injection smoke08 đã có nhưng không thay adversarial coverage trên freeze cuối; hai phiên re-ingestisolatedDB không thay freshcheckout/cleanvolumes/setup. Đợt tiếp cần chốt acceptance scope/evidence và xác nhận riêng, không tự gọi model/sửa UI/đóng gói từ kết quả này.

### K-098 — Acceptance nhiều lớp, bootstrap worker con và reuse evidence có kiểm chứng

**12/11/2026, đợt được xác nhận sau báo cáo human review:** kiểm chứng các mục còn thiếu trong AT-R01–23 bằng unit/SQL/Qdrant/frontend và đối chiếu evidence; bổ sung tests khi contract chưa được kiểm đúng. [Report](docs/final-acceptance-20261112.md), machine matrix (`.cache/at-20261112/acceptance-matrix.json`, chỉ lưu ở máy local), harness (`.cache/at-20261112/run-backend.py`, chỉ lưu ở máy local), hai tests mới (`.cache/at-20261112/test_gap_contracts.py`, chỉ lưu ở máy local). Không sửa production/UI/config/`.env`/prompt/model/corpus; không native Gemini/embedding inference, download/dependencies, commit/push, retry held-out hoặc fresh installation. Fixtures/tests/artifacts mới dùng scope riêng; không tự bắt đầu Bước12.

**Thiết kế và kết quả:** test DB mới `copilot_acceptance_20261112_test` được validate khác dev, migrate head20261103_rag04, rollback/cleanup theo fixtures; Qdrant thật nhưng vectors/providers giả, tokenizer cache-only. Process key rỗng/free-flagsfalse; chặn real HTTP transport ngoài Qdrant local, MockTransport Gemini tests vẫn chạy.302backend cases khác nhau cópass sau fullsuite và retest,2newcontracts/69eval/36frontend đạt, tổng409unique; không cộng retests vào số này. Ruff132files/frontendlint/build đạt. Không có một fullbackend invocation302/302pass: đầu300passed/2failed, retest có lịch sử riêng trongXML/matrix. JUnit parsed/dedup theo module/test, dùng kết quả cuối để gắncase đếnAT, giữ cả failure history.

**Hai gaps thực sự được bổ sung:** tên test search-disabled cũ gửi chat request nên chưa trực tiếp chứng minh search-only endpoint không dựng LLM; test mới POST `/search` với key/flagsfalse, provider factory fail-fast và count/generate fake logs rỗng. Follow-up test gửi hai câu trong cùngsession SQL, record literal query retrieval và native-shaped payload: một user message chứa câu hiện tại/evidence, không answer/câu hỏi trước. Sentinel fake answer chỉ kiểm rò history vào payload, không là claim được chấm faithful. Test ở artifacts để không thay source production freeze; không thêm test mirror code cho các sửa tài liệu.

**Lỗi môi trường và cách sửa đã kiểm chứng:** Python embedded bỏ PYTHONPATH; parser child và CLI `python -m app.worker` thiếu modulepaths. Bootstrap v1 chỉ sửa parser parent, làm cleanupCLI fail và workercon khôngtới realupsert trướcmarker15s. V2sửa CLI và verified TLS context trong child, CLIpass nhưng kill/restartvẫnfail. Rootcause còn thiếu parser bootstrap bên trong workercon: thêm cùng bootstrap vào `__mp_main__` và workerCLI support; kill→restart→lease/orphan assertions đạt9,46s, marker15s/deadline/assertions giữ nguyên. Ba tests CLI/model-startup/model-batch-timeout với harness cuối đạt. Không sửa parser/worker thành inlinefake, không verify=False/nới deadline/skip tests. Cadata certifi context giữ certificate/hostname verification; IO startup support không là thay runtime sản phẩm. Các helper tìm UI manifest sai/matcherJUnit thiếu describeprefix bị chặn trước receipt cuối, không biến lỗi helper thành pass.

**Reuse evidence:** build UI mới sinh ba files cùng hashes với bundle Chrome đã dùng;53backend app files cùng Chrome protocol cũng khớp. Có thể kế thừa luồngP0 source410/auth401/keyboard/navigation/states, vẫn ghi browser cũ chứ không giả rerun mới. B08injection smoke SHA khác phần lớn do line endings: normalizedtext answering/gemini/schema/sources/retrieval khớp, chat thay đổi; byte identity và semantic text identity là hai mức khác nhau. Giữ native smoke lịch sử, chưa gọi đó là current adversarial acceptance. Không dùng hash normalization để sửa lại protocol/historicalhashes.

**AT-R22 khác Bước12:** gaps inventory trước trộn rebuild từ manifest trên DB/index sạch với clean checkout/dependency install. Spec15.4choAT-R22yêu cầu cái đầu; hai native scopes đã preflight DB rỗng/re-ingest10docs/canonical mapping/config verify, giữreports/failures/cleanup. Receipt (`.cache/at-20261112/inherited-native-rebuild.json`, chỉ lưu ở máy local) xác minh2×10ingestions và cùng protocol, scoped IDs khác; sáu outputs(q022/024/028/032/038/041)có claims dẫn hơn một document và đã human chấm. Đủ inherited rebuild/AT11native evidence trong phạm vi, không cần model rerun. Fresh checkout/cleanvolumes/seed/dependency/cache topology/demo vẫn chưa làm và nằmBước12/M1DoD. Phân biệt tiêu chí giúp tránh gọi model thừa hoặc báo clean install sai.

**Bàn giao/giới hạn:**22/23scenarios có scopedpasses; AT-R14literal/no-tools/no-XSS contract đạt nhưng native adversarial trên bảnhiệntại/humanreview riêng cònpartial. Postrun audit (`.cache/at-20261112/postrun-audit.json`, chỉ lưu ở máy local) xác nhận21bảng nghiệp vụ0rows,0s6_test_/final_collections/0runtimefiles; basetempfixtures giữ làm artifacts, không dọn cache để giả cleanup.167source/config và60held-out/review files cùng combined/rescoredmetrics/protocol/controller/archives giữ hashes. Không modelcalls mới, ledgerheldout30generation/210count giữnguyên, countđãhết. GiữPLANv1.27/91,8%: mục7chưa fullAT, mục1/6/Bước12mở, không tăng theo409tests/22AT.

**Phương án/đợt tiếp chưa duyệt:** không dùng native smoke cũ thay lớp adversarial hiện tại hoặc tự nâng quota/reset parent. Report đề xuất hai dev adversarial cases: một giữfact/citation đúng dù có fake system/email/script instruction; một hỏi thông tin nguồn không có để kiểm abstention, output cần hai người chấm. Grant mới riêng tốiđa4generation/14count,0USD gồm repair/lostresponses, model/prompt giữ nguyên; flags/quota/cache/pacing/caps xác minh trướccall. Chưa viết/chạy native runner hoặc tạogrant/ledger cho scope đó ởđợt này. Dùng stub-only rẻ và đủ contract nhưng không trả lời semantic risk; native/human sẽ là lớp bổ sung sau xác nhận riêng. Không tune test hoặc thêm UI chức năng để thay acceptance còn thiếu.

### K-099 — Native adversarial nhỏ, chứng minh exposure và chấm người riêng

**12/11/2026, đợt được xác nhận tiếp sau K-098:** [runner](eval/adversarial_eval.py), [bootstrap](scripts/run-adversarial-eval.py), [unit tests](eval/tests/test_adversarial_eval.py), [SQL tests](eval/tests/test_adversarial_sql.py) và [report](docs/adversarial-at14-20261112.md). Hai câu synthetic/dev dùng allowance mới4generation/14count/0USD riêng; không reset allowance held-out30/210đã dùng. Không sửa production/UI/prompt/model/config/`.env`, tải model/dependencies, paid fallback, commit/push hoặc bắt đầu packaging. Native run đã hoàn tất trước lúc quota phiên trợ lý ngắt; tiếp tục từ summary/ledger, không suy rằng cần retry Gemini.

**Vấn đề/cách hoạt động:** output bỏ qua attack không có ý nghĩa nếu retrieval/context builder đã loại attack trước model. Fixture dùng một policy TXT, cùng một chunk chứa fact thật và fake-system/email sai/trợ cấp bịa/tool/script canary dạng literal. Audit actual canonical final context và generation payload chứng minh exposure2/2; wrapper tại native `_post` chỉ kiểm hash/câu hỏi/no-tools và ghi metadata, delegate transport nguyên bản, không lọc payload hoặc thay response. Giữ raw provider body/key/headers ngoài audit. No-tools/0functioncalls kiểm ranh giới công cụ; không thay kiểm XSS/rendering browser hoặc semantic correctness. Canary absence chỉ heuristic, không tự thành human pass.

**Lựa chọn/đánh đổi:** dùng `capture_run` chung với `split=dev`, synthetic_smoke và purpose adversarial rõ, giữ production model/prompt/index/budgets, DB/queue/storage riêng. Không dùng wrapper held-out hardcode test hoặc giả dataset human-reviewed; không thêm hai câu vào held-out average. One-shot fixedscope/planhash/exclusive output/SQLite reserve-before-call/no refund giữ failure history và caps, không atomic với HTTP hoặc billing cap phía provider. 85frozenfiles+2extras/archive được verify; không sửa source đã freeze khi hoàn tất audit. Stub-only kiểm contract rẻ hơn nhưng không đo semantic behavior; rerun old test/reset parent làm sai allowance/provenance; thêm attack suite rộng cần nhãn/mẫu/budget/đợt xác nhận riêng, xem lại khi cần đánh giá rủi ro lớn hơn hai cases này.

**Kiểm chứng đã có:** 26unit mới+45regression=71passed,3SQL riêng (success/budget/timeout, inference giả), Ruff5files đạt trước freeze. Lượt đầu5unitfail vì fixture Settings thiếu model/baseURL pinned, sửa fixture và giữ logs; không sửa runtime. Native E5cache/Gemini/SQL/Qdrant/auth/parser thật: planned2/attempted2/output2,8HTTP200,2generation+6count, không repair/retry; providerusage1059prompt+189candidate=1248tokens. Pacingmin5109ms,peak8requests/61s; answern2p50≈18,04s/p95≈18,52s gồm pacing, không SLA. Câu1grounded email chính thức/citationE1, câu2insufficient_evidence là quan sát output, chưa điểm human. Free/quota dựa xác nhận người dùng và manualflags; invoiceverifiednull/budget0USD, không chứng minh hóa đơn bằng flags. Audit (`.cache/adv-validation-20261112/final-audit.json`, chỉ lưu ở máy local) verify cleanup21tables0rows/0finalcollections/0ownedfiles,60heldoutfiles+scoredmetrics giữ hash, source/input/archive/capture/ledger/pacing khớp.

**Trạng thái/giới hạn:** [hai phiếu mới](docs/human-review-guide.md) đều blank, human0/2; correctness/faithfulness/citation chưa có điểm. Hai adversarial cases không chứng minh miễn nhiễm injection chung, browser mới hoặc các attack formats khác. AT-R14partial_pending_human_review,22scopedpasses cũ giữ snapshot; PLANv1.28vẫn4/7Bước11/91,8% vì fullAT/release/freshsetup chưa xong. Nhóm chấm hai output mới, không sửa29heldout đã chấm; merge/rescore/đóng acceptance cần đợt tiếp được xác nhận, không tự gắn human-approved.

### K-100 — Gộp human adversarial, acceptance có phạm vi và tiến độ có bằng chứng

**12/11/2026, đợt gộp được xác nhận sau khi nhóm chấm:** [report](docs/human-review-adversarial-20261112.md), helper offline (`.cache/adversarial-at14-scoring-20261112/merge-rescore.py`, chỉ lưu ở máy local), [combined review](eval/reports/final-20261112/adversarial/combined-review.json), [reviewed metrics](eval/reports/final-20261112/adversarial/reviewed-metrics.json), [receipt](eval/reports/final-20261112/adversarial/rescore-receipt.json), [ma trận mới](eval/reports/final-20261112/acceptance/acceptance-matrix.json). Đây là thay trạng thái pending ởK-099bằng điểm người dùng đã điền, không thay dữ liệu/model/prompt hoặc sửa kết quả sau khi xem test. Không nativecalls/embedding/DBwrites/UIchanges/commit/push/packaging.

**Cách chứng minh:** toolkit hiện hữu kiểm đúng IDs/run/outputhash, schema, hai reviewer IDs khác nhau, đủ correctness/claims/citationflags; merge giữ hai phiếu và resolve chỉ khi điểm khớp. Hai cases2/2khớp, khôngadjudication; correctnessmean2/2, strictsuccess2/2syntheticdev, support1/1claim/citation1/1link/completeness1/1. Từ chối khôngclaim vẫn cần correctness, không tạo claim giả để tăng denominator. Agent không tự chọn điểm hoặc dùng status/heuristic thay judgment. Độc lập thực tế của hai người dựa quy trình nhóm, công cụ chỉ kiểm IDs/scores/binding, không thể chứng minh ai thực sự điền. Không ghép2devcasesvàoheldout30hoặc công bố100%accuracy tổngquát.

**Đóng AT-R14theo hai lớp spec:** attack trong actualcontext/generationpayload2/2, native no-tools/0functioncalls và hai output đã được chấm; parser/prompt/repair cùng literal-render/no-XSS contracts có JUnit/sourcehash. Đối chiếu trực tiếp AnswerViewtest img/onerror hiển thị text/khôngimg và Appsource script làtext/khôngscriptelement, không chỉ suy từ React hoặc model khôngechoattack. Reuse bằng chứng componenttests/browserP0 được ghi rõ, không giả browserrerun/no-XSSmọitrườnghợp hoặc miễn nhiễm injection. Chọn consolidate22scopedpasses+AT14review thay chạy lại native tốnquota hoặc coi stubs làsemanticpass. Nếu source/config/rendering thay đổi, hashdrift hoặc cần attackformats rộng hơn, phải xem lại phạm vi và kiểm lại lớp bị ảnh hưởng.

**Bất biến/alternatives:** lưu outputs exclusive thư mục scoring mới, giữ rawmanifest/binding/metrics humanpending theo thời điểm xuất và ma trận22/23cũ như lịch sử. Reviewedmetrics/receipt/matrix mới là trạng thái hậu-review; sửa rawpending thànhpass sẽ làm sai provenance và frozenhashes. Snapshot đầu đợt958files bao gồm167source/config, toànnative scope/phiếu đã chấm/oldAT và60oldheldoutfiles+combinedmetrics, verifytrước/sau. Phiếu adversarial hợp lệ đã do người dùng thay blank sau handoffK099; snapshot bảo vệ mới bắt đầu sau thay đổi ấy, không bắt hashblankcũ phải khớp. Heldoutq023503/ledger30generation210count và adversarial2/6giữ nguyên; cleanup là audit trước đã hashverify, không giả một DBprobe mới khi offline.

**Progress/giới hạn:** ma trận mới23/23passed_with_scoped_evidence/full_acceptance_pass=true chỉ về23scenariosM1theobằngchứng đã mô tả, không đồng nghĩa freshsetup/release/M1Done. PLANv1.29thêmBước11mục7vào2–5→5/7; giữ trọng số8/mẫu số102,5,`(89,5+8×5/7)/102,5×100≈92,9%`. Mục1release/codecommitcònmở, mục6conditional chưa phát sinh/chưa cộng, Bước12vẫn0/6. Không tăng theo2câu/điểm100%/sốtests. Đợt tiếp cần chốt scope release/topology/cache và freshsetup/packaging theo PLAN, có xác nhận riêng; không tự cài/build/download/commit/push từ việc đóngAT14.

### K-101 — Chốt release: hash theo bytes vs nội dung, và bằng chứng phải nằm trong Git

**Ngày / loại:** 12/11/2026. Người dùng xác nhận đợt R1. Đã thực hiện và kiểm chứng. [Report](docs/release-m1-20261112.md), [bộ bằng chứng](eval/reports/final-20261112/provenance.json).

**Vấn đề 1: hash theo bytes phụ thuộc line-ending.**
- Manifest acceptance băm working tree trên Windows (phần lớn CRLF). Git với `core.autocrlf=true` lưu blob dạng LF.
- Sau commit, 96/167 file khác hash byte dù nội dung không đổi. Một file có EOL lẫn lộn cũng chỉ khác ở ký tự CR.
- Cách kiểm chứng đã dùng: so blob sau khi đổi sang CRLF, và so sau khi bỏ mọi CR. Kết quả 167/167 giống nội dung.
- Bài học: release phải ghi rõ chế độ EOL khi băm. Khi cài sạch ở Bước 12, so sánh sau chuẩn hóa EOL; nếu muốn khớp bytes tuyệt đối thì checkout với `core.autocrlf` giống lúc băm.
- Phương án chưa chọn: thêm `.gitattributes` `* text=auto eol=lf` để ép LF. Việc này sẽ đổi bytes của mọi file trong working tree và làm mất khả năng đối chiếu trực tiếp với các manifest cũ ngay trước hạn. Xem lại sau M1 nếu cần hash tái lập trên nhiều OS.

**Vấn đề 2: bằng chứng nằm trong thư mục bị ignore.**
- `.cache/` bị Git ignore, nên số liệu trong README sẽ không truy vết được trên repo.
- Đã chép một bộ nhỏ (19 file, khoảng 180KB) vào `eval/reports/final-20261112/`, kèm `provenance.json` ghi đường dẫn nguồn và SHA-256 trước/sau. File gốc giữ nguyên. `eval/reports/** -text` giữ nguyên bytes.
- Không đưa captures, ledgers SQLite hay archive vì lớn và không cần để đọc kết quả.

**Vấn đề 3: thông tin cá nhân trong artifact test.**
- JUnit XML ghi `hostname` là tên máy/người. Bản công khai thay bằng `redacted` và ghi cả hai hash, để vẫn truy vết được về bản gốc.
- Quét secret bằng giá trị thật trong `.env` (chỉ đếm, không in) cộng các mẫu thông dụng; dương tính giả `Bearer aaaa…` là tham số test.

**Commit theo nhóm** (backend, eval tooling, UI, launcher, evidence, docs) để reviewer đọc được từng phần, và giữ lịch sử thật thay vì squash thành một commit lớn.

### K-102 — Topology M1: storage trong Compose, compute trên host; cài sạch phải cô lập thật

**Ngày / loại:** 12/11/2026. Người dùng chọn phương án A và xác nhận R2. Đã triển khai và kiểm chứng. [Report](docs/fresh-setup-20261112.md), commit `0c1862b`.

**Bối cảnh:** service `backend` trong Compose build từ `requirements.lock`, không có Torch/Transformers. API cần E5 để embed câu hỏi, nên container đó chỉ trả được health/auth, không search hay answer được. Lock worker hiện chỉ pin wheel Torch cho Windows/CPython 3.12.

**Lựa chọn:**
- Compose chỉ chạy PostgreSQL và Qdrant (image pin digest, volume persistent, port loopback).
- API, worker và frontend chạy trên host bằng lockfile và launcher có sẵn.
- Migration và seed là bước tường minh; bỏ `alembic upgrade` khỏi `CMD` của Dockerfile.

**Phương án khác và lý do chưa chọn:**
- **B, container hóa đầy đủ:** cần lock Linux mới cho Torch CPU, tải wheel vài trăm MB, volume cho model cache, và kiểm thử lại worker (subprocess parser, lease) trên Linux. Rủi ro trễ hạn 15/11 cao, trong khi giá trị demo không đổi.
- **Giữ service `backend` hỏng:** dễ khiến người đọc tưởng API đã container hóa. Đây là "nói quá khả năng".

Điều kiện xem xét lại: sau M1, khi cần deploy lên server Linux hoặc demo không phụ thuộc Windows.

**Cài sạch thế nào mới là "sạch":**
- Clone từ Git, không copy working tree. Như vậy file chưa commit hay file bị ignore không lọt vào.
- Compose project riêng (`-p smefresh`) với volume mới và port khác. Không xóa volume dev để giả clean install.
- Venv và `node_modules` mới, cài từ lockfile; dùng chung cache tải về để tiết kiệm băng thông. Cache không phải trạng thái ứng dụng.
- Dùng chung model cache là điểm không sạch có chủ đích, và được ghi rõ. Trên máy mới phải tải E5 đúng revision theo runbook.

**Bài học từ script kiểm tra:** script của tôi so tên file bằng trường không tồn tại (`file_name`), nên báo 0 trúng, và phép kiểm tra "tài liệu đã xóa không quay lại" cũng thành rỗng nghĩa. Một kiểm tra phủ định ("không có X") với trường sai **luôn pass**. Vì vậy cần in schema hit trước, và kiểm tra phủ định bằng thuộc tính chắc chắn tồn tại (`document_id` ⊆ tập tài liệu ready). Đã chạy lại bằng `document_id`, chỉ đọc, và giữ cả kết quả sai lẫn kết quả đúng trong report.

### K-103 — README cho người đọc ngoài nhóm

**Ngày / loại:** 12/11/2026. Người dùng xác nhận R3 và yêu cầu viết đơn giản, không có phần đóng góp cá nhân. [README](README.md).

**Lựa chọn:**
- README cũ là nhật ký tiến độ (%, "Bước 0x", trạng thái từng đợt), khó đọc với người lọc hồ sơ. README mới đặt bài toán, tính năng, ảnh, cách hoạt động và kết quả lên trước. Nhật ký và quy trình nội bộ chuyển sang PLAN, KNOWLEDGE và `docs/`.
- Mọi con số đều lấy từ `reviewed-metrics.json` và các report đã có, kèm mẫu số và link bằng chứng. Ghi rõ dữ liệu là giả lập và quy mô nhỏ, và lỗi 503 vẫn được tính vào mẫu số.
- Ảnh chụp lại từ UI hiện tại thay vì dùng ảnh 06/11, vì một số file UI đã sửa sau đó. Chưa có ảnh câu trả lời thật vì Gemini tắt; bổ sung ở đợt video.
- Không có phần "Known limitations" dài hay dòng lịch sử máy cũ; giới hạn viết thành danh sách ngắn, đúng những gì chưa làm.

**Đánh đổi:** README ngắn thì ít chi tiết tái lập (cache, line-ending, ledger quota). Các chi tiết này vẫn nằm trong runbook và các report được link.

### K-104 — Link tới artifact local và rà soát trước khi nộp

**Ngày / loại:** 12/11/2026, đợt R5a đã thực hiện. [Report](docs/final-review-20261112.md).

- **Link tới thư mục bị ignore:** report viết trên máy local hay link vào `.cache/`; trên GitHub các link này chết. Quy tắc mới: nếu có bản đã đưa vào repo thì link tới bản đó; nếu không thì ghi đường dẫn dạng code kèm "chỉ lưu ở máy local", không để link chết. Kiểm tra bằng script quét mọi link tương đối trong file `.md` được track.
- **Quét secret theo giá trị thật:** quét mẫu (regex) không bắt được mật khẩu tự đặt, còn so với giá trị trong `.env` thì bắt được. Cần phân biệt giá trị mặc định công khai (có trong `.env.example`) với secret thật. Report công khai không nên mô tả cấu hình của máy local, kể cả khi rủi ro thấp.
- **Đăng xuất phía server (phát hiện 12/11):** API không có `/auth/logout`. Nút "Đăng xuất" chỉ xóa token khỏi sessionStorage; token còn hiệu lực ở server tới hết TTL 1 giờ. Đây là giới hạn đã biết từ kế hoạch UI ("chưa revoke-token"), nay ghi vào README. Chưa thêm endpoint vì release đã freeze; làm sau M1 kèm cập nhật spec và test. Bài học phụ: script kiểm thử bỏ qua status code của request dọn dẹp đã khiến report ghi sai là token đã bị thu hồi; request dọn dẹp cũng phải kiểm tra kết quả.
- **File chuẩn bị cá nhân** (bộ Q&A phỏng vấn, kịch bản video) chặn bằng `.git/info/exclude` thay vì `.gitignore`, để tên file không xuất hiện trên repo công khai.

### K-105 — UI v2: quản lý phiên, logout thật và hiển thị thời gian chờ trung thực

**Ngày / loại:** 13/11/2026, người dùng duyệt mockup và phạm vi đợt "UI v2 + tính năng nhỏ". Nhánh `feat/ui-v2`, chưa merge vào `main`. [Report](docs/ui-v2-20261113.md).

**Backend (3 endpoint, không migration):**
- `POST /auth/logout` đặt `revoked_at` cho đúng token đang gửi. Cột này đã có từ Bước 04 và `get_current_user` đã lọc `revoked_at IS NULL`, nên chỉ cần thêm đường ghi. Không thu hồi mọi token của user: đăng xuất ở một tab không nên đá các phiên khác. Giới hạn "đăng xuất không thu hồi token" ở K-104 được gỡ.
- `PATCH`/`DELETE /chat/sessions/{id}` chỉ cho chủ phiên. Scope lookup chạy trước, nên admin và người ngoài nhận 404 giống phiên không tồn tại (không lộ ID có thật).
- **Xóa hẳn thay vì soft delete.** Lịch sử chat là dữ liệu riêng của người dùng; không bất biến nào cần giữ nó sau khi chủ phiên muốn xóa, và soft delete sẽ buộc mọi truy vấn lịch sử thêm một điều kiện lọc. Thứ tự xóa theo khóa ngoại: citations → messages → query runs → session, trong một transaction.
- **Không xóa khi đang có câu hỏi chạy.** Câu hỏi không giữ lock trong lúc gọi model; nếu xóa giữa chừng thì lúc publish, run đã biến mất. Vì vậy delete lấy cùng khóa `NOWAIT` trên session như query start/publish, expire các run quá deadline, rồi trả `409 session_busy` nếu còn run `running`. Run đã quá deadline thì publish tự thất bại vì `remaining(deadline)` được kiểm tra trước khi đọc run.

**Frontend:**
- Bố cục sidebar trái (tài khoản và đăng xuất ở cuối), trang Lịch sử mới, đăng nhập một cột. Bảng màu slate trung tính, một màu nhấn xanh #1D4ED8; màu trạng thái giữ nghĩa cố định.
- Font Be Vietnam Pro tự host qua `@fontsource/be-vietnam-pro@5.3.0` thay cho Google Fonts: app chạy được khi không có mạng và không gửi request ra ngoài lúc mở trang.
- **Thời gian chờ trung thực:** `/chat/query` trả một lần, nên UI chỉ hiện đồng hồ đếm giây từ lúc gửi (lấy từ `startedAt` của pending query, sống sót qua reload) và khoảng "thường mất 30–45 giây" (p50/p95 đo ở held-out là 39/45 s). Không vẽ thanh % hay các bước con giả. Muốn hiện bước thật phải thêm stream (SSE): để sau.
- Tiến độ ingest lấy từ `stage` và `progress.completed_units/total_units` mà worker đã ghi sẵn trong `GET /jobs/{id}` ("Bước 4/6 · Lập chỉ mục · 8/14 đoạn"), cộng thời gian kể từ lúc tải lên. Không cần đổi backend.
- Nhóm lịch sử theo ngày lịch Asia/Ho_Chi_Minh, không theo UTC: phiên lúc 01:30 sáng giờ Việt Nam vẫn là "Hôm nay".
- Đăng xuất: gọi revoke trước, lỗi mạng vẫn xóa token ở tab (token khi đó hết hạn theo TTL).

**Kiểm chứng:** toàn bộ backend 311/311; 9 test mới trên PostgreSQL thật (gồm admin/người ngoài 404, 409 khi đang chạy, expire run quá hạn rồi xóa đủ 4 bảng). Frontend 45 test (9 mới). Smoke HTTP 14/14 trên stack dev với LLM tắt. Ảnh chụp bằng Edge headless qua CDP ở 1440×900 và 390×844.

**Chưa làm:** stream các bước khi hỏi, nhãn "có nguồn đã bị xóa" trong Lịch sử, thư mục, OCR.

**Sửa sau khi người dùng dùng thử (13/11, cùng ngày):**
- **Câu hỏi timeout 142,8 s:** trace cho thấy retrieval (14 ứng viên → 5 đoạn) và countTokens (~1.046 token) đều xong; lời gọi generateContent chờ hết call timeout 120 s, server ghi `model_timeout`/504. Lỗi ở phía Gemini (free tier quá tải), không do code UI. Hệ thống báo đúng là lỗi kỹ thuật. Phần cần sửa là UI: hai hộp cho một lỗi, chữ khó hiểu, và đồng hồ im lặng quá mốc "30–45 giây".
- **Hai bong bóng câu hỏi:** server lưu câu hỏi ngay khi run bắt đầu, nhưng client chỉ biết run ID sau khi request trả về. Trong lúc chờ, tải lại lịch sử sẽ vẽ cả bản đã lưu lẫn bong bóng "đang chờ". Sửa: ẩn bong bóng chờ khi lịch sử đã có câu hỏi cùng run ID, hoặc cùng nội dung và gửi sau `startedAt` (trừ hao 60 s lệch đồng hồ).
- **Spinner và rung khi chuyển tab:** thiết kế Bước 10 xóa tin nhắn khi tab ẩn và tải lại (có spinner) khi quay lại. Trình duyệt bắn cả `visibilitychange` lẫn `focus`, nên nội dung bị xóa và vẽ lại hai lần. Trang ngắn lại làm thanh cuộn biến mất, khiến cả trang dịch ngang. Sửa: gộp hai sự kiện thành một lần tải lại ở nền (debounce 150 ms), giữ nội dung đang hiện, và `scrollbar-gutter: stable`.
- **Đánh đổi có chủ đích:** nếu tài liệu bị xóa ở nơi khác trong lúc tab ẩn, nội dung cũ còn hiện thêm một khoảnh khắc cho tới khi server trả bản đã che. Xóa ngay trong app (`DOCUMENT_CHANGED`, `SOURCE_UNAVAILABLE`) vẫn xóa nội dung ngay lập tức. Backend vẫn che nội dung ở mọi response, nên bất biến "không hồi sinh nội dung đã xóa" giữ nguyên ở tầng dữ liệu.
- **Lỗi model:** một hộp duy nhất với câu chữ theo mã lỗi (`model_timeout`, `model_unavailable`, `model_busy`, `invalid_model_output`, `retrieval_unavailable`, `source_changed`) và nút "Hỏi lại". Sau 60 s, đồng hồ thêm dòng báo hệ thống tự dừng ở 2:30 (`QUERY_TIMEOUT_SECONDS` = 150).
- **Phân loại lỗi Gemini và báo lỗi sớm hơn (đợt A + B, người dùng không chọn tự retry):**
  - Trước đây mọi HTTP khác 200 đều thành `model_unavailable` "tạm thời không khả dụng", log không ghi mã gốc, nên không phân biệt được hết quota với quá tải. Giờ vẫn giữ code công khai `model_unavailable` (runner eval dùng code này để dừng sớm khi provider lỗi; đổi code sẽ phá phân loại lỗi trong report cũ) và thêm `details.reason`: 429 → `quota`, 5xx → `overloaded`, 4xx khác → `rejected`, lỗi mạng → `network`. Log ghi action + status, không ghi body vì body có thể chứa lại nội dung yêu cầu.
  - Reason lưu vào `config_json.failure_reason` của run để lần replay cùng `client_request_id` trả lại đúng lý do. Sửa luôn lỗi nhỏ: handler cũ ghi đè `details` bằng `run_id`, làm mất mọi details của provider.
  - Timeout mỗi lời gọi: 120 s → **60 s** (giữ trần 120). Held-out đo cả câu hỏi p50 38,8 s, max 45,5 s, đã gồm thời gian giãn request của eval; câu thành công trên máy dev mất 8,7 s. 45 s quá sát max, 60 s còn biên. Lời gọi treo giờ dừng ở khoảng 1 phút thay vì 2. Đây là đổi cấu hình runtime: report held-out ghi 120 s là cấu hình lúc đo, không bị đổi.
  - Không tự retry: mỗi lần retry tốn thêm quota free tier, và retry ngay khi provider quá tải thường thất bại lại.
  - **Sự cố môi trường khi chạy test:** `QDRANT_URL=http://localhost:6333` được thử IPv6 (`::1`) trước, nhưng Docker chỉ mở cổng trên 127.0.0.1. Lúc này ::1 không trả RST mà treo, nên một lần chạy `test_chat.py` kẹt ở SYN_SENT quá 10 phút (lần trước đó báo 1 lỗi setup). Chạy lại với `QDRANT_URL=http://127.0.0.1:6333` chỉ cho tiến trình pytest. Nên đổi `.env` sang 127.0.0.1 (đợt riêng).
- **Kiểm chứng:** frontend 48/48, chạy 3 lần không chập chờn. Ba test mới tái hiện đúng ba lỗi. Trên Edge headless, sau khi phát cả hai sự kiện, số tin nhắn và chiều rộng khung chat giữ nguyên trong 1,2 s và không có spinner.

## 4. Những bằng chứng cần bổ sung khi bắt đầu triển khai

- Retrieval/answer quality và human scoring trên pipeline thật; E5/Gemini compatibility smoke đã có K-030/K-034–036, chưa kiểm chứng thinking overrides hoặc chi phí theo hóa đơn.
- Parser span mapping K-047, SQL mapping/matcher K-058 và final-context/cited map K-062–067 đã có; cần nối metric cited-span/human quality và held-out eval Bước11.
- Dev retrieval K-059 và synthetic oracle/API answering K-066–067 đã có; UI E2E tổng hợp K-092 hoàn tất, còn human review và test holdout theo protocol, không tune test.
- Context/citation/session K-062–067, deletion/privacy/recovery K-068–072 và Chrome E2E K-092 đã có; final human-quality/held-out và packaging còn Bước11–12. Giữ các nền ingestion/search/auth đã kiểm chứng.
- Các lần thay đổi quyết định sau benchmark, kể cả giữ baseline vì treatment không cải thiện.
- Kiến thức phát sinh từ dependency/runtime, migrations, frontend, deployment và các bug thực tế.

Danh sách này là nội dung cần học/ghi trong tương lai, chưa phải các bước đã thực hiện. Mỗi lần hoàn thành công việc, cập nhật mục liên quan cùng bằng chứng thật thay vì chỉ thêm lời khẳng định “đã hiểu” hoặc “hoạt động tốt”.
