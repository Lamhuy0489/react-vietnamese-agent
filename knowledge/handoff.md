# Bàn giao phiên làm việc

Cập nhật: 2026-09-12. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Mới nhất: [request/native-metric auditor](efficient_requests_v1.md) đã có code/CLI,
78 test mới,124 focused pass23,79s; setup/Ruff/mypy285/knowledge đạt.
FullQA2.055pass/1optional skip454,190s (JUnit), không lỗi, source35fdad8;
[QA receipt](../experiments/manifests/phase5_efficient_requests_audit_v1_cpu_qa01.json).
`results/phase5_efficient_requests_audit_v1_cpu01_pytest.xml` đã hoàn tất.
Không test job còn chạy; 277 historical raw files kiểm lại không đổi.
Chưa GPU hoặc runtime adoption; source adapter/frozen overlays/seals giữ nguyên.
Tiếp real-spawn composition: ReadyFactory ngoài cùng, progress trước load,
metrics/attention roots riêng, readiness không tiêu thụ request index. Auditor
chưa xác thực supervisor PID, native load memory/publisher policy hoặc full KV.
Không cần quyền mới cho mốc CPU; GPU tương lai cần preflight riêng.

Lịch sử adapter CPU:

Ưu tiên mới: [efficient requests v1](efficient_requests_v1.md), adapter nhiều
request variable geometry riêng,46focused tests đạt0,91s. Source039af85;
fullQA1.977pass/1optional skip437,99s, setup/Ruff/mypy283/knowledge đạt.
[CPU QA](../experiments/manifests/phase5_efficient_requests_v1_cpu_qa01.json).
Chưa GPU hoặc nối runtime. Không cần quyền mới cho mốc CPU đã kiểm;
GPU tương lai cần preflight riêng. Receipt/native-metric auditor nay đã có;
tiếp real-spawn composition, rồi native repeated-request proof. Runtime integration
cần task owner agent-only cho A0/A1 và routing guard trực tiếp cho A2–A6;
không spawn ModelPair lồng trong WarmGuardFactory hoặc sửa frozen v5.

Owner yêu cầu làm luôn model integration sau tensor pass. Đang triển khai
[efficient stress v1](efficient_stress_v1.md): core/factory/dispatcher/auditor/
42filewrapper/builder và72focused tests đạt; real-spawn mới READY hai roles,
không weights. Source5267218; fullQA1.931pass/1optional skip389,21s, setup/Ruff/
mypy282/knowledge đạt. Exact42file hai layouts đạt trong clean checkout riêng;
quota28,02h/private Datasetv1ready. [QA](../experiments/manifests/phase5_efficient_stress_gpu_v1_pre_submit_qa01.json).
Source/QA đã pusha66514e; kernel `huylmhuhu/react-vn-efficient-stress-v1`
version1 COMPLETE một submission. 90raw/2remote files xác thực; audits01/02
byte-identical. Native full-context đạt4096+512/128 và fullKV4608/4224 trên đủ
28layers/model, không OOM. Generation48,447/6,085s có instrumentation;
agentpeak10,408/5,077GiB và guard3,248GiB trong caps.2TERM/-15/reaped,
6recovery samples residual0 haiGPU,0graceful. Không job còn chạy.
[Báo cáo](../docs/evaluation/phase5_efficient_stress_gpu_v1_report.md).
Tiếp versioned normal-request attention/ModelPair runtime integration; current
stress backend single-use/fixed geometry không dùng trực tiếp cho ReAct.
Không resubmit tensor/context/efficient identities hoặc sửa source5267218.

[Context/policy GPU v1](context_policy_gpu_v1.md) đã ERROR sau một submission,
không còn job RUNNING. Giữ nguyên 59 raw và 2 remote files; bootstrap/source/
metadata/Dummy/agent load/recovery đã kiểm. Agent lỗi sau load khoảng 259 giây,
guard chưa khởi động, không stress generation. Factory nhận ReadyBackend thay
vì native backend. [Failure receipt](../experiments/manifests/phase5_context_policy_gpu_v1_failure01.json).

[V2](../docs/architecture/phase5_context_policy_gpu_v2_contract.md) đã sửa: đưa
ReadyFactory ra ngoài progress/policy instrumentation. CPU real-spawn control
đã tái hiện bản cũ BACKEND_FAILURE và bản sửa READY cả hai roles, không weights.
36-file wrapper/builder mới thêm phép kiểm tra factory cho cả hai layouts.
Source `0a97953` đã commit, exact preflight cả hai layouts đạt (36 overlay files).
37 focused tests và full 1.825 pass/1 optional skip trong 394,49 giây; setup,
Ruff, mypy 270 files, knowledge đạt. Hai standalone real-spawn rehearsals từ
commit này khớp summary, 6 PID khác nhau/reaped, không model load.
[Pre-submit QA v2](../experiments/manifests/phase5_context_policy_gpu_v2_pre_submit_qa01.json).
Source/QA đã push `a39a9e6`; một kernel v2 version 1 đã chạy và ERROR.
Lỗi factory v1 không lặp: cả agent/guard native READY; load 232,950/30,953 giây.
Agent gặp OutOfMemoryError sau 1,134 giây trong stress 4096 token; guard chưa
chạy stress. Giữ nguyên 69 raw và 2 remote files, [failure receipt v2](../experiments/manifests/phase5_context_policy_gpu_v2_failure01.json).
Policy agent resolve/length/hook restore khớp; 2 TERMINATE/-15, 6 recovery
samples residual 0 trên cả hai GPU. Không full context/KV hoặc graceful claim.

Owner đã đồng ý [chẩn đoán/attention tiết kiệm VRAM](../docs/evaluation/phase5_context_policy_v2_oom_review.md).
Đã COMPLETE [SDPA tensor v1](sdpa_tensor_v1.md), không weights,10fresh
processes và predeclared parity/cap. Runner/28filewrapper/auditor đã có;
Source5aabea0,34focused/full1.859pass1optional skip379,56s; setup/Ruff/mypy275/
knowledge đạt. Hai exact28file layouts đạt trong clean checkout riêng vì
plan/phase6–9 có chỉnh sửa ngoài task (giữ nguyên, không commit).
[QA](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_pre_submit_qa01.json),
[package và đường dẫn](sdpa_tensor_v1.md). Quota28,07h/private Datasetv1ready
đã kiểm trước push. Source/QA push50a6092; một kernel tensor version1 COMPLETE.
59raw/2remote files, hai audits byte-identical, candidate_valid=true.4parity đạt;
long agent native OOM/candidate120MiB, guard native1920,172MiB/candidate52MiB
peakallocated; hai boundary decode đạt.14attention calls/0models. Đo được
math/efficient dispatch trong tensor run, không retrospectively quy kết OOM cũ.
[Báo cáo](../docs/evaluation/phase5_sdpa_tensor_gpu_v1_report.md).
Chưa đổi model attention. Tiếp [integration design](../docs/architecture/phase5_efficient_stress_v1_design.md):
mới thiết kế, cần versioned code/tests/auditor/fullQA/exactpreflight trước modelGPU.
Không tự giảm input,
đổi model, lượng tử hóa, nới caps/deadlines hay submit lại. Không job Kaggle/local
còn chạy. Giữ nguyên v1/v2 source, outputs và pre-submit QA. Quota28,17h chỉ là
trước v2; kiểm lại nếu có GPU mới. Không localweights/Test/privateGT.

Đã COMPLETE [native policy compatibility CPU](policy_native_compat_v1.md),
`huylmhuhu/react-vn-policy-native-compat-v1` version1, một submission.
Source `5c0c20e`; pre-submit source/QA đã push `c3bf60f`.
Native Transformers5.5.0/Torch2.10.0+cu128 CPU4cases đạt; không model.generate,
weights/GPU.68rawfiles xác thực, hai audits01/02 byte-identical.
[Báo cáo](../docs/evaluation/phase5_policy_native_cpu_v1_report.md).
Remote `build/kaggle/policy_native_cpu_v1_remote_source01`, raw
`results/phase5_policy_native_cpu_v1_raw01`, giữ nguyên. CPU machine_shape
serialize `"None"` đã thêm9tests,34focused đạt; không sửa submitted worker.
Full releaseQA:1.743pass/1optional skip375,60s; setup/Ruff/mypy260/knowledge đạt,
`results/phase5_policy_native_cpu_v1_release01_pytest.xml`.
PreQA1.734pass/1skip370,38s; lượtpre01 ngắt/noJUnit không tính pass.
Không Kaggle hoặc local QA job còn chạy; không local weights hoặc Test access.

Đã chốt CPU milestone [generation policy observation v1](generation_policy_v1.md):
38tests mới đạt; actual-stage hooks được fake differential/mutation kiểm chứng,
hai pinned-wheel source checks byte-identical. Full suite1.709pass/1optional native
skip trong399,13s, XML `results/phase5_generation_policy_v1_release01_pytest.xml`.
Setup/Ruff/mypy257/knowledge đạt. Không job local hoặc Kaggle mới còn chạy.
Không native model/GPU mới hoặc Test access. Nguồn cũ nguyên vẹn.

Đã chốt CPU QA [context stress artifact auditor](context_stress_audit_v1.md):
77 tests mới đạt; static native-wheel check hai lần byte-identical, không native
imports/load/inference. Full QA1.671pass/1optional native skip trong358,82s;
setup/Ruff/mypy253/knowledge đạt. XML
`results/phase5_context_stress_audit_v1_release01_pytest.xml`.
Không job local/context GPU đang chạy; chưa context GPU submission.
Phát hiện trước GPU: TF5.5.0 resolve None từ publisher config; prepared.json là
submitted config, không phải resolved policy. Cần versioned policy evidence
và matching auditor trước wrapper/preflight/submission. Không sửa frozen code.

Mốc trước: [context stress backend/runner CPU](context_stress_v1.md): 42 tests mới
đạt, source `d07e914` có hai CLI stub reproductions cùng summary/4PID reaped.
Full QA01 lỗi test isolation (30lateUNREGISTER từ object cũ trong IPC test),
giữ nguyên XML/trace. Teardown nhóm test mới đã sửa; probe+IPC46/46 đạt;
full QA02 hoàn tất: 1.594 pass/1 optional native skip trong344,79s, XML
`results/phase5_context_stress_v1_release02_pytest.xml`. Setup/Ruff/mypy250/
knowledge đạt. Chưa GPU wrapper/preflight/submission. Auditor mới kiểm receipt
consistency, không tự xác thực source hoặc effective policy. Không sửa nguồn cũ.

Phase5 còn mở. IPC diagnostic pair-ipc-v1 đã COMPLETE, một lần submit.
Audits03/04 tái lập selected audit byte-identical,99rawfiles. Nguồn semaphore
observed thuộc tqdm.std.create_mp_lock trong3busy workers;90parent+3idle locks
cóUNREGISTER. Cả6exits vẫn forced (5TERM/1KILL),0graceful.18VRAM samples về nền;
không chứng minh driver/IPC leak-free. [Đính chính](../docs/evaluation/phase5_pair_ipc_gpu_v1_review_addendum.md).

Đang triển khai [pair progress GPU v1](pair_progress_v1.md): entry/wrapper/builder
và auditor riêng đã có. Source `a1a90b3`: 21 test mới đạt, exact preflight cả hai
archive/expanded/PAX layouts đạt, 6 native-policy workers/layout và owner 90/90.
Full pre-submit QA đạt: 1.517 pass/1 optional native skip trong 358,49s;
setup/Ruff/mypy 247 files/knowledge đạt. Source/QA đã push `f8ab56d`; một kernel
`huylmhuhu/react-vn-pair-progress-v1` version 1 COMPLETE, một submission.
Hai audits01/02 byte-identical, 106 raw hashes verified; prevention gate đạt:
0 child registrations, owner 90/90, 0 unmatched/semaphore warning; 18 VRAM
samples residual 0 bytes hai GPU. 6 loads/0 generation, 5 TERM/1 KILL/0 graceful.
[Báo cáo](../docs/evaluation/phase5_pair_progress_gpu_v1_report.md).
Đã chốt bản sửa opt-in thread-only progress lock và hai native CPU reproductions:
[contract](../docs/architecture/phase5_worker_progress_v1_contract.md),
[tri thức](worker_progress_v1.md). Default/disabled/threadTERM/threadKILL controls
có1/1/0/0registrations; TQDM_DISABLE không phải fix. Chưa sửa frozen runtime.
Full QA hoàn tất: 1.496 đạt, 1 optional native pytest bỏ qua; XML
`results/phase5_worker_progress_v1_release01_pytest.xml`. Hai standalone native
runs thực sự đã chạy với pinned tqdm, 8 workers/PID khác nhau đều reaped.
Không job Kaggle hoặc local test còn chạy; không local weights/Test payload.
Full QA mới:
`results/phase5_pair_progress_v1_pre_submit01_pytest.xml` đã hoàn tất.

Trong lúc GPU chạy, [context geometry CPU](context_geometry_v1.md) đã có module
và 35 test đạt; full suite mới 1.552 đạt/1 optional native skip trong 343,38s, XML
`results/phase5_context_geometry_v1_release01_pytest.xml`. Chưa native stress
backend/inference hoặc sửa source đã gửi lên Kaggle. Setup/Ruff/mypy 248 files/
knowledge đạt; không local test job còn chạy sau mốc này.

Có báo cáo tiến độ MD/PDF/figures từ ngoài phiên này;
giữ nguyên, không stage/commit cùng task. Incoming handoff đã giữ nguyên tại
[bản lưu](handoff_20260909_ipc_draft.md); các khẳng định quá rộng được đính chính.

## Bước tiếp theo

Ưu tiên hiện tại: [ordinary requests](efficient_requests_v1.md) đã có adapter và
independent native-metric join CPU. Tiếp real-spawn factory/Ready/progress
composition trước native repeated-request proof; rồi task-local ownership, cold/warm metrics,
A0–A6 parity/Broker/final/lifecycle. Cần code mới/tests/differential/exact package
trước GPU tiếp; không suy stress pass thành benchmark adoption hoặc guard quality.

1. [Context-stress design](../docs/architecture/phase5_context_stress_v1_design.md):
   geometry/native backend/runner và independent23file auditor đã có. Static
   native interface checks đạt nhưng phát hiện publisher-default inheritance.
   Versioned policy receipt/outer audit và native library rehearsal đã có.
   GPU v1 lỗi thứ tự factory; v2 đã sửa READY nhưng agent OOM trong stress.
   Owner đã đồng ý bounded deviation và SDPA tensor v1 đã native pass.
   Versioned efficient-stress integration đã native pass: giữ ReadyFactory
   ngoài, scoped HF repeat/forced efficient/restoration và full boundary audited.
   Không retry v1/v2, tensor hoặc efficient identity.
   Exact4096input,512/128output;
   không suy output count thành full KV cache hoặc thay benchmark decoding.
2. Versioned runtime integration, A4 processing-scope anchors, private-record
   final entitlements, grouped Dev guard/model decision/differential/freeze.
   Không tune từ four-call diagnostic, không Phase6/7/Test access.

Pending access: chưa cần tài khoản/model access mới; owner đã chấp thuận bounded
attention deviation. Kiểm lại quota/private Dataset trước submission mới.
Kaggle huylmhuhu/kaggle1, systemCLI2.2.4; Dataset11942593private/v1, quota28,27h
chỉ là pre-submitCPU2026-09-10, kiểm lại trước runGPU mới. Không cycling account.
Llama/Meta pilot chưa chạy; không gán điểm0.

## Bằng chứng

- [Efficient model stress audit](../experiments/manifests/phase5_efficient_stress_gpu_v1_audit01.json):
  source5267218/pre-pusha66514e, version1 COMPLETE;90raw/2remote,hai audits SHA
  f60467ea45e5e46b523cf365a98cfb3e56e266b27963b7b7a01acef7541b9d5f.
  FullQA1.931pass1optional skip389,21s; postdownload72focused5,09s/setup/Ruff/
  mypy282.42file exactpreflight hai layouts;0localmodels/0Testpayloads.
  [Release QA](../experiments/manifests/phase5_efficient_stress_gpu_v1_release_qa01.json)
  binds selected audit/report/QA; all pre-submit source/evidence hashes reverified.
- [SDPA tensor GPU audit](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_audit01.json):
  source5aabea0/pre-push50a6092, one version1 COMPLETE;59raw/2remote files,
  10freshPID/14attention/0models; candidate true/4parity pass, không Phase5accepted.
  Hai audits SHA278c3f0759e71c5d6291e03303ed859487ecebcc5fb8deb77b17e6894494e772.
  PreQA1.859pass1skip, exact28file archive/expandedPAX đạt. Timings có profiler,
  không speedup claim; không sửa frozen context/tensor code hoặc outputs.
  [Release QA](../experiments/manifests/phase5_sdpa_tensor_gpu_v1_release_qa01.json):
  sau download rerun34focused/setup/Ruff/mypy275/knowledge đạt, recheck9preQA
  hashes/59raw/2remote; credential78files/4knownvalues/0matches.
- [Native CPU release QA](../experiments/manifests/phase5_policy_native_cpu_v1_release_qa01.json):
  source5c0c20e/pre-pushc3bf60f, one CPU version1 COMPLETE;68raw/2remote files,
  native4cases/0model.generate/0GPU. Two audits byte-identical, full1.743pass1skip.
- [Generation policy CPU release](../experiments/manifests/phase5_generation_policy_v1_release_qa01.json):
  38new/full1.709pass1skip; hai pinned-source checks byte-identical; fake roles
  agent/guard có5policyfiles/role, repeated audit và hook/nohook summaries khớp.
  Không native execution claim; source/evidence hashes và remaining gates có trong receipt.
- [Context stress audit CPU release](../experiments/manifests/phase5_context_stress_audit_v1_release_qa01.json):
  77new tests/full1.671pass1skip; hai static wheel receipts byte-identical.
  146frozenentries/296oldGPUraw/17overlay/4contextsource unchanged.
  [Publisher-default finding](../experiments/manifests/phase5_context_stress_generation_defaults_finding01.json)
  là source-level evidence; submitted config chưa chứng minh resolved policy.
- [Context stress CPU](../experiments/manifests/phase5_context_stress_v1_validation01.json)
  và [release QA](../experiments/manifests/phase5_context_stress_v1_release_qa01.json):
  runtime source `d07e914`, 42 test mới, full1.594pass/1skip; hai runs/4PID reaped,
  15rawfiles/run. Test-only isolation fix không đổi runtime hoặc raw receipts.
- [Pair-progress audit](../experiments/manifests/phase5_pair_progress_gpu_v1_audit01.json)
  và [release QA](../experiments/manifests/phase5_pair_progress_gpu_v1_release_qa01.json):
  source `a1a90b3`, pre-push `f8ab56d`, 106 raw files, hai audits byte-identical.
  Full QA 1.552 pass/1skip, setup/Ruff/mypy248/knowledge đạt; credential-value scan
  118 files/bốn values/0matches. Context geometry CPU commit `0d6d141`.
- [IPC selected audit](../experiments/manifests/phase5_pair_ipc_gpu_v1_audit01.json):
  source9087791, pre-pushmain31910cb; raw `results/phase5_pair_ipc_gpu_v1_raw01`,
  remote `build/kaggle/pair_ipc_gpu_v1_remote_source01`; audits01–04byte-identical.
  [Pre-submit QA](../experiments/manifests/phase5_pair_ipc_gpu_v1_pre_submit_qa01.json):
  1.481tests/359,83s,51new,setup/Ruff/mypy241files/knowledgepass.
- [Pair cancellation](pair_cancellation_v1.md), [small-context GPU](pair_gpu_v1.md):
  prior62+91raw hashes unchanged. Guard-only olderwarning2alsoimmutable.
- [Worker progress](worker_progress_v1.md): source `e8f72de`, 15 unit mới đạt;
  full suite 1.496 đạt/1 skip trong 354,52s, setup/Ruff/mypy 243 files/knowledge đạt.
  [Selected receipt](../experiments/manifests/phase5_worker_progress_v1_validation01.json)
  và [release QA](../experiments/manifests/phase5_worker_progress_v1_release_qa01.json)
  bind hai native runs bằng system Python 3.11.0/tqdm 4.67.3; mỗi lượt 7 raw files,
  registrations 1/1/0/0, warning 2 positive controls. Không dùng prototype dev01
  làm selected release. Frozen sources/overlays/raw GPU và seals hash-only đạt.
- [Gate còn lại](phase5_progress.md), [README](README.md) dẫn tới các mốc CPU/GPU
  và các phase đã accepted. Không merge nhánh bạn:
  [review](phase5_integration_review_20260909.md).

## Giới hạn

Worker reap, graceful exit, VRAM recovery và IPC cleanup là các kết luận khác nhau.
IPC trace không quan sát cachedaliases/Cregistrations/trackerOSunlink; timings
instrumented không gộp với lượt trước. Thread-only lock đạt bounded HF/GPU
creation-path prevention, không phải graceful/native generation shutdown proof.

Không privateGT/Testpayload/credentials/hiddenreasoning trong memory; memory không
đi vào prompts. Test seals chỉ hash-check, không model Test. Phase1–4 đã accepted
theo scope/owner self-review waiver; Phase5 chưa accepted. Không lấy số tests pass
làm phần trăm hoàn thiện hoặc bằng chứng chất lượng/security LLM.
