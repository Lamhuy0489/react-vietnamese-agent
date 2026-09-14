# Bàn giao phiên làm việc

Cập nhật: 2026-09-14. Chỉ dẫn hiện hành; lịch sử không thay thế mục này.

## Đang làm

Package v3 source `0d86536` đã chạy xong exact preflight; mỗi layout archive và
expanded đạt 8 tools, 21 clean Dummy, 112 grouped stub/resume, 128 module origins.
4.357 hashes recheck khớp, 4.360 files secret scan/0 matches. Xem
[report v3](../docs/evaluation/phase5_grouped_package_v3_report.md) và
[preflight receipt](../experiments/manifests/phase5_grouped_package_v3_preflight01.json).
**Full QA đã đạt 3.113 pass/1 skip/1.060,05s** tại
`results/phase5_grouped_package_v3_qa01`; setup/Ruff/mypy392/knowledge đạt.
555 source/7 raw/169 data hashes kiểm lại khớp; output đã đóng, không chạy lại.
[QA receipt](../experiments/manifests/phase5_grouped_package_v3_cpu01.json).
Chưa push source/GPU submission v3. Quota đúng owner: 29,02h; Dataset private ready/v1,
model Qwen v1 đọc metadata được. Đây là snapshot, không phải reservation.

Mốc CPU nền trước đó (đã đóng):

Đã chốt [grouped Dev runner/checkpoint v1](grouped_runner_v1.md), source `354b75b`.
27 focused tests đạt/130,62s; 112 ca/8 shards, resume/tampering/failure retention
đã kiểm. Full QA **3.055 pass/1 skip/973,70s**; setup/Ruff/mypy381/knowledge đạt.
537 source/1.783 raw/169 data hashes kiểm lại khớp; selected receipt đã lưu.
Output `results/phase5_grouped_runner_v1_cpu01` đã đóng. Không chạy trùng, sửa
source đã khóa hoặc ghi thêm raw của mốc này.

## Bước tiếp theo

Native v2 source `3486dbf` đã ghép. **Thu hồi kết luận package/import isolation**
của hai receipt cũ: overlay nằm dưới `configs`, editable install đã cung cấp
module từ repo. Giữ nguyên raw/receipt. Xem phần đính chính trong báo cáo native.
Package v3 preflight đã đạt; 14 regression tests đạt, Ruff/mypy392 đạt trước freeze.
Chưa có native submission mới.

1. CPU QA và preflight đã hoàn tất; không chạy lại. Selected QA receipt đính chính
   scope Test của full historical suite, không coi flag cũ là filesystem audit.
2. Kiểm hash receipt/source/raw, push GitHub; kiểm live owner `huylmhuhu`,
   Dataset/model private và quota. `kaggle1.json` là owner này; chọn owner explicit,
   không dùng default credential path rồi suy đoán tài khoản. Status document v1
   đã đọc lại thành công: COMPLETE; không phải thiếu quyền người dùng.
3. Theo [contract v3](../docs/architecture/phase5_grouped_package_v3_contract.md),
   submit shard 0/14 ca trước, timeout 14.400s, không chạy trùng/semantic retry.
   Audit native terminal artifacts trước khi chạy tiếp bảy shard còn lại.
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
  [receipt](../experiments/manifests/phase5_grouped_native_v2_preflight01.json).
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
