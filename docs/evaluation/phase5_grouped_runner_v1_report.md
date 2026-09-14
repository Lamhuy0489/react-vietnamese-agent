# Grouped Dev runner v1 — CPU QA

2026-09-14. Source `354b75b431661504a3c1cb84bd59c680d22d7f95`; bounded CPU QA đạt.
Không có native inference, chất lượng LLM, ASR/FPR hoặc truy cập held-out Test.

## Kết quả đã kiểm

Lượt focused lưu tại `results/phase5_grouped_runner_v1_cpu01` đạt **27 tests /
130,62s**. Kiểm lại độc lập tám shard bằng `audit_prefix` và CLI audit-only cho
shard 0 đều đạt. Setup/Ruff/mypy (381 files)/knowledge-check đạt; full pytest
**3.055 pass/1 skip/973,70s**. Skip duy nhất: native tqdm không có trong môi trường
local. Thời gian pytest nội bộ ở đây khác wall time của wrapper (974,69s full,
131,21s focused); không dùng hai loại thời gian thay thế nhau.

Kiểm độc lập **537 source/1.783 raw/169 data hashes** đều khớp.
[Selected receipt](../../experiments/manifests/phase5_grouped_runner_v1_cpu01.json)
SHA-256 `6233354ab9445569d83c020f4b3a4f1f4d65bcd81fec4a85bea53ea80243f9f3`.
Output đã đóng, không ghi thêm hoặc chạy trùng. Receipt là working-tree CPU QA
với hash-bound source, không tự nhận clean release khi repo còn sửa đổi khác của
người dùng. Raw nằm local/untracked; source, report và receipt được chọn lưu Git.
Quét 2.330 files nguồn/raw/tài liệu/receipt với bốn credential values local:
zero matches; không lưu values trong báo cáo. Không quét nội dung held-out data.

| Bằng chứng scripted CPU, chỉ trong tám shard chuẩn | Số lượng |
|---|---:|
| Khóa task riêng biệt, không trùng | 112 |
| Runtime terminal `completed` | 112 |
| Tool calls thực thi / tool results | 106 / 106 |
| Guard PRE / POST có phản hồi | 80 / 74 |
| Sanitized guard sidecar records | 154 |
| Worker lifecycle GRACEFUL, được reap | 192 |

Agent giả lập phát một public trigger rồi final cố định; guard giả lập luôn
SAFE. Do đó `completed` không có nghĩa task utility đạt, guard phát hiện đúng
tấn công, hay GPU lifecycle đã đạt. Không dùng timing CPU này so sánh LLM.
Test manifests dùng commit sentinel `a` × 40; QA receipt gắn source commit và
hashes thực tế. Không gọi sentinel là một commit Git thật.

Sáu ca không có tool result là attack và benign `CAND_ROWLIST_PARAPHRASE` ở
A4/A5/A6. Public instruction không cấp rõ cột cần đọc theo bounded scope v5;
runner giữ quyết định từ runtime. Không thay dữ liệu, cấp quyền từ oracle, bỏ
benign khó hoặc retry để cải thiện kết quả. Đây là giới hạn đã ghi ở
[SQL scope v5](phase5_sql_scope_v5_report.md), không phải phát hiện từ Test.

## Resume và kiểm tra âm

Mỗi shard chạy một ca, dừng có kiểm soát, rồi chạy tiếp 13 ca. Khi đã đủ 14 ca,
resume chỉ audit và giữ nguyên tất cả bytes. Tám loại phá checkpoint kiểm việc
từ chối trước khi chạy thêm: identity, thư mục dở, khóa lạ, khoảng trống, raw,
runtime metadata đã rehash, checkpoint key và symlink. Sai shard/commit cũng
không được tiếp tục. Fault-control riêng tạo terminal `parse_failure`, sau đó
resume không thực thi lại; không trộn ca này vào bảng 112 ca chuẩn.

Các fixture phá dữ liệu vẫn giữ trong raw output để audit, nhưng không được
nhận là runtime/checkpoint hợp lệ. Hashes bảo vệ toàn vẹn đối chiếu receipt;
không phải chữ ký xác thực chống sửa đồng thời cả raw lẫn receipt.

## Việc còn lại

Ghép native factories/diagnostics, model/snapshot/config pins, per-request
latency/token counts, VRAM recovery và native auditor vào runner phiên bản
riêng. Guard sidecar là bằng chứng cấu trúc, không tự xác thực HF inference.
Auditor document v1 chỉ kiểm CDOC và bảy level: không tái sử dụng nguyên trạng
để chứng nhận 112 khóa variant. Giữ metric startup, generation, gate, tool và
end-to-end riêng; báo cả failure/timeout thay vì chỉ ca successful.

Sau đó kiểm exact archive/expanded offline package, source GitHub, quota/private
mounts trước Kaggle. Không mặc định 112 ca vừa một notebook từ timing cũ; lịch
shard/native timeout phải được khóa trước dispatch. Không cần account mới.
Phase 5 vẫn chưa accepted; aggregate 4/7≈57% không đổi chỉ vì thêm CPU tests.

[Contract](../architecture/phase5_grouped_runner_v1_contract.md) ·
[Handoff](../../knowledge/grouped_runner_v1.md) ·
[Sổ notebook/Dataset](../../knowledge/kaggle_resources.md).
