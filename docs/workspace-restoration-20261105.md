# Khôi phục workspace trên máy nhận bàn giao — 05/11/2026

Người dùng xác nhận đợt khôi phục môi trường bằng “Thực hiện đi”. Phạm vi: dependencies từ lockfiles, cache ổ C, E5 đúng revision, DB/Qdrant, migration/seed sau kiểm tra dữ liệu, regression/lint/build và tài liệu. Không bao gồm UI Bước 10, Gemini requests, thay model/prompt/index, commit hoặc push. Tiến độ sản phẩm giữ **75,6% / 100%** theo [PLAN](../PLAN.md).

**Kết quả: hoàn thành khôi phục và kiểm chứng trên máy nhận.** 302 backend +91 eval tests đạt; frontend lint/build, Ruff/pip check, E5 local, auth/health và worker probes đạt. Docker DB/Qdrant giữ chạy; API/worker/frontend/model probe đã kết thúc. UI RAG Bước 10 cần đợt riêng. Không gọi Gemini hoặc thay đổi billing.

## Hiện trạng và cách khôi phục

Checkout nhận bàn giao ở commit `10090bd`, working tree sạch trước đợt này. Python **3.12.1**, Node **24.11.1**, npm **11.6.2** đã cài; venv, node_modules và cache model chưa có. Docker Desktop đã cài nhưng Linux engine chưa chạy. Các số đo và trạng thái máy ngày 02–04/11 trong reports cũ là bằng chứng lịch sử, không phải trạng thái tự có trên máy nhận.

Cache dùng `<repo>/.cache/{pip,npm,huggingface,tmp}` trên ổ C. `.cache/` đã được Git ignore; Docker backend build context là `backend/`, nên cache model ở root không nằm trong context đó. `.env` riêng dùng đường dẫn tuyệt đối cho HF_HOME/PIP_CACHE_DIR/NPM_CONFIG_CACHE để API và worker từ `backend/`, hoặc eval từ root, cùng thấy một cache. Chỉ đổi ba đường dẫn cache; giữ key, mật khẩu, free-tier flags và các cấu hình còn lại. `.env` không tự export biến môi trường cho pip/npm.

Chọn Python 3.12 vì lock worker pin wheel Torch CPU cho CPython 3.12/Windows x64. Không nâng dependencies hoặc tái sinh lockfiles để khớp máy. Không dùng wheel Windows trong Linux image. Cache trong repo thuận tiện cho máy chỉ có ổ C và nằm trong quyền workspace; nếu chuyển repo phải cập nhật ba đường dẫn tuyệt đối. Có thể chuyển cache ra ngoài repo khi cần chia sẻ hoặc giảm kích thước thư mục, nhưng phải giữ revision/file hashes/fingerprint.

## Lệnh setup cho checkout mới

Từ repo root, dùng PowerShell và đường dẫn cache riêng cho project; không đổi execution policy toàn máy:

```powershell
$restoreRoot = (Get-Location).Path
$restoreCache = Join-Path $restoreRoot '.cache'
New-Item -ItemType Directory -Force "$restoreCache/pip", "$restoreCache/npm", "$restoreCache/huggingface", "$restoreCache/tmp" | Out-Null
$env:PIP_CACHE_DIR = Join-Path $restoreCache 'pip'
$env:NPM_CONFIG_CACHE = Join-Path $restoreCache 'npm'
$env:HF_HOME = Join-Path $restoreCache 'huggingface'
$env:TEMP = Join-Path $restoreCache 'tmp'
$env:TMP = $env:TEMP

# Chỉ tạo nếu chưa có venv phù hợp; không tạo đè môi trường đang dùng.
py -3.12 -m venv backend/.venv
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.lock -r backend/requirements-worker-cpu.lock -e './backend[dev,worker]'
Push-Location frontend
npm.cmd ci --no-audit --no-fund
Pop-Location
```

Chuẩn bị `.env` từ `.env.example` trên checkout mới và điền credentials riêng; không chép đè `.env` đã có. Sửa HF_HOME/PIP_CACHE_DIR/NPM_CONFIG_CACHE thành đường dẫn tuyệt đối dưới `$restoreCache`. Các giới hạn parser/worker/answering không ghi riêng trong `.env` dùng defaults trong [Settings](../backend/app/core/config.py); thiếu key không tự động là lỗi config.

E5 public download chỉ được thực hiện trong đợt cho phép tải model. Dùng `huggingface_hub.snapshot_download` với model `intfloat/multilingual-e5-small`, revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, cache_dir `<HF_HOME>/hub`, `token=False` và sáu tên file từ [MODEL_FILES](../backend/app/services/embeddings.py). Đối chiếu hashes với fingerprint lịch sử trước sử dụng. Runtime bình thường vẫn `local_files_only=True`, không tự tải/fallback. Download weights không gọi hosted inference; đợt này không chạy Gemini hoặc kiểm tra quota bằng provider requests.

Ví dụ tải/đối chiếu từ `backend/` sau khi private `.env` đã có cache path đúng:

```powershell
@'
import hashlib, json
from pathlib import Path
from huggingface_hub import snapshot_download
from app.core.config import get_settings
from app.services.embeddings import MODEL_FILES
s = get_settings()
snapshot = Path(snapshot_download(
    s.embedding_model, revision=s.embedding_revision,
    allow_patterns=list(MODEL_FILES), cache_dir=str(s.hf_home / 'hub'),
    token=False, max_workers=2,
))
expected = json.loads(Path(
    '../eval/reports/ingestion_s6_20261103T093516Z_896b9799/manifest.json'
).read_text())['profile']['embedding_fingerprint']['files']
for name in MODEL_FILES:
    with (snapshot / name).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected[name], name
print('Six pinned E5 file hashes match.')
'@ | .venv/Scripts/python.exe -B -
```

Mở Docker Desktop, đợi Linux engine sẵn sàng, rồi từ root:

```powershell
docker compose ps --all
docker compose up -d --wait --wait-timeout 120 db qdrant
./backend/.venv/Scripts/python.exe -B scripts/check_infra.py
```

Kiểm tra databases/tables/current Alembic head và Qdrant collections trước khi migrate. Không xóa volumes hoặc dữ liệu cũ để làm setup xanh. Sau khi xác minh target:

```powershell
Push-Location backend
./.venv/Scripts/python.exe -B -m alembic upgrade head
./.venv/Scripts/python.exe -B -m app.seed
Pop-Location
```

Seed chỉ tạo tài khoản thiếu, không reset password/role của identity đã có. DB test phải được guard chấp nhận: loopback/Compose, PostgreSQL psycopg, tên lowercase ASCII kết thúc `_test`, khác DB dev, không query/fragment. Fixture tạo/migrate DB test riêng. Không chạy worker cùng queue DB với tests/eval.

## Kiểm chứng và khởi chạy dev

Kết quả thực chạy trong đợt này:

| Kiểm tra | Kết quả trên máy nhận |
|---|---|
| Frontend install | `npm ci --no-audit --no-fund`: 190 packages, không đổi lockfile |
| Frontend lint/build | PASS; Vite 6.4.5, 44 modules, build 4,54 s |
| Docker | Engine 27.3.1; DB/Qdrant healthy, đúng image digests trong Compose |
| Trước migration | DB `copilot` không có public tables; chưa có DB test; không xóa volumes |
| Volumes project mới | `sme-ai-operations-copilot_db_data`, `sme-ai-operations-copilot_qdrant_data`; khác tên project máy cũ trong report Bước 01 |
| Backend install | Dev + worker CPU locks và editable app cài đạt; không đổi lockfiles |
| Dependency/Ruff | `pip check` PASS; Ruff check/format PASS, 115 files vì bao gồm `scripts/check_infra.py` |
| E5 cache | Sáu file SHA-256, torch 2.9.1+cpu/transformers 4.57.6/tokenizers 0.22.2, embedding hash và index version khớp report Bước 06 |
| Dev migration/seed | Head `20261103_rag04`; tạo hai users `demo.admin`/`demo.member` từ private passwords |
| Reviewed validator | PASS: 10 documents, 8 fixtures, 45 questions/45 approvals; đây là structural validation |
| Eval regression | **91 passed, 1 warning, 10,54 s**; không chạy held-out hoặc Gemini |
| Backend regression sau sửa setup | **302 passed, 1 warning, 646,77 s**; không fail/skip |
| Local E5 process probe | Một query + một passage; 384 chiều, finite/unit norm đạt; 10,516 s gồm cold load và hai encode calls; không phải retrieval benchmark |
| API probe | ASGI TestClient: health 200; login/me/documents đạt cho knowledge_admin và member; xóa đúng hai token probe sau kiểm tra |
| Worker probes | `app.worker --once` và `app.worker --cleanup-only --once` đều exit 0 trên dev queue rỗng; default collection/5 payload indices được chuẩn bị |
| Trạng thái cuối | Dev/test head `20261103_rag04`; dev 2 users/test 0 users; cả hai 0 auth_tokens/documents/revisions/blocks/chunks/sessions/runs/messages/citations/jobs; Qdrant chỉ default collection, 0 points |

Npm cảnh báo ESLint 9.39.5 hết hỗ trợ; giữ nguyên version đã khóa trong đợt khôi phục và ghi nhận, không nâng major hoặc ẩn warning. Không dùng kết quả 302/91 của máy cũ thay kết quả hiện tại.

Hai regression invocations chạy offline cho HF/Transformers; process có `LLM_API_KEY` rỗng và free-tier/quota flags false, không sửa private `.env`. Provider tests dùng MockTransport/fakes có nhãn; không dùng credentials thật để chạy tests và không tạo answering/retrieval benchmark mới.

Warning Starlette/httpx còn ở cả hai suites và API probe; giữ đúng baseline, không chuyển HTTP client trong đợt môi trường. Chưa kiểm tra key/quota/free tier phía Google; private flags không phải provider billing cap. Không có hosted LLM request hoặc model spend trong đợt này.

**Lỗi setup phát hiện và cách sửa:** lượt backend đầu có **188 passed, 114 setup errors, 1 warning / 37,63 s** vì `backend/.cache` chưa tồn tại. Pytest tạo basetemp bằng `mkdir` nhưng không tạo thư mục cha. Tạo parent bằng `New-Item -ItemType Directory -Force .cache` từ backend, rồi chạy lại toàn bộ suite với basetemp mới; không sửa source/tests hoặc bỏ test. JUnit lỗi đầu được giữ ở `.cache/restoration/backend-tests-initial.xml`; kết quả lượt chạy lại lưu riêng ở `backend-tests.xml`. Eval JUnit ở `.cache/restoration/eval-tests.xml`. Cache artifacts không commit.

Index version giữ `9851b494ba14e5a4370604ac33064d65b40690b990118fce057e4fbcb5afc4a4`, embedding hash giữ `606e8d8cdccdcc32fb1d8be85e3b553de363669f4f44acd930b689403642c8cb`. Không đổi model/index chỉ vì chuyển đường dẫn cache hoặc Python patch version. Manifest reviewed còn nhãn lịch sử `parser_span_mapping=pending_step05`; canonical mapping đã có ở [artifact riêng](../eval/mappings/reviewed-v1-source-v1-e5-350-v1.json), không sửa manifest đã khóa tại chỗ.

Đối chiếu 422 tracked files với snapshot trước khôi phục: chỉ README/CLAUDE/KNOWLEDGE thay đổi, thêm báo cáo này; source, mọi lockfile, migrations, corpus/mapping và reports cũ giữ nguyên bytes. Scan 423 candidate files không thấy ba secrets riêng trong `.env`; không in values. `.env`, cache, venv và node_modules đều được ignore. Tất cả package versions trong runtime/dev/worker locks đã đối chiếu với metadata cài đặt và khớp, gồm Torch CPU direct-wheel version.

Bằng chứng local của đợt khôi phục trong `.cache/restoration/`: `backend-tests-initial.xml`, `backend-tests.xml`, `eval-tests.xml`, `model-files.json`, `profile.json`, `runtime-probe.json`, `final-state.json`, `integrity.json` và snapshot hashes trước thay đổi. Đây là artifacts kiểm chứng máy nhận được ignore; không thay các report đã khóa trong `eval/reports/`. Git whitespace và local file links của 7 tài liệu chính/runbook đạt. Source runtime không đổi, nên không cộng thêm tiến độ sản phẩm hoặc đánh dấu human review/E2E đã hoàn thành.

Snapshot khi regression đang chạy: Windows 11 Home Single Language, RAM total 15,75 GiB/available 2,33 GiB; C available 86,33 GiB. Containers: DB khoảng 62,33 MiB, Qdrant 198,7 MiB. Đây là ảnh chụp có ứng dụng khác đang chạy, không phải capacity benchmark. Giữ CPU/batch4/threads2/concurrency1; không nạp challenger hoặc chạy nhiều model đồng thời. Khi thực thi local E5 probe, đợi regression kết thúc để giảm tranh tài nguyên.

```powershell
Push-Location backend
New-Item -ItemType Directory -Force .cache | Out-Null
# Mỗi lần chọn basetemp mới; pytest có thể dọn đường dẫn basetemp đã tồn tại.
./.venv/Scripts/python.exe -B -m pytest tests -q -p no:cacheprovider --tb=short --basetemp .cache/restore-20261105-r2
Pop-Location
./backend/.venv/Scripts/python.exe -B -m pytest eval/tests -q -p no:cacheprovider --tb=short
./backend/.venv/Scripts/ruff.exe check --no-cache --config backend/pyproject.toml backend/app backend/tests backend/alembic eval scripts
./backend/.venv/Scripts/ruff.exe format --check --no-cache --config backend/pyproject.toml backend/app backend/tests backend/alembic eval scripts
./backend/.venv/Scripts/python.exe -B -m pip check
Push-Location frontend
npm.cmd run lint
npm.cmd run build
Pop-Location
```

Sau setup, API và worker chạy ở hai terminal riêng, cùng cwd `backend/` và storage profile:

```powershell
# Terminal API, từ backend/
./.venv/Scripts/python.exe -B -m uvicorn app.main:app --reload
# Terminal worker, từ backend/, sau khi dừng tests/eval
./.venv/Scripts/python.exe -B -m app.worker
# Terminal frontend, từ frontend/
npm.cmd run dev
```

Frontend hiện vẫn là placeholder Operations; UI RAG thuộc đợt Bước 10 được duyệt riêng. Khôi phục môi trường không hoàn thành human-quality review/held-out hoặc clean Compose packaging. Giữ bất biến reviewed corpus, parser mapping, applied migrations và eval reports cũ.
