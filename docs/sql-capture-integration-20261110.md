# Capture integration với PostgreSQL/Qdrant thật — 10/11/2026

Phạm vi được xác nhận bằng “Thực hiện đi bước tiếp theo”: bật storage từ images hiện có, xác minh DB test riêng, chạy capture integration với embeddings/provider giả, cập nhật tài liệu và kiến thức. Không sửa UI, `.env`, dependencies hay code production trong đợt này; không inference E5/Gemini, tải weights/image, mở nội dung held-out, commit/push. Đây là kiểm chứng tích hợp phần mềm, chưa phải phép đo chất lượng AI.

## Môi trường và cô lập

- `docker compose up -d --wait --wait-timeout 120 --pull never --no-build db qdrant` đã thành công; cả hai container healthy. Dùng đúng images pin trong `compose.yaml`, giữ volumes hiện hữu. Hai container được để chạy sau kiểm thử, không khởi động backend/worker dev mới.
- Probe `copilot_test`: guard khác dev đạt, SELECT 1 đạt, Alembic head `20261103_rag04`, queued/retry_wait/running jobs bằng 0; Qdrant `/readyz` HTTP200. Không in DSN/password/key.
- Suite tạo/migrate **`copilot_capture_test`**, suy từ TEST_DATABASE_URL đã qua guard rồi kiểm lại target thực. Không migrate dev hoặc dùng chung queue với `copilot_test`. Advisory lock chặn hai lượt suite cùng DB; không thay thế việc tránh worker ngoài suite dùng DB này.
- Mỗi ca có workspace/user/bearer thật, collection `final_<grant fingerprint prefix>` và storage dưới basetemp riêng: `backend/.cache/final-capture/<scope>`. Runtime nhận sessionmaker/engine thực và settings theo app; không override identity/retrieval/publish.
- Dùng Python3.12.6 của pgAdmin + packages hiện hữu. Venv vẫn thiếu interpreter gốc; không cài/sửa runtime hệ thống. Runner gỡ key LLM khỏi process, flags false, HF offline. Test chặn khởi tạo LocalEmbedder/GeminiProvider, HTTP ngoài Qdrant local/TestClient và mở các thư mục corpus/mapping/report thật.

## Đường đi đã triển khai

[Suite](../eval/tests/test_runtime_capture_sql.py) tạo một policy TXT và một câu hỏi tổng hợp; manifest/CSV approval là fixture contract có nhãn, **không phải human review thật**. Parser/chunker thật tạo mapping trước ingestion. Upload stream/register và IngestionWorker thật đưa source blocks/chunks vào SQL, upsert/verify/publish Qdrant bằng unit vectors 384 chiều giả. Query đi qua login, session API, production retrieval/SQL revalidation, context builder, SourceCheckedProvider, answer validation/publish và SqlCanonicalSources thật. Provider trả JSON cố định, token counter dùng code points; không suy ra ranking hoặc token budget E5/Gemini thực từ các fakes này.

Capture/export/replay giữ `origin=offline_fixture`, `provider_kind=fake`, không override auth. Worksheet vẫn pending; correctness/faithfulness chưa có điểm người chấm. Request ledger đếm **lời gọi fake interface**, không phải requests tới Google.

## Lỗi môi trường và sửa test harness

1. Python embedded có `python312._pth`, bỏ qua PYTHONPATH. Parser subprocess lần đầu trả `parse_failed` trước ingestion. Suite thêm bootstrap đường dẫn packages cho đúng subprocess `app.services.parsing`; vẫn chạy module/parser thật ở child process với timeout/serialization production. Không thay parser bằng inline fake hoặc sửa file Python hệ thống.
2. Admin connection của fixture ban đầu thiếu connect_timeout và chờ lâu. Stack dump xác định đang chờ psycopg connect; thêm timeout5s như các engine/probe khác. Chưa kết luận lỗi DNS/IPv6 chỉ từ stack này. Hai lượt chẩn đoán đang chờ đã dừng đúng process test tự tạo; không dừng process Python/dev khác.
3. Ca canonical drift ban đầu kỳ vọng ValueError, nhưng collector đã chuyển thành HTTP503 `eval_source_drift` theo contract. Sửa assertion theo mã lỗi thật; không cần đổi production code. Ba ca thành công/budget/source-change đã đạt ở lượt trước ca này.

## Kiểm chứng và artifacts

**6 integration tests đạt** trong 66,44s và **116 regression tests đạt** trong 18,29s (122 tests tổng cộng, không phải accuracy); mỗi suite có cùng warning Starlette/httpx đã có trước. Ruff check/format đạt trên ba Python files mới. Không chạy lại full backend reliability suite hoặc browser. Rà 271 liên kết nội bộ trong sáu tài liệu cập nhật không thấy target thiếu; diff whitespace đạt.

| Ca integration | Kết quả có bằng chứng |
|---|---|
| Login → ingest → query → publish → replay/export | Có citation SQL thật; cùng request ID trả đúng output, không thêm reservations/generation; ID mới bị409; canonical chunk ref/final context được capture; fake origin và pending human score giữ đúng |
| Budget đã hết | HTTP503 eval_budget_exhausted trước fake count/generate, retrieval completed giữ trong failed capture |
| Nguồn đổi giữa generation | HTTP409 source_changed, run failed, không assistant citation, không xuất draftanswer như completed |
| Canonical SQL text drift | HTTP503 eval_source_drift trước fake provider; capture failed |
| Auth/mutation | Thiếu bearer401, delete ngoài scope403, chưa admit attempt/call |
| Không còn nguồn ready | insufficient_evidence, empty retrieval/context, không gọi provider |

Probe cleanup sau suite: DB capture ở head `20261103_rag04`, cả 12 bảng fixture (workspace/user/token/document/revision/block/chunk/job/session/message/run/citation) đều 0 rows; Qdrant còn 0 collections prefix `final_`. DB test gốc vẫn 0 pending jobs, Qdrant readyz 200. Đây là trạng thái đo sau chạy, không khẳng định tất cả dữ liệu dev đã được audit. Giữ DB/schema, không drop database; giữ source files/capture/SQLite/report dưới basetemp để kiểm tra lại.

Logs: `.cache/sql-capture-20261110/pytest-sql.txt`, `pytest-regression.txt`, `storage-summary.txt`. Basetemp đạt: `.cache/sql-capture-tests-20261110-r5`, regression `.cache/sql-capture-regression-20261110-r1`. Giữ basetemp lỗi/chẩn đoán r1–r4; r2/r3 bị dừng khi chờ kết nối. Không ghi đè captures lịch sử hoặc eval/reports. Fixtures/artifacts chỉ ở `.cache` bị Git ignore.

Lệnh tái lập cần đợt được xác nhận vì tạo DB/dữ liệu/artifacts:

```powershell
# Từ root; thay interpreter bằng Python phù hợp trên máy nhận.
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -u -I -B scripts/run-capture-integration.py eval/tests/test_runtime_capture_sql.py -q -p no:cacheprovider --basetemp=.cache/<new-unique-directory>
```

Runner không bật storage hoặc tải/cài bất kỳ thứ gì. Probe chỉ đọc: `scripts/check-capture-storage.py`; `--activity` chỉ in DB/state/wait event/SQL verb, không raw SQL hay credentials.

## Giới hạn và đợt tiếp theo

Không kiểm chứng model quality, native token counting, embeddings thực, browser E2E, full delete/history lifecycle, visual/keyboard QA hoặc human/held-out acceptance. Dọn fixtures là housekeeping test, không thay bằng chứng sản phẩm xóa tài liệu theo Bước09. DB/schema test và artifacts filesystem được giữ để xem lại; rows/collection của từng ca phải được dọn đúng IDs/scope. Không reset dev volumes.

Sau integration mới đề xuất một live dev smoke **hai câu tổng hợp** (một answerable, một unanswerable), local E5 cache và Gemini qua ledger: tối đa **4 generateContent +14 countTokens** toàn đợt, gồm repair; không paid fallback, không warmup LLM hoặc auto-rerun ngoài cap. Cần xác nhận phạm vi/code runner và free-tier/quota trước calls, dừng nếu không xác minh hoặc không có model cache. Chưa thực hiện hoặc cấp quyền live từ đợt integration này. UI/browser và final held-out/human review vẫn là các đợt riêng.

**Tiến độ giữ 83,4% /100%** theo trọng số PLAN; chưa đóng đầu việc acceptance mới.
