# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **đã acquired/hash-verified Qwen guard; đang đóng gói synthetic GPU probe**.
[Contract](../docs/architecture/phase5_guard_probe_contract.md), [tiến độ](phase5_progress.md).
Source cũ `bc2023f`/evidence `abd0203` nguyên vẹn; không sửa adapter/test/contract
đã selected. Mốc mới thêm acquisition, probe cache-bypassed, wrapper và packager.

Acquisition `build/guard_models/qwen1_5b_hf_v1_acquisition01`: 10 files,
3.098.973.447 bytes. Hash chính thức đã pin trước download; TLS verified với CA
certifi. Partial downloads giữ riêng; no automatic retry. Snapshot identity gồm
revision chính thức + local file hashes. Model ở build, không add weights vào Git.

## Bước tiếp theo

1. Full suite pass 998 tests. Commit source rồi chạy
   `scripts/prepare_phase5_guard_probe.py` với acquisition trên,
   wheelhouse `build/guard_probe_wheels_v1`, output build/kaggle mới.
   Hai exact layouts phải pass: isolated Python, eight tools/fault recovery,
   21 Dummy + completed/missing-only resume, bốn-call stub probe.
2. Push source và lưu bundle receipt; kiểm private metadata, upload Dataset
   `huylmhuhu/react-vn-guard15-probe-data-v1` với keep-tabular, không public;
   đợi READY và xác minh version. Chưa Dataset/kernel mới được submit.
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

- Acquisition script báo valid, 10 files/3.098.973.447 bytes; artifact
  `acquisition.json` và `snapshot.json` ở build path trên. Packager sẽ kiểm lại
  mọi byte từ committed source trước inference. Chưa GPU/LLM mới.
- **998 tests pass** trong 275,42 giây: 56 mới (25 acquisition, 26 bundle,
  5 process-probe); setup/Ruff/mypy 203 files gồm kernel/knowledge pass.
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
