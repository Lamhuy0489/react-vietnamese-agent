# Phase 5 — phần còn phải đóng theo kế hoạch

Cập nhật2026-09-20, đối chiếu `plan/phase5.md` mụcCXXVI(20DoD) và
[trạng thái chính thức](../docs/project/phase_status.md).
Đây là hàng đợi phần còn mở, không phải tuyên bố mọi DoD khác đã được nghiệm thu.
Chỉ số4/7≈57% là nhóm acceptance trong [progress](phase5_progress.md).

Constrained GPU v1 COMPLETE/audit, source `0d4e82f`: 4 completed/8 valid guard
responses; 8 reaped/4 recovered, nhưng 4 TERMINATE/4 GRACEFUL. Không còn job pending.
[Report hiện hành](../docs/evaluation/phase5_constrained_gpu_v1_report.md).
Host auditor đã qua 59 tests mới; không submit lại notebook đã xong.
CPU post-serve controls đã đóng: 18 workers/6 modes×3 repeats, đủ reaped,
hai audits khớp. [Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md).
Observer exit milestones đã qua CPU gate: 18/18 reaped, 53 tests mới, 666 focused
+ 149 integration đạt. [Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md).
Chưa xác định root cause GPU; còn native runner/receipt join và exact package riêng.

| Phần cần hoàn thiện | Bằng chứng còn thiếu / bước cụ thể |
|---|---|
| DoD-5: A2 end-to-end, structured output ổn định | Constrained GPU v1 COMPLETE/audit: 4 completed/8 valid guard responses, không backend error; native source/policy/attention/count joins đạt. Chỉ 4 diagnostic tasks, còn representative guard quality/utility. V1 CPU failure và bare-JSON 2/6 valid giữ nguyên; không strip/repair parser hoặc suy diễn toàn bộ 30 lỗi baseline. |
| Lifecycle GPU của runtime | Baseline192reaped/13TERMINATE; observer8/3; bare-JSON8/1; constrained8/4. CPU controls và opt-in exit observer đã qua, nhưng chưa xác định native teardown cause. Cần nối native PID/role/task receipts và exact package riêng; chưa tăng grace2s. |
| DoD-9/13/14/16: A6 provenance, egress/final sink, unknown origin | Có bounded CPU controls; còn đối chiếu phạm vi hỗ trợ và các trường hợp ngoài phạm vi. Không đồng nhất “có sensitive artifact” với payload xuất ra. |
| DoD-15: benign utility đại diện | Native112ca chưa chứng minh utility: có ca không gọi tool, SQL sai bảng, thiếu column grant. Kiểm từ user instruction và public tool/catalog; lưu cả successful/denied/error. |
| Grouped Dev differential | Lịch112ca đã audit; cần đo và giải thích các khác biệt A0–A6 khi guard/lifecycle đủ ổn định, theo protocol đã khóa và giữ nguyên thất bại cũ. |
| DoD-20: formal freeze và báo cáo nghiệm thu | Chỉ khóa rules/guard/model/config/architecture khi các gate trên có bằng chứng. Lập mapping20DoD→tests/receipts/giới hạn trước chuyển phase. |

Mục đầu đã có [kết quả âm của bare-JSON candidate](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
Notebookv1 vẫn ERROR do auditCLI nhưng4inferences đã recovery-audit đủ; không
submit bare-json-v2 để lặp lại. Bước tiếp là kiểm chứng native adapter composition,
candidate constrained GPU v1 đã terminal/audit; còn representative quality/lifecycle.
[Finite-language CPU evidence](../docs/evaluation/phase5_guard_token_language_v1_report.md)
đã hoàn tất; còn các native gates trong contract. Tiếp tục giữ separation/Test/mock-side-effect invariants; không dùng
Test để lựa chọn phương án sửa. Formal freeze vẫn chưa đủ bằng chứng.
