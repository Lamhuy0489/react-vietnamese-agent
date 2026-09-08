# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **bootstrap v2 đã sửa PAX bằng commit binding; đang kiểm chứng trước GPU**.
[Contract v2](../docs/architecture/phase5_guard_mount_v2_contract.md).
V1/Dataset/runtime giữ nguyên; v2 là wrapper riêng và kernel-only packager.
38 targeted tests pass (12 mới); full suite và exact preflight cần hoàn tất.
[Nhật ký triển khai](guard_gpu_probe_v1.md). Chưa submit GPU kernel.
[Bundle receipt](../experiments/manifests/phase5_guard_bundle_v1_preflight03.json).
[Contract](../docs/architecture/phase5_guard_probe_contract.md), [tiến độ](phase5_progress.md).
Source cũ `bc2023f`/evidence `abd0203` nguyên vẹn; không sửa adapter/test/contract
đã selected. Mốc mới thêm acquisition, probe cache-bypassed, wrapper và packager.

Acquisition `build/guard_models/qwen1_5b_hf_v1_acquisition01`: 10 files,
3.098.973.447 bytes. Hash chính thức đã pin trước download; TLS verified với CA
certifi. Partial downloads giữ riêng; no automatic retry. Snapshot identity gồm
revision chính thức + local file hashes. Model ở build, không add weights vào Git.

## Bước tiếp theo

1. Bundle đã chọn: `build/kaggle/phase5_guard_probe_v1_bundle03`.
   Hai exact layouts pass: isolated Python, eight tools/fault recovery,
   21 Dummy + completed/missing-only resume, bốn-call stub probe mỗi layout.
   72 source/input files, no authoring/pool/GT/Test/knowledge, credential scan0.
   Bundle01 không chọn do broad source scope; bundle02 failed local eager import
   `validation.__init__` kéo pool validator. Bundle03 bỏ initializer, namespace
   chỉ có environment validator. Giữ các bundle trước, chưa upload bản lỗi.
2. Dataset `huylmhuhu/react-vn-guard15-probe-data-v1` READY/version 1/private,
   id 11942593. Source/receipt đã push `1e55203` trước upload, upload đã kết thúc.
   Remote có thêm `source/pax_global_header` 52 bytes; đã tải header/manifest và
   tái hiện frozen wrapper reject. [Diagnostic receipt](../experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json).
   Bản sửa: `notebooks/kaggle/guard_probe_kernel_v2.py`, packager
   `scripts/prepare_phase5_guard_mount_v2.py`. Không đổi bundle03 hoặc bỏ qua mọi extras.
   Kiểm lại archive và actual expanded mount có global PAX, eight tools/fault,
   21 Dummy/resume/stub trong isolated venv trước GPU. Chưa submit kernel.
3. Kernel `huylmhuhu/react-vn-guard15-probe-run-v1`: hai T4, internet off.
   Guard-only A→B→A/fresh-A, 120s inclusive/request, greedy128/seed42.
   Không agent resident; chưa combined-memory proof. Kết quả invalid/mismatch
   là kết quả phải giữ, không retry ngữ nghĩa. Download vào output mới rồi audit.
4. Kaggle CLI `python3 -m kaggle` 2.2.4. Selected account `huylmhuhu` (kaggle1)
   đã auth/quota read: GPU used0,51h/remaining29,49h, refresh2026-09-12T00:00:00.
   Không token/key trong logs/memory. Không đổi tài khoản để vượt quota.
5. Sau guard probe: cancellation/GPU cleanup, versioned agent placement và
   concurrent residency/context stress. MeasuredHFBackend cũ 13GiB/device không
   tái dùng nguyên cho coexistence. Rồi A4 scope/grouped Dev/final entitlements.
   Không Phase 6/Test; không cần user tạo tài khoản mới lúc này.

## Bằng chứng

- Added completed-probe auditor: 13 synthetic tests pass; old full suite
  998 tests pass lại/287,71 giây. Full suite mới 1.011 tests pass/281,27 giây,
  có cảnh báo cleanup symlinks khi dùng chung temp parent. Lượt tuần tự tiếp
  theo pass sạch **1.011 tests/271,34 giây**, basetemp mới
  `build/pytest_guard_audit_v1_validation01`. Không còn test/upload đang chạy.
  Setup/Ruff/mypy 205 files gồm kernel pass; 134 frozen adapter source hashes
  và clean/adversarial prerequisites kiểm lại nguyên vẹn, Test hash-only.

- Acquisition script báo valid, 10 files/3.098.973.447 bytes; artifact
  `acquisition.json` và `snapshot.json` ở build path trên. Packager sẽ kiểm lại
  mọi byte từ committed source trước inference. Chưa GPU/LLM mới.
- **998 tests pass** trong 275,42 giây: 56 mới (25 acquisition, 26 bundle,
  5 process-probe); setup/Ruff/mypy 203 files gồm kernel/knowledge pass.
  Full suite lần kế tiếp 998 tests/276,95 giây. Bundle03 source `7649d5b`;
  exact mounts đã thực thi lại sau thay đổi allowlist cuối, không GPU claim.
  Giữ các lỗi local QA đã sửa,
  không claim chúng là Kaggle failures.
- Guard adapter source `bc2023f`, [receipt](../experiments/manifests/phase5_guard_hf_v1_validation01.json):
  942 tests, 134 source/sáu raw logs, 1.176 prior source entries verified.
- Warm v5 source `2300751`, [receipt](../experiments/manifests/phase5_warm_guard_v1_validation01.json):
  891 tests; 22 cold/warm pairs = 44 Replay, 140 Broker calls, 240 fake guard
  classifications. 370 raw artifact hashes đã kiểm lại ở mốc trước.

## Giới hạn

Chưa real guard/GPU inference, không benchmark Dev tuning/Test payload parsing.
Probe stub-valid chỉ transport QA, không accuracy/ASR. Exact equality A có giới
hạn bốn calls, không chứng minh mọi HF state/history. Allocator cap process-wide,
free-memory endpoints không phải global peak; guard-only không combined fit.
HF candidate chưa chốt làm production guard. A6 vẫn bounded origin/S0 final,
không general private entitlements/aliases/paraphrase/encoding proof. Assistant
self-review theo owner waiver, không independent review. Không credentials/GT/
Test payload/CoT hoặc development memory trong model prompts.
