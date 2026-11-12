# Kế hoạch UI Bước 10 — bản đề xuất để duyệt

Ngày: 05/11/2026 · Phiên bản: 0.2 · Trạng thái: **người dùng đã xác nhận code UI; bản triển khai chờ nghiệm thu trực quan**.

Đợt đầu tạo tài liệu và [mockup tương tác](mockups/step10-ui.html). Sau đó người dùng xác nhận “bắt đầu code UI, thực hiện đi” để triển khai theo kế hoạch này. [Report triển khai](ui-step10-implementation.md) ghi code, dependencies, kết quả kiểm chứng và phần chưa nghiệm thu; không đổi backend contract hoặc gọi Gemini trong đợt UI.

Nguồn contract: [spec mục 11, 15.4](../SME_Knowledge_Copilot_RAG_Specification.md), [PLAN Bước 10](../PLAN.md#bước-10--ui-và-một-luồng-end-to-end-hoàn-chỉnh), [quy tắc workspace](../AGENTS.md). Môi trường đã khôi phục theo [runbook 05/11](workspace-restoration-20261105.md).

## 1. Tiêu chí riêng của người dùng

Các tiêu chí này là yêu cầu thiết kế cần giữ trong mọi đợt triển khai UI:

| Mã | Yêu cầu | Cách kiểm tra khi duyệt |
|---|---|---|
| UX-01 | Sạch, dễ dùng, hướng doanh nghiệp/văn phòng | Mỗi màn hình có mục đích rõ; thao tác chính dễ tìm; không chèn dashboard/trang trí làm loãng nội dung |
| UX-02 | Icon vừa phải, chỉ dùng khi cần | Điều hướng và thao tác có nhãn chữ; icon hỗ trợ nhận biết, không lặp icon ở mọi dòng/tiêu đề |
| UX-03 | Icon tiêu chuẩn, không màu mè | Một bộ Lucide, outline đơn sắc/currentColor, cỡ 16–18px; không emoji, icon minh họa lớn hoặc nhiều bộ trộn lẫn |
| UX-04 | Màu đơn giản, hài hòa | Một accent navy; nền/trang/bảng trung tính; màu trạng thái chỉ dùng vùng nhỏ và có nhãn chữ |
| UX-05 | Hiệu ứng đủ nhận biết | Hover/focus, trạng thái đang xử lý, panel/dialog xuất hiện nhẹ; không animation trang trí, confetti, gradient động hoặc typing giả |
| UX-06 | Tập trung vào đọc và làm việc | Câu trả lời và nguồn dễ đối chiếu; bảng tài liệu quét nhanh; không giấu thao tác thiết yếu sau hover |

## 2. Hệ thiết kế đề xuất

P0 ưu tiên **light theme**. Chưa làm theme switcher; có thể xem lại nếu người dùng cần dark mode sau khi duyệt baseline.

| Token/thuộc tính | Giá trị đề xuất |
|---|---|
| Nền chính / nền phụ | `#FFFFFF` / `#F6F7F9` |
| Chữ chính / chữ phụ | `#202B3B` / `#5D6979` |
| Viền | `#DEE3E9`, 1px; không kẻ dọc dày trong bảng |
| Accent / hover | `#254564` / `#1C3751` |
| Thành công | Chữ `#276047`, nền `#EDF5F0`; luôn có nhãn |
| Cảnh báo | Chữ `#7A5618`, nền `#FBF5E9`; luôn có lý do/hành động |
| Lỗi | Chữ `#9B3D3D`, nền `#FAEEEE`; không dùng đỏ cho nội dung bình thường |
| Font | `Segoe UI`, system-ui, sans-serif; không tải font ngoài |
| Chữ | Body 14–16px; nhãn phụ 12–13px; tiêu đề trang 22–24px; font-weight 400/500/600 |
| Nhịp khoảng cách | 4/8/12/16/24/32px; margin nội dung desktop 24–32px |
| Control | Cao 36–40px desktop, hit target ít nhất 44px trên touch |
| Bo góc | 6–8px; shadow chỉ dùng cho lớp nổi, không mọi khối |
| Motion | 120–180ms cho background/opacity/panel; tắt chuyển động khi prefers-reduced-motion |

Nút chính dùng navy đặc, nút phụ viền mảnh hoặc nhãn chữ. Chỉ hành động xóa dùng màu destructive. Không dùng màu để tạo “cảm giác AI”, không phần trăm confidence từ cosine score.

Mockup cho phép chỉnh thử mật độ dòng bảng và độ bo góc bằng công cụ duyệt nếu host hỗ trợ; đó là tùy chọn so sánh thiết kế, không phải settings của sản phẩm.

## 3. Bố cục và điều hướng

- Header khoảng 56–64px: tên sản phẩm, workspace, tài khoản. Không để tên service/model, quota hoặc thông số triển khai chiếm giao diện người dùng.
- Sidebar desktop khoảng 200–216px: **Hỏi đáp**, **Tài liệu**. Trong Hỏi đáp có nút cuộc trò chuyện mới và danh sách phiên gần đây. Không đưa navigation Operations cũ vào demo RAG.
- Vùng đọc chat tối đa khoảng 760–820px khi không mở nguồn. Tránh mỗi câu trả lời thành một thẻ nổi có shadow.
- Source panel bên phải khoảng 320–360px khi đủ chỗ; ở chiều rộng hẹp hơn dùng overlay có nền che và focus management. Không ép ba cột chật.
- Ở tablet/mobile: điều hướng rút gọn, sidebar chuyển sang drawer; nội dung chính một cột. Bảng tài liệu đổi thành từng mục có nhãn, giữ tên/trạng thái/thao tác đọc được.
- Giữ đường đi rõ: `/login`, `/chat`, `/chat/:sessionId`, `/documents`. Source là panel gắn với màn hình đang xem, không bắt buộc route riêng.

Mockup có thanh điều khiển duyệt ở ngoài product chrome: chuyển màn hình, đổi admin/member, chọn trạng thái. Đây không phải UI sẽ đưa vào sản phẩm.

## 4. Thiết kế bốn màn hình

### Đăng nhập

Form trung tâm, tên đăng nhập/mật khẩu, một nút Đăng nhập. Không banner minh họa, thông điệp quảng cáo hoặc chọn role. Lỗi thông tin đăng nhập là thông báo chung; 401 do hết hạn có thông báo riêng và hướng quay lại. Không tự điền mật khẩu thật.

### Tài liệu

Tiêu đề, mô tả ngắn, nút **Tải tài liệu** cho admin. Bảng gồm tên/định dạng, trạng thái, thời điểm tải, thao tác. Có loading/empty/error riêng. Trạng thái ready có warning vẫn dùng được, nhưng hiển thị rõ phần tài liệu chưa đọc đủ. Scan/needs_ocr hướng dẫn dùng bản có text, không có nút retry giả.

Upload là panel/dialog gọn, cho chọn hoặc thả file; backend hiện nhận một file/request. Hỗ trợ PDF text, DOCX, TXT/MD trong giới hạn server. Nếu tải nhiều file trong một lựa chọn được duyệt thì xử lý tuần tự, kết quả riêng từng file, không giả batch API. Chỉ hiển thị progress bytes nếu đo thật bằng transport có progress; nếu dùng fetch thì hiển thị trạng thái bất định.

Polling job từ 2 giây, backoff tối đa 10 giây, dừng khi terminal/unmount/logout. Khi chờ quá lâu, báo “Tác vụ vẫn đang xử lý” và cho kiểm tra lại; không tự đổi job thành failed. Thử lại ingestion/cleanup chỉ khi server cho phép. Delete dialog yêu cầu nhập tên tài liệu; sau 202 hiển thị đang xóa/dọn dẹp, không báo đã xóa vật lý hoàn tất. Member không có write controls; 403 vẫn được xử lý từ server.

### Hỏi đáp

Phiên gần đây, câu hỏi độc lập, bộ chọn tài liệu ready, composer có label rõ. Enter gửi, Shift+Enter xuống dòng. Chỉ gửi một câu/phiên đang xử lý; giữ draft khi lỗi. Khi request đang chạy hiển thị **Đang xử lý câu hỏi…**, không streaming/typing giả hoặc khẳng định stage nội bộ chưa có dữ liệu.

Render structured claims, citations cạnh từng claim và phần nguồn riêng. Nhãn **AI-generated** hiện trong mỗi câu trả lời. Các trạng thái:

| State | Trình bày |
|---|---|
| grounded | Claims và evidence IDs do backend trả; không tự tạo nguồn |
| partial/conflict | Phần đã có nguồn; phần còn thiếu/hạn chế riêng; cảnh báo mâu thuẫn khi có |
| insufficient_evidence | Thông báo thiếu bằng chứng và gợi ý bổ sung tài liệu/câu hỏi; không citation rỗng |
| model/vector/DB lỗi | Error có hành động phù hợp; không đổi thành “không có câu trả lời” |
| source_changed/source_unavailable | Che nội dung bị ảnh hưởng, đóng/clear nguồn; cho hỏi lại trên nguồn hợp lệ |

Session chỉ tổ chức lịch sử. P0 không dùng câu trả lời trước làm evidence, không hứa hiểu câu nối tiếp mơ hồ. Dòng nhắc ngắn dưới composer: “Mỗi câu hỏi cần đầy đủ ngữ cảnh.” Không bắt người dùng đọc chi tiết pipeline.

### Source Preview

Mở từ `[E1]` hoặc nguồn được chọn. Header có filename/vị trí và nút **Đóng**. Nội dung gồm excerpt, vị trí cụ thể (trang PDF, block DOCX, dòng TXT/MD) và thao tác mở bản nguồn. Không giả số trang DOCX. Không tải/sanitize Markdown thành HTML tự do; text tài liệu là text.

PDF/TXT/DOCX source fetch có Authorization, xử lý response binary riêng, tạo object URL khi cần; không nhét token vào URL hoặc mở endpoint bearer trực tiếp bằng link không xác thực. Revoke object URL khi đóng/đổi nguồn/logout. 401 yêu cầu đăng nhập lại; 410 clear nội dung cũ ngay; 404 không tiết lộ metadata ngoài scope. Khi tab được focus trở lại hoặc sau thao tác delete trong app, revalidate nguồn/history liên quan; không hứa thu hồi bytes đã tải trước delete.

## 5. Mapping API và giới hạn đã thấy trong source

| UI | API hiện có | Ghi chú triển khai |
|---|---|---|
| Login/me | POST `/auth/login`, GET `/auth/me` | Role từ server, không từ selector |
| Documents | GET/POST `/documents`, GET `/documents/{id}` | GET có `limit` tối đa 100, chưa cursor/status/search server-side |
| Jobs/retry | GET `/jobs/{id}`, POST `/documents/{id}/retry`, POST `/jobs/{id}/retry` | Phân biệt ingestion và cleanup |
| Delete | DELETE `/documents/{id}` | 202 đang dọn, 200 đã deleted; lặp idempotent |
| Sessions/history | GET/POST `/chat/sessions`, GET `/chat/sessions/{id}/messages` | Owner scope; chưa rename/delete session API |
| Query/recover | POST `/chat/query`, GET `/chat/runs/{id}` | Non-streaming; client_request_id; lỗi query_in_progress trả run_id |
| Source | GET `/documents/{id}/chunks/{chunkId}`, GET `/documents/{id}/content` | JSON envelope và binary phải có đường đọc riêng |

Đã đối chiếu [resources](../backend/app/api/resources.py), [identity](../backend/app/api/identity.py), [uploads](../backend/app/api/uploads.py), [chat](../backend/app/api/chat.py), [search/source](../backend/app/api/search.py), [deletion](../backend/app/api/deletion.py).

**Không giấu khoảng trống contract:**

1. Không vẽ phân trang/tìm toàn kho như đã có. Nếu thêm bộ lọc local, phải ghi “trong danh sách đã tải”. Đề xuất P0 tải tối đa 100 items, thông báo giới hạn nếu chạm cap. Cần phân trang thật thì đề xuất đợt backend riêng.
2. History hiện trả các message cũ nhất trước, tối đa 100; chưa thể hứa tải toàn lịch sử dài. Khi phiên chạm giới hạn phải báo và hướng tạo phiên mới; muốn history đầy đủ cần mở rộng backend riêng. Không chỉ append local rồi giả reload không mất dữ liệu.
3. Chưa có logout/revoke endpoint: UI chỉ kết thúc phiên ở trình duyệt, không tuyên bố thu hồi token server. Đề xuất sessionStorage theo tab để giữ reload; xóa khi logout/expiry. Đánh đổi XSS phải được kiểm soát bằng text rendering; memory-only an toàn hơn về persistence nhưng buộc login lại sau reload, HttpOnly cookie cần đổi backend.
4. Abort fetch không hủy công việc trên server. Khi network timeout không gửi lại mù với UUID mới; dùng cùng client_request_id để xác định/replay, hoặc theo run_id do server cung cấp. Chưa có cancel query API nên không vẽ nút “Dừng tạo câu trả lời”.
5. Job không có reliable percentage ở mọi stage; trình bày stage/counters nếu có, không tự tính phần trăm hoàn tất từ thời gian chờ.

## 6. Kế hoạch code sau khi thiết kế được duyệt

Phân chia công việc thiết kế ban đầu dưới đây; đường dẫn source thực tế và các phần còn pending xem report triển khai:

| Đợt | Thành phần/file dự kiến | Kết quả và kiểm tra |
|---|---|---|
| UI-A | `frontend/src/index.css`, `App.tsx`, `components/layout/AppShell.tsx`, `components/ui/*` | Tokens, controls, responsive shell; kiểm tra bàn phím/contrast/overflow |
| UI-B | `api/client.ts`, `api/types.ts`, `api/auth.ts`, `auth/AuthProvider.tsx`, `pages/LoginPage.tsx` | Bearer JSON/binary, expiry, route guard, local sign-out; kiểm tra 401/role/reload |
| UI-C | `api/documents.ts`, `pages/DocumentsPage.tsx`, `features/documents/*`, `hooks/useJobPolling.ts` | Upload/list/status/retry/delete; kiểm tra admin/member và lifecycle |
| UI-D | `api/chat.ts`, `pages/ChatPage.tsx`, `features/chat/*`, `hooks/useQueryRun.ts` | Sessions/composer/structured answer/citations/recovery; đổi phiên không lẫn dữ liệu |
| UI-E | `features/sources/SourcePanel.tsx`, source API helpers | Authorized source JSON/binary, 410 clearing, PDF page/text location, object URL lifecycle |
| UI-F | Browser E2E, tài liệu và KNOWLEDGE; test files/config tối thiểu nếu cần | Full P0 flow, frontend lint/build, keyboard/responsive; báo pass/fail/skipped thật |

Giữ React/TypeScript/Vite/Tailwind/React Router hiện có. Không thêm UI kit nặng hoặc state framework chỉ để dựng màn hình. Đề xuất một dependency icon nhỏ `lucide-react`, import từng icon; chỉ cài/pin khi đợt code UI có phạm vi dependencies được duyệt. Không tự nâng các dependencies cũ trong đợt UI.

API layer chịu envelope/errors/binary; hooks chịu cancellation/polling/idempotency; components chịu presentation. Không biến JSX thành nơi xử lý lifecycle hoặc tự dựng citations. Khi bỏ route Operations khỏi navigation vẫn giữ source legacy ngoài demo, không xóa lịch sử không liên quan.

Mỗi đợt triển khai cần trình bày phạm vi và xác nhận theo AGENTS; duyệt tài liệu này chưa tự cho phép code toàn bộ Bước 10. Nếu cần backend contract mới phải tách đề xuất bổ sung.

## 7. Tiêu chí nghiệm thu khi triển khai

- [ ] Đúng UX-01–06; màu/typography/icon thống nhất, người dùng đọc được tên file dài và nội dung tiếng Việt.
- [ ] Kiểm tra desktop 1440/1280/1024, tablet 768 và mobile 390/320; không tràn ngang toàn trang hoặc chồng controls.
- [ ] Focus dễ thấy; Tab/Enter/Escape hoạt động; panel/dialog giữ focus và trả lại trigger; thông báo động có aria-live phù hợp.
- [ ] Mục tiêu contrast nội bộ: chữ thường 4,5:1, chữ lớn/control/focus 3:1; không tuyên bố đạt chuẩn accessibility chỉ từ một screenshot.
- [ ] Reduced motion hoạt động; không spinner trang trí/animation lặp ngoài loading cần thiết.
- [ ] Admin/member đúng quyền qua API; không chỉ ẩn nút. Hết hạn/logout không giữ nguồn hoặc history nhạy cảm trên UI.
- [ ] Upload → ready → query → citation → source → delete → query/source/history lại được kiểm tra với dữ liệu thật được phép.
- [ ] Polling có giới hạn, dừng khi đổi màn hình/phiên/logout; stale response không ghi đè state mới.
- [ ] Grounded/partial/abstention/technical failure/source unavailable thể hiện riêng; không claim hoặc confidence giả.
- [ ] Không XSS từ filename, source, claim hoặc Markdown; không render HTML tài liệu không tin cậy.
- [ ] Frontend lint/build đạt; browser E2E và các acceptance cases liên quan ghi bằng chứng. Mockup pass không tính là AT-R23 pass.
- [ ] Chưa gọi LLM thật nếu chưa có đợt xác nhận + kiểm tra free tier/quota; có thể kiểm thử UI với fixtures ghi nhãn, không trình bày fixture thành kết quả AI thật.

## 8. Cách duyệt mockup

Mockup dùng dữ liệu giả lập, không gọi API/model, không đọc `.env` và không upload/xóa tài liệu thật. Có thể chuyển Đăng nhập/Tài liệu/Hỏi đáp/Nguồn, đổi admin/member và trạng thái mẫu; mở citation, chọn nguồn, thử composer và xác nhận xóa mẫu.

Người dùng cần duyệt: (1) bố cục sidebar + source panel, (2) palette/navy và độ tương phản, (3) mật độ khoảng cách/chữ, (4) icon ít và có mục đích, (5) trạng thái partial/error/delete. Các lựa chọn đều đang đề xuất; chưa tự đánh dấu human approval.

**Kiểm chứng đợt tài liệu/mockup:** fragment được preview renderer chấp nhận, JavaScript qua `node --check`, file dưới 1 MB và không có fetch/XHR/WebSocket. Source frontend/backend và dependencies chưa thay đổi. Có CSS responsive/reduced-motion và các tương tác mẫu, nhưng chưa xác minh trực quan desktop/mobile hoặc thực thi đầy đủ các tương tác trong browser.

Browser access host không khả dụng. Lần thử kiểm tra bằng trình duyệt Windows bị Computer Use dừng vì chưa hỗ trợ URL policy enforcement cho trình duyệt hiện tại; đã dừng kiểm tra UI, không chuyển sang công cụ tự động khác để vượt giới hạn. Vì vậy screenshot/visual QA, keyboard/focus và runtime interactions vẫn **chưa kiểm chứng**, không coi static checks là browser E2E. Người dùng có thể xem và phản hồi mockup; trước triển khai cần kiểm tra trực quan khi có browser surface được hỗ trợ.

Đợt chỉ tạo mockup giữ tiến độ75,6%; đợt code UI sau đó ghi nhận4/6 đầu việc theo PLAN, hiện **83,4% / 100%**. Việc người dùng xác nhận code không thay thế human acceptance/visual QA; các mục nghiệm thu ở trên chưa tự đánh dấu đạt.
