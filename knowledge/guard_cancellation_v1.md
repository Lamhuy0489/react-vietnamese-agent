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
late samples, six overlay integrity. Fullsuite và exact preflight đang chờ.
Chưa real GPU submission cho cancellation. Giữ các first guard GPU diagnostics:
B SAFE, forced terminate, không guard production acceptance. Phase5 chưa accepted.
