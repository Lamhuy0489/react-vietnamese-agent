# Ghi chú Kaggle Phase 1

## Cập nhật v1.1 — 2026-09-06

Khi tạo kernel mới, `id` và slug sinh từ `title` cần nhất quán. Lần v1.1 đầu
server cảnh báo rồi tạo handle theo title. Đó không phải inference failure:
dùng handle từ output push cho status/logs/output, không push lại để đổi tên.

Phase 2 còn gặp lỗi fault adapter không delegate `validate_arguments`, khiến
parser dùng generic BaseModel dù unit test execute trực tiếp vẫn pass. Vì vậy
preflight mới gọi tool qua AgentRuntime/parser/Broker và có recovery case.

Runner cũ chỉ ghi results cuối suite nên mất danh sách task hoàn thành khi lỗi
giữa chừng. Runner v1.1 lưu checkpoint mỗi task, từ chối identity/hash mismatch,
và không retry semantic failure. Bundle preflight kiểm tra cả archive/expanded
mount, 8 tool, Dummy đủ 21 task và resume trước upload. GPU kiểm tra bằng phép
tính tensor thực, không chỉ `cuda.is_available()`.

Skill `.agents/skills/experiment-repro/references/kaggle-preflight.md` đã lưu
quy trình; không sửa skill global để tránh áp điều kiện repo lên dự án khác.

Ba attempt đầu là lỗi hạ tầng và đều dừng trước inference:

1. Kaggle tự bung file `tar.gz` của Dataset thay vì mount nguyên archive.
2. Nội dung bung nằm trong một thư mục tên sinh tự động, không ở mount root.
3. Python subprocess không tự có `<repo>/src` trong `PYTHONPATH`.

Wrapper hiện tại xử lý cả archive và expanded mount, tìm đúng một package root,
kiểm tra SHA-256 từng file tracked, chấp nhận `Transformers` khác hoa/thường,
xác minh các file model bắt buộc, rồi truyền `PYTHONPATH` và frozen commit cho
mọi subprocess.

Quy tắc giữ nguyên:

- Chỉ một account cho authoritative run; không gộp quota nhiều account.
- Retry chỉ khi lỗi hạ tầng; không retry semantic failure để lấy điểm đẹp.
- Dataset/kernel đều private, model revision cố định, internet tắt.
- Chạy `make kaggle-bundle-validate` trước mọi lần upload.
