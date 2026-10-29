# SME AI Operations Copilot

Ứng dụng web biến bản ghi âm cuộc họp tiếng Việt thành task có bằng chứng. AI chỉ **đề xuất**; người có quyền duyệt; backend ghi task đúng một lần trong transaction có kiểm soát.

> **Trạng thái:** đang phát triển mốc M1. Hiện mới có khung project (hạ tầng backend, schema M1, test ràng buộc DB, frontend giữ chỗ). Chi tiết yêu cầu xem [đặc tả](SME_AI_Operations_Copilot_Specification.md).

## Kiến trúc

<!-- TODO: thêm sơ đồ kiến trúc thực tế khi xong M1 (có thể dùng sơ đồ mục 5.2 trong spec). -->

- **Backend:** FastAPI (modular monolith), SQLAlchemy + Alembic, PostgreSQL (+ pgvector cho M2).
- **Worker:** tiến trình riêng xử lý STT và extraction, nhận job từ bảng `processing_jobs`.
- **Frontend:** React + Vite + Tailwind.
- **AI:** faster-whisper (STT), LLM hosted qua adapter OpenAI-compatible.

## Chạy trên máy local

Yêu cầu: Python 3.11+, Docker, Node.js 20+.

```bash
# 1. Cấu hình
cp .env.example .env                 # PowerShell: Copy-Item .env.example .env

# 2. Database
docker compose up -d db

# 3. Backend
cd backend
python -m venv .venv
source .venv/bin/activate            # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload        # http://localhost:8000/docs

# 4. Frontend (terminal khác)
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

Chạy toàn bộ backend bằng Docker: `docker compose up -d --build`.

## Test và lint

```bash
cd backend
pytest                               # cần PostgreSQL đang chạy; tự tạo database copilot_test
ruff check . && ruff format --check .

cd frontend
npm run lint && npm run build
```

## Cấu trúc

```text
backend/    FastAPI app, models, migrations (alembic/), tests
frontend/   React app
eval/       Dataset đánh giá và kết quả đo
docs/       Kiến trúc và ADR
```

## Kết quả đánh giá

Chưa có. Kết quả sẽ được cập nhật từ `eval/results/` khi đo xong; chỉ ghi số đã đo thật.

## Roadmap

- **M1 (15/11/2026):** upload audio → STT → action items → proposal → phê duyệt → task; test guardrail; đánh giá nhỏ.
- **M2:** agent có tool calling, RAG tài liệu chính sách, so sánh STT model, so sánh pipeline cố định và agent.

## Known limitations

- Không phân biệt người nói (không có diarization); người phụ trách chỉ được nhận khi transcript nêu tên rõ.
- Xác thực dùng tài khoản demo, không phải cơ chế bảo mật production.

## Cập nhật dependencies

`backend/requirements.lock` pin các thư viện runtime dùng cho Docker image. Sau khi đổi dependencies trong `pyproject.toml`, tạo lại file lock và kiểm tra test vẫn pass.
