# Bàn giao cho Claude — SME Knowledge Copilot

> **Cập nhật 13/11:** Bước 13 (UI v2, đổi tên/xóa phiên, logout thật, phân loại lỗi Gemini) đã merge vào `main`, PLAN v1.31, **97,4%**. Còn video và đóng góp cá nhân (người dùng). [Report](docs/ui-v2-20261113.md).
>
> **Cập nhật 12/11 (sau R1–R3 và rà soát):** release đã merge vào `main`, Compose theo phương án A, cài sạch đạt ([report](docs/fresh-setup-20261112.md)), README mới. PLAN v1.30, tiến độ **96,4%**. Còn video, đóng góp cá nhân và rà soát cuối. Nội dung bên dưới là snapshot trước R1, giữ để tham khảo.

**Cập nhật:** 12/11/2026. **Nguồn trạng thái:** PLAN v1.29. **Tiến độ: 92,9% /100%**, là ước lượng khối lượng theo person-hours, không phải accuracy AI. Chưa M1 Done.

## 1. Mục tiêu và những gì đã làm

Project của nhóm hai SWE developers, xây **RAG thuần cho tài liệu nội bộ SME**, phục vụ portfolio ứng tuyển VNG AI Builder Residency. Người dùng thấy UI hiện tại ổn; ưu tiên hoàn thiện khả năng chạy lại, tài liệu và demo trước khi mở rộng chức năng.

- Ingestion PDF text/DOCX/TXT/MD → parse/chunk có vị trí nguồn → local E5 embeddings → Qdrant. PostgreSQL quản lý metadata/lifecycle; worker có lease, retry, recovery và fencing khi publish.
- Search và hỏi đáp bằng native Gemini adapter; citations do backend gắn với final context, validate schema và repair tối đa một lần; phân biệt grounded/partial/insufficient_evidence với lỗi kỹ thuật.
- Auth/phân quyền, workspace/session ownership; UI đăng nhập, tài liệu, chat và source viewer đã nối API.
- Delete chặn nguồn trước cleanup; dọn SQL/vector/files và redaction history, xử lý races/late writes để tránh hồi sinh nguồn.
- Có corpus/gold evidence, freeze/hash/archive, request ledger/pacing, capture pipeline thật, review hai người và rescore offline; giữ cả lỗi và các lượt kiểm thử thất bại.
- Baseline: FastAPI + React/TypeScript/Vite, PostgreSQL + Qdrant, local `multilingual-e5-small` CPU và `gemini-3.5-flash-lite`. Không thêm agent/STT/workflow Operations cũ. Hybrid/reranker/multi-turn là M2.

## 2. Kết quả đã kiểm chứng

| Hạng mục | Kết quả và giới hạn |
|---|---|
| UI/browser | Chrome E2E P0 có evidence cho upload → ready → hỏi đáp/citation → delete → kiểm tra source/history/query; frontend có 36 tests. Không khẳng định mọi browser/biến thể đã thử. |
| Acceptance phần mềm | Đợt acceptance có 409 test cases khác nhau đạt qua nhiều processes/scoped retests: 302 backend +2 contract bổ sung +69 eval +36 frontend. Giữ logs fail/retest; không phải một invocation pass toàn bộ. |
| Held-out | 30 attempted, 29 outputs, 1 lỗi Gemini generation HTTP503 ở q023. Hai người đã chấm/gộp đủ 29/29 outputs, khớp điểm; strict success **29/30 ≈96,67%**, giữ lỗi trong mẫu số. |
| Human grounding | Correctness trung bình 2/2 trên 29 outputs; support 34/34 claims, citation correctness 36/36 links, completeness 34/34 claims, theo điểm nhóm cung cấp. Tập reviewed nhỏ, không suy thành accuracy tổng quát. |
| Retrieval/latency | Recall@5 =1 trên 26 answerable queries; MRR@5 ≈0,9808. Answer latency n=29: p50 ≈38,81s, p95 ≈44,87s, concurrency1, gồm pacing/network; không phải SLA. |
| Adversarial riêng | Hai synthetic/dev cases chạy E5/Gemini/SQL/Qdrant thật, attack xuất hiện trong actual context/payload cả hai câu. No-tools/0 functioncalls. Hai người chấm/gộp khớp 2/2, support1/1 claim/citation1/1 link. Không cộng vào held-out30. |
| Acceptance hiện tại | **23/23 passed_with_scoped_evidence**. AT-R14 đã đóng bằng contract/literal-render tests + native exposure/no-tools + human review. Đây là evidence tổng hợp, không một lượt all-native/browser rerun hoặc chứng nhận miễn nhiễm injection. |

Đợt adversarial có thêm 26 unit tests mới +45 regression =71 passed, 3 SQL tests riêng passed; không cộng retests hoặc các nhóm overlap thành tổng tests mới.

**Trạng thái PLAN:** Bước00–10 hoàn thành theo phạm vi. Bước11 ghi nhận **5/7 mục: 2–5,7**. Mục1 release/code commit còn mở; mục6 là điều kiện nếu sửa sau khi xem test, chưa cộng. Bước12 vẫn **0/6**. Chưa release freeze/fresh installation/packaging/demo cuối.

## 3. Tài liệu cần đọc theo thứ tự

| File | Cần hiểu gì |
|---|---|
| [AGENTS.md](AGENTS.md) và [CLAUDE.md](CLAUDE.md) | Quy tắc xác nhận, cập nhật kiến thức, kiến trúc và bất biến nghiệp vụ. |
| [PLAN.md](PLAN.md) | **Trạng thái mới nhất ở đầu file**, cách tính tiến độ và Bước11–12. |
| [Specification](SME_Knowledge_Copilot_RAG_Specification.md) | Contract RAG hiện hành; mục15 acceptance/Definition of Done, mục16–19 kiến trúc/config. |
| [KNOWLEDGE.md](KNOWLEDGE.md) | Lý do lựa chọn và bằng chứng; ưu tiên K-086 đến K-100, tra các mục trước theo thành phần cần sửa. |
| [Human review held-out](docs/human-review-heldout-20261112.md) | Benchmark, denominator, lỗi q023 và giới hạn kết luận. |
| [Human review adversarial](docs/human-review-adversarial-20261112.md) | Trạng thái cuối mới nhất: human2/2, AT-R14 đóng, ma trận23/23 và progress92,9%. |
| [Acceptance report](docs/final-acceptance-20261112.md) | Tests, môi trường, lỗi harness/retests, provenance và evidence kế thừa. |
| [Portfolio review](docs/portfolio-review-20261110.md) | Hướng sản phẩm/CV/demo; phần chương trình tuyển dụng là thông tin đã đọc tại thời điểm báo cáo. |

Khi cần triển khai/setup, đọc thêm [final validation plan](docs/final-validation-plan.md), [runbook máy nhận](docs/workspace-restoration-20261105.md), [eval README](eval/README.md) và report từng bước được liên kết trong PLAN/KNOWLEDGE.

**Đọc trạng thái theo thời điểm:** AGENTS/CLAUDE/README và các đoạn lịch sử có thể còn số75,6%/83,4%/91,8% hoặc pending. Ưu tiên PLANv1.29 và báo cáo human adversarial mới nhất. Raw manifest/binding/metrics còn pending được giữ như snapshot lúc capture/xuất phiếu; reviewed-metrics mới là kết quả hậu-review. Không sửa raw files chỉ để đồng bộ nhãn trạng thái.

## 4. Artifacts và ràng buộc khi tiếp quản

- Artifacts held-out đã chấm: scoring folder (`.cache/final-heldout-scoring-20261112/`, chỉ lưu ở máy local), đặc biệt `reviewed-metrics.json`, `rescore-receipt.json`.
- Native adversarial: capture/review folder (`.cache/adversarial-at14-20261112/`, chỉ lưu ở máy local); hai phiếu đã hoàn tất, không chấm lại.
- Kết quả cuối: scoring folder adversarial (`.cache/adversarial-at14-scoring-20261112/`, chỉ lưu ở máy local), gồm `combined-review.json`, `reviewed-metrics.json`, `acceptance-matrix.json`, `rescore-receipt.json`, `handoff-final.json`.
- Ma trận acceptance cũ tại `.cache/at-20261112/` giữ lịch sử22/23. Ma trận mới ở scoring folder adversarial ghi23/23. Đợt merge cuối kiểm958 protected files không đổi, gồm source/config167 files và60 protected held-out files.
- `.cache/` có artifacts local có thể không nằm trong Git. Nếu chuyển máy/workspace, bàn giao có chọn lọc và xác minh hashes theo receipts; không xóa cache/archives/ledgers để làm sạch repo. Không đưa `.env` hoặc secrets vào tài liệu/Git.
- Ngân sách **free tier, tối đa0USD**, không bật billing/paid fallback. Held-out ledger đã dùng30generation/210count, count allowance đã hết. Native adversarial dùng2generation/6count trong grant riêng4/14. Không retry q023, reset/rebind ledger hoặc chạy lại scope one-shot để cấp thêm lượt. Calls mới cần scope/xác nhận/free-tier/quota phù hợp; invoice cost verified vẫn null.
- Trước mọi thay đổi, trình bày files/phạm vi/mục đích rồi chờ đúng **“Thực hiện đi”**. Áp dụng cả tài liệu, artifacts/tests có ghi file, cấu hình/dependencies/data/Git. Đợt mới không được kế thừa quyền từ đợt đã hoàn tất; UI cần xác nhận riêng.
- Mỗi thay đổi kỹ thuật cập nhật KNOWLEDGE trong cùng đợt; phân biệt đề xuất/code/kết quả đã đo. Mỗi phản hồi cuối báo tiến độ theo PLAN.
- Working tree bàn giao có nhiều thay đổi từ các đợt trước, chưa chốt release. Kiểm `git status` trước khi sửa; không reset/clean/ghi đè thay đổi chưa phân loại, không tự commit/push.
- Môi trường gần đây: Windows PowerShell; model cache theo private `.env` trên ổC của máy nhận. Venv Python thiếu interpreter gốc; các kiểm chứng gần đây dùng `C:/Program Files/PostgreSQL/17/pgAdmin 4/python/python.exe` với bootstrap import paths của repo/backend/site-packages. Đọc bootstrap đã có, kiểm môi trường thực tế trước khi dùng lệnh cũ trong CLAUDE/runbook. Host API/worker cùng cwd/storage `backend/`; tests/eval dùng DB/queue/collection/storage riêng, không dùng chung worker dev.

## 5. Các bước còn lại để hoàn thành M1

1. **Chốt release Bước11:** kiểm kê working tree và source/config/prompt/corpus; đối chiếu hashes/evidence, rà soát secrets trước khi chuẩn bị commit theo phạm vi được duyệt. Xác định trạng thái áp dụng của mục6; không tune thêm hoặc tạo hold-out mới chỉ để lấp checklist.
2. **Hoàn thiện Compose Bước12:** API/worker/frontend/PostgreSQL/Qdrant, migrations chạy bước riêng, model cache persistent; pin môi trường/dependencies theo nhu cầu tái lập.
3. **Kiểm chứng fresh setup:** volumes/DB/index/storage riêng, setup → migrate → seed → ingest → query, ghi lệnh/môi trường/kết quả/cleanup. Không xóa volume development để giả clean install; model calls mới cần duyệt riêng. Nếu source/config thay đổi, kiểm lại lớp bị ảnh hưởng trước khi kế thừa acceptance cũ.
4. **Hoàn thiện README/runbook:** cách chạy Windows/container, `.env.example` không secrets, cache/model preparation, tài nguyên đo thật, tests/benchmark/limitations và liên kết evidence.
5. **Quay video2–3phút:** câu hỏi nhiều nguồn, mở citation, câu thiếu bằng chứng, delete/source unavailable/query lại và benchmark report.
6. **Chuẩn bị hồ sơ:** sơ đồ kiến trúc/trade-offs, đóng góp từng người và CV chỉ nêu chức năng/số đo đã có bằng chứng.
7. **Rà soát cuối:** secrets/weights/dữ liệu riêng tư/artifacts lớn, tính truy vết số liệu, Definition of Done; cập nhật PLAN/KNOWLEDGE và chốt bàn giao/release theo phạm vi được xác nhận.

Hybrid/reranker/multi-turn/OCR/agent không phải việc cần bổ sung để đóng M1 hiện tại. Đợt gần nhất đã hoàn tất; Claude nên bắt đầu bằng kiểm tra chỉ đọc và đề xuất phạm vi release/packaging cụ thể để người dùng xác nhận, chưa tự thực hiện toàn bộ các bước trên.
