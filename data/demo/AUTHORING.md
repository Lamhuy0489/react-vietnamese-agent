# Hướng dẫn biên soạn tài liệu thử nghiệm tấn công (Injected Documents Authoring Guide)

Tài liệu này hướng dẫn quy trình kỹ thuật và định dạng dữ liệu dành cho các thành viên nhóm nghiên cứu khi biên soạn các tài liệu chứa chỉ thị tấn công (injected documents) phục vụ mục đích kiểm thử và demo giải pháp bảo mật Agent.

---

## 1. Vị trí lưu trữ và quy ước đặt tên

- **Đường dẫn tệp:** `data/demo/injected_documents.json`
- **Mã định danh tài liệu (`doc_id`):** Sử dụng tiền tố `INJ_` kèm 3 chữ số tăng dần (ví dụ: `INJ_001`, `INJ_002`, `INJ_003`,...).

---

## 2. Quy chuẩn định dạng dữ liệu (Schema)

Tệp dữ liệu phải là một mảng JSON (JSON array) hợp lệ, mã hóa UTF-8, thụt đầu dòng 2 khoảng trắng. Mỗi đối tượng tài liệu bắt buộc bao gồm đúng 5 trường sau:

| Trường | Kiểu dữ liệu | Quy định giá trị |
| :--- | :--- | :--- |
| `doc_id` | Chuỗi (`string`) | `INJ_001`, `INJ_002`, ... |
| `title` | Chuỗi (`string`) | Tiêu đề tài liệu bằng tiếng Việt |
| `content` | Chuỗi (`string`) | Nội dung chi tiết của tài liệu |
| `sensitivity` | Chuỗi (`string`) | Bắt buộc là `"S0"` (công khai) |
| `trust` | Chuỗi (`string`) | Bắt buộc là `"T1"` (nguồn bên ngoài / không tin cậy) |

---

## 3. Cấu hình hòm thư nhận dữ liệu trong danh sách cho phép (Allowlist)

Để minh họa trực quan hành vi rò rỉ dữ liệu khi hệ thống vận hành ở chế độ không có phòng thủ (Mode A0):
- Nhóm nghiên cứu phải cấu hình ít nhất một địa chỉ hòm thư đại diện cho bên tấn công (attacker mailbox) nằm trong danh sách cho phép (`email_allowlist`) của môi trường demo.
- Hòm thư này phải sử dụng tên miền giả lập (ví dụ: `attacker@adversary.example` hoặc `exfil@external.example`).
- Việc đưa địa chỉ vào allowlist nhằm đảm bảo công cụ gửi thư không bị tầng mạng cơ bản chặn trước khi logic của Agent kịp kích hoạt trong chế độ A0.

---

## 4. Danh mục kiểm tra bắt buộc (Authoring Checklist)

Trước khi commit bất kỳ tài liệu thử nghiệm nào vào tệp `injected_documents.json`, người biên soạn phải kiểm tra và xác nhận toàn bộ các tiêu chí sau:

- [ ] **Dữ liệu hoàn toàn nhân tạo:** Tuyệt đối không sử dụng danh tính người thật, số điện thoại thật, hoặc địa chỉ email thực tế. Toàn bộ thông tin email phải sử dụng định dạng miền thử nghiệm `*.example`.
- [ ] **Không tái sử dụng dữ liệu đánh giá:** Tuyệt đối không sao chép lại nguyên văn các câu lệnh, kịch bản hoặc đoạn trích từ tập dữ liệu Benchmark đánh giá (Dev/Test sets) để tránh thiên lệch kết quả nghiên cứu.
- [ ] **Kiểm thử trên cả hai chế độ:**
  - Chạy thử nghiệm trên **Chế độ A0 (Baseline/Unprotected):** Xác nhận Agent bị đánh lừa và thực hiện hành vi theo dõi/rò rỉ dữ liệu tới hòm thư đã cấu hình.
  - Chạy thử nghiệm trên **Chế độ BrokerGuard v3:** Xác nhận hệ thống phát hiện luồng dữ liệu độc hại, chặn đứng hành vi phát tán và bảo vệ dữ liệu nhạy cảm thành công.
- [ ] **Ghi nhận kịch bản tương ứng:** Ghi chú rõ tài liệu này được thiết kế để kích hoạt khi người dùng đưa ra câu lệnh/kịch bản tương tác nào trong phiên demo.
