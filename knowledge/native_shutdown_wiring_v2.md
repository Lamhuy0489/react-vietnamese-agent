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

Đã chốt source `dfbd54f`: 36 focused tests đạt (27,70s), full **2.740 pass/1
optional-tqdm skip**, 719,76s. Setup/Ruff/mypy 342 files/knowledge đạt.
[Receipt](../experiments/manifests/phase5_native_shutdown_wiring_v2_cpu01.json)
đã kiểm độc lập: 478 source/4.726 raw hashes khớp, 169 data hashes không đổi;
1.114 entries của parent receipt nguyên vẹn. [Report](../docs/evaluation/phase5_native_shutdown_wiring_v2_report.md).
15 actual runtime receipts/26 GRACEFUL-reaped events; 70 native-shaped mocked
records được đếm riêng, không phải native runs. Output
`results/phase5_native_shutdown_wiring_v2_cpu01` đã chốt, không ghi thêm/chạy trùng.
Không còn QA chạy. Lệnh ghi bằng chứng: `scripts/verify_phase5_native_shutdown_wiring.py`.
Factory tests không tải model; seven-level tests dùng synthetic subprocess.
Native-shaped sidecar tests mock checkpoint rõ ràng, không phải GPU evidence.

CLI mới: `scripts/run_phase5_shutdown_runtime_probe.py` và
`scripts/audit_phase5_shutdown_runtime_probe.py`. Ở mốc wiring chưa có wrapper;
[shutdown package v2](shutdown_package_v2.md) nay đã đạt exact offline preflight.
Calculator chỉ dùng làm CPU control ở mốc này; native diagnostic
tiếp theo cần mục tiêu tool/guard-path định trước, không retry kết quả v1.

Còn: xác thực source/terminal remote, native lifecycle/guard-path diagnostic
trên Kaggle, grouped Dev quality, broader
semantic coverage và freeze. [Sổ Kaggle](kaggle_resources.md) chưa có lượt mới.

## Checklist gói worker kế tiếp

- Version wrapper/builder riêng từ gói v1; giữ base Dataset, source cũ và receipt
  lịch sử nguyên vẹn. Allowlist phải có các module native/request/probe/audit v2,
  model_pair v2, worker_shutdown v2, pair_runtime/audit v3, worker_shutdown_audit v2
  và hai CLI mới; kiểm import closure chứ không chỉ đếm file.
- `run_payload` phải gọi đúng CLI mới, không fallback v1, không automatic retry.
  Version bootstrap/preflight identities và joined/release auditor cùng nhau.
- Kiểm archive/expanded mount trong venv cách ly, đủ 8 tools/recovery, 21 public
  Dummy/missing-only resume, bảy synthetic runtime levels. Native-shaped sidecar
  tests không thay thế chạy auditor CLI trong package hoặc xác thực source remote.
- Hiện native metrics không có hash nội dung request độc lập: binding dựa trên
  role/PID/order/config/timing; không gọi đó là chứng minh toàn bộ payload native.
  Không đổi loader frozen để thêm claim. Partial/failure evidence không được
  nâng thành joined success; release checker phải giữ rõ các giới hạn này.
- Chốt diagnostic mới trước GPU; calculator v1 zero-tool/guard là lịch sử, không
  phải missing work. Sau submission mới thêm URL/version thực tế vào sổ Kaggle.
