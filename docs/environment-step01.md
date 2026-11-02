# Bước 01 — Môi trường và hạ tầng local

> **Ngày:** 02/11/2026<br>
> **Trạng thái:** hoàn thành hạ tầng/dev baseline; chưa chạy model hoặc triển khai pipeline RAG.<br>
> **Phạm vi:** khôi phục backend/frontend, cache, PostgreSQL/Qdrant, config, lockfiles và kiểm chứng bằng công cụ thực.<br>
> **Nguồn:** [PLAN](../PLAN.md), [Spec RAG](../SME_Knowledge_Copilot_RAG_Specification.md), [audit Bước 00](rag-transition-audit.md).

## 1. Kết quả và phạm vi kiểm chứng

| Hạng mục | Kết quả thực tế |
|---|---|
| Backend environment | Python 3.12.8, venv mới tại backend/.venv, không dùng Python global để cài app dependencies |
| Dependency integrity | pip check: No broken requirements found |
| Backend tests | **64 passed, 1 warning**, gồm 56 guard cases + 8 tests legacy, PostgreSQL thật; 141,79 giây trong lần chạy ghi nhận |
| Frontend | npm lint pass; TypeScript + Vite production build pass, 44 modules; build ngoài sandbox do esbuild bị chặn đọc thư mục cha ở lần đầu |
| Lint/format | Ruff 0.17.3 pass; checker root dùng config backend tường minh, 27 files already formatted trong phạm vi app/tests/scripts |
| PostgreSQL | **16.15**, probe SELECT 1 và SHOW server_version thành công |
| Qdrant | **1.20.0**, HTTP /readyz và /collections thành công; 0 collections |
| Compose | db/qdrant running healthy; ports chỉ bind loopback; image digests cố định |
| Persistence | Sau recreate theo config image digest, test DB vẫn có Alembic revision 27b126c3c0bc |
| Model/API | Không tải weights hoặc gọi LLM/embedding; HF cache 0 bytes; chưa có benchmark chất lượng |
| Ngân sách | Người dùng chọn **free tier, trần 0 USD**; không được tự chuyển paid tier |

Đây là baseline phần mềm/hạ tầng, chưa phải AT-R01–23 pass hay demo RAG. 8 tests legacy vẫn kiểm tra schema/API Operations hiện có; các bảng RAG và auth/document/worker/search/chat/source viewer còn chưa triển khai.

## 2. Những thay đổi đã thực hiện

- Giữ venv hỏng dưới backend/.venv.legacy-20261102, tạo venv mới đúng interpreter đang có; không sửa pyvenv.cfg để trỏ sang Python khác. Backup được ignore trong Git và Docker context.
- Giữ runtime pins trong backend/requirements.lock; thêm [requirements-dev.lock](../backend/requirements-dev.lock) với pytest/httpx/Ruff và các dependency dev đã resolve. Editable app vẫn trỏ source project.
- Tạo frontend/package-lock.json v3 từ lần install đã kiểm tra. Node v24.11.1, npm 11.6.2; frontend build dùng Vite 6.4.5 đã resolve theo manifest hiện có.
- Tạo D:\AI-Cache\sme-copilot\pip, npm, huggingface, tmp. Cache phụ thuộc project, không đổi cấu hình cache toàn user hoặc di chuyển Docker disk.
- Thêm service Qdrant, persistent volume riêng và healthcheck thật trong compose.yaml; giữ PostgreSQL 16 image lineage cũ. Không thêm Redis/Celery/worker giả.
- Thêm Settings.qdrant_url/qdrant_collection, alias FILE_STORAGE_DIR ưu tiên hơn STORAGE_DIR và default upload 20 MiB theo spec. Config model trong .env.example chỉ chuẩn bị cho bước 03; Settings chưa tiêu thụ toàn bộ tham số model/chunk/worker trong spec.
- .env riêng được thêm 13 non-secret keys còn thiếu, giữ credentials/LLM values đang có; upload limit cập nhật 20 MiB. Không in hay commit file .env. LLM_API_KEY chưa được cấu hình tại thời điểm kiểm tra.
- Thêm [scripts/check_infra.py](../scripts/check_infra.py) để probe hai storage bằng config ứng dụng; chỉ đọc metadata, không tạo collections/documents hoặc ghi DB.
- Pin known-first-party app/tests trong Ruff để import classification nhất quán khi kiểm tra từ repo root/backend. Không reformat các test cũ theo một cấu hình root khác.

Dockerfile hiện vẫn là scaffold cũ có startup migration; Bước 01 chỉ chạy db/qdrant, không build/start backend container. API chạy host trong các bước dev tiếp theo; bước đóng gói sau sẽ tách migration theo spec.

## 3. Versions, endpoints và volume policy

| Thành phần | Host profile | Trong mạng Compose |
|---|---|---|
| PostgreSQL | localhost:5433 | db:5432 |
| Qdrant REST | http://localhost:6333 | http://qdrant:6333 |
| API (khi chạy host) | http://localhost:8000 | Chưa start API container trong bước này |
| Frontend dev (khi chạy) | http://localhost:5173 | Chưa có frontend container |

Images trong Compose được pin theo image đã pull và kiểm tra:

```text
pgvector/pgvector:pg16@sha256:0dd3149a06e4579a0d70d8fef9945636cd514005e7237deb27f9b67886f8dc4f
qdrant/qdrant:v1.20.0@sha256:9bfc89f9914fc14876a88c05270685921a55b8877b254a98bcc1cc2f0a424cd2
```

Đây là images Linux đã dùng trên Docker Desktop máy này, không tuyên bố đã thử mọi CPU/OS. Qdrant tag có [release chính thức v1.20.0](https://github.com/qdrant/qdrant/releases/tag/v1.20.0); lựa chọn phiên bản ở đây vẫn cần smoke kiểm chứng tại project, không chỉ dựa vào release notes.

Volumes của project: smeaioperationscopilot_db_data và smeaioperationscopilot_qdrant_data. Không xóa volume khi restart/recreate. Healthcheck PostgreSQL dùng pg_isready; Qdrant dùng HTTP /readyz qua bash TCP vì không mặc định image có curl/wget. Compose chờ service_healthy trước dependency startup. [Docker startup/readiness](https://docs.docker.com/compose/how-tos/startup-order/).

## 4. Resource snapshot trước khi load model

Máy: i7-1165G7, 4 cores/8 threads; RAM khoảng 15,7 GiB; Iris Xe theo khảo sát trước. Các số dưới là ảnh chụp khi làm Bước 01, có ứng dụng khác đang chạy, không phải benchmark capacity.

| Hạng mục | Trước cài | Sau cài / snapshot cuối |
|---|---|---|
| C free bytes | 8.779.603.968 (~8,18 GiB) | 11.762.864.128 (~10,96 GiB) |
| D free bytes | 85.944.336.384 (~80,04 GiB) | 85.534.404.608 (~79,66 GiB) |
| E free bytes | 96.901.742.592 (~90,24 GiB) | 96.901.746.688 |
| Host free physical RAM | Không đo ở snapshot đầu | 3.358.572 KiB (~3,20 GiB) |
| Host CPU load | Không đo ở snapshot đầu | 7% tức thời |
| PostgreSQL container | Chưa chạy | 32,08 MiB, 1,26% CPU ở lần snapshot |
| Qdrant container | Chưa chạy | 160,9 MiB, 0,79% CPU ở lần snapshot |

Không quy chênh lệch C free cho một hành động của project: không dọn dữ liệu/ứng dụng khác trong bước này. Giới hạn RAM Docker hiển thị khoảng 7,613 GiB là trần VM, không cộng nó như usage thực của hai container. Free RAM host khoảng 3,2 GiB là lý do vẫn ưu tiên embedding CPU nhẹ, batch nhỏ và hosted generation sau này; đo lại trước load model, không load nhiều models đồng thời.

| Thư mục | Logical file bytes cuối bước |
|---|---|
| backend/.venv | 115.947.909 |
| backend/.venv.legacy-20261102 | 116.451.833 |
| frontend/node_modules | 114.628.677 |
| D cache pip | 29.288.660 |
| D cache npm | 377.580.518 |
| D cache huggingface | 0 |

Model cache đặt trên D không chuyển Docker virtual disk hoặc repo/venv khỏi C. C chưa đạt mục tiêu dự phòng 20–30 GiB trong PLAN, nên chưa coi đã sẵn sàng tải model lớn. Dependencies/infra nhỏ của bước này đã chạy được; trước bước 03 vẫn cần kiểm tra lại dung lượng.

## 5. Cách chạy lại trên Windows

Các lệnh có thể cài package, khởi động service hoặc ghi DB/cache; chỉ thực hiện trong đợt đã được xác nhận theo AGENTS. Trên máy khác, chọn CacheRoot thực có dung lượng; các thư mục cache phải được chuẩn bị. Đừng copy venv hoặc ghi đè .env có credentials riêng.

PowerShell máy này chặn .ps1 nên dùng assignments trực tiếp, không thay execution policy/global PATH và không cần Activate.ps1:

```powershell
$step01CacheRoot = 'D:\AI-Cache\sme-copilot'
$env:PIP_CACHE_DIR = Join-Path $step01CacheRoot 'pip'
$env:NPM_CONFIG_CACHE = Join-Path $step01CacheRoot 'npm'
$env:HF_HOME = Join-Path $step01CacheRoot 'huggingface'
$env:TEMP = Join-Path $step01CacheRoot 'tmp'
$env:TMP = $env:TEMP
```

Trên checkout mới chưa có virtualenv, tạo bằng Python 3.12 đã chọn; máy hiện tại đã có venv hoạt động, không cần tạo đè:

```powershell
python -m venv backend/.venv
Push-Location backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
Pop-Location
Push-Location frontend
npm.cmd ci
Pop-Location
docker compose up -d --wait --wait-timeout 120 db qdrant
.\backend\.venv\Scripts\python.exe -B scripts/check_infra.py
```

pip/npm installs đã thực chạy bằng versions trong locks; npm ci là lệnh tái lập cho lần sau, không phải một clean reinstall thứ hai đã chạy trong Bước 01. Build-system setuptools vẫn theo build-system manifest; lockfile này pin dependencies, chưa có wheel hashes hay chứng minh byte-identical builds. [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/).

Chạy kiểm tra:

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\ruff.exe check --no-cache .
.\.venv\Scripts\ruff.exe format --check --no-cache .
Pop-Location
.\backend\.venv\Scripts\ruff.exe check --no-cache --config backend/pyproject.toml backend/app backend/tests scripts
Push-Location frontend
npm.cmd run lint
npm.cmd run build
Pop-Location
```

DB test được guard kiểm tra rồi tạo/migrate riêng; lần thực chạy dùng copilot_test, khác copilot dev. Không chạy migration vào DB dev trong Bước 01. Probe sau recreate đọc đúng test revision; không xóa/rebuild volume để tạo kết quả thành công.

## 6. Cảnh báo, giới hạn và việc kế tiếp

- Backend có 1 StarletteDeprecationWarning: TestClient dùng httpx được thông báo deprecate. npm cũng báo deprecated cho ESLint 9. Giữ baseline đã pass trong bước khôi phục, chưa đổi major HTTP client/linter; ghi nhận để review compatibility có chủ đích, không ẩn warnings rồi báo sạch.
- Probe/checks chạy ngoài sandbox khi cần kết nối local/Docker. Build sandbox bị esbuild access denied; ngoài sandbox build đạt nên không sửa source frontend để né lỗi môi trường.
- Chưa có API key/quota provider thật để xác minh. Người dùng chọn **0 USD/free tier**: bước 03 chỉ được smoke khi đã có project/key free tier phù hợp, quota khả dụng và phạm vi chạy được xác nhận. Hết quota thì hoãn/dừng, không tự bật billing hoặc paid fallback. Không yêu cầu gửi key vào chat; cấu hình riêng trong .env khi cần.
- Config E5/384/CPU/batch4/chunk350/overlap50 là profile khởi đầu chưa benchmark; chưa tải PyTorch/model/reranker hoặc tạo collection. Chỉ có hạ tầng vector server ready.
- Bước 02 sẽ chuẩn bị corpus và gold labels; Bước 03 mới smoke models. Mỗi bước là đợt thay đổi mới cần câu “Thực hiện đi”.

Kiến thức/lý do/các phương án khác được ghi tại KNOWLEDGE K-017–K-021. Audit Bước 00 giữ nguyên dữ liệu lịch sử; không viết lại các lỗi môi trường trước đây như chưa từng xảy ra.
