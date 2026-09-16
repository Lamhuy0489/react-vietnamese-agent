# Bàn giao phiên làm việc

Cập nhật: 2026-09-16. Phase 5 chưa nghiệm thu: 4/7 ≈ 57% nhóm acceptance.

## Đang làm

**Constrained exact package development và QA đã đạt; đang khóa source/release.**
[Report](../docs/evaluation/phase5_constrained_package_v1_report.md),
[receipt](../experiments/manifests/phase5_constrained_probe_package_dev01.json).
Builder `scripts/prepare_phase5_constrained_probe_package_v1.py`, template
`notebooks/kaggle/constrained_probe_kernel_v1.py`. Development package ở
`build/kaggle/phase5_constrained_probe_package_dev01`: 166 worker files,
172 source pins; mỗi layout 8 tools, 21 Dummy, 10 fresh constrained tasks và
6 retained checkpoints. 15 tests mới đạt; final QA 495 focused + 105 integration,
setup/Ruff/mypy444/knowledge/diff đạt; 142/86/175 frozen pins nguyên.
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

1. QA đạt: gom code/tests/skill/evidence/memory trong một source-freeze commit.
2. Rebuild builder **không `--development`**, output mới
   `build/kaggle/phase5_constrained_probe_package01`; chạy lại exact hai layout.
   Development receipt không đại diện committed release, không đưa lên GPU.
3. Nối/kiểm remote source/version/output authentication; kiểm quota/account,
   private Dataset/model mounts trước submission mới. Giữ prompt/model/parser/
   fallback/shutdown 2s để chỉ đo thay đổi decoding. Chưa submit notebook mới;
   requested alias `huylmhuhu/react-vn-constrained-guard-v1` chưa phải actual resource.
4. Tiếp tục guard quality/benign utility/lifecycle và mapping 20 DoD trước freeze.

## Bằng chứng

- Development package: 433 raw files/layout, 1.043 file scan không credential match.
  Source base `f5e97ae` + exact working-tree hashes, native submission disabled.
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

Exact package/remote release authentication, production guard/CUDA/quality, benign utility,
graceful shutdown và formal freeze vẫn mở. Không full pytest vì Test-assigned
authoring fixtures; không Test/private GT access. Không cần tài khoản mới;
kiểm quota/private mounts lại khi GPU package thực sự sẵn sàng.

GitHub `Lamhuy0489` khác Kaggle `huylmhuhu`; quyền GitHub không cấp quyền Kaggle.
Giữ notebook/Dataset private, credentials ngoài Git. Không đưa memory vào prompt.
Giữ nguyên chỉnh sửa riêng tại plan/phase6–9, docs/BAO_CAO_TIEN_DO_DO_AN.*,
docs/figures/. [Lịch sử bàn giao](history_20260916_constrained_cpu.md) không phải
chỉ dẫn submit hiện hành.
