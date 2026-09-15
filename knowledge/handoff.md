# Bàn giao phiên làm việc

Cập nhật: 2026-09-16. Phase 5 đang làm, chưa nghiệm thu.

## Đang làm

Đã đóng audit của bare-JSON candidate; [báo cáo và receipts](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
Notebook v1/ID134511636 `huylmhuhu/react-vn-guard-bare-json-v1` vẫn ERROR:
4 inference checkpoints đã xong, chỉ audit CLI cuối thiếu --condition.
Local recovery xác thực source `f7492fa`, 155 source pins, 157 raw/2 remote;
hai audits và summary byte-identical. Không chạy lại model/GPU.

Kết quả: 4/4 model_error; 6 guard responses có 2 valid và 4 fenced syntax errors;
thêm 2 POST backend failures không response. 4 tools, 8 workers reaped
(7 graceful/1 terminate), 4 VRAM recoveries. Prompt-only chưa cải thiện format.
Tổng task984,907s/startup951,355s; timing chi tiết trong report.
Phase5 vẫn 4/7≈57% acceptance groups; không phải tỷ lệ giờ công.

Đã sửa auditor phân biệt CPU/HF, yêu cầu đủ native metadata và đúng4task.
Đã bổ sung recovery kiểm source Git/archive/bootstrap/native metrics/telemetry.
Không sửa frozen runtime, parser, prompt hoặc inference outputs.

## Bước tiếp theo

Chuẩn bị thiết kế constrained-output thành candidate/protocol riêng, trước hết
CPU synthetic controls và tiêu chí native preregistered; chưa triển khai hay gửi.
Không strip/repair JSON hoặc chọn cấu hình bằng Test. Khảo sát shutdown wait bằng
synthetic lifecycle riêng, không gộp thay đổi timeout với prompt/model.
Đối chiếu [các DoD còn thiếu](phase5_remaining.md) trước formal freeze.

**Không submit gói bare-json-v2 đã chuẩn bị**: nó không cần thiết cho việc audit
v1 và sẽ lặp lại4 inference đã hoàn tất. Preflight02 là chứng cứ CPU lịch sử,
không phải native acceptance. Không resume/retry các semantic failures đã chốt.

## Bằng chứng

- Raw bất biến: `results/phase5_guard_bare_json_terminal_error01/raw`.
- Live observation/source: `results/phase5_guard_bare_json_terminal04`;
  kiểm 2026-09-15 17:10:52UTC, private/version1/ERROR.
- Audits: `results/phase5_guard_bare_json_recovery_audit01` và `..._audit02`.
- QA: `results/phase5_guard_bare_json_recovery_qa01`; focused suite,
  87 tests/49,99s, setup/Ruff/mypy418/knowledge đạt;
  [receipt](../experiments/manifests/phase5_guard_bare_json_recovered_qa01.json).
  175 baseline pins nguyên, scan184files/0credentials. Không full pytest chứa
  Test-assigned authoring fixtures.
- [Notebook/Dataset directory](kaggle_resources.md), [tiến độ](phase5_progress.md).
- [Bàn giao lịch sử](phase5_handoff_history_20260915.md); các lệnh submit ở đó đã cũ.

## Giới hạn

Không cần tài khoản mới; không có inference pending trong lịch đã audit.
Phải live-check quota/private mounts trước một GPU experiment mới được chuẩn bị.
GitHub `Lamhuy0489` khác owner Kaggle `huylmhuhu`; không chia sẻ credential
trong memory, không chuyển private resource sang public.
Giữ nguyên thay đổi riêng ở plan/phase6–9 và docs/BAO_CAO_TIEN_DO_DO_AN.*,
docs/figures/. Không đưa development memory vào benchmark prompts.
