# Prompt cho phiên sau

Cập nhật: 2026-10-26 19:45. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A. R3 đã đóng băng (tag final-config, manifest
configs/final/final_config_v1.json). Bảng RQ2 Dev: ASR ghép cặp A0 26 → A4–A6 0; A6 v3
benign 60/200. Dry-run Dummy trên Test đã pass.

Việc đầu tiên: hỏi owner hai việc đang chờ quyết: (1) RQ3 clean robustness, vì 250 biến thể
chưa tồn tại; (2) có chuyển repo sang private trước khi chạy Test không. Sau đó làm R4 theo
lệnh trong handoff: bật notebook, chạy security Test một lần, rồi clean Test cho 3 backbone.
Không sửa file nào nằm trong manifest; runner sẽ từ chối chạy Test nếu lệch.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
