# Architecture Decision Records

Nguồn hiện hành: [Spec RAG v2.1 mục 19](../../SME_Knowledge_Copilot_RAG_Specification.md). Mục 14 của spec RAG là evaluation, không phải danh mục ADR Operations cũ. Không triển khai Python tool loop theo hướng dẫn lịch sử.

ADR (*Architecture Decision Record*) lưu quyết định, bối cảnh, các phương án và đánh đổi. Spec giữ contract, PLAN giữ thứ tự, [KNOWLEDGE.md](../../KNOWLEDGE.md) giải thích kiến thức/bài học và liên kết ADR khi có.

## Quy tắc ghi

Implementation Bước 07: [ADR RAG-02 — dense retrieval baseline](0002-dense-retrieval-baseline.md), search/source/SQL revalidation và dev-only metrics; [report](../search-retrieval-step07.md).

Implementation Bước 06: [ADR RAG-05 — durable worker](0005-durable-ingestion-worker.md), lease/generation, local E5/Qdrant và recovery/publish; [report](../worker-index-step06.md).

Implementation Bước 05: [ADR RAG-07 — source-preserving ingestion](0007-source-preserving-ingestion.md), upload/parser/chunker và canonical mapping; worker/index chưa triển khai.

- Khi bắt đầu phần code liên quan, tạo ADR được người dùng xác nhận cùng phạm vi công việc; ví dụ `0001-rag-vector-storage.md` ánh xạ ADR-01 của spec. Bước 00 chỉ đồng bộ hướng dẫn, chưa tạo ADR implementation riêng.
- Phân biệt đề xuất, đã chọn ở thiết kế, đã triển khai và đã kiểm chứng. Model candidate/config khởi đầu chưa phải lựa chọn đã benchmark.
- Giữ nguyên danh tính model/runtime/config/artifact khi dẫn kết quả. Điều kiện đổi embedding phải xét reindex/manifest; không chỉ sửa một tên model trong env.
- Thay quyết định giữ file cũ, thêm liên kết tới ADR thay thế; không xóa trade-off hoặc thí nghiệm không cải thiện.
- Không tự thêm service/dependency hoặc mở rộng scope vì một ADR đề xuất; trước thay đổi phải có câu “Thực hiện đi” cho phạm vi cụ thể theo AGENTS.md.

## Danh mục baseline RAG

| ADR theo spec | Chủ đề / trạng thái cần phản ánh khi triển khai |
|---|---|
| ADR-01 | PostgreSQL + Qdrant, consistency/cleanup; chưa cấu hình Qdrant trong repo |
| ADR-02/03 | Dense baseline; BGE-M3 candidate, PLAN đề xuất smoke E5 CPU trước; chưa có benchmark chọn model |
| ADR-04 | LLM adapter, hosted/local; provider compatibility/usage phải kiểm tra thật |
| ADR-05/06 | Worker lease/generation và seed auth/workspace/session owner |
| ADR-07/08/09 | Source location theo định dạng, citation backend, text-first parsing |
| ADR-10/11/12 | Duplicate 409, fixed pipeline, sync chat/standalone P0 |
| ADR-13/14/15 | Structured claims/repair, delete/history policy, labeled reproducible benchmark |

Audit schema và các quyết định còn cần xác minh dữ liệu: [rag-transition-audit.md](../rag-transition-audit.md). Giữ số ADR trùng spec và ghi rõ namespace RAG khi so với quyết định trong tài liệu Operations lịch sử.

**Implementation đã có ngày 03/11/2026:** [ADR RAG-06 — identity/schema](0006-identity-and-rag-schema.md) được kiểm chứng ở [Bước 04](../schema-identity-step04.md). Baseline table phía trên giữ nguồn quyết định ban đầu; Qdrant đã cấu hình Bước 01, model smoke Bước 03 có reports nhưng chưa chọn model thắng bằng benchmark. Không coi mọi hàng baseline là chưa triển khai hoặc đã nghiệm thu.

Mẫu:

```markdown
# ADR-XX: <tiêu đề>

- Trạng thái: Đề xuất | Đã chọn ở thiết kế | Đã triển khai | Đã kiểm chứng | Thay thế bởi ADR-YY
- Ngày: YYYY-MM-DD
- Liên quan: spec/PLAN, code/commit, KNOWLEDGE K-xxx

## Bối cảnh
## Quyết định
## Phương án khác và vì sao chưa chọn
## Lý do và đánh đổi
## Cách kiểm chứng, kết quả và giới hạn
## Điều kiện xem lại
## Nguồn tham khảo
```
