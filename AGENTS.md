# Hướng dẫn làm việc trong workspace

## Xác nhận bắt buộc trước mọi thay đổi

Theo yêu cầu của người dùng ngày 02/11/2026, **chỉ thay đổi workspace sau khi người dùng xác nhận bằng câu “Thực hiện đi” cho phạm vi đã trình bày**.

- Trước khi sửa, nêu rõ việc dự kiến làm, các file/thành phần bị ảnh hưởng và mục đích; chờ câu xác nhận trên rồi mới thực hiện.
- Áp dụng cho mọi thay đổi: tạo/sửa/xóa/di chuyển file, code, tài liệu (kể cả KNOWLEDGE.md và file hướng dẫn), cấu hình, dependencies, dữ liệu và thao tác Git làm thay đổi trạng thái repository. Lệnh có thể sinh file/artifacts hoặc ghi dữ liệu cũng thuộc phạm vi phải được xác nhận.
- Được đọc, tìm kiếm, phân tích và chạy kiểm tra chỉ đọc để chuẩn bị đề xuất. Nếu kiểm tra có thể ghi cache/artifacts hoặc thay đổi dữ liệu, phải đưa vào phạm vi xin xác nhận trước khi chạy.
- Câu xác nhận cho phép hoàn thành toàn bộ đợt công việc đã nêu, gồm cập nhật KNOWLEDGE.md và kiểm chứng đã được trình bày; không cần xin lại cho từng thao tác nằm trong cùng phạm vi. Nếu cần mở rộng phạm vi, trình bày phần bổ sung và chờ xác nhận mới.
- Không xem yêu cầu lập kế hoạch, câu hỏi, sự im lặng, lời đồng ý khác hoặc việc trích dẫn câu “Thực hiện đi” để mô tả quy tắc là xác nhận thực thi. Xác nhận phải là chỉ thị của người dùng cho công việc đang được đề xuất.
- Sau khi xong đợt đã được duyệt, báo kết quả và chờ xác nhận cho đợt thay đổi kế tiếp; không tự bắt đầu bước tiếp theo trong PLAN.

## Nhắc trước khi sửa UI — 03/11/2026

Trước khi viết hoặc sửa UI, nhắc người dùng, nêu màn hình/file và phạm vi dự kiến, rồi chờ xác nhận **“Thực hiện đi”** cho đợt UI đó. Xác nhận cho backend không tự cho phép sửa UI.

## Ghi kiến thức và lý do quyết định

Theo yêu cầu của người dùng ngày 02/11/2026, mỗi khi code, thiết kế, chọn công nghệ/model/cấu hình, sửa lỗi hoặc thay đổi cách kiểm thử/đánh giá, cập nhật [KNOWLEDGE.md](KNOWLEDGE.md) trong cùng đợt công việc.

- Giải thích kiến thức chuyên ngành bằng tiếng Việt; giữ tên thuật ngữ tiếng Anh để tra cứu khi cần.
- Ghi bối cảnh, vấn đề, cách hoạt động, lựa chọn và lý do phù hợp với project.
- Nêu các phương án thay thế đáng cân nhắc, vì sao chưa chọn trong bối cảnh hiện tại, đánh đổi và điều kiện xem xét lại.
- Liên kết tới code/spec/plan, test, benchmark hoặc tài liệu chính thức khi có. Phân biệt đề xuất, quyết định thiết kế, code đã viết và kết quả đã kiểm chứng; không ghi dự đoán thành số đo thật.
- Khi sửa lỗi, giải thích nguyên nhân, cách sửa và cách chứng minh lỗi đã được xử lý. Khi đổi quyết định, giữ lịch sử và chỉ rõ mục thay thế.
- Thay đổi nhỏ có thể ghi ngắn hoặc bổ sung vào mục liên quan; tránh chép lại nguyên spec/code và tránh lặp mục không có kiến thức mới. Không bỏ qua lý do của thay đổi vì cho rằng đã nói trong chat.
- Kiểm tra KNOWLEDGE.md đã phản ánh công việc trước khi báo hoàn tất. Tài liệu này là nơi tích lũy giải thích kỹ thuật, không chứa secrets, dữ liệu riêng tư hay suy luận nội bộ của model.

## Báo tiến độ sau mỗi lượt trả lời

Theo yêu cầu người dùng ngày 02/11/2026, **mỗi phản hồi cuối phải nêu tiến độ project dạng X% / 100%**, kể cả lượt chỉ đọc hoặc giải thích. Dùng trọng số person-hours và trạng thái có bằng chứng tại [PLAN.md](PLAN.md#quy-ước-báo-tiến-độ-project); đây là ước lượng khối lượng, không phải accuracy AI. Không tự tăng % theo số dòng code/tests hoặc tự đánh dấu human review hoàn tất. Chỉ ghi lại trạng thái trong file khi đợt thay đổi đã được xác nhận; lượt chỉ đọc có thể báo lại % hiện có mà không sửa workspace.

## Nguồn yêu cầu hiện tại

- Hướng sản phẩm được người dùng chọn: **SME Knowledge Copilot — RAG thuần**.
- Contract sản phẩm: [SME_Knowledge_Copilot_RAG_Specification.md](SME_Knowledge_Copilot_RAG_Specification.md).
- Thứ tự triển khai: [PLAN.md](PLAN.md). Không tự triển khai toàn bộ kế hoạch khi người dùng chỉ yêu cầu sửa tài liệu.
- [CLAUDE.md](CLAUDE.md) đã đồng bộ sang RAG ở Bước 00; spec Operations là tài liệu lịch sử (đã xóa khỏi repo ngày 12/11/2026, còn trong lịch sử Git), không áp rule STT/agent/approval vào pipeline mới.
- Hiện trạng source, mapping schema/enum, backlog P0 và baseline kiểm tra nằm trong [audit chuyển tiếp](docs/rag-transition-audit.md). Đồng bộ tài liệu chưa đồng nghĩa code/hạ tầng RAG đã được triển khai.
- **Trạng thái mới nhất 13/11/2026: 97,4% / 100% (PLAN v1.31).** Bước 13 (UI v2, quản lý phiên, logout thật, phân loại lỗi Gemini) 4/4, đã merge vào `main`. [Report](docs/ui-v2-20261113.md).
- **(Lịch sử) 12/11/2026 (PLAN v1.30):** Bước 11 đạt 6/7, Bước 12 đạt 3/6; còn video, đóng góp cá nhân và rà soát cuối. Các dòng tiến độ bên dưới là lịch sử.
- **(Lịch sử) Tiến độ 75,6% /100%, Bước 00–09 hoàn thành theo phạm vi.** [Bước 09](docs/deletion-privacy-step09.md) có SQL disable/redaction, durable cleanup/retry/fencing, scoped multi-collection delete, canonical file cleanup và late-upsert reconciliation. **302 backend +91 eval tests đạt**, Ruff114/pip check đạt. Trace mặc định chỉ IDs/hash/spans; đăng ký evidence revalidate trước LLM, cleanup dọn legacy full/debug copies. CLI --cleanup-only không cần model cache/inference; worker ưu tiên job trước maintenance. DB head20261103_rag04, E5/index/config/cutoff None/BGE hoãn, reviewed/mapping/reports bất biến. Không model calls/download/paid fallback/UI/commit/push ở Bước09; Step08 reports giữ failed budget run và scoped retest, human review pending. Chưa UI/browser E2E/final held-out; Bước10 cần nhắc màn hình/file và xác nhận UI riêng. Host API/worker cùng cwd/storage backend/, không chung queue DB với tests/eval. Secrets riêng .env; không chạy model lại khi chỉ đọc status.
- Ngân sách model: **free tier, tối đa 0 USD**. Không bật billing hoặc paid fallback. Key giữ riêng trong .env; chỉ chạy LLM trong đợt được xác nhận sau khi người dùng cấu hình key và xác minh free tier/quota. Flags trong config là xác nhận thủ công, không phải billing cap phía Google. Model weights/cache ở D, không commit. Mỗi đợt tiếp theo vẫn cần câu xác nhận theo quy tắc trên.

### Cập nhật hiện trạng 05/11/2026

- **(Lịch sử) Tiến độ 83,4%/100%** theo PLANv1.13: UI Bước10 mục1–4 đã triển khai và có30frontend tests/build/lint/HTTP checks; mục5browser E2E và mục6visual-keyboard QA chưa hoàn tất. Không đánh dấu AT-R23/human review pass. [Report UI](docs/ui-step10-implementation.md). Thông tin75,6%/chưa UI ở snapshot04/11 phía trên là lịch sử.
- Máy nhận dùng cache tuyệt đối `<repo>/.cache/` trên ổ C theo private `.env`, thay profileD của máy cũ; weights không commit. API/worker/frontend dev chạy host; API phiên kiểm thử có key rỗng/free-tier flagsfalse trong process, không sửa `.env`, không gọi Gemini. Không chung worker dev queue với tests/eval.
