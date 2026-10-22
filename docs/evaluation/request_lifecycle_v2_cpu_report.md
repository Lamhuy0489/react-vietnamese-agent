# Request lifecycle v2 — CPU candidate

Ngày2026-09-28. Đã thêm state machine version riêng cho request-status/cancel:
[src](../../src/react_agent/serving/request_lifecycle_v2.py),
[contract](../architecture/request_lifecycle_v2_candidate.md),
[tests](../../tests/unit/test_request_lifecycle_v2.py).

Bảy CPU tests đạt cho success/dedup, cancel khi đang chạy, engine hợp tác với
stop event, fresh event cho request sau, hai loại failure, identity/conflict/
capacity/restart và lỗi ghi trạng thái trước dispatch. Pending cancel vẫn ghi
engine_active=true; chỉ đổi terminal sau callback kết thúc. Engine output bị
loại bỏ nếu cancel thắng trước terminal commit. Model exception được sanitize.
Journal không lưu prompt/modeltext/keys. Không network/GPU/model inference.

Đã nối HTTP endpoints trong candidate riêng
[request_http_v2.py](../../src/react_agent/serving/request_http_v2.py), có boot ID
ngẫu nhiên, kiểm auth trước đọc body/lookup, binding identity/hash và status/cancel
đồng thời với completion. Chưa nối HF/CUDA engine, chưa deploy lên notebook. Vì vậy
không có claim native cancellation. Worker v1 hiện hành vẫn thiếu status/cancel
và boot instance ID riêng. Các notebook đang chạy được giữ nguyên.

Giới hạn phát hiện khi kiểm tra API: endpoint/key có thể đổi trong khi metadata
session/source/model vẫn giống hệt, vì notebook chạy lại mã đã đóng gói. Host
không được dùng session_id v1 như boot identity hoặc coi health probe là bằng
chứng request cũ đã dừng. Snapshot cấu hình mới tách riêng lịch sử.

QA sau HTTP wiring:51tests đạt trong43.37s, gồm18lifecycle/HTTPtests và33tests
journal, scoring, public runtime, paired Dev/provenance regressions. Wire test
chạy loopback ngoài sandbox vì lần đầu bind bị PermissionError; không gọi Kaggle
hoặc inference. Kiểm auth trước body/lookup, malformed JSON/size, boot identity,
status hash/privacy, cancel đồng thời, cached duplicate và callback completion.
Setup/Ruff/mypy583files/knowledge-check/diff-check đều đạt. Không chạy lại full
suite; hai historical frozen-pin failures đã ghi trong handoff vẫn chưa xử lý.
[Receipt](../../experiments/manifests/request_lifecycle_v2_cpu.json) ghi nguồn QA.
Đây là host working-tree source, chưa commit/source freeze cho GPU deployment.
