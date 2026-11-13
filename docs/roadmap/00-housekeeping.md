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

### T3 — Kiểm kê schema và code cũ (chỉ đọc, ra báo cáo)

- **Phạm vi:** không sửa code. Lập bảng mọi bảng, model, router và test còn thuộc hướng Operations, kèm: còn được import ở đâu, có dữ liệu không, rủi ro nếu xóa.
- **Đầu ra:** `docs/legacy-inventory-<date>.md` với đề xuất (giữ / xóa bằng migration / để sau). Việc xóa là một đợt riêng do người dùng quyết.

## Không làm

- Không refactor worker hay đổi thông số lease, heartbeat.
- Không xóa bảng cũ trong T3.
