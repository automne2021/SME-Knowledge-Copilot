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

## 4. Những bằng chứng cần bổ sung khi bắt đầu triển khai

- Kết quả model smoke tests với model ID/revision, config, máy thực và peak RAM.
- Hai người gán/kiểm tra chéo đủ 45 câu, snapshot reviewed có ledger được khóa và parser span mapping đúng.
- Retrieval report đầu tiên với gold mapping và phân loại lỗi.
- Kết quả code/test của auth, parser, worker, context/citation và delete lifecycle.
- Các lần thay đổi quyết định sau benchmark, kể cả giữ baseline vì treatment không cải thiện.
- Kiến thức phát sinh từ dependency/runtime, migrations, frontend, deployment và các bug thực tế.

Danh sách này là nội dung cần học/ghi trong tương lai, chưa phải các bước đã thực hiện. Mỗi lần hoàn thành công việc, cập nhật mục liên quan cùng bằng chứng thật thay vì chỉ thêm lời khẳng định “đã hiểu” hoặc “hoạt động tốt”.
