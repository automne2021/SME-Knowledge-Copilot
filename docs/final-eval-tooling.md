# Công cụ chuẩn bị đánh giá offline

**Ngày:** 10/11/2026. **Phạm vi đã thực hiện:** code công cụ offline, fixtures/stubs, kiểm tra metric và tài liệu. Chưa chạy model, embedding, DB/Qdrant, browser hoặc nội dung câu hỏi held-out thật. [Protocol](final-validation-plan.md), [PLAN](../PLAN.md), [KNOWLEDGE K-087](../KNOWLEDGE.md#k-087--công-cụ-offline-cho-freeze-budget-và-human-review).

**Bổ sung sau đợt runtime cùng ngày:** [adapter API và kết quả mới](runtime-capture-step11-preparation.md) đã có hook capture/ledger với test qua route/core thật, storage/retrieval/identity stubs. Các câu “chưa có adapter/chưa gắn runtime” bên dưới mô tả bàn giao offline trước đó. SQL integration, model/browser/held-out thật vẫn chưa chạy; các probe storage đã được ghi riêng trong report mới. Ledger mới có runtime plan binding và LedgerUnavailable, không tự nâng schema hoặc reset các ledger lịch sử.

## 1. Các thành phần

| File | Chức năng và giới hạn |
|---|---|
| [final_eval.py](../eval/final_eval.py) | CLI freeze → replay observations → score worksheet. Nạp split dev/test có guard; kiểm tra hash nguồn/mapping và canonical chunks. Không có chế độ live hoặc tự gọi API |
| [final_budget.py](../eval/final_budget.py) | SQLite ledger với grant/caps cố định, chia batch và reserve trước transport; wrapper tương thích `count_tokens`/`generate`. Chưa được cài vào API/browser runtime |
| [final_review.py](../eval/final_review.py) | Worksheet hai reviewer, kiểm tra output/run hash, bất đồng và adjudication; tổng hợp human metrics từ điểm nhập thực |
| [test_final_eval.py](../eval/tests/test_final_eval.py) | Fixtures tự tạo trong thư mục tạm; chặn network và mở các corpus/mapping/report thật của project |

Hai runners cũ `run_retrieval_eval.py` và `run_answering_eval.py` giữ nguyên behavior/caps lịch sử. Công cụ mới xử lý **offline replay** của dữ liệu được capture; nó chưa tạo capture bằng production API, chưa nghiệm thu source preview/delete/auth trên browser và chưa xác minh provenance của capture bằng một phép chạy độc lập.

## 2. Môi trường đã dùng để kiểm thử

`backend/.venv` hiện trỏ Python312 gốc không tìm thấy; `py -0p` không thấy Python đăng ký. Máy có Python **3.12.6** trong `C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe` và Ruff **0.17.3** trong venv. Đã dùng interpreter có sẵn, không cài phần mềm, sửa `pyvenv.cfg` hoặc dependencies. Toolkit mới chỉ cần standard library; pytest lấy từ site-packages hiện hữu để chạy tests, không chứng minh toàn bộ backend venv đã phục hồi.

Lệnh kiểm chứng đã dùng, từ repo root (chỉ chạy khi đợt tạo artifacts đã được xác nhận):

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -I -B -c "import os,sys; sys.path[:0]=[os.getcwd(), os.path.join(os.getcwd(),'backend','.venv','Lib','site-packages')]; os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'; import pytest; raise SystemExit(pytest.main(['eval/tests/test_final_eval.py','eval/tests/test_metrics.py','eval/tests/test_span_metrics.py','-q','-p','no:cacheprovider','--basetemp=.cache/final-eval-offline-tests-20261110-r3']))"
```

Dùng thư mục basetemp mới cho mỗi lần chạy; không tái sử dụng để tránh pytest xóa artifacts cũ. Đã tắt plugin autoload, bytecode và pytest cache. Không chạy full backend suite vì nó cần môi trường/DB và không nằm trong phạm vi offline này. Khi cần khôi phục venv cho live integration, trình bày phạm vi riêng trước khi cài/sửa runtime.

## 3. CLI và freeze

Khi có Python hoạt động và import được repo, entry point là `python -B -m eval.final_eval`. Trên interpreter pgAdmin đang dùng, entry point tương đương đã kiểm tra help:

```powershell
& 'C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe' -I -B -c "import os,runpy,sys; sys.path.insert(0,os.getcwd()); runpy.run_module('eval.final_eval',run_name='__main__')" --help
```

Các lệnh dưới là **cách dùng cho đợt tương lai**, chưa chạy trên reviewed snapshot thật trong đợt này. Parent output phải tồn tại; dùng tên file/thư mục mới. Freeze ghi hashes và git HEAD/dirty status; không tự commit, không đọc `.env` và không parse nội dung questions. Source fingerprint bao gồm Python files dưới `backend/app` và `eval`; đây chưa phải snapshot dependencies/OS/container đầy đủ.

```powershell
python -B -m eval.final_eval freeze --dataset eval/snapshots/reviewed-v1 --mapping eval/mappings/reviewed-v1-source-v1-e5-350-v1.json --config eval/configs/dense.json --output .cache/<approved-run>/protocol.json
python -B -m eval.final_eval replay --protocol .cache/<approved-run>/protocol.json --capture .cache/<approved-run>/capture.json --split dev --output .cache/<approved-run>/replay
python -B -m eval.final_eval score --report .cache/<approved-run>/replay --reviews .cache/<approved-run>/reviews-filled.json --output .cache/<approved-run>/human-metrics.json
```

Thay placeholders bằng đường dẫn được duyệt. `--split test` cần thêm `--allow-heldout`, chỉ sau freeze và xác nhận thực thi. Flag là guard thao tác, không thay xác nhận của người dùng. Test suite chỉ dùng split tên `test` trong **fixture tự tạo**, không mở 30 câu held-out thật. Protocol dùng canonical-JSON SHA-256 (`fingerprint`), phân biệt với hash bytes của file JSON đã format.

Freeze yêu cầu manifest `human_reviewed` và đúng hashes corpus/questions/source blocks/human ledger, mapping đúng parent. Replay kiểm tra lại trước/sau xử lý; drift bị từ chối. Không dùng freeze mới sau mỗi batch để âm thầm thay model/source khi đang đánh giá một protocol. Các tệp chưa commit phải được mô tả bởi source hashes, không chỉ HEAD.

## 4. Hợp đồng capture offline

Capture JSON gồm đúng `schema=1`, `protocol_sha256`, `origin` (`offline_fixture` hoặc `captured_api`), `split`, `rows`. Mỗi row có ID câu thuộc split đã chọn, trạng thái `completed`/`failed`, captured latency và retrieval `{status,hits,latency_ms}`. Latency là thời gian của capture, không phải thời gian replay.

Một hit là `{document_id, chunk_index, text_sha256}` theo **canonical parser mapping**; `document_id` là external corpus reference, không phải SQL UUID. Offline evaluator lấy text/spans từ mapping đã khóa và tách namespace block theo document để tránh hai tài liệu có cùng `p1` bị tính nhầm. Capture adapter tương lai phải dùng loader revalidation SQL hiện có để chuyển nguồn thực sang mapping, không tự gán reference theo filename.

Row completed có `final_context=[{evidence_id,chunk}]` với IDs E1… theo thứ tự, là tập con không trùng của production top-k; `answer` giữ đủ structured fields `answer_status`, `claims`, `limitations`, `missing_information`, `conflict_detected`. Không gửi nguyên response chứa auth headers, provider bodies hoặc thoughts. Mỗi claim có text và evidence IDs đã cấp. Cấu trúc hợp lệ chỉ là kiểm tra kỹ thuật, không phải semantic pass.

Row failed chỉ giữ error category trong `provider/timeout/retrieval/invalid_output/budget/other`; không xuất draft answer/context hoặc exception text. Retrieval thành công vẫn được chấm riêng nếu answering thất bại. Thiếu row → `not_attempted`; duplicate/foreign/wrong-split IDs bị từ chối, không âm thầm bỏ khỏi mẫu số.

Mỗi replay tạo mới `manifest.json`, `config.json` (frozen protocol), `capture.json` nguyên bytes, `per_question.jsonl`, `metrics.json`, `human_review.json`, `report.md`. Manifest ghi `execution_kind=offline_replay`, origin, hashes, zero calls trong replay và `live_acceptance=not_established_by_replay`. Không suy ra chi phí của model run đã capture bằng 0; captured usage chưa có thì `null`. Không ghi đè artifact cũ hoặc reviewed inputs. Đây là format chuẩn bị, chưa có adapter capture production được triển khai.

## 5. Review và metrics

Copy `human_review.json` sang file mới để hai thành viên điền; giữ bản pending ban đầu. Reviewer mở đúng câu/gold trong dataset và final chunk text trong mapping/config đã khóa, kiểm tra output từng claim/citation. Các scores trong tests là fixture, không phải duyệt của con người.

- Hai reviewer IDs khác nhau, correctness 0/1/2, mỗi claim có supported true/false và từng citation được chấm riêng. Không để script tự điền score.
- Thiếu reviewer/điểm → pending. Bất đồng chưa giải quyết → chưa tính điểm cho câu đó. Nếu cần adjudication, nhập score cuối, reason và `agreed_by` gồm đúng hai reviewer gốc; không tự chọn người có điểm cao hơn.
- Worksheet gắn run ID và hash answer/final_context. Rescore kiểm tra hash các rows đã xuất; không áp điểm cho output khác hoặc sửa rows để hợp review. Hash bảo vệ sai sót/drift, không phải chữ ký chống người có quyền ghi cố ý sửa mọi file.
- Correctness/faithfulness/citation được báo trên phần đã review với số mẫu; strict correctness=2 trên tổng planned chỉ có rate khi mọi successful output đã được chấm. Technical errors/not-attempted không thành abstention đúng. Không đặt một “accuracy” chung cho software tests và model quality.
- Human scores pending → `null`; tỷ lệ không có mẫu cũng `null`. Report tách planned/attempted/not-attempted, strict retrieval và retrieval thành công; không che lỗi bằng cách loại khỏi denominator.

`score` ghi metrics vào file mới cùng review hash và nguồn report; không sửa manifest, output hoặc review cũ. JSON validator không thể chứng minh hai người đã thực sự đọc nguồn; human review vẫn là trách nhiệm của nhóm.

## 6. Ledger dùng cho đợt live sau này

Grant có đúng `scope_id`, `protocol_sha256`, tổng caps cho `generateContent/countTokens` và fixed batches. Tổng allocation batches không vượt total. `RequestLedger.create` chỉ tạo file mới; attach phải đúng grant và ledger hiện hữu. Mỗi scope được duyệt dùng **một ledger ổn định**, mọi batch/process trỏ cùng file; run ID mới không tạo ledger mới để reset ngân sách.

SQLite `BEGIN IMMEDIATE` kiểm tra cap và ghi reservation trong transaction, commit trước transport; timeout/mất response/repair đều tiêu reservation. Reserve lỗi hoặc ledger bị mất thì không gọi provider. Wrapper nhận provider factory lazy, không lưu payload/key trong ledger. DB/caps chỉ giới hạn requests trong runtime đã cài wrapper; không phải billing cap và không chặn một API dev khác đang chạy ngoài scope.

Trước live E2E phải dựng runtime test riêng, cài `GuardedProvider` vào mọi provider factory, kiểm tra lỗi budget được ánh xạ thành technical error đúng và mọi browser query dùng ledger đó. Đợt này chỉ kiểm tra interface bằng fake provider, chưa bật runtime. Dự toán hiện tại 30 queries/top5 → tối đa 60 generation +210 countTokens, chưa warmup/oracle/rerun; số dự toán không phải quyền gửi requests.

## 7. Kiểm chứng và phần tiếp theo

Suite tập trung đạt **57 tests** (toolkit mới cùng regression metric/span), Ruff check/format đạt. Raw output cuối ở `.cache/final-prep-20261110/pytest.txt`; fixtures/replay/ledger nằm trong basetemp riêng đã Git-ignore. Không tạo benchmark chất lượng thật trong `eval/reports`.

Lần đầu có một failure trên Windows do context manager của `sqlite3.Connection` quản lý transaction nhưng không tự đóng connection. File ledger bị giữ handle nên test xóa file báo WinError32. Đã sửa bằng `contextlib.closing` kết hợp transaction context; test chứng minh xóa ledger sau thao tác thành công, request tiếp bị chặn trước transport. Các tests khác gồm concurrency, restart/batch totals, lost response, wrong split, hash drift, citation giả, denominator, worksheet pending/disagreement và CLI freeze/replay/score với fixture.

Tiếp theo cần xác nhận đợt tích hợp runtime/capture và kiểm tra môi trường backend, rồi mới đề xuất live batch với quota/caps cụ thể. Bước 10 mục 5–6, human scoring output thật, final held-out và Bước 12 vẫn pending. **Tiến độ giữ 83,4% / 100%.**
