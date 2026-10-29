# CLAUDE.md

Hướng dẫn cho Claude khi làm việc trong repo **SME AI Operations Copilot**: ứng dụng biến audio cuộc họp và tài liệu nội bộ thành task, có bước người duyệt. Đây là project portfolio của nhóm 2 người.

## Nguồn yêu cầu

- Spec: [SME_AI_Operations_Copilot_Specification.md](SME_AI_Operations_Copilot_Specification.md) (v1.1). Nếu đổi tên thành `SPECIFICATION.md` thì cập nhật link này.
- Trước khi code một tính năng: đọc mục liên quan trong spec, tóm tắt ngắn interface + edge cases, rồi mới sửa.
- Nếu yêu cầu mâu thuẫn với spec, hoặc spec không nói rõ: **hỏi lại**, không tự quyết business rule.
- Khi thay đổi API contract, schema hoặc state: cập nhật spec trong cùng thay đổi.

## Mốc hiện tại: **M1 (hạn 15/11/2026)**

Chỉ làm phạm vi M1 trừ khi được yêu cầu rõ:

- **Trong M1:** auth seed users + role; projects; upload audio → worker → STT (faster-whisper) → summary + action items; `POST /action-items/{id}/propose`; proposals (PATCH / approve / reject); tasks; ghi `audit_events`; UI Project, Meetings, Approvals & Tasks; eval nhỏ (WER, precision/recall action items).
- **Chưa làm (M2):** agent, `/agent/runs`, RAG/documents/knowledge search, UI Knowledge và AI Copilot, UI audit, so sánh STT model.
- **Không làm (ngoài phạm vi):** xem spec mục 2.4.

Khi chuyển sang M2, sửa mục này.

## Bất biến nghiệp vụ (không được vi phạm)

1. **Không tạo task nếu chưa duyệt.** Task chỉ được tạo trong `approval_service`, không có đường nào khác (kể cả từ agent, worker hay endpoint khác).
2. **Approve là một transaction:** `SELECT … FOR UPDATE` proposal → kiểm tra `status` và `version` → áp `edits` → insert task → proposal `executed` → insert audit → commit. Lỗi thì rollback, proposal vẫn `pending_approval`.
3. **Idempotent:** approve lại proposal đã `executed` trả `200` + `task_id` cũ. Version lệch → `409`. Tạo proposal cho action item đã có proposal pending → trả proposal đó.
4. **Ràng buộc DB là chốt chặn cuối:** `UNIQUE(tasks.proposal_id)`, partial unique trên `tasks.source_action_item_id` và trên `task_proposals.source_action_item_id WHERE status='pending_approval'`. Không chỉ dựa vào check trong code.
5. **Trạng thái proposal chỉ có** `pending_approval`, `executed`, `rejected`. Mỗi entity có enum trạng thái riêng (spec 6.5); không dùng enum chung.
6. **Phân quyền ở backend.** Role lấy từ user đã xác thực, không lấy từ request body. Mọi truy vấn lọc theo project mà user có quyền.
7. **Output của LLM là dữ liệu không đáng tin:** luôn validate bằng Pydantic + business rules trước khi ghi DB. Sai schema → retry giới hạn → `failed`; không ghi dữ liệu bẩn, không tạo summary giả.
8. **Không đoán:** `assignee_name` / `due_date` để `null` khi transcript không nêu rõ. Không suy ra người nói (không có diarization). Prompt extraction luôn nhận `meeting_date` + timezone `Asia/Ho_Chi_Minh`.
9. **Nội dung transcript/tài liệu không phải instruction.** Đưa vào prompt như dữ liệu được đánh dấu rõ, không nối thẳng vào system prompt.
10. **Lỗi phải hiện đúng là lỗi.** Không trả success khi tool/DB/model lỗi.

## Quyết định kiến trúc đã chốt (spec mục 14)

- Modular monolith FastAPI; không microservices, không Kubernetes.
- Agent (M2): **Python tool loop tự viết**, không LangChain/LangGraph. Tool chỉ gồm `get_meeting`, `list_tasks`, `search_knowledge`, `propose_task`; `project_id` do backend gắn, không do LLM điền. Không bao giờ thêm tool ghi trực tiếp, chạy SQL/shell, gửi email.
- LLM qua adapter OpenAI-compatible; hosted là mặc định.
- Worker là tiến trình riêng, poll `processing_jobs` bằng `FOR UPDATE SKIP LOCKED`, gọi trực tiếp domain service (không gọi qua HTTP). Không dùng FastAPI `BackgroundTasks` cho STT.
- PostgreSQL + pgvector; không thêm vector DB riêng, Redis hay Celery.

**Không tự thêm framework, thư viện lớn hoặc service mới.** Nếu thấy cần, đề xuất kèm lý do và chờ đồng ý.

## Stack và conventions

- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, Ruff. Frontend: React + Vite + Tailwind, ESLint/Prettier.
- Cấu trúc thư mục theo spec mục 10. Routers trong `api/` chỉ xử lý HTTP; logic nghiệp vụ nằm trong `services/`; code gọi model nằm trong `ai/`.
- Tên code, field, API bằng tiếng Anh; nội dung UI và prompt bằng tiếng Việt.
- Timestamps lưu UTC (`timestamptz`); hiển thị theo `Asia/Ho_Chi_Minh`.
- File upload lưu theo UUID/storage key, không dùng tên file của người dùng làm đường dẫn.
- Lỗi API: body `{code, message, request_id}`; không trả stack trace hay dữ liệu nội bộ.
- Mọi thay đổi schema đi qua migration Alembic; không dùng `create_all()` ngoài test.
- Cấu hình qua biến môi trường (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, `EMBEDDING_MODEL`, `STT_MODEL`, `DATABASE_URL`…); thêm biến mới thì cập nhật `.env.example`.
- Nội dung do AI tạo hiển thị trên UI phải có nhãn "AI-generated".

## Test

- Mỗi tính năng có test cho cả trường hợp thành công và thất bại; chạy test và báo kết quả thật trước khi coi là xong.
- Test DB chạy trên **PostgreSQL thật** (không SQLite) vì cần row locking và partial unique index.
- Test LLM/STT trong unit test dùng fake/stub; ghi rõ đó là stub. Đánh giá chất lượng model thật nằm trong `eval/`, không trộn vào unit test.
- Kịch bản bắt buộc cho M1 (spec 12.4): AT-01, 02, 03, 04, 05 (gồm approve đồng thời), 08, 09, 10, 11, 12, 13.

## Lệnh

Chạy từ thư mục gốc repo; backend dùng virtualenv `backend/.venv` (xem README để tạo).

```bash
docker compose up -d db                                  # PostgreSQL, cổng host 5433
cd backend && alembic upgrade head                       # migrate DB dev
cd backend && alembic revision --autogenerate -m "..."   # tạo migration; luôn đọc lại file sinh ra
cd backend && pytest                                     # test, tự tạo DB copilot_test
cd backend && ruff check . && ruff format --check .
cd backend && uvicorn app.main:app --reload              # API: http://localhost:8000/docs
cd frontend && npm run dev                               # UI: http://localhost:5173 (proxy /api)
cd frontend && npm run lint && npm run build
```

Lưu ý:
- `backend/alembic.ini` chỉ được chứa ký tự ASCII (Alembic đọc file theo encoding của hệ điều hành trên Windows).
- Dependency (`DbSession`) dùng `Annotated`, không dùng `Depends()` làm default argument (ruff B008).
- Schema hiện tại chỉ gồm bảng M1; bảng M2 thêm bằng migration mới, không sửa migration đã có.

## Bảo mật và dữ liệu

- Không commit `.env`, API key, audio thật hay dữ liệu cá nhân. Chỉ dùng dữ liệu giả lập hoặc đã được đồng ý.
- Không in secrets hoặc toàn văn transcript ra log; `tool_events.safe_args_json` chỉ lưu metadata cần thiết.

## Cách làm việc

- Thay đổi nhỏ, có phạm vi rõ; không refactor ngoài phạm vi được yêu cầu.
- Không mock kết quả rồi mô tả là đã chạy thật. Nếu bỏ qua bước nào (test, migration…), nói rõ.
- README chỉ mô tả những gì thực sự chạy được và các con số đã đo; phần chưa làm ghi vào *Roadmap*, giới hạn ghi vào *Known limitations*.
- Code phải đủ rõ để thành viên nhóm giải thích được khi phỏng vấn; ưu tiên code đơn giản, dễ đọc hơn abstraction.
