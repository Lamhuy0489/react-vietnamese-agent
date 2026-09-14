# Shutdown package v2

2026-09-14. Tiếp [native wiring CPU](native_shutdown_wiring_v2.md).
[Contract](../docs/architecture/phase5_shutdown_package_v2_contract.md).

Wrapper/builder v2 giữ base bundle03 và mở rộng allowlist lên 94 files: worker/
pair v2, runtime/audit v3, native wiring/runner/auditor v2 và CLI package check.
Không thêm validation initializer, pool, Test, private GT hay credentials.
Release auditor riêng yêu cầu v2 preflight/bootstrap/remote identity; không đổi
source/receipt v1 hoặc gọi recovered là graceful.

Source `fa28401`: exact archive/expanded preflight01 đều đạt, mỗi layout 8 tools/
recovery, 21 public Dummy/missing-only resume và 7 synthetic levels; hai lượt
checkpoint audit lặp lại cùng bytes. 101 source/430 raw hashes khớp độc lập.
[Receipt preflight](../experiments/manifests/phase5_shutdown_package_v2_preflight01.json)
SHA-256 `b768d70b934e5aea4bced61a9dbfeac07303b8862c43a9bf92d91c363e184e45`.
24 focused tests đạt 7,11s; full **2.764 pass/1 optional-tqdm skip**, 693,35s.
Setup/Ruff/mypy 346 files/knowledge đạt; 485 source/137 raw hashes khớp,
169 data hashes không đổi và 5.204 prior entries nguyên vẹn.
[CPU receipt](../experiments/manifests/phase5_shutdown_package_v2_cpu01.json) SHA-256
`1802c3c635c6cf431540afd2046d779eba6dfc290d93bcb4f7c256dc506d7e7d`;
[report](../docs/evaluation/phase5_shutdown_package_v2_report.md). Không còn QA chạy.
Hai mount có 14 actual synthetic receipts, 20 fake guard attempts và 24
GRACEFUL/reaped workers; không phải native model evidence. Gói đã chốt tại
`build/kaggle/phase5_shutdown_package_v2_preflight01`, CPU QA
`results/phase5_shutdown_package_v2_cpu01`; không chạy trùng/ghi thêm output đã tồn tại.
Model tensors không materialize local; stub runtime, lazy native topology và
native audit CLI import được kiểm riêng, không coi là native inference.

Notebook ID trong metadata chỉ là **tên dự kiến** `huylmhuhu/react-vn-security-runtime-v2`,
chưa có submission hoặc remote version. `native_submission_ready=False` có chủ
đích: calculator là CPU control. Phải chốt diagnostic mới cho lifecycle/tool/
guard-path trước GPU, không retry semantic result v1. Khi có submission thật mới
thêm URL/version/receipt thực tế vào [sổ Kaggle](kaggle_resources.md).

Còn guard-path/native lifecycle, grouped Dev guard quality, broader semantic
coverage và Phase 5 freeze. Package CPU không đóng thêm production gate.
