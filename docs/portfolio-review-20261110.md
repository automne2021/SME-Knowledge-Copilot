# Đánh giá portfolio — SME Knowledge Copilot

**Ngày:** 10/11/2026. **Loại:** nhận xét qua source/tài liệu/artifacts và thông tin web đã đọc trong phiên; không phải audit toàn bộ hoặc kết quả chạy lại. Người dùng xác nhận lưu đánh giá và chuẩn bị kế hoạch; đợt này chỉ sửa tài liệu. Liên quan: [PLAN](../PLAN.md), [protocol kiểm chứng](final-validation-plan.md), [KNOWLEDGE K-086](../KNOWLEDGE.md#k-086--ưu-tiên-bằng-chứng-chất-lượng-và-demo-trước-mở-rộng-rag).

## 1. Kết luận và phản hồi người dùng

Project có chiều sâu về xử lý dữ liệu, truy vết nguồn và độ tin cậy backend; giá trị AI và sản phẩm chưa được chứng minh tương xứng. Người scan CV có thể chỉ thấy một chatbot tài liệu nếu README/demo không đưa ra bài toán cụ thể, kết quả đo và những tình huống khó đã xử lý.

Người dùng ngày 10/11 đã xem UI, thấy ổn và muốn sửa sau nếu cần. Giữ giao diện hiện tại để tập trung kiểm chứng. Đây không phải xác nhận toàn bộ browser E2E, khả năng dùng bàn phím hay chất lượng câu trả lời.

**Đính chính mốc UI trong đánh giá ban đầu:** số 30 tests và việc chưa truy cập được browser thuộc bàn giao 05/11. [Report UI](ui-step10-implementation.md) và KNOWLEDGE K-082–083 đã ghi ngày 06/11 có 36 tests/8 files, lint/build đạt, Edge/CDP với dữ liệu thật và ảnh mobile. Gemini bị chặn; chưa có câu trả lời/citation/abstention thật hoặc luồng delete → query/source/history đầy đủ. Không nói rằng project chưa từng được kiểm tra trên browser.

## 2. Phù hợp với VNG AI Builder Residency

[Trang chính thức](https://humanforward.academy/vi/AIBuilderResidency) được đọc ngày 10/11: chương trình 12 tuần, hướng tới sinh viên năm cuối, người mới tốt nghiệp và người có dưới hai năm kinh nghiệm; yêu cầu nền tảng lập trình, GPA và tiếng Anh. Nội dung gồm nền tảng AI, xây sản phẩm và vận hành. Hạn hồ sơ 15/11/2026; technical test 23–27/11; phỏng vấn 01–15/12; khai giảng 04/01/2027.

**Suy luận tư vấn, không phải rubric tuyển dụng của VNG:** nền tảng SWE phù hợp nếu nhóm giải thích được pipeline AI, chứng minh chất lượng bằng phép đo và trình bày đóng góp cá nhân. Chưa thấy rubric portfolio công khai trong nguồn đã đọc; không suy ra phải có fine-tuning, agent hoặc nghiên cứu mới, cũng không dự đoán xác suất trúng tuyển.

## 3. Điểm mạnh đã có bằng chứng

| Điểm mạnh | Bằng chứng và ý nghĩa |
|---|---|
| Truy vết nguồn | [Parser/chunker và mapping](parsing-upload-step05.md) giữ vị trí nguồn; có thể kiểm tra citation thay vì chỉ tin câu trả lời |
| Kiểm soát nguồn truy xuất | [Retrieval service](../backend/app/services/retrieval.py) lọc scope/generation và SQL revalidation; không tin payload vector như nguồn dữ kiện có thẩm quyền |
| Vòng đời dữ liệu | [Worker](worker-index-step06.md), [deletion/privacy](deletion-privacy-step09.md) có recovery, retry, fencing và xử lý bản sao câu trả lời |
| Kỷ luật đánh giá | [Dataset](../eval/datasets/README.md), [retrieval report](search-retrieval-step07.md) có gold spans, dev/test và snapshots; giữ cả lỗi thực nghiệm |

Các điểm này là chất liệu phỏng vấn tốt. Chúng chưa đủ để tuyên bố production-ready, semantic accuracy cao hoặc an toàn với mọi prompt injection.

## 4. Đối chiếu CSE_course_RAG

Đọc README, cây source, query pipeline, API/conversation và evaluator/report trên nhánh main ngày 10/11; chưa chạy repo hoặc xác minh deployment. Các link main có thể thay đổi về sau; đây là nhận xét tại thời điểm đọc, không phải benchmark hai hệ thống trên cùng dữ liệu.

| Khía cạnh | Repo tham khảo | SME Knowledge Copilot |
|---|---|---|
| Đối tượng | Tài liệu môn học CSE, mục đích dễ hình dung | Tri thức SME rộng; nên chọn một câu chuyện demo chủ đạo |
| Ingestion | README mô tả PaddleOCR và parser theo tài liệu môn học | PDF text/DOCX/TXT/MD; OCR ngoài M1 |
| Retrieval | Dense + reranker + query rewriting | Dense E5; hybrid/reranker chưa triển khai |
| Hội thoại | Lịch sử đưa vào generation, API có streaming | Session lưu trữ; câu hỏi độc lập, chưa streaming/multi-turn rewrite |
| Nguồn và lifecycle | Trả source chunks; phần đã đọc tập trung pipeline hỏi đáp | Mapping nguồn, kiểm tra quyền/trạng thái, cleanup/redaction |
| Evaluation | So bật/tắt rewriting, có conversation evaluator | Gold evidence và dev/test; final human-quality/held-out còn thiếu |

Nguồn phía repo: [README](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/README.md), [query pipeline](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/rag/query_pipeline.py), [API](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/api/main.py), [conversation](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/rag/conversation.py). Không dùng việc chưa thấy một khả năng trong các file đã đọc để kết luận toàn repo không có khả năng đó.

Repo tham khảo không phải chuẩn vàng. [Evaluator rewriting](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/evaluation/evaluate_rewriter_impact.py) dùng embedding cosine similarity làm tín hiệu thay cho answer quality/faithfulness, không kiểm chứng từng dữ kiện. [Report 20 queries](https://github.com/HatakekkSheeshh/CSE_course_RAG/blob/main/evaluation/evaluation_rewriter_results.json) ghi query–answer similarity giảm khoảng 0,498 → 0,472 khi bật rewriting, còn answer–chunk similarity tăng. Không thể gọi đó là cải thiện correctness hoặc so trực tiếp với recall của project này. Điểm đáng học: bài toán cụ thể, trải nghiệm hội thoại và thí nghiệm có control/treatment.

## 5. Khoảng trống cần xử lý

1. **Chất lượng AI:** [Bước 07](search-retrieval-step07.md) mới đo 10 tài liệu/14 chunks và 15 câu dev, trong đó 13 answerable. Recall@3 = 1,0 trên tập này chưa chứng minh khả năng truy xuất trong kho lớn/nhiễu. [Bước 08](answering-step08.md) có năm ca smoke qua hai runs; chưa final held-out/human answer scoring.
2. **Phân biệt bằng chứng:** 45 câu/nhãn đã được con người duyệt không có nghĩa output model đã được chấm. 302 backend +91 eval tests là kiểm tra phần mềm; không phải model trả lời đúng 393 câu nghiệp vụ.
3. **Trải nghiệm chức năng:** session có lịch sử không đồng nghĩa pipeline hiểu câu nối tiếp. Browser full E2E với model thật còn mở dù người dùng đã hài lòng về UI.
4. **Định vị và trình bày:** phần đầu README thiên về nhật ký triển khai. Khi làm Bước 12, nên đưa bài toán, demo, kết quả đo và giới hạn lên trước; giữ lịch sử ở docs. Chưa sửa README trong đợt này.
5. **Tính thực tế:** corpus hiện là synthetic nhỏ. Có thể bổ sung thử nghiệm với người chưa tham gia phát triển, tài liệu được phép sử dụng và corpus lớn hơn ở đợt riêng. Chưa có bằng chứng tiết kiệm thời gian hoặc nhu cầu SME thật.

Faithfulness cần kiểm tra từng factual claim có được context hỗ trợ không; similarity cao không thay được kiểm chứng con số/điều kiện. Tham khảo [định nghĩa Ragas](https://docs.ragas.io/en/v0.3.9/concepts/metrics/available_metrics/faithfulness/); M1 dùng human rubric hiện có, chưa cần judge trả phí.

## 6. Thứ tự ưu tiên và đánh đổi

**Đã chọn cho kế hoạch hiện tại:** giữ UI, hoàn tất Bước 10, đo baseline Bước 11 rồi đóng gói/demo Bước 12. Chuẩn bị công cụ eval offline trước live run vì runners hiện tại chưa hỗ trợ final held-out đầy đủ. Dự toán requests và xác nhận free tier là điều kiện trước mỗi đợt model; ngân sách 0 USD.

**Đề xuất thí nghiệm sau baseline, chưa triển khai:**

- Nếu lỗi nằm ở mã biểu mẫu/thuật ngữ chính xác: thử BM25, dense và hybrid trên cùng dữ liệu; đo recall và latency. Qdrant có [hybrid fusion/RRF](https://qdrant.tech/documentation/search/hybrid-queries/); hỗ trợ công cụ không chứng minh chất lượng tiếng Việt tốt hơn.
- Nếu nguồn đúng nằm trong candidates nhưng xếp thấp: thử reranker, giữ candidate/context budget rõ ràng; cân đối RAM và latency CPU.
- Nếu người dùng cần câu nối tiếp: dùng lịch sử để làm rõ query rồi retrieve lại; không dùng câu trả lời cũ làm bằng chứng. Cần eval riêng cho mất chủ thể, thay scope và nguồn bị xóa.
- OCR chỉ ưu tiên khi tài liệu mục tiêu có nhiều scan. Fine-tuning, GraphRAG, agent hoặc thêm nhiều model chưa có lỗi/nhu cầu đủ rõ để đầu tư ngay.

Đánh đổi: demo có ít chức năng AI hơn một số repo, đổi lại có thể hoàn thành và giải thích kết quả đáng tin cậy trước hạn hồ sơ. Xem lại ưu tiên khi baseline chỉ ra nhóm lỗi lớn, người dùng có nhu cầu cụ thể hoặc còn thời gian sau M1; không thêm thành phần chỉ để dài tech stack.

## 7. Demo và CV dự kiến

Định vị gợi ý: **Trợ lý tra cứu chính sách nội bộ tiếng Việt, trả lời có bằng chứng, chỉ rõ thông tin thiếu hoặc mâu thuẫn và cho mở tài liệu gốc.**

Video 2–3 phút sau kiểm chứng: câu nhiều điều kiện → mở nguồn; câu cần hai tài liệu; mâu thuẫn không đủ căn cứ chọn phiên bản; câu không có đáp án; xóa nguồn rồi kiểm tra lại. Dùng dev/fixtures demo riêng, không dùng held-out để chỉnh demo/prompt. Đây là kịch bản dự kiến, không phải năm tính năng đã nghiệm thu.

Mô tả CV dự thảo, mỗi thành viên chỉ nhận phần mình thực sự làm:

> Built a source-traceable Vietnamese document RAG pipeline with local multilingual embeddings, workspace-scoped retrieval, and document lifecycle validation.
>
> Implemented durable ingestion and deletion workflows; established a reviewed evaluation dataset with evidence annotations and separate development/test splits.

Sau final eval mới thêm kết quả định lượng, kèm quy mô và link report. Chuẩn bị hai case study: một lỗi retrieval/answering và một lỗi vận hành, có nguyên nhân, lựa chọn và evidence. Chưa công bố accuracy, hiệu quả thời gian hoặc cải thiện hybrid chưa đo.

**Trạng thái đợt lưu ghi chú:** chỉ bốn tài liệu trong phạm vi được duyệt; không model calls, sửa UI/code/config, ghi DB, commit/push. Tiến độ giữ **83,4% / 100%**, không tính việc ghi nhận đánh giá thành nghiệm thu M1.
