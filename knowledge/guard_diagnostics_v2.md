# Structural guard diagnostics v2

Cập nhật: 2026-09-15.

Đã có component CPU opt-in theo [contract](../docs/architecture/phase5_guard_diagnostics_v2_contract.md).
Giữ nguyên parser/diagnostic v1; thêm framing(enum), syntax error(enum), offset
và boolean end-of-input/trailing-comma/fence. Không lưu text/exception/schema
values; không strip Markdown hoặc sửa JSON để biến lỗi thành thành công.

71 focused synthetic tests đạt; setup/Ruff/mypy396 đạt. Không sửa175 frozen
worker pins, không inference/Test, không chấm lại112ca cũ bằng dữ liệu bịa.
[QA receipt](../experiments/manifests/phase5_guard_structural_v2_cpu01.json).

**Chưa làm:** observer sidecar v2, join audit request/PID/sequence và native
package. Bước tiếp là observer/join CPU có mutation tests, rồi mới xét synthetic
GPU diagnostic riêng. Không tự bật module mới vào worker hiện hành.
Không kết luận30lỗi trước là Markdown hay truncation vì không có raw guard text.
