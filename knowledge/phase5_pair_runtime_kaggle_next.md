# Native Kaggle follow-up cho pair/runtime

Đây là kế hoạch thực thi tiếp theo, chưa có upload hoặc GPU run mới.
Quota đọc qua CLI 2.2.4 ngày 2026-09-13, đúng `huylmhuhu`: GPU dùng 0,14h,
còn 29,86/30h, refresh `2026-09-19T00:00:00`. Không phải reservation; private
Dataset readiness/version và quota phải được kiểm lại ngay trước submission.

## Nguồn cần đóng gói

Entry point đã kiểm CPU: `react_agent.security_v1.pair_runtime_v2.run_pair_task`.
V1 CPU02 vẫn giữ làm bằng chứng lịch sử, không thay file tại chỗ.
Static import traversal tìm 51 project modules, không unresolved absolute project
imports. Đây chỉ là inventory; relative imports, templates, dữ liệu và dependency
native phải được exact preflight. Không dùng lại overlay ordinary 56 files mà
không tính closure mới vì nó chưa có runtime security v7/components v2.

Rà thêm ba entry points `pair_runtime_v1`, `pair_runtime_audit_v1` và
`ordinary_pair_probe_v1`: closure absolute project imports + package init hiện
có 74 file, không unresolved absolute imports. Không cộng cơ học 74 vào 56:
builder cần trừ đúng các file đã nằm trong base bundle và kiểm tất cả hash.

Inventory read-only mới cho v2 runtime + v2 auditor + ordinary native factory +
`tools.factory`: 90 source/init files, không unresolved absolute imports; 22 file
chưa nằm trong base và ordinary overlay, không có base-file hash conflict.
Manifest của `build/kaggle/phase5_guard_probe_v1_bundle03/dataset` và các prior
pins đã xác minh bằng `check_pins()`. Wheel sẵn tại
`build/kaggle/worker_progress_v1_wheels/tqdm-4.67.3-py3-none-any.whl`.
Đây chưa phải exact mount/runtime preflight. Runner/factory/auditor native mới
sẽ thêm dependencies; tính lại allowlist sau khi code các entry points đó.

Builder trước: `scripts/prepare_phase5_ordinary_pair.py`, wrapper trước:
`notebooks/kaggle/ordinary_pair_kernel_v1.py`. Tạo builder/wrapper mới thay vì
chỉnh bytes đã được đóng receipt. Reuse private/offline dataset và pinned model
snapshot sau khi xác minh phiên bản/quota hiện hành.

## Những điểm phải kiểm trên gói mới

1. Source commit mới đã push; allowlist source/hash không mang theo Test, pool,
   private ground truth, review hay credentials. Model source catalogs là host
   metadata cho synthetic task, không lấy từ evaluator annotations.
2. Archive và expanded mount trong isolated environment; import/run đúng gói,
   cả tám tools, public Dummy tasks và missing-only resume.
3. A2–A6 dùng `ordinary_pair_probe_v1.native_pair`/factory policy đã kiểm GPU,
   truyền NEW pair vào runner; không bọc pair trong guard_factory. A0/A1 cần
   equivalent agent-only native factory với attention/policy giống backbone,
   phải có thêm identity/behavior evidence trước claim cross-level GPU parity.
4. Fresh task/pair mỗi lần; READY không phải inference. Giữ per-role cold load,
   call timings, native policy, attention, memory và actual cleanup samples.
5. Wrapper phải chạy tensor check và xác nhận 2 T4; dùng enum `NvidiaTeslaT4`
   như bài học accelerator trước. Dataset/kernel private, fresh run identity.

CPU mới chỉ chứng minh control flow và worker ownership. Model không được ép
trả câu trả lời mong muốn trong native measurement; parse/semantic failure phải
giữ nguyên. Grouped Dev quality/guard selection là bước riêng trước freeze.

## Fault/timing follow-up trước native acceptance

- CPU02 v1 kiểm load/timeout/invalid-output/cancel, chưa kiểm worker
  sibling chết đúng sau khi worker đang gọi đã trả response. `ModelPair.generate`
  có liveness check sau response: host có thể ERROR dù transport attempt là OK.
  Auditor native phải giữ cả hai sự kiện, không đồng nhất hai status này.
- Startup thất bại ở v1 để outer `startup_seconds=0` (chưa hoàn tất startup),
  không phải load latency bằng không. Dùng attempt elapsed làm bằng chứng failure;
  trước bảng timing native cần ghi explicit elapsed/complete cho failed startup.
- [V2](phase5_pair_runtime_v2.md) đã sửa hai điểm trên và qua 64 integration tests;
  full QA 2.560 pass/1 skip, source/raw/data và CPU02 v1 audit đạt. Receipt v2 đã
  lưu; dùng source snapshot v2 sau commit/push cho package, không sửa bytes v1.
- Không dùng auditor CPU như chứng nhận toàn bộ lỗi native. Cần nối thêm model
  snapshot/tokenizer, attention/request policy và GPU memory evidence trên gói mới.

[CPU evidence](phase5_pair_runtime_v1.md) · [Handoff](handoff.md).
