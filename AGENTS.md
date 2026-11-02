# Hướng dẫn làm việc trong workspace

## Xác nhận bắt buộc trước mọi thay đổi

Theo yêu cầu của người dùng ngày 02/11/2026, **chỉ thay đổi workspace sau khi người dùng xác nhận bằng câu “Thực hiện đi” cho phạm vi đã trình bày**.

- Trước khi sửa, nêu rõ việc dự kiến làm, các file/thành phần bị ảnh hưởng và mục đích; chờ câu xác nhận trên rồi mới thực hiện.
- Áp dụng cho mọi thay đổi: tạo/sửa/xóa/di chuyển file, code, tài liệu (kể cả KNOWLEDGE.md và file hướng dẫn), cấu hình, dependencies, dữ liệu và thao tác Git làm thay đổi trạng thái repository. Lệnh có thể sinh file/artifacts hoặc ghi dữ liệu cũng thuộc phạm vi phải được xác nhận.
- Được đọc, tìm kiếm, phân tích và chạy kiểm tra chỉ đọc để chuẩn bị đề xuất. Nếu kiểm tra có thể ghi cache/artifacts hoặc thay đổi dữ liệu, phải đưa vào phạm vi xin xác nhận trước khi chạy.
- Câu xác nhận cho phép hoàn thành toàn bộ đợt công việc đã nêu, gồm cập nhật KNOWLEDGE.md và kiểm chứng đã được trình bày; không cần xin lại cho từng thao tác nằm trong cùng phạm vi. Nếu cần mở rộng phạm vi, trình bày phần bổ sung và chờ xác nhận mới.
- Không xem yêu cầu lập kế hoạch, câu hỏi, sự im lặng, lời đồng ý khác hoặc việc trích dẫn câu “Thực hiện đi” để mô tả quy tắc là xác nhận thực thi. Xác nhận phải là chỉ thị của người dùng cho công việc đang được đề xuất.
- Sau khi xong đợt đã được duyệt, báo kết quả và chờ xác nhận cho đợt thay đổi kế tiếp; không tự bắt đầu bước tiếp theo trong PLAN.

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
- [CLAUDE.md](CLAUDE.md) đã đồng bộ sang RAG ở Bước 00; spec Operations là tài liệu lịch sử, không áp rule STT/agent/approval vào pipeline mới.
- Hiện trạng source, mapping schema/enum, backlog P0 và baseline kiểm tra nằm trong [audit chuyển tiếp](docs/rag-transition-audit.md). Đồng bộ tài liệu chưa đồng nghĩa code/hạ tầng RAG đã được triển khai.
- Bước 00 và Bước 01 đã hoàn thành; [Bước 02](docs/dataset-step02.md) có 10 tài liệu/45 câu nháp, 8 fixtures và 37 tests đạt. Chờ hai người gán/kiểm tra chéo, 0/45 approved; chưa đóng gate Bước 02. Tiến độ hiện tại **11,2% / 100%**. Bước 03 chưa bắt đầu và cần xác nhận riêng.
- Ngân sách model do người dùng chọn: **free tier, tối đa 0 USD**. Không tự bật billing, đổi sang paid provider/tier hay paid fallback khi hết quota. API key giữ riêng; chuẩn bị corpus ở Bước 02, chỉ smoke model ở Bước 03 sau xác nhận và kiểm tra quota.
