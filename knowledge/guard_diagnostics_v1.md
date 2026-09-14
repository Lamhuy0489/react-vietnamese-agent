# Guard diagnostics v1 — hiện hành

2026-09-14. Bước nối tiếp [document diagnostic](document_diagnostic_v1.md).
Native v1 đã kết thúc và giữ nguyên; không retry semantic hoặc mở Test.

## Đã đạt CPU

Source `284590d`; [CPU01 receipt](../experiments/manifests/phase5_guard_diagnostics_v1_cpu01.json)
SHA-256 `3cf5a5e1ed2dfcf9cfa1848bbccafba4afa89b02f66b53003d2f4632628c2907`.
Full **2.871 pass/1 optional skip**, 714,93s; setup/Ruff/mypy362/knowledge đạt.
510 source/424 raw hashes khớp, 169 data unchanged. 40 runtime receipts và 25
diagnostic sidecars đã kiểm. Output `results/phase5_guard_diagnostics_v1_cpu01`
đã xong, không chạy trùng. [Dev schedule](../experiments/manifests/phase5_grouped_dev_plan_v1.json)
đã chốt metadata, dispatch-disabled.

## Đã triển khai

- `guard_diagnostics_v1`: phân loại JSON/schema lỗi bằng danh mục cho phép,
  không ghi text, giá trị, unknown field names hay exception context.
- `DiagnosticFactory`: wrapper opt-in, sidecar fsync/PID/request/config/hash,
  giữ nguyên response và lỗi transport; lỗi ghi sidecar fail closed đã định trước.
- CPU actual-spawn A2–A6: safe + invalid JSON + invalid schema + duplicate key,
  mỗi case có baseline và observed pair. Tái hiện retire đóng cả pair, POST và
  agent sau đó lỗi mà không có generation mới; không giả làm fallback thành công.
- Metadata-only Dev planner chọn một family ở mỗi 8 nhóm bằng hash seed cố định,
  lấy paraphrase và benign pair: 16cases×7levels=112 tasks dự kiến. 32 families
  còn lại tách riêng; chỉ đọc hai Dev payload có hash pin từ release đã accepted.
  Không copy task/overlay/GT vào kế hoạch, không chọn từ model outcomes.

Focused development: 50 tests đạt 50,55s trước thêm planner; planner8tests đạt
0,28s. Full QA đã chốt như phía trên, không suy thành Phase 5 acceptance.
[Contract](../docs/architecture/phase5_guard_diagnostics_v1_contract.md).

## Native composition CPU đã chốt

Source `c7fa18c`, [native contract](../docs/architecture/phase5_native_diagnostics_v1_contract.md):
factory ghép observer ngoài native policy/attention; auditor đối chiếu PID/request/
sequence và guard classification, từ chối log thiếu/thừa hoặc sai identity.
Full **2.888pass/1 optional native-tqdm skip**, 785,14s; 75focused/64,83s;
setup/Ruff/mypy365/knowledge đạt. 515source/567raw/169data hashes khớp, 51 actual
runtime receipts được audit. [Receipt](../experiments/manifests/phase5_native_diagnostics_v1_cpu01.json)
SHA-256 `1ae96fa272782a174d94687ce9c808fc3ab88830023c915a61d2969662b2f994`.
Output `results/phase5_native_diagnostics_v1_cpu01` đã đóng, không chạy lại.
45 observed-sidecar records có cả negative mutations, không phải 45 native
classifications thành công. [Báo cáo](../docs/evaluation/phase5_guard_diagnostics_v1_report.md).

## Bước tiếp theo

CPU diagnostics/native composition và Dev schedule đã xong; không còn QA chạy.
Bước kế worker input/catalog và scope phù hợp public fixtures: cả 16 selected
trigger đều unassessed theo v3 (static check), không xem đó là model failure.
Giữ `dispatch_allowed=false` đến khi worker input/catalog/manifest, runtime
diagnostic integration, exact package và QA được chốt. Không nới schema/prompt/
deadline hay đổi guard model để làm đẹp lỗi native document. Cần native diagnostic
cho các Dev inputs mới và đánh giá guard quality, không đoán lỗi JSON lịch sử.

Pending access: không cần tài khoản mới; model nặng chỉ Kaggle. Không có GPU job.
Phase 5 chưa accepted; grouped Dev, broader scope (`cho biết`) và freeze còn mở.
