# Native shutdown wiring v2

2026-09-14. Tiếp sau [pair/runtime v3 CPU](pair_runtime_v3.md).
[Contract](../docs/architecture/phase5_native_shutdown_wiring_v2_contract.md).

Đã triển khai composition native riêng trả `ShutdownPair` trực tiếp; giữ nguyên
stack progress/policy/attention và native HF factories. Agent-only dùng stack
cũ tương đương nhưng execution config mới, có start/call deadline riêng.
Runner `security_runtime_probe_v2` gọi runtime v3; checkpoint bind protocol,
config và public inputs, không resume từ v1 hoặc chạy lại partial/terminal.
Auditor native v2 tách `observed_graceful` khỏi `recovered`; failed/partial native
calls vẫn unverified. Không khẳng định xác thực remote từ hash local.

36 focused tests đã đạt (23,98s); full QA còn chờ chốt. Dự kiến dùng
`scripts/verify_phase5_native_shutdown_wiring.py` với output mới
`results/phase5_native_shutdown_wiring_v2_cpu01`; không chạy trùng khi đã tồn tại.
Factory tests không tải model; seven-level tests dùng synthetic subprocess.
Native-shaped sidecar tests mock checkpoint rõ ràng, không phải GPU evidence.

CLI mới: `scripts/run_phase5_shutdown_runtime_probe.py` và
`scripts/audit_phase5_shutdown_runtime_probe.py`. Chưa có wrapper/bundle v2 được
nghiệm thu. Calculator chỉ dùng làm CPU control ở mốc này; native diagnostic
tiếp theo cần mục tiêu tool/guard-path định trước, không retry kết quả v1.

Còn: exact archive/expanded package + release auditor/source authentication,
native lifecycle/guard-path diagnostic trên Kaggle, grouped Dev quality, broader
semantic coverage và freeze. [Sổ Kaggle](kaggle_resources.md) chưa có lượt mới.
