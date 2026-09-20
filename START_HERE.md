# Đồ án — bắt đầu tại đây

Trang điều hướng chung cho Obsidian, GitHub và trình soạn thảo; không sao chép
trạng thái nghiệm thu. Mở các nguồn bên dưới để đọc thông tin hiện hành.

## Tiếp tục công việc

1. [Phase nào đã nghiệm thu?](docs/project/phase_status.md)
2. [Kết quả mới nhất](knowledge/current_status.md)
3. [Đang dở gì, bước kế tiếp và giới hạn truy cập](knowledge/handoff.md)
4. [Danh sách phần còn thiếu của Phase 5](knowledge/phase5_remaining.md)

## Tra cứu và bàn giao cho Minh

| Cần tìm | Nguồn duy nhất cần cập nhật |
|---|---|
| Tri thức, lịch sử và hướng dẫn thao tác | [Mục lục knowledge](knowledge/README.md) |
| Notebook/Dataset Kaggle, phiên bản và quyền | [Sổ tài nguyên Kaggle](knowledge/kaggle_resources.md) |
| Phạm vi nghiên cứu và điều không được vi phạm | [Contract](docs/project/research_contract.md), [invariants](docs/project/invariants.md) |
| Lý do quyết định và ngoại lệ | [Decision log](docs/project/decision_log.md) |
| Báo cáo thực nghiệm | [Danh mục báo cáo](docs/evaluation/) |
| Biên bản máy đọc được, hash và nguồn thực nghiệm | [Manifests đã chọn](experiments/manifests/) |
| Lưu ở đâu, sao lưu thế nào, dùng Obsidian ra sao | [Quy ước lưu trữ](knowledge/storage_and_obsidian.md) |

Không nhập credentials, ground truth riêng hoặc payload Test vào ghi chú.
Không đưa knowledge vào prompt benchmark. Graph nhiều liên kết không có nghĩa
phase đã hoàn thành; phải đối chiếu acceptance và bằng chứng.

`results/` và `build/` là dữ liệu local bị Git bỏ qua: clone repo không khôi phục
chúng. Xem hướng dẫn lưu trữ trước khi xóa, đồng bộ cloud hoặc bàn giao máy.
