# Bàn giao — SME Knowledge Copilot

> **Cập nhật:** 13/11/2026. Dành cho AI assistant (Claude, Codex) hoặc thành viên mới tiếp nhận repo. Bản bàn giao giai đoạn M1 cũ ở [docs/history/handoff-claude-m1.md](docs/history/handoff-claude-m1.md).

## 1. Project là gì

RAG hỏi đáp tài liệu nội bộ tiếng Việt cho doanh nghiệp nhỏ: trả lời kèm trích dẫn mở được tới đúng đoạn gốc, và nói "chưa đủ bằng chứng" thay vì bịa. Đây là portfolio của nhóm 2 người, nộp hồ sơ VNG AI Builder Residency.

- **Hạn nộp CV:** 15/11/2026.
- **Technical test:** 23–27/11.
- **Phỏng vấn:** 01–15/12.

## 2. Hiện trạng

- **M1: 97,4% / 100%** theo [PLAN](PLAN.md). Phần còn lại do người dùng làm: quay video demo và viết phần đóng góp cá nhân (ngoài README).
- **Nhánh:**
  - `main`: bản hiện hành, có UI v2.
  - `release/m1`: bản chốt 12/11, không sửa.
  - `feat/ui-v2`: đã merge.
- **Kết quả đo:** held-out 29/30 (1 lỗi provider vẫn tính), trích dẫn đúng 36/36, Recall@5 1,0. Test: 316 backend, 277 eval tooling, 49 frontend.
- **Tài liệu chính:**
  - [README](README.md): trang sản phẩm.
  - [Spec v2.1](SME_Knowledge_Copilot_RAG_Specification.md): contract.
  - [KNOWLEDGE](KNOWLEDGE.md): kiến thức theo chủ đề, đọc mục 1 trước.
  - [roadmap](docs/roadmap/README.md): việc sau M1.
  - Report trong `docs/`.

## 3. Bắt buộc biết trước khi làm

1. Mọi thay đổi chờ người dùng nói **"Thực hiện đi"** cho đúng phạm vi đã trình bày; UI cần xác nhận riêng ([AGENTS.md](AGENTS.md)).
2. Mỗi phản hồi cuối nêu tiến độ **X% / 100%** của M1. Khi làm roadmap, nêu thêm % roadmap.
3. Mười bất biến nghiệp vụ ở [CLAUDE.md](CLAUDE.md) và [KNOWLEDGE mục 1](KNOWLEDGE.md) không được vi phạm.
4. Ngân sách model 0 USD. Gọi Gemini thật chỉ trong đợt được duyệt, kèm dự toán.
5. Cập nhật KNOWLEDGE (mục 15) và report trong cùng đợt công việc.

## 4. Môi trường (Windows)

- **Setup máy mới:** theo [runbook](docs/workspace-restoration-20261105.md).
  - Python 3.12, Node 24, Docker Desktop.
  - Cache ở `<repo>/.cache/`; model E5 phải có sẵn, ứng dụng không tự tải.
- **Chạy và dừng:**
  - `start-web.cmd` (hoặc `start-web.cmd -NoAI` để không gọi Gemini); dừng bằng `stop-web.cmd`.
  - Launcher từ chối chạy khi pytest đang chạy.
- **Kết nối:** PostgreSQL `127.0.0.1:5433`, Qdrant `127.0.0.1:6333`. Không dùng `localhost` (xem KNOWLEDGE mục 10).
- **Test:** lệnh chuẩn ở [roadmap mục 4.5](docs/roadmap/README.md). Eval tests cần `PYTHONPATH=backend`.
- **File riêng:** `docs/interview-qa.md` và `docs/demo-script.md` chỉ lưu ở máy local, chặn bằng `.git/info/exclude`.

## 5. Việc tiếp theo được đề xuất

1. Người dùng quay video và nộp hồ sơ trước 15/11. **Không** đổi gì ảnh hưởng demo trước khi quay xong.
2. Sau đó bắt đầu roadmap M2:
   - [00 dọn nợ kỹ thuật](docs/roadmap/00-housekeeping.md)
   - [01 eval v2](docs/roadmap/01-eval-expansion.md)
   - [02 hybrid search](docs/roadmap/02-hybrid-search-reranker.md)
   - [03 thư mục](docs/roadmap/03-folders-scoped-qa.md)
3. Giới hạn đã biết:
   - Dense-only.
   - Chưa hỏi nối tiếp.
   - Chưa OCR.
   - API/worker chưa chạy trên Linux.
   - Một test worker phụ thuộc thời gian có thể chập chờn.
