# Kết quả hai người chấm sáu câu E2E — 11/11/2026

Đã gộp điểm do nhóm cung cấp từ hai phiếu độc lập; kiểm tra đúng ID, run ID, output hash, schema và hai reviewer khác nhau. Không có bất đồng, không cần adjudication. Agent không tự chấm lại hoặc bổ sung điểm.

| Chỉ số | Kết quả | Mẫu số |
|---|---:|---:|
| Câu đã review đầy đủ | 6/6 | 6 câu thành công |
| Correctness trung bình | 2/2 | 6 câu |
| Strict success | 6/6 | 6 câu dự kiến |
| Faithfulness | 4/4 claims | 4 claims trong 2 câu trả lời có nội dung |
| Citation correctness | 4/4 links | 4 liên kết trích dẫn |
| Citation completeness | 4/4 claims | 4 claims có ít nhất một citation đúng |
| Abstention precision / recall | 1 / 1 | 4 câu từ chối đúng, 2 câu có đáp án |

Đây là **sáu tình huống tổng hợp của browser E2E**, gồm hai role trước/sau xóa và hai câu hỏi gốc. Các lượt lặp qua role/lifecycle không phải sáu mẫu kiến thức độc lập. Kết quả xác nhận review cho đúng các output này; không suy ra accuracy 100% trên doanh nghiệp thực tế, không thay benchmark 30 câu held-out. Tập nhỏ không phù hợp để kết luận cải thiện model/prompt. Lần merge/rescore không gọi model, không phát sinh chi phí inference.

## Artifacts mới và tính bất biến

- [Combined review](../.cache/final-review-practice-20261111/combined-review.json): hai điểm gốc cho từng output, adjudication null vì hai người đồng ý.
- [Reviewed metrics](../.cache/final-review-practice-20261111/reviewed-metrics.json): kết quả offline rescore, gắn run `offline_replay_aa586eb812264801825f2fa5ce1dbebd`.
- [Receipt](../.cache/final-review-practice-20261111/rescore-receipt.json): hashes trước/sau của hai phiếu, binding và báo cáo E2E gốc; tất cả giữ nguyên.
- [Helper một lần](../.cache/final-review-practice-20261111/merge-and-rescore.py): exclusive writes; không chạy lại trên các output đã tồn tại.

Hai phiếu gốc giữ SHA-256 `d87e8c5b8397c90b860a3abdb91df640688bb7360968badd900fec0533845eb3` và `e7ab7644879c18138c03226b8b9fda2bd8731f95623945e3563ab5f3c300accd`. Combined review: `20c022e028e4e5bb77fbddc21565334d9906249472c3018ebfaf67241d3e581f`. Reviewed metrics: `24eece66eb6b53fb2284d585c683c5e63c2bb8b06cda00021454b6d4a141c4d4`.

Báo cáo/binding lịch sử vẫn ghi human review pending tại thời điểm xuất, không ghi đè để sửa lịch sử; đọc file reviewed-metrics mới để biết kết quả hiện tại. [Hướng dẫn rubric](human-review-guide.md) giữ cách chấm cho đợt tiếp. Bước11 còn final held-out và review outputs mới; tiến độ **87,3% / 100%** theo trọng số PLAN.
