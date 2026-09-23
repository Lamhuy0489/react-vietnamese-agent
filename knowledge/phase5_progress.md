# Phase 5 — tiến độ và các gate còn lại

## Hiện hành — Dev32 v2 COMPLETE/audit, 2026-09-23

[Terminal report](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md):
32/32 public Dev A2/A6, 8/8 shards, 2.073 raw/2 remote hashes, 222 source
pins; hai audits và hai host reports khớp byte. 65/65 returned guard syntax
OK nhưng 8 tasks không gọi guard; 31/32 all-workers GRACEFUL, một guard
TERMINATE. Chưa chấm ASR/FPR/benign utility/final semantic safety; model weight
SHA chưa xác thực. Formal Phase5 vẫn 4/7≈57%, không tăng từ completion.
Tiếp theo evaluator-only Dev scoring và DoD review, không rerun/Test.

## Mốc trước — Dev32 v2 submitted/RUNNING, 2026-09-23

[Report](../docs/evaluation/phase5_clause_dev_package_v2_report.md): release02
source `ad152ff` qua hai layouts/222 source pins; actual
[notebook v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
v1/ID135499833 private/offline/T4, remote source/settings/version khớp.
09:55:43 UTC RUNNING; không model result hoặc quality claim. Chỉ monitor,
terminal download/authentication/audit trước scoring; không resubmit.
Formal Phase5 vẫn 4/7≈57%.

## Mốc trước — Dev32 v1 terminal ERROR, 2026-09-23

[Failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md):
v1remote/source/version khớp,nhưng dừng trước worker do duplicate`constrained`.
0/32tasks có result,12rawfiles đã giữ vàhai audits khớp;không quality proof.
V2 sửa ở đường native riêng. Development package qua hai layouts; QA03 sau
regression cache đạt 981 focused + 395 integration, Ruff/mypy501/setup.
Source freeze đầu `24164d8` đã push main; committed release01 qua rehearsal
nhưng [bị từ chối](../experiments/manifests/phase5_clause_dev_package_v2_release01_rejected.json)
do host auditor còn cache allowlist v1. Chưa gửi notebook v2. Tiếp theo chốt
commit sửa auditor, dựng release02, chạy release audit rồi mới submit một lần.
Formal 4/7≈57% không đổi; packaging không phải quality proof.

## Hiện hành — Dev32 native submitted, 2026-09-22

[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md):source`5a23528`
commit/pushmain một lần;committedpackage hai layouts đạt,218source pins xác thực.
Actual`huylmhuhu/react-vn-clause-dev32-v1`v1/ID135340687,RUNNING07:10:42UTC;
private/offline/T4/14400s,32Dev. Remote source/settings/version khớp. Chờ terminal
download/audit,không gửi lại. Phase5formal4/7≈57%không đổi từ submission.

## Hiện hành — Dev32 exact package development, 2026-09-22

[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md):211worker/
218source pins;hai layouts mỗi layout8tools/21Dummy/32Dev+audit/resume đạt.
976focused+395integration,setup/Ruff/mypy495/knowledge/diff đạt;182native/169data
pins không đổi. Chưa source-freeze/committed package hoặc native inference mới.
Live Kaggle quota29,75h và privateDatasetv1ready;tiếp theo release+submit một lần.
Formal4/7≈57% giữ nguyên,không dùng packaging làm model quality proof.

## Hiện hành — Dev32 runner/checkpoint CPU, 2026-09-22

[Report](../docs/evaluation/phase5_clause_dev32_v1_report.md):32/32synthetic tasks,
8shards/16Dev fixtures A2/A6;64GRACEFUL workers, complete-resume và hai audits/shard
không đổi raw.188source/928raw pins khớp;23tests mới. [QA02](../experiments/manifests/phase5_clause_dev32_qa02.json):
888focused+395integration,setup/Ruff/mypy488/knowledge/diff đạt;182native/169data pins nguyên.
Native artifact adapter có kiểm token/count nhưng chưa source/release admission;
HF vẫn khóa. Tiếp theo native launcher/release gate +exact package, không thêm
4task diagnostic. Chưa model quality/GPU/commit/push;formal4/7≈57% giữ nguyên.

## Mốc trước — V12/constrained ExitPair CPU, 2026-09-22

[Report](../docs/evaluation/phase5_clause_pair_v1_report.md): đã nối v12/scopev5/
originv3 vào paired constrained host, giữ frozen workers.12tasks/24workers reaped,
4deliberate model_error giữ nguyên,4egress controls đạt;20GRACEFUL/4TERMINATE chỉ
ở failure controls.184source/348raw pins khớp,scan349files/0credentials.
36newtests đạt; [final QA](../experiments/manifests/phase5_clause_pair_qa01.json):
879focused+381integration đạt; setup/Ruff/mypy483/knowledge/diff đạt;
182native/169data pins nguyên. Chưa32Dev native runner/package hoặc GPU;
không commit/push mới, formal4/7≈57% giữ nguyên.

## Mốc trước — Clause/cumulative candidate CPU, 2026-09-21

[Report](../docs/evaluation/phase5_clause_candidate_v1_report.md):78/78 synthetic
controls đạt, gồm26compound permission/prohibition;6Dev destination gaps đóng
ở parser, chưa payload/utility proof. CumulativeA1–A6, A0 raw parity và host-only
destination provenance có tests. 67new unit+65new integration đạt;157source/
1.400raw hashes kiểm riêng;scan1.401files/0credentials.
[Final QA](../experiments/manifests/phase5_clause_qa01.json):873focused+
351integration đạt; setup/Ruff/mypy478/knowledge/diff đạt;182native/169data pins nguyên.
Chưa constrained/native integration, package, model/GPU/commit/push mới;
formal4/7≈57% không đổi. Bước tiếp theo rõ trong [handoff](handoff.md).

## Mốc trước — Coverage và benign authorization CPU, 2026-09-21

[Report](../docs/evaluation/phase5_acceptance_controls_v1_report.md):16public Dev
fixtures/8cặp giữ seed, không chọn theo model output. Đã tái hiện9/26false-denials
dạng dấu chấm ở v10;ứng viên A6v11 đạt52/52controls nhưng chưa compound/cumulative/
native rollout.6Dev anchor gaps chưa đóng. Không GPU/commit mới;4/7≈57% giữ nguyên.
Final QA806focused+286integration, setup/Ruff/mypy474/knowledge/diff đạt;
182nativepins không đổi. Không dùng số tests làm tỷ lệ nghiệm thu.

## Hiện hành — ExitPair GPU terminal audit, 2026-09-21

[Report](../docs/evaluation/phase5_exit_gpu_v1_report.md):4completed/8validguard,
8GRACEFUL/0forced,4VRAM recoveries; tất cả exit stages return. Hai audits khớp,
182source/242raw/2remote;scan253files/0credentials. Source `6d039e2` không đổi,
final QA773focused +180integration, setup/Ruff/mypy468/knowledge/diff đạt;
actual notebookv1/ID135130970 COMPLETE sau download07:28:29UTC.
Không pending/resubmit; chưa root cause/fix vì lỗi không tái hiện. Còn coverage
matrix/representative quality/utility, lifecycle reliability và20DoD freeze.
Phase5 vẫn4/7≈57%; không nâng acceptance từ một diagnostic thành công.

## Hiện hành — ExitPair exact package, 2026-09-20

[Report](../docs/evaluation/phase5_exit_pair_package_v1_report.md): hai isolated
offline layouts đạt, 176 worker files/182 source pins, 74 package/release tests.
Final QA 763 focused + 180 integration, setup/Ruff/mypy467/knowledge đạt.
Source `6d039e2` đã push main; committed release hai layouts cũng đạt.
Actual `huylmhuhu/react-vn-exit-milestones-v1` v1/ID135130970 RUNNING lúc
2026-09-20 16:57:50 UTC, code/settings/version đã xác thực. Một submit;
còn terminal download/audit, chưa GPU result mới.
Phase5 vẫn4/7≈57%; không đồng nhất số tests hoặc việc đóng gói với acceptance.

## Hiện hành — ExitPair/runner và native audit wiring local, 2026-09-20

[Report](../docs/evaluation/phase5_exit_pair_cpu_v1_report.md):
54 tests mới, QA02 689 focused + 180 integration, setup/Ruff/mypy462/knowledge đạt.
Controls02 có 4 completed + 4 lỗi guard dự kiến, 16 reaped;
audits trước/sau resume khớp. Không đổi frozen workers; chưa native package/GPU.
Đã sửa host audit để bind interpreter run identity, không dùng OS/Python máy Mac.
Giữ local theo owner, không mặc định commit sau QA. Phase 5 vẫn 4/7 ≈ 57%.

## Hiện hành — exit milestones CPU acceptance, 2026-09-20

[Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md):
backend opt-in, kế thừa worker methods frozen; hooks chỉ trong child. 18/18 reaped,
hai audits khớp; phân biệt kẹt target/finalizers/thread shutdown bằng PID/timing.
53 tests mới; final QA 666 focused + 149 integration, setup/Ruff/mypy454/knowledge
đạt; 172/142/86/175 frozen pins nguyên. Chưa native cause/fix; còn native runner
receipt join + exact package trước GPU. Phase 5 vẫn 4/7 ≈ 57%, không job mới.

## Hiện hành — post-serve teardown CPU controls, 2026-09-17

[Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md):
18 workers/6 modes×3 repeats, đủ 18 reaped; 6 GRACEFUL/9 TERMINATE/3 KILL là
expected fault controls. Hai audits khớp; final QA 623 focused + 133 integration,
setup/Ruff/mypy450/knowledge đạt. Chưa xác định GPU teardown cause, chưa tăng grace2s.
Cần native exit milestones/protocol riêng. Không Kaggle run mới; Phase5 vẫn4/7≈57%.

## Hiện hành — constrained GPU v1 COMPLETE/audit, 2026-09-17

[Report](../docs/evaluation/phase5_constrained_gpu_v1_report.md),
[submission](../experiments/manifests/phase5_constrained_gpu_submission02.json):
actual `huylmhuhu/react-vn-constrained-guard-v1`, version 1/ID134673914,
COMPLETE post-download 03:43:34 UTC, source `0d4e82f` remote khớp. Private/offline/T4.
Release wrapper/summary có 64 tests mới; final QA02 573 focused + 105 integration đạt.
Hai audits byte-identical: 172 source/238 raw/2 remote, 4 completed/8 valid
guard responses; 8 workers reaped/4 recoveries, nhưng 4 forced terminations.
Còn quality/lifecycle analysis; không submit lại, chưa quality claim. Phase 5 vẫn 4/7≈57%.

## Hiện hành — constrained exact package, 2026-09-16

[Report](../docs/evaluation/phase5_constrained_package_v1_report.md):
notebook/bootstrap/builder mới qua development archive + expanded offline rehearsal;
166 worker files/172 source pins, đủ 8 tools, 21 Dummy và constrained controls/resume.
15 unit tests mới đạt; final QA 495 focused + 105 integration,
setup/Ruff/mypy444/knowledge đạt. Development mode chặn native để QA trước commit an toàn.
Source `0d4e82f` đã push main; committed package01 lặp hai layout đạt,
[receipt](../experiments/manifests/phase5_constrained_probe_package01.json).
Còn remote authentication rồi GPU; chưa job mới,
không quality claim. Phase 5 vẫn 4/7≈57%. Skill đã ghi quy tắc gom commit theo owner.

## Hiện hành — constrained runner/native join, 2026-09-16

[Report](../docs/evaluation/phase5_constrained_probe_v1_report.md):
runner/checkpoint và token-count join vào native policy/attention/HF metrics đã có;
32 tests mới qua; final QA 480 focused + 105 integration tests đạt.
Controls02 giữ 4 completed/4 expected errors, resume không retry.
Còn notebook/bootstrap/exact-package/remote authentication trước GPU. Không mới
native inference, không quality claim; Phase 5 vẫn 4/7≈57%.

## Hiện hành — constrained host/runtime CPU, 2026-09-16

[Report](../docs/evaluation/phase5_constrained_host_v1_report.md), source `e04cd8d`:
37 tests mới qua; final QA 438 focused + 90 integration tests đạt.
Host classifier/cache và runtime/sidecar/witness/constraint join
đã nối. CALC/DOC × A2/A6 dùng spawned synthetic workers; không native inference.
Còn native release metrics join, candidate runner/checkpoint/package, rồi GPU.
Phase 5 vẫn 4/7≈57%; các mục dưới là lịch sử.

## Hiện hành — native generation CPU v2 COMPLETE/audit, 2026-09-16

[Report/receipts](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md):
hai ca JSON + EOS thật, 28 token/ca; ForcedBOS/interrupt xử lý đúng và restore.
Hai audits byte-identical, 142 source pins; 401 focused tests / 21,87s đạt.
Không pretrained weights/GPU/quality. Không còn job CPU pending; bước tiếp là
host classifier/cache/benchmark auditor integration, rồi GPU preflight riêng.
Phase 5 vẫn 4/7≈57%; các mục dưới là lịch sử, không phải lệnh submit hiện hành.

## Hiện hành — constrained worker composition / native CPU, 2026-09-16

[Report](../docs/evaluation/phase5_constrained_generate_cpu_v1_run.md).
Worker nối policy/attention/observer đã có30tests mới; góiCPU01 qua cả2layout.
ActualGenerationMixin CPUv1 đãERROR trướcchainadmission,0completed cases,hook restored.
Đã reproduce6int/float expected-policy mismatches từ pinnedwheel; sourceb4ae0f7
sửa expectedpin và regression (78focused tests). Chuẩn bị riêngCPUv2; khôngGPU.
Còn hostclassifier/cache/auditor và productionguardquality/lifecycle/utility.
Phase5vẫn4/7≈57%. Các mục dưới là lịch sử, không dùng làm chỉ dẫn gửi lại.

## Hiện hành — constrained adapter CPU, 2026-09-16

[Contract/report](../docs/evaluation/phase5_constrained_guard_v1_cpu.md):
adapter opt-in + classifier cache bound decoding đã triển khai;47tests mới đạt.
Giữ repetition1.1, exact chain admission, completion/identity/retirement và
restoration. Chưa paired-factory/observer composition hoặc native model.generate.
QA source964c51b:340focused tests/15,57s; setup/Ruff/mypy426/knowledge đạt,
175baseline+86nativeCPU sourcepins nguyên; kiểm live config trước cache hit.
Tiếp theo native CPU integration rồi package/protocol mới; không GPU job mới.
Phase5vẫn4/7≈57%; các mốc bên dưới là lịch sử, không phải chỉ dẫn hiện hành.

## Hiện hành — native-library CPU COMPLETE/audit, 2026-09-16

[Report/receipts](../docs/evaluation/phase5_guard_language_native_v1_run.md):
tokenizerQwen đủ3069values/max36tokensinclEOS,248actualTransformersmask checks;
10raw/2remote/86sourcepins, hai local audits giống nhau.58tests đạt.
Đã đóng tokenizer/CPU-library compatibility, chưa native model generation hay
quality. Còn adapter/processor-composition admission/audit/package; không jobpending.
Phase5vẫn4/7≈57% acceptance; không quy đổi sốchecks thành acceptance.

## Hiện hành — finite-token language CPU, 2026-09-16

[Report/receipt](../docs/evaluation/phase5_guard_token_language_v1_report.md).
Đã triển khai bộ ràng buộc3069JSON schema-value combinations, không repair,
46focused tests (30new) đạt; hai probes từ source2017e24 giống nhau.
Chỉ dùng codec CPU giả lập; chưa actualtokenizer/nativeadapter/GPU/quality.
Bước tiếp: Qwen tokenizer admission + Transformers5.5 mask CPU, rồi adapter
và exactpackage. Phase5vẫn4/7≈57%; không submit bare-json-v2 cũ.

## Hiện hành — candidate terminal audit, 2026-09-16

[Bare-JSON v1 report](../docs/evaluation/phase5_guard_bare_json_terminal_v1.md):
4/4 checkpoints đã audit, notebook vẫn ERROR ở bước auditCLI. Hai local audits
giống nhau, không chạy lạiGPU. 2/6 guard responses valid,4fenced lỗi:
chưa cải thiện so observer baseline. 8reaped/4recovered, còn1forcedshutdown.
Phase5 vẫn4/7≈57% acceptance groups; không tăng vì chỉ hoàn thành audit.
Bước tiếp: constrained-output design/CPU controls theo protocol riêng, lifecycle
study riêng, utility và formal freeze. Không submit gói bare-json-v2 cũ.

Các mốc bên dưới là lịch sử, không phải chỉ dẫn submit hiện hành.

## Hiện hành — observer native v2

2026-09-15: notebookv1COMPLETE/audit,4taskCALC/DOC×A2/A6; version/source xác minh.
[Run report](../docs/evaluation/phase5_observer_native_v2_run.md),
[các DoD còn phải đóng](phase5_remaining.md).4model_error,2valid/4fenced guard
 responses;4toolcalls,8workersreaped/4VRAMrecoveries nhưng3forcedshutdown.
Hai audits/tables giống nhau,67focused tests đạt. Phase5vẫn4/7≈57%; mới xác định
được framing lỗi và vị trí chậm shutdown, chưa chứng minh candidate khắc phục.

2026-09-15: bare-JSON prompt candidate `f7492fa` CPU preflight01 đạt hai layout;
32 candidate tests + package checks, không model/GPU/Test. Synthetic fenced and
trailing-comma outputs remain rejected as designed. Access quota22.80h and
Datasetready/v1 recorded; candidate GPU submission is the next isolated run.

## Hiện hành — grouped Dev package v3

2026-09-15: **112/112 native terminal/audit**, [báo cáo toàn lịch](../docs/evaluation/phase5_grouped_v3_complete_report.md).
82completed/30model_error;192reaped/112recovered nhưng13forcedshutdown;
55guardvalid/30JSONinvalid+18backendfailures. Đây là100%lịchthử, **gate4/7≈57%**
không đổi. Không có jobpending; [follow-up CPU](../docs/evaluation/phase5_post_native_actions_v1.md).

Lịch sử:

2026-09-15: [shards5/6 COMPLETE/audit](../docs/evaluation/phase5_grouped_v3_batch56_report.md).
Tổng98/112audited(87,5%lịchnative),68completed/30model_error; guard41valid/30invalid
responses và18backend failures không có response.168workers reaped/98VRAMrecoveries.
Shard7 admission01 hết2GPUslots;02HTTP409; [attempt03 v1RUNNING](../docs/evaluation/phase5_grouped_v3_s7_admission_report.md)
lúc2026-09-15 05:06UTC chỉ đổi id/title, không đổi thực nghiệm. Đã gửi đủ112ca,
14ca cuối chưa audit; Phase5gate vẫn4/7≈57%.

Mốc trước:

2026-09-15: [shards3/4 COMPLETE/audit](../docs/evaluation/phase5_grouped_v3_batch34_report.md),
914 raw/4 remote hash khớp, scan918files/0credentials, hai audits/shard giống nhau.
Shard3 14 completed nhưng 0 tools, tự nói đã gửi mã; shard4 4 completed/10
model_error, 10 PRE JSON errors/4 POST backend failures. Tổng **70/112 (62,5%)**
lịch native, 50 completed/20 model_error; chưa semantic utility/ASR/FPR.
[Shards5/6 v1 RUNNING](../docs/evaluation/phase5_grouped_v3_batch56_report.md) lúc
2026-09-14 20:15 UTC; 28 ca chưa tính audited. Audit rồi shard7; không đổi
source/prompt/data. Gate vẫn4/7≈57%.

Mốc trước:

2026-09-15: [shards 1/2 native COMPLETE/audit](../docs/evaluation/phase5_grouped_v3_batch12_report.md),
1.244 raw/4 remote hashes khớp. Shard1 4 completed/10 model_error do guard JSON
syntax; shard2 14 completed và 21 guard responses hợp lệ (11 PRE/10 POST).
30 tool calls, 48 reaped workers, 28 recovered tasks. Tổng shards0–2 đạt
**42/112 ca native (37,5% lịch thử)**; không đồng nghĩa Phase5 accepted.
[Shards3/4 v1 đang RUNNING](../docs/evaluation/phase5_grouped_v3_batch34_report.md),
kiểm 2026-09-14 19:03 UTC; 28 ca mới chưa cộng vào audited coverage.
Không rerun/đổi prompt cho ca thất bại. Gate vẫn 4/7≈57%.

2026-09-14: [package v3](../docs/evaluation/phase5_grouped_package_v3_report.md),
source `0d86536`, đã đạt 170-file complete archive, hai layout/fresh venv,
8 tools/recovery + 21 clean Dummy + 112 grouped stub/resume mỗi layout.
175 source/4.166 raw/16 kernel hashes recheck khớp. Full QA **3.113 pass/1 skip**
(1.060,05s), setup/Ruff/mypy392/knowledge đạt; 555 source/7 raw/169 data hashes khớp.
Native shard 0 [v1 COMPLETE/audit](../docs/evaluation/phase5_grouped_v3_s0_report.md):
380 raw/2 remote hash khớp, 14 completed/recovered, 22 graceful/2 terminate,
24 workers reaped. **0 tool calls/0 guard classifications**, cả 14 trả ngay M208:
chưa chứng minh utility/guard quality. Chuẩn bị shards 1/2 theo lịch đã chọn trước.
Giữ **4/7≈57%** aggregate gates; CPU package không chứng minh LLM quality.
Kết luận isolation của v2 compile/import receipts đã thu hồi do editable-install
fallback và root `configs`; giữ raw lịch sử, không dùng valid=true để nghiệm thu.

## Mốc trước — grouped Dev runner/checkpoint

2026-09-14: [grouped runner v1](grouped_runner_v1.md), source `354b75b`, đã đạt
27 focused tests (112 ca/8 shards + kiểm tra resume, tampering và giữ lỗi).
Full QA **3.055 pass/1 skip/973,70s** đã đạt; setup/Ruff/mypy381/knowledge đạt,
537 source/1.783 raw/169 data hashes kiểm lại khớp. [CPU receipt](../experiments/manifests/phase5_grouped_runner_v1_cpu01.json)
đã chốt, không còn QA chạy; không đóng thêm aggregate gate. Native v2 adapter đã
ghép; preflight v2 chỉ có compile/hash, kết luận exact import bị thu hồi như trên.
Native exact
package, grouped Dev LLM/lifecycle/quality và freeze còn mở; vẫn 4/7≈57% theo
aggregate gates, không phải 57% thời gian/công sức. Không GPU job mới.

## Mốc trước — bounded SQL row scope / runtime v10

2026-09-14: [SQL scope v5/runtime v10](sql_scope_v5.md) đạt bounded CPU:
full **3.028pass/1skip/847,08s**, 120focused/44,59s; setup/Ruff/mypy376/knowledge.
531source/463raw/169data hashes khớp; 30scripted runtime receipts. Row/column
permission và pre-Broker controls đạt, không đồng nghĩa model quality. Còn Dev
runner/checkpoint/exact package, native GPU lifecycle/guard quality và freeze.
Không đóng thêm gate từ CPU; vẫn 4/7≈57%, không GPU job mới.

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
