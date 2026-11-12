# Rà soát repo trước khi nộp (Bước 12 mục 6) — 12/11/2026

Người dùng xác nhận đợt rà soát. Đợt này chỉ sửa tài liệu: không gọi model, không đổi code, config hay dữ liệu.

## 1. Link trong tài liệu

- 112 link markdown trong 15 file được track trỏ vào `.cache/`. Thư mục này bị Git ignore nên trên GitHub các link đều chết.
  - 34 link trỏ tới file đã đưa vào repo: đổi sang bản trong [`eval/reports/final-20261112/`](../eval/reports/final-20261112/).
  - 78 link còn lại: chuyển thành đường dẫn dạng code kèm ghi chú "chỉ lưu ở máy local". Vẫn biết file nằm ở đâu, nhưng không còn là link chết.
- Kiểm tra lại toàn bộ file `.md` được track: **0 link tương đối bị hỏng**.

## 2. Trạng thái trong file hướng dẫn

CLAUDE.md, AGENTS.md và HANDOFF_CLAUDE.md có thêm dòng trạng thái mới nhất (PLAN v1.30, 96,4%). Các dòng 75,6% / 83,4% / 92,9% được đánh dấu "(Lịch sử)", không xóa. CLAUDE.md cũng cập nhật mô tả Compose (phương án A) và held-out đã chạy.

## 3. Quét toàn repo

Phạm vi: 537 file được track. Quét theo 6 giá trị bí mật thật trong `.env` (chỉ đếm, không in) và các mẫu Google API key, bearer 43 ký tự, private key, GitHub token.

| Phát hiện | Đánh giá |
|---|---|
| `copilot_dev_password` trong `.env.example` và `compose.yaml` | Mật khẩu dev **mặc định, công khai từ đầu**, không phải secret bị lộ. **Khuyến nghị:** `.env` trên máy đang dùng đúng giá trị mặc định này cho DB dev. DB chỉ bind `127.0.0.1` nên rủi ro thấp; nếu muốn, đổi `POSTGRES_PASSWORD` và `DATABASE_URL` trong `.env` (cần tạo lại volume DB hoặc đổi mật khẩu trong Postgres). Chưa tự đổi. |
| `Bearer aaaa…` trong JUnit | Token giả làm tham số test 401 |
| Thông tin cá nhân (email, tên máy, đường dẫn người dùng) | Không có |
| `.env`, model weights, SQLite, file lớn | Không có; file lớn nhất là PDF corpus khoảng 600KB |

## 4. Số liệu trong README

Đối chiếu tự động với [`heldout/reviewed-metrics.json`](../eval/reports/final-20261112/heldout/reviewed-metrics.json):

| README | Bằng chứng |
|---|---|
| 29/30 | strict success 29/30 |
| 34/34 ý được hỗ trợ | faithfulness 1,0 trên 34 claim |
| 36/36 trích dẫn đúng | citation correctness 1,0 trên 36 link |
| Từ chối đúng 4/4, nhầm 0/25 | precision = recall = 1, false abstention 0 trên 29 output |
| Recall@5 1,0 / MRR 0,98 | 1,0 / 0,9808 (n = 26) |
| Thời gian ≈ 39 s / 45 s | p50 38,8 s / p95 44,9 s |
| 302 backend + 36 frontend tests | [Report cài sạch](fresh-setup-20261112.md) |

## 5. Definition of Done — MVP (spec 15.2)

| Điều kiện | Bằng chứng |
|---|---|
| Cài và chạy theo README, env placeholder, không hardcode key | README; [cài sạch](fresh-setup-20261112.md) từ `.env.example`; quét secret mục 3 |
| Upload PDF/DOCX/TXT/MD, hiển thị trạng thái và lỗi | AT-R01–04; UI Documents |
| Chunk có trích đoạn và vị trí chính xác | AT-R01–02; mapping [Bước 05](parsing-upload-step05.md) |
| Dense search đúng workspace, loại tài liệu không `ready` | AT-R08–09; cài sạch: 0 hit ngoài tài liệu ready |
| Hỏi đáp nhiều tài liệu, citation hợp lệ, source viewer | AT-R11; held-out 36/36 citation; Chrome E2E |
| Hành vi rõ khi không đủ bằng chứng | AT-R12; 4/4 từ chối đúng |
| Xóa thì truy vấn mới không dùng tài liệu đó | AT-R16–17; cài sạch mục 10–11 |
| Logs/trace và benchmark chạy lại được | Trace IDs/timings; manifest/config/hash của các run eval |
| README có stack, kiến trúc, giới hạn, lệnh chạy, ví dụ test | README mới |
| Không tuyên bố production-ready hay accuracy cao khi thiếu bằng chứng | README ghi rõ dữ liệu giả lập và quy mô nhỏ |
| Seed auth, quyền kiểm qua API | AT-R09; cài sạch: member upload 403 |
| Test worker restart/lease, upload trùng, xóa khi job đang chạy | AT-R05–07, AT-R17 |
| Acceptance P0 pass, có baseline report | 23/23 theo phạm vi ([acceptance](final-acceptance-20261112.md)); [held-out](human-review-heldout-20261112.md) |

Kết luận: **13/13 điều kiện có bằng chứng.** "Acceptance pass" nghĩa là 23/23 kịch bản đạt theo phạm vi bằng chứng đã ghi (contract + native + browser kế thừa), không phải một lượt chạy lại toàn bộ bằng model và browser thật.

## 6. Việc phải làm lại khi đổi UI

Người dùng sẽ đổi UI rồi tự cập nhật ảnh README và quay video. Sau khi đổi UI cần:

- Chạy lại `npm.cmd run lint`, `test`, `build`; vẫn phải đạt đủ test.
- Giữ các bất biến UI: nhãn "AI-generated", trích dẫn từ dữ liệu backend, không hiển thị % confidence, tách 3 trạng thái trả lời và lỗi kỹ thuật, render text thay vì HTML.
- Kiểm lại link ảnh trong README nếu đổi tên file ảnh.
- AT-R23 (UI) đang dựa trên bằng chứng Chrome E2E với bundle cũ. UI mới cần một lượt kiểm tra trên trình duyệt (ít nhất là luồng upload → hỏi → mở nguồn → xóa) trước khi khẳng định AT-R23 vẫn đạt.

## Tiến độ

Bước 12 mục 6 hoàn thành cho trạng thái repo hiện tại → Bước 12 đạt **4/6**.

`(89,5 + 8×6/7 + 5×4/6) / 102,5 × 100 ≈ 97,3%`. Còn mục 4 (video) và mục 5 (đóng góp cá nhân), cả hai do người dùng tự làm.
