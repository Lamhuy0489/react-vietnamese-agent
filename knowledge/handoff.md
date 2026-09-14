# Bàn giao phiên làm việc

Cập nhật: 2026-09-14. Chỉ dẫn hiện hành; lịch sử không thay thế mục này.

## Đang làm

Đã chốt [grouped Dev runner/checkpoint v1](grouped_runner_v1.md), source `354b75b`.
27 focused tests đạt/130,62s; 112 ca/8 shards, resume/tampering/failure retention
đã kiểm. Full QA **3.055 pass/1 skip/973,70s**; setup/Ruff/mypy381/knowledge đạt.
537 source/1.783 raw/169 data hashes kiểm lại khớp; selected receipt đã lưu.
Output `results/phase5_grouped_runner_v1_cpu01` đã đóng, không còn QA hoặc GPU job
mới. Không chạy trùng, sửa source đã khóa hoặc ghi thêm raw. Việc tiếp theo là
native grouped adapter/auditor, không phải chạy lại các mốc CPU đã hoàn tất.

## Bước tiếp theo

Native v2 source `3486dbf` đã ghép; offline overlay preflight đạt compile/hash/path checks,
`actual_model_loads=0`, `native_submission_ready=false`. Chưa submit Kaggle.

1. Ghép native runner phiên bản riêng: A0/A1 agent-only; A2–A6 dùng
   `native_guard_diagnostics_v1.native_pair`, runtime v10 và catalog public Dev.
   Identity cần model/snapshot/inventory/config pins, 112 variant+level keys và
   tám shards đã chọn trước. Không đổi nhãn CPU thành native.
2. Ghép auditor native cho từng variant: metrics/policy/attention/guard sidecar
   nối PID/request/runtime, baseline/recovery và timing. Auditor document v1 chỉ
   biết CDOC/bảy level, không chứng nhận grouped Dev nguyên trạng. Giữ cả failed
   attempts, không biến classification ERROR thành successful guard path.
3. Freeze native run/package, kiểm exact archive/expanded offline mounts và
   source đã push GitHub, rồi mới submit Kaggle. Khóa timeout/schedule trước chạy;
   không mặc định 112 ca vừa một notebook. Ghi URL/version thật sau submission.
4. Báo matched Dev guard structured-output/Pre/Post, lỗi, startup/generation/
   end-to-end timing và lifecycle; không retry ngữ nghĩa hoặc mở Test để tuning.

Pending access: không cần tài khoản mới. Owner Kaggle thực tế `huylmhuhu`;
phải kiểm live quyền/quota/private mounts trước submission. Snapshot quota cũ
trong sổ tài nguyên không phải reservation. Không cycling credentials hoặc làm
public tài nguyên private. Tác vụ model nặng chỉ chạy Kaggle.

## Bằng chứng

- [Báo cáo runner hiện hành](../docs/evaluation/phase5_grouped_runner_v1_report.md).
- [Grouped CPU receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json),
  SHA-256 `6233354ab9445569d83c020f4b3a4f1f4d65bcd81fec4a85bea53ea80243f9f3`.
- [Native v2 preflight](../docs/evaluation/phase5_grouped_native_v2_report.md) và
  [receipt](../build/kaggle/phase5_grouped_native_v2_preflight01/preflight_receipt.json).
- [SQL CPU prerequisite](../experiments/manifests/phase5_sql_scope_v5_cpu01.json),
  source `3667529`: 3.028 pass/1 skip, 531 source/463 raw/169 data hashes khớp.
  Output đã đóng, không chạy trùng/ghi thêm.
- [Native diagnostics CPU](../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json)
  đã chốt; chưa chứng nhận observer chạy native GPU.
- [Native document diagnostic](../experiments/manifests/phase5_document_gpu_v1_audit01.json):
  COMPLETE/audit, A2–A6 INVALID_OUTPUT; không retry. [Sổ link](kaggle_resources.md).
- [Lịch sử nguyên bản trước thu gọn](history_20260914_grouped_runner_handoff.md);
  không dùng câu “đang làm” cũ để quyết định chạy lại.

## Giới hạn

Phase 5 chưa accepted, aggregate 4/7≈57%. CPU scripted/fake guard không đo
utility/ASR/FPR. Public Dev ROWLIST thiếu explicit column grants nên sáu ca
A4–A6 không đọc được; giữ kết quả, không sửa data/cấp quyền từ oracle.
Không Test/private GT hoặc mock network I/O. Entitlement v1 receipt có hash
pytest.log sai: giữ lịch sử, không lấy valid=true làm nghiệm thu.

Giữ nguyên thay đổi của người dùng ngoài phạm vi: `plan/phase6.md`–`phase9.md`,
`docs/BAO_CAO_TIEN_DO_DO_AN.md`/PDF và `docs/figures/`; không stage/xóa.
