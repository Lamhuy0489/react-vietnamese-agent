# Pair/runtime v3 — observed shutdown integration

2026-09-14. Triển khai CPU, chưa native/GPU. [Contract](../docs/architecture/phase5_pair_runtime_v3_contract.md).
ShutdownPair tạo worker v2 trực tiếp cho hai role; A0/A1 cũng dùng ShutdownBackend
với start/call budget riêng. Không sửa source/runtime v1/v2/v7 đã frozen.
Auditor mới nối lifecycle PID/grace, owner/sibling isolation, cold/warm hashes,
READY và host outcome với trace. Các mutation tests không ghi đè raw.

63 tests bước đầu đạt; đang bổ sung policy/timeout negatives và chốt full QA qua
`scripts/verify_phase5_pair_runtime_v3.py`, output dự kiến
`results/phase5_pair_runtime_v3_cpu01`. Không chạy model hoặc Test mới.

Bước tiếp: native factory composition cần version mới, không dùng factory cũ
vì nó vẫn tạo ModelPair v1. Sau đó exact mount/auditor trước native diagnostic.
Không claim GPU cleanup từ CPU. [Sổ Kaggle](kaggle_resources.md).
