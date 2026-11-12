# Browser E2E — lượt thử lại có chung ngân sách

**Trạng thái cập nhật 11/11/2026:** hoàn tất luồng browser E2E và QA chức năng Bước10 trên Chrome. Harness retry-01 đã dừng/xuất capture/cleanup; URL8012 không còn phục vụ sau đợt test. Preview5173 là màn hình riêng. Final human-quality/held-out vẫn pending.

## Phạm vi và bằng chứng

Người dùng xác nhận “Thực hiện đi” cho khả năng khởi động lại harness, tests, tài liệu và E2E trên UI hiện có. Chỉ sửa [harness](../eval/browser_e2e.py) và [tests](../eval/tests/test_browser_e2e.py); không đổi UI source, API production, `.env`, dependencies hoặc tạo ngân sách model mới. Tổng trần của **cả lượt cũ và retry** vẫn8generateContent/28countTokens,0USD; chi phí hóa đơn chưa được xác minh.

`--serve --retry-unused` chỉ cho một đường dẫn cố định `.cache/browser-e2e-20261110/retry-01`, exclusive create. Điều kiện: lượt cũ đã cleanup/finish, không API/worker/native events, ledger thực0 reservations/0runtime bindings và khớp snapshot, grant đúng scope/caps, frozen archive verify, bundle UI khớp hashes. Config/corpus/questions của retry phải giống lượt đầu. Protocol mới freeze source hiện tại; protocol/archive/report/finish cũ được giữ nguyên. Không báo protocol cũ còn khớp workspace sau khi sửa harness.

`RetryLedger` reserve ledger gốc trước rồi ledger con trước mọi provider call. Ledger gốc pin hash grant retry bằng runtime_binding, nên không thể dùng lại plan runtime lượt đầu hoặc thay grant retry. Hai file không có transaction chung: nếu file con lỗi sau khi file gốc đã ghi, reservation gốc vẫn tính; đây là đánh đổi fail-closed, có thể mất một phần allowance nhưng không được refund để thử lại. Không hỗ trợ resume sau khi có query/runtime binding hoặc reset attempt đã tạo. Không mở cờ tổng quát để đổi scope/caps.

**Kiểm chứng:**119selectedtests đạt,1warning Starlette/httpx baseline; Ruff check/format2files đạt. Lượt test đầu sai tên test provider, lượt kế thiếu thư mục cha basetemp; sau đó8negative tests lỗi do dùng hàm JSON exclusive-create để sửa fixture. Đã sửa cách dựng fixture, giữ nguyên guard; lượt cuối119pass. Logs `.cache/browser-retry-validation-20261110/regression-pass.txt`. Tests dùng corpus tạm/network bị chặn; không thay human-quality hoặc browser acceptance.

Preflight `--retry-unused` đạt, không model calls. Harness được khởi động ngoài sandbox để truy cập storage và phục vụ loopback theo scope được duyệt. Status probe xác nhận documents/jobs/events rỗng, ledger con và tổng cùng0/0. Archive retry80files và3UIbundlefiles đã verify, archive gốc cũng verify. Artifacts mới ở thư mục retry-01; logs/probes ở `.cache/browser-retry-validation-20261110/`.

## Kết quả thực thi Chrome ngày 11/11

Native Computer Use đã điều khiển được Chrome sau khi chọn đúng cửa sổ, Raise và quan sát lại URL; browser access host vẫn unavailable. Có các lần AX chậm hơn UI, screenshot trả cửa sổ khác, geometry unavailable/window changed và một lần báo user input: đã quan sát lại binding/state trước khi tiếp tục, không dùng tọa độ từ ảnh sai. AX click input file chỉ focus; coordinate click trên đúng screenshot mở được native Open dialog. Không bypass URL guard, CDP hoặc browser console; không dùng API-only thay browser thao tác.

| Kiểm tra thực tế | Kết quả |
|---|---|
| Login admin → Tài liệu → native file picker → upload | POSTupload202, đúng SHA fixture; worker production parse/chunk/E5/upsert/publish1chunk, job hoàn tất lần1 |
| Admin answer/citation | grounded,2claims30ngày +hóa đơn/xác nhận quản lý; citationE1 mở đúng policy.txt/Dòng1 |
| Admin câu nghỉ phép | insufficient_evidence, claims/citations rỗng; UI không đưa số ngày |
| Logout/login member → Documents | Chỉ có Xem; không Tải/Xóa. Đây là UI affordance, không phải phát sinh POST/DELETE403 từ browser |
| Member answer/citation/abstention | Hai câu đúng nhánh, citation mở được cùng đoạn nguồn; không nhìn thấy session riêng của admin |
| Admin xóa trong cửa sổ Chrome ẩn danh riêng | Nhập đúng policy.txt trong dialog; DELETE202, documentdeleted, cleanup jobcompleted |
| Member giữ panel nguồn mở xuyên lúc admin xóa | Khi trở lại cửa sổ, nguồn revalidate410; UI báo “Nguồn không còn khả dụng”, nội dung cũ ẩn |
| History cả hai role | Nội dung phụ thuộc nguồn bị ẩn; citation cũ không còn hiển thị. Kể cả abstention trước xóa cũng redacted vì actual final context chứa nguồn đó |
| Hai câu sau xóa | insufficient_evidence,0hits/0final_context,0provider calls; UI báo chưa có tài liệu sẵn sàng |
| Keyboard/navigation/reload | Shift+Tab tới citation có focus ring/preview, Enter mở nguồn; Escape đóng dialog; Shift+Enter không gửi; bỏ newline rồi Enter gửi đúng câu; chat mới/sidebar session/reload không tạo query trùng |
| Token expiry | Chỉ fixture tokens của admin trong copilot_browser_test được đặt expires_at=created_at+1s (constraint vẫn hợp lệ). Reload→/auth/me401→login và thông báo phiên hết hạn. Không chờ TTL thực, không đổi auth config/production data |

Sáu queryPOST200, không technical error. **4generateContent +12countTokens**,16nativeHTTP200; hai ledgers cùng số, hai batches sau xóa0/0; không repair/retry/fallback. Đây là sáu câu tổng hợp trên một document/chunk, không ước lượng accuracy thực tế hoặc hoàn tất human review. Metrics human reviewed0/6, các human-quality scoresnull. Captured answer latency (bao gồm retrieval, không bao gồm upload): p50=9984.327ms, nearest-rankp95=max17478.208ms; hai câu sau xóa171.114/215.466ms. Ingestion total-before-publish88006.215ms, phần embedding84355.479ms gồm cold load/inference; không coi đó là warm query latency.

Protocol retry `5ee01925b6d08b93d167f6f84e4803ddf5bddc25bf7770058d69c2782ab980f6`, capture `52be51cb14e29d305f4bf99cd42f158a8c6c8dd68540efe2a60a0d56cd061470`. Capture origincaptured_api/native_gemini, không auth override. Source/UI archives verified trước và sau run. Capture/execution/replay/metrics/human worksheet ở retry-01; original summary0/0 là snapshot của lượt đầu, còn ledger gốc hiện4/12 — không viết lại lịch sử để giả như lượt đầu đã chạy.

**Cleanup:** finish sentinel mới riêng retry-01; summarycleanup_completed=true. Probe độc lập: head20261103_rag04,12bảng fixture0rows, Qdrant0final_collections, scoped canonical storage0files. Không xóa archive/ledger/capture, không dọn dữ liệu dev. Shell session khởi chạy server trả exit1 dù log không có Python traceback và artifacts capture/evaluation/cleanup đều hoàn tất; không ghi rằng process exit0. Kết luận chức năng dựa trên browser, HTTP/capture và probe độc lập. Audit helper lần đầu áp assertion “không GETjobs giữa query đầu và delete” quá rộng vì có lượt mở lại Documents hợp lệ; thu hẹp vào đoạn admin đã rời Documents→chat, trước login member. Lần kế đọc worksheet list nhầm dict; sửa helper đọc metrics human và giữ logs lỗi. Audit cuối ở `.cache/browser-retry-validation-20261110/audit-final.txt` là bằng chứng kiểm tra hoàn tất.

## Checklist đã thực hiện

Chỉ dùng dữ liệu tổng hợp/tài khoản disposable của harness này. Không upload tài liệu riêng. Mỗi câu dưới đây gửi **một lần**, giữ nguyên chữ, không dùng câu gợi ý khác hoặc đổi bộ lọc tài liệu. Nếu lỗi, báo lại trước khi tạo request mới; mỗi case chỉ cho một client_request_id mới.

1. Mở Chrome tại **http://127.0.0.1:8012/login**, đăng nhập `e2e.admin`, mật khẩu `Disposable-browser-E2E-20261110!`. Không lưu mật khẩu vào browser.
2. Vào Tài liệu → Tải tài liệu, chọn `<repo>/.cache/browser-e2e-20261110/retry-01/data/policy.txt`. Chờ trạng thái Sẵn sàng (lần tải E5 cache đầu có thể mất thời gian). Mở Xem để kiểm tra nguồn, đóng panel bằng bàn phím nếu được.
3. Vào Hỏi đáp, để phạm vi mặc định tất cả tài liệu. Gửi `Thời hạn nộp đề nghị hoàn ứng là bao lâu và cần giấy tờ gì?`. Kiểm tra30ngày, hóa đơn và xác nhận quản lý; mở citation và đối chiếu đoạn nguồn.
4. Gửi `Công ty quy định bao nhiêu ngày nghỉ phép năm cho mỗi nhân viên?`. Mong đợi chưa đủ bằng chứng, không tự đưa số ngày. Giữ lại URL cuộc trò chuyện admin để mở lại sau xóa.
5. Đăng xuất, đăng nhập `e2e.member` với cùng mật khẩu. Vào Tài liệu: kiểm tra không có nút Tải/Xóa. Trong Hỏi đáp gửi lần lượt `Tôi kết thúc công tác thì có bao nhiêu ngày nộp hoàn ứng, hồ sơ gồm gì?` và `Mỗi năm nhân viên được nghỉ phép bao nhiêu ngày theo tài liệu?`. Kiểm tra answer/citation và abstention như trên; giữ URL cuộc trò chuyện member.
6. Đăng xuất rồi đăng nhập admin. Xóa đúng `policy.txt` disposable trong Tài liệu. Mở lại chat/nguồn cũ sau refresh: nội dung phụ thuộc nguồn phải ẩn hoặc báo nguồn không khả dụng. Gửi `Sau khi nguồn bị xóa, hãy cho biết lại thời hạn hoàn ứng.`; mong đợi không có evidence, không model call.
7. Đăng nhập member, refresh chat cũ/nguồn cũ rồi gửi `Nguồn vừa xóa còn cho biết tôi cần hồ sơ gì để hoàn ứng không?`; mong đợi không evidence, không model call. Kiểm tra Tab/Shift+Tab, Enter gửi/Shift+Enter xuống dòng, Escape panel/dialog, refresh và điều hướng mà không vô tình submit lại câu đã chạy.
8. Báo các bước đã thực hiện và lỗi nhìn thấy; chưa tự coi human review/AT-R23 pass. Agent sẽ đối chiếu capture, actual native HTTP/ledger, source/history và cleanup sau khi kết thúc. Nếu không thao tác được, giữ trạng thái pending; API-only không thay browser evidence.

**Tiến độ:87,3% /100%.** Bước10 ghi nhận6/6: `(77,5+12)/102,5×100`. AT-R23 có bằng chứng chức năng UI/source410/auth401/empty/loading/AI label; không tự đánh dấu human-quality hoặc final/held-out/release pass. Bước11–12 vẫn0% trong trọng số; không tự triển khai đợt tiếp theo.
