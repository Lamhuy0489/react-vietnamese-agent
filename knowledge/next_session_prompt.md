# Prompt cho phiên sau

Cập nhật: 2026-10-26 13:00. Mở `claude` ở root repo rồi dán khối dưới đây. `CLAUDE.md` tự nạp
quy trình phiên chuẩn (thứ tự đọc, Bản đồ, việc cuối phiên), nên khối này chỉ nêu việc cụ thể.

```text
Tiếp tục đồ án theo quy trình phiên trong CLAUDE.md.

Trạng thái: rebuild A, R1 xong, R2 khoảng 75%. Lượt A0–A6 Dev đầy đủ (Qwen3-8B, A6 v2,
guard Llama-3.2-3B, 2.800 lượt) resume từ 2026-10-26 12:23 tại
results/rebuild_a/adv_dev_qwen3_8b_a6v2.

Việc đầu tiên: đếm runs/A*/*/result.json. Nếu < 2.800 thì chạy lệnh resume trong handoff
(bật lại notebook nếu đã tắt). Rồi chấm điểm, kiểm model_error < 2%, ghi bảng A0–A6 vào
decision log và cân nhắc đóng băng config (R3). Kiểm PR #4 đã merge và tag phase5-closure chưa.
Không sửa prompt v3, không đụng Test, không sửa dữ liệu đã seal.
```

## Ghi chú dùng

- Claude Code tự đọc `CLAUDE.md` ở root (quy trình phiên chuẩn), file này import `AGENTS.md`. Memory riêng
  của Claude nằm trong `~/.claude/projects/.../memory/` và không có trong Git.
- Muốn mở lại đúng đoạn chat cũ: chạy `claude --continue` (phiên gần nhất) hoặc
  `claude --resume` (chọn phiên trong danh sách).
- Không dán credential, GT private hay payload Test vào prompt.
- File này là bản gốc của prompt: agent viết lại khối `text` ở cuối mỗi phiên rồi commit,
  nên chat mới chỉ cần đọc file này, không cần bản copy trong chat cũ.
