# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **offline guard HF adapter v1 đã tái lập từ source sạch `bc2023f`**.
[Selected receipt](../experiments/manifests/phase5_guard_hf_v1_validation01.json)
khớp source/input/prior-evidence preflight01; chưa Phase 5 acceptance.
[Contract](../docs/architecture/phase5_guard_hf_contract.md),
[nguồn ứng viên](guard_model_preflight_evidence.md), [tiến độ](phase5_progress.md).
Không sửa runtime v5/policies/prompt hoặc source/test/contract đã khóa trước.

GuardSnapshot pin HF revision + SHA-256/size toàn bộ snapshot; local-only native
Qwen2/safetensors, FP16, single GPU, process allocator ceiling và context cap.
Factory picklable dùng với interface WarmGuardBackend; cần snapshot thật
và metrics path mới mỗi task. Fresh messages/config/dynamic cache, greedy128/seed42,
lỗi retire; không prompt/response/exception text trong adapter metrics.

## Bước tiếp theo

1. Kiểm Git/hashes và receipt guard HF. Script `scripts/verify_phase5_guard_hf.py`;
   không sửa adapter/test/contract/research note đã selected; version riêng nếu đổi.
2. **GPU prerequisites**: acquisition độc lập từ official HF revision
   `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, materialize rồi hash snapshot.
   `describe_snapshot` không tự xác thực publisher; cần acquisition receipt riêng.
   Chưa xác minh Kaggle variation/version tương đương. Đọc Kaggle skill + project
   preflight trước bundle/upload; exact archive/expanded mount tests phải pass.
3. Chuẩn bị runner synthetic cache-bypassed A→B→A vs fresh-A; không dùng cache-hit
   ModelGuard làm chứng cứ statelessness. Giữ invalid/mismatch, không retry ngữ nghĩa.
   Kiểm tensor thật, task-local load/deadline/cancel/reap và metrics dưới GPU.
4. Version riêng agent placement để đo concurrent residency/context stress.
   Guard default 5 GiB allocator + 1 GiB free headroom không phải combined fit.
   MeasuredHFBackend cũ balanced 13 GiB/device không tái dùng nguyên cho coexistence.
5. Rà A4 processing scope, grouped Dev tune/validation và broader final entitlements.
   Không Phase 6/Test. Không cần tài khoản mới cho local work; Kaggle account/quota
   chưa kiểm trong mốc này. Đã tìm được `python3 -m kaggle` phiên bản 2.2.4;
   `--version` và `quota --help` pass. `.venv/bin/kaggle` không có, không cần cài
   lại chỉ vì thiếu entrypoint trong venv. Chưa kiểm auth/quota qua mạng hoặc đổi
   credentials; không tự đổi tài khoản để vượt quota.

## Bằng chứng

- Adapter preflight01: **942 tests pass** (51 mới), 228,00 giây; setup/Ruff/mypy
  197 source files/knowledge pass. 134 source hashes, 1.176 prior source entries
  nguyên vẹn. Chưa GPU/LLM. 370 raw hashes của warm v5 cũng đã kiểm lại riêng.
- Selected validation01: source sạch `bc2023f`, 942 tests pass trong 228,14 giây;
  setup/Ruff/mypy 197 files/knowledge pass, source/input/prior evidence khớp
  preflight01. 134 source/sáu raw log hashes kiểm lại. Không GPU/LLM/Dev/Test run.
- Warm v5 source `2300751`, evidence commit `598ea7e`:
  [receipt](../experiments/manifests/phase5_warm_guard_v1_validation01.json).
  891 tests; 22 cold/warm pairs = 44 Replay, chín lifecycle conditions; 140 mock
  Broker calls, 240 fake guard classifications. 138 source/370 raw hashes,
  1.038 prior entries. Worker starts 53→18 chỉ là synthetic process counts.
- V4 source `04ae4c8`, [receipt](../experiments/manifests/phase5_a6_runtime_v1_validation01.json):
  845 tests, 50 Replay. Value-gate source `a3743a2`, origin source `3b9f565`;
  tất cả selected source và Test seals phải giữ nguyên.

## Giới hạn

Chưa tải model hoặc GPU/Kaggle run, không benchmark Dev tuning/Test parsing.
CPU fakes không chứng minh internals Transformers stateless hoặc CUDA compatible.
Allocator cap là process-wide, không gồm mọi CUDA overhead hoặc process agent;
global free-memory endpoints không phải global peak. Snapshot chỉ kiểm trước/sau
load, mount phải immutable. Model choice vẫn là technical candidate, không guard
đã freeze để so A2–A6. Guard model semantic/structured-output quality chưa đo.
Warm guard không bảo đảm host hard-kill/orphan recovery. A6 bounded origin/S0
final policy vẫn còn giới hạn entitlements, short names/aliases/encoded/paraphrase.
Assistant self-review theo owner waiver, không independent review. Không đưa
credentials/GT/Test payload/CoT vào knowledge hoặc development memory vào prompt.
