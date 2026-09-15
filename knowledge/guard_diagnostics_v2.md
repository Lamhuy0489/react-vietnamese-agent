# Structural guard diagnostics v2

Cập nhật: 2026-09-15.

Đã có component CPU opt-in theo [contract](../docs/architecture/phase5_guard_diagnostics_v2_contract.md).
Giữ nguyên parser/diagnostic v1; thêm framing(enum), syntax error(enum), offset
và boolean end-of-input/trailing-comma/fence. Không lưu text/exception/schema
values; không strip Markdown hoặc sửa JSON để biến lỗi thành thành công.

71 focused synthetic tests đạt; setup/Ruff/mypy396 đạt. Không sửa175 frozen
worker pins, không inference/Test, không chấm lại112ca cũ bằng dữ liệu bịa.
[QA receipt](../experiments/manifests/phase5_guard_structural_v2_cpu01.json).

## Observer và join v2 — bước tiếp theo đã triển khai

Đã bổ sung worker sidecar v2 và host witness độc lập: host tự hash response nhận
qua transport, không lấy hash từ sidecar. Auditor đối chiếu PID/request/generation/
sequence/response hash/length, rồi ghép với PRE/POST runtime trace. Có kiểm shape
strict, khóa trùng, bản ghi thiếu/thừa, dữ liệu bị sửa, lỗi sink và retirement.
[Contract](../docs/architecture/phase5_guard_observer_v2_contract.md),
[QA receipt](../experiments/manifests/phase5_guard_observer_v2_cpu01.json).

139 focused synthetic tests đạt; setup/Ruff/mypy399 đạt. A2–A6 dùng worker CPU
spawn thật nhưng backend scripted, không tải model. Lỗi JSON vẫn là INVALID_OUTPUT,
POST sau retirement vẫn BACKEND_FAILURE; không repair hoặc semantic retry.
Lỗi ghi host witness đóng/reap pair, audit không nhận như lượt có bằng chứng đủ.
Raw logs và process artifacts giữ tại `results/phase5_guard_observer_v2_cpu01`;
receipt khóa inventory/hash/source. Không sửa175worker pins hay112ca baseline.

Giới hạn: shape hợp lệ không chứng minh đúng từng syntax hint nếu không có raw
response; không xác thực weights hoặc chống đồng thời sửa tất cả artifacts.
Host witness là mới, không suy ra được cho những lần native trước đây.

## Native-shaped observer probe — CPU milestone

Đã khóa protocol riêng trong [contract](../docs/architecture/phase5_observer_native_v2_contract.md)
và thêm `run_phase5_guard_observer_v2.py`/auditor. Bốn task công khai tổng hợp
(CALC/DOC × A2/A6), mỗi task một pair mới, chạy hai điều kiện:

- `valid`: 4/4 completed, 8 guard responses, đủ PRE/POST, lifecycle/recovery đạt.
- `trailing_comma`: 0/4 completed, 4 model_error, 4 PRE response rồi POST
  BACKEND_FAILURE do retirement; không repair/retry.

Đây là backend scripted CPU, không tải model. Hai raw probe và manifest audit
được lưu tại `results/phase5_guard_observer_probe_v2_*` và
`experiments/manifests/phase5_guard_observer_probe_v2_cpu01.json`; auditor
re-audit checkpoint/hash, source commit, coverage và worker reaping.
26 kiểm thử native/probe bổ sung cùng 139 test observer trước đó; mypy403.

Native HF adapter v2 đã được viết nhưng chưa chạy: model mount, CUDA, Kaggle
package và remote identity vẫn là cổng riêng. Không dùng Test, không đổi175 pin
hay112 baseline; không coi scripted pass là guard quality/Phase5 acceptance.
Bước tiếp theo là exact isolated package preflight cho probe, sau đó mới cân
nhắc một GPU submission riêng nếu quota/mount được xác minh.
Không cần tài khoản mới ở mốc CPU; GPU quota/model access phải kiểm lại khi gửi.
Không kết luận30lỗi trước là Markdown hay truncation vì không có raw guard text.
