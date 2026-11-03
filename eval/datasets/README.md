# Corpus và nhãn nháp — Bước 02

Ngày 02/11/2026. Snapshot `synthetic-sme-v1` / `draft-v1` gồm **10 tài liệu, 35 source blocks, 45 câu hỏi**, thêm 8 fixtures riêng. Toàn bộ nội dung doanh nghiệp là giả lập; không phải chính sách, mật khẩu hay dữ liệu của công ty thật.

**Cập nhật 03/11/2026:** hai thành viên đã duyệt **45/45 câu**. Bản phát hành khóa hash cả sổ duyệt là [reviewed-v1](../snapshots/reviewed-v1/corpus_manifest.json). Thư mục datasets hiện tại vẫn là nguồn làm việc với manifest `draft-v1`; giữ để tái tạo/đối chiếu lịch sử, không đổi manifest draft thành reviewed tại chỗ. Câu/đáp án ban đầu do trợ lý soạn, đã được con người kiểm tra theo quy trình dưới đây. Chưa có RAG quality benchmark; E5 CPU smoke tương thích đã chạy tại [Bước 03](../../docs/model-smoke-step03.md).

## Files và quy ước nguồn

**Bước 05:** canonical author spans của snapshot reviewed-v1 đã có [mapping version mới](../mappings/reviewed-v1-source-v1-e5-350-v1.json) sang parser thật (35 blocks/45 câu/47 evidence references), xem [report](../../docs/parsing-upload-step05.md). Giữ nguyên draft và reviewed manifest; không thay offsets author-v1 tại chỗ.

| File/thư mục | Nội dung |
|---|---|
| `corpus/` | 2 PDF text, 3 DOCX, 2 TXT, 3 Markdown |
| `fixtures/` | Scan, blank, mixed, encrypted, malformed PDF/DOCX, MIME giả, prompt injection |
| `corpus_manifest.json` | Phiên bản, SHA-256, tool/font/seed fingerprints và trạng thái nhãn |
| `source_blocks.json` | Nội dung canonical do tác giả chia thành các đoạn ngắn, kèm vị trí nguồn |
| `questions.jsonl` | 15 dev, 30 test; câu hỏi, đáp án nháp, answerability, evidence groups/spans |
| `human_review.csv` | Sổ duyệt đang chờ, có `annotator`, `reviewer`, `status`, `notes` |

`source_block_id` dùng namespace **author-v1**, chưa phải ID/source spans của parser ứng dụng. Offset `char_start`/`char_end` là chỉ số ký tự Python trong text canonical Unicode NFC, bắt đầu 0, kết thúc exclusive. Vị trí trang/block/line bắt đầu 1. PDF có page thật; DOCX dùng body paragraph (không giả số trang), TXT/MD dùng dòng UTF-8. Bước 05 phải remap sang canonical parser blocks và kiểm tra quote/location trước retrieval evaluation; không so trực tiếp offset của hai bản text khác nhau.

Mỗi evidence group ở draft này có một span bắt buộc. Các groups khác nhau là những ý cần kết hợp; không coi hai nguồn lặp cùng một ý là hai điều kiện bắt buộc. Câu q032 được soạn để cần hồ sơ nghiệm thu ở một tài liệu và nội dung biểu mẫu ở tài liệu khác. `document_version=2` của bản chiết khấu B chỉ định danh nguồn; không chứng minh bản B thay thế A hay đang có hiệu lực.

Các câu cùng sự kiện/paraphrase ở cùng split. Validator kiểm tra cả `family_id` và canonical source block không xuất hiện làm gold ở hai split. Tất cả tài liệu vẫn thuộc cùng corpus để search; dev/test là chia câu hỏi, không chia index. Không dùng 30 câu test để chọn model/prompt/threshold. Đây là bộ nhỏ để phát hiện lỗi và demo, chưa đại diện cho tài liệu SME thực tế, bảng phức tạp hoặc mọi cách hỏi tiếng Việt.

## Hai người cần làm gì để duyệt

1. Người A đọc tài liệu gốc, tự xác định đáp án/điều kiện và bằng chứng trước khi đối chiếu nhãn nháp. Sửa hoặc ghi vấn đề nếu trợ lý soạn thiếu/sai; điền tên/ID ổn định vào `annotator` khi thực sự chịu trách nhiệm gán nhãn. Không điền tên trợ lý thành human annotator.
2. Người B kiểm tra độc lập từng câu: câu hỏi có rõ không, đáp án có đủ ý không, quote có trong đúng file/phiên bản/vị trí không, nguồn có thực sự cần kết hợp không. Điền `reviewer` khác A; không duyệt hộ hoặc tự kiểm tra chéo chính mình.
3. Với câu thiếu bằng chứng, tìm trên **toàn snapshot**, không chỉ tài liệu có vẻ liên quan. Sáu câu hiện tại là q014–015, q042–045. Không dùng kiến thức ngoài corpus để trả lời câu hỏi về doanh nghiệp mẫu.
4. Với q018, chỉ trả lời điều kiện giảm 10%, chưa kết luận giao dịch đã được duyệt/trả trước. Với q024, nêu 3%/5% và thiếu căn cứ hiệu lực; không chọn B chỉ vì số phiên bản lớn hơn. Hai câu này là `partial`, không phải abstain hoàn toàn.
5. Ghi `status=approved` chỉ khi A/B đã thống nhất và nhãn đúng; có lỗi ghi `changes_requested` và mô tả trong `notes`. Chưa xem giữ `pending`. Mỗi câu phải được kiểm tra, không duyệt theo số đông.
6. Nếu cần sửa câu/đáp án/nguồn, ghi notes để tạo snapshot phiên bản mới từ seeds cùng manifest/checksums, sau xác nhận phạm vi thay đổi. Không chỉ đổi hash để làm validator xanh. Công cụ `eval.publish_reviewed` đã xuất reviewed-v1 với `label_status=human_reviewed` và khóa cả ledger. Chỉnh sửa tiếp cần snapshot phiên bản mới; không sửa bản đã khóa hoặc re-bless hash để che khác biệt.

Validator chỉ kiểm tra có hai tên khác nhau; không thể chứng minh hai người đã thực sự đọc nguồn. Kết quả `structural_validation=passed` không thay việc duyệt nội dung.

## Rubric chấm answer ở các bước sau

Theo [spec 14.9](../../SME_Knowledge_Copilot_RAG_Specification.md#149-metric-definitions-và-rubric-chấm): correctness **0** nếu sai/bịa, **1** nếu đúng một phần hoặc thiếu điều kiện quan trọng, **2** nếu đúng và đủ. Chấp nhận diễn đạt tương đương, không bắt buộc khớp chuỗi đáp án mẫu. Mốc ngày, số tiền, người duyệt, mã mẫu và điều kiện phải đúng.

Chấm riêng claim faithfulness so với context thực gửi model, citation correctness theo từng liên kết và completeness theo từng claim. Câu unanswerable phải thông báo thiếu nguồn, không bịa số liệu; partial chấm claims/điều kiện còn thiếu riêng. Timeout/index/provider error là lỗi kỹ thuật, không tính thành abstention đúng. Mẫu số bằng 0 trả `null` cùng số mẫu ở report tương lai. Bước 02 chỉ có metric primitives, chưa có answer judge/report runner.

## Chạy kiểm tra từ repository root

Các lệnh Python không cần activate `.ps1`; chỉ chạy lệnh tạo artifacts trong đợt đã được người dùng xác nhận.

```powershell
.\backend\.venv\Scripts\python.exe -B -m eval.validate_dataset
.\backend\.venv\Scripts\python.exe -B -m pytest eval/tests -q -p no:cacheprovider
.\backend\.venv\Scripts\python.exe -B -m eval.validate_dataset --dataset eval/snapshots/reviewed-v1 --require-reviewed
```

Lệnh cuối đạt trên reviewed-v1 có đủ 45 approvals/hash ledger. Nếu dùng `--require-reviewed` trên đường dẫn draft mặc định, nó vẫn từ chối vì chưa phải manifest phát hành reviewed. Validator chỉ đọc; pytest tạo bản sao tạm để thử lỗi, không sửa corpus/review thật và không kết nối DB/model.

Builder từ [seeds](../seeds/) dành cho tái tạo/kiểm tra draft:

```powershell
.\backend\.venv\Scripts\python.exe -B -m eval.build_dataset
```

Builder dùng PyMuPDF 1.28.2, python-docx 1.2.0 và Arial máy Windows; pins trong `backend/requirements-dev.lock`, font hash trong manifest. Máy khác có thể dùng `--font <path>` với `--output <new-directory>`; khác font/version có thể khác bytes. Không phân phối file font gốc trong repo. Chạy lại cùng môi trường giữ nguyên checksum; gặp file đã sửa thì dừng, không ghi đè hoặc tự cập nhật hash. DOCX ZIP timestamps được cố định. PDF encrypted có salt ngẫu nhiên, nên lần đầu ở thư mục mới có hash khác; fixture đã freeze được giữ nguyên và kiểm tra lại thay vì tuyên bố build byte-identical trên mọi máy. CSV ghi nhận review không bị builder ghi đè.

## Fixtures chỉ là input chờ pipeline

| Fixture | Hành vi đích cần kiểm tra ở bước triển khai |
|---|---|
| `scan.pdf` | Có ảnh, không text layer → `needs_ocr` |
| `blank.pdf` | Không text/ảnh → `no_extractable_text`, khác scan |
| `mixed.pdf` | Trang 1 text, trang 2 scan → cảnh báo partial, ghi skipped page 2 |
| `encrypted.pdf` | Từ chối tài liệu cần mật khẩu → `encrypted_document` |
| `malformed.pdf`, `malformed.docx` | `parse_failed` có kiểm soát |
| `spoofed.pdf` | File text gắn đuôi PDF → `unsupported_file_type` |
| `prompt_injection.txt` | Nội dung không đáng tin, không thực thi hướng dẫn trong tài liệu |

Mật khẩu `fixture-only` chỉ mở file thử encrypted, không là secret thật. Validator xác minh tính chất file; **chưa chứng minh upload/parser/security/LLM của app xử lý đúng các mã trên**. Không gọi OCR, không tạo ZIP bomb hay tệp khai thác, không đưa các fixtures này vào điểm accuracy Q&A thông thường. Các giới hạn size/ZIP/XSS/quyền sẽ có software tests riêng ở các bước sau.
