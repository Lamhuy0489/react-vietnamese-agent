# Trạng thái hiện tại

Cập nhật: 2026-09-14. **Phase 5 đang làm, chưa nghiệm thu.**
Phase 1, clean_v1.1 Phase 2, adversarial_v2 Phase 3 và Phase 4 đã accepted theo
phạm vi/owner waiver trong [phase status](../docs/project/phase_status.md).

## Công việc hiện hành

Native grouped v2 đã ghép (source `3486dbf`) và preflight offline đạt; chưa load model, chưa submit
Kaggle. Xem [báo cáo native](../docs/evaluation/phase5_grouped_native_v2_report.md).

[grouped Dev runner/checkpoint v1](grouped_runner_v1.md), source `354b75b`:
27 focused tests đạt/130,62s; 112 khóa riêng biệt trên tám shard, 106 tool calls,
154 synthetic guard responses, 192 workers GRACEFUL/reaped. Resume không trùng
ca; ca terminal lỗi được giữ nguyên. Đây là scripted CPU, không phải LLM quality.

Full QA **3.055 pass/1 skip/973,70s**; setup/Ruff/mypy381/knowledge đạt.
537 source/1.783 raw/169 data hashes kiểm lại khớp;
[receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json) đã chốt.
Output `results/phase5_grouped_runner_v1_cpu01` đã đóng, không còn QA đang chạy.
Không GPU job mới, không mở Test/private oracle, không đổi benchmark.

## Đã chốt và dùng làm nền

- [SQL scope v5/runtime v10](sql_scope_v5.md), source `3667529`:
  3.028 pass/1 skip; 531 source/463 raw/169 data hashes khớp.
- [Public Dev catalog/resource scope v4](resource_scope_v4.md) và
  [native diagnostics CPU](guard_diagnostics_v1.md) đã kiểm; không chạy lại.
- [Native document diagnostic v1](document_diagnostic_v1.md) đã COMPLETE/audit:
  A0/A1 completed; A2–A6 model_error do guard PRE INVALID_OUTPUT. 8 GRACEFUL/
  4 TERMINATE, 12 reaped. Không retry để đổi kết quả; đây chưa phải guard quality.

## Việc còn thiếu

Native grouped adapter/observer/VRAM auditor → exact offline Kaggle package →
grouped Dev quality/timing/lifecycle → broader scope assessment và Phase 5 freeze.
Aggregate **4/7≈57%** giữ nguyên; không phải phần trăm thời gian/công sức.
Sáu ROWLIST cases A4–A6 chưa được đọc do thiếu explicit column grant; không tự
cấp quyền từ oracle hoặc sửa data. Không chuyển Phase 6/7/Test.

[Bước tiếp và quyền cần thiết](handoff.md) · [Tiến độ chi tiết](phase5_progress.md) ·
[Sổ notebook/Dataset](kaggle_resources.md) · [Chỉ mục](README.md).

[Lịch sử trước khi thu gọn](history_20260914_grouped_runner_current_status.md)
được giữ nguyên; các câu “đang làm” trong đó không mô tả job hiện tại.
