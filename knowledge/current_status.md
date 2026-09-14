# Trạng thái hiện tại

Cập nhật: 2026-09-14. **Phase 5 đang làm, chưa nghiệm thu.**
Phase 1, clean_v1.1 Phase 2, adversarial_v2 Phase 3 và Phase 4 đã accepted theo
phạm vi/owner waiver trong [phase status](../docs/project/phase_status.md).

## Công việc hiện hành

Native grouped v2 đã ghép (source `3486dbf`), nhưng bằng chứng package/import cũ
bị false positive do root `configs` và editable install. Đã đính chính trong
[báo cáo native](../docs/evaluation/phase5_grouped_native_v2_report.md).
[Package v3](../docs/evaluation/phase5_grouped_package_v3_report.md), source `0d86536`,
đã đạt hai layout/fresh venv: 8 tools + 21 clean Dummy + 112 grouped stub/resume
mỗi layout. 4.357 hashes recheck khớp. Full QA **3.113 pass/1 skip/1.060,05s**,
setup/Ruff/mypy392/knowledge đạt; 555 source/7 raw/169 data hashes khớp.
[QA receipt](../experiments/manifests/phase5_grouped_package_v3_cpu01.json).
Output `results/phase5_grouped_package_v3_qa01` đã đóng; không chạy lại.
Source/evidence đã push `93dc9a2`; **native shard 0 v1 RUNNING** trên
[Kaggle](https://www.kaggle.com/code/huylmhuhu/react-vn-grouped-dev-v3-shard-0).
[Submission](../experiments/manifests/phase5_grouped_v3_s0_submission01.json):
14 ca, private/offline T4x2, timeout 14.400s. Source remote hash khớp; chưa có
kết quả terminal, không chạy trùng hoặc submit bảy shard còn lại trước audit.

Kiểm gần nhất **2026-09-14 14:59:33 UTC: RUNNING, failureMessage=null**;
Kaggle chưa trả output/log tại lần đọc trước đó. Bộ kiểm terminal local đã sẵn
sàng, 32 focused tests đạt; [audit notes](../docs/evaluation/phase5_grouped_gpu_v3_audit_notes.md).

[grouped Dev runner/checkpoint v1](grouped_runner_v1.md), source `354b75b`:
27 focused tests đạt/130,62s; 112 khóa riêng biệt trên tám shard, 106 tool calls,
154 synthetic guard responses, 192 workers GRACEFUL/reaped. Resume không trùng
ca; ca terminal lỗi được giữ nguyên. Đây là scripted CPU, không phải LLM quality.

Full QA **3.055 pass/1 skip/973,70s**; setup/Ruff/mypy381/knowledge đạt.
537 source/1.783 raw/169 data hashes kiểm lại khớp;
[receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json) đã chốt.
Output nền `results/phase5_grouped_runner_v1_cpu01` đã đóng; không chạy lại mốc này.
Mốc CPU cũ không có GPU; job mới duy nhất là shard 0 nêu trên. Không đổi benchmark.

## Đã chốt và dùng làm nền

- [SQL scope v5/runtime v10](sql_scope_v5.md), source `3667529`:
  3.028 pass/1 skip; 531 source/463 raw/169 data hashes khớp.
- [Public Dev catalog/resource scope v4](resource_scope_v4.md) và
  [native diagnostics CPU](guard_diagnostics_v1.md) đã kiểm; không chạy lại.
- [Native document diagnostic v1](document_diagnostic_v1.md) đã COMPLETE/audit:
  A0/A1 completed; A2–A6 model_error do guard PRE INVALID_OUTPUT. 8 GRACEFUL/
  4 TERMINATE, 12 reaped. Không retry để đổi kết quả; đây chưa phải guard quality.

## Việc còn thiếu

Native grouped adapter/auditor v2 đã có; còn exact offline Kaggle package + full QA →
grouped Dev quality/timing/lifecycle → broader scope assessment và Phase 5 freeze.
Aggregate **4/7≈57%** giữ nguyên; không phải phần trăm thời gian/công sức.
Sáu ROWLIST cases A4–A6 chưa được đọc do thiếu explicit column grant; không tự
cấp quyền từ oracle hoặc sửa data. Không chuyển Phase 6/7/Test.

[Bước tiếp và quyền cần thiết](handoff.md) · [Tiến độ chi tiết](phase5_progress.md) ·
[Sổ notebook/Dataset](kaggle_resources.md) · [Chỉ mục](README.md).

[Lịch sử trước khi thu gọn](history_20260914_grouped_runner_current_status.md)
được giữ nguyên; các câu “đang làm” trong đó không mô tả job hiện tại.
