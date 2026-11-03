"""Logic nghiệp vụ. Routers trong app/api chỉ xử lý HTTP và gọi vào đây.

Module dự kiến cho M1:
- meeting_service.py: tạo meeting + processing job, lưu kết quả STT/extraction
  đã validate (spec 4.2).
- task_service.py: tạo proposal từ action item (idempotent), liệt kê task (spec 4.4).
- approval_service.py: approve/reject trong một transaction; nơi DUY NHẤT tạo task (spec 4.4, 6.3).
"""
