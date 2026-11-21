# Prompt cho phiên sau

Cập nhật: 2026-11-21. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

PHẦN CỨNG: không render hình/PDF trên máy (owner dùng Overleaf; đọc PDF owner tải về bằng PyMuPDF của python3 hệ thống ở
dpi thấp thì được), không tự khởi động lại OmniRoute. Mọi thực nghiệm đã xong, không có notebook Kaggle nào chạy.

Trạng thái (21/11): BÀI v3 ĐÃ CHỐT, main đủ (PR #8 merge, commit 4e70b5c). Bài ở docs/paper/brokerguard_v3/ (latex/ =
tiếng Việt, latex_en/ = tiếng Anh). Giai đoạn hiện tại: TRIỂN KHAI THỰC TẾ HỆ THỐNG BrokerGuard v3 (dịch vụ/demo dùng
được, không phải thực nghiệm mới).

Việc của phiên này:
1. Hỏi owner phạm vi triển khai: ai dùng, model và nơi chạy (Kaggle, OmniRoute, máy local), giao diện (API, web demo,
   CLI), dữ liệu demo (chỉ dữ liệu tổng hợp), quy mô. Đề xuất phương án khuyến nghị.
2. Lập kế hoạch, ghi quyết định vào docs/project/decision_log.md, rồi mới viết code dưới src/react_agent/ kèm test.
   Giữ các bất biến trong AGENTS.md (mọi tool qua Tool Broker, mock không gọi mạng, không dùng dữ liệu Test).

Để sau (owner chưa yêu cầu làm ngay): sửa bài theo phản biện. Các bản phản biện ở root, chưa commit: phan bien.md,
phan bien2.md, phan bien3.md, Review Huy.docx. Gộp vào đó việc đồng bộ bản Việt với bản Anh (phông Times có T5,
lượt 3b, 3c, 4), ≤ 15 trang, số chỉ lấy từ docs/paper/iccies2027/facts.md.

Commit và PR không ghi Claude là đồng tác giả. Claude không viết, đọc hay giao việc viết văn bản/prompt tấn công hay
nội dung Test; chỉ hạ tầng, số đếm và biên soạn.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
