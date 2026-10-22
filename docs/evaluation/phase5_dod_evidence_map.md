# Phase5 — bản đồ20DoD và cổng đóng còn lại

> **Đã đóng2026-10-02:** Phase5accepted20/20DoD theo [closure dossier](phase5_completion_20261002.md).
> Các backlog/NO_GO bên dưới được giữ theo thời điểm lịch sử,không là trạng thái hiện hành.

2026-09-21, cập nhật 2026-09-29. Đối chiếu `plan/phase5.md` mụcCXXVI. Đây là chỉ mục bằng chứng,
**không phải biên bản nghiệm thu20/20**. Test hiện diện không tự chứng minh pass;
luôn đọc receipt/report đúng source. Không mở Phase6/7 hoặc held-out Test.

## Cập nhật hướng API — 2026-09-27

[Paired API smoke](structured_pair_api_v1_report.md) bổ sung evidence vận hành
schema/guard-call/Broker choDoD5/10, nhưng chưa fullA2/A6, không tăng acceptance.
[Readiness audit 20 DoD](phase5_gate_readiness_v1_report.md) đã kiểm tra
admissibility bằng metadata công khai: 16 mục chỉ có CPU evidence, 3 mục là
diagnostic-only và DoD20 chưa đủ evidence; cả20 vẫn mở vì native blocker.
[Rà tiến độ và lộ trình](project_status_api_20260927.md) là hướng hiện hành:
manifest/runner Dev → pilot agent/guard → candidate integration → đối sánh
A0–A6/lifecycle → freeze20DoD. Bốn phase đầu accepted; Phase5 vẫn4/7nhóm.
Bridge typed-reference cần client schemaPlan, không dùng ngay action/final
client. Hai server không thay yêu cầu ba task backbones củaRQ1; chạy tuần tự
được. Không dùng readiness để đóng lifecycle hoặc guard-quality gates.
Các mục source/package/Dev32 dưới đây giữ làm evidence lịch sử, không phải
lệnh tự động submit lại. Lượt này chỉ audit tài liệu/source/receipt có sẵn.

Owner sau đó đã duyệt restructure giới hạn: [field-reference component](phase5_field_reference_v1_report.md)
giữ public8/8, deny8/8 trong32CPUexecutions. Đây chỉ evidence cơ chế choDoD9/14/15/16,
không nghiệm thu cácDoD đó: Grant host assumed, chưa model/guard/external sink/cumulative
runtime. Không đổi4/7 hoặc trộn điểm prototype với benchmark cũ.

Cập nhật2026-09-29: [terminal-line normalization ablation](phase5_terminal_normalization_ablation_v1_protocol.md)
đã chạy riêng trên 9 synthetic controls (4 canonical equivalents, 5 deny), giữ
raw/released hashes và không có model/API/network request. [Formal freeze
validator](phase5_formal_freeze_report_20260929.md) đã map đủ 20 DoD và xác minh
receipt/hash hiện hành. Đây là **NO-GO freeze**, không phải acceptance: cả20 DoD
vẫn mở và Phase5 không được đánh dấu accepted.

Ưu tiên 2026-09-25: [direction review](phase5_direction_review_20260925.md)
không promote doc_read candidate thành general remedy: controlled CPU utility2/8,
unsafe omissions3/4. Đề xuất tái cấu trúc giới hạn chờ owner duyệt; không đổi
DoD/gates hoặc suy core thesis infeasible. Package success không thay thế coverage.

Cập nhật2026-09-22: [v12/constrained ExitPair CPU](phase5_clause_pair_v1_report.md)
đã kiểm paired transport, origin replay, checkpoint/resume và4egress controls.
Đây là bằng chứng bổ sung choDoD9/10/16; không thay32Dev native quality/package
hoặc formal freeze. A0/A1 không chạy qua paired-guard adapter này.

[Dev32 runner CPU](phase5_clause_dev32_v1_report.md) đã kiểm32tasks/8shards,
manifest và checkpoint/resume; native artifact adapter có token/count joins.
Mốc này là trước native source/release admission. Cập nhật 2026-09-23:
[Dev32 v1](phase5_clause_dev_gpu_v1_failure_report.md) ERROR trước worker đầu;
[v2 release02](phase5_clause_dev_package_v2_report.md) đã qua admission hai
layouts; notebook private/offline/T4 version1/ID135499833 sau đó
[COMPLETE/audit](phase5_clause_dev_gpu_v2_terminal_report.md) với 32/32 Dev,
65 returned guard responses hợp lệ và một guard TERMINATE. Cập nhật cùng ngày:
[evaluator-only Dev32 scoring](phase5_clause_dev32_scoring_v1_report.md) đã
chấm đúng 32 trace, và [exit diagnostic](phase5_clause_guard_exit_diagnostic_v1_report.md)
đã kiểm shutdown. Có một A6 canonical safe-action false block; guard 31/32
GRACEFUL, một TERMINATE/-15. HF chỉ mở trong committed worker. Không suy
nghiệm thu từ completion, returned syntax hay CPU package. Đường xử lý
ba cổng còn lại ở [giải pháp kỹ thuật](phase5_completion_strategy_v1.md).

Cập nhật 2026-09-24: [final proof Dev + paired CPU](phase5_final_literal_dev_runtime_v1_report.md)
bổ sung bằng chứng DoD12/14/15/16: 24 synthetic component cases, runtime
FINAL-only không đổi PRE/POST, năm room controls mới và 14 raw-runtime audits
(kể cả max-steps/parse/model error không có final release). Chưa chứng minh
public-field proof trên doc_read thật hoặc native quality/lifecycle; không
đánh dấu các DoD này accepted chỉ từ CPU. [Receipt/hash](../../experiments/manifests/phase5_final_literal_dev_cpu_v1.json).

Cùng ngày, [proof raw doc_read](phase5_doc_read_final_proof_v1_report.md) đã nối
public-field FINAL với schema tool thật, giữ PRE/POST. 12 paired CPU conditions
cho utility 1/5→5/5, negative target omissions 7/7 cả hai; 24 raw outputs audit
hai lượt khớp byte sau recovery lỗi aggregation (không retry agent). Bổ sung
DoD12/14/15/16, **không nghiệm thu native**; source admission/full pair audit/
exact package/quality/lifecycle vẫn mở.

Cập nhật 2026-09-25: [doc_read native wiring CPU](phase5_doc_read_native_cpu_v1_report.md)
đã bổ sung admission nguồn/run/model, actual-import source check, full pair/
Broker/raw-final joins, checkpoint/resume và exact package04 hai layout.
53 focused tests, 191 worker files, 21 Dummy/layout. Đây là development package
với source_commit=null, 0 native run; không đổi acceptance DoD hoặc 4/7.
Matched prospective runs/source freeze và native quality/utility/lifecycle còn mở.

| DoD | Bằng chứng/đầu mối hiện có | Cổng còn phải đóng với candidate mới |
|---|---|---|
| 1 — bảy cấu hình | [Config tests](../../tests/integration/test_phase5_components.py), [v12CPU](phase5_clause_candidate_v1_report.md) | V12 cumulative đã có CPU controls, chưa native rollout |
| 2 — cô lập cấu hình | [Grouped identity](../../src/react_agent/llm/grouped_dev_identity_v1.py), [Dev32 terminal](../../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json) | Source/settings/remote/raw đã audit; còn đối chiếu các mức khác trên cùng run identity trước formal acceptance |
| 3 — A0 purity | [Replay parity](../../tests/integration/test_phase5_runtime.py) | Candidate delegateA0 cần kiểm parity khi tích hợp native |
| 4 — A1 | [Runtime differential](../../tests/integration/test_phase5_runtime.py) | Không làm suy yếu rule/authorization khi mở rộng anchors |
| 5 — A2 | [ExitPair native](phase5_exit_gpu_v1_report.md), [fallback tests](../../tests/integration/test_phase5_a2.py), [Dev32 scoring](phase5_clause_dev32_scoring_v1_report.md) | 65/65 returned syntax OK nhưng 8/32 ca không gọi guard; attack success A2 1/8 trong subset chọn trước. End-to-end semantic quality/coverage còn mở |
| 6 — A3 | [Session tests](../../tests/integration/test_phase5_session.py) | Giữ veto session sensitivity qua candidate integration |
| 7 — A4 | [Resource scope](../../tests/unit/test_resource_scope_v4.py), [v12CPU](phase5_clause_candidate_v1_report.md) | Compound grammar bounded đã test; cần giữ scopev5 trong native candidate |
| 8 — A5 | [Session tests](../../tests/integration/test_phase5_session.py) | Contrast unrelated-secretA5 vẫn DENY; không vô tình xóa veto |
| 9 — A6 artifact | [Current controls](phase5_acceptance_controls_v1_report.md) | CPU cho phép public-after-secret, chưa native representative proof |
| 10 — PreGate | [Value gates](../../tests/integration/test_phase5_value_gates.py) | Giữ actual broker dispatch checks, không chỉ xem final status |
| 11 — PostGate | [A6 runtime](../../tests/integration/test_phase5_a6_runtime.py) | Giữ post-view/raw provenance và guard verdict joins |
| 12 — FinalGate | [Final entitlement](../../tests/integration/test_phase5_final_entitlement_runtime.py) | Mọi terminal path phải giữ đúng proposed/released sink |
| 13 — S2 egress | [Controls](phase5_acceptance_controls_v1_report.md) | Recognized destination không cấp quyền gửi sensitive payload |
| 14 — final leakage | [Controls](phase5_acceptance_controls_v1_report.md) | Giữ REDACT/DENY; chưa khẳng định semantic leakage tổng quát |
| 15 — benign utility | [Coverage v12](../../experiments/manifests/phase5_clause_coverage01.json), [Dev32 scoring](phase5_clause_dev32_scoring_v1_report.md) | 16 benign native tasks đã chấm: typed utility A2 4/8, A6 3/8; một A6 canonical safe-action false block. Representative utility không được suy từ terminal completion và cổng vẫn mở |
| 16 — unknown lineage | [Value origin](../../tests/integration/test_phase5_value_origin.py), [controls](phase5_acceptance_controls_v1_report.md) | Không giả gán nguồn để tăng utility |
| 17 — GT separation | [Rejected evaluator fields](../../tests/integration/test_phase5_components.py) | Coverage/expectations chỉ ở host, không vào prompt/policy/package |
| 18 — Test integrity | [Research invariants](../project/invariants.md) | Trước formal freeze xác minh seal/hash bằng validator, không đọc payload để tuning |
| 19 — mocks only | [Socket/SMTP denial tests](../../tests/integration/test_phase5_components.py), [new CPU checks](../../tests/integration/test_sentence_runtime_v11.py) | Không network side effects khi native integration |
| 20 — formal freeze | [NO-GO receipt](../../experiments/manifests/phase5_formal_freeze_receipt_20260929.json), [formal report](phase5_formal_freeze_report_20260929.md) | Metadata/source/artifacts đã được hash và map đủ 20 DoD; native semantic quality, benign utility, lifecycle reliability và acceptance vẫn mở |

## Thứ tự đóng phần còn thiếu

1. Raw-user clause/cumulative v12 đã qua CPU controls; giữ bounded grammar/limits
   và frozen sources, không sửa benchmark theo model output.
2. Candidate cumulative parity/pair binding, exact package và source freeze
   cho Dev32 v2 đã có; giữ v1 ERROR và release01 rejection làm lịch sử.
3. Manifest 32 ca A2/A6 từ 16 public Dev đã COMPLETE/audit và được chấm
   evaluator-only một lượt v2. Giữ mọi failure/denial, denominator và một
   confirmed benign false block; không coi completed là đúng.
4. Lifecycle follow-up nếu cần có prospective paired order/repeat budget; không
   resubmit diagnostic v1 cho tới khi thấy kết quả đẹp.8GRACEFUL chưa chứng minh fix.
5. Gắn từngDoD với receipt/source/giới hạn, rồi formalize **NO-GO** nếu còn
   cổng mở. Receipt hiện tại đã hoàn tất bước này; không cập nhật phase_status
   thành accepted. Phần trăm4/7≈57% hiện là7nhóm acceptance, không phải20DoD.

Native API milestone 2026-09-28: [public runtime7mức](remote_api_levels_v1_report.md) có PRE/POST/FINAL trên một task calculator; không đóng quality/provenance/lifecycle DoD.
