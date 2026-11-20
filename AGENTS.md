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
- **Cấu trúc từ 13/11/2026:** KNOWLEDGE.md tổ chức theo chủ đề. Thêm mục mới vào **mục 15 — Nhật ký quyết định** (mã tiếp theo `K-106`, `K-107`…, 2–5 dòng) và sửa đoạn chủ đề liên quan. Bản gốc K-001 → K-105 ở [docs/history/knowledge-archive-m1.md](docs/history/knowledge-archive-m1.md) là lưu trữ chỉ đọc.

## Báo tiến độ sau mỗi lượt trả lời

Theo yêu cầu người dùng ngày 02/11/2026, **mỗi phản hồi cuối phải nêu tiến độ project dạng X% / 100%**, kể cả lượt chỉ đọc hoặc giải thích. Dùng trọng số person-hours và trạng thái có bằng chứng tại [PLAN.md](PLAN.md#quy-ước-báo-tiến-độ-project); đây là ước lượng khối lượng, không phải accuracy AI. Không tự tăng % theo số dòng code/tests hoặc tự đánh dấu human review hoàn tất. Chỉ ghi lại trạng thái trong file khi đợt thay đổi đã được xác nhận; lượt chỉ đọc có thể báo lại % hiện có mà không sửa workspace.

## Nguồn yêu cầu hiện tại

- Hướng sản phẩm: **SME Knowledge Copilot — RAG thuần**. Contract: [SME_Knowledge_Copilot_RAG_Specification.md](SME_Knowledge_Copilot_RAG_Specification.md) v2.1. Quy tắc kỹ thuật, bất biến nghiệp vụ và lệnh chuẩn: [CLAUDE.md](CLAUDE.md).
- Spec Operations cũ đã xóa khỏi repo (12/11/2026), chỉ còn trong lịch sử Git; không áp rule STT/agent/approval vào pipeline RAG.
- Thứ tự triển khai M1: [PLAN.md](PLAN.md). Việc sau M1: [docs/roadmap/](docs/roadmap/README.md). Không tự triển khai cả kế hoạch khi người dùng chỉ yêu cầu một phần.
- Ngân sách model: **free tier, tối đa 0 USD**. Không bật billing hay fallback trả phí. Key chỉ nằm trong `.env`; chỉ gọi LLM thật trong đợt được xác nhận, kèm dự toán số lần gọi. Hai cờ free tier trong cấu hình là xác nhận thủ công, không phải giới hạn chi phí phía Google.

## Trạng thái hiện tại (20/11/2026)

- **M1: 97,4% / 100%** (PLAN v1.32). Bước 00–10 và 13 xong; Bước 11 đạt 6/7; Bước 12 đạt 4/6. Phần còn lại (video demo, đóng góp cá nhân) do người dùng làm.
- `main` chứa UI v2, quản lý phiên, logout thật, phân loại lỗi Gemini ([report](docs/ui-v2-20261113.md)). `release/m1` là bản chốt M1, không sửa.
- Roadmap: 00 (dọn nợ) và 03 (thư mục) xong; 01 (eval v2) đang chờ đóng gate T3 và người duyệt nhãn. **Việc tiếp theo: xem mục 4.8 [roadmap README](docs/roadmap/README.md).** Migration head `20261118_folders`.
- Test (20/11, `main`): 418 backend, 79 frontend; eval full gần nhất 464 trên nhánh `feat/01-eval-v2` (18/11). Kết nối DB/Qdrant dùng `127.0.0.1`.
- Nhật ký các đợt trước: [docs/history/plan-log-m1.md](docs/history/plan-log-m1.md).

## Làm việc theo roadmap (dành cho Codex và các assistant)

1. Khi người dùng nói "Làm task NN-Tk": đọc **tối thiểu** theo mục "Đọc tối thiểu" ở đầu [docs/roadmap/README.md](docs/roadmap/README.md). Bắt buộc gồm mục 4 và mục 6 của file đó, cộng file tính năng `docs/roadmap/NN-*.md`. Spec, KNOWLEDGE, `CLAUDE.md` và code chỉ đọc đúng phần được trỏ tới. Không đọc `PLAN.md`, `docs/history/` hay report cũ.
2. Mỗi task `NN-Tk` trong file tính năng là **một** đợt: trình bày phạm vi (file, migration, API, test), chờ **"Thực hiện đi"**, làm đúng phạm vi, không tự sang task tiếp theo. Task có UI cần xác nhận UI riêng.
3. Nhánh `feat/NN-<slug>` từ `main`; commit theo task; **không push hay merge** khi chưa được xác nhận. Không sửa `release/m1`.
4. Gặp quyết định chưa có trong plan (contract, dependency, model, ngân sách): dừng và đề xuất 2–3 phương án kèm khuyến nghị.
5. Cuối task: report trong `docs/`, mục mới trong KNOWLEDGE mục 15, cập nhật bảng trạng thái roadmap, báo cáo theo mẫu ở roadmap mục 6, kèm **% M1** (theo PLAN) và **% roadmap** (theo roadmap mục 5).
