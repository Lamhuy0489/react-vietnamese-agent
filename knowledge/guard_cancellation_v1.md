# Guard cancellation / VRAM recovery v1

## Đang triển khai — 2026-09-08

[Contract trước GPU](../docs/architecture/phase5_guard_cancellation_v1_contract.md).
Không đổi weights/runtime/deadline/prompt hoặc chạy lại A/B. Ba workers mới:
resident close, active-CUDA timeout, active-CUDA với SIGTERM-ignore để buộc KILL.
Model chỉ được tải, không gọi generate; fixed transport ACK không là guard answer.

Parent CUDA observer tồn tại suốt probe; baseline vì vậy khác guard-only run cũ.
Đo free/total trước/resident/sáu lần sau reap; samples1s, ba cuối trong256MiB,
ít nhất2GiB giảm khi model resident. Baseline mỗi ca so với initial, không chỉ
so với ca trước để tránh che tích lũy. Failure halt, remaining skipped, no retry.
Normal close vẫn báo graceful riêng, không gọi terminate là graceful.

New source: `src/react_agent/llm/guard_cancellation_v1.py` và
`scripts/probe_phase5_guard_cancellation.py`. Kernel template/packager riêng
inject hai files base64/hash vào source tree đã verify, từ chối overwrite.
Dataset v1/model giữ nguyên. Preflight phải chạy actual PAX/archive, eighttools,
21Dummy/completed+missingonly resume, toàn cancellationstub trong isolatedvenv.

21 targeted tests pass: five process lifecycle/error persistence, ten tolerance/
late samples, six overlay integrity. Fullsuite1.067tests/301,86s pass;
exact archive/expanded PAX preflight pass cả hai layouts từ source dab6c64.
[Selected receipt](../experiments/manifests/phase5_guard_cancellation_v1_preflight01.json)
copy byte-identical; overlay/wrapper/134 frozen source hashes đã kiểm lại.
## GPU v1 đã hoàn tất và audit — 2026-09-09

Source/receipt push lên main52004ea trước first submission; runtime7649d5b,
overlay/bootstrapdab6c64. Kernel `huylmhuhu/react-vn-guard-cancel-run-v1` v1
COMPLETE, private/offline/T4, wrapper tải ngược khớp preflight; Dataset v1 giữ nguyên.
[Báo cáo](../docs/evaluation/phase5_guard_cancellation_v1_report.md),
[audit receipt](../experiments/manifests/phase5_guard_cancellation_v1_audit01.json).

ACK gồm load43,995/30,628/30,177s; timeout120,335/120,822s. Resident3,047GiB
cả ba,18samples sau reap residual0MiB. Close thường và busy timeout dùng
TERMINATE/-15; ignore-term dùng KILL/-9. Normal close vẫn không graceful.
Chỉ chứng minh recovery trong tolerance/protocol này, không exact zero leak
cho mọi tải, không chất lượng guard hoặc combined agent/guard fit.

Read-only auditor mới có20negative/positive CPU tests; full1.087tests/257s,
setup/Ruff/mypy213files pass. Hai audit/report tái tạo byte-identical;
67raw và134frozen source hashes kiểm lại, credential scan71files/0matches.
Raw `results/phase5_guard_cancellation_v1_raw01`, audit01/02 giữ nguyên;
remote source `build/kaggle/guard_cancellation_remote_source01`.
Cadence1s là khai báo trong source, không có timestamp riêng từng sample.
Không retry; giữ first guard GPU B SAFE/forced close, Phase5 chưa accepted.
Tiếp theo: versioned agent placement/concurrent residency/context stress.
