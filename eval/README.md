# Evaluation

Đánh giá theo spec mục 12. Mọi con số trong README chính phải truy được về file trong `results/`.

## Cấu trúc dự kiến

```text
eval/
├── datasets/
│   └── meetings/
│       └── <meeting_id>/
│           ├── audio.wav                  # người thật đọc kịch bản, không dùng TTS
│           ├── script.md                  # kịch bản gốc
│           ├── reference_transcript.txt   # bản chép chuẩn để tính WER
│           └── labels.json                # action items, assignee, deadline, segment bằng chứng
├── results/                               # kết quả mỗi lần chạy (commit vào repo)
└── run_evaluation.py                      # thêm khi có pipeline STT/extraction
```

## Quy tắc

- Dữ liệu là giả lập hoặc có sự đồng ý của người liên quan.
- Ghi rõ model, cấu hình, phần cứng và ngày chạy trong mỗi file kết quả.
- Quy tắc matching action item (thủ công hay theo ngữ nghĩa) ghi trong `results/` cùng kết quả.
- Báo cáo cả failure case, không chỉ các trường hợp thành công.
