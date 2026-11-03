# Cấu hình Gemini cho smoke test — ngân sách 0 USD

Đối chiếu tài liệu chính thức ngày **03/11/2026**. Người dùng đã tạo key riêng, cung cấp ảnh project Free/quota chưa dùng; smoke Gemini thật đã chạy 5 requests ban đầu và 1 retest được duyệt riêng. [Kết quả và giới hạn](model-smoke-step03.md). Hướng dẫn dưới dùng cho thiết lập/kiểm tra lại, không thay việc xác minh tài khoản mỗi đợt. Embedding local không cần key Gemini.

## 1. Tạo hoặc chọn project Free

Mở [Google AI Studio — API keys](https://aistudio.google.com/apikey) và đăng nhập. Chọn project riêng cho demo SME, kiểm tra project đó ở [Projects](https://aistudio.google.com/projects). Tài liệu Google mô tả mọi key gắn với một Cloud project và AI Studio có thể tạo project mặc định cho người dùng mới; giao diện/tên nút có thể thay đổi. [Hướng dẫn key](https://aistudio.google.com/docs/api-key).

Kiểm tra project đang **Free**, chưa liên kết billing account. Giữ nguyên trạng thái đó, không dùng thao tác nâng cấp/Set up billing/Prepay. Nếu project hiện đã có billing, hãy chọn/tạo project khác chưa bật billing trước khi smoke. Theo tài liệu billing, liên kết billing là bước chuyển sang paid tier; key riêng không tạo quota riêng cho từng key. [Billing](https://aistudio.google.com/docs/billing), [rate limits](https://aistudio.google.com/docs/rate-limits).

**Cách tìm đúng project:** mở trang API keys, xem tên project gắn với key vừa tạo; sang Projects tìm đúng tên đó rồi xem cột **Billing Tier / Status**. Không cần sao chép hoặc gửi giá trị key.

| Trạng thái thấy trên Projects | Cách hiểu cho đợt smoke 0 USD |
|---|---|
| Free; hoặc có hành động Set up billing | Set up billing là dấu hiệu project chưa gắn billing account theo tài liệu Google; giữ nguyên trạng thái, không bấm để nâng cấp |
| Tier 1/2/3, Prepay hoặc Postpay | Project có cấu hình paid; chưa xác nhận điều kiện chạy của project này |
| Set up Prepay hoặc No credits | Không suy ra Free từ số dư 0; kiểm tra billing hoặc chọn project Free khác |

Nguồn giải nghĩa các nhãn: [Google — Verify billing status](https://aistudio.google.com/docs/billing#verify-billing).

## 2. Kiểm tra model và quota

Trong [Rate limits](https://aistudio.google.com/rate-limit), chọn đúng project và kiểm tra quyền dùng `gemini-3.5-flash-lite`, RPM/TPM/RPD còn khả dụng. Smoke dự kiến tối đa **5 requests tuần tự**, không retry; thời điểm khác có thể cần chờ quota reset. Khi quota không đủ, giữ bước này chưa chạy.

Tìm đúng dòng model và đọc **RPM** (requests/phút), **TPM** (input tokens/phút), **RPD** (requests/ngày), cùng usage nếu giao diện có hiển thị. Quota áp dụng cho toàn project, không chỉ key mới. Nếu không thấy model hoặc limit bằng 0, chưa xác nhận chạy được. Bạn có thể báo lại tên trạng thái tier và các con số này bằng văn bản; không gửi key. Nếu RPM thấp hơn số requests định chạy, cần điều chỉnh nhịp chạy trước khi smoke, không bật billing để tăng quota.

Kiểm tra lại [bảng giá model](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) ngay trước lần chạy: ngày kiểm tra hiện tại, standard text input/output có free tier. Free tier công khai không chứng minh key/project cụ thể của bạn được miễn phí hoặc còn quota. Chỉ dùng corpus giả lập trong smoke; bảng giá công bố dữ liệu free tier có thể được dùng cải thiện sản phẩm.

## 3. Tạo key và lưu riêng trong `.env`

Tạo key trong project vừa kiểm tra rồi lưu vào **file `.env` tại repository root**, không phải `.env.example`. Tài liệu hiện hành của Google mô tả key mới trong AI Studio là authorization keys; dùng quy trình mặc định của AI Studio. [Quản lý key](https://aistudio.google.com/docs/api-key#api-keys).

Các dòng cần cấu hình:

```dotenv
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_MODEL=gemini-3.5-flash-lite
LLM_API_KEY=<dán key thật vào đây trong file .env>
LLM_FREE_TIER_CONFIRMED=false
LLM_QUOTA_CONFIRMED=false
```

Sau khi tự xác nhận project chưa bật billing, model có free tier và quota đủ, đổi **hai flags** thành `true`. Hai flags ghi nhận xác nhận của bạn, không phải công cụ đọc trạng thái billing của Google. Giữ `false` nếu chưa chắc chắn. Adapter đọc `LLM_API_KEY` theo quy ước project, gửi header `x-goog-api-key` tới endpoint Google cố định.

Không gửi key qua chat hoặc commit. `.env` đã được ignore; giữ placeholder trong `.env.example`. Nếu key bị lộ, thu hồi/đổi key qua AI Studio trước khi sử dụng tiếp.

## 4. Chạy sau khi cấu hình và xác nhận đợt thực thi

Báo lại rằng bạn đã cấu hình key và kiểm tra project/quota, không cung cấp nội dung key. Bước smoke thật thuộc đợt cần xác nhận theo AGENTS; đợt chuẩn bị hiện tại kết thúc với LLM `not_run`.

Lệnh từ root, trong đợt chạy đã được xác nhận:

```powershell
.\backend\.venv\Scripts\python.exe -B -m eval.model_smoke llm
```

Runner tự tạo thư mục report mới dưới `eval/reports/`; không ghi đè run cũ. Thiếu key/model/endpoint hoặc xác nhận free/quota thì `not_run` với **0 requests**. HTTP lỗi, hết quota, timeout hoặc JSON/citation-ID sai thì dừng lượt, không retry hay đổi sang provider/model trả phí. Bản thân code không có quyền ngăn một billing account được bật bên ngoài; giữ project Free là điều kiện vận hành bắt buộc cho ngân sách 0 USD.

## 5. Kiểm tra kết quả

Report lưu schema/ID validity, usage provider trả về, model version, thời gian và error code an toàn. Không lưu key, headers, provider error body hoặc thought parts. Usage thiếu là `null`; không tự biến số token thành hóa đơn 0 USD. Sau model run vẫn cần người chấm nội dung từng câu, vì JSON hợp lệ và citation ID tồn tại không chứng minh claim đúng.

Smoke dùng 4 câu dev và 1 case xung đột tự soạn có nhãn riêng; chưa dùng test questions để tune. Đường gọi này dùng native REST `generateContent`, chưa nối vào production answering API và chưa chứng minh end-to-end RAG.

**Cập nhật lượt tiếp theo ngày 03/11/2026:** key đã được người dùng điền vào .env; chỉ kiểm tra sự hiện diện, chưa chứng minh key hoạt động. Người dùng chưa kiểm tra billing/quota nên hai flags vẫn false. [Preflight lần 2](../eval/reports/smoke_llm_preflight_20261103_02/metrics.json) ghi not_run, 0 requests và 0 USD. Đợt LLM đã được người dùng yêu cầu tiếp tục; thông tin còn thiếu là điều kiện tài khoản, không phải cần gửi key hoặc cấp lại quyền cho cùng phạm vi.

**Cập nhật sau ảnh xác nhận:** ảnh project Free level và counters quota chưa dùng được ghi nhận như xác nhận thủ công, hai flags đã đặt true. Key đã được Google endpoint chấp nhận trong live run. [Run đầu](../eval/reports/smoke_llm_20261103_01/assessment.md) 4/5 outputs hợp lệ; [retest conflict](../eval/reports/smoke_llm_conflict_20261103_02/assessment.md) 1/1 đạt sau xin thêm đúng 1 request. Tổng 6 calls, không bật billing/fallback. API cost live để null vì chưa có đối chiếu hóa đơn, không suy từ standard serviceTier thành Free. Không gửi key qua chat; flags không tự biến thành billing cap phía Google.
