# Runtime thu capture và giới hạn request — chuẩn bị Bước 10–11

**Ngày:** 10/11/2026. **Loại:** đã triển khai và kiểm thử bằng provider giả; chưa real-model/browser/held-out acceptance. Người dùng xác nhận bước tiếp theo sau toolkit offline. Liên quan [PLAN](../PLAN.md), [protocol](final-validation-plan.md), [toolkit offline](final-eval-tooling.md), [KNOWLEDGE K-088](../KNOWLEDGE.md#k-088--capture-trong-pipeline-thật-với-runtime-kiểm-thử-riêng).

## 1. Kết quả triển khai

| Thành phần | Thay đổi |
|---|---|
| [API chat](../backend/app/api/chat.py) | Hook capture factory nội bộ mặc định tắt; chọn provider đã gắn ledger; báo success/failure cho collector; settings snapshot riêng theo app |
| [Chat service](../backend/app/services/chat.py) | Observer tùy chọn nhận hits sau SQL/source check và final evidence sau packing/revalidation, trước generation |
| [Search/source API](../backend/app/api/search.py) | Đọc settings theo app khi được cấu hình, bao gồm source content storage; app thường vẫn dùng get_settings |
| [Runtime adapter](../eval/runtime_capture.py) | Scope khóa câu hỏi/user/workspace/filter/top-k/batch, thu canonical refs và structured answer, xuất capture nối trực tiếp sang offline replay |
| [Ledger](../eval/final_budget.py) | Pin runtime plan hash bền vững; phân biệt BudgetExceeded với LedgerUnavailable trước transport |
| [Tests runtime](../eval/tests/test_runtime_capture.py) | ASGI route, core answering/context/repair/validation thật; identity, SQL state và retrieval được stub rõ ràng |

Không có tùy chọn capture/model/provider mới trong request schema của sản phẩm. Chỉ code khởi tạo app kiểm thử mới cài `query_capture_factory`, `rag_settings` và provider hook; app mặc định không thu full context hay tạo artifacts mới. Không sửa UI, `.env`, model/index config, reviewed corpus/mapping/reports cũ, dependencies hoặc commit/push.

## 2. Capture lấy dữ liệu ở đâu

Luồng: FastAPI auth/input → kiểm tra scope đã khóa → production query → retrieval/source validation → observer nhận hits → context builder đếm/budget → source revalidation và đăng ký evidence → observer nhận toàn bộ final context → provider có ledger → structured validation/repair → publish → collector nhận output.

Final context gồm cả nguồn không được model trích dẫn. Không suy ngược context từ citations, không chạy một search phụ rồi nhận đó là candidates đã được pipeline dùng. Payload gửi count/generate được đối chiếu question/evidence với observer trước transport. SourceCheckedProvider hiện hữu vẫn revalidate trước mỗi count/generate/repair; hook không thay thế quyền hoặc SQL checks.

`SqlCanonicalSources` dùng `load_active_mapping` để kiểm checksum/parser/index/text/location/spans trên sources thực được tham chiếu, sau đó ánh xạ SQL chunk UUID thành external document reference/chunk index/text hash. Không map bằng filename hay đoán theo text giống nhau. Hai tài liệu có block ID giống nhau vẫn có namespace riêng. Empty hits không tạo nguồn giả; nguồn không thuộc corpus hoặc đổi lifecycle/text bị từ chối. Adapter SQL đã có code và unit test bằng session/loader stub, **chưa chạy với SQL/Qdrant thật trong đợt này**.

Capture của provider fake luôn mang `origin=offline_fixture`, kể cả khi sau này kết hợp với SQL thật; chỉ nhánh SqlCanonicalSources + native Gemini được gắn `captured_api`. Execution file giữ provider kind và các override auth; origin không phải chứng nhận provenance độc lập. Capture/replay vẫn không tự đóng AT-R23 hoặc human-quality gate.

## 3. Cô lập runtime và scope

`CaptureRuntime` chỉ cài trên app mới chưa start. Plan chọn câu từ split đã khóa, kiểm exact question, user/workspace UUIDs, document filters, production top-k và fixed batch. Native provider cần `provider_kind=native_gemini`, `allow_live=True`, đúng GeminiProvider và các flags/config hợp lệ; tạo object không cấp quyền chạy model. Mặc định fake, fallback provider ngoài observer bị chặn.

Đối với SQL adapter:

- Engine thực của sessionmaker phải qua guard DB test local, tên kết thúc `_test`, khác dev; không chỉ tin một chuỗi config khai báo.
- Collection bắt buộc `final_<16 ký tự đầu grant fingerprint>` và storage `<root>/backend/.cache/final-capture/<scope>`; mapping/index phải khớp freeze.
- Khi install phải cấp search runtime có profile khớp; get_db được override sang đúng sessionmaker đó, search/source/query dùng settings app riêng. Không mutate Settings global hay đổi `.env` để chuyển profile.
- Runtime thu baseline chỉ cho auth/search/chat session/query và các thao tác đọc; upload/delete/retry hoặc mutation ngoài scope trả 403. Corpus cần được chuẩn bị riêng đúng scope trước capture; delete/browser lifecycle acceptance cần đợt riêng, không dùng collector này để tự sửa/xóa dữ liệu dev.

Runtime plan hash gồm specs, settings hash không secrets, SQL source binding, origin và provider kind; ledger giữ hash đó qua restart. Thay plan/cấu hình sau bind bị chặn. Một query spec nhận một client_request_id mới; lặp đúng payload có thể replay response mà không thêm calls/capture. Client ID mới cho spec đã dùng bị từ chối, cần một phạm vi attempt được duyệt khác. Collector giữ rows trong RAM; process crash có thể làm mất capture chưa export nhưng reservations SQLite vẫn còn. Chưa có resume tự tái dựng observations; không tự tạo ledger mới hoặc retry để che phần mất.

## 4. Budget và lỗi

Mọi count/generate/repair của route scoped nhận provider riêng gắn chung ledger. Reserve commit trước gọi factory/transport; hết cap → 503 `eval_budget_exhausted`; lỗi/mất ledger → 503 `eval_ledger_unavailable`, không gọi provider. Timeout/HTTP lỗi của provider giữ loại lỗi kỹ thuật riêng và reservation vẫn được tính.

Việc tách LedgerUnavailable ở bước này tránh bắt nhầm TimeoutError (là OSError) phát sinh **sau** transport thành lỗi ledger. Request quota là giới hạn trong runtime đã cài guard, không phải billing cap; flags free-tier/quota là xác nhận thủ công. Với top5 vẫn dự toán tối đa 2 generation +7 count/query, không bao gồm warmup/extra runs. Không có model requests thật trong đợt này.

Capture failure sau publish có thể khiến HTTP trả lỗi dù SQL answer đã commit; reservations và query ID vẫn giữ, không tự generate lại. Failed capture không xuất draft như một câu trả lời đạt. Export kiểm dữ liệu/caps trước tạo thư mục, dùng đường dẫn mới và giữ nguyên captures cũ; mất ledger thì không xuất một bộ artifact trông hoàn chỉnh.

## 5. Sử dụng cho đợt tương lai

Đây là API khởi tạo, **không phải lệnh đã chạy trên corpus/model thật**:

```python
# Chuẩn bị root/protocol/specs/settings/sessionmaker/search runtime và ledger riêng
# trong đợt đã được xác nhận; không dùng dev DB/storage/collection.
sources = SqlCanonicalSources(sessions, workspace_id, uploaded, mapping, profile)
runtime = CaptureRuntime(
    root, protocol, "dev", specs, ledger, sources, scoped_settings,
    approved_provider_factory, provider_kind=approved_provider_kind,
    allow_live=explicit_live_batch_authorized,
)
app = create_app()
runtime.install(app, search_runtime=scoped_search_runtime)
# Gọi app qua client/server kiểm thử; sau khi các requests kết thúc:
runtime.export(new_output_directory)
```

Module không tự start server/container, ingest, migrate hoặc tải model. `specs` có đúng `id/question/user_id/workspace_id/document_ids/batch`; IDs và question phải thuộc split trong protocol. Provider native chỉ chọn ở đợt được duyệt số calls/free tier, không bật trong đợt này. Full held-out cần allow-heldout và freeze riêng trước thực thi.

Output gồm `capture.json` theo schema toolkit và `execution.json` với plan/protocol hash, provider kind, ledger counts, các outcomes/usage có nhãn và auth override flag. Không lưu key, headers, provider raw body hoặc thoughts. Usage thiếu là null. Dùng `eval.final_eval replay` để tạo report/worksheet; không dùng fixture score như review thật.

Chat đang lấy production top5, nên capture ghi `chat_retrieval_top_k=5`; replay @10 trên danh sách này chỉ phản ánh tối đa năm hits đã lấy. Muốn benchmark độc lập top10 phải chạy retrieval-only riêng theo protocol, không gọi @10 từ capture này là một lần search top10 thực tế.

## 6. Kiểm chứng thực hiện

**116 tests đạt, 1 warning Starlette/httpx baseline**: 22 tests runtime, 57 toolkit/metric/span regression và 37 unit tests gốc answering/Gemini adapter. API/controller, SourceCheckedProvider, context builder, prompt/schema validation và repair đi qua code thật; storage/retrieval/identity/publish của các runtime tests là stubs có nhãn. Native adapter tests dùng MockTransport, không gọi Google. Ruff check/format đạt trên 7 Python files bị thay đổi/tạo trong đợt.

Raw log `.cache/runtime-capture-20261110/pytest.txt`, final basetemp `.cache/runtime-capture-tests-20261110-r6`. Không chạy full backend reliability suite, không dùng SQL/Qdrant thật trong tests, không embedding inference hay browser. Không mở nội dung reviewed held-out; fixture guard từ chối mở corpus/mapping/report thật. Tests Settings dùng `_env_file=None`, key None và flags false; không phụ thuộc credentials thật.

Lần đầu kiểm tra network quá chặt đã chặn cả socketpair nội bộ mà asyncio Windows dùng cho self-pipe; TestClient chưa khởi tạo được, chưa tới pipeline. Đã giới hạn ngoại lệ cho cặp loopback tự tạo trong fixture, giữ chặn mọi application socket connect/DNS khác. Không tắt network guard chung hoặc mở kết nối loopback tùy ý tới DB/HTTP. Một test guard DB sau đó kỳ vọng nhầm ValueError; guard hiện hữu trả RuntimeError khi DB test trùng dev và đã chặn đúng trước kết nối; sửa kỳ vọng theo contract gốc.

Các ca có evidence: default route không capture vẫn trả lời; auth thiếu trả401 trước admit; unapproved question/workspace/top-k/filter bị chặn; source/config/plan drift; ledger mất; budget hết trong count; repair dùng reservation thứ hai; timeout được phân loại riêng; no-hits không provider; idempotent replay không gọi lại; final context giữ nguồn không cited; capture → offline replay → pending worksheet; SQL target/collection/storage và source-content settings cô lập được kiểm bằng stubs.

**Cập nhật kế tiếp cùng ngày:** phần kiểm chứng bên trên là đợt stubs ban đầu. [Đợt SQL/Qdrant integration](sql-capture-integration-20261110.md) sau đó đã bật storage từ images có sẵn, xác minh DBtest và đạt6integration+116regressiontests với auth/SQL/retrieval/publish thật, inference giả. Native model/browser/held-out/human review vẫn chưa chạy. Không đọc snapshot môi trường dưới đây như trạng thái storage mới nhất.

## 7. Kiểm tra môi trường và phần còn lại

Python **3.12.6** có sẵn trong pgAdmin import được FastAPI0.162.0, HTTPX0.28.1, Pydantic2.14.1, SQLAlchemy2.1.6 và psycopg3.3.6 từ packages hiện hữu. Venv gốc vẫn thiếu interpreter Python312; chưa sửa/cài dependencies. Import pass không chứng minh dịch vụ hoặc native inference hoạt động.

Kiểm tra chỉ đọc ngày 10/11:

| Probe | Quan sát |
|---|---|
| Docker client/daemon | 27.3.1 /27.3.1; sandbox ban đầu không đọc được pipe/config, kiểm tra chỉ đọc ngoài sandbox đạt |
| Compose ps của project | Không liệt kê container đang chạy trong lần đọc |
| DB test qua guard | Kết nối/probe thất bại OperationalError; chưa thực hiện được SELECT1/schema/job count, không kết luận nguyên nhân cụ thể |
| Qdrant readyz | ConnectError; chưa xác minh ready |
| LLM configuration | Endpoint/model/key có nội dung; hai cờ manual free-tier/quota true; không kiểm key/billing/quota với Google |

Không in DSN/password/API key hoặc raw provider errors. Không bật/dừng container, migrate/seed, ghi DB/Qdrant, sửa `.env`, gọi Gemini hoặc download weights trong probes. Cần khôi phục/khởi động storage trong đợt được duyệt trước SQL integration/model run; không suy từ Docker daemon chạy thành hai storage đã healthy.

**Bước tiếp theo nên trình bày:** bật lại PostgreSQL/Qdrant từ images hiện hữu, xác minh DB test khác dev/schema/queue và chạy integration capture với SQL/Qdrant thật, embeddings/provider giả trên tài nguyên riêng; model calls vẫn0. Nếu thiếu images/schema/dependencies hoặc cần mở rộng thao tác, trình bày bổ sung trước thay đổi. Sau đó mới chốt dev live smoke với số calls/quota cụ thể, rồi E2E/human review/held-out. Giữ **83,4% /100%** vì chưa đóng Bước10 mục5–6 hoặc Bước11.
