# Kết quả human review held-out — 12/11/2026

Nhóm đã điền hai phiếu của29outputs thuộc [composite hai phiên](final-continuation-20261112.md). Đợt được xác nhận này chỉ validate, merge và rescore offline: **không gọi Gemini/embedding, ghi DB/Qdrant, sửa UI/pipeline, retry hoặc đổi model/prompt**. Agent giữ nguyên điểm do nhóm cung cấp, không chấm thay hoặc thêm adjudication.

## Kết quả đã lưu

Hai phiếu đều đủ29entries, thuộc đúng run/output hash, schema hợp lệ và dùng hai reviewer IDs khác nhau (`reviewer-1`, `reviewer-2`). Điểm khớp29/29; không bất đồng hoặc pending, nên toàn bộ `adjudication` giữnull. Kiểm tra này xác nhận định dạng/identity/binding và sự khớp điểm, không chứng minh độc lập quy trình chấm ngoài những gì nhóm xác nhận.

| Chỉ số | Kết quả | Mẫu số và cách hiểu |
|---|---:|---|
| Planned / attempted / successful / errors / not attempted | 30 /30 /29 /1 /0 | Lỗi q023 từ phiên đầu được giữ nguyên |
| Output đã human review | 29/29 | Không có output để chấm cho q023failed |
| Correctness trung bình | 2/2 | 29output thành công đều được hai người chấm2 |
| Strict end-to-end success | 29/30≈96,67% | Output thành công có correctness2 /toàn bộ30câu dự kiến |
| Faithfulness | 34/34claims=100% | Theo support judgments của nhóm, so actual final context |
| Citation correctness | 36/36links=100% | Chấm từng liên kết claim–evidence |
| Citation completeness | 34/34claims=100% | Mỗi claim có ít nhất một citation được chấm đúng |
| Abstention precision /recall | 1 /1 | Bốn expected-abstain, cả bốn trả insufficient_evidence |
| False abstention | 0/25=0% | 25answerable có output; q023lỗi không tính thành từ chối |
| Technical error rate | 1/30≈3,33% | q023generationHTTP503, không bị xóa khỏi denominator |

Mẫu số abstention gồm29outputs (25answerable+4unanswerable), không phải30generation thành công. Faithfulness/citations chỉ có34claims/36links; các câu từ chối không có claims vẫn cần correctness. Không suy thành độ an toàn hoặc accuracy100% trên tài liệu doanh nghiệp thực tế. Hai reviewer cho cùng điểm không thay thế đánh giá bên ngoài; tập synthetic reviewed nhỏ và nhãn/gold của nhóm là giới hạn của benchmark.

Retrieval26answerable: Recall@5=1,0, MRR@5≈0,9808; bao gồm q023 đã retrieve trước lỗi generation. Multi-evidence5câuRecall@1=0,6, @3=0,9, @5=1,0. Production capturetop5; cột@10 generic không là10hits thật. Latency concurrency1 trên29outputs: p50≈38,81s, p95nearest-rank≈44,87s; retrieval30queriesp50≈586,79ms/p95≈634,98ms. Query latency chứa pacing/network, E5/index đã nạp lúc ingest; không suy thành LLM latency thuần, cold-start SLA hoặc concurrent throughput.

## Phân tích lỗi và giới hạn

**Một lỗi kỹ thuật đã xác minh: q023, tầng provider generation.** Capture đánh dấu `provider`, native event ghi `generateContent`HTTP503 sau retrieval thành công; query duration≈39,25s, không có final answer/usage generation. Vì retrieval có đủ gold groups ởtop5, quan sát này không phải một retrieval miss hoặc abstention. Chưa có raw provider body hay dữ liệu trạng thái hệ thống Google để xác định nguyên nhân cụ thể; không quy thành hết quota/429. Không retry: reservation1generation+7count được giữ, continuation chỉ chạy22câu chưa từng thử. Count allowance gốc hiện210/210, không reset hoặc đổi scope để gọi tiếp. Xem [capture/lỗi gốc](final-heldout-20261111.md).

Hướng xử lý sau này, chưa triển khai: nếu cần kiểm tra khả năng phục hồi provider, dùng dev fixture và một scope/request allowance được duyệt riêng, giới hạn retry và lưu cả lỗi cũ; không thay q023 trong report này hoặc tune bằng held-out. HTTP503 đơn lẻ chưa đủ bằng chứng để sửa retrieval/model/prompt. Trước tối ưu latency cần tách pacing khỏi từng stage và đo trên dev; không đổi deadline hoặc bỏ count để làm số đo đẹp hơn.

**Không phát hiện lỗi nội dung theo điểm nhóm đã nộp.** q024 là `partial` nhưng được cả hai chấm correctness2; status partial tự nó không là lỗi, rubric cho phép trả đúng phần có căn cứ và nêu phần thiếu/mâu thuẫn. Bốn từ chối cũng được chấm2. Đây là quan sát đã chấm của các outputs cụ thể, không thêm hai lỗi giả cho đủ ba case. Lỗi parser/context/citation khác chỉ được kết luận khi có evidence mới.

Các phạm vi còn thiếu: fullAT-R01–23 trên bản chốt, fresh setup/clean volumes riêng, mapping/rebuild trên môi trường sạch, native adversarial coverage theo bản chốt và browser variants ngoài luồng P0. Có lịch sử smoke injection/oracle ởBước08; đó không là một ablation/adversarial benchmark mới trên30câu. Không đo oracle/no-context đối chứng cho final, ba lượt/query hoặc concurrent load. [Ma trận khoảng trống](final-acceptance-gaps-20261112.md) giữ các mức bằng chứng riêng; chưa tuyên bố M1 hoặc production-ready.

## Artifacts và kiểm chứng

- [Combined review](../.cache/final-heldout-scoring-20261112/combined-review.json), [reviewed metrics](../.cache/final-heldout-scoring-20261112/reviewed-metrics.json), [receipt](../.cache/final-heldout-scoring-20261112/rescore-receipt.json).
- [Helper một lần](../.cache/final-heldout-scoring-20261112/merge-and-rescore.py): gọi merge/rescore hiện có, exclusive writes; không chạy lại trên outputs đã tồn tại.
- [Hashes trước thao tác](../.cache/final-heldout-scoring-20261112/input-hashes-before.json):60files gồm hai phiếu hiện tại, binding/worksheet, captures/executions/SQLite ledgers/raw reports của hai phiên và composite, protocol/controller/grants/approvals, packet7outputs cũ và practice6câu. Tất cả hashes trước/sau khớp; source/input/archive/controller cũng verify trước/sau.
- Binding/metrics raw vẫn ghi pending/0reviewed tại thời điểm xuất, không sửa lịch sử. Trạng thái mới nằm ở reviewed-metrics; raw manifest vẫn `completed_with_errors`, không chuyển thành full acceptance pass.

Đã kiểm tra độc lập phép tính từ hai bộ điểm khớp: correctness,29/30strict success, support trên34claims,36citation links và completeness. Không viết test mới chỉ để lặp lại implementation hoặc chạy lại model/backend suites khi không sửa pipeline. Model calls/embedding calls/DB writes mới đều0, chi phí inference mới0; invoice của native capture trước đó vẫn chưa xác minh (`null`).

Run `offline_replay_1183a4c02b204744b58b042eed56c802`, productionprotocol `1340f78f14f054fc63196e983c5cd876939f52534d999f663cdffe8257ae4b3d`. Source rows SHA `e62bbb5131877a53693410d6479868293348f1e00e08eb5f6b54ceb01da1a754`; combined review SHA `84d4b8a1c59eb2089eb2d98a5c4f9a31b3988628e9e2fc982483434153762f96`. Hashes hai phiếu và reviewed metrics đầy đủ trong receipt, không lưu secrets hoặc suy luận nội bộ.

## Trạng thái kế hoạch

Bước11 ghi nhận **4/7 đầu việc:2,3,4,5** — báo cáo held-out có human metrics; phân biệt unit/stub/native/oracle lịch sử và phần chưa đo; latency concurrency1 có mẫu số; failure analysis theo đúng số lỗi quan sát. Mục1 còn chốt release/code commit, mục6 giữ chính sách không tune test và chỉ kiểm lại khi có thay đổi, mục7 còn fullAT-R. Mục6 chưa cộng tiến độ chỉ vì điều kiện chưa phát sinh. Bước12 chưa thực thi; không đổi trọng số.

`100×(89,5+8×4/7)/102,5≈91,8%`. Đây là ước lượng khối lượng theo PLAN, không phải accuracy. **Tiến độ:91,8% /100%.**

Bước kế tiếp được đề xuất là đóng ma trận acceptance với lệnh/evidence và phạm vi riêng, rồi mới fresh setup/đóng gói/demo theo PLAN. Đợt này dừng ở báo cáo và xác định gaps; không tự chạy các kịch bản còn thiếu.
