"""Worker xử lý job nặng, chạy như tiến trình riêng (ADR-05).

Dự kiến job_worker.py: poll processing_jobs bằng SELECT ... FOR UPDATE SKIP LOCKED,
gọi trực tiếp domain service (không gọi qua HTTP), retry có giới hạn theo attempts.
"""
