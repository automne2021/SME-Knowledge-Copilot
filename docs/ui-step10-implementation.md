# UI Bước 10 — triển khai và bằng chứng kiểm tra

> Cập nhật11/11/2026: hai mục browser E2E/keyboard-navigation còn mở trong bản ghi05–06/11 đã hoàn tất qua [Chrome retry-01](browser-e2e-retry-20261110.md). Bước10 hiện6/6, tiến độ87,3%/100%; human-quality/held-out vẫn pending. Các số liệu/trạng thái bên dưới giữ theo từng đợt lịch sử.

Ngày: 05/11/2026. Người dùng xác nhận “bắt đầu code UI, thực hiện đi” theo [kế hoạch đã trình bày](ui-step10-plan.md). Phạm vi frontend, dependencies icon/test, kiểm tra và tài liệu. Không đổi backend contract/schema/model/prompt, không gọi Gemini, không commit/push.

**Trạng thái:** đã triển khai 4/6 đầu việc Bước 10; browser E2E và kiểm tra trực quan/bàn phím/responsive trên trình duyệt thật còn pending. Không coi Bước 10 hoặc AT-R23 hoàn thành. Tiến độ trọng số `(77,5 + 12 × 4/6) / 102,5 = 83,4% / 100%`.

## Giao diện đã viết

- Light theme nền trắng/xám, một accent navy, font hệ thống; điều hướng Hỏi đáp/Tài liệu bằng chữ. Chỉ dùng Lucide Plus ở cuộc trò chuyện mới và Upload ở nút tải tài liệu, đơn sắc/cỡ16. Không avatar/illustration, gradient, typing giả hoặc số confidence.
- Login lấy identity/role từ server; guard routes, kiểm tra TTL và `/auth/me`, xử lý 401, đăng xuất cục bộ. Token lưu sessionStorage theo tab, fallback memory nếu storage không dùng được. Không có role selector hoặc mật khẩu demo cài sẵn trong UI.
- Documents nối list/upload/job/retry/delete APIs. Admin có write controls; member xem nguồn. Poll từ2s/backoff tối đa10s, dừng terminal/unmount và tạm dừng sau15phút chờ; server job không bị đổi thành failed vì UI hết chờ. Không có phần trăm giả. Scan/warnings/failed và cleanup failure hiển thị riêng.
- Delete yêu cầu đúng filename; 202 hiển thị đang dọn, phát tín hiệu invalidate nội dung liên quan. Không coi việc ẩn nút là kiểm tra quyền server.
- Chat có sessions, câu hỏi độc lập, filter tài liệu ready, structured claims/citations, AI-generated label, partial/abstention/technical error. Không render HTML/Markdown tự do từ claim/filename/source; React text escaping. Không lấy `message.content` làm fallback answer khi thiếu structured answer.
- Source được tải lại qua IDs và bearer API; bỏ qua URL model/citation tự cung cấp. 401/404/409/410 xóa nội dung cũ; hidden tab clear nội dung và focus lại revalidate. Blob chỉ nhận PDF/text, revoke khi đóng/đổi/logout. PDF dùng viewer trình duyệt và có link tải blob đã xác thực; TXT/MD/DOCX extracted text hiển thị bằng text/pre.
- Sidebar và source panel không lẫn khi đổi route/session; mobile dùng native dialog. Focus-return và Escape có xử lý trong code. CSS có breakpoint 760/1199px, wrap tên dài, reduced motion và touch targets; chưa kiểm chứng pixel/keyboard bằng browser thật.

Code chính: [App](../frontend/src/App.tsx), [AuthProvider](../frontend/src/auth/AuthProvider.tsx), [API client](../frontend/src/api/client.ts), [Documents](../frontend/src/pages/DocumentsPage.tsx), [Chat](../frontend/src/pages/ChatPage.tsx), [useChat](../frontend/src/features/chat/useChat.ts), [SourcePanel](../frontend/src/features/sources/SourcePanel.tsx), [CSS](../frontend/src/index.css).

## Các lựa chọn và giới hạn contract

GET documents/sessions/messages hiện không có cursor. UI không hiển thị nút phân trang/tìm toàn kho giả; tải tối đa100 items, ghi giới hạn danh sách khi chạm cap. “Tất cả tài liệu sẵn sàng” trong query vẫn dùng workspace scope thật của backend, không giới hạn trong100 tài liệu được hiển thị ở bộ chọn.

History API lấy100 tin cũ nhất, nên composer chặn gửi mới khi phiên có từ98 tin; hướng tạo phiên mới trước khi một cặp question/answer vượt cap. Chưa có rename/delete session, cancel query hoặc revoke-token API. Đăng xuất xóa tab state; token server vẫn có TTL. Không thêm các chức năng backend này ngoài phạm vi.

Abort network không hủy query server. Pending payload giữ `client_request_id`, câu hỏi, document IDs và optional run_id trong sessionStorage theo user/session để kiểm tra lại cùng thao tác, tránh UUID mới/generate trùng. Snapshot không có evidence/answer/source text; câu hỏi do người dùng nhập vẫn có thể chứa dữ liệu nhạy cảm. Khôi phục chỉ chấp nhận snapshot dưới10phút; key được xóa khi terminal/logout/expiry hoặc khi đọc snapshot đã quá hạn. Đây không phải bảo đảm background secure erase tại đúng phút thứ10. Memory fallback cho phép đổi route trong cùng tab khi storage bị chặn; reload trong chế độ này không bảo toàn pending state.

Khi POST đã trả run_id/running, GET run có polling hữu hạn. Khi network outcome không rõ, UI giữ pending và yêu cầu “Kiểm tra lại truy vấn”, không tự tạo câu hỏi khác. Lỗi terminal cho phép giữ câu hỏi trong composer để người dùng chủ động thử lại. Khi auth revalidation thành công, không unmount cây UI làm mất draft; identity/workspace/role thay đổi thì reset workspace state.

Source PDF viewer/native dialog/focus/aria-live cần browser thật để nghiệm thu. Việc đã có CSS và jsdom test không chứng minh layout hoặc assistive technology behavior.

## Kiểm tra đã chạy

| Kiểm tra | Kết quả và phạm vi |
|---|---|
| Frontend regression | **30 tests, 7 files, 0 failed/skipped**; raw report cuối ghi riêng trong cache |
| TypeScript + Vite build | PASS; JS313,29kB/gzip98,31kB, CSS17,85kB/gzip4,88kB; số đo ở run đã ghi, không phải latency browser |
| ESLint | PASS, không warning/error ở run cuối |
| API transport qua Vite thật | Login/me/documents/sessions cho admin/member đạt; health200, missing source404, member upload403; không upload thành công/tạo chat trong probe |
| Probe cleanup | Xóa đúng2auth tokens tạo bởi smoke theo digest; dev giữ2users,0documents/jobs/sessions/tokens sau probe |
| Browser/visual E2E | **Chưa chạy** — browser access host không khả dụng; không chuyển sang Windows browser bị policy chặn hoặc công cụ vòng tránh |
| Gemini/held-out | Không gọi; không sửa hoặc tái chạy reports lịch sử |

Test coverage tập trung vào hành vi có rủi ro: bearer/multipart/binary boundaries; stale401/lateJSON không ghi đè phiên mới; source410 xóa excerpt, revoke object URL; exact-name delete; file validation/duplicate recovery; member không có write controls; login/logout; tạo session→query→citation→source với fixtures; giữ draft khi focus; phân biệt partial/abstention/technical errors; uncertain retry cùng UUID; navigation stale response; history cap; polling dừng khi terminal; pending run recovery chỉ GET.

Fixture/mock network được ghi nhãn trong `src/test/fixtures.ts`; chỉ tests import chúng. UI runtime không có mock mode, fallback answer hoặc role override. Native dialog APIs/Blob.text được polyfill riêng trong jsdom; không dùng polyfill đó làm bằng chứng focus trap/PDF viewer trên browser.

Lỗi trong lúc kiểm tra được giữ đúng nguyên nhân: typings của mock fetch được sửa; integration test tìm “Trang2” phải scope/đếm vì cả citation và panel đều hiển thị vị trí; jsdom Blob thiếu `.text()` cần polyfill test-only. Không skip test để xanh. Báo cáo lỗi integration đầu ở `.cache/ui-review/app-tests-initial.json`; report cuối `.cache/ui-review/frontend-tests.json`. Kết quả live HTTP ở `.cache/ui-review/live-api-smoke.json`. Artifacts local này được ignore, không thay immutable eval reports.

Lệnh từ `frontend/`:

```powershell
npm.cmd ci
npm.cmd run test
npm.cmd run build
npm.cmd run lint
```

Backend/eval source không đổi; kết quả302backend+91eval từ đợt khôi phục vẫn là baseline riêng, không mô tả là rerun trong đợt UI.

Audit cuối đối chiếu384protected files (backend/eval/scripts và cấu hình hạ tầng) không đổi bytes;455candidate files không chứa3secrets thực của private `.env`. Bundle production không chứa test fixtures/password mẫu;234local document links và Git whitespace đạt. Ba file frontend legacy chỉ bị formatter đổi EOL đã khôi phục đúng hash ban đầu, không refactor nội dung ngoài phạm vi. Kết quả ở `.cache/ui-review/integrity-final.json`.

## Dependencies và tài nguyên

Thêm pin `lucide-react@1.68.0`, `vitest@4.1.11`, `jsdom@26.1.0`, Testing Library React16.3.0/user-event14.6.1; giữ Vite6.4.5 đã resolve và stack cũ. Chỉ import icon cần dùng. [Lucide React](https://lucide.dev/guide/react) xác nhận individual/tree-shakable components; [Testing Library](https://testing-library.com/docs/react-testing-library/intro/) dùng queries theo nhãn/DOM thay implementation internals.

Đã thử Vitest3 để giữ compatibility ban đầu, nhưng npm audit chỉ ra critical ở tinypool. Chuyển sang4.1.11 sau kiểm tra registry metadata cho thấy hỗ trợ Node24 và Vite6 hiện có; audit cuối **0critical/0high,9moderate**. `npm audit --omit=dev` ghi **0 vulnerabilities ở production dependencies**. Bảy moderate thuộc chuỗi ESLint/minimatch có sẵn, hai moderate thuộc test dependency Vitest/mocker; chưa force-upgrade sang major5/Vite mới vì nằm ngoài mục tiêu UI và cần đánh giá tương thích riêng. Chỉ chạy `vitest run`, không mở test/UI server ra mạng. Raw audits ở `.cache/ui-review/npm-audit*.json`; không tuyên bố toàn bộ dependency graph sạch vulnerabilities.

## Chạy bản local và việc còn lại

Bản dev tại **http://127.0.0.1:5173/**, API127.0.0.1:8000, DB/Qdrant loopback theo Compose; worker chạy từ `backend/` cùng storage profile. Vite proxy trỏ127.0.0.1 để không phụ thuộc IPv6 resolution của localhost. Dùng demo.admin/demo.member với mật khẩu riêng trong `.env`; không đưa credentials vào chat hoặc bundle.

API của phiên kiểm thử được khởi động với LLM_API_KEY rỗng và free-tier/quota flagsfalse **chỉ trong process**, không sửa `.env`. Vì vậy người dùng có thể xem UI, auth, upload/source/lifecycle local, còn generation có evidence sẽ báo model unavailable cho đến đợt chạy Gemini được xác nhận/quota được kiểm tra. Không mô tả test fixtures là câu trả lời thật trong sản phẩm.

Để tự chạy lại bằng terminal riêng: `backend/.venv/Scripts/python.exe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000` từ backend; worker `python -B -m app.worker` cùng cwd; frontend `npm.cmd run dev -- --host 127.0.0.1 --port 5173`. Cấu hình chặn Gemini trong đợt này phải được giữ khi chỉ kiểm tra UI. Không chạy worker cùng DB queue với tests/eval.

**Còn lại trước đóng Bước10:** browser E2E upload→ready→query→source→delete→revisit với hai roles; visual QA các kích thước và native focus/keyboard; kiểm tra login expiry/navigation/reload trên browser thật; human review thiết kế thực tế. Model thật/free-tier gate là đợt riêng nếu cần. Bước11held-out/final eval và Bước12packaging chưa bắt đầu.

## Đợt polish giao diện 06/11/2026

Người dùng xác nhận đợt này. Mục tiêu là giao diện đủ đẹp để quay video demo cho hồ sơ AI Builder Residency của VNG (hạn 15/11). Đợt này không đổi backend/API contract, không gọi Gemini và không thêm dependency npm. Font Be Vietnam Pro được tải qua Google Fonts trong `index.html`. Lý do và đánh đổi ghi ở [KNOWLEDGE K-082](../KNOWLEDGE.md).

- **Login:** bố cục hai cột. Cột trái giới thiệu ba điểm khác biệt: trích dẫn nguồn, biết abstain, đúng quyền/xóa là ngừng dùng. Dưới 960px chỉ còn form.
- **Shell:** logo, nav có icon, phiên gần đây cắt dòng bằng ellipsis, avatar, header và sidebar sticky.
- **Chat:**
  - Màn hình trống có câu hỏi gợi ý lấy từ tập dev; bấm vào chỉ điền ô nhập.
  - Bubble người dùng nằm bên phải; câu trả lời là một thẻ.
  - Citation là số nhỏ, rê chuột hoặc focus để xem trước đoạn trích. Nguồn tham chiếu hiển thị dạng thẻ.
  - Badge "Có nguồn dẫn"/"Trả lời một phần" lấy từ `answer_status`; khối abstention có giao diện riêng.
  - Chỉ báo chờ trung thực, không giả stage.
  - Composer bo tròn, nút gửi dạng icon, bộ chọn phạm vi dạng chip mở lên trên.
- **Documents:** 4 thẻ đếm, badge loại file, badge trạng thái có chấm màu, thanh vị trí stage ingest lấy từ `job.stage` thật, nút có icon.
- **Source panel/dialog:** icon file, chip vị trí, khung trích dẫn được làm nổi bật, nút đóng dạng icon. Upload dùng vùng kéo thả lớn.

**Kiểm tra:**
- `npm.cmd run lint` và `npm.cmd run build` đạt.
- `npm.cmd run test`: **34 passed / 7 files**, gồm 4 test mới.
- Ảnh Login chụp bằng Edge headless 1440×900 qua `vite preview`, đã tắt server sau khi chụp.
- **Chưa** kiểm tra bằng mắt các trang Chat/Documents/Source với dữ liệu thật, vì DB/Qdrant/API không chạy và việc bật dịch vụ nằm ngoài phạm vi đợt này. Browser E2E và visual-keyboard QA (mục 5–6) vẫn còn mở; tiến độ giữ 83,4%.

## Chạy UI với dữ liệu thật 06/11/2026

Người dùng xác nhận đợt này ("Thực hiện đi").

**Dịch vụ:**
- DB/Qdrant bật bằng Compose. Alembic head là `20261103_rag04`, không cần migrate.
- API (`127.0.0.1:8000`) và worker chạy trên host từ `backend/` với `LLM_API_KEY` rỗng, cờ free-tier/quota false, HF/Transformers offline, chỉ trong process. `.env` không đổi.
- Vite dev chạy ở `127.0.0.1:5173`.

**Dữ liệu ghi vào DB dev:**
- 10 tài liệu corpus giả lập (`eval/datasets/corpus`) upload bằng `demo.admin`; cả 10 đều `ready`.
- 1 phiên chat với một truy vấn kết thúc **503**, vì model bị chặn.
- Các token probe được logout sau mỗi lần chụp.
- Không xóa tài liệu nào; hộp thoại xóa chỉ được mở để chụp.

**Chụp màn hình:** dùng Edge headless qua DevTools Protocol, token lấy qua API và không in ra. Ảnh lưu ở `.cache/ui-review/screens-20261106/` (Git ignore). Các màn hình đã chụp:
- Login (desktop và mobile)
- Documents (desktop và mobile)
- Source panel của file TXT
- Hộp thoại upload và xóa
- Chat trống, đang xử lý, phiên cần kiểm tra lại, lỗi 503
- Chat và menu điều hướng trên mobile 390px

**Lỗi tìm thấy và đã sửa** (chi tiết ở [KNOWLEDGE K-083](../KNOWLEDGE.md)):
1. Mọi dialog tự đóng ngay trong bản dev, do StrictMode kết hợp sự kiện `close` được đưa vào hàng đợi. Sửa ở `Dialog.tsx`, thêm `Dialog.test.tsx`.
2. Dialog không căn giữa, do Tailwind preflight. Sửa bằng `margin: auto`.

Ngoài ra giảm khoảng trống trên màn chat trống ở mobile, để câu gợi ý thứ 4 không bị composer che.

**Kết quả:** 36 tests / 8 files, lint và build đạt. Log API có 0 request tới Gemini.

**Còn mở:**
- Ảnh câu trả lời thật (citation, hover, thẻ nguồn, abstention) cần một đợt có gọi Gemini, sau khi kiểm tra quota.
- Luồng E2E đầy đủ (delete → hỏi lại → source/history) với hai role chưa chạy hết.
- Bước 10 mục 5–6 chưa đóng; tiến độ giữ 83,4%.
