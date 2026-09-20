# Bàn giao phiên làm việc

Cập nhật: 2026-09-20. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

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

1. Không còn pending notebook; **không push/resubmit constrained GPU v1**.
   Giữ raw `results/phase5_constrained_gpu_monitor02`, hai audits tại
   `results/phase5_constrained_gpu_audit01.json` và
   `results/phase5_constrained_gpu_report01/release_audit.json`.
2. Observer + CPU controls đã đóng. Nối MilestoneBackend vào native diagnostic
   runner riêng, bind milestones với PID/role/task receipts và giữ partial failures.
   Không đổi ownership/transport/signal/model outputs; không thay frozen runner.
   Rehearse archive/expanded + interpreter hash trong exact package riêng, rồi mới
   source-freeze/GPU diagnostic. Chưa tăng grace2s hoặc resubmit old diagnostic.
3. Giữ syntax success8/8 tách khỏi guard semantic quality/benign utility;
   lập representative Dev follow-up rồi mapping20DoD trước formal freeze.
4. Tiếp tục quy tắc gom commit sau phần việc hoàn chỉnh/QA đạt;
   không status-only commit hoặc amend worker source `0d4e82f`.

## Bằng chứng

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
