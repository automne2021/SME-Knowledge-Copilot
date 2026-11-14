# 01 — Spec nội dung corpus v2 (tài liệu giả lập giống thật)

> **Dùng cho:** task 01-T2a, 01-T2b, 01-T2c trong [01-eval-expansion.md](01-eval-expansion.md). Task 01-T3 (draft câu hỏi) dùng lại **fact registry** ở mục 3.
> **Người viết:** Claude (PM), 15/11/2026. **Người thực hiện:** Codex.
> **File này là "bộ nhớ" giữa các phiên Codex.** Mỗi phiên đọc lại toàn bộ file này, cập nhật bảng ở mục 8 cuối mỗi task, không dựa vào trí nhớ của phiên trước.

## 1. Vì sao cần corpus v2

Corpus v1 (`eval/datasets/corpus/`) có 10 file, mỗi file chỉ khoảng 450–830 ký tự chữ. Gần như câu nào cũng mở đầu bằng "Trong bộ dữ liệu mẫu…". Bộ này đủ để kiểm thử pipeline, nhưng không giống tài liệu doanh nghiệp thật:

- Không có văn bản dài với nhiều mục gây nhiễu.
- Không có bảng.
- Không có phiên bản cũ và mới mâu thuẫn nhau.
- Không có mã định danh dày đặc.
- Không có văn phong email hay biên bản.

Vì vậy Recall@5 = 1,0 trên v1 chưa nói được nhiều. Corpus v2 phải đọc như **tài liệu nội bộ thật của một công ty nhỏ**, để:

1. Số đo ở 02 (hybrid), 04 (bảng), 06 (hỏi nối tiếp) và 08 (OCR) có ý nghĩa.
2. Demo và ảnh README thuyết phục hơn: người xem thấy app trả lời trên tài liệu giống tài liệu họ có.

## 2. Công ty hư cấu

Mọi tài liệu thuộc **cùng một công ty** và nhất quán với nhau về tên phòng ban, mã, người ký và ngày tháng.

| Mục | Giá trị |
|---|---|
| Tên | **Công ty Cổ phần Thiết bị Văn phòng Thiên Lam**, tên ngắn "Thiên Lam", mã viết tắt `TL` |
| Ngành | Phân phối, cho thuê và bảo trì máy in, máy photocopy, máy chiếu cho doanh nghiệp |
| Quy mô | Khoảng 85 nhân viên. Trụ sở TP.HCM, chi nhánh Đà Nẵng |
| Địa chỉ | Chỉ ghi dạng hư cấu: "Tầng 5, Tòa nhà Thiên Lam, đường số 12, KDC giả lập, TP.HCM". Không dùng địa chỉ thật |
| Liên hệ | Tổng đài `1800-0000` (giả lập), email dạng `@thienlam.example` |
| Người ký (hư cấu) | Tổng Giám đốc: Lê Hoàng Phúc · Kế toán trưởng: Nguyễn Thị Thu Hà · Trưởng phòng HCNS: Phạm Quốc Bảo · Trưởng kho HCM: Võ Thành Nhân · Trưởng phòng Kỹ thuật dịch vụ: Đặng Minh Tuấn |

**Phòng ban và mã:**

| Mã | Phòng ban |
|---|---|
| `BGĐ` | Ban Giám đốc |
| `HCNS` | Hành chính – Nhân sự |
| `KT` | Kế toán |
| `KD` | Kinh doanh |
| `KTDV` | Kỹ thuật dịch vụ |
| `CSKH` | Chăm sóc khách hàng |
| `KHO` | Kho vận |
| `IT` | Công nghệ thông tin |

**Quy ước mã:**

- **Số hiệu văn bản:** `<số>/<năm>/<loại>-TL`, với loại là `QĐ`, `QC`, `TB`, `QT`, `HD`. Ví dụ `15/2025/QĐ-TL`.
- **Biểu mẫu:** `BM-<phòng>-<số 2 chữ số>`, ví dụ `BM-NS-03`, `BM-KT-02`, `BM-KHO-07`.
- **Mã kho:** `KHO-HCM-01`, `KHO-DN-01`. **Vị trí kệ:** `K<kho>-<dãy><số>-T<tầng>`, ví dụ `K1-A03-T2`. **Khu chờ kiểm định (QC):** `KQ-01`.
- **Mã lỗi thiết bị** (dùng trong SOP kho và FAQ): `E-<nhóm>-<số>`, ví dụ `E-FD-12` là lỗi kéo giấy.

## 3. Fact registry (sự kiện cốt lõi)

Đây là **nguồn sự thật duy nhất**. Mỗi con số hay quy định quan trọng có một mã `F-…`:

- Tài liệu chỉ được nói khác registry ở những chỗ **ghi là bẫy**.
- Trong seed, mỗi block chứa sự kiện phải gắn `facts: ["F-…"]`.
- Codex được **thêm** fact mới (đánh mã tiếp theo, ghi vào bảng này trong cùng commit), nhưng không sửa fact đã có nếu chưa hỏi người dùng.

| Mã | Sự kiện | Tài liệu | Ghi chú / bẫy |
|---|---|---|---|
| F-HR-01 | Phép năm **12 ngày** cho nhân viên chính thức (theo sổ tay 2025) | D01 | Bị F-HR-02 thay thế từ 01/01/2026 |
| F-HR-02 | Phép năm **14 ngày** từ 01/01/2026 | D02 | **Bẫy conflict:** câu trả lời đúng là 14, nên nêu cả việc sổ tay cũ ghi 12 |
| F-HR-03 | Cứ đủ 5 năm thâm niên được cộng thêm 1 ngày phép | D01 | D02 không đổi điều này |
| F-HR-04 | Phép chưa dùng được chuyển tối đa **5 ngày**, dùng trước **31/03** năm sau | D01 | D02 đổi hạn thành **30/06** (từ năm 2026), số ngày vẫn 5 |
| F-HR-05 | Thử việc 60 ngày, lương thử việc bằng 85% lương chính thức | D01 | |
| F-HR-06 | Giờ làm 08:00–17:00, nghỉ trưa 12:00–13:00, thứ Hai đến thứ Sáu | D01 | Chi nhánh Đà Nẵng làm thêm sáng thứ Bảy (08:00–11:30) |
| F-HR-07 | Xin nghỉ phép bằng biểu mẫu `BM-NS-03`, gửi trước ít nhất 3 ngày làm việc | D01 | |
| F-CT-01 | Bảng định mức công tác phí theo **vùng** và **cấp bậc** (xem mục 4, D03) | D03 | **Slice bảng** |
| F-CT-02 | Tạm ứng công tác bằng `BM-KT-02`, nộp trước chuyến đi 2 ngày làm việc; quyết toán trong 5 ngày làm việc sau khi về | D03 | |
| F-CT-03 | Vé máy bay hạng phổ thông; Trưởng phòng trở lên được hạng thương gia nếu chặng bay trên 4 giờ | D03 | |
| F-MH-01 | Ma trận phê duyệt mua hàng: dưới 10 triệu → Trưởng phòng; 10–50 triệu → Trưởng phòng và Kế toán trưởng; trên 50–200 triệu → Tổng Giám đốc; trên 200 triệu → Hội đồng quản trị | D04 | **Slice bảng** |
| F-MH-02 | Biên bản họp **đề xuất** nâng ngưỡng Trưởng phòng lên 15 triệu, giao HCNS dự thảo, **chưa ban hành** | D10 | **Bẫy:** đây là đề xuất, không phải quy định đang áp dụng; ngưỡng hiện hành vẫn là 10 triệu |
| F-MH-03 | Đơn mua từ 20 triệu phải có ít nhất 3 báo giá (`BM-MH-01`) | D05 | |
| F-MH-04 | `BM-MH-01`: Bảng tổng hợp báo giá và phương án lựa chọn; `BM-MH-02`: Phiếu đề nghị mua và trình duyệt; `BM-MH-03`: Biên bản giao nhận, nghiệm thu; `BM-MH-04`: Phiếu chuyển hồ sơ thanh toán | D05 | Bổ sung 01-T2a; cố định ý nghĩa mã cho slice identifier |
| F-KHO-01 | Hàng lỗi phải chuyển vào khu `KQ-01` trong 24 giờ kể từ khi phát hiện | D06 | Slice mã định danh |
| F-KHO-02 | Kiểm kê định kỳ cuối mỗi quý; chênh lệch trên 2% phải lập biên bản `BM-KHO-07` | D06 | |
| F-DV-01 | Hợp đồng bảo trì gói **Tiêu chuẩn**: phản hồi trong 4 giờ làm việc, kỹ thuật viên có mặt trong 24 giờ (nội thành) | D07 | Nằm sâu trong văn bản dài |
| F-DV-02 | Gói **Cao cấp**: phản hồi 2 giờ, có mặt trong 8 giờ | D07 | |
| F-DV-03 | Phạt chậm SLA: 0,5% phí dịch vụ tháng cho mỗi giờ trễ, tối đa 10% | D07 | |
| F-BH-01 | Máy mới bảo hành 12 tháng; linh kiện thay thế bảo hành 3 tháng | D08 | |
| F-BH-02 | Đổi máy mới trong 7 ngày nếu lỗi do nhà sản xuất | D08 | |
| F-BH-03 | Không bảo hành lỗi do dùng mực hoặc linh kiện không chính hãng | D08 | |
| F-CSKH-01 | Tổng đài CSKH hoạt động 07:30–20:00, kể cả thứ Bảy | D09 | |
| F-IT-01 | Mật khẩu đổi mỗi 90 ngày, tối thiểu 12 ký tự, bật MFA cho email | D11 | Email viết **không dấu**, lẫn tiếng Anh |
| F-IT-02 | Truy cập ERP từ ngoài văn phòng phải qua VPN | D11 | |

**Câu không có đáp án (unanswerable)** phải hỏi về chủ đề **gần** với corpus nhưng corpus không nói, ví dụ "phụ cấp gửi xe bao nhiêu?" hay "thưởng Tết năm 2026 mấy tháng lương?". Không được viết những chủ đề đó vào bất kỳ tài liệu nào.

## 4. Danh sách tài liệu

Độ dài quy đổi: 1 trang A4 khoảng 2.500–3.000 ký tự. **Không độn chữ:** tài liệu dài phải dài vì có nhiều điều khoản thật (thủ tục, ngoại lệ, định nghĩa, trách nhiệm), không lặp câu.

| # | File | Định dạng | Độ dài | Nội dung chính | Slice phục vụ | Đợt |
|---|---|---|---|---|---|---|
| D01 | `so_tay_nhan_su_2025.pdf` | PDF text, nhiều trang | 10–12 trang | Tuyển dụng, thử việc, giờ làm, nghỉ phép, chế độ, kỷ luật, nghỉ việc | text, conflict, multi_doc | T2b |
| D02 | `thong_bao_sua_doi_che_do_phep_2026.docx` | DOCX | 1–2 trang | Thông báo `TB` sửa điều khoản phép của D01 | conflict | T2a |
| D03 | `quy_che_cong_tac_phi.docx` | DOCX, **có 2 bảng** | 4–5 trang | Phạm vi, định mức (bảng vùng × cấp bậc: lưu trú, khách sạn, đi lại), tạm ứng, quyết toán | table, identifier | **T2a (tài liệu mẫu)** |
| D04 | `ma_tran_phe_duyet_mua_hang.pdf` | PDF có **bảng kẻ khung** | 2 trang | Ma trận ngưỡng × người duyệt, ghi chú ngoại lệ | table | T2a |
| D05 | `quy_trinh_mua_hang.docx` | DOCX | 3–4 trang | Các bước, biểu mẫu `BM-MH-01..04`, báo giá, nghiệm thu, thanh toán | text, identifier, multi_doc | T2a |
| D06 | `sop_nhap_xuat_kho.pdf` | PDF text, có 1 bảng mã lỗi | 6–8 trang | Nhập, xuất, hàng lỗi, kiểm kê; nhiều mã kho, vị trí, lỗi | identifier, table | T2b |
| D07 | `hop_dong_bao_tri_mau.pdf` | PDF text, nhiều trang | 10–12 trang | Hợp đồng dịch vụ mẫu: định nghĩa, phạm vi, SLA, phạt, bảo mật, chấm dứt, phụ lục | text (nhiễu dài), multi_section | T2b |
| D08 | `chinh_sach_bao_hanh_doi_tra.md` | Markdown, có **bảng** | 2–3 trang | Thời hạn, điều kiện, loại trừ, quy trình gửi bảo hành | table, text | T2b |
| D09 | `faq_cham_soc_khach_hang.md` | Markdown hỏi đáp | 2–3 trang | 15–20 cặp hỏi đáp; một số câu tham chiếu D08 và mã lỗi D06 | text, multi_doc, paraphrase | T2c |
| D10 | `bien_ban_hop_giao_ban_thang_10_2026.docx` | DOCX biên bản | 2 trang | Thành phần, nội dung, **đề xuất** nâng ngưỡng duyệt, việc giao | conflict (bẫy đề xuất) | T2c |
| D11 | `email_it_bao_mat_tai_khoan.txt` | TXT email | 1 trang | Email từ IT viết **không dấu**, lẫn thuật ngữ tiếng Anh (MFA, VPN, phishing) | no_diacritics, text | T2c |
| D12 | `bang_gia_dich_vu_sua_chua_2026.pdf` | PDF **bảng kẻ khung** | 2 trang | Giá công sửa theo nhóm máy, phụ phí ngoài giờ, chiết khấu khách hợp đồng | table | T2c |
| D13 | `bien_ban_ban_giao_thiet_bi_scan.pdf` | PDF **ảnh** (không lớp chữ) | 1 trang | Bàn giao máy kèm số serial | scan (chờ 08) | T2c |
| D14 | `phieu_de_nghi_thanh_toan_scan.pdf` | PDF **ảnh** | 1 trang | Phiếu `BM-KT-04` đã điền tay (mô phỏng) | scan (chờ 08) | T2c |

**Bảng định mức của D03** (F-CT-01; giá trị cố định, Codex không tự đổi):

| Cấp bậc | Lưu trú vùng 1 | Lưu trú vùng 2 | Khách sạn tối đa vùng 1 | Khách sạn tối đa vùng 2 |
|---|---|---|---|---|
| Nhân viên | 300.000 đ/ngày | 220.000 đ/ngày | 900.000 đ/đêm | 650.000 đ/đêm |
| Trưởng nhóm | 350.000 đ/ngày | 260.000 đ/ngày | 1.100.000 đ/đêm | 800.000 đ/đêm |
| Trưởng phòng trở lên | 450.000 đ/ngày | 320.000 đ/ngày | 1.500.000 đ/đêm | 1.000.000 đ/đêm |

Vùng 1 gồm Hà Nội, TP.HCM và Đà Nẵng; vùng 2 là các tỉnh, thành còn lại. Công tác nước ngoài **không** thuộc quy chế này (chỗ dành cho câu unanswerable).

## 5. Văn phong

**Bắt buộc:**

- **Văn bản hành chính** (D01–D05, D07, D10, D13, D14) có bố cục thật:
  - Quốc hiệu và tiêu ngữ.
  - Tên công ty, số hiệu, ngày ban hành, ngày hiệu lực.
  - "Chương / Điều / Khoản".
  - Nơi nhận, chữ ký (tên và chức vụ hư cấu), phụ lục nếu có.
- **SOP và FAQ** có mục đích, phạm vi, định nghĩa, các bước đánh số, trách nhiệm, lịch sử phiên bản.
- **Email D11** có From/To/Subject/Date, lời chào, nội dung gạch đầu dòng và chữ ký. Viết không dấu như người gõ vội; có lỗi chính tả nhẹ nhưng vẫn đọc hiểu.
- **Nhãn giả lập:** mỗi file có đúng **một** dòng "TÀI LIỆU GIẢ LẬP – dùng để kiểm thử SME Knowledge Copilot, không phải quy định của doanh nghiệp thật", đặt ở header/footer (PDF, DOCX) hoặc dòng đầu (MD, TXT). **Không** chèn "trong bộ dữ liệu mẫu" vào từng câu như v1.
- Câu có độ dài khác nhau. Có câu dẫn chiếu chéo, ví dụ "theo Điều 9 Quy chế công tác phí". Có ngoại lệ, ví dụ "trừ trường hợp…".

**Đoạn mẫu chuẩn** (giọng văn để bám theo):

> **Điều 7. Tạm ứng công tác phí**
> 1. Người được cử đi công tác lập Giấy đề nghị tạm ứng theo mẫu `BM-KT-02`, có xác nhận của Trưởng bộ phận, và gửi Phòng Kế toán chậm nhất **02 ngày làm việc** trước ngày khởi hành.
> 2. Mức tạm ứng không vượt quá tổng định mức lưu trú và khách sạn tính theo số ngày công tác dự kiến tại Phụ lục 01. Chi phí đi lại bằng máy bay do Phòng HCNS đặt trực tiếp, không tạm ứng.
> 3. Trường hợp chuyến công tác bị hủy, người tạm ứng hoàn trả toàn bộ số tiền trong vòng 03 ngày làm việc kể từ ngày có quyết định hủy.

**Cấm:**

- Tên, địa chỉ, mã số thuế, logo hoặc thương hiệu của doanh nghiệp thật. Tên người thật nổi tiếng.
- Số CCCD, số tài khoản ngân hàng hoặc số điện thoại có định dạng dùng được. Chỉ dùng chuỗi rõ là giả, ví dụ `0000-xxx`.
- Chép nguyên văn văn bản pháp luật. Được nhắc tên chung chung kiểu "theo quy định của pháp luật lao động hiện hành".
- Độn chữ (lorem ipsum, lặp đoạn) hoặc nội dung không liên quan doanh nghiệp.
- Viết thêm chủ đề dành cho câu unanswerable (mục 3).

## 6. Cách sinh file (tái tạo được)

- **Seed:** `eval/seeds/corpus_v2.json` với `corpus_version: "synthetic-sme-v2"`, `company`, `notice`, `documents[]`. Mỗi document có `document_id` (`D01`…), `file_name`, `format`, `title`, `doc_number`, `effective_date`, `blocks[]`. Kiểu block:
  - `heading` (`level`, `text`)
  - `paragraph` (`text`)
  - `list_item` (`text`, `ordered`)
  - `table` (`header`, `rows`)
  - `page_break`
  - `signature` (`lines`)

  Block nào chứa fact thì có `facts: [...]`.
- **Builder:** `eval/build_corpus_v2.py`, viết mới; không sửa `eval/build_dataset.py` của v1. Ghi ra `eval/datasets/corpus_v2/` và `eval/datasets/corpus_v2_manifest.json` (sha256 từng file, version thư viện).
  - **DOCX:** dùng python-docx; heading dùng style `Heading N`, vì parser lấy ngữ cảnh heading từ style này. Bảng là `doc.add_table` có style `Table Grid`. Ghim timestamp ZIP và core properties như `docx_bytes` của v1.
  - **PDF text:** dùng PyMuPDF với font tiếng Việt truyền qua tham số, như v1. Text phải tự xuống trang, không được tràn. Nên dùng `pymupdf.Story`. Bảng phải có **đường kẻ khung**, vì parser chỉ nhận bảng kiểu `lines_strict`.
  - **PDF scan:** dựng trang như PDF text, render ra pixmap khoảng 150 dpi, chèn ảnh vào PDF mới **không có lớp chữ**. Không thêm dependency.
  - **Tái tạo được:** chạy builder 2 lần cho cùng sha256. Nếu file đã tồn tại với nội dung khác thì báo lỗi, như hàm `put` của v1.
- **Không thêm dependency mới.** Nếu bắt buộc phải thêm, dừng lại và đề xuất theo roadmap mục 4.
- **Tách khỏi v1 khi đánh giá:** corpus v1 không có danh tính công ty, và một số chủ đề trùng với v2 nhưng khác số (ví dụ phép năm, mật khẩu). Vì vậy v1 và v2 được ingest vào **workspace riêng** khi chạy eval, không trộn chung một index.

## 7. Test và nghiệm thu (mỗi đợt)

- **Test mới** (ví dụ `eval/tests/test_corpus_v2.py`):
  - Seed hợp lệ, mỗi fact trong registry xuất hiện ở ít nhất một block.
  - Builder cho kết quả giống nhau qua 2 lần chạy.
  - `parse_file` đọc được mọi tài liệu không phải scan; tài liệu scan ra `needs_ocr`.
  - Mỗi bảng tạo ra block có `location.kind` là `docx_table` hoặc bảng PDF, có hàng tiêu đề.
- **Kiểm tra độ dài:** số ký tự mỗi tài liệu nằm trong khoảng ở mục 4.
- **Report** `docs/corpus-v2-<date>.md` (cộng dồn qua 3 đợt). Mỗi tài liệu ghi: định dạng, số trang, số ký tự, số block, số chunk sau khi chạy chunker, các fact, các slice.
- **Không gọi Gemini.** Có thể dùng E5 local nếu cần đếm chunk qua pipeline, nhưng không bắt buộc.

## 8. Trạng thái từng tài liệu (Codex cập nhật cuối mỗi task)

Trạng thái gồm: `chưa viết` → `đã viết` → `người dùng đã duyệt`. Chỉ người dùng chuyển sang "đã duyệt".

| # | Trạng thái | Commit | Ghi chú duyệt |
|---|---|---|---|
| D01 | chưa viết | — | — |
| D02 | đã viết | xem commit 01-T2a | 2 trang DOCX; chưa human review |
| D03 | người dùng đã duyệt | xem commit 01-T2a | Chuẩn văn phong: người dùng xác nhận “D03 đạt” ngày 15/11/2026; 5 trang, 2 bảng |
| D04 | đã viết | xem commit 01-T2a | 2 trang PDF text, bảng kẻ khung; chưa human review |
| D05 | đã viết | xem commit 01-T2a | 4 trang DOCX; chưa human review |
| D06 | chưa viết | — | — |
| D07 | chưa viết | — | — |
| D08 | chưa viết | — | — |
| D09 | chưa viết | — | — |
| D10 | chưa viết | — | — |
| D11 | chưa viết | — | — |
| D12 | chưa viết | — | — |
| D13 | chưa viết | — | — |
| D14 | chưa viết | — | — |

**Chuẩn văn phong đã duyệt: D03** — `quy_che_cong_tac_phi.docx`, người dùng duyệt ngày 15/11/2026. Các phiên sau đọc D03 trong `eval/seeds/corpus_v2.json` trước khi viết tài liệu tiếp theo.
