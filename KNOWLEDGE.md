# KNOWLEDGE — Học SME Knowledge Copilot theo chủ đề

> **Phiên bản 2 (13/11/2026).** Bản này tổ chức lại kiến thức giai đoạn M1 theo chủ đề để học và ôn phỏng vấn. Nội dung gốc 105 mục K-001 → K-105 (theo dòng thời gian, đầy đủ chi tiết và số đo) được giữ nguyên tại [docs/history/knowledge-archive-m1.md](docs/history/knowledge-archive-m1.md).
>
> Mã `K-xxx` vẫn là định danh ổn định: mỗi chủ đề ghi các mã liên quan, tra chi tiết trong archive bằng tìm kiếm.

## Cách dùng

- **Học lần đầu:** đọc mục 1 (bức tranh tổng thể), rồi từng chủ đề 2–11 theo thứ tự. Mỗi chủ đề có: *Khái niệm* → *Cách làm trong project* → *Vì sao, đã loại gì* → *Bằng chứng* → *Tự kiểm tra*.
- **Ôn phỏng vấn:** mục 12 (số đo chính), 13 (các bug đáng kể), câu tự kiểm tra cuối mỗi chủ đề, và bộ Q&A riêng `docs/interview-qa.md` (chỉ lưu ở máy local, không commit).
- **Ghi kiến thức mới (cho người và AI assistant):**
  1. Thêm một mục ngắn ở **mục 15 — Nhật ký quyết định**, mã tiếp theo `K-106`, `K-107`…
  2. Sửa đoạn chủ đề liên quan nếu kiến thức đổi (giữ dòng cũ dạng "Trước đây … ; từ <ngày> …").
  3. Phân biệt rõ năm mức: *đề xuất* · *quyết định thiết kế* · *đã triển khai* · *đã kiểm chứng* (kèm lệnh, điều kiện, kết quả thật) · *đã thay thế* (giữ lý do cũ).
  4. Không ghi secret, dữ liệu riêng tư, toàn văn hội thoại; số đo luôn kèm mẫu số và điều kiện.

---

## 1. Bức tranh tổng thể

**Bài toán:** nhân viên công ty nhỏ hỏi về quy định nội bộ (nghỉ phép, chiết khấu, bảo mật…). Hệ thống trả lời **kèm trích dẫn mở được tới đúng đoạn gốc**, và nói "chưa đủ bằng chứng" khi tài liệu không có thông tin.

**Vì sao RAG cố định, không phải agent hay fine-tune (K-001):** câu hỏi luôn đi một đường: tìm đoạn liên quan → chọn ngữ cảnh → LLM tổng hợp → kiểm tra output. Agent chỉ cần khi model phải tự chọn công cụ; fine-tune không cho cơ chế cập nhật/xóa tài liệu hay mở nguồn cho từng câu trả lời. Đây là lý do *hoãn*, không phải kết luận rằng chúng kém hơn.

### Vòng đời một tài liệu

```text
Upload (API, admin) ─► lưu file theo UUID + SHA-256, tạo document/revision/job (1 transaction)
   └► Worker claim job (FOR UPDATE SKIP LOCKED, lease 60s, heartbeat 15s)
        └► Parse (subprocess, timeout 60s) ─► Chunk 350 token / overlap 50, giữ vị trí nguồn
             └► Embed E5 (child process, CPU) ─► Upsert Qdrant (generation riêng)
                  └► Kiểm tra đủ point theo manifest ─► 1 transaction SQL: ready + active generation
Xóa (admin) ─► 1 transaction: deleting + che lịch sử + tạo cleanup job ─► worker dọn vector/file/text
```

### Vòng đời một câu hỏi

```text
POST /chat/query ─► kiểm tra chủ phiên, idempotency (client_request_id), tạo query_run "running"
   └► Retrieval: SQL snapshot tài liệu ready ─► E5 "query:" ─► Qdrant top-20 ─► SQL kiểm tra lại ─► top-5
        └► Context: countTokens của Gemini, ngân sách 4.000 token evidence, cấp ID E1…En SAU khi đóng gói
             └► Gemini (JSON claims) ─► validate schema + ID ─► sai thì repair tối đa 1 lần ─► sai nữa: 502
                  └► Khóa tài liệu, kiểm tra nguồn lần cuối ─► 1 transaction: message + citations + completed
```

### Mười bất biến (nói bằng lời thường)

1. Quyền lấy từ token đã xác thực; admin cũng không đọc chat của người khác.
2. Chỉ dùng tài liệu `ready`, đúng phiên bản, đúng workspace; luôn kiểm tra lại bằng SQL, không tin Qdrant một mình.
3. Tài liệu chỉ `ready` khi đủ mọi chunk; bản dở dang không bao giờ được tìm thấy.
4. Retry an toàn nhờ generation và ràng buộc DB; không hứa "exactly-once".
5. Xóa là chặn dùng **ngay khi commit**, dọn dẹp sau; lịch sử không "hồi sinh" nội dung đã xóa.
6. Trích dẫn chỉ trỏ vào đoạn thật sự gửi cho model; tên file, vị trí, đoạn trích do backend dựng.
7. Output của model là dữ liệu không đáng tin: kiểm tra, sửa tối đa 1 lần, còn sai là lỗi.
8. Trích dẫn hợp lệ chưa chứng minh câu trả lời đúng nghĩa; không biến score thành "độ tin cậy %".
9. Tài liệu là dữ liệu, không phải mệnh lệnh: không cho model công cụ, SQL, shell hay URL tự do.
10. Lỗi phải là lỗi: lỗi model/vector/DB không bao giờ giả thành "không có thông tin".

---

## 2. Ingestion: đưa tài liệu vào an toàn và giữ được nguồn

**Khái niệm**
- *Token* khác *từ* và khác *ký tự*. Ngân sách chunk phải tính bằng tokenizer của model embedding.
- *Provenance*: mỗi đoạn biết mình đến từ trang/đoạn/dòng/hàng bảng nào, để trích dẫn mở đúng chỗ.
- Hai hệ thống (filesystem và SQL, hay SQL và Qdrant) **không có transaction chung**; phải thiết kế thứ tự ghi và đường bù trừ.

**Cách làm trong project**
- **Upload (K-043):** stream theo khối 64 KiB, giới hạn tổng bytes và bytes file (Starlette `max_part_size` chỉ giới hạn field không phải file). Kiểm extension + MIME + chữ ký file. Hash SHA-256 trên bytes gốc, lưu theo UUID. Partial unique index `(workspace, sha256)` chặn trùng kể cả khi hai request đồng thời → đúng 1 response 202 và 1 response 409. Dedup theo workspace (không toàn cục, tránh lộ tài liệu của workspace khác).
- **File + SQL (K-044):** ghi file trước, rồi document → revision → job, chỉ trả 202 sau commit. Rollback thì xóa file; mất xác nhận commit thì đọc lại để quyết định giữ hay dọn; DB không trả lời được thì giữ file và log ID để đối soát.
- **Parser (K-045):** PyMuPDF 1.28.2, python-docx 1.2.0. Chuẩn hóa hẹp: NFC, gộp khoảng trắng, soft hyphen `U+00AD` → `-` (bug thật: `BM­09`, K-023). Offset tính theo code point trên text đã chuẩn hóa. DOCX không bịa số trang. Giới hạn: 200 trang, 2.000 entry ZIP / 100 MiB (chống ZIP bomb), 2 triệu ký tự, 20.000 block, 5.000 chunk. PDF không có chữ → `needs_ocr`. Parser chạy trong **subprocess** với timeout 60 s vì timeout bằng thread không dừng được code C bị treo. Bảng PDF có kẻ khung và bảng DOCX được tách theo hàng, giữ header.
- **Chunking (K-003, K-046):** tách theo cấu trúc rồi giới hạn 350 token tính cả `passage: `, heading và special token; overlap 50; không gộp xuyên trang hay xuyên heading; cắt ở ranh giới từ. Header lặp lại mang `role=context`, nội dung mang `role=content`. Ví dụ vì sao cần: tách "giảm tối đa 5%" khỏi "trừ khi có phê duyệt" làm câu trả lời mất điều kiện.

**Vì sao, đã loại gì:** cắt theo số ký tự không kiểm được ngân sách token; cửa sổ token cố định dễ cắt ngang điều kiện; lưu bytes trong PostgreSQL làm DB phình; OCR và layout AI hoãn vì CPU và ngân sách 0 USD. PyMuPDF là AGPL, cần xem license trước khi phân phối thương mại.

**Bằng chứng:** fixture thật cho scan, trắng, mã hóa, hỏng, ZIP bomb, NFD, CRLF; fault injection ở flush/commit không để lại rác; corpus 10 tài liệu → 54 block → 14 chunk, chunk dài nhất 162 token (chưa stress giới hạn 512).

**Tự kiểm tra**
1. Ngân sách 350 token tính trên phần nào? → Toàn bộ input embedding: prefix `passage: `, heading, text, special token.
2. Vì sao parser chạy subprocess? → Để kill thật được code native bị treo; thread chỉ ngừng chờ.
3. Hai request upload cùng file cùng lúc, chuyện gì xảy ra? → Partial unique index cho đúng một bản ghi; request kia nhận 409 kèm ID tài liệu đã có.

---

## 3. Embedding và retrieval

**Khái niệm**
- *Embedding* (văn bản → vector để tìm gần nghĩa) và *LLM* (sinh câu trả lời) là hai lựa chọn độc lập; *số chiều vector* khác *context window* (K-002).
- E5 cần prefix theo vai trò: `query:` cho câu hỏi, `passage:` cho đoạn tài liệu (K-030, K-056).
- *Cosine score không phải xác suất đúng.*
- Model ID chưa đủ để tái lập: phải pin **revision** và fingerprint file.

**Cách làm trong project**
- **Model (K-029, K-050):** `intfloat/multilingual-e5-small`, 384 chiều, revision `614241f6…`, fingerprint SHA-256 của 6 file, `trust_remote_code=False`, chỉ đọc cache local (thiếu cache là lỗi, không tự tải). Mean pooling theo attention mask rồi chuẩn hóa L2. `truncation=False`: input > 512 token bị từ chối (để không âm thầm cắt mất điều kiện). Chạy trong một child process lâu dài; timeout 120 s mỗi batch thì kill. Vector NaN, toàn 0 hoặc sai chiều bị từ chối trước khi vào Qdrant. Fingerprint gồm cả pooling/prefix/dtype: hai model cùng 384 chiều vẫn là hai không gian khác nhau.
- **PostgreSQL là nguồn sự thật, Qdrant chỉ tìm ứng viên (K-004):** payload Qdrant chỉ chứa ID; text, tên file, vị trí lấy từ SQL.
- **Hai lớp lọc (K-055):** Qdrant lọc workspace + generation + index version; sau đó SQL đọc lại ứng viên để kiểm `ready`/active/lifecycle hiện tại. Nếu chỉ lọc sau retrieval, vector cũ hoặc ngoài quyền có thể chiếm hết suất ứng viên.
- **Tham số:** candidate 20, top 5, cosine, **không có ngưỡng score**. Transaction đọc/auth kết thúc trước khi gọi model hay Qdrant. Model nạp lazy khi có tài liệu hợp lệ; đang bận thì trả 429 thay vì xếp hàng vô hạn.
- **Mã lỗi theo scope:** ID ngoài quyền hoặc không tồn tại → 404; tài liệu của mình chưa ready → 409; đang xóa → 410; lỗi kỹ thuật → 503 `retrieval_unavailable`.
- **Mở nguồn an toàn (K-057):** kiểm workspace/status trước khi đọc file; chỉ phục vụ revision active; PDF trả bytes gốc, TXT/MD trả `text/plain` + `nosniff`, DOCX trả text đã trích; `no-store`, CSP sandbox, tên file được làm sạch, path phải nằm trong storage root; checksum sai hay file mất → 410.

**Vì sao, đã loại gì:** BGE-M3 hoãn vì RAM trống ít và chưa có cache; hybrid/reranker hoãn để không đổi nhiều biến một lúc (K-009); pgvector đáng cân nhắc nhưng spec đã chọn Qdrant để học retrieval.

**Bằng chứng (K-059, dev 15 câu):** Recall@1 = 11/13, Recall@3/@5 = 13/13, MRR = 0,923; latency p50 83 ms. Hai câu "không có đáp án" có top score 0,845 và 0,838, *cao hơn* top score thấp nhất của câu có đáp án (0,843) → **không ngưỡng nào tách được**, nên giữ cutoff None và để bước trả lời quyết định từ chối.

**Tự kiểm tra**
1. Vì sao không đặt ngưỡng cosine để từ chối trả lời? → Số đo cho thấy điểm của câu không có đáp án chồng lên câu có đáp án; cosine không phải xác suất.
2. Vì sao payload Qdrant chỉ chứa ID? → Để mọi thứ người dùng thấy đều đọc lại từ SQL, nơi quyết định quyền và trạng thái hiện tại.
3. Đổi model embedding cần làm gì? → Collection/fingerprint mới và reindex toàn bộ; không chỉ đổi tên model trong `.env`.

---

## 4. Context, sinh câu trả lời và trích dẫn

**Khái niệm:** ba lớp kiểm tra khác nhau (K-006):
- *Schema hợp lệ*: JSON đúng cấu trúc.
- *Citation hợp lệ*: ID có trong context đã gửi.
- *Faithfulness*: nguồn thật sự hỗ trợ câu nói đó. Ví dụ E1 nói "tối đa 5%" nhưng model viết "giảm 10% [E1]": hai lớp đầu đạt, lớp ba sai.

**Cách làm trong project**
- **Ngân sách token phải theo tokenizer của LLM (K-062):** đếm bằng `countTokens` native của Gemini trên toàn request (system, câu hỏi, khung evidence, schema), không dùng tokenizer E5 hay `len/4`. Evidence tối đa 4.000; output tối đa 800 (gồm thinking); margin 256; trần app 32.768. Chunk giữ nguyên: quá lớn thì bỏ và xét chunk sau. ID `E1…` cấp **sau** khi đóng gói xong.
- **Output có kiểu (K-063):** Pydantic strict, `extra=forbid`, tối đa 12 claim × 1.000 ký tự, ID phải thuộc final context. `grounded` phải có claim; `partial` phải nêu phần thiếu; `insufficient_evidence` có claims rỗng; mâu thuẫn phải là `partial` với ≥ 2 evidence. Model chỉ thấy câu hỏi và ID/text evidence; tên file, vị trí, URL do backend dựng từ SQL.
- **Repair tối đa 1 lần** trên cùng context; sai lần hai → 502. **Không** xóa citation sai rồi giữ kết luận (kết luận khi đó mất chứng cứ).
- **Deadline và lỗi (K-065, K-105):** HTTPX timeout theo phase không chặn tổng thời gian, nên bọc `asyncio.timeout`. Mỗi lời gọi tối đa **60 s** (trước 13/11 là 120 s), cả câu hỏi tối đa 150 s. Lỗi kỹ thuật → 503/504, chỉ thiếu bằng chứng thật mới là `insufficient_evidence` (200). Lỗi provider giữ mã `model_unavailable` kèm `details.reason`: `quota` (429), `overloaded` (5xx), `rejected` (4xx khác), `network`. Không tự retry.
- **Idempotency và đồng thời (K-064):** hash gồm câu hỏi đã trim + session + filter + mode + top-k; unique `(session, client_request_id)`; partial unique cho run đang chạy → mỗi session tối đa 1 câu đang chạy. Không giữ lock khi gọi model. Lúc publish: khóa tài liệu theo thứ tự UUID, kiểm tra lại, ghi message + citations + completed trong 1 transaction. Mất xác nhận commit thì replay tìm thấy kết quả đã lưu, không gọi model lần hai.
- **Prompt injection (K-099):** tài liệu được bao bằng delimiter, model không có công cụ. Khi test, phải **chứng minh nội dung tấn công thực sự nằm trong context gửi đi** trước khi kết luận model "đã bỏ qua" nó.

**Tự kiểm tra**
1. Vì sao không dùng tokenizer E5 để tính ngân sách cho Gemini? → Mỗi model có tokenizer riêng; ngân sách phải đúng với model nhận request.
2. Model trả citation `E99` không có trong context, xử lý thế nào? → Repair 1 lần; vẫn sai thì 502, không giữ claim.
3. Vì sao lỗi 429 của Google không trả cho người dùng là 429? → 429 của app dành cho "app đang bận" (`model_busy`); lỗi quota provider là `model_unavailable` + `reason: quota`.

---

## 5. Worker, đồng thời và tính bền vững

**Khái niệm**
- *Lease*: quyền xử lý tạm thời có hạn, gia hạn bằng heartbeat.
- *Generation*: mỗi lần thử có không gian dữ liệu riêng.
- *Fencing*: worker mất lease không được ghi nữa.
- *Idempotent* ≠ *exactly-once*. `SKIP LOCKED` chỉ giảm tranh chấp row, không tự có lease hay retry (K-005).

**Cách làm trong project**
- **Queue trong PostgreSQL (K-049):** claim bằng `FOR UPDATE SKIP LOCKED` trong transaction ngắn; khóa document trước job theo thứ tự cố định; không giữ lock khi inference. Heartbeat 15 s, lease 60 s theo đồng hồ DB. Lease token + generation dùng để fence mọi lần ghi (stage, persist, publish, fail). Point ID = UUIDv5(generation, chunk), ổn định trong một attempt.
- **Publish nguyên tử qua hai hệ thống (K-051):** đóng băng manifest (ID, số lượng, hash) trước khi embed → upsert `wait=true` → scroll cả generation so đúng ID/số lượng/payload → **một transaction SQL** đặt revision ready + active generation + job completed. SQL là nơi quyết định.
- **Retry (K-052):** tối đa 3 lần, backoff mũ 5 s → 60 s có jitter; chỉ lỗi tạm thời tự retry (lỗi parse, OCR, config là vĩnh viễn); admin retry thủ công khi `retryable=true`. Sweeper mỗi 60 s dọn generation không active và không được trích dẫn, sau thời gian chờ ≥ 1 giờ.
- **Ràng buộc ở DB (K-038):** partial unique chặn upload trùng, 2 job active cùng loại, 2 câu hỏi chạy cùng session; composite FK ép scope (người tạo + workspace, revision + document). DB **không** chứng minh được đủ vector hay text đúng; phần đó do manifest và kiểm tra.
- **Cleanup sau xóa (K-070):** dùng lại lease/heartbeat/backoff; xóa vector theo filter `workspace AND document` với `wait=true` rồi kiểm tra rỗng; xóa file kiểm path chuẩn, từ chối symlink. Sweeper xóa lại vector của tài liệu đã xóa để xử lý upsert đến muộn: lease không hủy được một HTTP request đã rời process.

**Vì sao, đã loại gì:** FastAPI `BackgroundTasks` không bền qua restart; Redis/Celery thêm hạ tầng chưa cần; distributed transaction vượt khả năng hạ tầng.

**Bằng chứng:** hai claim không bao giờ cùng sở hữu một job; kill process thật sau batch Qdrant đầu rồi restart → generation mới đủ point, token cũ bị từ chối; test barrier dừng worker đúng ở upsert/count/generate rồi cho delete chen vào (K-071).

**Tự kiểm tra**
1. Worker A hết lease nhưng vẫn đang embed; điều gì ngăn A ghi đè kết quả của B? → Fencing bằng lease token + generation ở mỗi lần ghi.
2. Vì sao không publish từng batch vector? → Query sẽ thấy một tài liệu chỉ có một phần nội dung.
3. Vì sao sweeper phải xóa lại vector của tài liệu đã xóa? → Một upsert đã gửi trước khi mất lease có thể đến Qdrant sau khi cleanup chạy.

---

## 6. Xóa tài liệu và quyền riêng tư

**Khái niệm:** ẩn nút trên UI không phải phân quyền (K-008). Xóa an toàn = **chặn trước, dọn sau** (soft-disable + durable cleanup), không phải transaction phân tán.

**Cách làm trong project**
- **Một transaction SQL khi xóa (K-068):** khóa document, chuyển `deleting`, tăng `lifecycle_version`, bỏ con trỏ active, hủy lease ingest, che các câu trả lời liên quan, tạo cleanup job. Mốc commit là mốc từ đó câu hỏi mới không dùng nguồn này. Câu hỏi đang chạy dùng nguồn này → `failed/source_changed` (409).
- **Che theo context đã dùng, không chỉ theo citation:** câu trả lời có thể chịu ảnh hưởng của đoạn được gửi cho model mà không được cite, kể cả câu từ chối trả lời (K-068, K-092).
- **Tối thiểu hóa dữ liệu (K-069):** trace trong SQL chỉ lưu ID, version, hash và offset; prompt chỉ nằm trong RAM. `SourceCheckedProvider` kiểm tra lại SQL **trước mỗi lời gọi**, kể cả `countTokens`, vì `countTokens` cũng gửi text ra ngoài.
- **Lịch sử chat (K-040, K-105):** mỗi lần đọc lịch sử đều kiểm tra lại SQL hiện tại; nguồn không hợp lệ thì che nội dung. Chủ phiên xóa cuộc trò chuyện là **xóa hẳn** citations → messages → runs → session (soft delete buộc mọi truy vấn thêm điều kiện, và không bất biến nào cần giữ). Đang có câu hỏi chạy → 409.
- **UI:** panel nguồn đọc lại mỗi lần hiển thị, gặp 404/409/410 thì xóa nội dung; không cache đoạn trích để "xem offline" (K-079). Từ 13/11, khi quay lại tab UI tải lại lịch sử **ở nền** thay vì xóa trắng; bất biến thật vẫn ở backend (K-105).

**Tự kiểm tra**
1. Vì sao không chỉ xóa vector trong Qdrant? → Text vẫn còn trong SQL, file và lịch sử; cleanup có thể dở dang; worker cũ có thể ghi lại.
2. Vì sao kiểm tra nguồn trước cả `countTokens`? → Lời gọi đó cũng gửi nội dung tài liệu ra provider.
3. Cam kết cứng của thao tác xóa là gì? → Mọi câu hỏi bắt đầu sau commit xóa không dùng nguồn đó; câu đang bay bị chặn ở bước publish.

---

## 7. Xác thực và phân quyền

**Cách làm trong project**
- **Mật khẩu khác token (K-039):** mật khẩu do người chọn có entropy thấp → Argon2id (chậm, tốn bộ nhớ, có salt). Token là 32 byte ngẫu nhiên (~256 bit) → chỉ cần lưu SHA-256. Opaque token thay JWT (không cần quản lý secret/rotation); đổi lại mỗi request tra DB. TTL 1 giờ; role và `is_active` đọc lại mỗi request. User không tồn tại vẫn verify một dummy hash (chống dò user qua thời gian). Lỗi luôn là 401 chung.
- **Phân quyền theo tài nguyên (K-040):** scope lấy từ token, không từ body. Tài nguyên ngoài workspace hoặc không tồn tại → **404** (không lộ sự tồn tại); thiếu quyền → 403; chưa đăng nhập → 401. Session gắn chủ, admin không bypass.
- **Envelope:** `{data, request_id}` / `{error: {code, message, details}, request_id}`, header `X-Request-ID`, `Cache-Control: no-store`. Không echo input hay log traceback/tham số SQL.
- **Seed (K-041):** ID cố định cho `demo.admin`/`demo.member`, mật khẩu đọc từ `.env` (12–128 ký tự, hai tài khoản phải khác nhau), một transaction, chạy lại không reset mật khẩu hay nâng quyền.
- **Logout (K-105):** `POST /auth/logout` thu hồi **đúng token đang gửi**; tab/máy khác vẫn đăng nhập.
- **Phía client (K-078):** token theo tab trong `sessionStorage`; client kiểm token trước và sau khi đọc response để response 401 của token cũ không đăng xuất token mới.

**Tự kiểm tra**
1. Vì sao token chỉ cần SHA-256 mà mật khẩu cần Argon2id? → Token đã đủ ngẫu nhiên; mật khẩu thì không, nên cần hash chậm để chống dò.
2. Vì sao tài liệu của workspace khác trả 404 thay vì 403? → 403 xác nhận tài nguyên tồn tại.
3. Tên database trong `CREATE DATABASE` có dùng bind parameter được không? → Không, đó là identifier; dùng `psycopg.sql.Identifier` (K-015).

---

## 8. Đánh giá (evaluation)

**Khái niệm (K-007, K-025)**
- **Retrieval:**
  - *Hit@K*: có ít nhất một bằng chứng trong top K.
  - *Recall@K*: tỉ lệ nhóm bằng chứng được tìm thấy.
  - *All-evidence*: đủ mọi nhóm.
  - Ví dụ câu cần 2 nhóm mà tìm được 1: Hit = 1, Recall = 1/2, All-evidence = 0.
  - *MRR*: nghịch đảo hạng đầu tiên có nhóm hoàn chỉnh.
- **Abstention (từ chối trả lời):**
  - *Precision*: các lần từ chối có đúng không.
  - *Recall*: các câu thật sự thiếu nguồn có được từ chối không.
  - *False-abstention*: tỉ lệ từ chối nhầm câu có đáp án.
  - Lỗi kỹ thuật **không** tính là từ chối đúng.
- **Đánh giá retrieval trước generation.** *Oracle context* (đưa thẳng gold vào model) là công cụ chẩn đoán: vẫn sai thì lỗi ở prompt/schema/model, không ở retriever (K-066).

**Cách làm trong project**
- **Dữ liệu (K-022, K-023, K-027):**
  - 10 tài liệu giả lập tiếng Việt và 45 câu hỏi: 15 dev, 30 test; 6 câu không có đáp án.
  - Gold bám **nguồn canonical** (block, vị trí, quote), không bám chunk UUID, vì chunk đổi khi đổi cấu hình.
  - Chia dev/test theo *họ câu hỏi* để paraphrase không rò sang test.
  - Hai người duyệt độc lập; publish snapshot bất biến `reviewed-v1` có hash.
  - **Corpus v2 (kế hoạch, K-107):** 14 tài liệu của một công ty hư cấu, viết như văn bản thật (dài, có bảng, phiên bản mâu thuẫn, mã định danh, email không dấu, PDF scan). Mọi con số quan trọng nằm trong *fact registry* làm nguồn sự thật cho cả tài liệu lẫn gold. Spec: [01-corpus-v2-spec.md](docs/roadmap/01-corpus-v2-spec.md).
- **Chấm khớp bằng chứng (K-058):** các quote thay thế trong một nhóm là OR, các span dựng một quote là AND, các nhóm cần cho câu trả lời là AND; span hợp trên cùng block, phủ ≥ 80% là đạt; lệch mapping thì fail, không loại câu khỏi mẫu số. Remap gold không fuzzy match (K-047).
- **Kỷ luật chạy model thật (K-086 → K-097):**
  - **Ledger trước khi gọi:** SQLite `BEGIN IMMEDIATE` giữ chỗ trước mỗi request, không hoàn lại khi mất response (fail-closed).
  - **Pacing:** cửa sổ 61 s, ≤ 12 request, cách nhau ≥ 5,1 s.
  - **Held-out chạy một lần sau khi đóng băng cấu hình:** không tune trên test, không retry câu lỗi. Một lần chạy bị ngắt thì dùng *continuation* giữ allowance, ghi rõ là hai phiên.
  - **Người chấm:** hai người chấm độc lập trên phiếu riêng; giữ bất đồng.
- **Ranh giới bằng chứng (K-080, K-090, K-098):** test phần mềm ≠ đo chất lượng ("91 eval test" không phải "91 câu đúng"); smoke tương thích ≠ benchmark; acceptance là "đạt theo phạm vi bằng chứng đã ghi".

**Bằng chứng chính:** xem mục 12.

**Tự kiểm tra**
1. Vì sao báo 29/30 thay vì 29/29? → Mẫu số là 30 câu đã lên kế hoạch; câu lỗi provider vẫn tính.
2. Vì sao gold không bám chunk UUID? → Đổi chunk size hay generation thì UUID đổi dù dữ kiện không đổi.
3. Vì sao phải đo context thật đã gửi chứ không suy từ citation? → Suy từ citation làm sai mẫu số faithfulness và giấu lỗi ở bước đóng gói context (K-088).

---

## 9. Frontend và trải nghiệm người dùng

**Nguyên tắc chính:** UI phải **trung thực với contract** (K-081).
- API không có phân trang thì không vẽ phân trang giả.
- API không stream thì không giả hiệu ứng gõ chữ.
- Không suy % tiến độ từ thời gian.
- Đồng hồ chờ là thời gian thật, kèm khoảng thường gặp (K-105).
- Tiến độ ingest lấy từ `stage` và số chunk mà worker ghi.

**Cách làm trong project**
- **Stack:** React + TypeScript + Vite + Tailwind; context cho identity/sessions/source, hooks cho vòng đời; native `<dialog>`.
- **UI v2 (K-105):**
  - Sidebar trái, trang Lịch sử (nhóm theo ngày giờ Việt Nam), đổi tên/xóa cuộc trò chuyện có xác nhận.
  - Chip phạm vi tài liệu, sao chép câu trả lời kèm nguồn.
  - Font Be Vietnam Pro **tự host** (không gửi request ra Google), bảng màu slate + một màu nhấn #1D4ED8.
- **Hiển thị an toàn (K-079):** text để React escape; không render HTML/Markdown của tài liệu; PDF dùng object URL và thu hồi khi đóng/đăng xuất; request mở nguồn chỉ dựng từ ID + bearer.
- **Phản hồi lỗi:** một hộp lỗi cho mỗi lỗi, câu chữ theo mã lỗi và `details.reason`, có nút "Hỏi lại".
- **Ba lớp bằng chứng UI (K-080):** test jsdom, smoke HTTP thật, và E2E trên trình duyệt thật; không cộng gộp thành "đã nghiệm thu".

**Bài học từ trình duyệt thật**
- **Dialog tự đóng (K-083):** React StrictMode mount → cleanup → mount, còn sự kiện `close` của `<dialog>` được đưa vào hàng đợi; listener mới nhận sự kiện cũ. Sửa: bỏ qua `close` khi dialog vẫn đang mở. jsdom bắn đồng bộ nên test không thấy.
- **Tailwind preflight** đặt `margin: 0` cho `<dialog>` → dialog dính góc; thêm `margin: auto`.
- **Khi người dùng thử thật (13/11):**
  - Hai bong bóng câu hỏi: server lưu câu hỏi trước khi client biết run ID.
  - Spinner và rung khi chuyển tab: `focus` + `visibilitychange` cùng xóa rồi tải lại; thanh cuộn ẩn/hiện làm trang dịch ngang. Sửa bằng debounce + tải nền + `scrollbar-gutter: stable`.

**Tự kiểm tra**
1. Vì sao test jsdom pass mà dialog vẫn lỗi trên trình duyệt? → jsdom bắn sự kiện `close` đồng bộ, trình duyệt thật thì xếp hàng.
2. Mất mạng khi đang chờ câu trả lời, client làm gì? → Giữ nguyên `client_request_id` để hỏi lại trạng thái, không sinh ID mới (K-078).

---

## 10. Vận hành, môi trường và tái lập

**Cách làm trong project**
- **Topology M1, phương án A (K-102):** Compose chỉ chạy PostgreSQL và Qdrant (pin theo **digest**, healthcheck thật: `pg_isready`, `/readyz`); API, worker, frontend chạy trên Windows bằng `start-web.cmd`. Migration và seed là bước riêng. Container hóa đủ chờ lock Torch cho Linux (roadmap [11](docs/roadmap/11-deploy-linux-docker.md)).
- **Dùng `127.0.0.1`, không dùng `localhost` (K-105):** `localhost` có thể phân giải sang `::1` trước; Docker chỉ mở cổng IPv4 nên kết nối có lúc treo. Đổi xong, bộ test backend từ 566 s còn khoảng 320 s.
- **Container chạy ≠ dịch vụ sẵn sàng; tag ≠ digest (K-019).** Trong container, `localhost` là chính container đó (K-020).
- **Launcher (K-084, K-085):** supervisor ẩn cho từng dịch vụ, xác định quyền sở hữu tiến trình bằng command line + executable + PID + thời điểm tạo (không tin PID trong file). Biến môi trường ghi đè dotenv, nên launcher bỏ các override LLM kế thừa; `-NoAI` để chạy không gọi Gemini. Launcher từ chối khởi động khi pytest đang chạy (tránh dùng chung hàng đợi).
- **Dependency (K-018, K-029):** manifest ghi khoảng phiên bản, lock ghi phiên bản đã resolve; tách runtime/dev/worker lock; frontend `npm ci`. Model pin revision + fingerprint.
- **Source ≠ trạng thái runtime (K-074):** Git không mang venv, `node_modules`, volume, weights hay `.env`; máy mới phải khôi phục theo runbook và kiểm fingerprint model.
- **Line ending (K-028, K-101):** `core.autocrlf=true` làm hash theo bytes khác sau commit dù nội dung không đổi; `.gitattributes` đặt `-text` cho dữ liệu đã hash. Release phải nói rõ hash theo bytes hay theo nội dung.
- **DB test an toàn (K-015):** guard fail-closed: driver đúng, host loopback hoặc `db`, tên kết thúc `_test` và khác DB dev, URL không có query string.
- **Migration (K-037):** chỉ bổ sung, không xóa dữ liệu legacy; autogenerate không tự viết backfill/CHECK nên phải review; downgrade có guard từ chối khi đã có dữ liệu RAG.
- **Git (K-061):** quét secret trên **bytes đã stage**; quét theo giá trị thật trong `.env` bắt được mật khẩu tự đặt mà regex bỏ sót (K-104); không force-push.
- **Ngân sách model (K-031 → K-034, K-095):** 0 USD, free tier, không fallback trả phí. Key ≠ billing tier ≠ quota; quota tính theo project (tạo key mới không tăng quota). Quota ngày làm mới lúc 0 giờ giờ Thái Bình Dương (khoảng 15:00 giờ Việt Nam). Chi phí chưa đối soát hóa đơn ghi `null`, không ghi 0.

**Tự kiểm tra**
1. Vì sao pin image theo digest? → Tag có thể bị trỏ sang image khác; digest định danh đúng nội dung.
2. Test pass ở máy cũ có chứng minh máy mới chạy được không? → Không; môi trường runtime phải được khôi phục và kiểm lại.
3. Vì sao `.gitattributes` đặt `-text` cho dataset? → Để autocrlf không đổi bytes của file đã được hash.

---

## 11. Quy trình làm việc của nhóm

- **Xác nhận theo phạm vi (K-011):** mọi thay đổi chờ câu "Thực hiện đi" cho đúng phạm vi đã trình bày; mở rộng phạm vi cần xác nhận mới. Chi tiết: [AGENTS.md](AGENTS.md).
- **Tiến độ theo khối lượng có bằng chứng (K-026):** trọng số cố định theo bước nhân tỉ lệ đầu việc đã có bằng chứng; không tăng % vì thêm docs hay test; % không phải accuracy.
- **Audit trước khi code (K-012):** đừng tin tên bảng hay thư mục; đối chiếu contract với source thật.
- **Ưu tiên bằng chứng chất lượng trước mở rộng tính năng (K-086).**
- **README cho người ngoài nhóm (K-103):** bài toán, tính năng, ảnh, cách hoạt động, kết quả có mẫu số; nhật ký nội bộ để ở PLAN và report.
- **Sau M1:** việc mới theo [roadmap](docs/roadmap/README.md), mỗi task một đợt xác nhận.
- **Giữ ngữ cảnh giữa các phiên AI bằng file, không bằng trí nhớ (K-107):** spec, fact registry, bảng trạng thái và report cuối task là "bộ nhớ"; phiên mới đọc lại chúng thay vì kéo dài một phiên đến khi context bị tóm tắt.

---

## 12. Các số đo chính (M1)

| Số đo | Giá trị | Điều kiện |
|---|---|---|
| Held-out thành công đầu-cuối | **29/30** (q023 lỗi HTTP 503, vẫn tính) | 30 câu, chạy một lần sau freeze, hai phiên continuation (K-096, K-097) |
| Faithfulness / citation đúng / đầy đủ | 34/34 claim · 36/36 link · 34/34 claim | Hai người chấm, 29/29 khớp, không cần phân xử |
| Từ chối đúng | 4/4 câu không có đáp án, 0/25 từ chối nhầm | Held-out |
| Retrieval held-out | Recall@5 = 1,0 · MRR@5 ≈ 0,98 | 26 câu có đáp án |
| Latency trả lời | p50 ≈ 38,8 s · p95 ≈ 44,9 s · max 45,5 s | Gồm thời gian giãn request của eval; retrieval p50 ≈ 0,59 s |
| Dev retrieval baseline | Recall@1 11/13 · Recall@5 13/13 | 15 câu dev (K-059) |
| Ingest | Cold 1 tài liệu 13,0 s (load model 10,2 s) · warm 10 tài liệu 4,6 s | Máy dev cũ (K-053) |
| Test phần mềm | 316 backend · 277 eval tooling · 49 frontend | 13/11/2026 |
| Chi phí | 0 USD theo cấu hình free tier | Chưa đối soát hóa đơn |

Giới hạn khi trích dẫn số: dữ liệu **giả lập và nhỏ**; không phải độ chính xác trên tài liệu doanh nghiệp thật.

---

## 13. Các bug đáng kể (dùng để kể khi phỏng vấn)

| Bug | Nguyên nhân | Bài học | Mã |
|---|---|---|---|
| Soft hyphen làm lệch gold | PyMuPDF trích `BM­09` | Chuẩn hóa hẹp có test, không nới tới mức gộp `ẹ`/`ệ` | K-023 |
| API trả nhầm job cũ | Hai timestamp trùng nhau | Xếp hạng bằng window function, ưu tiên job active | K-052 |
| Fault injection ở commit không chạy | Service đã flush nên `Session.dirty` rỗng | Test lỗi phải assert lỗi đã thật sự được bơm | K-071 |
| Dự toán 19 lời gọi đếm token, thực tế 21 | File MD có heading riêng → thêm chunk | Dự toán quota theo số chunk thật; giữ nguyên report thất bại | K-067 |
| Ledger SQLite giữ file trên Windows | `sqlite3.Connection` làm context manager không đóng kết nối | Dùng `contextlib.closing` | K-087 |
| `TimeoutError` bị phân loại là lỗi ledger | `TimeoutError` là lớp con của `OSError` | Bắt exception cụ thể trước | K-088 |
| Dialog tự đóng | StrictMode + sự kiện `close` xếp hàng | jsdom không thay được trình duyệt thật | K-083 |
| 96/167 file lệch hash sau commit | CRLF ở working tree, LF trong Git | Ghi rõ hash bytes hay hash nội dung | K-101 |
| Kiểm tra "không có X" luôn pass | Script so trường không tồn tại | Kiểm tra phủ định phải dùng thuộc tính chắc chắn có | K-102 |
| Report ghi sai "đã thu hồi token" | Script bỏ qua status code của request dọn dẹp | Request dọn dẹp cũng phải kiểm kết quả | K-104 |
| Gemini treo 142,8 s, UI hiện hai hộp lỗi | Lời gọi generate chờ hết timeout 120 s | Phân loại lỗi provider, timeout 60 s, một hộp lỗi rõ ràng | K-105 |
| Test treo hơn 10 phút | `localhost` → `::1`, Docker chỉ mở IPv4 | Dùng `127.0.0.1` | K-105 |

---

## 14. Thuật ngữ

| Thuật ngữ | Nghĩa ngắn |
|---|---|
| RAG | Tìm đoạn tài liệu liên quan rồi đưa cho LLM tổng hợp câu trả lời |
| Chunk | Đoạn tài liệu đã cắt theo ngân sách token để embed |
| Embedding | Vector biểu diễn nghĩa của văn bản |
| Dense retrieval | Tìm theo độ gần vector; khác lexical (theo từ khóa) |
| Hybrid / RRF | Kết hợp dense và lexical; Reciprocal Rank Fusion gộp theo hạng |
| Reranker | Model chấm lại top ứng viên chính xác hơn nhưng chậm hơn |
| Grounded / partial / insufficient_evidence | Trả lời đủ nguồn / một phần / chưa đủ bằng chứng |
| Abstention | Hệ thống chủ động từ chối trả lời khi thiếu nguồn |
| Faithfulness | Nguồn thật sự hỗ trợ nội dung câu trả lời |
| Gold evidence | Bằng chứng chuẩn do người duyệt gắn cho câu hỏi eval |
| Held-out / test split | Phần dữ liệu chỉ chạy một lần sau khi đã đóng băng cấu hình |
| Oracle context | Đưa thẳng gold vào model để tách lỗi retrieval khỏi lỗi generation |
| Lease / heartbeat | Quyền xử lý tạm thời có hạn / tín hiệu gia hạn |
| Generation (worker) | Không gian dữ liệu riêng của một lần xử lý tài liệu |
| Fencing | Chặn worker đã mất quyền khỏi việc ghi |
| Idempotency | Gửi lại cùng request không tạo thêm tác dụng phụ |
| Manifest | Danh sách đóng băng (ID, số lượng, hash) dùng để kiểm tra đủ dữ liệu |
| Soft-disable / tombstone | Đánh dấu ngừng dùng trước khi dọn dữ liệu thật |
| Fingerprint | Hash định danh chính xác model/cấu hình/index |
| Fail-closed | Khi không chắc chắn thì từ chối, không cho qua |

### Bảng tra mã K-xxx theo chủ đề

Mức học: **in đậm** = nên đọc chi tiết trong archive; thường = đọc khi cần; *(lịch sử)* = chủ yếu là số liệu tiến độ của một thời điểm.

| Chủ đề | Mã |
|---|---|
| Tổng quan, kiến trúc | **K-001**, **K-004**, K-009 |
| Ingestion | **K-003**, **K-043**, **K-044**, **K-045**, **K-046**, **K-051** |
| Embedding, retrieval, mở nguồn | **K-002**, **K-029**, **K-030**, **K-050**, **K-055**, **K-056**, **K-057**, **K-059** |
| Context, sinh câu trả lời, trích dẫn | **K-006**, K-031, **K-035**, **K-062**, **K-063**, **K-065**, **K-099** |
| Worker, đồng thời | **K-005**, **K-038**, **K-049**, **K-052**, **K-064**, **K-070**, **K-071** |
| Xóa, quyền riêng tư | **K-008**, **K-068**, **K-069** |
| Auth, phân quyền | **K-015**, **K-039**, **K-040**, K-041, **K-078** |
| Đánh giá | **K-007**, **K-022**, **K-023**, K-024, **K-025**, **K-027**, **K-047**, **K-058**, **K-066**, **K-067**, **K-086**, **K-087**, **K-088**, K-089, **K-090**, K-091, **K-092**, **K-093**, K-094, **K-095**, **K-096**, **K-097**, K-098, K-100 |
| Frontend, UX | K-076, K-077, **K-079**, **K-080**, **K-081**, K-082, **K-083**, **K-105** |
| Vận hành, môi trường | K-013, K-014, K-016, K-017 *(lịch sử)*, K-018, **K-019**, K-020, K-021, K-028, **K-037**, **K-061**, **K-074**, K-075, K-084, K-085, **K-101**, **K-102**, K-104 |
| Model và chi phí | K-031, K-033, K-034, **K-095** |
| Quy trình, tiến độ | K-010, K-011, K-012, K-026, K-032 *(lịch sử)*, K-036, K-042 *(lịch sử)*, K-048 *(lịch sử)*, K-053, K-054, K-060 *(lịch sử)*, K-072 *(lịch sử)*, K-073 *(lịch sử)*, K-103 |

---

## 15. Nhật ký quyết định (từ 13/11/2026)

Mỗi mục: **K-số — tiêu đề** · ngày · loại · 2–5 dòng (quyết định, lý do, bằng chứng, link report). Các mục K-001 → K-105 nằm trong [archive](docs/history/knowledge-archive-m1.md); tóm tắt theo chủ đề ở trên.

### K-106 — Tổ chức lại KNOWLEDGE và lập roadmap cho Codex

13/11/2026 · quy trình · đã triển khai.
- KNOWLEDGE cũ (1.558 dòng, 105 mục theo thời gian) khó dùng để học. Chuyển nguyên bản vào `docs/history/`, viết bản này theo chủ đề với câu tự kiểm tra.
- Từ nay ghi mục mới ở đây và cập nhật chủ đề liên quan.
- Roadmap sau M1 ở [docs/roadmap/](docs/roadmap/README.md): mỗi tính năng một file dạng ticket, mỗi task một đợt xác nhận, tiến độ roadmap tính riêng với % của M1.

### K-107 — Corpus v2 giống văn bản thật, có fact registry

15/11/2026 · đánh giá, quy trình · kế hoạch (chưa triển khai).
- Corpus v1 mỗi file chỉ khoảng 500 ký tự và lặp cụm "trong bộ dữ liệu mẫu", nên Recall@5 = 1,0 nói được ít. Corpus v2 là 14 tài liệu của công ty hư cấu "Thiên Lam": văn bản hành chính có Điều/Khoản, 2 tài liệu dài 10–12 trang, bảng kẻ khung, thông báo 2026 mâu thuẫn sổ tay 2025, biên bản chỉ có *đề xuất*, email không dấu, 2 PDF scan.
- **Fact registry** là nguồn sự thật duy nhất: tài liệu chỉ lệch registry ở chỗ cố ý cài bẫy, và T3 lấy gold từ đó. Phương án để Codex tự viết tự do rồi mới trích gold bị loại vì dễ sinh mâu thuẫn ngoài ý muốn.
- v1 và v2 ingest vào workspace riêng khi eval, vì chủ đề trùng nhưng số khác.
- Chia T2 thành 3 phiên Codex, phiên đầu dừng ở 1 tài liệu mẫu để người dùng duyệt văn phong; ngữ cảnh giữa các phiên giữ bằng spec và bảng trạng thái. GIF demo thành task 00-T4, công cụ ghép GIF cài tạm ngoài dependency.
