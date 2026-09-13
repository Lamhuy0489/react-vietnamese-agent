# Pair/runtime v3 — observed shutdown integration

2026-09-14. Triển khai CPU, chưa native/GPU. [Contract](../docs/architecture/phase5_pair_runtime_v3_contract.md).
ShutdownPair tạo worker v2 trực tiếp cho hai role; A0/A1 cũng dùng ShutdownBackend
với start/call budget riêng. Không sửa source/runtime v1/v2/v7 đã frozen.
Auditor mới nối lifecycle PID/grace, owner/sibling isolation, cold/warm hashes,
READY và host outcome với trace. Các mutation tests không ghi đè raw.

Source `c4afb83`: 74 focused tests đạt trong 76,90s, gồm policy/timeout negatives.
Kiểm độc lập 63 runtime receipts đều join hợp lệ; 110 lifecycle events gồm
91 GRACEFUL, 15 TERMINATE, 4 EXITED, tất cả reaped. Có thêm bốn pair teardown
fixtures riêng. Đây chỉ là synthetic CPU evidence, không tỷ lệ thành công GPU.
Full QA đã đạt **2.704 pass/1 optional-tqdm skip**, 670,56s; setup/Ruff/mypy
335 files/knowledge đạt. [Receipt](../experiments/manifests/phase5_pair_runtime_v3_cpu01.json)
đã kiểm độc lập: 468 source/646 raw hashes khớp, 169 data hashes không đổi;
1.139 parent source/raw entries nguyên vẹn. [Báo cáo](../docs/evaluation/phase5_pair_runtime_v3_report.md).
Output `results/phase5_pair_runtime_v3_cpu01` đã chốt, không ghi thêm/chạy trùng.
Không còn QA chạy; không chạy model hoặc Test mới.

Bước tiếp: native factory composition cần version mới, không dùng factory cũ
vì nó vẫn tạo ModelPair v1. Sau đó exact mount/auditor trước native diagnostic.
Không claim GPU cleanup từ CPU. [Sổ Kaggle](kaggle_resources.md).
