# Bàn giao phiên làm việc

Cập nhật: 2026-09-23. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

**Dev32 v2 COMPLETE/audit; bước tiếp là evaluator-only Dev scoring.**
[Terminal report](../docs/evaluation/phase5_clause_dev_gpu_v2_terminal_report.md),
[selected receipt](../experiments/manifests/phase5_clause_dev_v2_gpu_terminal01.json).
Actual notebook [v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version1/ID135499833, source `ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e`,
private/offline/T4, Dataset guard15v1. Terminal trước/sau download COMPLETE,
source/metadata/version khớp. Raw `results/phase5_clause_dev_v2_gpu_monitor01/raw`
có 2.073 files; 2 remote files, 222 source pins, 8 shards/32 tasks được hai
audits độc lập byte-identical. Host descriptive report chạy lại từ hai audits
cũng byte-identical; 67 targeted tests/setup/Ruff/mypy502 đạt. 65/65 guard
responses `OK`, 8 tasks không gọi guard, 31/32 all-workers graceful, một
guard TERMINATE; không tự suy ra ASR/FPR/utility. Known credential scan
2.077 files/3 values có 0 matches. Không Test/private GT, không inference mới.

Bước cụ thể: khóa evaluator-only Dev scoring protocol/denominators/error handling
trước khi đối chiếu traces với oracle Dev; giữ raw và v1 ERROR/release01 rejection
bất biến. Không rerun notebook để chọn kết quả tốt hơn, không mở held-out Test.
Sau đó cập nhật DoD5/15/20 theo bằng chứng, quality/lifecycle limitations và
formal freeze. Phase5 vẫn 4/7≈57%. Quyền: không thiếu Kaggle; raw chưa backup
riêng ngoài máy. Receipt/báo cáo terminal hiện local, gom một commit sau khi
QA/knowledge-check đầy đủ; không status-only commit hoặc amend source worker.

Mốc trước — v2 RUNNING (quan sát lịch sử):

**Dev32 v2 RUNNING; không submit lại.** Actual
[huylmhuhu/react-vn-clause-dev32-v2](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v2)
version 1/ID 135499833, private/offline/T4, source
`ad152ff8c8970df28cd6b5b0a0eebd02481b8e1e` đã push GitHub main.
[Release02](../experiments/manifests/phase5_clause_dev_package_v2_release02.json)
qua hai layouts/222 committed source pins/213 worker files;
[QA03](../experiments/manifests/phase5_clause_dev_package_v2_qa03.json)
981 focused + 395 integration, Ruff/mypy501/setup/knowledge đạt.
[Submission](../experiments/manifests/phase5_clause_dev_v2_gpu_submission01.json)
đã xác minh remote source/settings/version; live 09:55:43 UTC 2026-09-23 là
RUNNING, chưa có model result. Dataset guard15 private/ready/v1; quota còn
29,73h lúc submit. Không Test/private GT, không semantic retry.

Bước cụ thể: monitor v2 read-only. Khi terminal, tải một lần vào thư mục mới,
ghi source/version/status trước-sau và chạy `audit_phase5_clause_dev_gpu_v2.py`
hai lần độc lập trên raw bất biến. Nếu ERROR, giữ partial và phân loại lỗi trước
mọi lần thử khác. Sau audit mới chấm quality/benign utility/lifecycle; formal
Phase5 vẫn 4/7≈57%. Quyền: tài khoản Kaggle hiện có đủ; bạn Minh cần quyền
Kaggle riêng nếu dùng tài khoản khác. Raw chưa có backup riêng ngoài máy.

Mốc trước — v1 failure và chuẩn bị v2 (không phải trạng thái hiện hành):

**Dev32 v1 terminal ERROR; v2 đã qua development package và QA, chưa submit.**
[Failure report](../docs/evaluation/phase5_clause_dev_gpu_v1_failure_report.md),
[v2 report](../docs/evaluation/phase5_clause_dev_package_v2_report.md),
[QA03](../experiments/manifests/phase5_clause_dev_package_v2_qa03.json),
raw `results/phase5_clause_dev_gpu_monitor01`, audit
`results/phase5_clause_dev_failure_audit01` và `audit02`.
Actual [v1](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1)
version1/ID135340687 ERROR lúc08:39:20UTC2026-09-22;remote source/settings
vàdownload-before/after version khớp.12raw files;0/32completed,
0native-generation receipts;baseline/environment/recovery của ca đầu giữ nguyên.
Traceback native `constrained` truyền hai lần, trước worker start.
`clause_dev_dispatch_v2` bỏ caller-supplied root ở native; test tái hiện v1 TypeError
và xác nhận v2 dùng root của factory, không load weights. V1 source/output bất biến.
Gói v2 development hai layouts mỗi layout 8 tools/21 Dummy/32 Dev/8 shard audits;
QA02: 980 focused + 395 integration, setup/Ruff/mypy501/knowledge/diff đạt;
182 native source và 169 tracked data pins giữ nguyên. Read-only Kaggle preflight
ngày 2026-09-23: GPU còn 29,73h, Dataset guard15 private/ready/v1, v1 ERROR.

Source freeze `24164d8` đã push main. Rehearsal committed
`build/kaggle/phase5_clause_dev_package_v2_release01` qua hai layouts nhưng
host validator có allowlist cache v1 thay vì v2; release01 bị từ chối trước
Kaggle. Sửa riêng auditor và regression test đã qua QA03: 981 focused,
395 integration, Ruff/mypy501/setup/knowledge. Bước cụ thể: chốt commit sửa
lỗi, dựng release02 từ commit đó, xác thực release,
kiểm tra v2 notebook chưa tồn tại rồi submit một lần v2 private/offline/T4
cho đúng 32 ca cố định. Không dùng release01; không resume v1 hay semantic retry.
Sau v2 terminal mới download/source audit/quality analysis. Hiện không Kaggle
job pending của v1; v2 chưa submit. Không Test/privateGT; formal4/7≈57% chưa đổi.

Mốc trước — submission v1 khi còn RUNNING (lịch sử):

**32Dev đang chạy Kaggle, một submission; không gửi lại.**
Live07:10:42UTC2026-09-22: actual=requested
[huylmhuhu/react-vn-clause-dev32-v1](https://www.kaggle.com/code/huylmhuhu/react-vn-clause-dev32-v1),
v1/ID135340687,RUNNING;source`5a2352834a791b11824a7c0c69e82f2390a03ca0`
đã commit/pushmain một lần. Private/offline/T4/timeout14400s;Dataset guard15v1.
[Submission](../experiments/manifests/phase5_clause_dev_gpu_submission01.json),
[committed package](../experiments/manifests/phase5_clause_dev_package_release01.json),
[report](../docs/evaluation/phase5_clause_dev_package_v1_report.md).
Hai committed layouts mỗi8tools/21Dummy/32Dev đạt;218source release pins xác thực;
remote code/settings/version khớp. QA976focused+395integration/setup/Ruff/mypy495
đạt trướcfreeze;model generation/deadlines không đổi. Không final/Test inference.
Rawsubmission `results/phase5_clause_dev_gpu_submission01`;releasebundle
`build/kaggle/phase5_clause_dev_package_release01`;QA `results/phase5_clause_dev_package_qa02`.

Bước cụ thể: read-only monitor đúngv1. Khi terminal tải vào thư mục mới, lưu
version/source trước-sau download và chạy`audit_phase5_clause_dev_gpu_v1.py`hai lần.
Nếu ERROR: giữ partial checkpoints/logs, phân loại infrastructure/semantic;
không tự repush hoặc retry semantic. Model outcomes chưa biết,không suy từCPU32/32.
Nguồn đã freeze: không sửa218pinned files. Receipt/memory saufreeze đanglocal;
không tạo status-onlycommit. Quyền:account đã đủ,networkapproval sandbox khi cần;
raw chưabackup riêng. Formal4/7≈57%chưađổi;quality/lifecycle/DoDfreeze cònmở.

Mốc trước — development package:

**Dev32 exact package đã qua development preflight; đang chuẩn bị source freeze.**
[Report](../docs/evaluation/phase5_clause_dev_package_v1_report.md),
[package](../experiments/manifests/phase5_clause_dev_package_dev01.json),
[QA02](../experiments/manifests/phase5_clause_dev_package_qa02.json).
211worker/218source pins; hai layouts mỗi layout8tools/21Dummy/32Dev,
prefix/missing-only/complete-resume và8auditCLI đạt;1.027raw/layout.
88tests mới;976focused/56,23s+395integration/403,50s đạt;setup/Ruff/mypy495/knowledge/diff đạt.
182native/169data pins giữ nguyên;scan2.278files/0credentials. Raw build
`build/kaggle/phase5_clause_dev_package_dev04`; development01–03 giữ lỗi cũ.
Native đường mới chỉ chấp nhận committed source; oldCPU runner vẫn khóa HF.
QA01 bị từ chối source đổi giữa run; QA02 ổn định là bằng chứng dùng.

Bước cụ thể: một source-freeze commit/push cần thiết, committed rehearsal vào
thư mục mới và `audit_phase5_clause_dev_gpu_v1.validate_package`, rồi submit một lần.
Lịch32Dev giữ nguyên;8shards tuần tự,session cap14400s,T4/private/offline;
không đổi deadline/model/prompt, không thêm4taskGPU diagnostic. Chưa submission.
Live `results/phase5_clause_dev_kaggle_preflight03`:ownerhuylmhuhu,29,75hGPU,
Dataset guard15 private/ready/v1;notebook cũ COMPLETE. Dùng systempython3 cho
KaggleCLI2.2.4;venv không có kaggle. Requested `huylmhuhu/react-vn-clause-dev32-v1`
chưa actual. Không cần account mới;raw chưa backup riêng. Test/privateGT không đọc.
Formal4/7≈57% chưa đổi. Sau submit chỉ monitor/tải/audit, không push trùng.

Mốc trước — Dev32 CPU runner:

**Đã đóng CPU gate cho runner32Dev A2/A6; native dispatch chưa mở.**
[Report](../docs/evaluation/phase5_clause_dev32_v1_report.md),
[contract](../docs/architecture/phase5_clause_dev32_v1_contract.md),
[controls](../experiments/manifests/phase5_clause_dev32_cpu01.json),
[audit](../experiments/manifests/phase5_clause_dev32_audit01.json).
32completed/8shards/16publicDev;64GRACEFUL workers reaped,32synthetic recovery.
188source/928raw pins kiểm riêng, hai audits/shard và complete-resume không đổi raw.
23tests mới; [QA02](../experiments/manifests/phase5_clause_dev32_qa02.json):888focused+
395integration,setup/Ruff/mypy488/knowledge/diff đạt;182native/169data pins nguyên.
Raw `results/phase5_clause_dev32_cpu01`, audits `results/phase5_clause_dev32_audit01`,
QA `results/phase5_clause_dev32_qa02`; QA01 cũng hoàn tất và giữ lại.
Không chấm utility/ASR từ scripted agent; recovery/teardown chỉ synthetic.
`clause_dev_native_audit_v1` nối token/count/constraint evidence nhưng KHÔNG
model-source/release authentication. `clause_dev_runner_v1.run` từ chối HF trước output.

Bước cụ thể tiếp theo: native source/release admission và launcher cho32Dev,
rồi exact archive/expanded rehearsal. Đọc Kaggle preflight +skill trước đóng gói.
Chỉ mở HF sau cổng này; source freeze/commit chỉ khi cần cho thực nghiệm thật,
không commit status. Giữ manifest32ca/seed/model/settings, frozen worker và
mọi failure; không lặp4task GPU diagnostic, không chọn ca theo model output.
Source hiện là base6d039e2 +working-tree pins, chưa GitHub source freeze mới.
Không pending Kaggle hoặc model/GPU/commit/push mới, không Test/private GT parsing.
Quyền còn thiếu: chưa cần tài khoản mới; raw chưa có backup riêng ngoài máy.
Formal4/7≈57% chưa đổi: native quality/utility, lifecycle và DoD freeze còn mở.

Mốc trước — constrained ExitPair integration:

**Đã nối v12 vào constrained ExitPair và kiểm toán riêng, CPU gate đạt.**
[Report](../docs/evaluation/phase5_clause_pair_v1_report.md),
[contract](../docs/architecture/phase5_clause_pair_v1_contract.md),
[controls](../experiments/manifests/phase5_clause_pair_controls01.json),
[audit](../experiments/manifests/phase5_clause_pair_audit01.json).
Raw `results/phase5_clause_pair_controls01`; full audits `results/phase5_clause_pair_selected01`.
12tasks/24workers reaped:4valid completed +4deliberate model_error +4egress controls.
20GRACEFUL/4TERMINATE (forced chỉ ở deliberate failures), chưa native reliability.
Egress A6public ALLOW; A6sensitive/A6unknown/A5public DENY đúng kỳ vọng. Hai audits
và complete-resume không đổi raw.184source/348raw pins khớp;scan349files/0credentials.
36new tests đạt; [final QA](../experiments/manifests/phase5_clause_pair_qa01.json):
879focused/50,17s +381integration/305,62s, setup/Ruff/mypy483/knowledge/diff đạt.
Logs `results/phase5_clause_pair_qa01`;182native pins +7prior candidate pins
+169tracked data hashes không đổi. Full pytest loại sealed Test-authoring fixtures.
Nguồn cũ v12/78controls và native182pins giữ nguyên; không Test/private GT parsing.
Không model lớn/GPU/commit/push mới; không có Kaggle job pending.

Bước cụ thể: chuẩn bị runner/manifest32Dev A2/A6 + independent native release
audit trên `clause_pair_runtime_v1`; profile mới `security_runtime_v12_constrained_exit_v1`.
Không chạy GPU4task probe mới chỉ để lặp dữ liệu teardown. Probe4task hiện là
CPU/package control. Phải gắn source closure, input/environment/model/generation
hashes, scopev5 + originv3, constraint cache/exit joins vào32task checkpoint;
giữ failures và missing-only resume. Sau đó exact archive/expanded rehearsal,
kiểm quota/private mounts, source freeze cần thiết rồi submit một lần.
Outer scope pre-start cũng cần ResourceBindings/RowBindings từ host catalog;
đừng chỉ nối constructor trong inner runtime. Audit cross-host dùng recorded
interpreter, không dùng mặc định máy Mac. Không dùng metadata version để giả nâng runtime.
Quyền còn thiếu: chưa cần account mới; raw chưa có backup riêng ngoài máy.
Formal acceptance không đổi: quality/utility, native lifecycle và DoD freeze còn mở.

Mốc trước — clause/warm-runtime CPU (đã có paired integration ở trên):

**Clause authorization v3/runtime v12 đã qua 78/78 CPU controls.**
[Report](../docs/evaluation/phase5_clause_candidate_v1_report.md),
[contract](../docs/architecture/phase5_clause_authorization_v3_contract.md),
[receipt](../experiments/manifests/phase5_clause_candidate01.json),
[Dev coverage](../experiments/manifests/phase5_clause_coverage01.json).
Raw `results/phase5_clause_candidate01`; selected `results/phase5_clause_selected01`.
157source/1.400raw pins kiểm riêng;scan1.401files/0credentials. 67new unit +65new
integration đạt; [final QA](../experiments/manifests/phase5_clause_qa01.json):
873focused/60,91s +351integration/310,06s, setup/Ruff/mypy478/knowledge/diff đạt.
Logs `results/phase5_clause_qa01`;182native pins +169data hashes không đổi;
10prior acceptance source pins nguyên. Không full pytest vì Test-authoring fixtures.
Cumulative A1–A6 dùng cùng parser; A0 giữ v10. Sáu Dev đích gửi đã nhận đúng;
payload sensitivity/unknown-lineage/guard veto/final gates vẫn độc lập.
`value_origin_v3` chỉ bổ sung literal đích từ raw host-user, giữ labels/hash/budgets;
sửa false-denial email trước dấu chấm, không chữa toàn bộ extractor punctuation.
Không Test/private GT parsing, không model/GPU/commit/push; source base6d039e2
+working-tree pins, không được gán source mới cho GitHub commit cũ.

Bước cụ thể tiếp theo: tích hợp runtimev12 và originv3 vào constrained ExitPair
(native hiện vẫn dùng scopev3/runtimev8, KHÔNG tự coi đã nâng cấp). Cần bind
HostClassifier/PROMPT giữ finite-language/cache identity, metadata runtime mới,
independent audits/runner checkpoint/source closure và tests spawned pair; giữ
frozen worker/old receipts. Sau đó exact archive+expanded rehearsal, source freeze
thật sự cần thiết, rồi32Dev A2/A6 đã chọn. Không resubmit diagnostic cũ.
Parser cố ý từ chối toàn bộ quoted/conditional/reported instructions và unsupported
prefix; chưa phải parser ngôn ngữ tổng quát. Native quality/lifecycle/freeze còn mở.
Quyền còn thiếu: không cần account mới; raw chưa có đích backup riêng ngoài máy.
Không job Kaggle pending, formal acceptance vẫn4/7≈57%.

Mốc trước (v11 là lịch sử, đã có v12 CPU ở trên):

**Coverage + bounded A6 authorization candidate đã có CPU evidence.**
[Report](../docs/evaluation/phase5_acceptance_controls_v1_report.md),
[matrix](../experiments/manifests/phase5_acceptance_coverage01.json),
[baseline](../experiments/manifests/phase5_acceptance_baseline01.json),
[candidate](../experiments/manifests/phase5_acceptance_candidate01.json).
Không đổi benchmark/Test/frozen worker. Public Dev16fixtures/8cặp giữ seed cũ;
native candidate workload32taskA2/A6 vẫn dispatch=false. Sáu fixtures có raw-user
destination anchor chưa nhận; không đồng nghĩa sensitive payload được phép gửi.
Synthetic baselinev10:26/26semicolon,17/26period;9failures giữ nguyên.
Opt-in A6runtimev11+anchorv2:52/52controls đạt;A0–A5 delegatev10, chưa cumulative
native release.27parser+6coverage+54baseline+52candidate tests mới;
[final QA](../experiments/manifests/phase5_acceptance_qa01.json):806focused+
286integration đạt, setup/Ruff/mypy474/knowledge/diff đạt,182nativepins nguyên.
Raw `results/phase5_acceptance_controls01`, `results/phase5_sentence_candidate01`;
52executions/run,933raw/run;scan1868files/0credentials. Không model/GPU/commit/push.
Bước cụ thể: thiết kế/test quyền-cấm theo raw clause spans và quote context;
giải quyết6Dev anchor gaps mà không cho sensitive egress, kiểm cumulative/A0
parity/native pair trước exact package/source freeze. V11 chỉ giải quyết bounded
read-then-send, không coi compound prohibition đã giải quyết. Không job pending.
Hardening bắt buộc trước promote: read-prefix dạng tường thuật không quote,
quote xuyên mệnh đề và thu hồi quyền; lexical READ không phải resource grammar.
Quyền còn thiếu: chưa cần account mới; backup raw riêng tư vẫn chưa có đích.
[Bản đồ20DoD](../docs/evaluation/phase5_dod_evidence_map.md) ghi rõ evidence và
cổng candidate/quality/lifecycle/freeze; không phải acceptance20/20.

Mốc trước:

**ExitPair GPU v1 COMPLETE; terminal release audits đã khớp byte-for-byte.**
[Report](../docs/evaluation/phase5_exit_gpu_v1_report.md),
[audit](../experiments/manifests/phase5_exit_gpu_audit01.json),
[summary](../experiments/manifests/phase5_exit_gpu_summary01.json).
Post-download07:28:29UTC ngày2026-09-21:actual `huylmhuhu/react-vn-exit-milestones-v1`,
v1/ID135130970, source `6d039e2`, private/offline/T4; remote pins/settings/version khớp.
4 completed/8 valid guard responses;8GRACEFUL/0TERMINATE/0KILL,4VRAM recoveries.
Tất cả target/finalizers/threads return; lỗi teardown cũ không tái hiện, chưa root
cause/fix. Hai audits182source/242raw/2remote;scan253files/0credential matches.
Raw `results/phase5_exit_gpu_monitor01`, report `results/phase5_exit_gpu_report01`.
Không còn job pending, không submit lại. Host summary +10 tests mới; final
[QA](../experiments/manifests/phase5_exit_gpu_qa01.json):773focused +180integration,
setup/Ruff/mypy468/knowledge/diff đạt; frozen pins nguyên. Không commit/push;
giữ nguồn worker frozen, gom evidence về sau.
Bước cụ thể: chuẩn bị coverage matrix public Dev cho guard quality/benign utility
và DoD5/9/13/14/15/16; đọc nhiệm vụ và policy expectations trước chọn run manifest,
không chọn theo model success. Lifecycle cần prospective paired comparison nếu
muốn kết luận reliability/fix; không tự tăng grace hoặc rerun v1.
Quyền đang chờ: không thiếu credentials; raw chưa có backup riêng ngoài máy.

Mốc submit dưới đây là lịch sử, không phải trạng thái RUNNING hiện tại:

**ExitPair GPU v1 đã submit một lần, RUNNING lúc 16:57:50 UTC ngày 2026-09-20.**
Actual `huylmhuhu/react-vn-exit-milestones-v1`, v1/ID135130970;
[submission](../experiments/manifests/phase5_exit_gpu_submission01.json),
[report](../docs/evaluation/phase5_exit_pair_package_v1_report.md).
Private/offline/T4/timeout3600s/guard Dataset v1; source `6d039e2` đã push main.
Remote code/settings/version khớp. API trả ref có `/code/`; host check ban đầu
dừng sau push thành công, đã sửa bằng read-only verification, không submit lại.
Development + committed archive/expanded đạt:176worker/182source pins,
mỗi layout8tools/21Dummy/10fresh controls/6retained. Final QA763focused +180integration,
setup/Ruff/mypy467/knowledge/diff đạt. Không đổi frozen worker/grace2s/Test.
Bước cụ thể: kiểm tra job hiện tại; khi terminal tải vào thư mục mới, xác thực
version/source trước-sau download, chạy hai release audits và phân tích milestones.
Chưa terminal/download/native cause/acceptance. Không submit trùng, không commit
status: receipts/memory sau freeze đang local. Không thiếu credentials; chỉ cần
network approval của sandbox khi monitor. Raw chưa có backup riêng ngoài máy.

Các mốc trước (không thay trạng thái hiện hành ở trên):

**ExitPair/runner và native audit wiring đã đóng CPU QA02, chưa commit/push.**
Owner nhắc lại: không mặc định commit cuối mỗi lượt dù checks đạt. Giữ local;
chỉ commit theo yêu cầu hoặc khi cần chốt nguồn cho thực nghiệm thật.
Đã nối role/task/PID/cold-warm identity qua sidecar riêng, giữ frozen sources.
Đã sửa kiểm toán native để bind interpreter theo run identity, không theo máy Mac
đang audit. Controls01/QA01 giữ lịch sử; controls02/QA02 bind source sửa.
Chưa package/release/GPU. Final QA02: 689 focused + 180 integration, setup/Ruff/
mypy462/knowledge/diff đạt. [Report](../docs/evaluation/phase5_exit_pair_cpu_v1_report.md).

**Exit-milestone observer đã đóng CPU gate; chưa nối native runner.**
[Report](../docs/evaluation/phase5_exit_milestones_cpu_v1_report.md),
[protocol](../docs/architecture/phase5_exit_milestones_v1_contract.md).
Backend opt-in kế thừa generate/cleanup cũ; hooks chỉ trong child, PID/timing và
Python non-daemon thread counts, không payload/tên luồng. Config identity riêng.
18/18 worker reaped; đối chứng phân biệt kẹt target/finalizers/thread shutdown,
không chứng minh native GPU cause. 53 tests mới; 666 focused + 149 integration,
setup/Ruff/mypy454/knowledge/diff đạt. Không Kaggle/model/Test/private GT access.

Đã củng cố điều hướng/lưu trữ cho vault Obsidian hiện có:
[START_HERE](../START_HERE.md), [quy ước](storage_and_obsidian.md).
Không thay settings/plugin/sync; `.obsidian/` và `.trash/` ngoài Git.
Raw vẫn local, chưa có bản sao ngoài máy; chưa chọn đích backup riêng tư.

**Nền post-serve teardown CPU probe v1 đã hoàn tất.**
[Report](../docs/evaluation/phase5_teardown_cpu_v1_report.md),
[contract](../docs/architecture/phase5_teardown_probe_v1_contract.md).
18 fresh spawned workers: 6 modes × 3 reps, 2 public responses/worker. Đủ 18 reaped;
6 GRACEFUL/9 TERMINATE/3 KILL đúng fault controls. Hai audits byte-identical,
19 raw files/31 source-evidence scan/0 credential matches. 44 tests mới;
final QA 623 focused + 133 integration, setup/Ruff/mypy450/knowledge đạt.
Finalizer bị kẹt và live non-daemon thread cùng tái hiện serve-returned+forced exit;
đây là phân biệt cơ chế CPU, **không xác định native GPU root cause**.
Không đổi frozen worker, grace2s, model, prompt, Test; không job Kaggle mới.

Mốc native trước:

**Constrained GPU v1 COMPLETE/audit; không submit lại.**
Actual `huylmhuhu/react-vn-constrained-guard-v1`, v1/ID134673914;
Post-download 03:43:34 UTC ngày 2026-09-17, source `0d4e82f` authenticated,
private/offline/T4/timeout3600s/guard Dataset v1.
[Report](../docs/evaluation/phase5_constrained_gpu_v1_report.md),
[submission](../experiments/manifests/phase5_constrained_gpu_submission02.json).
Host auditor `scripts/audit_phase5_constrained_gpu_v1.py` đã có 59 tests mới,
thêm summary adapter5tests; final QA02 573 focused + 105 integration,
setup/Ruff/mypy446/knowledge đạt. Gom host code/tests/receipts/memory trong một
commit khi đóng thực nghiệm; không đổi/amend source worker.
Hai release audits byte-identical: 172 source pins/238 raw/2 remote files.
4 completed tasks, 8/8 valid guard responses, zero incomplete constraints/backend
errors; 8 workers reaped/4 VRAM recoveries. Còn 4 TERMINATE/4 GRACEFUL,
chưa guard semantic quality/utility hoặc lifecycle acceptance.
[Summary](../experiments/manifests/phase5_constrained_gpu_summary01.json),
[audit](../experiments/manifests/phase5_constrained_gpu_audit01.json).

Nền package đã đóng:

**Constrained exact package đã đạt development + committed release preflight.**
[Report](../docs/evaluation/phase5_constrained_package_v1_report.md),
[receipt](../experiments/manifests/phase5_constrained_probe_package_dev01.json).
Builder `scripts/prepare_phase5_constrained_probe_package_v1.py`, template
`notebooks/kaggle/constrained_probe_kernel_v1.py`. Development package ở
`build/kaggle/phase5_constrained_probe_package_dev01`: 166 worker files,
172 source pins; mỗi layout 8 tools, 21 Dummy, 10 fresh constrained tasks và
6 retained checkpoints. 15 tests mới đạt; final QA 495 focused + 105 integration,
setup/Ruff/mypy444/knowledge/diff đạt; 142/86/175 frozen pins nguyên.
Đã gom một commit `0d4e82f`, push `origin/main`; release rebuild ở
`build/kaggle/phase5_constrained_probe_package01` cũng qua hai layout.
[Release receipt](../experiments/manifests/phase5_constrained_probe_package01.json).
Biên bản release và memory sau freeze được gộp vào phần host release audit/report;
không thêm status-only commit, không amend source thực nghiệm.
Đã cập nhật skill commit cadence và knowledge index: không commit mỗi status,
gom việc hoàn chỉnh; source freeze là ngoại lệ cần thông báo trước.

Nền runner đã đóng:

**Đã nối constrained runner/checkpoint/native evidence join**, QA đạt.
[Report](../docs/evaluation/phase5_constrained_probe_v1_report.md),
[contract](../docs/architecture/phase5_constrained_probe_v1_contract.md).
32 tests mới qua; final QA 480 focused + 105 integration tests đạt,
setup/Ruff/mypy443/knowledge đạt. Controls02: 4 completed + 4 deliberate model_error, missing-only
resume đúng; hai valid audits byte-identical. Native boundary tests dùng mock,
runner dùng spawned synthetic workers, không phải pretrained/native GPU proof.
Owner yêu cầu bớt commit: gom implementation + QA/memory trong một commit cuối.

Mốc host/cache làm nền:

**Đã nối constrained host/cache/runtime + read-only join**, source `e04cd8d`.
[Report](../docs/evaluation/phase5_constrained_host_v1_report.md),
[contract](../docs/architecture/phase5_constrained_host_v1_contract.md).
37 tests mới đạt, gồm CALC/DOC × A2/A6 qua spawned workers và các lỗi identity,
cache/receipt/worker; synthetic CPU, không production guard. Final QA đã đạt:
438 focused + 90 integration tests, setup/Ruff/mypy437/knowledge.
Host cache kiểm ownership/worker health và receipt history, không giả nhận đã
introspect live model từ xa. Lỗi không dispatch được ghi rõ không thêm inference.

Nền native CPU đã đóng:

Đã chốt **native constrained generation CPU v2 COMPLETE/audit**;
[report](../docs/evaluation/phase5_constrained_generate_cpu_v2_run.md).
Actual notebook `huylmhuhu/react-vn-constrained-generate-cpu-v2`,
version 1/ID 134579648; source `b4ae0f7`, Dataset guard15 v1/private.
Post-download check 08:25:13 UTC ngày 2026-09-16 vẫn COMPLETE/source khớp.
Không còn notebook pending trong lịch này; không submit lại.

Hai success cases sinh JSON + EOS, mỗi ca 28 token; ForcedBOS rejected trước
forward và interrupt restored. Đây là tiny random Qwen CPU, không pretrained
guard 1.5B hoặc benchmark quality. CPU v1 thất bại vẫn lưu, không xóa/retry.

## Bước tiếp theo

1. Không còn pending ExitPair GPU v1; **không resubmit ExitPair hoặc constrained v1**.
   Giữ raw `results/phase5_constrained_gpu_monitor02`, hai audits tại
   `results/phase5_constrained_gpu_audit01.json` và
   `results/phase5_constrained_gpu_report01/release_audit.json`.
2. Terminal outputs đã tải/kiểm toán; giữ raw/audits trong các thư mục mới nêu
   ở đầu. Lỗi không tái hiện, không suy diễn instrumentation là fix.
3. Clause/cumulative candidate v12 đã nối constrained ExitPair và audit CPU;
   chuẩn bị32task runner/native release audit +exact package trước GPU.
   Giữ syntax8/8 tách khỏi semantic quality, không resubmit4task probe cũ.
   Lifecycle follow-up nếu cần phải khóa repeat/order budget riêng trước chạy;
   hoàn tất mapping20DoD trước formal freeze.
4. Giữ thay đổi local qua các lượt, không commit chỉ vì QA đạt. Commit khi owner
   yêu cầu hoặc cần source freeze thật; không status-only/amend nguồn thực nghiệm.

## Bằng chứng

- [ExitPair close02](../experiments/manifests/phase5_exit_pair_cpu_close02.json),
  [QA02](../experiments/manifests/phase5_exit_pair_cpu_qa02.json):
  `results/phase5_exit_pair_cpu_controls02` có valid4 + deliberate model_error4,
  16 workers reaped; valid8 GRACEFUL, failure4 GRACEFUL/4 TERMINATE.
  Hai audits mỗi condition trước/sau complete-resume byte-identical,
  101 valid/77 failure raw files, 31 runner source pins.
  689 focused/50,98s + 180 integration/180,37s; 172/142/86/175 frozen pins nguyên.
  Controls01/QA01/close01 giữ/excluded sau sửa cross-host interpreter binding.
  Base `5875bb7` + exact working-tree pins, không commit/push hoặc job GPU mới.
  Native wrapper tests chỉ mock/lazy; raw chưa backup ngoài máy.

- [Exit milestones close](../experiments/manifests/phase5_exit_milestones_cpu_close01.json),
  [QA](../experiments/manifests/phase5_exit_milestones_cpu_qa01.json):
  15 execution source pins, 19 raw files tại `results/phase5_exit_milestones_cpu_controls02`;
  audits `results/phase5_exit_milestones_cpu_audit01.json`/`...audit02.json` byte-identical.
  QA logs `results/phase5_exit_milestones_cpu_qa01`: 666/44,72s + 149/138,93s.
  Base Git `3cb2b54` + working-tree pins, chưa native release.
  Controls01 giữ/excluded sau harden thứ tự kiểm symlink trước đọc JSON;
  controls02 bind source mới, không semantic model retry. Raw mới vẫn local,
  chưa backup ngoài máy; không cần account mới trước bước native preflight.

- Kiểm lại ngày 2026-09-20: 50 tests chọn lọc (knowledge + teardown unit và
  integration) đạt/11,24s; setup/Ruff/mypy450/knowledge/diff đạt.
  56 source/QA-log pins và 19 raw pins khớp; audit mới ở
  `results/phase5_teardown_cpu_audit_20260920_01.json` byte-identical với audit01.
  Validator đã kiểm thêm links của START_HERE, có regression cho link hỏng,
  đường dẫn ra ngoài repo, credential link và bỏ qua vault settings.
  Ví dụ Markdown ban đầu tạo broken link giả đã sửa; rerun 50/50 đạt.
  Không chạy full pytest hoặc model, không đổi receipt thực nghiệm cũ.
- [Teardown close](../experiments/manifests/phase5_teardown_cpu_close01.json),
  [final QA](../experiments/manifests/phase5_teardown_cpu_qa01.json):
  raw `results/phase5_teardown_cpu_controls02`, audit01/02 byte-identical.
  CPU CPython3.11.0/Darwin; runtime internals và 10 execution sources hash-bound,
  Git base27626b1 + working-tree pins. 172/142/86/175 frozen source pins không đổi.
  Preparation01 thiếu cases directory, giữ identity/excluded; regression đã thêm,
  không GPU/model rerun. Final QA 623/44,37s + 133/125,28s.
- [Terminal](../experiments/manifests/phase5_constrained_gpu_terminal01.json),
  [audit](../experiments/manifests/phase5_constrained_gpu_audit01.json),
  [summary](../experiments/manifests/phase5_constrained_gpu_summary01.json).
  Scan 256 files/0 matches. Summed startup901,127s/task total947,261s;
  agent7,196 token/s và guard17,041 token/s chỉ từ joined generation, không startup.
- [Final release/report QA02](../experiments/manifests/phase5_constrained_release_cpu_qa02.json):
  573 tests/44,43s + 105 integration/111,61s; 142/86/175 frozen pins nguyên.
  [QA01 trước summary](../experiments/manifests/phase5_constrained_release_cpu_qa01.json)
  giữ nguyên (562 + 105), không ghi đè.
- Live access `results/phase5_constrained_gpu_access01`: còn 22,50h GPU,
  Dataset ready/v1. Preparation01 dừng trước push do metadata `info.isPrivate`;
  corrected submission02 mới là một job GPU thật, raw được giữ cả hai.
- Development package: 433 raw files/layout, 1.043 file scan không credential match.
  Source base `f5e97ae` + exact working-tree hashes, native submission disabled.
- Committed package01: source `0d4e82f`, 172 Git source pins/166 worker files;
  hai layout/433 raw files mỗi layout xác minh lại; scan 1.043 file/0 matches.
- [Package QA](../experiments/manifests/phase5_constrained_package_cpu_qa01.json):
  495 focused/42,96s + 105 integration/111,91s; logs trong
  `results/phase5_constrained_package_cpu_qa01`.
- [Runner/native join report](../docs/evaluation/phase5_constrained_probe_v1_report.md):
  raw `results/phase5_constrained_probe_cpu_controls02`; base Git `e655658`,
  execution source hashes bind working-tree code, chưa GPU release identity.
  Controls01 nhập nhầm base SHA được giữ/excluded. Không sửa raw hoặc chọn kết quả.
- [Final QA](../experiments/manifests/phase5_constrained_probe_cpu_qa01.json):
  480 tests/42,60s + 105 integration/112,49s; raw `results/phase5_constrained_probe_cpu_qa01`.
  [Integrity/controls](../experiments/manifests/phase5_constrained_probe_cpu_close01.json).
- [Host integration report](../docs/evaluation/phase5_constrained_host_v1_report.md):
  37 tests mới qua; [final QA](../experiments/manifests/phase5_constrained_host_cpu_qa02.json)
  có 438 focused/42,30s + 90 integration tests đạt, raw ở `results/phase5_constrained_host_cpu_qa02`.
  Source `d270830`/QA01 trước hardening giữ lịch sử, không ghi đè.
- [Submission v2](../experiments/manifests/phase5_constrained_generate_cpu_submission02.json),
  [terminal](../experiments/manifests/phase5_constrained_generate_cpu_terminal01.json),
  [audit](../experiments/manifests/phase5_constrained_generate_cpu_audit01.json),
  [summary](../experiments/manifests/phase5_constrained_generate_cpu_summary01.json).
- [QA source 8298502](../experiments/manifests/phase5_constrained_generate_cpu_qa03.json):
  401 focused tests / 21,87s; setup/Ruff/mypy433/knowledge pass; 22 auditor tests mới.
  QA local không chạy native library; kết quả native nằm trong receipt riêng.
- Hai audits `results/phase5_constrained_generate_audit02` và `..._audit03`
  byte-identical, xác minh 142 source/25 raw/2 remote files.
  Raw/remote: `results/phase5_constrained_generate_monitor03`;
  post-download observation: `results/phase5_constrained_generate_terminal04`.
- Package đúng: `build/kaggle/phase5_constrained_generate_cpu_package02`;
  [preflight](../experiments/manifests/phase5_constrained_generate_cpu_preflight02.json).
  142 active + 86 prior native + 175 baseline source pins không đổi.
- [V1 failure và diagnosis](../docs/evaluation/phase5_constrained_generate_cpu_v1_run.md),
  [Kaggle directory](kaggle_resources.md), [DoD queue](phase5_remaining.md).

## Giới hạn

Bounded constrained native syntax/release và synthetic teardown controls đã đạt;
native teardown cause, representative guard quality, benign utility,
graceful shutdown và formal freeze vẫn mở. Không full pytest vì Test-assigned
authoring fixtures; không Test/private GT access. Không cần tài khoản mới;
kiểm quota/private mounts lại khi GPU package thực sự sẵn sàng.

GitHub `Lamhuy0489` khác Kaggle `huylmhuhu`; quyền GitHub không cấp quyền Kaggle.
Giữ notebook/Dataset private, credentials ngoài Git. Không đưa memory vào prompt.
Giữ nguyên tài liệu riêng tại docs/BAO_CAO_TIEN_DO_DO_AN.*,
docs/figures/ và cấu hình Obsidian. Ngày 2026-09-20 plan/phase6–9 không còn dirty;
không phục hồi các thay đổi cũ. [Lịch sử bàn giao](history_20260916_constrained_cpu.md) không phải
chỉ dẫn submit hiện hành.
