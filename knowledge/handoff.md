# Bàn giao phiên làm việc

Cập nhật: 2026-09-08. Đây là chỉ dẫn tiếp tục, không thay thế contract.

## Đang làm

Phase 5: **Task-local warm guard + runtime v5 đã tái lập từ source `2300751`**.
[Contract](../docs/architecture/phase5_warm_guard_contract.md), [tiến độ](phase5_progress.md).
[Selected receipt](../experiments/manifests/phase5_warm_guard_v1_validation01.json)
khớp preflight01; chưa Phase 5 acceptance. Không sửa source/test/contract đã khóa.

Worker spawn/load một lần/task, JSON IPC giới hạn, full inclusive request deadline,
cold/warm timing, liveness-aware cache và close/terminate/kill/reap. Không worker/
cache xuyên task hoặc automatic retry. Invalid guard JSON cũng retire cache/worker.
Runtime v5 dùng cùng A0–A6 policies, close trên terminal và unexpected exception.
A6 contexts khác run-local source IDs: so sánh slot host đó bằng verified source
binding, không đổi nội dung source/model và vẫn giữ raw context trong artifacts.

## Bước tiếp theo

1. Kiểm tra Git/hashes và [runbook](runbook.md). Source `2300751` cùng các source
   trước đã hash; không sửa tại chỗ, mở version riêng nếu cần thay hành vi.
2. **Bước triển khai tiếp**: chốt guard model/revision từ nguồn chính thức; chuẩn bị
   real-backend statelessness/memory-fit test rồi GPU preflight. Đọc Kaggle skill/
   preflight reference trước đóng gói/upload. Warm worker chưa chứng minh backend
   không giữ conversational/KV history giữa generate calls; cần kiểm tra adapter.
   Lưu ý từ code local: `MeasuredHFBackend` cũ bắt buộc hai T4, balanced placement
   và max_memory 13 GiB/device. Không tái dùng nguyên cấu hình đó cho guard chạy
   đồng thời agent; version riêng cần explicit device/memory budgets và kiểm fit.
   Đây là giới hạn cấu hình đã đọc, không phải một lỗi OOM đã thực nghiệm.
3. Rà A4 processing scope và grouped Dev tune/validation trước tuning. General
   private final entitlement/broader origin coverage còn mở. Không Phase 6/Test.
4. Không cần tài khoản mới cho local work. Meta access thiếu cho Llama pilot riêng.

## Bằng chứng

- Preflight01: **891 tests pass**, 46 mới, 226,45 giây; setup/Ruff/mypy 194 files/
  knowledge pass. 138 source/370 raw hashes kiểm lại, 1.038 prior source entries.
- 22 cold/warm runtime pairs = 44 Replay, chín lifecycle conditions, 140 mock
  Broker calls và 240 fake runtime guard classifications. Worker starts trong
  paired runs: 53 cold → 18 warm; chỉ synthetic process-count evidence, không GPU speedup.
- Selected validation01: source sạch `2300751`, stable summary khớp preflight,
  **891 tests pass** trong 225,80 giây; 138 source/370 raw hashes và worker starts
  53/18 đã kiểm lại. Không Test payload parsing, model/GPU inference hoặc tuning.
- V4 source `04ae4c8`, [receipt](../experiments/manifests/phase5_a6_runtime_v1_validation01.json):
  845 tests, 50 Replay, 56 mock Broker calls, 121 fake guard classifications;
  135 source/435 raw hashes verified. GitHub evidence commit `d9367de`.
- Value-gate source `a3743a2`,
  [receipt](../experiments/manifests/phase5_value_gates_v1_validation02.json):
  769 tests. Origin source `3b9f565`,
  [receipt](../experiments/manifests/phase5_value_origin_v1_validation01.json):
  696 tests; tất cả selected source phải nguyên vẹn.

## Giới hạn

Chưa real guard/LLM/GPU/Kaggle, không benchmark Dev tuning hoặc Test parsing.
Synthetic cold/warm timing không phải model throughput; không bỏ cold load khỏi
chi phí. Worker reuse chỉ trong task. Close khi request đang chạy bị từ chối;
owner-thread interrupt/deadline là cơ chế cancel. Host hard-kill/orphan recovery
chưa được bảo đảm. Failed cancellation không được ghi giả là reaped.
A6 vẫn là bounded origin/S0 final policy, chưa arbitrary private entitlements,
short-name/SQL-alias/encoded/paraphrase/email-case protection. Phase 5 chưa xong.
Assistant self-review theo owner waiver; không independent review. Không ghi
credentials/private GT/Test payload/CoT vào knowledge hoặc đưa memory vào prompt.
