# Phase 5 — tiến độ và các gate còn lại

## Hiện hành — host-bound resource scope / runtime v9

2026-09-14: [resource scope v4/runtime v9](resource_scope_v4.md) đạt bounded CPU:
full **2.945pass/1skip/865,40s**, 75focused/25,18s, setup/Ruff/mypy371/knowledge.
524source/295raw/169data hashes khớp; 20 scripted Dev runtime checks/21 reads.
Host-bound AWB/AUX document/page scope và catalog đã ghép; SQL row scope, native
Dev package/GPU/quality/freeze còn thiếu. Không đóng thêm aggregate gate chỉ từ
CPU checks; vẫn 4/7≈57%, không có GPU job mới.

2026-09-14: [guard diagnostics v1](guard_diagnostics_v1.md) đạt CPU full2.871pass/
1skip; 510source/424raw hashes khớp. Native observer/independent auditor tiếp theo
đạt full **2.888pass/1skip/785,14s**, 75focused/64,83s; 515source/567raw/169data
hashes kiểm lại khớp, 51 runtime receipts. Không còn QA chạy; chưa có GPU mới.
Lịch Dev cố định 8pairs/16cases/112 A0–A6 tasks chỉ
là metadata, chưa dispatch. Còn worker input/catalog và scope coverage; không
tăng gate từ số test. [Báo cáo](../docs/evaluation/phase5_guard_diagnostics_v1_report.md).

2026-09-14: [document diagnostic v1](document_diagnostic_v1.md), source `54aa3ec`,
đã sửa bounded CDOC bằng scope v3/runtime v8. 49 focused tests, full **2.813 pass/
1 skip**, 693,77s; setup/Ruff/mypy357/knowledge đạt. CPU501source/158raw và exact
110source/430raw hashes khớp, 169 data unchanged. Chuẩn bị submission mới;
chưa đóng gate native/quality/freeze. **Native v1 đã COMPLETE/audit**:
261raw/2remote khớp, 7doc reads; A0/A1completed, A2–A6model_error do guard
INVALID_OUTPUT/retired pair. 8GRACEFUL/4TERMINATE, 7recovered. Mục tiêu successful
guard Pre/Post không đạt; không tăng số gate đã nghiệm thu.
[Report](../docs/evaluation/phase5_document_diagnostic_v1_report.md).

2026-09-14: [shutdown package v2](shutdown_package_v2.md) đạt exact archive/
expanded isolated preflight: 8 tools, 21 public Dummy/resume, 7 synthetic levels
mỗi layout; 101 source/430 raw hashes khớp. Full CPU QA **2.764 pass/1 skip**,
24 focused tests, setup/Ruff/mypy 346 files/knowledge đạt; 485 source/137 raw
hashes khớp, 169 data hashes không đổi. Chưa submit GPU, không đóng thêm gate.
[Report](../docs/evaluation/phase5_shutdown_package_v2_report.md).

2026-09-14: [native shutdown wiring v2](native_shutdown_wiring_v2.md) đạt bounded
CPU: 36 focused tests, full 2.740 pass/1 skip, 719,76s; setup/Ruff/mypy 342 files/
knowledge đạt. 478 source/4.726 raw hashes khớp, 169 data hashes không đổi.
Factory/runner/auditor mới đã nối; exact package/release auditor và GPU còn mở.
Không đóng thêm gate nghiệm thu từ CPU. [Report](../docs/evaluation/phase5_native_shutdown_wiring_v2_report.md).

2026-09-14: [pair/runtime v3](pair_runtime_v3.md) đã nối observed shutdown vào
cả pair và agent-only trên CPU. 74 focused tests, 63 joined receipts và bốn
pair teardown fixtures; full **2.704 pass/1 skip**, 670,56s. Setup/Ruff/mypy
335 files/knowledge đạt; 468 source/646 raw hashes khớp, 169 data hashes không
đổi. Native factory/runner/auditor và exact package là bước tiếp; gate GPU,
guard quality và freeze vẫn mở. [Report](../docs/evaluation/phase5_pair_runtime_v3_report.md).

2026-09-14: [standalone observed shutdown v2](worker_shutdown_v2.md) đạt 80 focused
tests, full 2.630 pass/1 skip; 462 source/677 raw hashes khớp, 169 data hashes
không đổi. Hai synthetic cases GRACEFUL, các fault cases vẫn bounded/reaped.
Ở mốc standalone chưa nối pair/native; CPU v3 phía trên bổ sung pair wiring,
không đóng thêm production lifecycle gate từ CPU.

Native runtime technical pilot đã COMPLETE/audit: 205 raw/2 remote files khớp,
7/7 terminal và VRAM recovery. Nhưng **0 tool calls/0 guard calls**, 12 workers
TERMINATE/-15. Package/native model execution đã có bằng chứng; gate production
lifecycle vẫn mở. [Báo cáo](../docs/evaluation/phase5_security_runtime_gpu_v1_report.md).
Release QA 2.596 pass/1 skip; không suy phần trăm từ số test tăng thêm.

Mốc tiếp theo [pair/runtime v2](phase5_pair_runtime_v2.md) đã đóng phần CPU
post-response worker death và failed-startup timing: 64 focused tests,
2.560 pass/1 skip full QA (551,55s), 63 joined receipts, 445 source/641 raw
hashes khớp. Không đóng thêm gate GPU, guard quality hoặc freeze từ mốc CPU này.

Tiếp theo remediation, [pair/runtime CPU02](phase5_pair_runtime_v1.md) đã đạt:
52 focused tests, full 2.496 pass/1 skip (477,43s), 51 joined receipts, 441 source/
530 raw hashes khớp và 169 tracked data hashes không đổi. Chỉ bounded CPU
integration; native fault/timing/package/GPU và guard quality còn mở.

[Repair notes](phase5_remediation_v2.md) và [handoff](handoff.md) là chỉ dẫn hiện hành.
V1 entitlement/v6 chỉ giữ cho đối chiếu lịch sử; không dùng cho inference mới.
Audit đã tái hiện cấp quyền chéo, supplied grant không canonical, mixed raw/zero-width
lọt và metadata A0 bị gắn policy A6. Selected entitlement receipt còn có hash
pytest log sai; không được coi `valid=true` là đủ.

Bản sửa có clause-bound source/type grants, residual scan, table/column scope pairs,
A4–A6 PRE integration, task-local scope audit và typed synthetic student IDs.
91 focused tests pass; full QA 2.444 pass/1 native-tqdm skip, 460 giây.
Receipt mới đã re-audit 436 source/573 raw hashes khớp; 169 tracked data hashes
không đổi. Chưa gọi là production-ready.

## Gate để nghiệm thu

Theo bảng tổng hợp bên dưới, hiện **4/7 nhóm gate đã đạt ≈57%**, tính mỗi nhóm
ngang nhau. Đây không phải ước lượng công sức/thời gian, không phải số DoD trong
`plan/phase5.md` đã nghiệm thu, và không suy từ số test pass. Native wiring v2
đạt CPU nhưng chưa đóng thêm gate GPU. Ba nhóm còn lại phải có bằng chứng riêng.

| Gate | Trạng thái |
|---|---|
| Repair CPU, receipt toàn vẹn | Đạt working-tree CPU QA; lịch sử sai hash giữ riêng |
| Bounded A4 runtime integration | V7 đã qua regression/full QA |
| Bounded private-final/origin fixes | V2 đã qua regression/full QA |
| ModelPair/runtime host ownership + trace join CPU | V3 thêm observed shutdown và cold/warm/PID joins đạt QA; v1/v2 giữ nguyên |
| Production ModelPair/runtime + graceful GPU lifecycle | Chưa đóng |
| Production guard quality + grouped Dev differential | Chưa đóng |
| Broader semantic coverage + formal Phase 5 freeze | Chưa đóng |

Native ordinary pair T4×2 trước đó đã có 6/6 calls, repeat hashes và recovery
samples; chỉ là technical transport/residency/timing evidence. Forced cleanup
không đồng nghĩa graceful. Efficient 4096-token diagnostic pass không tự chứng
minh general ReAct/runtime performance.

Không suy phần trăm từ test count. Phase 5 chưa accepted, không mở Phase 6/7 hoặc
held-out Test. Các đoạn phía dưới là lịch sử, không phải nhiệm vụ kế tiếp.

## Lịch sử: guard-only GPU preflight

First real guard GPU kernel v1 đã COMPLETE và audit: four schema-valid responses,
matching A hashes, nhưng all A/B giống nhau và malicious synthetic B bị SAFE.
Hai worker reaped bằng TERMINATE/-15; graceful cleanup chưa đạt. Không chốt guard
hoặc Phase 5. Cold47,895/32,814s, warm0,956/0,991s, peakallocated2,898GiB.
[Report](../docs/evaluation/phase5_guard_gpu_v1_report.md),
[receipt](../experiments/manifests/phase5_guard_gpu_v1_audit01.json),
[audit deviation](../docs/evaluation/phase5_guard_gpu_audit_deviation.md).
21 Dummy/84 events, remote wrapper/private/offline/T4 và 56 raw hashes verified.
1.046 full tests pass/276,16 giây (23 mới), setup/Ruff/mypy208files/knowledge pass;
[release QA](../experiments/manifests/phase5_guard_gpu_v1_release_qa01.json).
Không semantic retry/Test/agent coexistence. Còn cancellation/GPU memory recovery,
versioned agent placement, grouped Dev validation/guard selection, A4/general final.

## Lịch sử: remote mount detection

Bundle03 đã qua archive/expanded isolated mounts, source `7649d5b` và receipt
đã push trước upload Dataset riêng tư. Remote READY v1/private đã xác minh,
nhưng có extra `source/pax_global_header` 52 bytes khiến frozen wrapper reject.
Đã tái hiện cục bộ từ file download, chưa kernel submission/GPU.
Thêm completed-probe audit với 13 synthetic tests; tách integrity và measured
repeatability, không đổi frozen inference code. Full suite 1.011 tests pass
tuần tự/271,34 giây; setup/Ruff/mypy 205 files gồm kernel pass.
[Nhật ký](guard_gpu_probe_v1.md) và
[remote diagnostic](../experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json).

## Lịch sử: acquisition

Weights Qwen 1.5B đã acquired/hash-verified (10 files, 3.098.973.447 bytes).
[Probe contract](../docs/architecture/phase5_guard_probe_contract.md): two task-local
workers, A→B→A/fresh-A bypass cache, strict JSON, no semantic retry. **998 tests
pass** (56 mới), 275,42 giây; setup/Ruff/mypy 203 files/knowledge pass.
Two-layout isolated bundle validation là bước kế tiếp. Chưa GPU run.
Kaggle `huylmhuhu` còn 29,49 giờ GPU tại lần đọc 2026-09-08; không đổi account.

## Lịch sử: HF adapter CPU

Adapter [HF guard v1](../docs/architecture/phase5_guard_hf_contract.md) qua CPU
preflight01: 942 tests pass (51 mới), 228,00 giây; setup/Ruff/mypy 197 files và
knowledge pass. 134 source hashes và 1.176 prior entries nguyên vẹn. Candidate
[Qwen 1.5B/revision evidence](guard_model_preflight_evidence.md), chưa tải weights.
Content-bound identity, GPU/process budget, context cap, fresh generation config/
cache và metrics riêng; không sửa runtime v5 hay các source đã hash.
Không suy CPU fake thành GPU fit hoặc model-quality/statelessness evidence.
Phase 5 chưa accepted; acquisition/bundle/GPU và grouped Dev còn mở.
[Selected receipt](../experiments/manifests/phase5_guard_hf_v1_validation01.json)
từ source sạch `bc2023f` khớp preflight, **942 tests pass** trong 228,14 giây;
134 source/sáu raw log hashes kiểm lại. Không sửa adapter/test/contract đã selected.

## Lịch sử: warm guard/runtime v5

[Warm guard/runtime v5](../docs/architecture/phase5_warm_guard_contract.md) đã tái lập:
model load một lần/task, bounded JSON IPC, cold/warm timing riêng và deadline
tính đủ cold load. Không cache/worker xuyên task, không tự restart/retry. Worker
lỗi hoặc guard output invalid bị loại, cache xóa. V5 close ở terminal và exception.
Preflight01: **891 tests pass**, 46 mới; setup/Ruff/mypy 194 files/knowledge pass.
22 cold/warm pairs = 44 Replay + chín lifecycle conditions; 140 mock Broker calls,
240 fake runtime guard classifications. 138 source/370 raw hashes kiểm lại,
1.038 prior entries giữ nguyên. Paired worker starts 53 cold → 18 warm, không GPU
throughput claim. [Selected receipt](../experiments/manifests/phase5_warm_guard_v1_validation01.json)
từ source sạch `2300751` khớp preflight, 891 tests pass trong 225,80 giây;
138 source/370 raw hashes kiểm lại, worker starts vẫn 53/18. Chưa Phase 5 acceptance.
A6 Post source IDs chỉ được đối chiếu
qua source binding; context gốc vẫn lưu nguyên. Chưa guard/model/GPU thật.

## Lịch sử: A6 runtime v4

Runtime v4 A0–A6 theo [contract](../docs/architecture/phase5_a6_runtime_contract.md)
đã qua preflight01: **845 tests pass** (76 mới), setup/Ruff/mypy 190 files/knowledge
pass. 26 synthetic conditions + 12 A0–A5 parity pairs = 50 Replay, 56 Broker mock
calls, 121 fake guard classifications. 135 source/435 raw hashes kiểm lại,
903 prior source entries giữ nguyên.
[Selected reproduction](../experiments/manifests/phase5_a6_runtime_v1_validation01.json)
từ source sạch `04ae4c8` khớp preflight, 845 tests pass trong 178,29 giây;
135 source/435 raw hashes kiểm lại. 25 A6 finals: 23 ALLOW/1 REDACT/1 DENY;
một A5 final pass-through. Đây là predeclared synthetic conditions, không ASR.
Coarse verdict/value/composed verdict lưu riêng; chỉ thay coarse sensitivity
veto khi đủ nguồn public. Guard/control veto không bị vượt qua. Actual Post view
vào context; final proposed/released tách biệt và chỉ released text được trả ra.
Không sửa source đã hash, không dùng Test hoặc chạy model thật.
Guard production/revision/GPU lifecycle, A4 scope, grouped Dev validation/freeze
và general final entitlements vẫn chưa hoàn tất; không nghiệm thu Phase 5.

## Lịch sử: value PreGate/Post-view components

PreGate component nhận host user/proposal artifacts, yêu cầu exact raw-user anchors
và origin của critical leaves; protected/unknown/coverage failures chặn external.
Kiểm tra hai chiều index↔exposure để không bỏ sót nguồn S2 hoặc dùng public chưa
được thấy. Post-view giữ raw và nhãn, dùng JSON data envelope cho untrusted source.
[Contract](../docs/architecture/phase5_value_gates_contract.md).

Preflight02: **769 tests pass**, 73 mới; setup/Ruff/mypy 186 files/knowledge pass.
24 Pre cases (4 ALLOW/20 DENY) + sáu Post cases; bốn Broker mock calls, zero model/
guard/Replay runs. 771 prior source entries nguyên vẹn, 132 source/121 raw hashes
đã kiểm lại. [Selected reproduction](../experiments/manifests/phase5_value_gates_v1_validation02.json)
từ source sạch `a3743a2` khớp preflight; 769 tests pass trong 138,14 giây.
Preflight01 source-changed bị loại. Validation01 gián đoạn trước receipt; giữ
nguyên thư mục và chạy validation02 mới, không ghi đè hoặc chọn kết quả từng ca.

Vẫn chưa runtime A6: phải kết hợp guard/control risks, arbitration coarse session,
critical-field bindings, Post context và released-final accounting/authorization.
Không coi value ALLOW là full A6 ALLOW. Còn guard thật/GPU lifecycle, A4 scope và
grouped Dev validation. Không ASR/utility claim hoặc Test payload parsing.

## Lịch sử: value-origin/final-release

Source `3b9f565`: [component contract](../docs/architecture/phase5_value_origin_contract.md)
cho typed origin index và deterministic final release. Đây là phần nền A6, chưa
bật A6 runtime hoặc thay A0–A5. Index chỉ nhận raw roots do host quan sát, giữ mọi
nguồn trùng giá trị và nhãn sensitivity/trust độc lập; hỗ trợ DB columns/rows,
numeric equivalence có giới hạn, kiểm soát tài nguyên và admission atomic.
Final mới liên kết proposal/nguồn, raw và nhãn gốc giữ nguyên. Normalized-only hit,
scan failure hoặc protected value chuẩn hóa thành rỗng dẫn tới DENY.

Preflight **696 tests pass** (103 mới), setup/Ruff/mypy 183 files/knowledge pass.
24 synthetic conditions: 12 ALLOW, 8 REDACT, 4 DENY; không fresh Replay hoặc guard
classification. 130 source/101 raw hashes ghi, 641 prior source entries nguyên vẹn.
[Selected reproduction](../experiments/manifests/phase5_value_origin_v1_validation01.json)
từ commit sạch khớp stable preflight, 696 tests pass; 130 source/101 raw hashes
đã kiểm lại. Kiểm tra riêng serialized artifacts đã đối chiếu
ID/hash/labels/proposed/released cho cả 24 ca.

Không benchmark Dev tuning/Test parsing hoặc model inference. ALLOW chỉ là không
khớp profile hiện hành; không chứng minh không có rò rỉ ngữ nghĩa/encoded/paraphrase.
Final authorization và unknown critical relations cần runtime policy riêng, không GT.
Tiếp theo: A6 Pre/Post/Final/veto arbitration, A4 general processing scope, guard
production/revision/GPU lifecycle và grouped Dev protocol. Phase 5 chưa nghiệm thu.

## Lịch sử: A3–A5 session runtime

Runtime v3 hỗ trợ A0–A5 với policy cumulative, không tạo ablation ngầm. A3 chặn
external sau S1/S2; A4 thêm authorization raw-user sau untrusted; A5 thêm joint
rule/LLM SUSPICIOUS/MALICIOUS/error veto. Session snapshot riêng từng task, không
vào agent prompt; zero-call có guard trace rỗng. [Contract](../docs/architecture/phase5_session_contract.md).

Preflight **593 tests pass** (147 mới), setup/Ruff/mypy 179 files/knowledge pass.
44 exact A0–A2 pairs + 30 session conditions = 118 fresh Replay. Riêng session
matrix: 165 fake guard classifications, 225 snapshots, 15 expected denials.
127 source/780 raw hashes đã kiểm, 514 prior source entries nguyên vẹn. Source
`8a4ca3d`, [selected receipt](../experiments/manifests/phase5_session_v1_validation01.json)
khớp stable preflight, 593 tests pass. Đây không phải ASR hoặc model quality.

Còn A4 general processing scope ngoài grammar external anchors; A6 value-origin,
Post/Final; guard LLM thật/revision/GPU lifecycle; grouped Dev validation/freeze.
Coarse policy chủ động overblock unrelated S0 sau S1/S2; final chưa leak protection.
Không Dev tuning/Test payload parsing, không đổi điểm pilot, chưa nghiệm thu Phase 5.

## Lịch sử: A2 process guard

Preflight A2 v2: **446 tests pass** (80 mới), setup/Ruff/mypy 175 files pass.
40 exact smoke pairs A0/A1 đối chiếu v1 + chín A2 synthetic trajectories = 89
fresh Replay, 31 fake guard classifications. Validator kiểm tra source/action/
proposal linkage, cache identity, error/result schema, counters và worker reap.
124 source/548 raw hashes ghi trong preflight, 390 prior source entries bất biến.
Selected source `15ed921`, [receipt](../experiments/manifests/phase5_a2_v2_validation01.json)
khớp preflight; toàn bộ source/raw hashes kiểm lại thành công.

Đã có A2 Pre/Post trong ReAct, cumulative A1, sticky MALICIOUS/error external veto,
read-open, SUSPICIOUS tagging, final pass-through. Guard inference riêng process;
timeout thực + terminate/kill/reap, failure retirement, fresh task cache, typed
output và cold end-to-end latency. [Contract](../docs/architecture/phase5_a2_runtime_contract.md).

**Chưa xong Phase 5:** chốt guard thật/revision cố định A2–A6 và worker GPU hiệu quả,
A3–A5 session enforcement, A6 value-origin/Post/Final, grouped Dev validation.
Cold process mỗi cache miss chưa phù hợp đo warm throughput. Chưa có model-quality
evidence hoặc benchmark Dev/Test run mới. Quy tắc/cache đã khóa không tune theo Test.

## Lịch sử: runtime A0/A1

Source `d2ec2d5`, [receipt](../experiments/manifests/phase5_runtime_v1_validation01.json),
[contract runtime](../docs/architecture/phase5_runtime_contract.md).
366 tests pass (66 mới), setup/Ruff/mypy 170 files pass. 20 smoke exact A0 parity
pairs với Phase 4 + 24 synthetic A0/A1 conditions, 64 fresh Replay. 655 artifacts
trong các run Phase 5, sáu denials đúng micro-case expectations; không diễn giải
6/12 thành benchmark ASR. 120 source và 369 raw hashes khớp; 270 prior hash entries
giữ nguyên. Stable summary khớp preflight. Không benchmark Dev/Test inference.

Vòng ReAct chung đã có actual context/model/argument/final lineage. Policy denial
không gọi Broker, không tạo ToolResult/call ID giả; phản hồi chính sách có artifact
và các parent liên quan. Lặp denial tiêu thụ step budget; parse retry tiếp tục đúng
context. Detector lỗi ghi class-only, read-open/external-closed; final A0/A1 vẫn
pass-through, không giả A6. Có validator thứ tự proposal/pre/denied-or-call/post/final.
Runtime chỉ hỗ trợ A0/A1 và từ chối A2–A6 trước khi tạo output.

Tiếp theo: grouped Dev tune/validation trước tuning; chốt guard model/revision và
bounded inference, tích hợp A2; session enforcement A3–A5 rồi value-origin A6.
Không sửa các module/config/receipt đã hash; thêm version tiếp theo. Rules/anchors
chưa được tune trên benchmark, giữ giới hạn lexical/JSON-escape và grammar đã ghi.
Không cần tài khoản mới cho local implementation; chưa có guard model run thật.

## Lịch sử: mốc component đầu tiên

Owner authorized 2026-09-07. Source `4bddd23`,
[receipt](../experiments/manifests/phase5_components_v1_validation01.json),
[contract](../docs/architecture/phase5_policy_contract.md).

Đã triển khai bảy config cumulative strict, decision/reason/stage enums và public
observation schemas từ chối GT fields. A1 scan raw + normalized detector view,
post TAG và pre deny external sau signal nếu thiếu user destination authorization.
Adapter A0/A1 gọi Tool Broker cho mọi call được phép; deny không tạo ToolResult giả.
Raw user anchors có grammar giới hạn; không lấy addresses trong nguồn truy xuất.
A2 mới có backend interface, prompt/parser/cache và fail-open read/fail-closed sink.
Không dùng fake/Replay guard để tuyên bố chất lượng LLM.

300 tests pass, gồm 56 micro-tests mới; setup/Ruff/mypy 166 files pass.
Validator kiểm tra 153 Phase 4 source hashes, hai seals/hash-only Test và bảy config
hashes. Không benchmark Dev run, Test parsing hoặc model inference. Các source
đã chọn tiếp tục bất biến; thay đổi sau milestone cần module/version kế tiếp.

Tiếp theo:

1. Shared ReAct runtime riêng cho Phase 5: gắn policy ở Pre/Post/Final, giữ đầy đủ
   raw model output/context lineage, proposed/executed distinction và A0 parity.
2. Chốt guard model/revision dùng chung A2–A6, bounded timeout/cancellation thực,
   tích hợp A2. Hiện backend adapter chỉ xử lý TimeoutError, chưa tự ngắt inference.
3. Session sensitivity/trust/A5 và value-origin A6, unknown critical deny/final protection.
4. Chia grouped Dev tune/validation theo protocol trước tuning; không mở Test.
5. Differential utility/security QA rồi freeze theo 20 DoD; không lấy config count
   làm tỷ lệ hoàn thành hoặc claim A1/A2 đã end-to-end qua agent loop.

Giới hạn: lexical detector có false positives khi trích dẫn hướng dẫn; anchor parser
không hiểu mọi câu tiếng Việt. Adapter hiện chỉ host-proposal lineage, không phải
runner để đánh giá LLM. Không thay điểm pilot cũ; Meta access vẫn là việc pilot riêng.
