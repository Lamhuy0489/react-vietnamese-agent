# Ghi chú Kaggle Phase 1

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
