# Phase 5 — phần còn phải đóng theo kế hoạch

> **Đã đóng2026-10-02:** Phase5accepted20/20DoD theo [closure dossier](../docs/evaluation/phase5_completion_20261002.md).
> Các backlog/NO_GO bên dưới được giữ theo thời điểm lịch sử,không là trạng thái hiện hành.

> **Chỉ mục lịch sử:** danh sách này giữ lại backlog và bằng chứng cũ để audit.
> Trạng thái và next action hiện hành nằm ở [`current_status.md`](current_status.md),
> [`handoff.md`](handoff.md) và [direction audit 2026-09-29](../docs/evaluation/phase5_direction_audit_20260929.md).
> Không dùng các mục cũ để mở thêm nhánh triển khai.

## Rà tiến độ và hướng hoàn thiện — 2026-09-27

[Tiến độ và lộ trình hoàn thiện qua API](../docs/evaluation/project_status_api_20260927.md): Phase1–4 accepted, Phase5 vẫn4/7nhóm nghiệm thu;
không dùng57% cho toàn đồ án. API pair đã qua technical smoke, chưa native
fullA6/guard quality. Có thể tiếp tục bằng local runner + Kaggle inference;
không cần tăng kích thước model hoặc fine-tune để đáp ứng contract.
RQ1 vẫn cần3task backbones, có thể chạy lần lượt; một agent + một guard chưa
đủ ba model. RQ2 giữ task backbone/decoding cố định quaA0–A6, A0 không guard.

**Bước cụ thể kế tiếp:** manifest + runner Dev nhỏ có checkpoint/fault QA,
đo clean utility và guard attack/benign riêng; rồi nối candidate A6 với
Pre/Post/Final và cumulative parity. Bridge cần schemaPlan adapter riêng,
HTTP client hiện tại chỉ action/final; không coi bridge đã tích hợp qua API.
Lifecycle API cần evidence riêng; không tự đóng lỗi worker cũ từ READY.

**Bằng chứng/giới hạn:** đọc contract/20DoD/source và receipt paired smoke
đã có; không probe uptime hoặc inference mới, không Test. Không thay model
chính thức/research scope/phase acceptance. Không có access mới cần cấp cho
lượt tài liệu này; khi chạy tiếp phải kiểm health/session hiện hành. Report
và memory còn local, không commit/push trạng thái riêng.

## Bằng chứng và backlog lịch sử trước chuyển API

Dev32 v1 đã terminal ERROR trước worker start:
[failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md).
V2 correction/package/QA03 và release02 đã đạt; committed release01 bị từ chối
do host auditor cache allowlist sai. Actual
[notebook v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version1/ID135499833 đã COMPLETE, tải và
[terminal audit](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md)
cho 32/32 ca; 65/65 returned guard syntax OK, một guard TERMINATE.
Cập nhật 2026-09-23: evaluator-only [Dev scoring](../docs/evaluation/phase5_clause_dev32_scoring_v1_report.md)
đã xong, thấy một A6 benign canonical safe-action false block; [exit
diagnostic](../docs/evaluation/phase5_clause_guard_exit_diagnostic_v1_report.md)
đã xác định một TERMINATE sau Python milestones nhưng chưa root cause. Còn
prospective remedy/guard quality, lifecycle reliability và formal freeze;
không dùng v1
CPU pass hay v1 ERROR làm model quality proof.

Cập nhật 2026-09-23, đối chiếu `plan/phase5.md` mục CXXVI (20DoD) và
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
Source freeze `5a23528` và v1 committed release audit đã đạt; native32Dev v1
đã submit một lần nhưng terminal ERROR trước worker start. [V1 failure](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md)
đã audit; không resubmit v1. V2 [package report](../docs/evaluation/phase5_clause_dev_package_v2_report.md),
release02, native run và evaluator-only scoring đã hoàn tất; còn remedy
prospective, representative quality/utility và lifecycle reliability.

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
| DoD-15: benign utility đại diện | V12 đạt78CPUcontrols, paired12tasks và Dev32 native đã chấm: typed benign utility A2 4/8, A6 3/8 trên 8 families selected; một A6 canonical safe-action false block. V13/v14 proof-carrying public-field synthetic CPU là remedy prospective, chưa chứng minh Dev/model utility. Giữ mọi denied/error. |
| Grouped Dev differential | Lịch112ca đã audit; cần đo và giải thích các khác biệt A0–A6 khi guard/lifecycle đủ ổn định, theo protocol đã khóa và giữ nguyên thất bại cũ. |
| DoD-20: formal freeze và báo cáo nghiệm thu | Chỉ khóa rules/guard/model/config/architecture khi các gate trên có bằng chứng. Lập mapping20DoD→tests/receipts/giới hạn trước chuyển phase. |

Mục đầu đã có [kết quả âm của bare-JSON candidate](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md).
Notebookv1 vẫn ERROR do auditCLI nhưng4inferences đã recovery-audit đủ; không
submit bare-json-v2 để lặp lại. Bước tiếp là kiểm chứng native adapter composition,
candidate constrained GPU v1 đã terminal/audit; còn representative quality/lifecycle.
[Finite-language CPU evidence](../docs/evaluation/phase5_guard_token_language_v1_report.md)
đã hoàn tất; còn các native gates trong contract. Tiếp tục giữ separation/Test/mock-side-effect invariants; không dùng
Test để lựa chọn phương án sửa. Formal freeze vẫn chưa đủ bằng chứng.

- 2026-09-28: [journal + public runtime native A0–A6](../docs/evaluation/remote_api_levels_v1_report.md) đã có diagnostic7/7; quality/provenance/remote cancellation/freeze còn mở.
