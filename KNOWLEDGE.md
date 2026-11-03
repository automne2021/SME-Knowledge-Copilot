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

## 4. Những bằng chứng cần bổ sung khi bắt đầu triển khai

- Retrieval/answer quality và human scoring trên pipeline thật; E5/Gemini compatibility smoke đã có K-030/K-034–036, chưa kiểm chứng thinking overrides hoặc chi phí theo hóa đơn.
- Parser span mapping K-047, SQL generation mapping và retrieval span loader/matcher K-058 đã có; cần nối context/cited spans và held-out eval Bước 08/11.
- Dev retrieval report đầu tiên K-059 đã có; cần answer/oracle/E2E và test holdout theo protocol, không tune test.
- Context/citation và delete lifecycle tests; search/source action matrix K-055–060, worker K-049–054, parser/upload K-043–048 và auth/schema K-037–042 đã có; answering/delete chưa triển khai.
- Các lần thay đổi quyết định sau benchmark, kể cả giữ baseline vì treatment không cải thiện.
- Kiến thức phát sinh từ dependency/runtime, migrations, frontend, deployment và các bug thực tế.

Danh sách này là nội dung cần học/ghi trong tương lai, chưa phải các bước đã thực hiện. Mỗi lần hoàn thành công việc, cập nhật mục liên quan cùng bằng chứng thật thay vì chỉ thêm lời khẳng định “đã hiểu” hoặc “hoạt động tốt”.
