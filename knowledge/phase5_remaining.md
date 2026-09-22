# Phase 5 — phần còn phải đóng theo kế hoạch

Cập nhật2026-09-22, đối chiếu `plan/phase5.md` mụcCXXVI(20DoD) và
[trạng thái chính thức](../docs/project/phase_status.md).
Đây là hàng đợi phần còn mở, không phải tuyên bố mọi DoD khác đã được nghiệm thu.
Chỉ số4/7≈57% là nhóm acceptance trong [progress](phase5_progress.md).

Candidate clausev3/runtimev12 đã qua78/78CPU controls, gồm26compound cases:
[report](../docs/evaluation/phase5_clause_candidate_v1_report.md).
CumulativeA1–A6 và boundedA0 parity có tests;6Dev destination gaps đã đóng ở parser.
Không coi destination permission là sensitive-payload permission. Workload32caA2/A6
vẫn dispatch=false. Constrained ExitPair/runtime/auditor đã qua12CPUtasks:
[paired report](../docs/evaluation/phase5_clause_pair_v1_report.md).
Runner32Dev/checkpoint đã qua32CPUtasks, native artifact adapter đã có:
[Dev32 report](../docs/evaluation/phase5_clause_dev32_v1_report.md).
Source admission/launcher và exact development package đã đạt:
[package report](../docs/evaluation/phase5_clause_dev_package_v1_report.md).
Còn source freeze,committed rehearsal/independent release validation và một
native32Dev run. DevelopmentHF vẫn khóa. Chưa representative quality/utility
hoặc lifecycle reliability.

ExitPair GPU v1 COMPLETE/audit (2026-09-21 07:28:29 UTC), actual
`huylmhuhu/react-vn-exit-milestones-v1`, source `6d039e2`:4completed/8validguard,
8GRACEFUL/0forced; lỗi cũ không tái hiện, chưa root cause/fix. Không job pending.
[Report/terminal/audit](../docs/evaluation/phase5_exit_gpu_v1_report.md).
Constrained GPU v1 COMPLETE/audit, source `0d4e82f`: 4 completed/8 valid guard
responses; 8 reaped/4 recovered, nhưng 4 TERMINATE/4 GRACEFUL. Không submit lại job cũ.
[Report hiện hành](../docs/evaluation/phase5_constrained_gpu_v1_report.md).
Host auditor đã qua 59 tests mới; không submit lại notebook đã xong.
CPU post-serve controls đã đóng: 18 workers/6 modes×3 repeats, đủ reaped,
hai audits khớp. [Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md).
Observer exit milestones đã qua CPU gate: 18/18 reaped, 53 tests mới, 666 focused
+ 149 integration đạt. [Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md).
ExitPair/native runner/receipt join đã triển khai và qua 54 tests chuyên biệt,
[report](../docs/evaluation/phase5_exit_pair_cpu_v1_report.md). Chưa xác định GPU
root cause. Exact notebook/package development + committed release hai layout
đã đạt; native exit-milestone experiment đã terminal/audit, không submit lại.

| Phần cần hoàn thiện | Bằng chứng còn thiếu / bước cụ thể |
|---|---|
| DoD-5: A2 end-to-end, structured output ổn định | Constrained GPU v1 COMPLETE/audit: 4 completed/8 valid guard responses, không backend error; native source/policy/attention/count joins đạt. Chỉ 4 diagnostic tasks, còn representative guard quality/utility. V1 CPU failure và bare-JSON 2/6 valid giữ nguyên; không strip/repair parser hoặc suy diễn toàn bộ 30 lỗi baseline. |
| Lifecycle GPU của runtime | Baseline192reaped/13TERMINATE; observer8/3; bare-JSON8/1; constrained8/4; ExitPair8/0. Native milestones đã audited, lỗi không tái hiện nên chưa cause/fix/reliability. Muốn so sánh cần khóa prospective paired repeat/order budget riêng, không rerun v1 hoặc tăng grace2s theo kết quả. |
| DoD-9/13/14/16: A6 provenance, egress/final sink, unknown origin | Có bounded CPU controls; còn đối chiếu phạm vi hỗ trợ và các trường hợp ngoài phạm vi. Không đồng nhất “có sensitive artifact” với payload xuất ra. |
| DoD-15: benign utility đại diện | V12 đạt78CPUcontrols, paired12tasks và Dev32 CPU runner. Sáu Dev destination gaps đóng ở parser. Còn native release/launcher/package và quality/utility; native112ca cũ vẫn không phải utility proof. Giữ mọi denied/error. |
| Grouped Dev differential | Lịch112ca đã audit; cần đo và giải thích các khác biệt A0–A6 khi guard/lifecycle đủ ổn định, theo protocol đã khóa và giữ nguyên thất bại cũ. |
| DoD-20: formal freeze và báo cáo nghiệm thu | Chỉ khóa rules/guard/model/config/architecture khi các gate trên có bằng chứng. Lập mapping20DoD→tests/receipts/giới hạn trước chuyển phase. |

Mục đầu đã có [kết quả âm của bare-JSON candidate](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
Notebookv1 vẫn ERROR do auditCLI nhưng4inferences đã recovery-audit đủ; không
submit bare-json-v2 để lặp lại. Bước tiếp là kiểm chứng native adapter composition,
candidate constrained GPU v1 đã terminal/audit; còn representative quality/lifecycle.
[Finite-language CPU evidence](../docs/evaluation/phase5_guard_token_language_v1_report.md)
đã hoàn tất; còn các native gates trong contract. Tiếp tục giữ separation/Test/mock-side-effect invariants; không dùng
Test để lựa chọn phương án sửa. Formal freeze vẫn chưa đủ bằng chứng.
