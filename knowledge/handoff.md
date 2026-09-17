# Bàn giao phiên làm việc

Cập nhật: 2026-09-17. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

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
2. Controlled lifecycle follow-up: 4 CALC workers nhận STOP/serve-return trong
   53–61ms nhưng vẫn TERMINATE sau deadline2s. Thiết kế CPU post-serve delay /
   teardown controls và protocol riêng trước GPU; chưa đổi deadline hay model.
3. Giữ syntax success8/8 tách khỏi guard semantic quality/benign utility;
   lập representative Dev follow-up rồi mapping20DoD trước formal freeze.
4. Tiếp tục quy tắc gom commit sau phần việc hoàn chỉnh/QA đạt;
   không status-only commit hoặc amend worker source `0d4e82f`.

## Bằng chứng

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

Bounded constrained native syntax/release đã đạt; representative guard quality, benign utility,
graceful shutdown và formal freeze vẫn mở. Không full pytest vì Test-assigned
authoring fixtures; không Test/private GT access. Không cần tài khoản mới;
kiểm quota/private mounts lại khi GPU package thực sự sẵn sàng.

GitHub `Lamhuy0489` khác Kaggle `huylmhuhu`; quyền GitHub không cấp quyền Kaggle.
Giữ notebook/Dataset private, credentials ngoài Git. Không đưa memory vào prompt.
Giữ nguyên chỉnh sửa riêng tại plan/phase6–9, docs/BAO_CAO_TIEN_DO_DO_AN.*,
docs/figures/. [Lịch sử bàn giao](history_20260916_constrained_cpu.md) không phải
chỉ dẫn submit hiện hành.
