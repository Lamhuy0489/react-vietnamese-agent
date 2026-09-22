# Phase5 — bản đồ20DoD và cổng đóng còn lại

2026-09-21. Đối chiếu `plan/phase5.md` mụcCXXVI. Đây là chỉ mục bằng chứng,
**không phải biên bản nghiệm thu20/20**. Test hiện diện không tự chứng minh pass;
luôn đọc receipt/report đúng source. Không mở Phase6/7 hoặc held-out Test.

Cập nhật2026-09-22: [v12/constrained ExitPair CPU](phase5_clause_pair_v1_report.md)
đã kiểm paired transport, origin replay, checkpoint/resume và4egress controls.
Đây là bằng chứng bổ sung choDoD9/10/16; không thay32Dev native quality/package
hoặc formal freeze. A0/A1 không chạy qua paired-guard adapter này.

[Dev32 runner CPU](phase5_clause_dev32_v1_report.md) đã kiểm32tasks/8shards,
manifest và checkpoint/resume; native artifact adapter có token/count joins.
Còn native source/release admission, launcher vàexact package; HF vẫn khóa.

| DoD | Bằng chứng/đầu mối hiện có | Cổng còn phải đóng với candidate mới |
|---|---|---|
| 1 — bảy cấu hình | [Config tests](../../tests/integration/test_phase5_components.py), [v12CPU](phase5_clause_candidate_v1_report.md) | V12 cumulative đã có CPU controls, chưa native rollout |
| 2 — cô lập cấu hình | [Grouped identity](../../src/react_agent/llm/grouped_dev_identity_v1.py) | Manifest mới phải giữ model/data/tools/decoding cùng nhau |
| 3 — A0 purity | [Replay parity](../../tests/integration/test_phase5_runtime.py) | Candidate delegateA0 cần kiểm parity khi tích hợp native |
| 4 — A1 | [Runtime differential](../../tests/integration/test_phase5_runtime.py) | Không làm suy yếu rule/authorization khi mở rộng anchors |
| 5 — A2 | [ExitPair native](phase5_exit_gpu_v1_report.md), [fallback tests](../../tests/integration/test_phase5_a2.py) |8valid chỉ4diagnostic; còn representative classification |
| 6 — A3 | [Session tests](../../tests/integration/test_phase5_session.py) | Giữ veto session sensitivity qua candidate integration |
| 7 — A4 | [Resource scope](../../tests/unit/test_resource_scope_v4.py), [v12CPU](phase5_clause_candidate_v1_report.md) | Compound grammar bounded đã test; cần giữ scopev5 trong native candidate |
| 8 — A5 | [Session tests](../../tests/integration/test_phase5_session.py) | Contrast unrelated-secretA5 vẫn DENY; không vô tình xóa veto |
| 9 — A6 artifact | [Current controls](phase5_acceptance_controls_v1_report.md) | CPU cho phép public-after-secret, chưa native representative proof |
| 10 — PreGate | [Value gates](../../tests/integration/test_phase5_value_gates.py) | Giữ actual broker dispatch checks, không chỉ xem final status |
| 11 — PostGate | [A6 runtime](../../tests/integration/test_phase5_a6_runtime.py) | Giữ post-view/raw provenance và guard verdict joins |
| 12 — FinalGate | [Final entitlement](../../tests/integration/test_phase5_final_entitlement_runtime.py) | Mọi terminal path phải giữ đúng proposed/released sink |
| 13 — S2 egress | [Controls](phase5_acceptance_controls_v1_report.md) | Recognized destination không cấp quyền gửi sensitive payload |
| 14 — final leakage | [Controls](phase5_acceptance_controls_v1_report.md) | Giữ REDACT/DENY; chưa khẳng định semantic leakage tổng quát |
| 15 — benign utility | [Coverage v12](../../experiments/manifests/phase5_clause_coverage01.json) |6Dev destination gaps đã đóng; chưa payload/quality/utility proof từ model |
| 16 — unknown lineage | [Value origin](../../tests/integration/test_phase5_value_origin.py), [controls](phase5_acceptance_controls_v1_report.md) | Không giả gán nguồn để tăng utility |
| 17 — GT separation | [Rejected evaluator fields](../../tests/integration/test_phase5_components.py) | Coverage/expectations chỉ ở host, không vào prompt/policy/package |
| 18 — Test integrity | [Research invariants](../project/invariants.md) | Trước formal freeze xác minh seal/hash bằng validator, không đọc payload để tuning |
| 19 — mocks only | [Socket/SMTP denial tests](../../tests/integration/test_phase5_components.py), [new CPU checks](../../tests/integration/test_sentence_runtime_v11.py) | Không network side effects khi native integration |
| 20 — formal freeze | [Phase status](../project/phase_status.md) | Chưa đủ: candidate native integration/package, quality, lifecycle reliability |

## Thứ tự đóng phần còn thiếu

1. Raw-user clause/cumulative v12 đã qua CPU controls; giữ bounded grammar/limits
   và frozen sources, không sửa benchmark theo model output.
2. Chốt candidate cumulative parity và pair/native evidence binding. Chạy exact
   package rehearsal trước một source freeze thật sự cần thiết.
3. Manifest32caA2/A6 từ16public Dev đã có CPU evidence; sau native admission chạy
   một lượt trên model thật và giữ mọi
   failure/denial. Đo guard decisions và utility độc lập, không coi completed là đúng.
4. Lifecycle follow-up nếu cần có prospective paired order/repeat budget; không
   resubmit diagnostic v1 cho tới khi thấy kết quả đẹp.8GRACEFUL chưa chứng minh fix.
5. Gắn từngDoD với receipt/source/giới hạn, rồi mới formal freeze và cập nhật
   phase_status. Phần trăm4/7≈57% hiện là7nhóm acceptance, không phải20DoD.
