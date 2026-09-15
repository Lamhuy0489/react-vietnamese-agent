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

**Chưa làm:** native wiring/package và thực nghiệm synthetic GPU riêng. Bước kế
là khóa protocol synthetic diagnostic (expected calls/response coverage và fail
cases), ghép observer opt-in vào native factory riêng, rồi exact isolated CPU
package preflight trước khi submit. Không tự bật vào worker/lịch Dev đã chốt.
Không cần tài khoản mới ở mốc CPU; GPU quota/model access phải kiểm lại khi gửi.
Không kết luận30lỗi trước là Markdown hay truncation vì không có raw guard text.
