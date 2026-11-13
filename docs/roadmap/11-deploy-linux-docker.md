# 11 — Docker Linux, CI và demo online

**Mốc:** M3 · **Công sức:** L · **Phụ thuộc:** không · **Nhánh:** `feat/11-deploy`

## Mục tiêu

1. Chạy toàn bộ hệ thống (API, worker, frontend, PostgreSQL, Qdrant) bằng **một lệnh** trên Linux hoặc Docker Desktop.
2. Có **CI trên GitHub Actions**: chạy test backend (PostgreSQL và Qdrant thật dưới dạng service) và test frontend cho mỗi lần push.
3. (Tùy chọn, người dùng quyết) Có một **link demo online** để nhà tuyển dụng tự bấm thử.

## Giá trị với nhà tuyển dụng

- Huy hiệu CI xanh trên README là tín hiệu dễ thấy nhất.
- Link demo online giúp người lọc hồ sơ thử ngay, không cần cài đặt.
- Thể hiện năng lực MLOps cơ bản: đóng gói model, cache model, cấu hình theo môi trường.

## Hiện trạng

- Theo K-102, phương án A đang được dùng: Compose chỉ chạy storage; API, worker và frontend chạy trên Windows.
- Lock Torch hiện chỉ có wheel cho Windows x64 / CPython 3.12 (`backend/requirements-worker-cpu.lock`).
- `backend/Dockerfile` hiện chỉ có runtime lock, không có Torch/E5; có ghi chú rằng image này không thuộc topology M1.
- E5 phải nằm sẵn trong `HF_HOME` với đúng revision. Ứng dụng không tự tải model.

## Thiết kế

- **Lock cho Linux:** `backend/requirements-worker-cpu-linux.lock` (Torch CPU wheel cho manylinux, CPython 3.12), sinh trong container và có hash.
- **Image:**
  - `backend` multi-stage: một image cho cả API và worker, khác nhau ở command.
  - Model E5 **không** đóng vào image. Dùng volume `hf_cache` cùng một job `model-fetch` một lần, có pin revision và kiểm tra fingerprint (K-050, K-074).
  - `frontend`: build Vite, phục vụ bằng nginx, proxy `/api` sang API.
- **Compose:**
  - Thêm profile `full` gồm `migrate` (chạy một lần), `seed` (chạy một lần, mật khẩu đọc từ `.env`), `api`, `worker`, `web`.
  - Profile mặc định vẫn chỉ chạy storage, để workflow Windows hiện tại không đổi.
- **CI:**
  - Job backend: services `postgres` và `qdrant` theo đúng digest trong `compose.yaml`, chạy `pytest` + `ruff`.
  - Job frontend: lint, test, build.
  - Test cần E5 thật hoặc Gemini phải được đánh dấu và **bỏ qua có lý do** trong CI; số test bị bỏ qua in ra trong summary.
  - Không đưa secret thật vào CI.
- **Demo online (T4, chờ người dùng chọn):**
  - Lựa chọn hạ tầng: VM miễn phí; Hugging Face Spaces dạng Docker (CPU, RAM có hạn, dữ liệu không bền); hoặc máy cá nhân kèm tunnel.
  - **Bắt buộc:**
    - Chỉ dùng corpus giả lập.
    - Có tài khoản demo chỉ đọc.
    - Rate limit theo IP.
    - Có trần số câu hỏi mỗi ngày để giữ quota Gemini free.
    - Ẩn chức năng upload với tài khoản demo.
    - Ghi rõ "dữ liệu giả lập".
  - Key Gemini đặt trong secret của nền tảng, không bao giờ nằm trong image.

## Task

### T1 — Lock Linux và image backend

- **Test:** trong container, `pytest` chạy đủ bộ test (cần E5 cho worker: tải vào volume bằng job `model-fetch`); `pip check` đạt.

### T2 — Compose profile `full` và runbook Linux

- **Nghiệm thu:** trên máy sạch, `docker compose --profile full up` → migrate → seed → upload một tài liệu → hỏi (tắt LLM thì phải ra 503 đúng) → xóa. Report ghi thời gian từng bước.

### T3 — GitHub Actions CI

- Workflow `.github/workflows/ci.yml`, cache pip/npm, có badge trên README.
- **Nghiệm thu:** một PR thử chạy xanh; số test chạy, số bỏ qua và lý do in ra rõ ràng.

### T4 — Demo online (đợt riêng, người dùng chọn hạ tầng)

- Gồm rate limit, chế độ demo, giới hạn quota, và trang "Giới thiệu" nói rõ giới hạn.
- Phải kiểm tra bảo mật trước khi mở công khai: không lộ secret, có CSP, tài khoản demo không ghi được.

## Không làm

- Kubernetes, autoscaling.
- Dùng GPU trong CI.
- Đóng model weights vào repo Git.
