# 00 — Dọn nợ kỹ thuật trước M2

**Mốc:** M2 · **Công sức:** S · **Phụ thuộc:** không · **Nhánh:** `feat/00-housekeeping`

## Mục tiêu

Trước khi đo đạc cho M2, loại bỏ các nguồn nhiễu: test chập chờn làm sai kết luận, lệch nhỏ giữa UI và thiết kế, và rác schema từ hướng Operations cũ.

## Giá trị với nhà tuyển dụng

Bộ test ổn định là điều kiện để tin các số đo trước và sau ở tính năng 01 và 02. Khi phỏng vấn, "chúng tôi sửa test chập chờn trước khi đo" là một câu chuyện tốt về kỷ luật kỹ thuật.

## Hiện trạng

- `backend/tests/test_worker.py::test_heartbeat_runs_during_inference_without_document_lock` dựa vào thời gian thực: lease 2 s, test ngủ 2,2 s. Test đã fail 1 lần khi máy bận (13/11), chạy riêng thì đạt.
- `frontend/src/components/ui/Dialog.tsx`: khi mở hộp xác nhận, focus rơi vào nút đóng (X) đầu tiên thay vì nút Hủy. Ảnh hưởng `DeleteDialog`, `DeleteSessionDialog`.
- Schema vẫn còn các bảng của hướng Operations cũ (`projects`, `project_members`, các model `meeting.py`, `task.py`, `audit.py`). Xem audit trong `docs/rag-transition-audit.md`. **Không xóa trong roadmap này** nếu chưa có quyết định riêng (task T3 chỉ lập danh sách).

## Task

### T1 — Ổn định test heartbeat

- **Phạm vi:** chỉ sửa test (và helper test nếu cần), không đổi logic worker.
- **Hướng làm:** thay `time.sleep(2.2)` bằng điều kiện quan sát được. Ví dụ: chờ cho tới khi `lease_expires_at` được gia hạn vượt mốc lease ban đầu (poll có timeout); hoặc tăng lease trong test và kiểm tra heartbeat đã ghi ít nhất 2 lần.
- **Test bắt buộc:** chạy test 20 lần liên tiếp (`pytest --count` nếu có plugin, hoặc vòng lặp shell) đều đạt; chạy toàn bộ backend 2 lần đều đạt.
- **Nghiệm thu:** report ghi số lần chạy và kết quả.

### T2 — Focus mặc định vào nút an toàn trong hộp xác nhận

- **Phạm vi (UI, cần xác nhận UI):** `Dialog.tsx` nhận prop `initialFocus` (ref), hoặc tôn trọng `autoFocus` của phần tử con; `DeleteDialog` và `DeleteSessionDialog` focus vào **Hủy**.
- **Lưu ý:** `showModal()` tự focus phần tử đầu tiên, nên phải focus lại sau khi mở. Giữ nguyên guard chống sự kiện `close` đến muộn dưới StrictMode (KNOWLEDGE, mục Frontend; test `Dialog.test.tsx`).
- **Test bắt buộc:** test frontend kiểm tra `document.activeElement` là nút Hủy sau khi mở; Escape vẫn đóng; focus trả lại phần tử đã mở dialog.
- **Kết quả (20/11/2026, xong):**
  - `Dialog.tsx` có prop `initialFocus` (ref), focus lại sau `showModal()`. Guard sự kiện `close` đến muộn và việc trả focus khi đóng giữ nguyên.
  - Ba hộp xóa focus vào **Hủy**: `DeleteDialog` (tài liệu), `DeleteSessionDialog`, `FolderDialog` ở chế độ xóa (thêm ngoài mô tả gốc vì có từ 03-T4).
  - `DeleteSessionDialog` trước đây dùng `autoFocus`, nhưng `showModal()` chạy sau nên focus bị kéo về nút đóng; đã thay bằng `initialFocus`.
  - Test:
    - `Dialog.test.tsx` giả lập `showModal()` focus phần tử đầu như trình duyệt, kiểm tra focus ở Hủy, Escape gọi `onClose`, đóng xong focus trở về nút mở. Đã thử bỏ dòng focus thì test fail.
    - Thêm test focus cho ba hộp xóa và một test xác nhận hộp đổi tên thư mục không bị kéo focus.
  - Lint, build đạt; frontend **79/79** đạt. Chưa kiểm tra bằng trình duyệt thật.

### T3 — Kiểm kê schema và code cũ (chỉ đọc, ra báo cáo)

- **Phạm vi:** không sửa code. Lập bảng mọi bảng, model, router và test còn thuộc hướng Operations, kèm: còn được import ở đâu, có dữ liệu không, rủi ro nếu xóa.
- **Đầu ra:** `docs/legacy-inventory-<date>.md` với đề xuất (giữ / xóa bằng migration / để sau). Việc xóa là một đợt riêng do người dùng quyết.
- **Kết quả (20/11/2026, xong):** [legacy-inventory-20261120.md](../legacy-inventory-20261120.md).
  - Router, service, frontend không còn code Operations. 8 bảng legacy (meetings, transcript_segments, action_items, task_proposals, tasks, projects, project_members, audit_events) đều 0 dòng trên DB development, chỉ còn model và `test_schema_constraints.py` dùng.
  - Đề xuất ba nhóm: C (code chết: 2 package placeholder, `stt_model`, extra `[stt]`), A (drop 8 bảng bằng một migration có kiểm số dòng), B (siết `processing_jobs` và role cũ, để sau vì chạm worker).
  - Không sửa code, không chạy migration.

### T4 — GIF demo cho README

- **Mục tiêu:** một GIF khoảng 15 giây cho người xem README thấy luồng chính: gõ câu hỏi → câu trả lời có trích dẫn → bấm trích dẫn → mở đúng đoạn gốc được tô sáng.
- **Không phụ thuộc** T1–T3; làm được ngay. Không sửa UI, không sửa code app.
- **Cách làm:**
  - Chạy stack bằng `start-web.cmd`, dùng dữ liệu demo hiện có trong DB development. Không xóa hay upload lại tài liệu.
  - Điều khiển Edge headless qua Chrome DevTools Protocol (CDP), dùng WebSocket có sẵn của Node 24, không cài Puppeteer/Playwright. Viewport khoảng 1280×800.
  - Lấy khung hình bằng `Page.startScreencast` hoặc chụp `Page.captureScreenshot` định kỳ. Gõ câu hỏi từng ký tự cho tự nhiên.
  - Đoạn chờ Gemini **cắt ngắn** còn khoảng 1 giây (bỏ bớt khung hình), không tua nhanh UI theo cách gây hiểu nhầm.
  - Câu hỏi: dùng câu hỏi trong ảnh `docs/images/chat.png`. Ghi câu hỏi định dùng trong phần trình bày phạm vi để người dùng xác nhận.
- **Công cụ ghép GIF:**
  - Cài **tạm ngoài dependency của project**, trong `.cache/tools/gif/` (đã nằm trong `.gitignore`). Ví dụ `npm install --prefix .cache/tools/gif gifenc@<version cố định>`, hoặc venv riêng có Pillow ở cùng thư mục.
  - **Không** sửa `package.json`, `package-lock.json` hay các file `requirements*.lock`.
  - Nêu công cụ và version trong phần trình bày phạm vi.
- **Script quay:** lưu ở `scripts/record_demo_gif.mjs` (commit) để tái tạo được. Ghi cách chạy ở đầu file. Script không chứa mật khẩu; đọc mật khẩu demo từ biến môi trường.
- **Ngân sách:** tối đa **2 lần** hỏi Gemini (1 lần quay chính, 1 lần quay lại nếu hỏng). Nếu gặp lỗi quota hoặc quá tải, **dừng và báo**, không tự thử lại. Nên chạy sau khoảng 15:00 giờ Việt Nam.
- **Đầu ra:**
  - `docs/images/demo.gif`, dưới **5 MB**, rộng khoảng 960 px, 8–10 khung hình/giây, lặp vô hạn.
  - Chèn vào `README.md` ngay dưới phần mở đầu, kèm alt text tiếng Việt. Giữ 2 ảnh tĩnh hiện có.
- **Kiểm tra trước khi commit:**
  - Mở GIF xem lại toàn bộ.
  - Không lộ token, mật khẩu, đường dẫn máy, tab hay thanh địa chỉ có thông tin riêng.
  - Câu trả lời có nhãn "AI-generated" như UI thật.
- **Nghiệm thu:** report ngắn (có thể ghi trong report của tính năng 00): câu hỏi dùng, số lần gọi Gemini, kích thước GIF, lệnh tái tạo.

### T5 — Ổn định test cleanup sau late upsert

- **Hiện trạng (ghi 20/11/2026):** `backend/tests/test_deletion.py::test_late_upsert_after_delete_is_not_published_and_is_reconciled` fail 2/3 lượt full backend trong 03-T2 (cleanup `run_once()` trả `None` ở bước kỳ vọng claim job cleanup); chạy riêng thì đạt; ở 03-T3 và 03-T4 full backend đạt 418/418. Chi tiết: [report 03-T2](../folders-20261119.md).
- **Giả thuyết (chưa chứng minh):** heartbeat `JobQueue.touch` đang khóa document, còn `JobQueue.claim` dùng `SKIP LOCKED` nên được phép trả `None`; test giả định lần claim đầu luôn có job.
- **Phạm vi:** chỉ sửa test (và helper test nếu cần), không đổi logic worker hay cleanup. Ví dụ: poll `run_once()` có timeout cho tới khi claim được job, hoặc chờ heartbeat nhả khóa trước khi claim.
- **Test bắt buộc:** chạy test này 20 lần liên tiếp đều đạt; full backend 2 lần đều đạt. Nếu tìm thấy lỗi thật ở production code, dừng và đề xuất thay vì sửa trong task này.
- **Kết quả (20/11/2026, xong):**
  - Thêm helper `run_cleanup_until_claimed` trong test: gọi `cleanup.run_once()` lặp lại, mỗi 50 ms, tối đa 10 s, cho tới khi claim được job. Cách này giống vòng lặp worker thật.
  - Giữ nguyên bước chờ heartbeat thấy lease bị thu hồi (thêm ở 03-T2) và mọi assertion cũ.
  - Không đổi production code.
  - Kiểm chứng:
    - Chạy riêng 20/20 đạt.
    - Full backend 2 lượt: 418/418 (402 s) và 418/418 (398 s).
    - Ruff check và format sạch.
  - **Giới hạn:** chưa có probe ghi lại transaction nào giữ khóa lúc fail, nên giả thuyết `SKIP LOCKED` vẫn là suy luận từ code. Test chỉ chịu được khóa ngắn, không che lỗi claim vĩnh viễn: hết 10 s vẫn `None` thì fail với thông báo rõ.

## Không làm

- Không refactor worker hay đổi thông số lease, heartbeat.
- Không xóa bảng cũ trong T3.
- Không thêm dependency vào project cho T4.
