# Trạng thái hiện tại

Cập nhật 2026-09-16. **Phase 5 đang làm: 4/7 ≈ 57% nhóm nghiệm thu**,
không phải phần trăm công sức hoặc số dòng mã. Phase 1–4 đã accepted theo
[trạng thái chính thức](../docs/project/phase_status.md); Test vẫn khóa.

## Kết quả mới nhất

**Runner/checkpoint và native-auditor join đã nối xong, QA đạt.**
[Report](../docs/evaluation/phase5_constrained_probe_v1_report.md).
32 tests mới qua; controls02 có 4 completed/4 lỗi chủ động được giữ nguyên,
resume không chạy lại ca terminal. Đây là synthetic CPU, chưa gói Kaggle/GPU.
480 focused + 105 integration tests đạt; setup/Ruff/mypy443/knowledge đạt.
142 active + 86 prior-native + 175 baseline source pins nguyên.
Pre-commit working-tree source hashes được lưu; gom một commit sau khi QA đạt.

Nền host/runtime trước:

**Host classifier/cache đã nối với paired runtime và read-only auditor riêng.**
[Report](../docs/evaluation/phase5_constrained_host_v1_report.md), source `e04cd8d`.
37 tests mới qua, gồm spawned CALC/DOC × A2/A6, cache không thêm IPC, lỗi worker,
đổi identity và thay receipt bị chặn. Đây là synthetic CPU, chưa production guard.
Final QA: 438 focused + 90 integration tests đạt; setup/Ruff/mypy437/knowledge đạt.
142 active + 86 prior-native + 175 baseline source pins nguyên. Không có GPU job mới.

Mốc native CPU trước, giữ nguyên:

**Native constrained-generation CPU v2 COMPLETE và audit đạt.**
[Report và bằng chứng](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md).
Notebook `huylmhuhu/react-vn-constrained-generate-cpu-v2`, version 1/ID 134579648,
source `b4ae0f7`; sau download xác minh COMPLETE/private/source khớp lúc
2026-09-16 08:25:13 UTC. Không còn job pending trong lịch CPU này.

Hai ca sinh thật trên tiny random Qwen đều hoàn tất JSON + EOS, mỗi ca 28 token;
0,2362s và 0,1462s. ForcedBOS bị từ chối trước forward; interrupt truyền ra và
khôi phục hook. Cả bốn ca khôi phục đúng; không pretrained weights/GPU/quality.
Hai audits byte-identical: 142 source pins, 25 raw và 2 remote files xác minh.
401 focused tests đạt / 21,87s; setup/Ruff/mypy 433/knowledge đạt.
22 tests mới kiểm auditor. Không full pytest vì có Test-assigned authoring fixtures.

CPU v1 ERROR và sáu lỗi int/float trong policy pin được giữ nguyên lịch sử,
không thay thất bại cũ bằng v2. V2 chỉ sửa expected typed policy identity,
không đổi numerical decoding/prompt/model/parser.

## Việc đang nối tiếp

Worker composition và host classifier/cache/runtime join đã có CPU tests.
Native wrapper đã nối constraint với policy/attention/HF metrics và runner có
checkpoint identity riêng. **Còn notebook/bootstrap, exact-package rehearsal và
remote release authentication**, rồi thực nghiệm GPU theo protocol riêng.
Native CPU pass không chứng minh production guard 1.5B,
CUDA attention, chất lượng phân loại, benign utility hoặc graceful lifecycle.

Giữ baseline 175 source pins, native tokenizer 86 pins và package CPU 142 pins.
Không submit lại bare-json-v2, CPU v1/v2 hoặc retry semantic failures.
Không chuyển Phase 6/7 hoặc mở Test. Không cần tài khoản mới lúc này.

## Nền đã đóng

- Grouped native: đủ 112/112 ca đã audit; 82 completed/30 model_error,
  55 valid/30 malformed guard responses; 192 workers reaped, còn 13 forced shutdowns.
  [Báo cáo tổng](../docs/evaluation/phase5_grouped_v3_complete_report.md).
- Bare-JSON: 4 model_error, 2/6 valid guard responses; prompt-only chưa khắc phục.
  [Kết quả âm](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
- Tokenizer native: 3069 values, max 36 tokens gồm EOS, 248 mask checks.
  [Nền CPU](../docs/evaluation/phase5_guard_language_native_v1_run.md).
- [SQL scope](sql_scope_v5.md), [public resource scope](resource_scope_v4.md),
  [grouped runner](grouped_runner_v1.md) giữ nguyên.

[Bàn giao](handoff.md) · [DoD còn thiếu](phase5_remaining.md) ·
[Sổ notebook/Dataset](kaggle_resources.md) · [Chỉ mục](README.md).
[Lịch sử trước mốc CPU v2](history_20260916_constrained_cpu.md) giữ nguyên;
các câu “đang chạy/chuẩn bị” trong lịch sử không phải trạng thái hiện tại.
