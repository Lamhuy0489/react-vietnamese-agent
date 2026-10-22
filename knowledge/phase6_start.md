# Bắt đầu Phase 6 trong phiên ngày mai

Cập nhật: 2026-10-02. Owner yêu cầu lưu thông số, dọn file tạm và chuẩn bị tiếp tục
Phase 6 ngày mai (dự kiến 2026-10-03). Phase 5 đã accepted; hôm nay chỉ chuẩn bị
bàn giao, chưa triển khai hoặc tuyên bố nghiệm thu Phase 6.

## Đầu vào cần đọc

1. `AGENTS.md`, [phase status](../docs/project/phase_status.md),
   [current status](current_status.md), [handoff](handoff.md).
2. [Research contract](../docs/project/research_contract.md) và
   [invariants](../docs/project/invariants.md).
3. [Kế hoạch Phase 6](../plan/phase6.md), nhất là ngày 1 và 15 DoD.
4. [Thông số đã khóa](phase5_parameters.md) và
   [bằng chứng Phase 5](../experiments/manifests/phase5_completion_20261002.json).

## Việc đầu tiên, có đầu ra cụ thể

Kiểm kê các scorer hiện có để tái sử dụng, chưa viết lại runtime hoặc defense.
Đầu mối gồm `scripts/evaluate_clean_v11_dev.py`,
`scripts/evaluate_structured_api_dev_v1.py`,
`scripts/evaluate_phase5_native_observations_v2.py`,
`scripts/evaluate_phase5_native_closure_controls_v1.py` và
`src/react_agent/validation/pilot_statistics.py`. Scorer smoke chuyên biệt không
mặc nhiên là evaluator tổng quát đã được chấp nhận.

Theo ngày 1 trong plan, viết và thống nhất `docs/metrics_spec.md` trước khi code:
TSR, ToolSelAcc, ArgAcc, SeqAcc, StepOverhead, ErrRecovery; ASR, FPR, BlockRate,
PVR proposed, PVR executed và STSR. Với từng metric phải ghi tử số, mẫu số,
điều kiện eligibility/exposure, missing/error và cách xử lý trace không hợp lệ.
Tách proposed khỏi executed; completed khỏi task success; classifier flag khỏi
runtime block. Không silently loại lỗi model khỏi denominator hoặc coi mất output
là an toàn. Không đổi ý nghĩa metric sau khi nhìn kết quả Test.

Sau đó chốt schema per-task score và aggregate, golden synthetic cases, phép
chấm lại saved traces không gọi model; mới nối capability/security/robustness,
statistics-ready output, batch/resume và human-validation protocol theo 15 DoD.
Evaluator phải frozen trước Test; không lấy waiver QA cũ làm bằng chứng đã có
human validation của Phase 6. Final experiments thuộc Phase 7.

## Có cần bật hai API ngay không?

Không. Đọc code, thống nhất metric, golden tests và chấm lại trace có thể làm
local CPU. Chỉ bật API khi đã có phạm vi Dev inference mới cần thiết. Khi đó kiểm
health/model/prompt/worker boot mới; giữ key trong ignored local files, không
chép vào ghi chú. Không resume các run closure84 hoặc guard80 đã terminal.

Không có job tự động cho ngày mai được tạo. Mở lại workspace và nhắn:

> Tiếp tục Phase 6 từ knowledge/phase6_start.md và handoff.md. Trước hết rà các
> scorer và chốt metrics_spec cùng denominator; dùng Dev/synthetic, giữ Test khóa.

## Dữ liệu và trạng thái cần bảo toàn

Native closure72/84 completed,12model_error; guard TP21/FN19/FP5/TN35; C6 false
block và provenance giới hạn vẫn là kết quả của baseline. Không sửa defense hay
retry semantic failure để cải thiện bảng chấm. Runtime source419938b đã freeze;
report/diagnostic/knowledge mới vẫn local, chưa commit/push.
