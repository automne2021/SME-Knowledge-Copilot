# Retest riêng case mâu thuẫn

Người dùng xác nhận cho phép **thêm đúng 1 request** sau khi biết kết quả run đầu. CLI chọn `--case-id adhoc_conflict_not_human_gold`, thực tế 1 request, không retry/fallback.

Prompt v2 làm rõ partial phải có claims được dẫn nguồn và missing_evidence nêu căn cứ còn thiếu. Kết quả `partial`, hai claims dẫn đúng E1 (12 ngày) và E2 (15 ngày); missing_evidence nêu không có ngày hiệu lực/thay thế. Model không tự chọn bản A/B đang có hiệu lực. Kiểm tra này do trợ lý đối chiếu context ad hoc, không là human gold hoặc điểm benchmark.

Schema/status/citation-ID whitelist đạt; model version `gemini-3.5-flash-lite`, prompt 188 tokens, candidate 143, tổng 331; thời gian 1,663 giây. Không có technical error trong request này. Cost null vì chưa đối chiếu billing thực, tài khoản Free dựa trên ảnh/xác nhận người dùng.

Run v1 vẫn failed (4/5 outputs hợp lệ); run v2 là 1/1 retest đạt. Tổng **6 requests**, gồm một lỗi ở run đầu. Không báo hai run thành một bộ 5/5 trên prompt v2, không nói nguyên nhân lỗi cũ đã được chứng minh: output bị từ chối của run v1 không được lưu đủ để xác định chính xác.

Source snapshot `.py.txt` và source/config hashes đi kèm run này để giữ phiên bản đã đo khi source working tree thay đổi sau đó. Không copy .env/API key hoặc provider thought/error body. Đây là compatibility smoke dùng context thủ công, chưa có retrieval, app API hay human correctness benchmark.
