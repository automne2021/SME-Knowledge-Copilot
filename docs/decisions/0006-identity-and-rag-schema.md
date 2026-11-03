# ADR RAG-06 — Seed identity và chuyển tiếp schema

- Ngày: 03/11/2026.
- Trạng thái: Đã triển khai và kiểm chứng nền Bước 04; chưa phải nghiệm thu toàn bộ security/lifecycle M1.
- Liên quan: spec 2.5/9/10, PLAN Bước 04, [report](../schema-identity-step04.md), KNOWLEDGE K-037–K-042.

## Quyết định

Tái sử dụng workspaces/users; giữ email/roles/bảng legacy. Username lowercase ASCII được backfill theo UUID; users có sẵn inactive cho đến khi review, không tự map approver/demo_admin thành knowledge_admin. RAG login chỉ nhận member/knowledge_admin đang active. Jobs dùng discriminator document_id/kind để tách domain, không diễn giải lại generic entity_id của jobs cũ.

Dùng Argon2id cho passwords và opaque random bearer tokens có expiry/revocation trong PostgreSQL; chỉ giữ digest token. Một backend demo không cần JWT/key rotation/refresh flow. Quyền/active state đọc DB mỗi request, workspace không nhận từ client, admin vẫn không đọc chat user khác. Seed là CLI có transaction, không API tự đăng ký hoặc tự cấp quyền; chạy lại không reset passwords/promote user.

Schema dùng partial unique indexes cho dedup/active jobs/running queries và composite FKs cho creator scope, active revision, run/session. Autogenerate là bản nháp phải review CHECKs, backfill, FK cycles/thứ tự. Downgrade từ chối khi có dữ liệu RAG; không drop bảng legacy.

## Phương án khác và đánh đổi

JWT giảm DB lookups nhưng cần ký/rotation và giải quyết thu hồi quyền nhanh; chưa hữu ích với traffic/demo hiện tại. Plaintext token DB tăng hậu quả lộ DB; SHA-256 phù hợp token ngẫu nhiên 256-bit, còn mật khẩu entropy thấp cần Argon2id. Bcrypt/PBKDF2 chưa chọn vì Argon2id phù hợp baseline hiện tại, không có ràng buộc compatibility/FIPS bắt buộc.

Tạo identity/tables jobs riêng hoàn toàn tăng migration và nhân đôi scope; xóa/đổi tên tùy tiện legacy mất lịch sử hoặc phá FK. Giữ discriminator thêm CHECKs/service filters phức tạp hơn, nhưng giữ dữ liệu và ngăn worker/query RAG ăn nhầm legacy jobs. Không tự map email local-part thành username để tránh trùng/lộ email hoặc map role cũ thành admin để tiện demo.

## Kiểm chứng và giới hạn

PostgreSQL thật: migration từ legacy có dữ liệu, schema-only rollback, không downgrade khi đã có RAG data; auth/token expiry/revoke, 401/403/404/410, owner/workspace scopes và source-history masking. Login/me/seed idempotent còn được probe trên DB dev đã migrate. Current source/test commands trong report.

Upload/delete/retry chưa triển khai nên role dependency qua HTTP test riêng chỉ là foundation, không full AT-R09. Chưa có worker lease/race, source cleanup, production multi-tenant/RLS, login rate limiter, refresh/SSO hoặc auth UI. Nếu mở rộng nhiều backend/traffic, xác định policy session store/token rotation và kiểm chứng triển khai trước khi đổi JWT hoặc auth provider.

Nguồn: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [PostgreSQL constraints](https://www.postgresql.org/docs/16/ddl-constraints.html).
