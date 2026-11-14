# 00 — Dọn nợ kỹ thuật: GIF demo và test heartbeat

Phần đầu ghi kết quả **00-T4** tại thời điểm hoàn tất T4. Kết quả và tiến độ mới nhất sau **00-T1** nằm ở [phần heartbeat](#00-t1--ổn-định-test-heartbeat).

**Ngày:** 15/11/2026 (giờ Việt Nam). **Nhánh:** `feat/00-housekeeping`, chưa push/merge.
**Phạm vi:** chỉ task T4 trong [00-housekeeping](roadmap/00-housekeeping.md); T1–T3 chưa thực hiện.
**Trạng thái:** hoàn tất 00-T4; kiểm chứng backend lần cuối 316/316 đạt.

## Kết quả

- [README](../README.md) hiển thị [GIF](images/demo.gif) ngay sau phần giới thiệu, có alt text tiếng Việt và ghi rõ đã cắt ngắn thời gian chờ AI; giữ cả hai ảnh tĩnh.
- Luồng quay từ UI thật: gõ từng ký tự → gửi câu hỏi → câu trả lời có nhãn **AI-generated**, trạng thái **Có nguồn dẫn** → bấm trích dẫn → mở `quy_dinh_nghi_phep.docx`, Đoạn 1–6, trong khung nguồn nền vàng.
- Câu hỏi: **“Đơn nghỉ phép thông thường cần gửi trước bao lâu và ai phê duyệt?”** Câu trả lời nêu trước ít nhất **3 ngày làm việc**, **quản lý trực tiếp** phê duyệt; đã đối chiếu hai ý với đoạn nguồn hiển thị.
- GIF: **960×600 px, 150 khung × 100 ms = 15 giây, 10 fps, lặp vô hạn, 484.047 bytes** (khoảng 473 KiB, dưới 5 MB).
- SHA-256: `0bfabf182af1e2c60e7756898ac45cacf7bef6f1bbaf7430aabc9dfd704ed17c`.

Không sửa UI/code app, API, schema, model, prompt, project dependencies hoặc lockfiles. Chỉ thêm script quay, GIF và tài liệu. Dùng 10 tài liệu demo đã có; không upload/xóa tài liệu. Hai phiên chat mới được giữ lại trong development DB. Các token đăng nhập của script đã được logout (HTTP 200); stack do launcher mở đã được dừng, Docker/storage giữ nguyên.

## Công cụ và tái tạo

[scripts/record_demo_gif.mjs](../scripts/record_demo_gif.mjs) dùng Node **24.11.1**, WebSocket tích hợp và Edge headless **157.0.4341.46** qua CDP trên loopback. Viewport 1280×800, `Page.captureScreenshot` scale 0,75. Mật khẩu chỉ đọc từ biến môi trường `DEMO_ADMIN_PASSWORD`; không ghi vào script, đối số dòng lệnh hay report.

`gifenc@1.0.3` được cài riêng trong `.cache/tools/gif/`; không thêm Puppeteer/Playwright hay thư viện ảnh khác. PNG được đọc bằng Node zlib; gifenc quantize màu, transparency/disposal 1 giữ pixel không đổi từ khung trước. Cách encode toàn bộ ảnh lặp lại ban đầu vượt 5 MB; nén phần không đổi giữ đủ 150 khung và thời lượng 100 ms. Bản cuối dùng 254 màu cộng một màu transparency, ánh xạ màu bằng cache RGB chính xác để giảm lẫn các nền trắng/xanh nhạt gần nhau.

Lệnh chuẩn, từ gốc repo (Node/npm cần có trong PATH):

```powershell
npm.cmd install --prefix .cache/tools/gif --no-audit --no-fund --save-exact gifenc@1.0.3
.\start-web.cmd -NoBrowser
# DEMO_ADMIN_PASSWORD phải có trong process environment, lấy từ .env riêng.
node scripts/record_demo_gif.mjs --check
node scripts/record_demo_gif.mjs --record
.\stop-web.cmd
```

`--check` chỉ đăng nhập/kiểm tra dữ liệu/chụp ảnh, không hỏi Gemini. `--record` đặt trước một lượt trong ledger **trước khi submit**. Hai lượt đã dùng hết; script hiện chặn lần quay thứ ba, không được xóa/reset ledger để quay thêm nếu chưa có phạm vi ngân sách mới được duyệt.

Ghép lại bản cuối từ PNG đã lưu, **không mở browser hay gọi model**:

```powershell
node scripts/record_demo_gif.mjs --encode .cache/demo-gif/2026-11-14T18-08-41-906Z
```

PNG, manifest, ledger và bằng chứng giải mã nằm trong `.cache/demo-gif/` đã gitignore. Clone mới không có cache này; script vẫn tái tạo được bằng một lượt quay mới được phê duyệt và DB demo đã khôi phục. Không reset ledger của đợt này.

## Ledger Gemini và sự cố lượt đầu

Người dùng duyệt tối đa **2 lượt hỏi**, ngân sách **0 USD**, giữ free tier và không paid fallback. Không gặp lỗi quota/quá tải, không retry provider. Gọi trước 15:00 giờ Việt Nam; đây là khuyến nghị giờ chạy trong task, không phải điều kiện bắt buộc. Cấu hình hai cờ free tier/quota là xác nhận thủ công, không phải hard billing cap.

| Lượt | Run ID | Kết quả quay | Thời gian backend | generateContent | countTokens |
|---|---|---|---:|---:|---:|
| 1 | `7eeef6ed-aaa3-41b1-b0bb-8d428f64b14c` | Backend hoàn tất; khung quay có `session_busy`, bị loại | 54,694 s | 1 | 7 |
| 2 | `f234bdcc-fc4a-48be-a3f9-c0a9739e6e6d` | Bản GIF được dùng | 27,515 s | 1 | 7 |
| Tổng | 2 câu hỏi | Dùng đủ grant | — | **2** | **14** |

Số generation lấy từ `generation_attempts` đã lưu trong PostgreSQL; số countTokens **suy ra** từ hai run thành công và đường đi `build_context`: một base count + năm candidate counts + một final count/run. Đây không phải bộ ghi HTTP độc lập. `usage` được giữ trong ledger cache; chi phí hóa đơn chưa đối soát (`costUsd: null`), không ghi 0 như số tiền đã đo.

Lượt đầu chuyển từ trang chat mới sang phiên có auto-send trong development StrictMode; request trùng gặp `session_busy`, trong khi run gốc vẫn hoàn tất. Có thử ghép tiếp từ lịch sử của cùng run bằng GET, không hỏi thêm model; khi rà hình phát hiện khung chờ vẫn chứa lỗi nên loại toàn bộ bản này. Script cuối chuẩn bị phiên trống trước khi quay, submit từ trang phiên đã ổn định và từ chối chụp khung có `.feedback-error`. Không sửa logic app trong task này; nguyên nhân race chính xác và cách sửa app cần một task riêng nếu muốn xử lý.

## Kiểm chứng

- Node `--check scripts/record_demo_gif.mjs`: đạt. Prettier của frontend đã có sẵn: `--check scripts/record_demo_gif.mjs` đạt; không cài dependency mới cho định dạng.
- Luồng thành công trên Edge thật: đăng nhập, đọc tài liệu sẵn sàng, gửi một câu hỏi trong phiên trống, hiển thị nhãn AI và trích dẫn, mở đúng đoạn nguồn; đã xem lại chuỗi ảnh tổng hợp toàn bộ 15 giây cùng ảnh gốc ở bước chờ/trả lời/nguồn.
- Mở GIF bằng decoder của Edge (`ImageDecoder`): giải mã **150/150** khung, mỗi khung 100 ms, `repetitionCount = Infinity`. So sánh cả 150 ảnh sau giải mã với PNG gốc: sai số trung bình kênh lớn nhất **2,2571/255** (GIF bảng màu mất một phần màu); không có pixel nào lệch quá 40 mức kênh. Ngưỡng kiểm tra 3/255 trung bình và dưới 0,5% pixel lệch lớn được dùng cho kiểm tra compositing, không phải chỉ số accuracy của AI. Rà hình xác nhận không lộ token, mật khẩu, đường dẫn máy hoặc thanh địa chỉ/tab.
- Thử lượt hỏi thứ ba: script trả lỗi budget **trước khi mở Edge**, hash ledger không đổi; không phát sinh câu hỏi/model call.
- Backend lần 1: `315 passed, 1 error` trong 413,34 s. Lỗi setup `tests/test_search.py::test_technical_failure_is_not_empty_success[invalid_embedding]`: Qdrant timeout 2 s khi tạo payload index `revision_id`, trước logic assertion. Chạy riêng lại: **1 passed** trong 3,68 s, không sửa code/config.
- Backend lần 2: `315 passed, 1 error` trong 474,31 s; lỗi setup tương tự tại `tests/test_deletion.py::test_delete_during_counting_prevents_any_generation_and_registration`, timeout tạo payload index `workspace_id`. Test này chạy riêng lại: **1 passed** trong 5,32 s. Cả hai container đều healthy; không còn Edge do task tạo chạy nền.
- Backend lần 3 (cuối): **316 passed, 1 warning** trong **400,52 s**, exit 0; log tại `.cache/demo-gif/backend-final.log`. Đây là một lần chạy toàn bộ đạt, không phải gộp các lượt chạy riêng. Warning sẵn có là Starlette deprecate HTTPX TestClient; không sửa dependency ngoài phạm vi.
- Ruff: `ruff check --no-cache .` đạt; `ruff format --check --no-cache .`: **78 files already formatted**.
- Trước commit: `git diff --cached --check` đạt; stage đúng 6 file; quét giá trị private từ `.env` cùng pattern API/private key trên bytes đã stage không có phát hiện. Hash/kích thước GIF đã stage đúng bản kiểm tra; README giữ đủ 3 ảnh (GIF + 2 ảnh tĩnh); các liên kết local trong README, KNOWLEDGE và report đều hợp lệ. Tooling và ledger cache đều bị gitignore.
- Frontend/eval tests không chạy lại vì không sửa UI, `eval/` hay service mà eval dùng. Không thay đổi test suite, prompt/model hoặc cấu hình chạy app.

Backend chạy bằng lệnh roadmap, khi web stack đã dừng:

```powershell
cd backend
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\ruff.exe check --no-cache .
.\.venv\Scripts\ruff.exe format --check --no-cache .
```

## Giới hạn và tiến độ

- GIF chỉ minh họa một câu hỏi và dữ liệu giả lập; không phải benchmark hay bằng chứng human review mới. Thời gian chờ bản cuối thực tế khoảng 27,5 s được cắt còn một giây trong GIF, ghi chú tại README.
- API/app/DB vẫn giữ nguyên hành vi; sự cố race của lượt đầu chưa được sửa trong app. Bản GIF cuối quay trực tiếp, không dùng kết quả từ lịch sử của lượt trước.
- M1 giữ **97,4% / 100%** theo trạng thái PLAN v1.32 đã công bố; không đọc/sửa PLAN trong task roadmap.
- **00: 1/4 task xong (chỉ T4)**. Trọng số: M2 41, M3 40, M4 48, tổng 129; tiến độ **M2 2,4% / 100%**, **M3 0% / 100%**, **M4 0% / 100%**, **tổng roadmap 0,8% / 100%**. T1–T3 chưa thực hiện; không tự chuyển task tiếp theo.

## 00-T1 — Ổn định test heartbeat

**Ngày:** 15/11/2026 (giờ Việt Nam). **Nhánh:** `feat/00-housekeeping`.
**Trạng thái:** hoàn tất 00-T1; 20 lượt heartbeat liên tiếp đạt và hai lượt backend toàn bộ đạt. Phần T4 ở trên giữ nguyên kết quả tại thời điểm hoàn tất T4.

### Vấn đề và cách sửa

Test cũ giữ fake inference, ngủ cố định 2,2 s với lease 2 s rồi kiểm tra lease còn hạn. Cách này phụ thuộc thời điểm thread heartbeat được CPU/DB phục vụ; sleep không trực tiếp chứng minh heartbeat đã ghi. Đây là nguồn phụ thuộc thời gian xác định được từ code, không phải phép tái hiện chính xác mọi lần fail trước đây.

Chỉ sửa `backend/tests/test_worker.py`, không sửa helper dùng chung hay logic worker:

- Lease của riêng fixture instance trong test heartbeat tăng lên **30 s**, heartbeat vẫn **0,2 s**. Các test recovery/fencing giữ lease 2 s như trước.
- Chờ fake inference báo đã vào bằng `Event`; lấy mốc lease hiện tại rồi đọc qua **session mới** mỗi lần, yêu cầu **hai lần tăng lease đã commit** khi inference vẫn bị chặn. Deadline dùng `time.monotonic()` **10 s**; khoảng nghỉ **50 ms** chỉ giảm tải polling.
- Giữ kiểm tra `FOR UPDATE NOWAIT` lấy được khóa document trong lúc inference chờ. Kiểm tra lease còn hạn theo `clock_timestamp()` của PostgreSQL để cùng nguồn thời gian với queue.
- Luôn thả inference trong `finally`, rồi yêu cầu worker `completed`. Timeout vào inference/kết quả **15 s**, safety timeout của fake inference **30 s**.

Không chọn chỉ tăng sleep vì vẫn phụ thuộc lịch thực thi; không mock DB/heartbeat trong kiểm tra chính vì cần chứng minh thread thật gia hạn được lease. Hai lần tăng quan sát được là ít nhất hai commit, không phải phép đếm toàn bộ heartbeat. Test có timeout hữu hạn và vẫn phụ thuộc DB/Qdrant; 20 lần đạt không bảo đảm mọi môi trường đều hết flaky.

### Kiểm chứng 00-T1

- Dừng web stack bằng `stop-web.cmd`; Docker/storage/volumes giữ nguyên. Sandbox ban đầu chặn launcher, Python nền của venv và Docker; chạy lại các lệnh cần quyền ngoài sandbox, không sửa môi trường/dependencies để né lỗi.
- Dùng `validate_test_database_url` xác nhận DB test tên `_test`, khác development, host **127.0.0.1** trước pytest. PostgreSQL và Qdrant đều healthy; Qdrant ở `http://127.0.0.1:6333`. Fixture tự tạo/dọn dữ liệu test riêng và áp migration hiện có nếu cần; không thêm migration.
- **Heartbeat: 20/20 lượt độc lập liên tiếp đạt**, mỗi lượt gọi pytest trong tiến trình mới; thời gian pytest mỗi lượt **4,04–7,33 s**, tổng **89,05 s** (không tính overhead khởi động shell/interpreter). Log: `.cache/housekeeping-t1/heartbeat-1.log` đến `heartbeat-20.log` (gitignore).
- **Kiểm tra âm:** patch `Heartbeat._run` thành chờ stop chỉ trong một tiến trình Python; pytest trả exit **1**, fail đúng assertion `expected two committed lease renewals during inference; observed 0`, sau **14,15 s**. Wrapper xác minh đúng exit/message rồi trả 0. Không sửa file production; patch kết thúc cùng tiến trình. Log: `.cache/housekeeping-t1/heartbeat-disabled.log`.
- **Backend lần 1:** **315 passed, 1 failed, 1 warning** trong **362,28 s**. `test_multiple_collections_scoped_vector_filter_and_missing_files` lỗi `vector_timeout` khi tạo payload index `revision_id` của collection thứ hai với timeout 2 s; heartbeat đạt. Chạy lại riêng test deletion: **1 passed, 1 warning** trong **8,55 s**, không sửa code/config. Đây là bằng chứng lỗi tạm thời ở yêu cầu Qdrant, chưa xác định nguyên nhân gốc của độ trễ. Lượt full này không tính là đạt. Log: `backend-1.log`, `deletion-recheck.log` trong `.cache/housekeeping-t1/`.
- **Backend lần 2:** **316 passed, 1 warning** trong **354,83 s**, exit 0; log `.cache/housekeeping-t1/backend-2.log`.
- **Backend lần 3:** **315 passed, 1 failed, 1 warning** trong **341,96 s**. `test_concurrent_duplicate_real_transactions` lỗi `storage_error` tại guard `path.is_relative_to(root)` trong `store_stream` (`uploads.py:88`), heartbeat đạt. Chạy lại riêng: **1 passed, 1 warning** trong **0,80 s**. Chưa xác định nguyên nhân gốc của lỗi đường dẫn; không sửa uploads/test_uploads ngoài phạm vi T1. Log: `backend-3.log`, `uploads-recheck.log` trong `.cache/housekeeping-t1/`.
- **Backend lần 4:** **316 passed, 1 warning** trong **330,97 s**, exit 0; log `.cache/housekeeping-t1/backend-4.log`. Đủ **hai lượt toàn bộ đạt (lần 2 và 4), không liên tiếp**; tổng cộng đã chạy bốn lượt, không gộp kết quả chạy riêng thành full pass. Heartbeat đạt trong cả bốn lượt.
- Ruff sau sửa code: `check --no-cache .` đạt; `format --check --no-cache .`: **78 files already formatted**.
- Rà soát trước commit: đúng **4 file** thuộc phạm vi được duyệt; `git diff --cached --check` đạt; **55 liên kết local** trong tài liệu staged tồn tại; quét bytes staged không phát hiện giá trị private lấy từ dotenv hay pattern API/private key. Log kiểm chứng nằm trong `.cache/` được gitignore.
- Không chạy frontend/eval tooling vì không sửa UI, `eval/` hay service mà eval dùng. **0 lần gọi Gemini**; fake embedding có nhãn như fixture hiện có.

Lệnh kiểm chứng từ `backend/` (PowerShell), từng lượt dừng nếu exit khác 0. Hai lượt có lỗi được chẩn đoán/chạy lại riêng như ghi trên, sau đó chạy thêm lượt toàn bộ; các lượt sau dùng thêm `--tb=short`:

```powershell
for ($heartbeatRun = 1; $heartbeatRun -le 20; $heartbeatRun++) {
    .\.venv\Scripts\python.exe -B -m pytest tests/test_worker.py::test_heartbeat_runs_during_inference_without_document_lock -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw "Heartbeat run $heartbeatRun failed" }
}
for ($backendRun = 1; $backendRun -le 2; $backendRun++) {
    .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw "Backend run $backendRun failed" }
}
.\.venv\Scripts\ruff.exe check --no-cache .
.\.venv\Scripts\ruff.exe format --check --no-cache .
```

Tái tạo kiểm tra âm trong tiến trình riêng (kỳ vọng pytest exit 1 và đúng assertion 0 lần gia hạn):

```powershell
$heartbeatProbe = @'
import pytest
from app.worker import Heartbeat
Heartbeat._run = lambda self: self.stop.wait()
raise SystemExit(pytest.main(['tests/test_worker.py::test_heartbeat_runs_during_inference_without_document_lock', '-q', '-p', 'no:cacheprovider', '--tb=short']))
'@
.\.venv\Scripts\python.exe -B -c $heartbeatProbe
```

### Giới hạn và tiến độ 00-T1

Không sửa worker, UI, API/schema, model/prompt hay dependency. Warning Starlette/HTTPX có sẵn; kiểm tra âm còn có warning pytest về module `anyio` đã import trước assertion rewrite. Không dùng test phần mềm làm bằng chứng chất lượng AI/human review.

Hai lỗi ngoài heartbeat chưa được sửa nguyên nhân gốc: độ trễ tạo index Qdrant và guard đường dẫn upload đồng thời cần đợt điều tra riêng nếu tiếp tục xuất hiện. Test heartbeat vẫn có timeout hữu hạn; không khẳng định toàn bộ suite đã hết flaky. Web stack giữ trạng thái đã dừng sau kiểm thử. Không push/merge, không sửa `release/m1`, không chuyển T2/T3.

**00: 2/4 task xong (T1, T4)**. Theo trọng số hiện có: **M2 4,9% / 100%** (2/41), **M3 0% / 100%**, **M4 0% / 100%**, **tổng roadmap 1,6% / 100%** (2/129). M1 giữ **97,4% / 100%** theo PLAN v1.32 đã công bố; không đọc/sửa PLAN trong task roadmap.
