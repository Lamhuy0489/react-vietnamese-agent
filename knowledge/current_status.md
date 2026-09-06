# Trạng thái hiện tại

## Việc đang tiếp tục: Phase 3 và bộ nhớ dự án — 2026-09-06

Đọc [handoff](handoff.md) để tiếp tục đúng điểm đang dở, [runbook](runbook.md)
cho lệnh hiện hành, và [Phase 3 progress](phase3_progress.md) cho audit mới.
Knowledge đã có chỉ mục, bàn giao và validator link/cấu trúc; đây là memory
phát triển, không đưa vào prompt agent benchmark.

Phase 3 đã thêm validator chặt hơn, audit tĩnh và helper surface có bảo vệ
literal. Draft v1 giữ nguyên, chưa accepted: trùng template, lệch category
giữa split, lỗi biến thể/target và chưa có executable overlay/oracles. Bước
tiếp theo là canonical/pair typed fixtures, không chạy thêm Kaggle lúc này.
Kiểm tra lượt này: 130 tests pass; setup/Ruff/mypy/knowledge-check pass;
clean_v1.1 seal và measured release hashes giữ nguyên. Các số test trong
phần lịch sử bên dưới thuộc các mốc trước, không phải lần kiểm tra mới nhất.

## Kết quả model gần nhất: pilot có đo hiệu suất — 2026-09-06

Gemma 4 E4B IT và Qwen2.5 7B Instruct đã chạy xong cùng 21 Dev task trên
Kaggle (mỗi model kernel v1, hai T4, cùng source/software, không chạy lại lỗi
ngữ nghĩa). CPU preflight pass; hai audit pass, 0 model errors, 0 secret matches.
Gemma đạt strict 6/21, trung bình 11,66 giây/task; Qwen 7B đạt 3/21,
10,92 giây/task. Schema validity tương ứng 100% và 94,74%.

[Báo cáo và giới hạn](../docs/evaluation/measured_dev_pilot_report.md),
[bảng/CSV/JSON](../experiments/reports/measured_dev21_v1/report.md),
[nhật ký pilot](multimodel_dev_pilot.md). Các script sinh báo cáo/biểu đồ từ
artifact đã audit; không sửa điểm tay và không chốt model từ mẫu nhỏ này.
Qwen 3B lịch sử không thuộc so sánh tốc độ có kiểm soát. Llama vẫn chưa chạy
vì chưa được cấp quyền Meta; không ghi model thiếu thành điểm 0.
Kiểm tra cuối: setup/Ruff/mypy pass, 107 tests pass; JSON/CSV/Markdown tái tạo
khớp từng byte, biểu đồ PNG/PDF đã kiểm tra hiển thị.

Phase 1 và Phase 2 v1.1 đã accepted; Phase 3 vẫn là draft cần semantic/overlay
QA. Held-out Test chưa chạy model. Phần dưới là lịch sử Phase 1–2.

## Lịch sử đóng Phase 2 — 2026-09-06

Owner đã phê duyệt bản thay thế. v1.1 đã qua QA thực thi 250/250 và khóa split
150/100 không tách nhóm ngữ nghĩa. Kaggle v1.1 COMPLETE ngay lần đầu: 21/21
terminal, 0 crash, 318 trace hợp lệ, 5/21 Dev diagnostic. 96 test pass. Đã
đóng Phase 2 cho benchmark frozen dưới automated-QA waiver; các giới hạn
annotation/cách trả lời tương đương được ghi rõ và không được diễn giải quá mức. Đọc
[clean_v11_progress.md](clean_v11_progress.md) trước phần audit lịch sử bên dưới.

Cập nhật: 2026-09-06, sau audit lại. **clean_v1.0 bị quarantine; clean_v1.1 là
benchmark thay thế đã được chấp nhận dưới waiver.** Kết luận cũ về v1.0
được rút lại; xem `integrity_audit_20260905.md` để biết lịch sử.

## Đã hoàn thành

- Setup repository, GitHub riêng tư và CI.
- Phase 0: research contract và các quyết định nền tảng.
- Phase 1: A0 baseline, simulated university environment, 8 mock tools, 20
  smoke tasks, trace JSONL, local Replay/Dummy và real-model Kaggle smoke.
- Kaggle authoritative run: kernel v4, Dataset v5, Qwen2.5-3B-Instruct v1,
  NVIDIA T4, internet tắt.
- Minh review được chủ dự án cho phép hoãn; lời mời GitHub vẫn giữ nguyên.
- clean_v1.1 đã tạo 250 task, môi trường, split 150/100 và Dev pilot; v1.0
  trước đó có 30 cặp cùng fact/nguồn bị gán nhóm khác nhau, 12 cặp xuyên Dev/Test.

## Trạng thái chất lượng

- Local Replay: 20/20 success, 20/20 terminal, 0 crash, 8/8 tool coverage.
- Real model: 20/20 terminal, 0 crash, 3/20 task success, 78,87% schema
  validity; đây là smoke metric, không phải kết quả luận văn.
- Test sau audit: 96 pass; Ruff/mypy/setup pass. Software pass không thay thế
  thẩm định ngôn ngữ độc lập.
- Phase 1 audit lại: hai lượt Replay/Dummy có cùng hành vi khi bỏ timestamp/run
  ID; 8/8 artifact Kaggle khớp hash, 262 sự kiện hợp lệ, không chạy lại model.
- Phase 2 oracle mẫu: 250/250, đủ 8 tool; review flag được gán sẵn nên không
  chứng minh 250 task đã qua đủ 10 kiểm tra QA.
- Kaggle Dev pilot v2: 21/21 terminal, 0 crash, 334 trace hợp lệ, 7/21 task
  provisional diagnostic success, chưa phải strict TSR; worker đọc 0 Test/GT.
- Held-out Test: đã niêm phong, chưa chạy model và không được dùng để tuning.

## Trạng thái phase tại thời điểm audit v1 (lịch sử)

Phase 2 mở lại, v1 giữ nguyên làm lịch sử. Đã sửa signature/group/hash validator,
chặn ghi đè bản khóa và chặn đóng gói split lỗi. Không đổi task/GT/môi trường/
schema/manifest v1. Cần chủ dự án chấp thuận version benchmark thay thế để sửa
quy trình nhóm xuyên category, QA theo bằng chứng và comparator trước khi khóa
lại. Phase 3 chưa bắt đầu; không cần thêm tài khoản hay Minh review.

Huy và Minh dùng chung máy nên chủ dự án bỏ peer review. Dataset không ghi giả
reviewer; thay vào đó phải có automated QA theo owner waiver, đồng thời ghi
rõ hạn chế thiếu independent human review trong data card. Không ghi rằng chủ
dự án đã inspect từng task; audit record dùng `automated_gate`.
