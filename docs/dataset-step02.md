# Bước 02 — Bộ dữ liệu và nền đánh giá

**Ngày:** 02/11/2026.<br>
**Kết quả:** hoàn thành phần chuẩn bị kỹ thuật; **chưa đóng gate Bước 02 vì thiếu gán nhãn/kiểm tra chéo của hai người**. Chưa bắt đầu Bước 03.

## Deliverables đã có

| Thành phần | Kết quả thật |
|---|---|
| Corpus giả lập | 10 files: 2 PDF, 3 DOCX, 2 TXT, 3 Markdown; 35 source blocks |
| Domain | Nghỉ phép, bảo mật, helpdesk, chiết khấu A/B, duyệt ngoại lệ, onboarding, nghiệm thu, chi phí, biểu mẫu |
| Câu hỏi/đáp án nháp | 45 câu: 15 dev, 30 test; 6 unanswerable (2 dev, 4 test) |
| Loại câu | 22 direct fact, 3 paraphrase, 3 multi-section, 1 conditional, 6 exact identifier, 3 cross-document, 1 conflict, 6 unanswerable |
| Human approval | **0/45**; annotator/reviewer trống, tất cả `pending` |
| Fixtures riêng | 8 files, không gộp vào benchmark Q&A |
| Công cụ | Builder có bảo vệ ghi đè, validator checksum/nguồn/split/review, retrieval/abstention metric primitives |
| Kiểm thử mới | **37 passed**; không DB, không model |

Hướng dẫn thao tác và rubric: [eval/datasets/README.md](../eval/datasets/README.md). Manifest: [corpus_manifest.json](../eval/datasets/corpus_manifest.json). Sổ cần người xử lý: [human_review.csv](../eval/datasets/human_review.csv). Kiến thức/lý do: [KNOWLEDGE K-022–K-026](../KNOWLEDGE.md#k-022--bộ-dữ-liệu-giả-lập-và-human-gold-là-hai-trạng-thái-khác-nhau).

## Môi trường và khả năng tái lập

Python 3.12.8/Windows, venv đã dựng ở Bước 01. Thêm extras `corpus` vào `backend/pyproject.toml`; pin PyMuPDF **1.28.2**, python-docx **1.2.0**, lxml **6.1.3** vào dev lock. Runtime lock và production pipeline không đổi. Không cài CUDA/PyTorch, không tải embedding/LLM, không gọi API; chi phí API phát sinh trong đợt này **0 USD**.

Source seeds và font/tool hashes lưu trong manifest; canonical namespace `author-v1`, parser mapping vẫn `pending_step05`. Builder chạy lại cùng môi trường đạt, giữ nguyên file đã freeze. Encrypted PDF mới ở thư mục khác có thể có hash khác do salt; snapshot hiện tại dùng bytes đã lưu. Hai PDF và các fixtures thật được mở kiểm tra, DOCX đối chiếu paragraph, TXT/MD đối chiếu dòng. Tổng bytes của 18 files corpus/fixture là **2.505.158 bytes**; không phải số đo RAM hay tốc độ model.

Fingerprint snapshot draft sau sửa nhãn trước phát hành:

```text
corpus_manifest.json a4263ce9ab06d4c00845aa88e3a02ec2fbcb2c187ac924ea212651b2c9d869cb
questions.jsonl     48926e7705990879fb1e82ffc8df411f75f4e701ba7d149102800fafc354287a
source_blocks.json  8c4365947738b6a9f6896a9fb5a5d3a80a9d7063138e9843b639413a318ebeae
```

`human_review.csv` là sổ làm việc còn thay đổi nên chưa nằm trong hash manifest draft. Snapshot reviewed trước final benchmark phải khóa cả ledger; không được dùng hash ba files trên để khẳng định sổ duyệt cũng đã được freeze.

## Kiểm chứng đã chạy

Từ root, dùng `.\backend\.venv\Scripts\python.exe -B`:

| Lệnh module | Kết quả |
|---|---|
| `-m eval.build_dataset` | Tạo/đối chiếu 10 documents, 8 fixtures, 45 draft questions; chạy lại không ghi đè |
| `-m eval.validate_dataset` | Structural validation passed; human-approved 0; model benchmark not_run |
| `-m eval.validate_dataset --require-reviewed` | Exit 1 đúng mong đợi: independent human review is incomplete |
| `-m pytest eval/tests -q -p no:cacheprovider` | 37 passed |
| `-m pip check` | No broken requirements found |
| `-m ruff check --config backend/pyproject.toml --no-cache eval scripts backend/app backend/tests` | All checks passed |
| `-m ruff format --check --config backend/pyproject.toml --no-cache eval scripts backend/app backend/tests` | PASS — không cần định dạng lại |

Tests kiểm tra các lỗi có ý nghĩa: sai quote/offset/version/location/group; family/source block rò rỉ dev/test; dữ liệu bị sửa checksum; DOCX bịa page; PDF dẫn sai trang; review thiếu người hoặc tự duyệt; path ra ngoài dataset; chống ghi đè; metric nhiều bằng chứng, duplicate overlap, cutoff/rank, mẫu số 0 và technical errors. Các trường hợp sai được tạo trên bản sao hoặc cấu trúc trong RAM, không sửa nhãn thật.

Kiểm tra PDF ban đầu phát hiện `BM-09` trích xuất thành `BM\u00ad09` khi xuống dòng. Validator có normalization NFC/whitespace/soft hyphen tường minh và regression test; chưa phải remap spans của parser. Trước freeze draft cũng sửa q032 từ hai nguồn lặp cùng một ý sang câu cần dữ kiện bổ sung từ hai tài liệu, tránh phạt retrieval vì không lấy nguồn trùng. Các chỉnh sửa này vẫn là soạn nháp, không được tính như independent human review.

Baseline Bước 01 **64 cases** và frontend lint/build giữ nguyên bằng chứng tại [report trước](environment-step01.md); không chạy lại trong đợt dataset vì không sửa app/API/DB/frontend. Không cộng 64 + 37 thành một lần full suite đã chạy. Chưa tuyên bố hoàn thành AT-R21/22: mới kiểm tra toán metric và artifacts, chưa có span matcher/index rebuild/pipeline thật.

## Tiến độ và việc còn lại

Theo [quy ước PLAN](../PLAN.md#quy-ước-báo-tiến-độ-project), đã có 00/01 và **6/7 đầu việc Bước 02**; đầu việc 5 cần hai người xác nhận nhãn. Tiến độ ước lượng **11,2% / 100%** = `(1,5 + 4 + 7 × 6/7) / 102,5 × 100`. Đây là tỷ lệ khối lượng kế hoạch, không phải accuracy hay thời gian thực tế đã tiêu.

Hai thành viên cần rà soát 45 câu theo hướng dẫn dataset. Nếu có lỗi, ghi `changes_requested` và notes để sửa có phiên bản. Không tự điền approved thay người dùng. Khi review hoàn tất còn cần xuất snapshot reviewed; trước retrieval eval cần mapping Bước 05. Công việc kế tiếp về model là Bước 03, chỉ bắt đầu trong đợt riêng được xác nhận, kiểm tra lại tài nguyên/free quota và giữ trần **0 USD**, không paid fallback.
