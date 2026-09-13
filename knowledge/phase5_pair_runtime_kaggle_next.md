# Native Kaggle follow-up cho pair/runtime

Đây là kế hoạch thực thi tiếp theo, chưa có upload hoặc GPU run mới.
Quota đọc qua CLI 2.2.4 ngày 2026-09-13, đúng `huylmhuhu`: GPU dùng 0,14h,
còn 29,86/30h, refresh `2026-09-19T00:00:00`. Không phải reservation; private
Dataset readiness/version và quota phải được kiểm lại ngay trước submission.

## Nguồn cần đóng gói

Entry point CPU mới: `react_agent.security_v1.pair_runtime_v1.run_pair_task`.
Static import traversal tìm 51 project modules, không unresolved absolute project
imports. Đây chỉ là inventory; relative imports, templates, dữ liệu và dependency
native phải được exact preflight. Không dùng lại overlay ordinary 56 files mà
không tính closure mới vì nó chưa có runtime security v7/components v2.

Rà thêm ba entry points `pair_runtime_v1`, `pair_runtime_audit_v1` và
`ordinary_pair_probe_v1`: closure absolute project imports + package init hiện
có 74 file, không unresolved absolute imports. Không cộng cơ học 74 vào 56:
builder cần trừ đúng các file đã nằm trong base bundle và kiểm tất cả hash.

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

## Fault/timing cases cần bổ sung trước native acceptance

- CPU integration hiện kiểm load/timeout/invalid-output/cancel, chưa kiểm worker
  sibling chết đúng sau khi worker đang gọi đã trả response. `ModelPair.generate`
  có liveness check sau response: host có thể ERROR dù transport attempt là OK.
  Auditor native phải giữ cả hai sự kiện, không đồng nhất hai status này.
- Startup thất bại hiện để outer `startup_seconds=0` (chưa hoàn tất startup),
  không phải load latency bằng không. Dùng attempt elapsed làm bằng chứng failure;
  trước bảng timing native cần ghi explicit elapsed/complete cho failed startup.
- Không dùng auditor CPU như chứng nhận toàn bộ lỗi native. Cần nối thêm model
  snapshot/tokenizer, attention/request policy và GPU memory evidence trên gói mới.

[CPU evidence](phase5_pair_runtime_v1.md) · [Handoff](handoff.md).
