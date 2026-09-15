# Phase 5 — phần còn phải đóng theo kế hoạch

Cập nhật2026-09-15, đối chiếu `plan/phase5.md` mụcCXXVI(20DoD) và
[trạng thái chính thức](../docs/project/phase_status.md).
Đây là hàng đợi phần còn mở, không phải tuyên bố mọi DoD khác đã được nghiệm thu.
Chỉ số4/7≈57% là nhóm acceptance trong [progress](phase5_progress.md).

| Phần cần hoàn thiện | Bằng chứng còn thiếu / bước cụ thể |
|---|---|
| DoD-5: A2 end-to-end, structured output ổn định | Baseline có30JSON errors. Observer native v1 đang chạy để cung cấp dấu hiệu lỗi có hash; sau audit mới xác định sửa gì và đo lại trong protocol riêng. |
| Lifecycle GPU của runtime | Baseline192workers reaped nhưng13TERMINATE. Đánh giá observed graceful và recovery của từng worker; thiết kế kiểm tra lỗi/shutdown cần thiết từ bằng chứng. |
| DoD-9/13/14/16: A6 provenance, egress/final sink, unknown origin | Có bounded CPU controls; còn đối chiếu phạm vi hỗ trợ và các trường hợp ngoài phạm vi. Không đồng nhất “có sensitive artifact” với payload xuất ra. |
| DoD-15: benign utility đại diện | Native112ca chưa chứng minh utility: có ca không gọi tool, SQL sai bảng, thiếu column grant. Kiểm từ user instruction và public tool/catalog; lưu cả successful/denied/error. |
| Grouped Dev differential | Lịch112ca đã audit; cần đo và giải thích các khác biệt A0–A6 khi guard/lifecycle đủ ổn định, theo protocol đã khóa và giữ nguyên thất bại cũ. |
| DoD-20: formal freeze và báo cáo nghiệm thu | Chỉ khóa rules/guard/model/config/architecture khi các gate trên có bằng chứng. Lập mapping20DoD→tests/receipts/giới hạn trước chuyển phase. |

Hiện đang thực hiện mục đầu: [observer native run](../docs/evaluation/phase5_observer_native_v2_run.md).
Notebook v1 đã gửi, version/source xác minh. Khi COMPLETE: tải fresh output,
releaseaudit, thống kê syntax/toolpath/timing/lifecycle, rồi chọn bước sửa có
bằng chứng. Tiếp tục kiểm separation/Test hash/mock-side-effect invariants theo
contract; không dùng dữ liệu Test để lựa chọn phương án sửa.
