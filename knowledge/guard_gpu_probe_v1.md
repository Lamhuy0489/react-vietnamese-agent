# Guard GPU probe v1 — nhật ký triển khai

Cập nhật 2026-09-08. Phase 5 vẫn đang làm, không phải benchmark ASR/utility.

## Đầu vào đã khóa

- Bundle `build/kaggle/phase5_guard_probe_v1_bundle03`, source `7649d5b`.
- [Preflight receipt](../experiments/manifests/phase5_guard_bundle_v1_preflight03.json):
  hai exact layouts pass, 72 source/input files, 21 Dummy mỗi layout,
  completed/missing-only resume, tám tools/fault recovery và bốn-call stub.
- Qwen2.5-1.5B-Instruct revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`;
  mười file/3.098.973.447 bytes đã đối chiếu publisher hashes.
- GitHub đã đồng bộ `1e55203` trước upload. Không sửa gói đang truyền.

## Trạng thái bên ngoài

Đã bắt đầu `datasets create -t -r skip -q`, không `--public`, tới
`huylmhuhu/react-vn-guard15-probe-data-v1`. CLI đã exit 0 và báo private Dataset
being created. Status/metadata ngay sau create từng HTTP 403; mine-search chưa
thấy Dataset. Lần đọc sau đã READY/version 1; metadata `info.isPrivate=true`,
dataset id 11942593. Không cần tài khoản/quyền mới. Chưa submit kernel.
Quota đọc lại: 0,51 giờ dùng / 29,49 giờ còn, refresh 2026-09-12.
Không đổi account hoặc khởi tạo upload thứ hai khi lượt đầu đang chạy.

## Phát hiện trước GPU

Remote file listing có `source/pax_global_header` 52 bytes, không có trong
source inventory. Tải riêng header và manifest vào
`build/kaggle/guard_pax_diagnostic01`; CLI đặt header ở basename, không giữ
prefix `source/` trong lần tải file này. Manifest khớp local; header đúng
`52 comment=<source commit>\n` của Git archive, không phải code/payload lạ.
Python tarfile giấu global PAX record trong metadata, nhưng Kaggle bung thành
file thường. Đã thêm đúng header tải về vào source đã extract/verify cục bộ:
frozen wrapper báo `exact bundle inventory/hash mismatch`.
[Biên bản đã chọn](../experiments/manifests/phase5_guard_remote_mount_v1_diagnostic01.json).
Bundle03 giữ nguyên; mô phỏng expanded trước đó chưa tái hiện khác biệt này.
Không submit GPU để rồi chờ lỗi đã biết, không nới lỏng mọi extra file.

## Audit đã chuẩn bị

[CLI](../scripts/audit_phase5_guard_probe.py) và
[module](../src/react_agent/validation/guard_probe_audit_v1.py) chỉ đọc outputs;
không khởi chạy model. Kiểm manifest/hash, request/generation identity,
four-call coverage, CUDA tensor receipt, metrics/load, process close/reap,
snapshot/config và đối chiếu summary với từng trial. Lưu hash mọi raw artifact.
Tính tokens/s từ tokens và generation time, giữ cold/warm request times riêng.

`integrity_valid` khác `probe_valid`: bốn câu trả lời hợp lệ nhưng A khác hash
vẫn là kết quả đo không ổn định, không được retry để lấy kết quả tốt hơn.
Transport thiếu/lỗi cần biên bản lỗi riêng; không tạo receipt completed giả.
Audit này không tự xác minh remote privacy/version, Dummy score, API keys,
global peak VRAM hoặc VRAM sau reap; các kiểm tra tương ứng phải làm riêng.
Raw response text không được lưu theo protocol; response hash là dữ liệu do
producer ghi, không thể tự tính lại hash đó chỉ từ parsed JSON đã bỏ whitespace.

13 synthetic audit tests pass, không CUDA/HF. Bộ cũ 998 tests pass lại trong
287,71 giây. 134 source hashes adapter cũ và clean/adversarial prerequisites
được kiểm lại nguyên vẹn (Test hash-only). Full suite mới 1.011 tests pass trong
281,27 giây, nhưng pytest phát cảnh báo dọn temporary symlinks sau suite khi hai
phiên test dùng chung temporary parent. Không assertion failure. Sẽ kiểm lại
tuần tự với basetemp mới riêng; không sửa frozen tests hoặc tự xóa thư mục cũ.
Lượt tuần tự hoàn tất: **1.011 tests/271,34 giây, không cảnh báo cleanup**,
basetemp `build/pytest_guard_audit_v1_validation01`. Setup/Ruff/mypy 205 files gồm
kernel pass. Test count không phải Phase 5 acceptance hoặc measured guard result.

## Tiếp tục

1. Sửa packaging/bootstrap bằng identity mới để xử lý global PAX metadata;
   giữ exact inventory và byte binding. Có thể tạo archive không PAX hoặc hỗ trợ
   đúng sidecar có hash/commit đã biết; không bỏ qua arbitrary extra files.
   Giữ bundle03/Dataset v1 và không đổi runtime/model/prompt vì lỗi đóng gói.
2. Chạy lại exact archive và actual expanded layout, cả eight tools/fault,
   21 Dummy/resume và stub probe trong isolated environments. Commit/push và
   lưu receipt mới trước khi push kernel riêng tư
   `huylmhuhu/react-vn-guard15-probe-run-v1`, hai T4/internet off/timeout 1800s.
3. Lưu status/logs, tải outputs vào thư mục mới; quét khóa credentials chỉ ghi
   số match, audit probe và Dummy checkpoint identity/coverage trước báo kết quả.
4. Sau guard-only probe mới làm cancellation và agent+guard coexistence.
   Không suy bốn calls thành production guard acceptance hoặc Phase 5 complete.
