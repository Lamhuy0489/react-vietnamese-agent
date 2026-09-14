# Grouped Dev native v2 — package preflight

## Đính chính 2026-09-14: chưa chứng minh package độc lập

Hai receipt dưới đây được giữ nguyên để truy vết, **không dùng làm bằng chứng
isolated import hoặc exact archive/expanded execution**. Kiểm tra lại cho thấy
builder chọn thư mục đầu tiên `configs` làm root, đặt bảy file overlay vào đó.
Lệnh `python -I` vẫn dùng `.venv` có editable install; `react_agent.__file__` và
runner thực tế trỏ về `src/` của repo, không phải gói đã giải nén. Compile chỉ
kiểm cú pháp; 11 tests được dẫn không kiểm lỗi nguồn import này.

Đang thay bằng [package v3](../architecture/phase5_grouped_package_v3_contract.md):
gói đầy đủ, fresh venv, kiểm module origins, cả hai layout và toàn bộ selected
Dev stub/resume. Các câu kết luận preflight/import ở phần lịch sử sau đây bị
thu hồi về phạm vi nêu trên. Không có model/GPU run mới từ hai receipt này.

## Nội dung lịch sử (không phải kết luận hiện hành)

2026-09-14. Native runner/auditor source `3486dbf` đã ghép, nhưng bước này không tải model
và không submit Kaggle. Preflight tại `build/kaggle/phase5_grouped_native_v2_preflight01`
đạt archive/expanded overlay hash, path traversal và compile; receipt ghi
`actual_model_loads=0`, `gpu_runs=0`, `test_payload_accessed=false`,
`native_submission_ready=false`.

Sau khi sửa root detection của archive, isolated import audit đạt **11 tests
liên quan / 1,09s** và import được runner/auditor trong Python `-I`; không có
`torch`, `transformers` hoặc `tokenizers` trong module graph. [Import receipt](../../experiments/manifests/phase5_grouped_native_v2_import01.json)
ghi `model_imported=false`, `actual_model_loads=0`.

Đây chỉ là bằng chứng toàn vẹn/import cục bộ, không chứng minh import trên Kaggle,
chất lượng guard, latency, VRAM recovery, ASR/FPR hoặc utility. Bước kế là
kiểm live quota/private mounts rồi submit shard native mới với identity riêng.

[Preflight receipt](../../experiments/manifests/phase5_grouped_native_v2_preflight01.json) ·
[Native contract](../architecture/phase5_grouped_native_v2_contract.md) ·
[CPU runner evidence](phase5_grouped_runner_v1_report.md).
